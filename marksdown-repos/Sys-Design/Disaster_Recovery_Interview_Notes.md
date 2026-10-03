# Disaster Recovery (DR) System Design — 8-Minute Interview Guide

> **Interview objective:** Be able to answer a CTO/Architect when they ask:
>
> **“How would you design Disaster Recovery for a highly critical financial system?”**

The key is **not to start with AWS, Kubernetes, Kafka, or databases**.

Start by asking:

> **“What failure are we protecting against, and how much data/service disruption can the business tolerate?”**

---

# 1. First Question: What exactly is Disaster Recovery?

### What this teaches
It separates **DR from normal high availability (HA)**.

### Why needed
Many candidates immediately say:

> “We'll deploy the application in two regions.”

That's not enough.

DR asks:

> **“If our entire primary environment becomes unavailable, how do we continue business and recover data?”**

Think:

```text
             NORMAL WORLD

        PRIMARY REGION
       +---------------+
       | Application   |
       | Database      |
       | Kafka         |
       | Cache         |
       +---------------+
              |
              v
           Customers
```

Now imagine:

```text
       PRIMARY REGION
       XXXXXXXXXXXXXXX
       X  REGION DOWN X
       XXXXXXXXXXXXXXX

              |
              | Disaster
              v

       SECONDARY REGION
       +---------------+
       | Application   |
       | Database      |
       | Kafka         |
       +---------------+
```

DR is the capability to:

```text
Detect
   ↓
Decide
   ↓
Failover
   ↓
Restore service
   ↓
Recover data
   ↓
Validate
   ↓
Resume normal operations
```

---

# 2. Question: HA and DR — aren't they the same?

### What this teaches
This is one of the **first follow-up questions an architect may ask**.

### Why needed
You need to demonstrate that you understand different failure domains.

### High Availability

Protects against:

```text
Server failure
    ↓
Another server takes over
```

Example:

```text
             Load Balancer
                  |
          +-------+-------+
          |               |
       Server A         Server B
          X
          |
          v
       Server B
```

### Disaster Recovery

Protects against:

```text
Entire Region
Entire Data Center
Major infrastructure failure
Large-scale operational disaster
```

Example:

```text
       REGION A                  REGION B
     PRIMARY                    DR

   +---------+                +---------+
   | App     |  Replication   | App     |
   | DB      | --------------> | DB      |
   | Kafka   |                | Kafka   |
   +---------+                +---------+
```

Remember:

```text
HA = survive component failure

DR = survive environment failure
```

---

# 3. Question: Before designing DR, what should we ask the business?

### What this teaches
You learn the most important DR concepts:

**RTO and RPO.**

### Why needed
DR architecture is driven by **business requirements**, not technology preference.

Ask:

> “How much downtime can the business tolerate?”

This is **RTO**.

### RTO

**Recovery Time Objective**

```text
Disaster
   |
   |---- 15 min ----|
                   |
                   v
             Service restored
```

If:

```text
RTO = 15 minutes
```

The system must be restored within approximately 15 minutes.

---

Ask:

> “How much data can we afford to lose?”

This is **RPO**.

```text
Database

10:00 ---- 10:01 ---- 10:02 ---- 10:03
                         X
                      Disaster
```

If:

```text
RPO = 1 minute
```

We should lose no more than roughly one minute of committed data under the defined DR scenario.

### Remember:

```text
             DR REQUIREMENTS

          +-------------------+
          |      Business     |
          +---------+---------+
                    |
             +------+------+
             |             |
             v             v
            RTO           RPO
             |             |
             v             v
        How fast?      How much
                       data loss?
```

---

# 4. Question: How do RTO/RPO change our architecture?

### What this teaches
You learn how to convert **business requirements into technical architecture**.

### Why needed
This is where a senior architect differentiates themselves.

Suppose:

```text
RTO = 24 hours
RPO = 24 hours
```

You could potentially use:

```text
Backup
  ↓
Restore
  ↓
Rebuild
```

But:

```text
RTO = 5 minutes
RPO = near-zero
```

Now you need:

```text
Continuous replication
+
Warm/Hot DR
+
Automated failover
+
Pre-provisioned infrastructure
```

Think:

```text
       LOW DR REQUIREMENT

Primary -----> Backup
                 |
              Restore
                 |
              DR System


       HIGH DR REQUIREMENT

Primary ==================> DR
          Continuous
          Replication

       Ready to take traffic
```

