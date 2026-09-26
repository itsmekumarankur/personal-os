# Payment Reconciliation System — 8-Minute Architecture Guide

> **Goal:** Design a payment reconciliation platform that can ingest financial records from many systems, match them accurately, identify exceptions, and provide a complete audit trail.

The easiest way to understand this system is to **think like an architect asking questions in sequence**.

---

# 1. First Question: What problem are we actually solving?

### What this teaches
This establishes the **business problem before jumping into Kafka, databases, or microservices**.

### Why needed
Reconciliation is fundamentally about answering:

> **“Do all systems agree about the money?”**

Imagine one payment:

```text
Customer
   |
   v
Payment Platform
₹1,000
TXN123
   |
   +--------------------+
   |                    |
   v                    v
Gateway              Bank
₹1,000               ₹1,000
   |                    |
   v                    v
Settlement File      Bank Statement
```

We need to prove:

```text
Our System      Gateway       Bank
₹1,000          ₹1,000        ₹1,000
TXN123          GW987         BANK456

        ============
        MATCHED
        ============
```

But real life looks like:

```text
Internal System
TXN123 | ₹1,000 | 10:01 AM | SUCCESS

Gateway
GW987  | ₹1,000 | 10:03 AM | CAPTURED

Bank
BANK456 | ₹999 | 11:30 AM | SETTLED
```

Now:

```text
                Reconciliation
                       |
             +---------+---------+
             |                   |
          Matched             Exception
                               |
                    +----------+----------+
                    |          |          |
                 Amount      Missing    Status
                 mismatch   record     mismatch
```

So reconciliation is essentially a **financial consistency engine across independent systems**.

---

# 2. Question: What does the high-level architecture look like?

### What this teaches
You learn how to divide a large reconciliation system into **independent scalable components**.

### Why needed
Different sources have different:

- formats
- APIs
- file structures
- identifiers
- delivery mechanisms
- timing

Therefore we should **normalize everything into a common financial transaction model**.

```text
                   EXTERNAL SOURCES
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
   Payment Gateway     Banks        Merchant Files
        |                |                |
        +----------------+----------------+
                         |
                         v
                 +---------------+
                 | Ingestion     |
                 | Layer         |
                 +---------------+
                         |
                         v
                 +---------------+
                 | Raw Transaction|
                 | Store          |
                 +---------------+
                         |
                         v
                 +---------------+
                 | Normalization |
                 +---------------+
                         |
                         v
                 +---------------+
                 | Reconciliation|
                 | Engine        |
                 +---------------+
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
          MATCHED    EXCEPTION    DUPLICATE
             |           |           |
             +-----------+-----------+
                         |
                         v
                +------------------+
                | Investigation /  |
                | Resolution       |
                +------------------+
                         |
             +-----------+-----------+
             |                       |
             v                       v
        Reports/Dashboards       Audit Store
```

---

# 3. Question: How do we ingest data from completely different systems?

### What this teaches
You learn the **Source → Adapter → Canonical Model** pattern.

### Why needed
One gateway may send:

```json
{
  "paymentId": "ABC123",
  "amount": 1000,
  "status": "CAPTURED"
}
```

Another may send:

```text
GW_TXN=XYZ999
AMT=1000.00
STATE=SUCCESS
```

A bank may provide:

```text
Date | Ref | Credit | Description
```

We don't want reconciliation logic understanding all these formats.

Instead:

```text
Gateway A --------\
Gateway B ---------\
Bank API ------------> Source Adapters ---> Canonical Transaction
Bank File ----------/
Merchant File ------/
```

Each adapter does:

```text
External Format
      |
      v
Parse
      |
      v
Validate
      |
      v
Normalize
      |
      v
Canonical Model
```

For example:

```text
Gateway
GW123
₹1,000
CAPTURED
10:02

        |
        v

Canonical Transaction

transaction_id = INT123
external_id    = GW123
amount         = 100000 paise
currency       = INR
status         = CAPTURED
transaction_ts = ...
source         = GATEWAY_A
```

### Important architectural decision

Keep the **raw record immutable**.

```text
Raw Data
   |
   +---- NEVER MODIFY
   |
   v
Normalized Data
   |
   v
Reconciliation
```

