# MRC: How OpenAI Built a Network That Keeps 100,000+ GPUs Working Together

## A 6-minute easy explanation from an AI + Software Architect perspective

OpenAI's MRC (Multipath Reliable Connection) is a networking architecture designed for large-scale AI training.

The central problem is simple:

> **How do you keep 100,000+ GPUs communicating quickly and reliably when congestion and failures are inevitable?**

---

## 1. Why AI Training Needs a Huge Network

Normal applications often look like:

```text
User
  │
  ▼
Application Server
  │
  ▼
Database
```

Large AI training looks more like:

```text
                AI TRAINING JOB

       ┌───────┬───────┬───────┐
       │       │       │       │
      GPU     GPU     GPU     GPU
       │       │       │       │
       ├───────┼───────┼───────┤
       │       │       │       │
      GPU     GPU     GPU     GPU
       │       │       │       │
       └───────┴───────┴───────┘
                NETWORK
```

The GPUs constantly exchange data. In synchronous training, if one GPU is delayed, many other GPUs may have to wait.

Think of 100,000 people rowing a giant boat:

```text
Person 1      → ROW
Person 2      → ROW
Person 3      → ROW
...
Person 100000 → ROW
```

If one person stops:

```text
99,999 people → WAIT
```

---

## 2. The Real Enemy: One Slow Network Path

Imagine many GPUs sending traffic through one link:

```text
GPU ──┐
GPU ──┤
GPU ──┤
GPU ──┼────► ONE LINK ────► Destination
GPU ──┤
GPU ──┤
GPU ──┘
```

The link becomes congested.

At 100,000+ GPUs, even small congestion problems can become major training-performance problems.

---

## 3. Networks Also Fail

At small scale:

```text
100 servers
     │
     ▼
Maybe one network failure
```

At enormous scale:

```text
100,000+ GPUs
       │
       ▼
Millions of network links
       │
       ▼
Failures become inevitable
```

The question isn't:

> "Can we build a network that never fails?"

The better question is:

> **"Can the system continue working when parts of the network fail?"**

That is the philosophy behind MRC.

---

## 4. Traditional Approach: One Path

A traditional route might look like:

```text
GPU A
  │
  ▼
Switch 1
  │
  ▼
Switch 2
  │
  ▼
Switch 3
  │
  ▼
GPU B
```

If something breaks, the network has to find another route.

At huge scale, waiting for routing changes can be expensive.

---

## 5. MRC's Big Idea: Use Many Paths

Instead of sending a transfer through one path:

```text
One transfer
     │
     ▼
ONE PATH
```

MRC spreads packets across many paths:

```text
                 ┌──► Path 1 ──►
                 │
                 ├──► Path 2 ──►
GPU ──► MRC ─────┼──► Path 3 ──► GPU
                 │
                 ├──► Path 4 ──►
                 │
                 └──► Path 5 ──►
```

Think of sending 100 packages.

Traditional:

```text
100 packages
     │
     ▼
One truck
     │
     ▼
One highway
```

MRC:

```text
100 packages
 │ │ │ │ │
 ▼ ▼ ▼ ▼ ▼
🚚 🚚 🚚 🚚 🚚
 │ │ │ │ │
 ▼ ▼ ▼ ▼ ▼
Many roads
```

If one road becomes slow or fails, other roads can continue carrying traffic.

---

## 6. Packets Can Arrive Out of Order

When packets use different paths:

```text
Packet 1 → Path A
Packet 2 → Path B
Packet 3 → Path C
Packet 4 → Path D
```

They may arrive as:

```text
Packet 3
Packet 1
Packet 4
Packet 2
```

MRC handles this by allowing out-of-order arrival and using the destination memory address so data can be placed correctly.

Important architecture principle:

> **Don't force the network to preserve order if the destination can reconstruct the correct order.**

---

## 7. Multiple Network Planes

MRC also uses a multi-plane design.

For example, instead of treating an 800 Gb/s interface as one giant connection:

```text
800 Gb/s
    │
    ▼
ONE BIG CONNECTION
```

it can use multiple independent links:

```text
             800 Gb/s NIC
                  │
        ┌─────────┼─────────┐
        │         │         │
       100       100       100
       Gb/s      Gb/s      Gb/s
        │         │         │
     Switch    Switch    Switch
```

OpenAI gives an example where one interface can connect to eight switches, creating eight 100 Gb/s network planes instead of one 800 Gb/s plane.

Think of it as multiple roads:

```text
CITY
 │
 ├──► ROAD 1
 ├──► ROAD 2
 ├──► ROAD 3
 ├──► ROAD 4
 ├──► ROAD 5
 ├──► ROAD 6
 ├──► ROAD 7
 └──► ROAD 8
```

---

## 8. Why This Matters for 100,000+ GPUs

OpenAI says this multi-plane design can connect roughly **131,000 GPUs with only two tiers of switches**, compared with three or four tiers for a conventional 800 Gb/s design.

Simplified:

```text
Traditional

GPU
 │
 ▼
Tier 1
 │
 ▼
Tier 2
 │
 ▼
Tier 3
 │
 ▼
GPU


MRC

GPU
 │
 ▼
Tier 1
 │
 ▼
Tier 2
 │
 ▼
GPU
```

Fewer layers can mean:

- fewer components
- fewer failure points
- lower power consumption
- lower cost
- simpler architecture

---

## 9. What Happens When a Path Fails?

Imagine:

```text
GPU
 │
 ├──► Path A ✓
 ├──► Path B ✓
 ├──► Path C ❌
 ├──► Path D ✓
 └──► Path E ✓
```

MRC can stop using the failed path while continuing over healthy paths.

```text
Path C
   │
   ▼
FAILED
   │
   ▼
STOP USING IT
```

OpenAI says MRC can detect failures and route around them on a **microsecond timescale**, whereas conventional network fabrics can take much longer to stabilize.

---

## 10. What About Lost Packets?

MRC uses **packet trimming**.

If a switch becomes congested, instead of simply dropping the whole packet:

```text
Packet
  │
  ▼
Switch
  │
  X
DROP
```

MRC can trim the packet and forward its header:

```text
Full Packet
    │
    ▼
Congested Switch
    │
    ▼
Header only
    │
    ▼
Destination
    │
    ▼
"Please retransmit this packet."
```

This helps distinguish congestion from actual network-path failure.

---

## 11. Source Routing with SRv6

Traditional routing often lets switches dynamically decide where packets go.

MRC uses **SRv6 source routing**.

Conceptually:

```text
Sender

"I want this packet to go:

Switch A
   ↓
Switch D
   ↓
Switch F
   ↓
Switch J
   ↓
Destination"
```

The sender can specify the sequence of network segments.

This moves some routing intelligence toward the endpoints.

---

## 12. Why Can Simpler Switches Be Better?

At enormous scale:

```text
More intelligence
       │
       ▼
More software
       │
       ▼
More state
       │
       ▼
More complexity
       │
       ▼
More failure modes
```

MRC shifts more intelligence toward the endpoints:

```text
Traditional

Switches
  │
  ├── calculate
  ├── communicate
  ├── recalculate
  └── react


MRC

Sender
  │
  ├── knows paths
  ├── detects failures
  └── chooses another path

Switches
  │
  └── forward packets
```

Architecture principle:

> **Move complexity to the component that has better information and can make the decision faster.**

---

## 13. MRC in One Picture

```text
                     GPU CLUSTER
                  100,000+ GPUs
                        │
                        ▼
              ┌──────────────────┐
              │   MRC NETWORK    │
              └────────┬─────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
      Plane 1       Plane 2       Plane 3
         │             │             │
     ┌───┼───┐     ┌───┼───┐     ┌───┼───┐
     ▼   ▼   ▼     ▼   ▼   ▼     ▼   ▼   ▼
    S1  S2  S3    S4  S5  S6    S7  S8  S9
     │   │   │     │   │   │     │   │   │
     └───┴───┴─────┴───┴───┴─────┴───┴───┘
                       │
                 Many paths
                       │
                       ▼
                Destination GPU

        ┌─────────────────────────────┐
        │ Adaptive packet spraying    │
        │ + failure detection         │
        │ + packet trimming           │
        │ + SRv6 source routing       │
        └─────────────────────────────┘
```

---

## 14. What MRC Achieves

OpenAI highlights three major advantages:

### 1. Huge scale

Multi-plane networking can support supercomputers with **100,000+ GPUs using two tiers of Ethernet switches**.

### 2. Less congestion

Packets are spread across many paths instead of concentrating traffic on individual links.

### 3. Fast failure recovery

Instead of waiting for the network to recompute routes, MRC can stop using a failed path and continue over healthy paths.

---

## 15. A Real Production Example

OpenAI describes a production example where four Tier-1 switches needed to be rebooted during training.

With MRC:

```text
Training
   │
   ▼
Switch reboot
   │
   ▼
MRC avoids failed path
   │
   ▼
Training continues
```

The training team did not need to coordinate the switch reboot with the training job.

That's the real definition of resilience:

> **Failure happens, but the application doesn't care.**

---

## 16. The Software Architecture Lesson

This article isn't only about networking.

It teaches a broader architecture principle.

```text
              SYSTEM
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
    Compute   Network    Storage
       │         │         │
       ▼         ▼         ▼
    Failure   Failure    Failure
```

You cannot eliminate every failure.

Instead:

```text
FAILURE
   │
   ▼
Detect quickly
   │
   ▼
Avoid failed component
   │
   ▼
Continue working
```

That's **resilience engineering**.

---

## 17. MRC vs Traditional Network

| Area | Traditional approach | MRC approach |
|---|---|---|
| Paths | Usually one path per flow | Many paths |
| Congestion | Can create hotspots | Packet spraying distributes load |
| Network planes | Single-plane designs | Multi-plane |
| Failure handling | Recompute routes | Stop using failed path |
| Routing | Dynamic routing | SRv6 source routing |
| Packet order | Typically preserve order | Can handle out-of-order packets |
| Scale | More switch tiers | 100K+ GPUs with two tiers |
| Complexity | More control-plane logic | Simpler network control plane |
| Recovery | Can take much longer | Microsecond-scale path reaction |
| Goal | Connectivity | Predictable AI training performance |

---

## 18. The Biggest AI Architecture Insight

The key lesson is:

> **AI performance isn't just about GPUs.**

The complete stack matters:

```text
                AI TRAINING PERFORMANCE
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      MODEL            GPU             NETWORK
        │                │                │
        ▼                ▼                ▼
   Algorithms       Compute         Data movement
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  Training speed
                         │
                         ▼
                   Model quality
```

You can have extremely fast GPUs.

But if the network is slow:

```text
Fast GPU
   │
   ▼
Waiting for network
   │
   ▼
GPU idle
```

That's wasted compute.

---

## 19. The Ultimate Mental Model

Think about a large AI training cluster like a Formula 1 racing team.

```text
Fast Engine
     +
Fast Tires
     +
Fast Driver
```

But if the pit crew takes 30 seconds every lap:

```text
Fast car
   │
   ▼
Slow pit stop
   │
   ▼
Poor overall performance
```

AI is similar:

```text
Fast GPU
   +
Fast Model
   +
Fast Network
   +
Fast Storage
   +
Efficient Scheduler
   =
Fast AI Training
```

**Every layer matters.**

---

## 20. The Crux in 30 Seconds

Imagine 100,000 students solving one giant puzzle together.

They constantly need to exchange pieces.

If everyone uses the same road:

```text
Traffic jam
   ↓
Waiting
```

If one road breaks:

```text
Everyone waits
```

MRC creates many roads, spreads traffic across them, detects broken roads quickly, and stops using them.

```text
          100,000+ GPUs
                │
                ▼
        ┌───────────────┐
        │ MRC NETWORK   │
        └───────┬───────┘
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
     Path 1   Path 2   Path 3
       │        │        │
       └────┬───┴───┬────┘
            ▼       ▼
          Many parallel paths
                │
         ┌──────┴──────┐
         ▼             ▼
      Congestion      Failure
         │             │
         ▼             ▼
    Spread traffic   Avoid path
         │             │
         └──────┬──────┘
                ▼
        Training continues
```

---

# Final Takeaway

The deepest idea in OpenAI's MRC architecture is:

> **At extreme scale, reliability is not something you add after building the system. Reliability has to be part of the architecture itself.**

MRC combines:

```text
Multi-plane network
        +
Packet spraying
        +
Adaptive load balancing
        +
Fast failure detection
        +
Packet trimming
        +
SRv6 source routing
        ↓
Predictable AI training
```

For an **AI/Software Architect**, the broader lesson is:

> **Don't ask only, "How fast is my component?" Ask, "What happens when 100,000 components are communicating simultaneously and some of them inevitably fail?"**

That is where **real distributed-systems architecture** begins.

---

## One-Line Mental Model

```text
MORE GPUs
   +
MORE NETWORK PATHS
   +
FAST FAILURE DETECTION
   +
SMART PACKET ROUTING
   =
SCALABLE + RESILIENT AI TRAINING
```

**Source:** OpenAI — *MRC: A network architecture for large-scale AI training*
