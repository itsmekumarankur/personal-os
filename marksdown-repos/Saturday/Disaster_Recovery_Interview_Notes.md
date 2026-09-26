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

# 15. Question: What about external dependencies?

### What this teaches
You learn **dependency-aware DR**.

### Why needed
Your system may recover while external systems don't.

```text
             Your Platform
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
    Gateway      Bank        KYC
       X           X           ✓
```

Your application is healthy but:

```text
Gateway unavailable
```

So DR is not:

```text
"My servers are running"
```

It is:

```text
End-to-end business capability is available
```

Maintain:

```text
Dependency inventory
Health status
Fallback strategy
Timeouts
Retries
Circuit breakers
Manual process
```

---

# 16. Question: How do we prevent data corruption during recovery?

### What this teaches
You learn **reconciliation-before-resumption**.

### Why needed

After failover:

```text
DR is UP
```

doesn't mean:

```text
DR is CORRECT
```

Before reopening traffic:

```text
                 DR
                  |
          +-------+-------+
          |       |       |
          v       v       v
        DB      Kafka   Storage
          |       |       |
          +-------+-------+
                  |
                  v
           Consistency Check
                  |
                  v
          Business Validation
                  |
                  v
             GO / NO-GO
```

Example:

```text
Payment count
Settlement amount
Ledger balance
Kafka offsets
Database replication position
```

must be validated.

---

# 17. Question: How do we test DR?

### What this teaches
You learn the difference between **having a DR architecture and actually having DR capability**.

### Why needed

The worst DR design is:

```text
"We have a DR environment."

"Have you tested it?"

"Not yet."
```

You need regular exercises.

```text
                DR TESTING

             +-------------+
             | DR Exercise |
             +------+------+
                    |
       +------------+------------+
       |            |            |
       v            v            v
    Failover     Recovery      Data
      Test         Test       Validation
```

Test scenarios:

```text
Application failure
Database failure
Kafka failure
Region failure
Network partition
DNS failure
Dependency failure
Corrupted deployment
Human error
Ransomware scenario
```

Measure:

```text
Actual RTO
Actual RPO
Recovery success rate
Replication lag
Manual steps
Data inconsistencies
```

---

# 18. Question: What if the DR region itself fails?

### What this teaches
You learn **resilience beyond a simple primary/secondary model**.

### Why needed

Basic:

```text
A → B
```

is better than nothing.

But critical systems may need:

```text
             REGION A
             PRIMARY
                |
        +-------+-------+
        |               |
        v               v
    REGION B         REGION C
      DR             Backup DR
```

Or:

```text
             Multi-region

          +------+------+
          |             |
       Region A       Region B
          |             |
          +------+------+
                 |
              Region C
```

The architecture depends on:

```text
Risk
Cost
Regulatory requirements
RTO/RPO
Data sovereignty
Business criticality
```

---

# 19. Question: What about backups?

### What this teaches
You learn that **replication is not the same as backup**.

### Why needed

Suppose bad data gets written:

```text
             PRIMARY DB
                 |
                 v
            Corrupted data
                 |
                 | replication
                 v
               DR DB
```

Now both have corrupted data.

Therefore you need:

```text
Replication
+
Independent Backups
+
Point-in-time recovery
```

Architecture:

```text
             PRIMARY DB
                 |
       +---------+---------+
       |                   |
       v                   v
   DR Replica          Backup Store
                           |
                           v
                    Point-in-Time
                       Recovery
```

Replication protects against:

```text
Infrastructure failure
```

Backups help protect against:

```text
Data corruption
Human error
Logical deletion
Ransomware
Bad deployment
```

---

# 20. Question: What should the final DR architecture look like?

### What this teaches
This connects all the concepts into one interview-ready architecture.