This becomes extremely important during audits.

---

# 4. Question: How do we avoid processing the same transaction twice?

### What this teaches
This introduces **idempotency**, one of the most important concepts in payment architecture.

### Why needed

Suppose the gateway sends:

```text
TXN123
₹1000
```

Then network failure occurs.

Our system doesn't know whether processing succeeded.

Gateway retries:

```text
TXN123
₹1000
```

If we blindly process both:

```text
₹1000
+
₹1000
=
₹2000
```

Financial disaster.

Therefore:

```text
Incoming Event
      |
      v
+-------------+
| Idempotency |
| Check       |
+-------------+
      |
      +---- Already processed ---> Ignore
      |
      +---- New -----------------> Process
```

Use a unique business key such as:

```text
source + external_transaction_id
```

Example:

```text
GATEWAY_A:GW123
```

Database constraint:

```text
UNIQUE(source, external_transaction_id)
```

The key principle:

> **At-least-once delivery + idempotent processing is usually safer than trying to build an exactly-once distributed system.**

---

# 5. Question: How do we actually match transactions?

### What this teaches
This is the **core reconciliation algorithm**.

### Why needed
Identifiers are often different.

```text
Internal     Gateway       Bank
---------    --------      --------
INT123       GW789         BANK456
```

So we need multiple matching strategies.

## Level 1 — Exact Match

Try strongest identifiers first.

```text
Internal.gateway_reference
          =
Gateway.gateway_reference
```

If:

```text
ID       = same
Amount   = same
Currency = same
```

Then:

```text
              MATCH
```

## Level 2 — Composite Match

If IDs differ:

```text
Merchant ID
+
Amount
+
Currency
+
Transaction Date
```

Example:

```text
Merchant = M123
Amount   = ₹1000
Date     = 16-Sep

             +
Gateway record
```

## Level 3 — Fuzzy/Temporal Match

Sometimes timestamp differs.

```text
Internal: 10:01:10
Gateway : 10:02:03
Bank    : 10:15:20
```

Use a configurable time window:

```text
Internal transaction
       |
       | ± 30 minutes
       |
       +---- Gateway candidate
```

But **never allow uncontrolled fuzzy matching** for financial records.

---

# 6. Question: Should matching be one rule?

### What this teaches
You learn why reconciliation should use a **rule hierarchy**, rather than one giant matching algorithm.

### Why needed

A practical hierarchy:

```text
             Incoming Record
                    |
                    v
          +--------------------+
          | Exact ID Match     |
          +--------------------+
                    |
              not found
                    |
                    v
          +--------------------+
          | Composite Match    |
          +--------------------+
                    |
              not found
                    |
                    v
          +--------------------+
          | Time + Amount      |
          +--------------------+
                    |
              not found
                    |
                    v
               UNMATCHED
```

Each rule should produce:

```text
match_rule = EXACT_ID
confidence = HIGH
```

or:

```text
match_rule = AMOUNT_DATE_MERCHANT
confidence = MEDIUM
```

For high-value transactions, you may require stricter matching.

---

# 7. Question: What transaction states do we need?

### What this teaches
You learn to model reconciliation as a **state machine**, not simply `matched=true/false`.

### Why needed
Payments have complex lifecycles.

```text
INITIATED
    |
    v
AUTHORIZED
    |
    v
CAPTURED
    |
    v
SETTLED
```

But there can also be:

```text
CAPTURED
   |
   +----> REFUNDED
   |
   +----> CHARGEBACK
   |
   +----> REVERSED
```

And reconciliation states:

```text
             RECONCILIATION STATUS

                    |
       +------------+------------+
       |            |            |
       v            v            v
    MATCHED      UNMATCHED    DUPLICATE
       |
       v
  AMOUNT_MISMATCH
```

Do **not** confuse:

```text
Payment Status = SUCCESS
```

with:

```text
Reconciliation Status = AMOUNT_MISMATCH
```

---

# 8. Question: How do we handle refunds, partial payments and chargebacks?

### What this teaches
You learn why a **transaction should be modeled as a financial event/ledger relationship**, rather than simply overwriting one payment row.

### Why needed

Suppose:

```text
Original Payment
₹1,000
```

Refund:

```text
₹300
```

Remaining:

```text
₹700
```

Don't change:

```text
original_amount = ₹700
```

Instead:

```text
Payment
₹1,000
  |
  +------ Refund ₹300
  |
  +------ Net ₹700
```

Similarly:

```text
Payment ₹1000
      |
      +---- Partial Refund ₹200
      |
      +---- Partial Refund ₹300
      |
      +---- Chargeback ₹100
```

The reconciliation engine can calculate:

```text
Original
- Refunds
- Chargebacks
+ Reversals
----------------
Net Financial Position
```

This gives us a proper **financial event chain**.

---

# 9. Question: What happens when data arrives late?

### What this teaches
You learn an important distributed-systems concept:

> **Event time ≠ processing time**

### Why needed

Our system receives:

```text
T0       T1        T2
 |        |         |
Internal Gateway   Bank
  |        |         |
  +--------+---------+
           |
           v
       Reconcile
```

So don't immediately declare:

```text
BANK RECORD MISSING
```

Instead:

```text
UNMATCHED
   |
   v
WAITING_FOR_SOURCE
   |
   +---- data arrives ---> REPROCESS
```

Use configurable reconciliation windows:

```text
T + 0 day
   |
T + 1 day
   |
T + 2 day
   |
T + N day
```

After the defined window:

```text
OPEN EXCEPTION
```

---

# 10. Question: What database model should we use?

### What this teaches
You learn the separation between **transaction data, reconciliation results and audit history**.

### Why needed
Financial systems require traceability.

A simplified model:

```text
TRANSACTION
----------------------
transaction_id
merchant_id
amount
currency
status
transaction_time
source
external_reference
```

```text
RECONCILIATION
----------------------
reconciliation_id
transaction_id
recon_run_id
status
match_rule
matched_transaction_id
difference_amount
created_at
```

```text
RECON_EXCEPTION
----------------------
exception_id
transaction_id
exception_type
amount_difference
status
assigned_to
resolution
resolved_at
```

```text
AUDIT_EVENT
----------------------
event_id
entity_id
entity_type
action
old_value
new_value
actor
timestamp
reason
```

---

# 11. Question: Why separate the audit trail?

### What this teaches
You learn **immutability and financial auditability**.

### Why needed

Imagine an operator changes:

```text
₹1,000
```

to:

```text
₹900
```

You cannot simply update the database and lose the original state.

Instead:

```text
AUDIT LOG

10:01 SYSTEM
Created transaction ₹1000

10:10 SYSTEM
Marked AMOUNT_MISMATCH

10:30 USER: Rahul
Changed exception status

10:35 USER: Rahul
Resolution = Gateway fee difference
```

Think:

```text
             Business DB
                 |
                 |
                 v
           Audit Events
                 |
                 v
        Immutable History
```

For stronger controls, audit storage can be append-only/WORM-oriented.

---

# 12. Question: How does manual investigation work?

### What this teaches
You learn how to combine **automation + human workflow**.

### Why needed
Not every financial exception can be resolved automatically.

Example:

```text
                    Exception Queue
                          |
       +------------------+----------------+
       |                  |                |
       v                  v                v
Amount mismatch       Missing          Duplicate
       |                  |                |
       v                  v                v
Investigator
       |
       +---- Review transactions
       |
       +---- View raw records
       |
       +---- Contact gateway/bank
       |
       +---- Add resolution
       |
       v
       RESOLVED
```

Important:

```text
Operator
   |
   v
Cannot directly modify transaction
```

Instead:

```text
Operator
   |
   v
Resolution Action
   |
   v
Validated Workflow
   |
   v
Audit Event
```

This prevents unauthorized financial manipulation.

---

# 13. Question: What if Kafka or the reconciliation service fails?

### What this teaches
You learn **fault tolerance and recovery**.

### Why needed
Financial reconciliation cannot lose data because one service crashes.

Architecture:

```text
Source
  |
  v
Kafka
  |
  +----------------+
  |                |
Consumer A      Consumer B
  |                |
  v                v
Normalize       Archive
  |
  v
Reconciliation
```

If reconciliation crashes:

```text
Kafka
 |
 v
Message remains
 |
 v
Service restarts
 |
 v
Process again
```

Because processing is idempotent:

```text
Process
   |
   v
Already processed?
   |
  YES
   |
   v
Skip safely
```

---

# 14. Question: How do we scale to billions of transactions?

### What this teaches
You learn **horizontal scalability and partitioning**.

### Why needed
Suppose:

```text
10 million transactions/day
```

A single reconciliation service becomes a bottleneck.

Instead:

```text
                  Kafka
                    |
       +------------+------------+
       |            |            |
    Partition 1  Partition 2  Partition 3
       |            |            |
       v            v            v
    Worker 1     Worker 2     Worker 3
```

Scale horizontally:

```text
100M records

        |
        v

Partition by:
merchant / date / transaction_id

        |
        +---- Worker 1
        +---- Worker 2
        +---- Worker 3
        +---- ...
        +---- Worker N
```

Database strategy:

```text
                DB
                 |
       +---------+---------+
       |                   |
   Partition            Index
   by date              transaction_id
```

For very large datasets:

```text
Hot Data
   |
   v
Operational DB

Old Data
   |
   v
Object Storage / Data Lake
```

---

# 15. Question: What consistency model should we use?

### What this teaches
This is one of the most important architecture decisions.

### Why needed

Not every part of the system requires the same consistency.

### Financial transaction state

Needs strong consistency around:

```text
transaction identity
amount
currency
financial event
```

Use:

```text
ACID database transaction
+
unique constraints
+
optimistic/concurrency controls
```

### Event processing

Can use:

```text
At-least-once delivery
+
idempotent consumers
```

### Dashboard

Doesn't need strong consistency.

It can be:

```text
eventually consistent
```

So:

```text
                  Consistency

Financial State -----> STRONG
Reconciliation ------> STRONG
Audit ----------------> APPEND ONLY
Dashboard ------------> EVENTUAL
Analytics ------------> EVENTUAL
```

This is a much more practical design than trying to make the entire platform globally strongly consistent.

---

# 16. Question: What if matching happens incorrectly?

### What this teaches
You learn why **financial accuracy > matching speed**.

### Why needed

Suppose:

```text
Transaction A = ₹1000
Transaction B = ₹1000
```

Both have similar timestamps.

A careless fuzzy matcher might do:

```text
A <----> B
```

But that could be wrong.

Therefore use:

```text
High confidence
    |
    +---- Auto reconcile

Medium confidence
    |
    +---- Review queue

Low confidence
    |
    +---- Exception
```

Example:

```text
Exact transaction ID
        |
        v
   AUTO MATCH

Amount + Merchant + Date
        |
        v
  CONDITIONAL MATCH

Only timestamp similarity
        |
        v
    NO AUTO MATCH
```

A reconciliation system should be **conservative**.

False positive matching can be more dangerous than leaving something unmatched.

---

# 17. Question: How do we make reconciliation reproducible?

### What this teaches
You learn about **reconciliation runs and deterministic processing**.

### Why needed

Suppose today's reconciliation produced:

```text
1,000,000 matched
20,000 unmatched
500 amount mismatches
```

Tomorrow we may need to reproduce exactly what happened.

Create:

```text
RECON_RUN
----------------
run_id
business_date
source
rule_version
started_at
completed_at
status
```

Then:

```text
                 RECON RUN
                    |
             Rule Version 7
                    |
          +---------+---------+
          |         |         |
       Match      Exception  Duplicate
```

If rules change:

```text
Rule V7
Rule V8
```

Old results remain associated with:

```text
Rule V7
```

This is critical for auditability.

---

# 18. Question: What happens if the same reconciliation job runs twice?

### What this teaches
This combines **idempotency + deterministic processing**.

### Why needed

Scheduler accidentally starts:

```text
Run #101
Run #101
```

We should not create duplicate financial outcomes.

Use:

```text
recon_run_id
+
source
+
business_date
```

with uniqueness constraints.

```text
             Start Recon
                  |
                  v
          Run already exists?
             /          \
           YES          NO
            |            |
         Resume/       Create
         skip safely     run
```

---

# 19. Question: What operational dashboards do we need?

