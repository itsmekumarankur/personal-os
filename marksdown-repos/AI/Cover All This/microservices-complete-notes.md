# PART 1: THE BIG PICTURE

## 1. What Is a Microservice, Really?

In one sentence: A microservice is a small, independent application that does one business job and owns its own data.

Think of a restaurant:

```text
 MONOLITH (one giant kitchen)          MICROSERVICES (separate stations)

 +--------------------------+          +--------+  +---------+  +--------+
 |  ONE kitchen             |          | Grill  |  | Salad   |  | Dessert|
 |  - takes orders          |          | station|  | station |  | station|
 |  - cooks everything      |          +---+----+  +----+----+  +----+---+
 |  - washes dishes         |              |            |            |
 |  - does billing          |          [Grill    ]  [Salad   ]  [Dessert ]
 |  ONE team, ONE menu      |          [fridge   ]  [fridge  ]  [fridge  ]
 +--------------------------+          (own data)   (own data)   (own data)

 If the grill breaks, the      If the grill station breaks,
 whole restaurant stops.        salads and desserts still work.
```

The key properties:

| Property | What it means |
|---|---|
| Independent deploy | You can update the Payment service without touching Orders |
| Own data | Each service has its own database (not shared) |
| Network communication | Services talk over HTTP, gRPC, or messages |
| Organized by business capability | "Payments" not "Controllers" or "DAOs" |
| Small team owns it | One team can change it without asking three other teams |

The honest trade-off:

```text
 MONOLITH                          MICROSERVICES
 +--------------------------+      +--------------------------+
 | + Simple to start        |      | + Independent deploys    |
 | + Easy to debug          |      | + Independent scaling    |
 | + One database, one txn  |      | + Team autonomy          |
 | + Fast in-process calls  |      | + Fault isolation        |
 |                          |      |                          |
 | - Hard to scale parts    |      | - Network is unreliable  |
 | - One bug can crash all  |      | - Distributed data is hard|
 | - Teams block each other |      | - Ops overhead explodes  |
 | - Long deploy cycles     |      | - Hard to debug across   |
 +--------------------------+      |   many services          |
                                   +--------------------------+
```

Interview line: "Microservices trade code complexity for operational complexity. I adopt them when the real problem is organizational scaling — many teams stepping on each other — not just because they're trendy."

## 2. When Should You NOT Use Microservices?

Say this in an interview — it shows maturity:

| Situation | Better choice |
|---|---|
| Small team (under ~8 engineers) | Modular monolith |
| Early-stage product, domain not understood | Monolith first, split later |
| No DevOps maturity (no CI/CD, no monitoring) | Monolith first |
| Simple CRUD app | Monolith |
| Heavy transactional consistency needed everywhere | Monolith or modular monolith |

The "Modular Monolith" middle ground:

```text
 MODULAR MONOLITH
 +------------------------------------------+
 |  ONE deployable app                      |
 |  +--------+  +--------+  +--------+      |
 |  | Orders |  |Payment |  | Users  |      |
 |  | module |  | module |  | module |      |
 |  +--------+  +--------+  +--------+      |
 |  Each module: clear boundary,            |
 |  own data, no direct cross-module        |
 |  database access. But ONE process,       |
 |  ONE deploy, ONE database.               |
 +------------------------------------------+
```

You get clean boundaries without network complexity. When one module needs to scale separately, you extract it into a service. This is the strangler fig approach — grow the new around the old.

## 3. How to Split a System into Services

### The wrong way (by technical layer)

```text
 WRONG (distributed monolith)
 +-------------+  +-------------+  +-------------+
 | Controllers |  |  Services   |  |    DAOs     |
 +-------------+  +-------------+  +-------------+
 Every feature change touches all three. You've just
 made a monolith with network calls.
```

### The right way (by business capability)

```text
 RIGHT (bounded contexts)
 +-----------+  +-----------+  +-----------+  +-----------+
 | Customer  |  | Payments  |  | Portfolio |  |   IPO     |
 | & KYC     |  |           |  |           |  |           |
 +-----------+  +-----------+  +-----------+  +-----------+
 Each owns its data, its team, its release cycle.
```

### How to tell if a boundary is wrong

| Smell | What it means |
|---|---|
| Two services always deploy together | They're one service pretending to be two |
| Service A calls Service B 10 times per request | Too chatty — merge them or redesign |
| Two services share a database | Hidden coupling — split the data |
| A change in one service forces changes in three others | Wrong boundaries |
| The call chain is A→B→C→D→E for one user action | You built a distributed monolith |

### The 30% rule (a practical test)

Look at your Git history. If two services change together in more than 30% of releases, they're really one service. Merge them or fix the boundary.

### Invariants — the real boundary maker

An invariant is a rule that must always be true. For example: "A bank balance can never go negative."

Rule: An invariant that must hold atomically (all-or-nothing) lives inside one service with one database transaction.

```text
 WRONG: Split a balance across two services
 +-------------+     +-------------+
 | Account Svc |     | Ledger Svc  |
 | balance=500 |     | balance=500 |   <- Two copies, now they disagree
 +-------------+     +-------------+      after a crash. Which is right?

 RIGHT: One owner
 +-----------------------+
 | Account Svc           |
 | balance=500           |   <- Single source of truth.
 | (local ACID txn)      |      Others ask or reserve.
 +-----------------------+
```

# PART 2: HOW SERVICES TALK

## 4. Sync vs Async — The Most Important Decision

This is the first question to ask about any service interaction.

```text
 SYNCHRONOUS (phone call)              ASYNCHRONOUS (email)

 Caller ----request----> Callee        Caller --message--> [Broker/Queue]
        <---response----                       (Kafka, RabbitMQ, SQS)
                                           Caller continues immediately
 Both must be up at the same time.         Callee processes when ready.
 Caller waits.                             Nobody waits.
 If callee is slow, caller is stuck.       If callee is down, messages wait.
```

|  | Synchronous (REST/gRPC) | Asynchronous (Kafka/RabbitMQ) |
|---|---|---|
| Coupling | Both must be alive | Time-decoupled |
| Latency | Caller waits for answer | Caller moves on |
| Failure | Cascades to caller | Buffered in broker |
| Use for | "I need the answer now" (queries, reads) | "Do this eventually" (events, notifications, long jobs) |
| Complexity | Simple to reason about | Harder (idempotency, ordering, DLQ) |

The rule of thumb:

- User is waiting for the answer? → Synchronous.
- Can happen later? → Asynchronous.

### Availability math — why sync chains hurt

Every synchronous hop multiplies the failure probability:

```text
 Place-order flow: Gateway → Order → Pricing → Risk → Payment → Ledger
 That's 6 synchronous hops.
 If each hop is 99.9% available (8.8 hours downtime/year):

 0.999 × 0.999 × 0.999 × 0.999 × 0.999 × 0.999 = 0.994 = 99.4%
 That's ~52 hours of downtime per year for the whole flow.
```

To get 99.99% (52 minutes/year), you cannot have 6 synchronous hops at 99.9% each. You must remove hops from the critical path.

### How to fix it

```text
 BEFORE (sync, fragile):
 User → GW → Order → Pricing → Risk → Payment → Ledger → response
        (6 things must all be up)

 AFTER (async, resilient):
 User → GW → Order → [save to DB + outbox] → 202 Accepted
                         |
                         | events (async)
                         v
              Pricing    Risk    Payment    Ledger
              (each can be down; they catch up later)
```

Levers, in order of usefulness:

- Remove hops from the synchronous path (accept durably, process after).
- Make hops optional (degrade instead of fail).
- Cache data locally so you don't call at all.
- Merge services that are always called together.
- Add redundancy per hop (multi-AZ).

## 5. REST vs gRPC vs Messaging

```text
 REST (HTTP + JSON)              gRPC (HTTP/2 + Protobuf)       MESSAGING (Kafka, RabbitMQ)
 +--------------------------+    +--------------------------+    +--------------------------+
 | GET /orders/123          |    | rpc GetOrder(OrderReq)   |    | producer → [topic] →     |
 | { "id": 123, ... }       |    | returns OrderResp        |    | consumers                |
 +--------------------------+    +--------------------------+    +--------------------------+
 Human readable                  Binary, fast, typed             Decoupled, durable
 Browser-friendly                Service-to-service              Event-driven
 Simple                          Streaming, bidirectional        Replayable, buffered
 Slower, verbose                 Needs codegen                   Operational overhead
```

| Use | When |
|---|---|
| REST | Public APIs, browser clients, simple CRUD |
| gRPC | Internal service-to-service, low latency, streaming, strongly typed |
| Messaging | Events, async workflows, decoupling, buffering |

Interview tip: There is no "best" protocol. Ask about the client, latency needs, and whether the call can be async.

## 6. API Gateway and BFF

```text
 Internet
   |
   |  Mobile app ----+
   |                 |
   |  Web browser ---+-----> [ API GATEWAY ] ----> Order Service
   |                 |       - TLS termination       Payment Service
   |  Partner API ---+       - JWT validation        User Service
                             - Rate limiting
                             - Routing
                             - Request aggregation
```

API Gateway responsibilities:

| Job | Why |
|---|---|
| TLS termination | Decrypt HTTPS once at the edge |
| Authentication | Validate JWT before it reaches services |
| Rate limiting | Protect backend from abuse |
| Routing | /orders/\* → Order service, /payments/\* → Payment service |
| Request aggregation | Call 3 services, merge into one response |
| Response caching | Reduce backend load |

### BFF — Backend for Frontend

```text
 +----------+     +-------------+
 | Mobile   |---->| Mobile BFF  |----+
 +----------+     +-------------+    |     +-------------+
                                     +---->| Order Svc   |
 +----------+     +-------------+    |     +-------------+
 | Web      |---->| Web BFF     |----+     | Payment Svc |
 +----------+     +-------------+          +-------------+
```

Why BFF? Mobile needs small payloads, fewer fields. Web needs rich data. A single API can't serve both well. Each BFF shapes the response for its client.

Rule: Put BFFs at the edge for read composition. Never put write workflows or business rules there.

## 7. Service Mesh — What It Actually Does

A service mesh is a network of sidecar proxies that handle cross-cutting concerns for every service.

```text
 WITHOUT mesh:

 +-------------+        +-------------+
 | Order Svc   |------->| Payment Svc |
 | (must code: |        | (must code: |
 |  mTLS,      |        |  mTLS,      |
 |  retries,   |        |  retries,   |
 |  timeouts,  |        |  timeouts,  |
 |  tracing)   |        |  tracing)   |
 +-------------+        +-------------+

 WITH mesh:

 +-------------+  +-------+     +-------+  +-------------+
 | Order Svc   |->| Envoy |---->| Envoy |->| Payment Svc |
 | (just HTTP) |  |sidecar|     |sidecar|  | (just HTTP) |
 +-------------+  +-------+     +-------+  +-------------+
                      ^              ^
                      |              |
                 +-------------------------+
                 |  Control Plane (istiod) |
                 |  - certs (mTLS)         |
                 |  - routing rules        |
                 |  - telemetry            |
                 +-------------------------+
```

What the mesh gives you (without code changes):

| Feature | What it does |
|---|---|
| mTLS | Encrypts and authenticates every service-to-service call |
| Retries | Retries failed calls (careful: default is on) |
| Timeouts | Cuts long calls |
| Circuit breaking | Ejects bad instances |
| Traffic splitting | 5% to canary, 95% to stable |
| Telemetry | Every call is traced and measured |

What the mesh CANNOT do:

- Business fallbacks (return cached price when pricing service is down)
- Idempotency
- Compensation logic

Interview rule: Mesh handles infrastructure resilience. App handles business resilience. Pick one layer to own retries (not both, or you get 9x amplification).

# PART 3: DATA AND CONSISTENCY

## 8. Database Per Service

The rule: Each service owns its data. No other service reads its database directly.