```text
                         USERS
                           |
                           v
                  GLOBAL TRAFFIC MANAGER
                           |
              +------------+------------+
              |                         |
              v                         v
        REGION A                    REGION B
        PRIMARY                    DR REGION
       +---------+                +---------+
       |   WAF   |                |   WAF   |
       +----+----+                +----+----+
            |                          |
            v                          v
       Load Balancer             Load Balancer
            |                          |
       +----+-----+               +----+-----+
       |          |               |          |
       v          v               v          v
     App 1      App 2           App 1      App 2
       |          |               |          |
       +----------+---------------+----------+
                  |
             Event Platform
                  |
          +-------+-------+
          |               |
          v               v
      Kafka Primary    Kafka DR
          |               |
          +------->-------+
                  |
                  v
            DATABASE
          +----------+
          | Primary  |
          +----+-----+
               |
        Replication
               |
               v
          +----------+
          | DR DB    |
          +----------+

               +

        BACKUP / DATA LAKE
               |
        +------+------+
        |             |
        v             v
     Backup       PITR Backup

               +

        MONITORING
             |
      +------+------+
      |             |
      v             v
   Alerts       DR Metrics

               +

       DR ORCHESTRATOR
             |
      +------+------+
      |             |
      v             v
   Failover      Recovery
   Workflow      Workflow
```

---

# 21. The DR Failover Story

For an interview, tell the story like this:

```text
REGION A
   |
   | Disaster
   v
DETECT
   |
   v
DECLARE
   |
   v
STOP / FENCE PRIMARY
   |
   v
CHECK REPLICATION
   |
   v
PROMOTE DR DATABASE
   |
   v
START / SCALE DR SERVICES
   |
   v
VERIFY KAFKA + DEPENDENCIES
   |
   v
SWITCH TRAFFIC
   |
   v
RUN BUSINESS VALIDATION
   |
   v
OPEN TRAFFIC
   |
   v
MONITOR
```

Then:

```text
DR becomes PRIMARY
        |
        v
Rebuild original region
        |
        v
Validate data
        |
        v
Replicate back
        |
        v
Controlled failback
```

---

# 22. The 10 Questions to Remember in an Interview

If a CTO says:

> **“Design disaster recovery for our payment platform.”**

Walk through these questions:

```text
Q1. What are we protecting?
        ↓
Business services + data + dependencies

Q2. What is the business RTO?
        ↓
How quickly must we recover?

Q3. What is the business RPO?
        ↓
How much data loss is acceptable?

Q4. What failures are in scope?
        ↓
Server / DB / DC / Region / dependency

Q5. What DR strategy?
        ↓
Backup / Pilot / Warm / Active-Active

Q6. How is data replicated?
        ↓
DB + Kafka + Object Storage

Q7. How do we prevent split-brain?
        ↓
Fencing + leader/single-writer control

Q8. How do we handle in-flight transactions?
        ↓
Idempotency + status inquiry + reconciliation

Q9. How do we fail over?
        ↓
Detect → Fence → Promote → Route → Validate

Q10. How do we know DR actually works?
        ↓
Regular DR drills + measured RTO/RPO
```

---

# 23. The Mental Model — Remember These 7 Words

You don't need to memorize the entire architecture.

Remember:

```text
              DISASTER RECOVERY

                 BUSINESS
                    |
                    v
                 RTO / RPO
                    |
                    v
               REPLICATION
                    |
                    v
                FAILOVER
                    |
                    v
                VALIDATION
                    |
                    v
                 RECOVERY
                    |
                    v
                  TEST
```

And remember these **7 architectural principles**:

```text
1. RTO/RPO DRIVE THE DESIGN

2. HA ≠ DR

3. REPLICATION ≠ BACKUP

4. DATABASE IS THE CRITICAL ASSET

5. DESIGN FOR IN-FLIGHT TRANSACTIONS

6. PREVENT SPLIT-BRAIN

7. DR IS NOT REAL UNTIL IT IS TESTED
```

---

# CTO Interview — One-Sentence Answer

> **“I would design DR starting from business-defined RTO/RPO, then choose the appropriate multi-region topology, continuously replicate critical state, protect against split-brain and duplicate processing, automate controlled failover, validate financial consistency before reopening traffic, maintain independent backups, and regularly test the actual recovery process against measurable RTO/RPO targets.”**

This gives you a **strong 8-minute opening answer**, after which the CTO can drill into database replication, Kafka, Kubernetes, DNS, networking, consistency, or financial transaction recovery.
