# Distributed Tracing

## 1. The Big Picture

> A request travels through many microservices. How do we follow that one request from beginning to end without slowing down the actual application?

The design has 3 main paths:

1. **Ingest Path** — collect traces and decide which traces to keep.
2. **Store & Read Path** — save kept traces and allow engineers to search them.
3. **Control Plane** — change policies, monitor the system, and scale it.

---

# 2. Request Starts in Our Services

> OpenTelemetry SDK adds `trace_id` and `span_id` to every call.

```text
Request
   ↓
Service A
   ↓
Service B
   ↓
Service C
   ↓
Service D
```

### trace_id - This is the ID of the complete request journey.

### span_id - Each individual operation gets its own ID.

```text
trace_id = 12345

Service A → span A
Service B → span B
Service C → span C
```


---

# 3. Local Agent

```text
Your Services
      ↓
Local Agent
```

The agent:

- batches spans
- retries
- has a bounded queue

The business request should continue even if the tracing system is slow.

> **Fire-and-forget: the request never waits on tracing.**

---

# 4. What If the Tracing System Is Overloaded?

> **Queue full? Drop spans + count. Never block.**

So:

```text
Application
    ↓
Local Agent
    ↓
Queue full?
    ↓
YES
    ↓
Drop span
+
Count the drop
```

---

# 5. Agent Sends Spans to Ingestion Gateway

```text
Local Agent
      ↓
Ingestion Gateway
```

The gateway is:

> **Stateless, many copies behind a load balancer.**

The gateway is - **front door of the tracing platform**.

If too much traffic arrives:

> Don't allow tracing overload to hurt the application.

---

# 6. Gateway Sends Spans to Kafka

> **key = trace_id**

This is important. The reason is that spans belonging to the same trace should go to the **same assembler instance**.

---

# 7. Trace Assembler / Sampler

```text
Kafka
  ↓
Trace Assembler / Sampler
```

Why do we need this?

Because we don't want to immediately decide:

> "Keep this span."

We want to see the **whole trace first**.

The assembler maintains a:

> **Per-trace buffer**

For: a trace_id it collects all spans.
Now the system has the complete picture of the request.

---

# 8. Tail Sampling Decision

Once the assembler has enough information, it makes a decision.

The diagram says:

### KEEP if:

- error
- slow
- priority flow

Otherwise:

- keep a small random percentage

The decision looks like:

```text
Trace
 ↓
Was there an error?
 ↓
YES → KEEP

Was it slow?
 ↓
YES → KEEP

Is it priority?
 ↓
YES → KEEP

None of these?
 ↓
Keep only a small percentage
```

The important idea is:

> **We decide after seeing the complete trace, not at the beginning.**

---

# 9. What If the Trace Never Finishes?

The diagram has a:

### Sweeper

It says:

> **forces a decision after a max wait**

Imagine we are waiting for:

```text
Span A
Span B
Span C
Span D
```

But Span D never arrives.

We cannot wait forever.

So:

```text
Wait
 ↓
Maximum wait reached
 ↓
Sweeper
 ↓
Force decision
```

This prevents buffers from staying occupied forever.

---

# 10. DROP or KEEP

Now there are two possibilities.

### Not interesting

```text
Sampler
   ↓
DROP
```
> discard + count it

So we throw it away but still count the drop.

### Interesting

```text
Sampler
   ↓
KEEP
```

Then it goes to storage.

---

# 11. Hot Writer

> **Hot Writer saves KEPT traces**

And:

> **idempotent by span_id**

The important architecture idea is that the writer is separate from the sampling decision.

> **A slow database should not stall sampling.**

---

# 12. Hot Storage

> **Hot Storage — last 24–72 hours**

It uses:

> wide-column DB + TTL

with:

```text
key = trace_id
```

Think:

```text
Today
Yesterday
Last 2 days
      ↓
  HOT STORAGE
```

Recent traces stay in fast storage.

---

# 13. Query Service

Engineers don't directly access the database.

Instead:

```text
Engineer
   ↓
Query Service
   ↓
GET /v1/traces/{trace_id}
   ↓
Hot Storage
```

The diagram says:

> **checks hot first, cold if older**

So the Query Service decides where to look.

If the trace is recent:

```text
Query
 ↓
Hot Storage
```

If it is old:

```text
Query
 ↓
Cold Storage
```

This hides storage complexity from the user.

---

# 14. Dashboards / Alerts / On-call

The Query Service feeds:

```text
Dashboards
Alerts
On-call tools
```

So engineers can actually use the tracing data.

The read path becomes:

```text
Engineer
   ↓
Query Service
   ↓
Hot / Cold Storage
   ↓
Trace
```

---

# 15. Old Traces Move to Cold Storage

Hot storage is not meant to keep everything forever.

The diagram shows:

```text
Hot Storage
    ↓
Tiering Job
    ↓
Cold Storage
```

The tiering job moves old traces out.

The diagram uses:

> **S3**

as cold storage.

The diagram shows retention of:

```text
7 days
+
90 days for regulated flows
```

---

# 16. Eventually Delete the Data

After the retention period:

```text
Cold Storage
     ↓
Retention expires
     ↓
Hard Delete
     +
Audit Log
```

So the storage lifecycle is:

```text
HOT
 ↓
COLD
 ↓
EXPIRE
 ↓
DELETE
 +
AUDIT
```

---

# 17. Control Plane

The diagram has a separate section:

> **CONTROL PLANE**

This is how operators control the tracing system without changing the application.

There are three important areas.

---

## A. Operator / SRE / Compliance

They can change:

```text
Sampling policy
Retention policy
Purge a trace
Review
Audit
```

They don't directly change the components.

They go through:

```text
Operator
   ↓
Control API
```

---

# 19. Monitoring

The Local Agents send heartbeats. The monitoring system watches things like:

```text
Queue depth
Drops
Assembler buffer %
Evictions
```

So the system knows:

> "Are we becoming overloaded?"

---

# 20. Autoscaling

The diagram has a simple rule:

> **Autoscaler adds assemblers when buffer ≥70%.**

So:

```text
Assembler buffer
       ↓
   ≥ 70% ?
       ↓
      YES
       ↓
Autoscaler
       ↓
Add more assemblers
```

This allows the system to handle increased tracing traffic.

---

# 21. The Entire Diagram in One Simple Story

One customer request travels through the system like this:

```text
Customer Request
      ↓
80+ Microservices
      ↓
OpenTelemetry
      ↓
trace_id + span_id
      ↓
Local Agent
      ↓
Ingestion Gateway
      ↓
Kafka
      ↓
Trace Assembler
      ↓
Collect all spans
      ↓
Tail Sampling
      ↓
 ┌───────────────┐
 │               │
DROP            KEEP
 │               │
 ↓               ↓
Discard       Hot Writer
                  ↓
             Hot Storage
                  ↓
             Query Service
                  ↓
          Dashboard / Engineer
```


And around the whole system:

```text
Operator / SRE
      ↓
Control API
      ↓
Policy Store
      ↓
Assemblers / Tiering

Monitoring
      ↓
Metrics
      ↓
Autoscaler
      ↓
More Assemblers
```

---

# 22. Architect's Core Thinking

The diagram is essentially making four strong architectural decisions:

### 1. Never slow the business request because of tracing
### 2. Use Kafka + `trace_id`
### 3. Decide KEEP/DROP after seeing the trace

The system can recognize:

- errors
- slow traces
- priority flows

before deciding what to retain.

### 4. Separate responsibilities

```text
Ingestion
   ↓
Sampling
   ↓
Storage
   ↓
Query
   ↓
Control
```

Each part can therefore be managed and scaled independently.

---

# 23. One-Line Memory Flow

> **Service → Agent → Gateway → Kafka → Assembler → KEEP/DROP → Storage → Query**

And the control/operations side is:

> **Operator → Control API → Policy Store → Components**

The central flow to remember is:
