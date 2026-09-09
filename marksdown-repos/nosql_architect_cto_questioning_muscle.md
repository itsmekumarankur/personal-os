# NoSQL System Design — Architect & CTO Questioning Muscle

## Purpose

Build the **questioning muscle** required to think like a Senior Architect, Principal Architect, or CTO.

The exercise is deliberately question-driven:

- Do not memorize textbook answers.
- Ask the next question that exposes the hidden assumption.
- Connect questions across multiple lenses.
- Think about failure, trade-offs, scale, cost, security, customer impact, product requirements, and business risk.
- Progress from architect-level thinking to CTO-level thinking.
- The objective is not merely to know NoSQL, but to learn **how to ask the right architectural question at the right time**.

---

# Set 1 of 5 — Architect Fundamentals

## Scenario

You are designing the data layer for a high-scale Wealth platform.

Requirements:

1. A customer can have thousands of transactions.
2. Most queries are:
   - Get all transactions for customer X
   - Get customer's latest 20 transactions
   - Get transactions between two dates
3. One IPO/scheme can suddenly receive traffic from hundreds of thousands of customers simultaneously.
4. The system must scale horizontally.
5. Transaction history is important, but the customer-facing dashboard can tolerate a small amount of temporary staleness.

Do not jump directly to:

> "I'll use Cassandra/MongoDB/DynamoDB."

Think like an architect.

---

## Q1.1 — Access Pattern

Before choosing the database, what questions would you ask the product/business team to understand the access patterns completely?

---

## Q1.2 — Data Model

Based on the stated queries, what would you choose as:

```text
Partition Key = ?
Sort Key      = ?
```

And why?

---

## Q1.3 — Partitioning

Suppose you choose:

```text
customer_id → partition
created_at  → sort
```

What happens when one customer becomes extremely large?

More importantly:

> How would you determine whether this design will actually distribute the workload well?

---

## Q1.4 — Hot Partition

Now change the problem:

```text
IPO = ABC123

500,000 customers
        ↓
all accessing ABC123
        ↓
same logical key
        ↓
🔥 HOT PARTITION
```

Would simply adding 50 more database nodes solve the problem?

Why or why not?

---

## Q1.5 — CTO Question

Imagine your engineering team says:

> "Let's use NoSQL because it is faster and horizontally scalable."

As CTO, what questions would you ask them before approving that decision?

---

# Set 2 of 5 — Distributed NoSQL Thinking

This set moves from:

**data modeling → replication → consistency → failure → business impact**

---

## Scenario

You have chosen a distributed NoSQL database.

```text
                    ┌──────────────┐
                    │   Clients    │
                    └──────┬───────┘
                           │
                     ┌─────▼─────┐
                     │ API Layer │
                     └─────┬─────┘
                           │
              ┌────────────▼────────────┐
              │      NoSQL Cluster      │
              │                         │
              │  Node A   Node B Node C │
              │     \       |      /    │
              │       Replicas           │
              └─────────────────────────┘
```

Your transaction data is replicated across multiple nodes.

---

## Q2.1 — Start With the Business Question

A customer submits a transaction.

```text
Client
  │
  ▼
Write Transaction
  │
  ├── Node A
  ├── Node B
  └── Node C
```

Before deciding how many replicas you need, what questions should an architect ask?

Think about:

- durability
- availability
- latency
- regulatory/business requirements
- acceptable data loss

---

## Q2.2 — Consistency Decision

Product says:

> "When a customer completes a transaction, the transaction should immediately appear in the portfolio."

Another team says:

> "We don't want writes to become slow. A little temporary inconsistency is acceptable."

You now have a tension:

```text
Strong consistency
       ↕
Availability
       ↕
Latency
```

What questions would you ask to determine the right consistency model?

Do not simply answer "strong" or "eventual."

---

## Q2.3 — Quorum Thinking

Suppose:

```text
Replication Factor = 3

N = 3
W = 2
R = 2
```

You are told:

> "Since W + R > N, we are guaranteed to always get the latest value."

Would you accept that statement in a production architecture review?

What assumptions would you challenge?

What additional questions would you ask around:

```text
W = ?
R = ?
N = ?
```

---

## Q2.4 — Failure Scenario

Node B suddenly fails:

```text
             Node A ✓
              /   \
Client ──────      Node B ✗
              \   /
             Node C ✓
```

The system continues accepting writes.

Node B comes back 6 hours later.

Ask:

1. Where did the writes go while B was down?
2. How does B discover what it missed?
3. Could B contain stale data?
4. Who repairs it?
5. How do you know repair actually succeeded?
6. What happens if another node fails during repair?

---

## Q2.5 — CTO Escalation

Incident:

> Due to a replication/consistency problem, 0.1% of customer portfolio views showed stale transaction data for 15 minutes.

The system technically remained "available."

But customers saw incorrect portfolio values.

As CTO, what would you investigate first?

Think beyond infrastructure.

Question chain:

```text
Customer impact
      ↓
Business impact
      ↓
Data correctness
      ↓
Consistency model
      ↓
Failure mode
      ↓
Detection
      ↓
Recovery
      ↓
Prevention
      ↓
Cost
```

---

# Set 3 of 5 — Storage Engine, Performance & Scaling

Now move from:

**distributed behavior → what is happening underneath the database**

The goal is to train yourself to ask:

> "Why is this system becoming slow, and what question should I ask next?"

---

## Scenario

Production data:

```text
Day 1          1 TB
Year 1        50 TB
Year 2       300 TB

Writes:   100K/sec
Reads:    300K/sec
```

Initially everything was fine.

Now:

```text
p50 latency  →  10 ms
p95 latency  →  80 ms
p99 latency  →  900 ms
```

The team says:

> "We need bigger machines."

Do not accept that yet.

---

## Q3.1 — First Architect Question

Before changing infrastructure, what questions would you ask to identify where the latency is actually coming from?

Build the investigation chain:

```text
Request
   ↓
API
   ↓
DB client
   ↓
Network
   ↓
Partition
   ↓
Storage engine
   ↓
Disk / Memory / Cache
```

What would you measure at each stage?

---

## Q3.2 — LSM-Tree Thinking

Your database uses an LSM-tree style storage engine:

```text
             Writes
                │
                ▼
           MemTable
                │
             Flush
                ▼
              SSTable
                │
        ┌───────┴────────┐
        ▼                ▼
     SSTable          SSTable
        │                │
        └───────┬────────┘
                ▼
           Compaction
```

The database team says:

> "Reads are becoming slower because we have too many SSTables."

Do not immediately accept "increase compaction."

Ask:

- Why are there many SSTables?
- What is the write amplification?
- What is the read amplification?
- Is compaction consuming CPU?
- Is compaction consuming disk I/O?
- Is there enough disk bandwidth?
- What happens to latency while compaction runs?
- What is the impact of the compaction strategy?

---

## Q3.3 — The Hidden Trade-off

Team proposes:

> "Let's run aggressive compaction so reads become faster."

Trade-off:

```text
More compaction
      │
      ├──► Fewer SSTables
      │        ↓
      │     Better reads
      │
      └──► More I/O
               ↓
          More CPU/disk
               ↓
          Worse writes
```

What questions would you ask before approving aggressive compaction?

---

## Q3.4 — Indexing Problem

Data contains:

```text
customer_id
transaction_id
created_at
scheme_id
status
amount
```

Queries include:

```text
customer_id + created_at
scheme_id + status
status + created_at
amount > X
```

Developer says:

> "The query is slow. Let's add an index."

Would you allow indexes for all these queries?

What questions would you ask first?

Think about:

```text
Read performance
       ↕
Write performance
       ↕
Storage
       ↕
Maintenance
       ↕
Cardinality
       ↕
Query frequency
```

---

## Q3.5 — Hot Partition Investigation

Production:

```text
Partition 1 → 5K requests/sec
Partition 2 → 4K requests/sec
Partition 3 → 6K requests/sec
Partition 4 → 500K requests/sec 🔥
Partition 5 → 3K requests/sec
```

Average cluster CPU is only 35%.

Team says:

> "We still have plenty of capacity."

Do you agree?

What questions would you ask?

Most importantly:

> Why can a cluster be only 35% utilized while one partition is completely overloaded?

---

## Q3.6 — CTO-Level Decision

VP Engineering proposes:

> "Let's double the database cluster from 50 nodes to 100 nodes."

Before approving the additional infrastructure cost, what questions would you ask?

Question chain:

```text
Observed symptom
      ↓
Root cause
      ↓
Scaling bottleneck
      ↓
Architecture limitation
      ↓
Possible solutions
      ↓
Operational complexity
      ↓
Cost
      ↓
Customer impact
      ↓
Long-term scalability
```

---

# Set 4 of 5 — Failure, Recovery, Transactions & Operational Resilience

Now ask:

> "What happens when the system behaves badly?"

A CTO doesn't just ask:

> "Does it work?"

They ask:

> "How does it fail, how fast do we detect it, and what happens to the business while it is failing?"

---

## Scenario

You operate:

```text
                  ┌───────────────┐
                  │   API Layer   │
                  └───────┬───────┘
                          │
             ┌────────────▼────────────┐
             │      NoSQL Cluster      │
             │                         │
             │ A      B      C      D  │
             │ │      │      │      │  │
             │ └──────┴──────┴──────┘  │
             └─────────────────────────┘
```

Replication factor = 3.

System processes:

```text
200K writes/sec
600K reads/sec
```

---

## Q4.1 — Failure Taxonomy

First ask:

> "What exactly can fail?"

Failure tree:

```text
Database failure
      │
      ├── Node failure
      ├── Disk failure
      ├── Network failure
      ├── AZ failure
      ├── Region failure
      ├── Software failure
      ├── Configuration failure
      └── Human/operator failure
```

What other failure scenarios would you add?

For each failure, ask:

> Is this a failure of availability, consistency, durability, or correctness?

---

## Q4.2 — Network Partition

Imagine:

```text
             Network Partition
                    │
        ┌───────────┴───────────┐
        │                       │
     Node A                  Node B
     Node C                  Node D
```

Both sides believe they are healthy.

Both continue accepting writes.

Potentially:

```text
Customer X
    │
    ├── Side A → Balance = ₹10,000
    │
    └── Side B → Balance = ₹12,000
```

What questions should you ask to determine whether your NoSQL system can safely handle this?

Think about:

- split brain
- conflict resolution
- consistency
- quorum
- availability
- write acceptance
- reconciliation

Then ask:

> Which business data can tolerate conflict, and which data absolutely cannot?

---

## Q4.3 — Rebalancing

A new node is added:

```text
Before:

A ─ B ─ C ─ D

After:

A ─ B ─ C ─ D ─ E
```

Database needs to redistribute partitions.

Team says:

> "Rebalancing is automatic, so there is nothing to worry about."

Would you accept this?

What questions would you ask about:

```text
Data movement
     ↓
Network bandwidth
     ↓
Disk I/O
     ↓
CPU
     ↓
Existing traffic
     ↓
Latency
     ↓
Failure during movement
```

Now make it harder:

> What happens if the node being used as the source of the data fails halfway through rebalancing?

---

## Q4.4 — Disaster Recovery

Primary region goes down:

```text
        REGION A ❌
             │
             X
             │
        REGION B
             │
          Clients
```

Business says:

> "We need zero data loss and zero downtime."

Instead of saying "Yes, we'll build multi-region replication", ask the business:

```text
RPO
 ↓
RTO
 ↓
Consistency
 ↓
Replication
 ↓
Failover
 ↓
Data loss
 ↓
Recovery
 ↓
Cost
```

If they demand RPO = 0 and RTO = 0, what architectural questions immediately arise?

---

## Q4.5 — Transactions

New requirement:

```text
Debit ₹1,00,000
       +
Create Investment
       +
Update Portfolio
       +
Record Transaction
```

Team says:

> "NoSQL doesn't need transactions. We'll just use events."

Failure:

```text
Debit Account        ✓
Create Investment    ✓
Update Portfolio     ✗
Record Transaction   ✗
```

Customer has been debited, but the investment doesn't appear.

As architect, what questions do you ask?

Think about:

```text
Atomicity
Consistency
Idempotency
Retry
Ordering
Duplicate events
Partial failure
Compensation
Reconciliation
```

Then ask:

> Does this business operation actually require ACID semantics, or can the business tolerate eventual consistency?

How would you determine that?

---

## Q4.6 — TTL and Data Lifecycle

Database stores temporary data:

```text
Session
OTP metadata
Temporary portfolio calculations
Cache-like records
```

Team proposes:

> "We'll use TTL everywhere."

What questions should you ask before approving that?

Consider:

- storage reclamation
- deletion guarantees
- tombstones
- compaction
- read behavior
- compliance
- audit requirements
- accidental deletion
- recovery

Reverse the problem:

> What happens if a regulator says transaction records must be retained for 10 years, but your database schema has TTL enabled?

What architectural/governance questions should immediately come to mind?

---

## Q4.7 — CTO Incident Question

At 2:00 AM:

```text
Replication lag increasing
        ↓
Read latency increasing
        ↓
Timeouts increasing
        ↓
Retries increasing
        ↓
Write load increasing
        ↓
Cluster becoming unstable
```

Engineering team starts restarting nodes.

As CTO, would you allow that?

What questions would you ask before anyone touches production?

Chain:

```text
Symptom
  ↓
Is it real?
  ↓
Scope
  ↓
Blast radius
  ↓
Root cause
  ↓
Safe mitigation
  ↓
Customer impact
  ↓
Data correctness
  ↓
Recovery
  ↓
Permanent fix
```

---

# Set 5 of 5 — CTO-Level NoSQL Architecture

Final level:

> "If I own this platform as CTO, what questions must I ask before accepting this architecture?"

Now connect:

**product → architecture → scale → reliability → security → cost → organization → long-term strategy**

---

# Q5 — You Are the CTO

You are building a high-scale financial platform.

Current scale:

```text
Customers              20 Million
Transactions/day       200 Million
Peak writes             100K/sec
Peak reads              500K/sec
Data                    300 TB
Regions                 2
Availability target     99.99%
```

Architecture proposal:

```text
                  ┌─────────────┐
                  │   Clients   │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │ API Gateway │
                  └──────┬──────┘
                         │
              ┌──────────▼──────────┐
              │    Application      │
              │      Services       │
              └──────────┬──────────┘
                         │
                  ┌──────▼──────┐
                  │   NoSQL DB  │
                  │             │
                  │ Partitions  │
                  │ Replicas    │
                  │ Indexes     │
                  └─────────────┘
```

Architecture team says:

> "This architecture will scale. We should approve it."

You are not convinced.

---

## Q5.1 — CTO Starts With "Why?"

Before discussing database technology, what questions do you ask?

Think:

```text
What business problem?
        ↓
What workloads?
        ↓
What access patterns?
        ↓
What scale?
        ↓
What consistency?
        ↓
What availability?
        ↓
What durability?
        ↓
What compliance?
```

### Task

Give the 10 most important questions you would ask the architecture team before approving the NoSQL decision.

---

## Q5.2 — Product vs Architecture

Product:

> "Customers must see their portfolio immediately after every transaction."

Engineering:

> "Eventual consistency is cheaper and more scalable."

Compliance:

> "Financial records must never be lost."

Operations:

> "The system must survive a complete region failure."

Finance:

> "Infrastructure cost must stay within budget."

Competing requirements:

```text
             ┌──────────────┐
             │   Product    │
             │  UX/Latency  │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │ Architecture │
             └──────┬───────┘
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Reliability   Security      Cost
```

### CTO question

How do you turn these conflicting statements into measurable architectural requirements?

Ask around:

```text
RPO
RTO
p95 / p99 latency
Availability
Consistency
Durability
Cost/request
Data retention
```

Then:

> Which should be hard requirements versus negotiable trade-offs?

---

## Q5.3 — Multi-Region Architecture

Architecture proposes active-active:

```text
              Global Traffic
                    │
           ┌────────┴────────┐
           ▼                 ▼
       Region A           Region B
           │                 │
        NoSQL              NoSQL
           │                 │
           └───────┬─────────┘
                   │
              Replication
```

Scenario:

```text
Customer → Region A → Write ₹10,000

simultaneously

Customer → Region B → Write ₹12,000
```

Ask:

- What is the source of truth?
- Who wins?
- Can both writes succeed?
- How are conflicts resolved?
- Can the application make decisions based on stale data?
- What happens when regions reconnect?

### Cost dimension

What questions would you ask about active-active cost?

```text
Replication traffic
+
Cross-region bandwidth
+
Duplicate infrastructure
+
Operational complexity
+
Conflict resolution
+
Testing
+
On-call burden
```

Would active-active still be your default?

Why?

---

## Q5.4 — Security

Architecture:

```text
Application
     │
     ▼
   NoSQL
     │
 ┌───┴────────┐
 ▼            ▼
Customer     Transaction
Data         Data
```

Team says:

> "Database access is restricted to the application network."

Build your NoSQL security questioning chain:

```text
Who can access?
      ↓
What can they access?
      ↓
How is access authenticated?
      ↓
How is authorization enforced?
      ↓
How is data encrypted?
      ↓
How are keys managed?
      ↓
How is access audited?
      ↓
How are suspicious activities detected?
```

Financial-domain concerns:

- PII
- financial transactions
- encryption at rest
- encryption in transit
- auditability
- least privilege
- backup security
- replica security
- data deletion
- privileged access

### Critical question

> If an engineer accidentally gets read access to the production NoSQL cluster, what prevents them from reading 20 million customers' data?

---

## Q5.5 — Cost Architecture

Proposal:

```text
100 database nodes
+
3 replicas
+
2 regions
+
multiple indexes
+
cross-region replication
+
large SSDs
```

Finance asks:

> "Why is our database bill so high?"

Architect responds:

> "Because we need scale."

Reject that answer.

### Questions

What questions determine the actual cost drivers?

Think:

```text
Compute
Storage
IOPS
Network
Replication
Indexes
Backups
Cross-region traffic
Compaction
Operational overhead
```

Then:

> What is the cost of one additional read/write at scale?

And:

> Which architectural decision is responsible for the largest part of the bill?

---

## Q5.6 — Vendor Lock-In

Team recommends a managed NoSQL database.

CTO asks:

> "What happens if the vendor increases pricing by 40%?"

Architecture says:

> "We can migrate later."

Do not accept that.

Questions:

```text
Data model
     ↓
Query model
     ↓
Proprietary APIs
     ↓
Operational tooling
     ↓
Data export
     ↓
Migration time
     ↓
Downtime
     ↓
Dual-write strategy
     ↓
Validation
     ↓
Rollback
```

Then the bigger CTO question:

> Is vendor lock-in always bad?

When might paying for a managed proprietary service actually be the correct strategic decision?

---

## Q5.7 — The 10x Growth Question

Today:

```text
200 Million transactions/day
```

Business expects:

> 10x growth in three years.

Don't simply multiply today's infrastructure by 10.

Ask what changes:

```text
Data volume
        ↓
Partition count
        ↓
Hot keys
        ↓
Rebalancing
        ↓
Replication
        ↓
Backup duration
        ↓
Recovery time
        ↓
Compaction
        ↓
Operational complexity
        ↓
Cost
```

Then:

> Which part of the architecture will fail first at 10x?

How would you prove your answer rather than guess?

---

## Q5.8 — CTO Incident Simulation

At 10:15 AM:

```text
p99 latency ↑
     ↓
timeouts ↑
     ↓
retries ↑
     ↓
writes ↑
     ↓
hot partitions
     ↓
replication lag ↑
     ↓
customer complaints
```

At 10:25 AM:

```text
One AZ fails.
```

At 10:30 AM:

```text
Traffic shifts to remaining AZs.
```

At 10:35 AM:

```text
Remaining nodes become overloaded.
```

At 10:40 AM:

```text
Some customers see stale portfolio information.
```

### You are in the war room.

What questions do you ask in the first 5 minutes?

Not solutions.

Questions.

Build and extend:

```text
What is happening?
        ↓
How many customers?
        ↓
Which operations?
        ↓
Which regions/AZs?
        ↓
Is data being lost?
        ↓
Is data incorrect?
        ↓
Can we safely accept writes?
        ↓
Can we reduce traffic?
        ↓
Can we fail over?
        ↓
What is the safest mitigation?
```

---

# Q5.9 — The Ultimate Architecture Review

Architecture team asks:

> "Can we approve this NoSQL architecture?"

Before saying yes, what questions must you answer?

Build your own **CTO Architecture Review Checklist**.

Categories:

```text
1. Business
2. Product
3. Data model
4. Access patterns
5. Partitioning
6. Consistency
7. Replication
8. Failure
9. Disaster recovery
10. Performance
11. Storage engine
12. Indexing
13. Transactions
14. Security
15. Compliance
16. Observability
17. Cost
18. Vendor lock-in
19. 10x scalability
20. Operational complexity
```

For each category ask:

> "What is the one question that could expose a serious architectural flaw?"

---

# Final CTO Challenge

Imagine you have only **15 minutes** with the architecture team.

You cannot ask 100 questions.

You must identify the **10 questions with the highest information value**.

## Task

What are your 10 questions?

Order them:

```text
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.
```

Base the ordering on what you would ask **first as CTO**.

---

# The Core Skill

The real skill is not knowing the most answers.

It is knowing:

> **Which question should I ask next?**

A strong questioning chain looks like:

```text
Requirement
    ↓
Why?
    ↓
Workload?
    ↓
Access pattern?
    ↓
Data model?
    ↓
Partitioning?
    ↓
Scale?
    ↓
Failure mode?
    ↓
Consistency?
    ↓
Customer impact?
    ↓
Business impact?
    ↓
Cost?
    ↓
Security?
    ↓
Operational risk?
    ↓
Long-term scalability?
    ↓
What decision should we make?
```

The progression is:

```text
Engineer
   ↓
Senior Engineer
   ↓
Architect
   ↓
Principal Architect
   ↓
CTO
```

The higher you go, the less the question is:

> "How does the database work?"

and the more it becomes:

> **"What assumption are we making, what happens when it fails, who is affected, what does it cost, and is this the right business decision?"**