---

# 5. Question: What DR strategies are available?

### What this teaches
You learn the standard DR patterns.

### Why needed
The interviewer may ask:

> “Why did you choose active-passive instead of active-active?”

There are several approaches.

## Strategy 1 — Backup & Restore

```text
PRIMARY
   |
   | periodic backup
   v
Backup Storage
   |
   | Disaster
   v
Restore
   |
   v
DR
```

Characteristics:

```text
Cost       LOW
Recovery   SLOW
RPO        HIGHER
RTO        HIGHER
```

Suitable when downtime/data-loss tolerance is relatively high.

## Strategy 2 — Pilot Light

Keep critical infrastructure/data replicated but application capacity is limited.

```text
PRIMARY                 DR

App x 100               App x 5
DB                     DB replica
Kafka                  Kafka replica
```

During disaster:

```text
Scale DR
   ↓
Start services
   ↓
Route traffic
```

## Strategy 3 — Warm Standby

```text
PRIMARY                  DR

App x 100                App x 30
DB Primary  ---------->  DB Replica
Kafka      ---------->   Kafka
```

DR is already running.

Failover is faster.

## Strategy 4 — Active-Active

Both regions serve traffic.

```text
                 Global DNS
                     |
             +-------+-------+
             |               |
             v               v
        REGION A          REGION B
        Active             Active
          |                  |
          +------ Sync ------+
```

Advantages:

```text
High availability
Fast failover
Better utilization
```

But complexity is much higher:

```text
Data consistency
Conflict resolution
Distributed transactions
Cross-region latency
Traffic routing
```

---

# 6. Question: What architecture would you choose for a financial system?

### What this teaches
You learn how to make a **reasoned architecture choice**.

### Why needed
For a payment/wealth/banking platform, availability and financial integrity both matter.

A practical architecture could be:

```text
                  GLOBAL DNS / ROUTER
                         |
             +-----------+-----------+
             |                       |
             v                       v
       PRIMARY REGION           DR REGION
       Region A                 Region B
             |                       |
      +------+-------+         +-----+------+
      |              |         |            |
     App            Kafka     App          Kafka
      |              |         |            |
      v              v         v            v
     DB ----------Replication---------> DB
      |
      v
 Object Storage -----------------------> Object Storage
```

Depending on the workload, you could choose:

```text
Critical APIs
     |
     v
Active-Active / Warm

Financial DB
     |
     v
Strongly controlled replication

Batch systems
     |
     v
Warm standby
```

**Don't automatically make everything active-active.**

The right answer is driven by:

```text
RTO
RPO
Consistency
Cost
Complexity
Regulatory requirements
Data topology
```

---

# 7. Question: What happens to the database during a disaster?

### What this teaches
The **database is usually the hardest DR component**.

### Why needed
You can recreate application servers relatively easily.

You cannot casually recreate:

```text
Financial transactions
Customer balances
Orders
Payments
Ledger entries
```

Suppose:

```text
PRIMARY DB

TX100
TX101
TX102
TX103
```

Replication:

```text
PRIMARY DB
TX100
TX101
TX102
TX103
   |
   | replication
   v
DR DB
TX100
TX101
TX102
TX103
```

Disaster occurs:

```text
Primary DB X

DR DB
TX100
TX101
TX102
TX103
```

DR becomes primary.

---

# 8. Question: How do we handle replication lag?

### What this teaches
You learn why **RPO is an actual technical measurement**.

### Why needed

Imagine:

```text
PRIMARY                 DR

TX100 ----------------> TX100
TX101 ----------------> TX101
TX102 ----------------> TX102

TX103
TX104
   |
   | still replicating
   X
Disaster
```

DR only has:

```text
TX100
TX101
TX102
```

Potential data loss:

```text
TX103
TX104
```

Therefore monitor:

```text
Replication Lag
```

Example:

```text
Replication Lag = 3 seconds
```

If your RPO is:

```text
1 minute
```

you are within the target.

If:

```text
Replication Lag = 20 minutes
```

you have an RPO breach.

Dashboard:

```text
+--------------------------------+
|       DR HEALTH                |
+--------------------------------+
| DB Replication Lag     3 sec   |
| Kafka Replication Lag  5 sec   |
| Object Sync Lag       12 sec   |
| DR Capacity            80%     |
+--------------------------------+
```

---

# 9. Question: What happens to Kafka during DR?

### What this teaches
You learn that **DR is not just a database problem**.