```text
 WRONG (shared database):                RIGHT (database per service):

 +-------+  +-------+  +-------+         +-------+   +-------+   +-------+
 |Order  |  |Payment|  |User   |         |Order  |   |Payment|   |User   |
 +---+---+  +---+---+  +---+---+         +---+---+   +---+---+   +---+---+
     |          |          |                 |           |           |
     +----------+----------+                 v           v           v
                |                       [Order DB]  [Payment DB]  [User DB]
          [ ONE DB ]                   (only Order  (only Payment  (only User
     Schema changes break everyone      touches it)  touches it)    touches it)
```

How to get cross-service data:

| Need | Technique |
|---|---|
| Show order + customer on one screen | API Composition — gateway calls both, merges |
| Frequent complex queries across services | CQRS read model — build a denormalized view from events |
| Analytics / reporting | CDC (Debezium) or events → data warehouse |

```text
 API Composition:
 Mobile → Gateway → calls Order Svc (get order)
                 → calls Customer Svc (get customer)
                 → merges → returns one JSON

 CQRS Read Model:
 Order Svc ---event---> [Projector] ---> Reporting DB (flat, fast)
 Customer Svc ---event--->     ^              ^
                               |              |
                          (Kafka topic)  (queries hit this)
```

## 9. The Dual-Write Problem and the Outbox Pattern

### The problem

A service must do two things when an order is placed:

- Save the order to its database.
- Publish an OrderCreated event to Kafka.

```text
 BAD:
 BEGIN;
   INSERT INTO orders ...;
 COMMIT;
 ---- CRASH HERE ----
 publish to Kafka;  ← Event is lost forever. Database has the order. Nobody knows.
```

Or the reverse: the event publishes, but the DB commit fails. Now downstream services think an order exists that doesn't.

This is the dual-write problem. It is unsolvable with just a database and a message broker.

### The solution: Transactional Outbox

Write the business data and the event to the same database in one transaction. A separate relay process publishes the event.

```text
 +------------------- Order Service --------------------+
 |                                                      |
 |  BEGIN TRANSACTION;                                  |
 |    INSERT INTO orders (id, ...) VALUES (...);        |
 |    INSERT INTO outbox (event_type, payload, status)  |
 |           VALUES ('OrderCreated', '{...}', 'NEW');   |
 |  COMMIT;   ← Both or neither. Atomic.               |
 |                                                      |
 +------------------------+-----------------------------+
                          |
                          | Relay process polls outbox
                          | (or Debezium reads the DB log)
                          v
                     [ Kafka topic: orders ]
                          |
                          v
              Consumers (at-least-once delivery)
```

Two relay options:

| Relay | How | Pros | Cons |
|---|---|---|---|
| Polling publisher | SELECT \* FROM outbox WHERE status='NEW' every second | Simple | DB load, latency, ordering issues with multiple pollers |
| CDC (Debezium) | Reads the database's write-ahead log | Low latency, preserves commit order | Operational complexity |

Key points that show depth:

- Ordering is per partition. Use aggregateId (e.g., orderId) as the Kafka key so one order's events stay ordered.
- Delivery is at-least-once. Consumers need an inbox table or naturally idempotent writes.
- Outbox table grows. Purge or partition by time.
- Relay lag is a metric. Alert on it — it's invisible business delay.

## 10. Saga Pattern — Multi-Step Business Flows

### The problem

In a monolith, a multi-step operation uses one ACID transaction:

```text
 BEGIN;
   debit_customer();
   allot_units();
   send_confirmation();
 COMMIT;  ← All or nothing
```

In microservices, the steps are in different services with different databases. No single transaction can span them. Two-phase commit (2PC) is slow, fragile, and most modern databases/services don't support it well.

### The solution: Saga

A saga is a sequence of local transactions. If a step fails, compensating actions undo the previous steps.

```text
 SUCCESS PATH:
 Step 1: Reserve units    (Inventory DB)
 Step 2: Debit customer   (Payment DB)
 Step 3: Confirm allotment (Portfolio DB)
 Step 4: Notify user      (Notification DB)

 FAILURE AT STEP 3:
 Step 3 fails → orchestrator (or events) trigger:
   Compensate Step 2: Refund customer
   Compensate Step 1: Release reservation
   Order marked FAILED_REFUNDED
```

### Choreography vs Orchestration

```text
 ORCHESTRATION (a conductor):           CHOREOGRAPHY (a dance):

 +-------------------+                  Order Svc --OrderCreated--> Payment Svc
 | Order Orchestrator|                                              |
 +--+-----+-----+----+                                              v
    |     |     |                   Payment Svc --PaymentDone--> Portfolio Svc
    v     v     v                                                        |
 [Inv] [Pay] [Port]                                                      v
                                   Portfolio Svc --UnitsAllotted--> Order Svc
 One service knows the whole flow.  Each service reacts to events.
 Easy to see, but can become       Loose coupling, but flow is
 a god-service.                    scattered across services.
```

|  | Orchestration | Choreography |
|---|---|---|
| Visibility | One place to see the flow | Scattered |
| Coupling | Orchestrator knows everyone | Loose |
| Best for | Complex flows (4+ steps) | Simple reactions (2-3 steps) |
| Risk | God service | Cyclic dependencies, hard to debug |

### The critical ordering rule

```text
 COMPENSATABLE steps → PIVOT (point of no return) → RETRYABLE steps

 Example:
 1. Reserve units    (cheap to undo)     ← do first
 2. Validate address (cheap to undo)     ← do first
 3. Debit customer   (PIVOT — hard to undo, customer-visible)
 4. Confirm allotment (retry until success)
 5. Notify user      (retry until success)
```

Why? Put cheap-to-undo, likely-to-fail steps first. Put hard-to-undo, customer-visible steps last. After the pivot, only steps that can be retried to success remain.

### The isolation problem (that interviewers love)

Sagas give you atomicity (all steps complete or are compensated) but not isolation. Other transactions can see intermediate state.

```text
 Customer places order:
   t=0: Debit customer (balance drops by 5000)
   t=1: Allot units FAILS
   t=2: Refund (balance back up)

 In between t=0 and t=2, the customer's loan auto-debit bounced
 because the balance looked too low. Damage done.
```

Countermeasures:

- Semantic lock: mark the row PENDING so other operations know to wait or reject.
- Commutative updates: design operations so order doesn't matter (+500 / -200, not set balance = 5000).
- Re-read before write: check the value hasn't changed before overwriting.
- Compensations must be idempotent (a refund might arrive twice — handle it).

## 11. Idempotency — The Most Important Word in Microservices

Idempotent means: doing it once has the same effect as doing it many times.

```text
 NON-IDEMPOTENT (dangerous):           IDEMPOTENT (safe):

 POST /payments { amount: 5000 }       PUT /accounts/123/balance { value: 5000 }
   Run once:  debit 5000                 Run once:  balance = 5000
   Run twice: debit 10000 ← BAD          Run twice: balance = 5000 ← Fine
```

### Why it matters

In distributed systems, you cannot tell the difference between a slow call and a failed call. When the caller times out, it doesn't know if the work happened.

```text
 Caller ---POST /payments---> Payment Service
        <---timeout--------
 Did the debit happen? Yes? No? UNKNOWN.
 The only safe answer: retry with an idempotency key.
```

### How to implement it (REST)

```text
 POST /payments
 Idempotency-Key: 7c1f-4a2b-9e3d-abc123
 { "amount": 5000, "to": "ACC123" }

 Server:
   1. INSERT INTO idempotency_store (key, status) VALUES (:key, 'IN_PROGRESS')
      UNIQUE constraint on (client_id, key)
   2. If insert succeeds: process the payment, store the response, set status='DONE'
   3. If insert fails (duplicate): return the stored response from step 2
   4. If status='IN_PROGRESS': return 409 (another request is running)
```

### The details that fail in production

| Pitfall | Fix |
|---|---|
| Global key space | Scope by (client_id, operation, key) so one client can't replay another's key |
| Same key, different payload | Store a payload hash. Return 422 if it doesn't match |
| Crash between key insert and work | Both must be in the same DB transaction |
| External side effect (bank call) | Pass the same reference to the bank so it deduplicates |
| Key expires too soon | TTL must be longer than the longest retry window (hours to days) |
| Store only the key, not the response | Store and replay the response |

### For Kafka consumers

```text
 Consumer reads message (eventId=abc123):
   1. Check inbox table: has abc123 been processed?
   2. If yes → skip
   3. If no → process, insert abc123 into inbox, commit offset
   4. Both in same DB transaction
```

The famous quote: "Exactly-once delivery is a myth. The practical answer is at-least-once delivery + idempotent consumers."

Kafka's "exactly-once semantics" only works inside Kafka (read → process → write to Kafka). It does not cover your database or HTTP side effects.

## 12. CQRS and Event Sourcing

### CQRS (Command Query Responsibility Segregation)

Separate the write model from the read model.

```text
 COMMANDS (writes)                    QUERIES (reads)
 POST /orders                         GET /orders/summary

 +-------------+     events     +-------------+     +------------+
 | Write Model | ------------> | Projector   |---->| Read Model |
 | (normalized)|               | (consumes)  |     | (denormal) |
 +-------------+               +-------------+     +------------+
                                                         ^
                                                         |
                                                   GET /orders
                                                   (fast, no joins)
```

When to use: read and write patterns are very different. Example: writes are simple (INSERT), reads need complex joins across 5 services.

The cost: eventual consistency. The read model lags behind the write model. See read-your-writes below.

### Event Sourcing

Store the sequence of events as the source of truth. Rebuild state by replaying.

```text
 Account 123:

 Event store (append-only):
 1. AccountOpened(balance=0)
 2. Deposited(amount=500)
 3. Withdrawn(amount=200)

 Current balance = 0 + 500 - 200 = 300

 To get balance: replay events. (Snapshots speed this up.)
```

When to use: you need a perfect audit trail, temporal queries ("what was the balance last Tuesday?"), or event-driven integration.

The cost: complexity — event versioning, snapshots, eventual consistency, learning curve. Do not use it unless the audit trail justifies it.

### Read-your-writes (the classic CQRS problem)

```text
 User places order → write model → event → projector → read model
 User immediately refreshes → GET /orders → read model hasn't caught up → order missing!
```

Solutions:

- Return a version/offset token with the write; the read API waits (bounded) until the projection catches up.
- Optimistic UI: merge local state until the projection catches up.
- Route to the write model for a short window after a write.
- Show an explicit "processing" state.

## 13. CAP Theorem in Plain English

CAP: In a network partition (a break in communication between nodes), you must choose:

- Consistency: every read sees the latest write.
- Availability: every request gets a response.
- Partition tolerance: the system keeps working despite network breaks.

The reality: Network partitions will happen. So P is not optional. The real choice is C vs A during a partition.

```text
 PARTITION HAPPENS
       |
       v
 +-----+-----+
 |           |
 C           A
 |           |
 v           v
 Refuse      Serve stale
 writes/     data, accept
 reads       eventual
 (CP)        consistency (AP)
```

In microservices:

- Inside one service's database: CP (ACID, strong consistency). A bank balance must be correct.
- Across services: AP (eventual consistency). The portfolio view updates a few seconds after payment.

The PACELC extension: Even when there's no partition, you still trade Latency vs Consistency (replicating data takes time).

Interview line: "I use strong consistency where money is involved (single database, ACID). I use eventual consistency across services (events, sagas, CQRS) and make the staleness explicit in the UI."

# PART 4: RESILIENCE — STAYING ALIVE WHEN THINGS BREAK

## 14. Why "Slow" Is Worse Than "Down"

This is the most important resilience concept and interviewers love it.

```text
 A DEAD service:                    A SLOW service:

 Caller → X (connection refused)    Caller → (waiting...) → (waiting...) → (waiting...)
 Fails in 1ms.                       Holds a thread for 30 seconds.
 Caller moves on.                    Caller's thread pool fills up.
                                    Caller's health check can't get a thread.
                                    Caller gets restarted.
                                    Traffic shifts to other callers.
                                    They die too.
                                    CASCADE.
```

### Little's Law — the math behind it

