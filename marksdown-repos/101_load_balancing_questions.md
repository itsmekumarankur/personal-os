# System Design Interviewing: Question Before Choosing Technology

The screen is teaching a very important **system-design interviewing technique**:

> **Don't jump from requirements → technology. First interrogate the problem.**

Here, someone proposes:

> **“Let’s use an L4 load balancer with round-robin.”**

The interviewer wants you to **challenge that proposal before accepting it**.

---

## 1. Understand the problem first

You are designing the **front door of a global banking platform**.

You have:

- Millions of users
- HTTP/1.1
- HTTP/2
- gRPC
- Highly uneven request costs
- Some long-lived connections
- Multiple backend services
- Strict availability requirements
- Requirement that an LB-node failure should happen **without users noticing**

The inexperienced architect immediately says:

```text
Users
  |
  v
L4 LB + Round Robin
  |
  +---- Backend 1
  +---- Backend 2
  +---- Backend 3
```

The experienced architect says:

> **“Before I choose L4 + round-robin, let me understand what exactly needs to be balanced and what failure/traffic characteristics I have.”**

That's the core lesson.

---

## 2. Question: What exactly are we balancing?

This is the first critical question.

Are we balancing:

```text
Requests?
Connections?
Sessions?
Streams?
Bytes?
CPU work?
Backend capacity?
```

These are **not the same thing**.

For example:

```text
Backend A
Connection 1 → 1 request → 10 ms

Backend B
Connection 2 → 1 request → 5 seconds
```

If you use simple connection-level distribution:

```text
Connection 1 → A
Connection 2 → B
```

you might technically have **50/50 connection distribution**.

But the workload is nowhere near 50/50.

Backend B is doing dramatically more work.

### Therefore:

> **Equal connections ≠ equal workload.**

This immediately makes you question whether round-robin is appropriate.

---

## 3. Question: Where should traffic decisions happen?

Now ask:

> **At what layer do I actually need to make routing decisions?**

There are different possibilities:

```text
DNS
  ↓
Anycast / Global LB
  ↓
L4 Load Balancer
  ↓
L7 Load Balancer / API Gateway
  ↓
Service
```

Each layer knows different information.

### L4 knows things such as:

```text
Source IP
Destination IP
Source port
Destination port
TCP/UDP
Connection
```

But L4 generally doesn't understand application semantics such as:

```text
GET /accounts
POST /payments
GET /portfolio
Authorization header
API version
HTTP path
gRPC method
```

L7 can understand those.

So you need to ask:

> **Do we need application-aware routing?**

For a banking platform, you might eventually discover requirements like:

```text
/api/payments/*      → Payment service
/api/investments/*   → Wealth service
/api/loans/*         → Loan service
```

That pushes the architecture toward an L7-aware component.

---

## 4. Question: What happens when one connection carries disproportionate work?

This is particularly important because the problem explicitly says:

> **Highly uneven request costs**

Imagine:

```text
Request A → 5 ms
Request B → 10 ms
Request C → 20 ms
Request D → 10 seconds
```

Round-robin sees:

```text
A → Server 1
B → Server 2
C → Server 3
D → Server 1
```

It doesn't inherently understand that:

```text
D ≫ A
```

in terms of backend resource consumption.

Now consider persistent connections:

```text
Client 1
   |
   +---- Connection ----> LB ----> Server A
                             ↑
                       thousands of
                         requests
```

If the LB makes its decision only when establishing the connection, all subsequent traffic can remain tied to that backend.

So you need to ask:

> **Is our balancing unit a connection or an individual request/stream?**

That question can completely change the architecture.

---

## 5. Question: What happens with HTTP/2 and gRPC?

This is one of the biggest traps.

With HTTP/1.1 you might have:

```text
Client
  |
  +--- TCP connection 1 ---> Server A
  +--- TCP connection 2 ---> Server B
```

But HTTP/2 supports **multiplexing**.

You can have:

```text
                HTTP/2 connection
Client --------------------------> LB
          |       |       |
        Stream  Stream  Stream
           1       2       3
```

Potentially many requests/streams share **one TCP connection**.

gRPC commonly uses HTTP/2 as well.

So suppose:

```text
Client
   |
   | one HTTP/2 connection
   |
   v
L4 LB
   |
   v
Backend A
```