### What this teaches
You learn how architecture becomes **operable in production**.

### Why needed
A system processing money needs visibility.

```text
+------------------------------------------------+
|           PAYMENT RECON DASHBOARD              |
+------------------------------------------------+
| Total Transactions       10,000,000            |
| Matched                   9,850,000            |
| Unmatched                   100,000            |
| Amount Mismatch              30,000            |
| Duplicate                    10,000             |
| Pending                       10,000            |
+------------------------------------------------+
| Gateway A Success: 99.9%                       |
| Gateway B Success: 98.7%                       |
| Bank File Delay: 35 minutes                    |
+------------------------------------------------+
```

Monitor:

```text
Throughput
Latency
Match %
Exception %
Duplicate %
Missing %
Processing lag
Source availability
Kafka lag
DB latency
Failed files
```

And importantly:

```text
Financial difference amount
```

not just number of exceptions.

---

# 20. Final Architecture

Putting everything together:

```text
                       PAYMENT SOURCES
                            |
          +-----------------+------------------+
          |                 |                  |
       Gateway             Bank           Merchant
          |                 |                  |
          +-----------------+------------------+
                            |
                            v
                 +----------------------+
                 | INGESTION LAYER      |
                 | API / File / SFTP    |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 | RAW IMMUTABLE STORE  |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 | NORMALIZATION        |
                 | Canonical Model      |
                 +----------------------+
                            |
                            v
                       +---------+
                       | Kafka   |
                       +---------+
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
        Reconciliation   Archive       Analytics
          Workers
             |
             v
      +----------------+
      | Matching Engine|
      +----------------+
             |
      +------+------+------+------+
      |      |      |      |
      v      v      v      v
   MATCH  UNMATCH  DUP  MISMATCH
      |      |      |      |
      +------+------+------+
             |
             v
      Exception Workflow
             |
      +------+------+
      |             |
      v             v
   Auto Resolve  Manual Review
      |             |
      +------+------+
             |
             v
      +--------------+
      | Audit Trail  |
      +--------------+
             |
      +------+-------+
      |              |
      v              v
   Reports       Dashboards
```

---

# 21. The Architecture in 10 Questions

If you're preparing for an **architect/system-design interview**, remember the entire design through these questions:

```text
Q1. What are we reconciling?
        |
        v
Transactions across multiple financial systems

Q2. How does data enter?
        |
        v
API / Files / SFTP / Events

Q3. How do different formats become comparable?
        |
        v
Canonical transaction model

Q4. How do we prevent duplicates?
        |
        v
Idempotency + unique constraints

Q5. How do we match?
        |
        v
Exact ID
   ↓
Composite attributes
   ↓
Controlled time-window matching

Q6. What happens when things don't match?
        |
        v
Exception classification

Q7. What about refunds/chargebacks?
        |
        v
Financial event model

Q8. What if data arrives late?
        |
        v
Reconciliation window + reprocessing

Q9. How do we recover from failures?
        |
        v
Kafka + retries + DLQ + idempotent consumers

Q10. How do we prove what happened?
        |
        v
Immutable raw data
+
Versioned reconciliation runs
+
Append-only audit trail
```

---

# 22. The Core Mental Model

The whole system can be remembered as:

```text
       INGEST
          |
          v
       NORMALIZE
          |
          v
        DEDUPE
          |
          v
        MATCH
          |
          v
     CLASSIFY RESULT
          |
     +----+----+
     |         |
     v         v
  MATCHED   EXCEPTION
               |
               v
          INVESTIGATE
               |
               v
            RESOLVE
               |
               v
             AUDIT
```

And the **five architectural principles** are:

```text
1. NEVER LOSE A FINANCIAL EVENT
        ↓
2. NEVER PROCESS IT TWICE
        ↓
3. NEVER AUTO-MATCH WITH LOW CONFIDENCE
        ↓
4. NEVER DELETE AUDIT HISTORY
        ↓
5. ALWAYS BE ABLE TO REPRODUCE A RECONCILIATION RUN
```

If you can explain those five principles and then walk through the **10 questions above**, you can take this design from a basic system-design answer to a strong **Staff/Principal/Architect-level payment-system discussion**.