```text
 Concurrency (L) = Throughput (λ) × Latency (W)

 Payment service: 500 req/s, bank call = 200ms
   L = 500 × 0.2 = 100 in-flight calls.  (Pool of 200: fine.)

 Bank degrades to 30 seconds:
   L = 500 × 30 = 15,000 in-flight calls.  (Pool of 200: saturated in <1 second.)
```

What happens next:

```text
 Thread pool full
   → new requests queue (unbounded queue = unbounded latency)
   → health endpoint can't respond (no free thread)
   → liveness probe fails
   → Kubernetes restarts the pod
   → traffic shifts to remaining pods
   → they die too
   → THE DEATH SPIRAL
```

### The defence stack (in order)

```text
 1. TIMEOUT         — bound the wait. Never wait forever.
 2. CIRCUIT BREAKER — stop calling a sick service.
 3. BULKHEAD        — isolate resources so one dependency can't starve others.
 4. RETRY           — only for transient blips, with backoff + jitter.
 5. FALLBACK        — degrade gracefully.
 6. LOAD SHEDDING   — protect yourself when overloaded.
```

## 15. Timeouts

### The layers of a timeout

```text
 DNS lookup     Connect     TLS handshake     Pool wait     Request/response     Overall deadline
 (50ms)         (1-2s)      (1-2s)            (???)         (p99 + margin)       (sum of all)
```

The bug that hides everywhere: no pool-acquisition timeout. The downstream timeout never fires because the thread is stuck waiting for a connection from the pool.

### How to set values

Use the p99 of successful calls plus margin. Not the incident worst case.

Different per operation (read vs write).

Never leave defaults — many HTTP clients default to infinite.

### The layered timeout model (inner < outer)

```text
 Client     5s
  Gateway   4s
   Order    3s  (call to Payment)
    Payment 2s  (call to Bank)

 If inner > outer: the caller gives up, but the callee keeps working.
 Wasted work + retries = overload.
```

Better: propagate a deadline (gRPC does this natively; REST can use a header like x-deadline-ms). Each hop computes remaining = deadline - now and refuses if too little is left.

### Common timeout bugs

| Bug | Symptom |
|---|---|
| No pool-acquisition timeout | Threads queue forever; downstream timeout never fires |
| Client gives up, server keeps working | Wasted work + retries = overload |
| Idle-timeout mismatch (LB 60s vs app 75s) | Intermittent 502 on reused connections |
| Async client timeout doesn't cancel I/O | Leaked connections |
| Default infinite | Hangs forever |

## 16. Retries (and Why They Can Kill You)

### When to retry

| Failure | Retry? |
|---|---|
| Connection refused (request never sent) | ✅ Yes, even for non-idempotent calls |
| 503 / 429 with Retry-After | ✅ Yes, honour the header |
| Read timeout on idempotent call | ✅ Yes, with backoff |
| Read timeout on non-idempotent call | ⚠️ Only with an idempotency key (outcome is UNKNOWN) |
| 4xx business/validation error | ❌ Never |
| Circuit open | ❌ Don't hammer; fail fast or fallback |

### How to retry

```text
 Exponential backoff + jitter:

 Attempt 1 fails → wait random(0, 100ms)
 Attempt 2 fails → wait random(0, 200ms)
 Attempt 3 fails → wait random(0, 400ms) → give up

 WITHOUT jitter: 1000 clients all retry at exactly t+1s → thundering herd.
 WITH jitter: retries spread out. The sick service can recover.
```

### Retry amplification — the killer

```text
 Gateway (3 retries) → Order (3 retries) → Payment (3 retries) → Bank

 One user request = 3 × 3 × 3 = 27 calls to the Bank when it's already struggling.
```

The rule: Retry at ONE layer only. Usually the one closest to the failing call. The others propagate errors.

Watch out: Istio's default is 2 retries. If your app also retries 3 times, you get 6x without realizing it.

### Retry budgets

Allow retries up to a fraction of normal traffic (e.g., 10%) using a token bucket. This turns retries from a multiplier into a bounded cost.

### Hedging (for reads only)

Send a second identical request to another replica after p95 latency. Take whichever finishes first. Cancel the loser.

```text
 Request 1 → replica A (slow)
 Request 2 → replica B (fast) ← wins
 Cancel request 1.

 Reduces tail latency. Costs extra load. Reads only, with a budget.
```

## 17. Circuit Breakers

### The three states

```text
                  failure rate ≥ threshold (e.g. 50%)
      +--------+ ----------------------------------> +--------+
      | CLOSED |                                    |  OPEN  |
      | calls  |                                    | calls  |
      | flow   |                                    | fail   |
      | normally                                    | FAST   |
      +--------+ <---------------------------+      +----+---+
          ^                                  |           |
          | probes succeed                   |           | after waitDuration (e.g. 30s)
          |                                  |           v
          |                           +------+-------------------+
          +---------------------------|      HALF-OPEN          |
                                      | allow N trial calls     |
                                      +----------+--------------+
                                                 |
                                                 | probes fail
                                                 +--> back to OPEN
```

| State | Behavior |
|---|---|
| CLOSED | Normal. Calls pass. Results recorded. |
| OPEN | Calls rejected immediately (CallNotPermittedException). No load on the sick service. |
| HALF-OPEN | Limited trial calls decide whether to close or reopen. |

### What to measure

| Metric | Why |
|---|---|
| Failure rate | Exceptions, 5xx, connection errors |
| Slow-call rate | Calls over a threshold (e.g., 2s). Critical — latency is more dangerous than errors |
| Minimum calls | Don't evaluate before N calls (2 calls with 1 failure = 50% — meaningless) |

### Key configuration

```yaml
resilience4j.circuitbreaker.instances.bank:
  slidingWindowType: COUNT_BASED          # or TIME_BASED
  slidingWindowSize: 20                   # last 20 calls
  minimumNumberOfCalls: 10                # don't evaluate before 10
  failureRateThreshold: 50                # open at 50% failures
  slowCallDurationThreshold: 2s           # 2s+ = slow call
  slowCallRateThreshold: 80               # open at 80% slow calls
  waitDurationInOpenState: 30s            # time before HALF-OPEN
  permittedNumberOfCallsInHalfOpenState: 5
  recordExceptions: [IOException, TimeoutException]
  ignoreExceptions: [BusinessValidationException]  # 4xx don't count!
```

### What counts as a failure

Count: timeouts, connection errors, 5xx, 429, 503.

Do NOT count: 4xx business errors (400, 404, 409). Otherwise bad user input "breaks" a healthy dependency.

### Partial failure — the wrong-tool problem

```text
 33% of Payment pods are bad (one AZ has issues):

 Service-level breaker (threshold 50%):
   Failure rate = 33% < 50% → stays CLOSED → users see 33% errors. (Wrong tool.)

 Service-level breaker (threshold 30%):
   Opens → rejects 100% of traffic → total outage for a 33% problem. (Worse!)

 RIGHT TOOLS for partial failure:
   - Mesh outlier detection: eject bad hosts (per-instance)
   - Retry to a different host
   - Locality failover
   - Zone-aware routing
```

Keep the service-level breaker for "the whole dependency is sick." Use outlier detection for "some instances are sick."

### Placement

One breaker per downstream dependency (and per critical operation). Not one global breaker.

State is per pod, in memory. Do not share through a central store (adds a dependency to your resilience layer).