The L4 LB sees essentially one TCP connection.

It doesn't see the individual application-level requests in the same way an L7 proxy does.

Therefore, you need to ask:

> **Does connection-level balancing still give us the distribution we want when HTTP/2/gRPC multiplex many streams over one connection?**

This is a very strong architect-level question.

---

## 6. Question: What happens if the LB itself fails?

The requirement says:

> **“Survive an LB-node failure without users noticing.”**

That immediately means:

```text
             ┌── LB Node 1 ──┐
Users ───────┤                ├── Backend
             └── LB Node 2 ──┘
```

is not enough unless you understand:

- How are LB nodes deployed?
- Is there active-active?
- How does traffic move when one node dies?
- Is there a VIP?
- Anycast?
- DNS?
- ECMP?
- Health checks?
- Connection state?
- What happens to existing connections?
- What happens to new connections?

And most importantly:

### What does “users don't notice” actually mean?

Does it mean:

```text
No failed requests?
```

or:

```text
No TCP connection reset?
```

or:

```text
Retry automatically and user doesn't see an error?
```

These are very different availability guarantees.

---

## 7. Question: What availability are we actually promising?

Suppose your LB node dies.

For **new connections**, you may be able to route traffic to another node:

```text
Before:

Client → LB1 → Backend

After LB1 failure:

Client → LB2 → Backend
```

But what about an **existing TCP connection**?

```text
Client
   |
   | existing TCP connection
   |
  LB1  X
```

If LB1 dies, that TCP connection may be lost.

The client might need to reconnect.

So:

> **LB-node failure tolerance does not automatically mean zero connection disruption.**

You have to define the SLA/SLO.

For example:

```text
99.99% availability
+
automatic client retry
+
connection re-establishment
```

may satisfy the business requirement even though a TCP connection technically breaks.

That's why an architect asks the question instead of assuming the answer.

---

## 8. Question: What cost and complexity are we willing to introduce?

This is the CTO-level question.

You could build an extremely sophisticated architecture:

```text
Global DNS
   ↓
Anycast
   ↓
Global LB
   ↓
Regional LB
   ↓
L7 Gateway
   ↓
Service Mesh
   ↓
Backend
```

But do you actually need it?

More components mean:

```text
More infrastructure
More operational burden
More failure modes
More monitoring
More configuration
More cost
More people required to operate it
```

So the question becomes:

> **What problem are we solving, and is the additional complexity justified by the business requirement?**

---

# The thinking framework

The entire exercise can be reduced to this:

```text
              DON'T START HERE
                    ↓
          "Which LB should I use?"
                    |
                    X
                    |
                    ↓
        START WITH REQUIREMENTS
                    |
          ┌─────────┴─────────┐
          ↓                   ↓
     Traffic model       Failure model
          |                   |
          ↓                   ↓
 Requests?             What can fail?
 Connections?          What happens?
 Streams?              How much disruption?
          |                   |
          └─────────┬─────────┘
                    ↓
              Protocol model
                    |
             HTTP/1.1?
             HTTP/2?
             gRPC?
                    |
                    ↓
             Routing needs
                    |
             L4 sufficient?
             Need L7?
                    |
                    ↓
            Availability/SLO
                    |
                    ↓
          Cost + operational
             complexity
                    |
                    ↓
             THEN choose:
       L4 / L7 / DNS / Anycast /
       active-active / etc.
```

---

# What the interviewer is really testing

They aren't primarily testing:

> **“Do you know L4 load balancing?”**

They are testing whether you have the **questioning muscle of an architect**.

A junior engineer might say:

> “Round-robin is simple and distributes traffic evenly.”

A senior architect should respond:

> “Before selecting round-robin, I need to understand whether we're balancing connections, requests, or streams; whether connection duration and request cost are uniform; how HTTP/2 and gRPC multiplex traffic; whether routing needs application awareness; and what failure semantics the availability requirement actually demands.”

A CTO goes one step further:

> **“What business outcome are we optimizing, what failure are we trying to prevent, and is the additional infrastructure complexity justified?”**

That is exactly the progression the exercise is trying to teach:

**Architect → Senior Architect → CTO**

rather than simply memorizing:

**L4 vs L7 → Round Robin vs Least Connections.**