### Why needed
Modern architectures often depend heavily on event streams.

```text
Primary Kafka
      |
      | replication
      v
DR Kafka
```

We need to consider:

```text
Topics
Partitions
Offsets
Consumer groups
Messages in flight
Replication lag
Ordering
Duplicates
```

Potential failure:

```text
Producer
   |
   v
Kafka Primary
   |
   X
Consumer hasn't processed event
```

After failover:

```text
DR Kafka
   |
   v
Consumer
```

The event may be processed again.

Therefore:

```text
Kafka
 +
Idempotent Consumers
 +
Business Deduplication
```

Again:

> **Don't depend on exactly-once semantics across the entire distributed system.**

Design downstream operations to tolerate replay.

---

# 10. Question: How do we fail over?

### What this teaches
You learn the **actual DR sequence**, rather than simply saying "DNS will switch."

### Why needed
Failover is a distributed operation.

A typical sequence:

```text
              DISASTER
                  |
                  v
          Detect / Declare
                  |
                  v
          Freeze Primary
                  |
                  v
        Stop conflicting writes
                  |
                  v
       Validate DR replication
                  |
                  v
        Promote DR Database
                  |
                  v
        Start / Scale services
                  |
                  v
       Switch traffic routing
                  |
                  v
          Health Validation
                  |
                  v
           RESUME TRAFFIC
```

---

# 11. Question: Who decides that a disaster has happened?

### What this teaches
You learn the difference between **failure detection and disaster declaration**.

### Why needed

Suppose:

```text
Application health check fails
```

That doesn't necessarily mean:

```text
REGION IS DEAD
```

Maybe:

```text
One service crashed
Network issue
Deployment problem
Database overload
Monitoring problem
```

Therefore:

```text
Monitoring
    |
    v
Detection
    |
    v
Incident Management
    |
    v
DR Decision
    |
    v
Failover
```

For critical systems, uncontrolled automatic failover can itself create problems such as split-brain.

---

# 12. Question: What is split-brain?

### What this teaches
This is a classic senior-level DR question.

### Why needed
Imagine both regions think they are primary.

```text
              Traffic
             /       \
            v         v

       REGION A     REGION B
       PRIMARY      PRIMARY

          |             |
        WRITE         WRITE
          |             |
          +------X------+
```

Now:

```text
TX100 = ₹1000
```

could become:

```text
Region A → ₹1100
Region B → ₹1200
```

Now reconciliation becomes extremely difficult.

Therefore we need a **single-writer/leader control mechanism** for systems that cannot safely accept concurrent writes.

```text
                 Leader
                   |
          +--------+--------+
          |                 |
       Region A          Region B
       STANDBY             READ
```

After controlled failover:

```text
Region A X

Region B
   |
   v
NEW LEADER
```

---

# 13. Question: How do we handle DNS and traffic routing?

### What this teaches
You learn how the customer actually reaches the DR system.

### Why needed
Even if DR is perfectly healthy, users won't reach it unless routing changes.

```text
                 Users
                   |
                   v
            Global Traffic
              Manager
             /         \
            /           \
           v             v
      Region A       Region B
      Primary           DR
```

During disaster:

```text
Region A
   X
   |
   v
Traffic Manager
   |
   v
Region B
```

Possible mechanisms:

```text
DNS failover
Global load balancer
Anycast
Cloud traffic manager
Application-level routing
```

But remember:

> **DNS failover has TTL/cache implications.**

Don't claim:

> "DNS switches instantly."

---

# 14. Question: What happens to in-flight transactions?

### What this teaches
This is particularly important for **payments and financial systems**.

### Why needed

Suppose:

```text
Customer
   |
   v
Payment API
   |
   v
Gateway
   |
   X
Region fails
```

Question:

> Did the payment happen or not?

This creates the dangerous state:

```text
UNKNOWN
```

We cannot simply retry blindly.

Because:

```text
First request → Gateway processed ₹1000
Second request → Gateway processes another ₹1000
```

Potential double payment.

Therefore:

```text
Payment Request
      |
      v
Idempotency Key
      |
      v
Payment Gateway
```

After DR:

```text
UNKNOWN PAYMENT
       |
       v
Query gateway/payment status
       |
   +---+---+
   |       |
FOUND    NOT FOUND
   |       |
   v       v
Reconcile  Retry
```

This is one of the most important points to mention in a financial DR interview.

---