New pods start CLOSED (they haven't learned yet).

### How the breaker itself causes outages

| Problem | Fix |
|---|---|
| 4xx counted as failures | ignoreExceptions |
| Window too small | Increase minimumNumberOfCalls |
| Self-invocation bypasses proxy | Call through a different bean (Spring AOP) |
| Opens on non-critical dependency with no fallback | Add a fallback or don't break on it |
| Deploys reset state | Accept it; or use mesh outlier detection |

## 18. Bulkheads

Named after ship compartments: if one compartment floods, the ship doesn't sink.

```text
 WITHOUT bulkhead:                    WITH bulkhead:

 +--------------------------+         +--------------------------+
 | ONE shared thread pool   |         | Pool A: Bank      (20)   |
 | 200 threads              |         | Pool B: Email     (10)   |
 |                          |         | Pool C: Reports   (10)   |
 | Email is slow →          |         |                          |
 | ALL 200 threads blocked. |         | Email is slow →          |
 | Payment can't run.       |         | only Pool B is blocked.  |
 +--------------------------+         | Payment is fine.         |
                                      +--------------------------+
```

Types:

| Type | How | Trade-off |
|---|---|---|
| Semaphore bulkhead | Limit concurrent calls (counter) | Cheap, same thread |
| Thread-pool bulkhead | Dedicated pool per dependency | Stronger isolation, more overhead, breaks ThreadLocal (trace IDs, security context) |

Also at infrastructure level:

- Separate connection pools per dependency.
- Separate node pools or namespaces for critical vs non-critical workloads.
- Separate health/admin port with its own thread pool.

## 19. Fallbacks

When a call fails or the circuit is open, return something useful.

| Strategy | Example |
|---|---|
| Cached/stale data | Show last known NAV with an "as of 10:05" label |
| Default value | Recommendations service down → show generic top funds |
| Degrade a feature | Hide "similar products" section; rest of page works |
| Queue for later | Notification service down → put message on a queue |
| Fail with a clear error | Payments: never fake success. Return "try again" |

### Fail-open vs fail-closed

| Operation class | Dependency down | Policy |
|---|---|---|
| Money movement, trades | Authz, limits, ledger | Fail closed (reject or pend). Never fabricate state |
| Sensitive reads | Entitlement service | Fail closed or serve cached decision within a short TTL |
| Non-sensitive reads | Recommendations, pricing display | Fail open with stale cache and an "as of" label |
| Notifications, analytics | Anything | Async: drop or queue, never block |

Rules:

- Stale data must have a staleness bound and be labelled.
- Log every fail-open decision (audit).
- Test your fallbacks. An untested fallback often throws.

## 20. Metastable Failure — The Scary One

A system enters a state that persists after the trigger is gone, sustained by its own recovery behaviour.

```text
 Trigger: dependency slow for 90 seconds
   ↓
 Timeouts fire → retries → 3x load
   ↓
 Queues full of requests whose callers already gave up
   ↓
 Workers burn time on dead work
   ↓
 Pools exhausted, caches cold, pods restarting
   ↓
 THE LOAD ITSELF SUSTAINS THE FAILURE
   ↓
 Even after the dependency is healthy, the system stays down.
```

### Mitigations

| Mitigation | What it does |
|---|---|
| Load shedding | Return 503 fast at saturation |
| Drop expired work | Check the deadline when dequeuing. Don't process requests nobody is waiting for |
| LIFO or adaptive queues | Process newest requests first (they're most likely still wanted) |
| Retry budgets | Bound the amplification |
| Circuit breakers | Cut the amplification |
| Slow start | Ramp traffic to cold instances instead of full load at once |
| Kill switch | Disable retries or shed a traffic class manually |
| Drain and refill | Cut load to near zero, let the system recover, restore gradually |

Interview line: "The scariest outage is the one that doesn't end when the trigger ends. That's metastable failure — the system's own recovery behaviour keeps it down."

# PART 5: SERVICE DISCOVERY — HOW SERVICES FIND EACH OTHER

## 21. The Problem of Moving IPs

In the cloud, IPs change constantly. Pods scale, crash, and move. You cannot hard-code addresses.

```text
 order-svc wants to call payment-svc:

 10.1.4.12:8080  ← today
 10.1.7.3:8080   ← after a deploy
 10.1.9.21:8080  ← after a scale-out
```

Service discovery maintains a live registry: "service name → healthy instance addresses."

## 22. Kubernetes DNS and Service Discovery

```text
 order-svc calls:  http://payment-svc.payments.svc.cluster.local:8080
        |
        | (1) CoreDNS resolves name → ClusterIP (stable virtual IP, e.g. 10.96.34.7)
        v
 (2) kube-proxy (iptables/IPVS rules on every node) picks one backend
        |
        v
 (3) EndpointSlice → only READY pods
     10.1.4.12  10.1.7.3  10.1.9.21
```

Key facts:

- Service = stable name + virtual IP + load balancing.
- EndpointSlice = updated automatically as pods come and go.
- Readiness probe failure = removed from endpoints (no traffic).
- DNS format: `<service>.<namespace>.svc.cluster.local`. Same namespace: just payment-svc.

### The DNS 5-second mystery

If you've seen random 5-second latency spikes, it's often DNS:

```text
 resolv.conf has: options ndots:5

 Looking up "api.example.com" (2 dots < 5):
   1. api.example.com.<ns>.svc.cluster.local   ← fail
   2. api.example.com.svc.cluster.local        ← fail
   3. api.example.com.cluster.local            ← fail
   4. api.example.com                          ← finally, the real lookup

 Plus: parallel A/AAAA UDP lookups can race in conntrack and one packet is dropped.
 The resolver waits its 5-second timeout before retrying.
```

Fixes:

- NodeLocal DNSCache (each node runs a DNS cache).
- Trailing-dot FQDNs for external names (api.example.com.) or lower ndots.
- Scale CoreDNS.
- JVM: set networkaddress.cache.ttl explicitly (10-30s). The default can cache forever, so after pods move, the app keeps calling dead IPs.

### Client-side vs server-side discovery

```text
 CLIENT-SIDE (Eureka + Spring Cloud LoadBalancer):

 Order-svc --(1) fetch list--> [Eureka Registry]
 Order-svc --(2) pick instance itself--> Payment pod #2


 SERVER-SIDE (Kubernetes Service, AWS ALB):

 Order-svc --> [Load balancer / kube-proxy] --> Payment pod (LB chooses)
```

|  | Client-side | Server-side |
|---|---|---|
| Who picks | Caller (library) | Infrastructure |
| Extra hop | No | Usually cheap |
| Language coupling | Needs a library | None |
| Examples | Eureka, Consul | Kubernetes Service, Envoy |

In Kubernetes, server-side is the default. Eureka is usually unnecessary unless you have VMs + K8s hybrid.

### Eureka staleness (if asked)

```text
 Heartbeat: every 30s
 Eviction: after ~90s of missed heartbeats
 Client fetch: every 30s (cached)
 Client LB cache: another few seconds

 Total window for a dead instance to remain visible: MINUTES.
 So you need client retries + circuit breaker.
```

## 23. Health Probes — The Three Types

```text
 +------------------------------------------------------------------+
 |  Pod lifecycle                                                   |
 |                                                                  |
 |  STARTUP probe ──(fails)──> keep waiting, don't run others       |
 |       │                                                          |
 |       └──(passes)──> LIVENESS + READINESS take over              |
 |                                                                  |
 |  LIVENESS probe ──(fails 3x)──> RESTART the container            |
 |       "Is the process deadlocked?"                               |
 |       NEVER check dependencies here.                             |
 |                                                                  |
 |  READINESS probe ──(fails)──> REMOVE from Service endpoints      |
 |       "Can it serve traffic right now?"                          |
 |       NO restart. Just no traffic.                               |
 +------------------------------------------------------------------+
```

```yaml
readinessProbe:
  httpGet: { path: /actuator/health/readiness, port: 8080 }
  periodSeconds: 5
livenessProbe:
  httpGet: { path: /actuator/health/liveness, port: 8080 }
  periodSeconds: 10
  failureThreshold: 3
startupProbe:
  httpGet: { path: /actuator/health/liveness, port: 8080 }
  failureThreshold: 30
  periodSeconds: 5   # allows up to 150s to start
```

### The #1 probe mistake

Putting dependency checks in the liveness probe.

```text
 DB blips for 5 seconds
   → liveness probe fails (DB check failed)
   → ALL pods restart
   → capacity drops to zero
   → a 5-second DB blip becomes a 5-minute total outage.
```

Liveness checks only the process itself. Readiness can check local init (config loaded, warm enough), but not downstream dependencies — if all pods go unready, endpoints drop to zero.

### Graceful shutdown

On pod termination, Kubernetes sends SIGTERM and removes the pod from endpoints at the same time (not in order). Traffic can still arrive for a few seconds.

```text
 Fix:
   lifecycle:
     preStop:
       exec:
         command: ["sleep", "10"]    # keep serving while endpoints update

   terminationGracePeriodSeconds: 45  # > preStop + longest request
```

# PART 6: SECURITY

## 24. Zero Trust — The Mindset

Old model: "Inside the firewall is safe. Trust everything inside."

Zero trust: "Never trust the network. Verify every call, every time."

```text
 INTERNET          DMZ              INTERNAL NETWORK
   |                |                     |
   |  untrusted     |  semi-trusted       |  STILL NOT TRUSTED
   v                v                     v
 [WAF] → [Gateway] → [Service A] → [Service B] → [DB]
                         ^             ^
                         |             |
                    Must prove      Must prove
                    identity        identity
```

The layers of defence (defence in depth):

```text
 Layer 1: NetworkPolicy   — Can this pod even reach that pod? (L3/L4)
 Layer 2: mTLS            — Is the channel encrypted and authenticated?
 Layer 3: Authorization   — Is this caller allowed to do this?
 Layer 4: JWT / user      — On whose behalf?
 Layer 5: App authz       — Does this user own this resource?
 Layer 6: Secrets         — Are credentials short-lived and safe?
```

"mTLS is enough" is wrong. mTLS authenticates (proves who is calling). It does not authorize (prove they're allowed).

## 25. mTLS — What It Really Means

Normal TLS: only the server proves its identity. (Your browser verifies the bank's certificate.)

mTLS (mutual TLS): both sides present certificates.

```text
 Order-svc (client)                              Payment-svc (server)
     | ---- ClientHello ----------------------------> |
     | <--- ServerHello + server cert --------------- |
     | verify server cert against trusted CA          |
     | ---- client cert ----------------------------> |
     |                       verify client cert (CA)  |
     | <=========== encrypted session ==============> |
```

### How workload identity works (SPIFFE/Istio)

```text
 Pod starts
   → sidecar generates key pair
   → sends CSR to istiod (control plane) with its K8s ServiceAccount token
   → istiod validates the token with the API server
   → issues a short-lived X.509 cert (default ~24h) with SAN:
       spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>
   → rotated automatically
```

Identity is bound to the ServiceAccount, not IP or hostname (IPs are recycled constantly).

### What breaks it

| Failure | Impact |
|---|---|
| Control plane down longer than cert TTL | Certs expire, all east-west traffic dies |
| Clock skew | Cert validation fails |
| Sidecar/node compromise | Attacker gets that workload's identity |
| default ServiceAccount | All services share one identity — blast radius is everything |
| kubelet probes | Can't do mTLS — injector must rewrite them |
| Jobs/CronJobs | Never finish because the sidecar keeps running |

### The control plane time bomb

```text
 Control plane down at 02:00.
 Certs have 24h TTL.
 At 02:00 next day: every cert expires simultaneously.
 All service-to-service calls fail at once.
 It looked healthy for 24 hours. Then everything died.
```

Mitigation: alert on time-to-expiry, HA control plane, cert TTL comfortably longer than worst-case MTTR, overlapping root CA rotation, practiced break-glass.

## 26. JWT and Identity Propagation

There are three identities in play:

- The calling service (proved by mTLS).
- The end user (proved by JWT).
- Sometimes the original client/app.

```text
 User --JWT(aud=gateway)--> Gateway --???--> Order Svc --???--> Payment Svc
```

### Patterns for passing user identity

| Pattern | How | When | Risk |
|---|---|---|---|
| Forward the JWT as-is | Pass Authorization: Bearer `<jwt>` downstream | Simple, user-scoped | Token has aud=gateway; every downstream holds a powerful, replayable token |
| Token exchange (RFC 8693) | Swap for a new token with narrower aud/scope | Downstream needs limited access | Extra hop to STS |
| Internal signed "passport" | Mint at the edge, short TTL (minutes) | Many internal hops | You own the minting service |
| Client credentials | Service gets its own token | System-initiated (batch, reconciliation) | Must not be used to "act as" a user |

### The confused deputy problem

```text
 Payment trusts an X-User-Id header from Order.
 Any pod in the cluster can call Payment with X-User-Id: <victim>.
 → Impersonation. → Fraud.

 Fix:
 1. mTLS: only Order's identity can call Payment.
 2. Signed token: X-User-Id replaced with a JWT Payment can verify.
 3. Authorize BOTH: "Order may call this route" AND "user U may touch account A."
 4. Strip inbound identity headers at the edge. Never trust plain headers.
```

## 27. Authorization — Who Can Do What

```text
 COARSE (who may call what)  →  Mesh AuthorizationPolicy
                                 (cheap, uniform, no code)

 DOMAIN (who may see what)   →  Inside the service
                                 (needs data: ownership, relationships)

 CROSS-CUTTING rules         →  Policy engine (OPA/Cedar)
                                 (as library or sidecar, with pushed bundles)
```

### Istio example

```yaml
# 1. Require mTLS for the whole namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: payments
spec:
  mtls:
    mode: STRICT
---
# 2. Only order-svc may call POST /payments
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-order-to-pay
  namespace: payments
spec:
  selector:
    matchLabels:
      app: payment-svc
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/orders/sa/order-svc"]
      to:
        - operation:
            methods: ["POST"]
            paths: ["/payments*"]
```

Once any ALLOW policy exists on a workload, everything not matched is DENIED.

### The central PDP problem

```text
 If every request calls a central authorization service:
   Entitlement service down → whole platform down.

 Better: local evaluation.
   Service → local policy engine (OPA in-process or sidecar)
              ^ policy + entitlement bundles pushed periodically
              ^ decision cache (short TTL)

   PDP down → local engine keeps deciding with last known bundle (bounded staleness).
```

Per operation class:

- Money movement: fail closed when bundle staleness exceeds a limit.
- Non-sensitive reads: fail open from cache, with an audit log.

# PART 7: DEPLOYMENT

## 28. Helm in Plain English

Helm is the package manager for Kubernetes. Instead of maintaining 10 YAML files per service per environment, you ship a chart (templates + default values) and install it as a release.

```text
 order-chart/
 ├── Chart.yaml          # name, version, appVersion
 ├── values.yaml         # default config
 ├── values-prod.yaml    # prod overrides
 └── templates/
     ├── deployment.yaml
     ├── service.yaml
     ├── hpa.yaml
     └── _helpers.tpl    # reusable snippets

 helm install order ./order-chart -f values-prod.yaml -n orders
        │
        v  renders templates + values → K8s manifests → applied to cluster
        v  release "order" revision 1 recorded (in a Secret in the namespace)
```

### Essential commands

| Command | Purpose |
|---|---|
| helm lint | Static check |
| helm template | Render locally, no cluster (CI validation) |
| helm upgrade --install | Idempotent deploy |
| helm diff upgrade (plugin) | Preview changes |
| helm history `<rel>` | List revisions |
| helm rollback `<rel>` `<rev>` | Roll back |
| helm uninstall | Remove |

Critical flags: --atomic (auto-rollback on failure), --wait (wait until ready), --timeout, --history-max 10.

### Helm pitfalls that bite in production

| Pitfall | What happens | Fix |
|---|---|---|
| replicas hardcoded | HPA changes it, Helm resets it on every upgrade | Omit replicas when HPA is enabled |
| --reuse-values | Reuses old values, ignores new chart defaults | Pass full values, or --reset-then-reuse-values |
| Immutable fields | Changing Deployment selector fails the upgrade | Treat selector labels as permanent |
| Release history | Stored in Secrets, ~1 MiB limit | --history-max |
| CRDs | Installed on first install only, never upgraded | Manage them separately |
| GitOps | Argo CD/Flux render charts, so no Helm release history | Rollback by Git revert |

### Hooks

```yaml
annotations:
  "helm.sh/hook": pre-upgrade,pre-install
  "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

Use for: DB migrations before new pods start.

Gotchas:

- Hook resources are not part of the release (no automatic cleanup unless you set delete policy).
- A pre-upgrade migration runs while old pods are still serving → must be backward compatible.
- Jobs are immutable — fixed names fail on re-run unless you use before-hook-creation.
- Migrations in the app's startup race when several replicas boot simultaneously. Use a single Job or a lock (Flyway/Liquibase).

### Rollback truth table

| Restored by helm rollback | NOT restored |
|---|---|
| Image, env, resources, probes, ConfigMaps | Database schema and data |
| Service/Ingress/HPA/PDB definitions | PVC contents, CRDs, secrets |
|  | Messages already published, side effects, feature flags |

Therefore: design for N-1 compatibility and prefer roll-forward when the data layer moved.

## 29. Rolling, Blue-Green, Canary — When to Use Which

```text
 ROLLING UPDATE:
 v1 v1 v1 v1  →  v2 v1 v1 v1  →  v2 v2 v1 v1  →  v2 v2 v2 v2
 + No extra capacity, K8s default
 - Slow rollback, mixed versions run together

 BLUE-GREEN:
 [Blue v1 live] [Green v2 idle] → switch router → [Green live], keep Blue for rollback
 + Instant rollback
 - Double infrastructure

 CANARY:
 95% traffic v1, 5% v2 → watch error rate/latency → 25% → 50% → 100%
 + Lowest blast radius, real traffic validation
 - Needs good metrics and traffic splitting (mesh/ingress)
```

| Strategy | Best for |
|---|---|
| Rolling | Most services, default |
| Blue-green | When instant rollback matters more than cost |
| Canary | High-risk changes, when you have good observability |

### Zero-downtime deployment checklist

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate: { maxSurge: 25%, maxUnavailable: 0 }
terminationGracePeriodSeconds: 60
lifecycle:
  preStop: { exec: { command: ["sleep", "10"] } }
readinessProbe / livenessProbe / startupProbe   # different semantics
resources.requests set   # needed by scheduler and HPA
topologySpreadConstraints across zones
PodDisruptionBudget: maxUnavailable: 1 (NOT minAvailable = replicas)
```

The PDB trap: minAvailable equal to replicas (or 100%) blocks node drains and Cluster Autoscaler scale-down forever.

## 30. Database Migrations — The Expand-Contract Dance

The problem: You need to add a NOT NULL column. The new code expects it. The old code doesn't write it. During a rolling update, both versions run simultaneously.

```text
 BAD (single release):
 R1: Add NOT NULL column + code reads/writes it.
     → Old pods crash (column is NOT NULL, they don't write it).
     → Rollback restores old code, but the column stays.
     → Old code fails against new schema. STUCK.
```

The fix: three releases

```text
 R1 EXPAND:
    Add column NULLABLE (or with default).
    Code writes old + new. Reads old.
    → Both old and new code work.

 R2 SWITCH:
    Backfill old rows.
    Code reads new column.
    Keep dual-write.
    Feature flag controls the switch.

 R3 CONTRACT:
    Make NOT NULL / drop old column.
    Only after N-1 versions are gone and flag is stable.

 Each release is individually rollback-safe (N-1 compatible).
```

Interview line: "The database is the hardest thing to roll back. That's why every schema change must be backward compatible for at least one release."

# PART 8: SCALING

## 31. HPA — How It Actually Works

```text
 kubelet/cAdvisor → metrics-server (scrape ~15-60s) → HPA controller (loop every 15s)
                                                          │
                                                          v
                                    desired = ceil( currentReplicas × currentMetric / targetMetric )
```

Example: 4 pods, CPU at 90%, target 60% → ceil(4 × 90 / 60) = 6 pods.

### The key rules

| Rule | What it means |
|---|---|
| Utilisation is % of requests | If requests are set too low, HPA sees 300% and over-scales |
| Tolerance ~10% | HPA ignores small changes to avoid jitter |
| Multiple metrics | Compute each, take the maximum |
| Scale-up fast, scale-down slow | Default scale-down stabilization: 300s |
| Not-ready pods are handled conservatively | Assumed 0% when scaling up, 100% when scaling down |

### The real reaction time

```text
 t=0     traffic spike
 t+30-60s  metrics catch up
 t+75s   HPA decides +N pods
 t+90s   pods Pending → (no capacity) → Cluster Autoscaler provisions node: +60-180s
 t+...   image pull, JVM start, warm-up: +30-120s
 t+4-6 min  new pods Ready, delivering ~30-60% of steady-state capacity at first
```

HPA is a trend follower, not a spike absorber. It reacts in minutes, not seconds.

### Choosing the right signal

| Signal | Good when | Danger |
|---|---|---|
| CPU % | CPU-bound services | I/O-bound services stay at low CPU while saturated |
| In-flight concurrency per pod | I/O-bound, request/response (best general signal) | Needs instrumentation |
| RPS per pod | Predictable cost per request | Cost varies |
| Queue depth / consumer lag | Consumers (KEDA) | Capped by partitions |
| Latency | SLO-aware | Scaling out on latency when the dependency is slow adds load and worsens it |

Anti-pattern: scaling callers when the bottleneck is a downstream (DB, partner API). More pods = more pressure = worse outage.

### The HPA formula for pods

```text
 pods = ceil( peakRPS × p95Latency / targetConcurrencyPerPod ) × headroom
```

### HPA troubleshooting

| Symptom | Likely cause |
|---|---|
| TARGETS `<unknown>` | metrics-server down, or no resource requests set |
| Not scaling despite load | Metric is not the bottleneck (I/O-bound), already at max, within tolerance, stabilization window, pods not Ready |
| Scaled but latency still bad | New pods Pending (no nodes), cold JVM, connection pinning, downstream saturated |
| Scales up then flaps down | Aggressive scale-down policy, bursty metric, window too short |
| Resets after deploy | Helm/GitOps overriding replicas |
| Over-scales | Requests too low, startup CPU spike counted, throttling |
| Pods Pending | Node capacity, quotas, anti-affinity, PV zone |

## 32. Capacity Planning and Connection Budgets

### The connection budget trap

```text
 DB max_connections = 500 (shared by 7 services)

 Order: 8 pods × pool 20 = 160 today
 HPA max 40 pods × pool 20 = 800 → EXCEEDS 500 → outage when "scaling works"
```

Fix:

- Connection budget per service: maxReplicas = budget / poolSize.
- Use a pooler (PgBouncer/RDS Proxy). Caveat: transaction pooling breaks session state, advisory locks, and some prepared statements.
- Bounded pool wait with fail-fast (503) so callers don't queue forever.
- Same coupling applies to Kafka partitions, partner API rate limits, cache/hot-key limits.

### AZ-loss sizing

```text
 Required pods at peak: P = 24
 3 AZs, must survive loss of one AZ at peak:
 → remaining 2 AZs must hold 24
 → per-AZ = 12, total = 36 (run at ~67% utilisation of total capacity)
```

### Little's Law for pool sizing

```text
 Pool size = concurrency × (fraction of time in DB)
           = (requests/sec × DB latency) × headroom
```

Not "20 because it's the default."

## 33. Cold Start and Spike Handling

```text
 t=0     spike
 t+30-60s  metrics catch up
 t+75s   HPA decides
 t+4-6 min  new pods fully warm
```

Mitigations (combine them):

| Mitigation | What it does |
|---|---|
| Higher minReplicas | Set from SLO and AZ-loss requirement, not average load |
| Scheduled scaling | KEDA cron before known events (IPO opening, market open, salary day) |
| Headroom | Target utilisation 50-60%, not 80% |
| Overprovisioning | Low-priority "pause" pods that are preempted by real pods (warm node capacity) |
| Faster start | Smaller images, pre-pulled images, AppCDS/GraalVM native, lazy init |
| Slow-start in LB/mesh | New pods ramp up traffic instead of getting a full share instantly |
| Admission control | Queue-based load levelling to absorb the spike while scaling catches up |

# PART 9: OBSERVABILITY

## 34. Logs, Metrics, Traces — The Three Pillars

```text
 A request flows: Gateway → Order → Payment → Bank

 LOGS:    "Order 123 created"           (what happened)
 METRICS: http_requests_total=5000      (how many / how fast)
 TRACES:  [Gateway 120ms][Order 900ms][Payment 38s][Bank 35s]  (where time went)
          traceId = abc123, propagated through every hop
```

| Pillar | Answers | Tools |
|---|---|---|
| Logs | What happened? | ELK, Loki, Splunk |
| Metrics | How much / how fast? | Prometheus, Grafana |
| Traces | Where did the time go? | Jaeger, Tempo, Zipkin |

Always propagate a correlation/trace ID across HTTP calls and Kafka headers (W3C traceparent). Structured JSON logs should include traceId.

### Alerting

RED for services: Rate, Errors, Duration.

USE for resources: Utilisation, Saturation, Errors.

Alert on SLO burn rate, not every CPU blip.

## 35. SLOs, SLIs, and Error Budgets

| Term | Meaning | Example |
|---|---|---|
| SLI (Indicator) | A measured number | "99.95% of requests succeed" |
| SLO (Objective) | A target for the SLI | "99.9% success rate over 30 days" |
| SLA (Agreement) | A contract with consequences | "99.9% or we refund 10%" |
| Error budget | 100% − SLO | "0.1% = ~43 minutes/month of allowed failure" |

How error budgets work:

- If you have budget left, ship features.
- If you've burned the budget, freeze releases and fix reliability.

```text
 Error budget for 99.9% over 30 days = 43 minutes.

 Used 40 minutes in week 1? → freeze releases, fix reliability.
 Used 5 minutes in week 1?  → ship features faster.
```

## 36. The Four Golden Signals

Google's SRE book says: monitor these four for every service.

| Signal | What it means | Example metric |
|---|---|---|
| Latency | How long requests take | p50, p95, p99 response time |
| Traffic | How much demand | Requests per second |
| Errors | How many requests fail | 5xx rate, exception count |
| Saturation | How full is the service | CPU %, connection pool usage, queue depth |

If you can only monitor four things, monitor these.

# PART 10: THE 30 INTERVIEW SCENARIOS

## Scenario 1: Product wants 99.99% for "place order." The flow has 6 synchronous hops, each at 99.9%. What do you do?

The math: 0.999^6 = 99.4% = ~52 hours downtime/year. Target is ~52 minutes/year.

Answer:

- Classify each hop: required to accept the order vs. required to complete it.
- Redesign the accept path:

```text
 BEFORE (sync):
 User → GW → Order → Pricing → Risk → Payment → Ledger → response
        (6 things must be up)

 AFTER (accept fast, complete async):
 User → GW → Order → [save to DB + outbox] → 202 Accepted
                         │
                         │ events
                         v
              Pricing    Risk    Payment    Ledger
              (async, can be down, catches up)
```

- Cache the price snapshot (versioned) instead of a live Pricing call.
- Risk limits locally (updated via events), or a single reservation service for hard invariants.
- Define SLO on acceptance (99.99%) and a separate SLO on completion time.
- Add criticality tiers and bulkheads for anything left synchronous.

The trap: answering "retries and circuit breakers." They don't fix multiplicative availability.

## Scenario 2: A dependency was down for 90 seconds. It recovered, but your system stayed down for 25 minutes. Why?

This is metastable failure. The system's own recovery behaviour keeps it down.

```text
 90s of slowness
   → timeouts + retries (3 layers) → 27x load
   → queues full of requests whose callers gave up
   → workers burn time on dead work
   → pools exhausted, caches cold, pods restarting
   → THE LOAD SUSTAINS THE FAILURE
```

Fixes:

- Retry at one layer with a budget, jitter, and deadline awareness.
- Drop expired requests on dequeue. Bounded queues, LIFO under overload.
- Load shedding at saturation (503 fast).
- Circuit breakers with slow-call detection.
- Slow-start for restarted pods.
- Liveness must not depend on the dependency.
- Kill switch to disable retries or shed a traffic class.
- Game day: inject slowness (not just outage), verify recovery after removal.

The trap: "Add more pods." Under metastable load, cold pods make it worse.

## Scenario 3: Payment calls a bank. The call times out after 2 seconds. Did the customer get debited?

A timeout is neither success nor failure. It is UNKNOWN.

```text
 Three states: SUCCESS | FAILED | UNKNOWN

 1. Persist intent first:
    INSERT INTO payments (id, bankRef=UNIQUE, status='INITIATED')

 2. Call bank with bankRef (bank deduplicates on it):
    ok       → SUCCESS
    declined → FAILED (definitive)
    timeout  → UNKNOWN (do NOT fail, do NOT blindly retry)

 3. UNKNOWN resolution:
    - status-inquiry API with backoff (same bankRef)
    - fallback: end-of-day reconciliation file from the bank
    - until resolved: funds shown as pending/held, customer told "processing"

 4. Resolve to SUCCESS or FAILED → continue saga or compensate.
```

Never:

- Retry with a new reference ID (double debit).
- Mark it failed (customer charged, order cancelled).
- Auto-refund an UNKNOWN (it may have debited).

## Scenario 4: A purchase saga debits the customer, then allotment fails and the refund is queued. Meanwhile the customer's loan auto-debit bounced. How should the saga have been designed?

The saga exposed intermediate state (a dirty read of a debit that would later be reversed).

```text
 BEFORE:
 debit → allot units → confirm
 (allot fails → refund; damage done in between)

 AFTER:
 1. Reserve units (cheap undo, can fail)    ← do first
 2. Validate everything else
 3. Debit (PIVOT — hard to undo)            ← do late
 4. Confirm allotment + notify (retry)      ← only retryable steps after pivot
```

Additional points:

- Represent the debit as a hold/authorisation (semantic lock) if it must precede.
- Make downstream consumers (EMI engine) aware of "available vs ledger balance."
- Compensations must be idempotent and retried until success, with priority and SLA.
- Include a customer-impact policy (waive the bounce penalty automatically).
- Record saga state and expose status so support can see "pending refund."

## Scenario 5: A Risk service consumes account events. After you added retry topics, it raised a false limit breach because a debit was processed before the credit that preceded it. Fix it.

Cause: retry topics break per-key ordering. Multiple relay instances or partitions can also reorder.

Options (in increasing robustness):

- Key by accountId, single-threaded per key, use blocking retry on the key (park the key, continue others) with bounded attempts, then DLQ.
- Per-aggregate sequence number in each event. Consumer applies only lastApplied + 1; buffers or parks out-of-order events.
- State-based consumer: events carry the full resulting state/version. Apply if version > current, ignore otherwise (commutative, idempotent).
- Producer side: outbox relay must preserve order per key (no concurrent relays for the same key).
- Risk breach logic should be computed from authoritative state (balance and limit versions), not from a sequence of deltas that can arrive in any order.

## Scenario 6: Security mandates mTLS everywhere and default-deny authorization across 80 live services in one quarter, with no outage. How do you roll it out?

Phased and reversible:

```text
 Phase 0: Inventory & telemetry — who calls whom, who's outside the mesh
 Phase 1: PERMISSIVE mesh-wide (accepts plaintext + mTLS), inject sidecars gradually
 Phase 2: Observe — dashboards for plaintext traffic by source/destination; fix each
 Phase 3: STRICT per namespace, lowest risk first; canary a few services per wave
 Phase 4: Default-deny AuthorizationPolicy in audit/dry-run, review denies, enforce
 Phase 5: Egress control (default-deny egress, allow-list via egress gateway)
```

Rollback per wave: switch that namespace back to PERMISSIVE (fast — it's config).

Gotchas that cause real incidents:

- Non-mesh callers (cron jobs, VMs, other clusters, monitoring scrapers).
- kubelet probes can't do mTLS; the injector rewrites probes — verify they still work.
- Jobs/CronJobs never finish because the sidecar keeps running.
- Startup race: app calls out before the sidecar is ready.
- Headless/StatefulSet and TCP protocols (databases, Kafka) need explicit protocol/port settings.
- Per-hop latency and CPU/memory overhead.

## Scenario 7: Payment trusts an X-User-Id header from Order. A pentest shows any pod can impersonate a user. How do you fix it?

Fix properly (defence in depth):

- Authenticate the caller: mTLS + AuthorizationPolicy so only Order's identity can call Payment's specific routes.
- Authenticate the user context cryptographically: replace the header with a signed token (user JWT, exchanged token with aud=payment, or an internal passport minted at the edge). Payment verifies signature, issuer, audience, expiry.
- Authorize both: "service Order may call this route" and "user U may act on account A" (resource-level check in Payment). Record actor in the act claim.
- Strip inbound identity headers at the edge and never accept them from internal callers.
- NetworkPolicy default-deny for defence in depth; audit logging with both identities.

The trap: "Order is trusted because it's inside the cluster." Order can be compromised or buggy and then act for any user (confused deputy).

## Scenario 8: At 02:10 every east-west call starts failing with TLS errors. The mesh control plane had been unhealthy for a day. What happened?

The control plane time bomb:

```text


What happened?

Think of certificates like ID cards that allow services to trust each other.

1. Every service has an ID card valid for about 24 hours.
2. The mesh control plane was down, so certificates could not be renewed.
3. After 24 hours, the certificates expired.
4. Services could no longer trust each other, so all secure service-to-service calls started failing at once.

Why did it fail at 02:10? Because that is when the certificates expired.

### How to prevent it?

- Alert: Warn before certificates expire.
- High availability: Keep backup control-plane instances running.
- Certificate lifetime: Ensure enough time to recover before expiry.
- Test failure: Practice what happens when the control plane goes down.

Architect's takeaway: The system looked healthy because existing certificates were still valid. The control plane failure became visible only when those certificates expired.
```


## Scenario 9: After traffic growth, services show random 5-second latency spikes and some calls hit dead pod IPs after deployments. Diagnose.
```text
Two separate problems:
The service itself may be fine; the delay happens because finding its address is taking too long. The exact 5-second delay depends on the DNS timeout and retry configuration.

2. Calls hit dead pod IPs — stale IP problem
- A service remembers a pod's old IP address.
- The pod gets replaced during deployment.
- The service still calls the old IP, so the request fails.
Fix: Use stable Kubernetes Service IPs, refresh stale connections, and retry failed connections safely.
Architect's takeaway
- 5-second spikes → Investigate DNS performance.
- Dead IPs after deployment → Investigate stale DNS entries and connection pools.
Monitor DNS latency, connection failures, and errors during deployments.
```
## Scenario 10: HPA scaled your gRPC service from 5 to 20 pods, but old pods are still at 90% CPU, new pods at 2%. Why?

Connection pinning:

```text
Think of 5 old buses carrying all the passengers, while 15 new buses are almost empty.

Why does this happen?

- gRPC keeps connections open: Clients continue using the same old pods.
- Load balancing happens per connection: New requests keep going to old pods instead of spreading evenly.
- HPA gets confused: It sees high CPU and adds more pods, but those new pods remain idle.

How to fix it?

1. L7 Load Balancer: Distributes requests more evenly across pods.
2. Reconnect clients periodically: Gives clients a chance to connect to new pods.
3. Monitor each pod: Detect overloaded pods instead of looking only at average CPU.

Interview takeaway: Adding more pods won't help if traffic isn't distributed properly. Fix the load balancing first.
```


## Scenario 11: A market-open event raises traffic 15x within a minute. CPU-based HPA reacts too late and CPU stayed low while latency exploded. Design the scaling.

Why CPU stayed low: threads were blocked on I/O.

Design:

- Use in-flight concurrency or RPS-per-pod as the signal (not CPU).
- Capacity maths: peak 6,000 rps, p95 120ms, target 40 concurrent per pod → 6000 × 0.12 / 40 = 18 pods. Add 30% headroom → 24. To survive AZ loss → 36 total.
- Pre-scale on schedule before the event (KEDA cron) and keep the floor through the peak.
- Cold start: warm-up before readiness, slow-start in LB, overprovisioning pods, pre-pulled images.
- Absorb the spike: admission control, per-client rate limiting at the edge, queue-based load levelling for non-interactive work, degrade optional features.
- Dependencies: scale or pool DB/cache ahead, verify connection budget.
- Prove it: load test at 1.5x projected peak, including an AZ-loss run.

The trap: lowering the CPU target to 30% and calling it done.

## Scenario 12: HPA scaled Order from 8 to 40 pods; the system got slower and the DB started refusing connections. Explain and fix.

The connection budget trap:

```text
 8 pods × 20 conns = 160
 40 pods × 20 = 800
 vs DB max_connections = 500 (shared with 6 services)
```

Fix:

- Per-service connection budget; maxReplicas = budget / poolSize.
- Reduce pool size using concurrency × DB time fraction.
- Add a pooler (and know its caveats).
- Bounded pool wait that fails fast with 503 (backpressure) instead of queueing.
- Cache and read replicas for read-heavy paths.
- Split write-heavy flows to async.
- Scale on the true bottleneck signal (DB saturation, pool wait time).
- Add automatic protection (concurrency limit at the service) so scale-out cannot take the DB down.

The trap: raising max_connections (memory per connection and context switching make it worse).

## Scenario 13: A release adds a NOT NULL column and code. Helm + Argo CD with a pre-upgrade migration hook. New pods crash. Rollback. Old version now fails against the new schema. Replicas reset to 3 during the incident. What went wrong?

Three problems:

- Schema/code coupling: the migration ran while old pods served; rollback restored old code but not the schema. A NOT NULL column without a default breaks old writers.
- Fix: expand-contract, three releases (R1 nullable, R2 switch, R3 contract). Each release individually rollback-safe.
- Hook mechanics: hooks are not release-managed (cleanup via delete policy); Jobs are immutable; concurrent starts can race; under Argo CD the Helm hook maps to Argo's hook phases, so verify behaviour. Run migrations as a single, locked job before rollout, with monitoring and its own timeout.
- Replicas reset: the template hardcoded replicas while the HPA also owned it, or Argo self-heal reverted the HPA's change.
- Fix: omit replicas (or configure ignore-differences) when HPA is on.
- Rollout safety: canary/progressive delivery with automated abort, and roll-forward capability, because rollback does not cover data.

## Scenario 14: One of three AZs has noisy-neighbour issues, and 33% of Payment calls fail. A teammate says "the circuit breaker should handle it." Does it?

No. A service-level breaker is the wrong tool.

```text
 Threshold 50%:
   Failure rate = 33% < 50% → stays CLOSED → users see 33% errors.

 Threshold 30%:
   Opens → rejects 100% of traffic → total outage for a 33% problem.

 RIGHT TOOLS:
   - Mesh outlier detection: eject hosts with consecutive 5xx or latency anomalies
   - Retry on a different host (with retry budget)
   - Locality failover / zone-aware routing
   - Remove the bad AZ from rotation
   - Capacity that survives losing that zone
```

Keep the service breaker for "the whole dependency is sick."

Observability: per-pod and per-AZ error/latency breakdowns, not just service averages.

## Scenario 15: Your central authorization service is down. What happens to the platform, and what should have been designed?

If every request calls a central PDP synchronously, the platform fails with it.

Design so the PDP is not a runtime hard dependency:

```text
 Service → local policy engine (OPA/Cedar, in-process or sidecar)
              ^ policy + entitlement bundles pushed/pulled periodically
              ^ decision cache (short TTL, stale-while-revalidate)

 PDP down → local engine keeps deciding with last known bundle (bounded staleness).
```

Per operation class:

- Money movement / sensitive writes: fail closed once bundle staleness exceeds a limit (reject or pend).
- Non-sensitive reads: fail open from cache with an audit log.
- Bound staleness (e.g., "entitlements revoked can lag by up to X minutes") — make X a business decision and have a fast revocation path for high-risk changes via push.
- Circuit breaker plus fallback to cached decisions; alert on bundle age.
- Test it: take the PDP down in staging and verify critical paths behave per policy.

## Scenario 16: A user taps "Pay" twice (or the client retries on timeout) and money is debited twice. How do you prevent it?

Idempotency keys.

```text
 Client generates Idempotency-Key (UUID) per payment intent, resends SAME key on retry.

 Server:
   INSERT INTO idem (key, status) VALUES (:k, 'IN_PROGRESS')  -- UNIQUE(client_id, key)
     duplicate → return stored result (or 409 if still in progress)
     new       → process payment → store response → status DONE
```

Also:

- Database unique constraint on the business key (client_order_ref).
- Downstream calls to the bank carry the same key (bank-side idempotency/reference).
- TTL the keys (24-48h).
- Disable the button in UI after click (UX only, not a guarantee).

## Scenario 17: A mutual fund purchase: money was debited, but unit allotment failed. How do you keep the system consistent?

Orchestrated saga with compensation:

```text
 1. Order Svc:     create order (PENDING)
 2. Payment Svc:   debit customer          → compensation: refund
 3. Portfolio Svc: allot units             → compensation: reverse allotment
 4. Order Svc:     mark COMPLETED

 Step 3 fails → orchestrator: refund (step 2 compensation) → order = FAILED_REFUNDED
```

Details interviewers like:

- Each step is a local transaction + outbox event; consumers idempotent.
- Compensation is retried until success (must not fail permanently). If it cannot, route to manual reconciliation queue.
- Persist saga state (state machine) so it survives crashes.
- Add a timeout on each step (stuck order auto-escalates).
- Daily reconciliation job compares ledger vs allotments and flags mismatches.

## Scenario 18: The order was saved to the DB, but the "OrderCreated" event never reached Kafka. How do you guarantee both?

Transactional Outbox + CDC:

```text
 TX { orders, outbox } --commit--> Debezium reads WAL --> Kafka --> consumers (idempotent)
```

Order row and outbox row in one DB transaction. Debezium (or a poller) publishes outbox rows. Consumers deduplicate by event ID.

## Scenario 19: A pod in the cluster is compromised. How do you limit what the attacker can reach?

Zero-trust layers:

```text
 Compromised pod (notification-svc):

 X NetworkPolicy: default deny; only listed paths open → cannot even connect to DB/payment
 X mTLS STRICT: attacker has no valid cert for other IDs → cannot impersonate order-svc
 X AuthorizationPolicy: notification-svc not allowed on /payments
 X RBAC: ServiceAccount token has minimal K8s API permissions
 X Short-lived secrets: stolen DB creds expire in 1h
 X Pod Security: non-root, read-only FS, no privileged

 Plus runtime detection (Falco), audit logs, image scanning,
 egress restrictions (so it cannot exfiltrate), and rotating credentials after an incident.
```

## Scenario 20: IPO opens at 10:00 and traffic jumps 20x within 60 seconds. HPA is too slow. What do you do?

Pre-scale: schedule higher minReplicas (KEDA cron) 15 minutes before; pre-warm caches and connection pools.

Load test the IPO flow in advance to know per-pod capacity.

Queue-based load levelling: accept the bid into Kafka quickly ("received"), process asynchronously at a controlled rate.

Rate limiting and load shedding at the gateway (protect core), with fair per-user limits.

Cache read-heavy data (IPO details), CDN for static.

Scale dependencies (DB read replicas, connection pooler) and cap maxReplicas using DB limits.

Degrade non-essential features (recommendations, analytics) via feature flags.

Use RPS/latency-based HPA metrics (leading indicators).

## Scenario 21: HPA scaled Order service from 5 to 40 pods and the whole system slowed down. Why?

The bottleneck was downstream (DB connections, a rate-limited third-party API, or a Kafka partition limit). More callers just increased pressure.

Approach: find the actual constraint with traces and metrics (DB active connections, pool wait time, downstream latency).

Fix: connection pooler, caps in maxReplicas, caching, bulkheads and rate limits toward the dependency, scale the dependency or make the work asynchronous.

Scale on saturation of the real bottleneck, not blindly on CPU.

## Scenario 22: How do you roll out a breaking API change across 80 services with zero downtime?

```text
 Phase 1 EXPAND:   Provider supports old + new (v1 and v2, or new optional fields)
 Phase 2 MIGRATE:  Consumers move to v2 one team at a time (contract tests in CI)
 Phase 3 OBSERVE:  Metrics show v1 traffic = 0 for N days
 Phase 4 CONTRACT: Remove v1, drop old DB column
```

Also:

- Consumer-driven contracts (Pact): provider CI fails if it breaks a consumer.
- Tolerant reader (ignore unknown fields), never reuse or repurpose a field.
- Canary deploy the provider change; feature flags to switch behaviour.
- Events: add a schema registry with compatibility rules (BACKWARD/FULL) for Avro/Protobuf.
- Never "big bang" release 80 services together — that's a distributed monolith smell.

## Scenario 23: helm upgrade applied a DB migration, then the new pods crash. You roll back. What breaks?

Rollback restores the old image/config, but the migration stays applied. If the old code can't work with the new schema, you're down.

Prevention:

- Expand/contract migrations: only additive changes in the release that ships with code; destructive changes in a later release after the old code is gone.
- Run migration as a pre-upgrade hook or separate job, validated in staging with the previous app version against the new schema.
- Use --atomic for chart resources, but remember it does not undo the schema.
- Backups/point-in-time recovery plan; test roll-forward ("fix forward") as often as rollback.

## Scenario 24: The circuit breaker to a downstream service opens, then flips between OPEN and HALF-OPEN repeatedly (flapping). Why and how to fix?

Causes:

- Downstream is only partially recovered (can serve a few probes but not full load).
- waitDurationInOpenState is too short.
- Probe count too small, so a single failure re-opens it.
- Low traffic makes the failure-rate window noisy.

Fixes:

- Increase waitDurationInOpenState (and use exponential growth if supported).
- Increase permittedNumberOfCallsInHalfOpenState (e.g., 10) so the decision is statistically meaningful.
- Tune minimumNumberOfCalls, window size, and thresholds to traffic volume.
- Fix the root cause (downstream capacity), and ramp traffic gradually (mesh traffic shifting/slow start).
- Verify only real failures count (no 4xx).

## Scenario 25: Kafka consumer lag keeps growing and one partition has stopped moving. What is wrong?

Likely a poison message: the consumer throws on one record and retries it forever, blocking that partition (ordering means it can't skip).

```text
 Partition 3: [ok][ok][POISON][ok][ok]...
 Consumer stuck on POISON, lag grows.
```

Fix:

- Retry topics with backoff (orders.retry.1m, .10m) and a Dead Letter Topic (DLT) after N attempts; alert and replay later.
- Distinguish non-retryable errors (deserialisation, validation) straight to DLT vs transient errors with retry.
- Idempotent consumers (safe to replay), correct max.poll.interval.ms (slow processing triggers rebalances and duplicates).
- Scale consumers up to the number of partitions; lag-based autoscaling with KEDA.

## Scenario 26: A non-critical Notification service became slow and took down the Checkout flow. How?

How: Checkout called Notification synchronously with no timeout and a shared thread pool. Slow notifications consumed all threads → checkout stalled.

```text
 FIX:
 Checkout --(event)--> [Kafka] --> Notification Svc    (async, decoupled)

 If sync is required:
 short timeout + bulkhead + circuit breaker + fallback (skip silently)
```

Principle: classify dependencies as critical vs non-critical. Non-critical ones must never fail the critical path — make them async, isolate with a bulkhead, degrade gracefully.

## Scenario 27: A customer says "my SIP order took 40 seconds." The call touches 12 services. How do you find the root cause?

```text
 1. Get the traceId (from the user's request ID / gateway log).

 2. Open the trace in Jaeger/Tempo:

    Gateway      |==|                                            120ms
    Order        |==========|                                    900ms
    Payment         |======================================|    38s   ← find it
      Bank call                |==============================|  35s   ← the culprit

 3. Drill into the slow span: attributes (DB query text, downstream host, retry count).
 4. Cross-check metrics (p99 latency, error rate, saturation: thread pool, DB pool wait)
    and logs filtered by traceId.
 5. Check for retries/timeouts misconfiguration (timeout too long, retried 3 × 10s?),
    GC pauses, noisy neighbour, CPU throttling.
 6. Fix and add an alert/SLO so it is detected before the customer calls.
```

Requires: trace context propagation everywhere (HTTP headers, Kafka headers, async executors) and consistent structured logging.

## Scenario 28: During a rolling deployment, users see sporadic 502/503 errors for a few seconds. Why?

Pod termination race:

```text
 SIGTERM sent ─────────────────────────> app stops accepting immediately
 Endpoint removal propagates (kube-proxy/ingress) takes 1-5s
 ...requests still routed to the dying pod → 502
```

Fixes:

- Add preStop: sleep 10 so the pod keeps serving while endpoints are removed.
- Handle SIGTERM gracefully (finish in-flight, server.shutdown=graceful).
- terminationGracePeriodSeconds > preStop + max request time.
- Readiness probe so new pods get traffic only when truly ready (and warm).
- maxUnavailable: 0, maxSurge: 25%.
- PDB for node drains.
- Keep-alive mismatch: ingress/LB idle timeout vs app keep-alive timeout (app should have a longer one), otherwise connections get reset.
- Stale discovery entries (Eureka) → client retries on idempotent requests + circuit breaker.

## Scenario 29: A user places an order, then immediately refreshes the page — the order is missing. Why?

Read-your-writes problem with async projections (CQRS):

```text
 Write model → event → projector → read model
 User refreshes before the projector catches up → order not in read model.
```

Solutions:

- Return a version/offset token with the write; the read API waits (bounded) until the projection reaches it, or routes to the write model.
- Optimistic UI with local state merged until the projection catches up.
- Session-sticky read from the write store for a short window after a write.
- Show an explicit "processing" state instead of pretending consistency.

## Scenario 30: You need to migrate a monolith to microservices. How do you approach it?

Strangler Fig pattern:

```text
 Phase 1: Put a facade (API gateway) in front of the monolith.
 Phase 2: Extract one capability at a time behind the facade.
 Phase 3: Route traffic gradually to the new service.
 Phase 4: Remove the extracted code from the monolith.
 Repeat until the monolith is gone or small enough.
```

```text
 BEFORE:
 Client → Monolith (everything)

 DURING:
 Client → Facade → [Monolith (most things)]
                 → [New Service (one capability)]

 AFTER:
 Client → Facade → [Service A] [Service B] [Service C] [Small monolith]
```

Key principles:

- Never big-bang rewrite. Incremental, reversible steps.
- Database decomposition is the hardest part. Start with the service owning its data; use events/CDC to sync.
- Keep the monolith working throughout — it serves traffic for unextracted capabilities.
- Use the facade for routing, so clients don't know or care which backend serves them.
- Measure: deploy frequency, lead time, change failure rate should improve.

# PART 11: DESIGN PRINCIPLES AND PATTERNS

## 31. SOLID — The Five Principles

|  | Principle | One line |
|---|---|---|
| S | Single Responsibility | A module has one reason to change (one actor) |
| O | Open/Closed | Open for extension, closed for modification |
| L | Liskov Substitution | A subtype must be usable wherever the base type is |
| I | Interface Segregation | Clients should not depend on methods they don't use |
| D | Dependency Inversion | Both high-level policy and low-level detail depend on abstractions |

### S — Single Responsibility

Misreading: "a class does one thing" → hundreds of one-method classes.

Correct reading: one reason to change, meaning one actor (stakeholder group). Group things that change for the same reason; separate things that change for different reasons.

```java
// Violation: three actors in one class
class Statement {
    BigDecimal computeFees() {...}   // Finance changes this
    String renderPdf() {...}         // Compliance/Marketing changes this
    void saveToDb() {...}            // Platform/DBA changes this
}
```

Architecture level: this is the service boundary rule. A service that changes for two teams' reasons violates SRP. The 30% change-coupling test is SRP measured empirically.

### O — Open/Closed

Add behaviour by adding code, not by editing tested code.

```java
// Violation: every new payment mode edits this method
BigDecimal fee(Payment p) {
    if (p.mode == UPI) ...
    else if (p.mode == NEFT) ...
}

// Open/Closed: new mode = new class, existing code untouched
interface FeePolicy { boolean supports(Mode m); BigDecimal fee(Payment p); }
class UpiFee implements FeePolicy {...}
class NeftFee implements FeePolicy {...}
// Spring injects List<FeePolicy>; caller selects the one that supports(mode)
```

Architecture level: additive API and event evolution; new consumers subscribe without changing the producer.

### L — Liskov Substitution

Code written against the base type must work with any subtype without knowing the difference. This is about behavioural contracts, not just signatures.

Rules: a subtype must not strengthen preconditions, must not weaken postconditions, must preserve invariants, must not throw unexpected exceptions.

```java
interface Wallet { void debit(BigDecimal amt); }  // contract: debits, or throws InsufficientFunds

class ReadOnlyWallet implements Wallet {
    public void debit(BigDecimal amt) { throw new UnsupportedOperationException(); }  // LSP violation
}
```

Architecture level: contract compatibility. A new service version or an alternate implementation must honour the old semantics: same error behaviour, same idempotency guarantees, same ordering. Consumer-driven contract tests are LSP checks across services.

### I — Interface Segregation

```java
// Fat interface
interface AccountService { open(); close(); debit(); credit(); statement(); kycUpdate(); adminFreeze(); }

// Segregated by client role
interface AccountReader { Balance balance(AccountId id); }
interface AccountWriter { void debit(...); void credit(...); }
interface AccountAdmin  { void freeze(...); }
```

Architecture level: consumer-specific APIs (BFF per client type), separate gRPC services per consumer group, CQRS read vs write APIs, consumer-driven contracts.

### D — Dependency Inversion

High-level policy must not depend on low-level detail; both depend on abstractions.

Abstractions must not depend on details; details depend on abstractions.

```text
 WITHOUT                                   WITH (inverted)

 +-----------------+                       +-----------------+
 | PaymentService  |  (domain)             | PaymentService  |  (domain)
 +--------+--------+                       +--------+--------+
          | depends on                              | depends on
          v                                         v
 +-----------------+                  <<interface>> PaymentGateway   (OWNED BY THE DOMAIN)
 | HdfcBankClient  |  (detail)                      ^ implements
 +-----------------+                       +-----------------+
                                           | HdfcBankAdapter |  (detail)
                                           +-----------------+
```

The key point is who owns the interface. If it lives beside the bank client, you only added a layer. It belongs to the domain side, shaped by what the domain needs.

DIP is not dependency injection. DI is a wiring mechanism; DIP is a rule about dependency direction and interface ownership. You can use DI and still violate DIP.

Architecture level: hexagonal (ports and adapters), clean architecture, anti-corruption layer (ACL) toward partners and legacy systems.

### SOLID mapped to service design

| Principle | Service-level equivalent |
|---|---|
| SRP | Service boundary = one actor / one reason to change |
| OCP | Additive API and event evolution; extend by adding consumers |
| LSP | Backward-compatible versions and alternate implementations honour the same behavioural contract |
| ISP | BFF, CQRS, consumer-driven contracts, no fat shared SDK |
| DIP | Domain owns its ports; ACL isolates partners and legacy systems |

## 32. Adapter Pattern

Intent: convert one interface into the one the client expects, so incompatible components can work together without changing either.

```text
 Client --uses--> <<PaymentGateway>> (target, owned by domain)
                          ^
                          | implements
                  +----------------+   translates    +------------------+
                  | HdfcAdapter    | --------------> | HdfcBank SOAP/   |
                  | (object adapter|   calls         | REST client (the |
                  |  via composition)                | "adaptee")       |
                  +----------------+                 +------------------+
```

```java
public interface PaymentGateway {                     // domain-owned port
    PaymentResult pay(PaymentRequest r);              // SUCCESS | FAILED | UNKNOWN
}

class HdfcAdapter implements PaymentGateway {         // object adapter (composition)
    private final HdfcClient client;                  // third-party/legacy API
    public PaymentResult pay(PaymentRequest r) {
        try {
            HdfcResp resp = client.initiate(toHdfc(r));       // map domain → partner model
            return switch (resp.code()) {                      // map partner codes → domain outcomes
                case "00" -> PaymentResult.success(resp.ref());
                case "51" -> PaymentResult.failed(Reason.INSUFFICIENT_FUNDS);
                default   -> PaymentResult.failed(Reason.UNKNOWN_PARTNER_ERROR);
            };
        } catch (TimeoutException e) {
            return PaymentResult.unknown(r.id());               // timeout is UNKNOWN, not FAILED
        }
    }
}
```

Architect-level points:

- It is the implementation of DIP and the anti-corruption layer: partner models and error codes stop at the adapter, and the domain stays clean.
- The adapter is the natural place for boundary resilience: timeouts, retry, circuit breaker, bulkhead, idempotency reference, and mapping of failures to domain outcomes (including UNKNOWN).
- Object adapter (composition) is preferred over class adapter (inheritance) in Java.
- Multiple providers (HDFC, ICICI, NPCI) each get one adapter behind the same port. Selection by a factory. This enables provider failover and A/B routing.
- Service level: a gateway/adapter service, or a sidecar, that translates a legacy protocol (SOAP/MQ/ISO 8583) to your event or REST model.

Not the same as:

| Pattern | Difference |
|---|---|
| Facade | Simplifies a subsystem with a new, easier interface; doesn't need to match an existing target |
| Decorator | Same interface in and out; adds behaviour (logging, caching, retry) |
| Proxy | Same interface; controls access (lazy load, security, remote) |
| Adapter | Different interface; translates between two |

## 33. Singleton Pattern

Intent: one instance per scope, with a global access point.

```java
// 1. Enum singleton: simplest, thread-safe, safe against serialization and reflection
public enum Config { INSTANCE; ... }

// 2. Initialization-on-demand holder: lazy and thread-safe, no explicit synchronization
public class Registry {
    private Registry() {}
    private static class Holder { static final Registry I = new Registry(); }
    public static Registry get() { return Holder.I; }
}

// 3. Double-checked locking: needs volatile (Java 5+) or it is broken
public class Cache {
    private static volatile Cache instance;
    public static Cache get() {
        if (instance == null) {
            synchronized (Cache.class) {
                if (instance == null) instance = new Cache();
            }
        }
        return instance;
    }
}
```

Architect-level points:

- Scope is per JVM (per classloader), not per cluster. In Kubernetes with 10 replicas you have 10 "singletons."

```text
 Pod A: [scheduler singleton]   Pod B: [scheduler singleton]   Pod C: [scheduler singleton]
 → the "single" nightly job runs 3 times.

 Fix: leader election (Kubernetes Lease), distributed lock (ShedLock, DB or Redis lock),
      or a single-replica worker, or partition ownership (Kafka consumer group).
```

- Hidden global mutable state: hard to test, hidden coupling, thread-safety bugs, lifecycle problems. This is why the classic static singleton is considered an anti-pattern in modern code.
- Prefer container-managed singleton scope (Spring beans are singleton by default): same single instance, but injected (DIP), mockable, with managed lifecycle. The beans must be stateless or thread-safe.
- Legitimate uses: configuration holders, connection pools, metrics registries, caches, circuit breaker registries. All are per pod, so each pod learns independently.
- State that must be global across the cluster belongs in an external store, not in a singleton.

## 34. Factory Patterns

Intent: encapsulate object creation so callers depend on an abstraction and not on concrete classes.

| Variant | Idea |
|---|---|
| Simple factory | One method with a switch that returns the right implementation (not a GoF pattern) |
| Factory Method | Subclass decides which class to instantiate |
| Abstract Factory | Creates a family of related objects without specifying concrete classes |

```text
 Client --> PaymentProcessorFactory.forMode(mode) --> <<PaymentProcessor>>
                                                         ^        ^        ^
                                                    UpiProcessor NeftProcessor ImpsProcessor
```

```java
// Registry-based factory: no switch, honours Open/Closed. Spring injects all implementations.
@Component
class PaymentProcessorFactory {
    private final Map<Mode, PaymentProcessor> byMode;
    PaymentProcessorFactory(List<PaymentProcessor> all) {
        this.byMode = all.stream().collect(toMap(PaymentProcessor::mode, identity()));
    }
    PaymentProcessor forMode(Mode m) {
        return Optional.ofNullable(byMode.get(m))
                       .orElseThrow(() -> new UnsupportedModeException(m));
    }
}
```

Architect-level points:

- A switch factory violates OCP (edit on every new type); a registry/auto-wired map does not.
- Abstract Factory use: per-environment or per-region families (a bank client + auditor + notifier for India vs Singapore), per-tenant resource sets, test vs production implementations.
- Factory vs Strategy: the factory chooses and creates; the strategy is the interchangeable behaviour itself. They are commonly combined.
- In microservices: provider selection (primary/secondary bank), per-tenant client creation, feature-flagged implementation selection, and failover (the factory returns the healthy adapter, backed by a circuit breaker).
- Pitfalls: a god factory that knows everything; hidden dependencies created via new inside the factory (hard to test); creation logic mixed with business rules.

## 35. Observer Pattern

Intent: a subject notifies registered observers of state changes without knowing who they are (one-to-many, loose coupling).

```text
 Subject (OrderService) --publish OrderPlaced--> [Event bus / listener list]
                                                    |-> Observer: InventoryReserver
                                                    |-> Observer: NotificationSender
                                                    |-> Observer: AuditLogger

 Subject does not know the observers; new observer = no change to the subject (OCP).
```

```java
// In-process (Spring)
applicationEventPublisher.publishEvent(new OrderPlaced(order.id()));

@Component
class NotificationSender {
    @TransactionalEventListener(phase = AFTER_COMMIT)  // run only if the DB transaction committed
    void on(OrderPlaced e) { ... }
}
```

In-process observer vs distributed pub/sub:

|  | In-process observer | Kafka / message bus |
|---|---|---|
| Coupling | Same process, compile-time types | Contract/schema only |
| Delivery | Immediate, in order, lost on crash | Durable, at-least-once, replayable |
| Failure | Observer exception can break the subject (if synchronous) | Consumer failure is isolated (retry/DLQ) |
| Transactions | Can share the DB transaction (careful) | No shared transaction: need outbox |
| Ordering | Call order | Per partition only |

Architect-level points:

- Event-driven microservices are a distributed Observer, but you inherit new problems: at-least-once delivery (idempotent consumers), ordering, the dual-write problem (outbox), schema evolution, and eventual consistency.
- Transaction timing: if an observer sends an email or publishes to Kafka inside the transaction, a rollback leaves a phantom notification. Use AFTER_COMMIT or the outbox.
- Pitfalls: lapsed listener (never deregistered, memory leak); synchronous observers adding latency; hidden control flow; notification cascades (cycles); no backpressure with slow observers.
- Prefer async observers with bounded executors, isolated failures, and observability (trace the event through listeners).

## 36. How the Principles and Patterns Fit Together

```text
 DIP  →  Adapter (implements a domain-owned port; ACL around partners)
 OCP  →  Factory/registry (add types without editing), Observer (add listeners without editing)
 SRP  →  separates "create" (Factory), "translate" (Adapter), "react" (Observer), "decide" (domain)
 LSP  →  every Adapter/implementation must honour the port's behavioural contract
 ISP  →  small role-specific ports, so adapters stay small and mockable
```

Worked example: payment provider integration

Domain defines the PaymentGateway port (DIP, ISP).

HdfcAdapter and IciciAdapter implement it, translating models and errors, with timeouts and idempotency at the boundary (Adapter, LSP).

GatewayFactory selects the adapter by provider/region/health (Factory, OCP).

Payment outcome is published as PaymentCompleted through an outbox to Kafka, and Notification, Ledger, and Audit subscribe independently (Observer / pub-sub).

The scheduler for reconciliation runs once per cluster using a lease (Singleton, cluster-aware).
