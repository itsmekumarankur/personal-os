# Microservices Architect Interview Notes (Final, Merged Edition)

This file merges two earlier documents into one:

- **Part 1: Architect notes.** Trade-offs, failure modes, internals, numbers, 15 hard scenarios, SOLID and design patterns. This is the main material.
- **Part 2: Foundations and quick-reference Q&A.** The earlier guide, kept intact: definitions, diagrams, ready-to-use YAML/config samples, and a classic scenario set. Use it for fast revision and as the source of copy-paste snippets. Its items are prefixed `Ref-` (for example `Ref-Q8`, `Ref-SC3`) so they never clash with Part 1 IDs.

Defaults quoted (HPA 15 s loop, 300 s scale-down window, Istio default retries, Eureka timings, etc.) are from memory of recent versions. Verify against the versions you run before quoting them in an interview.

## How the two parts relate

| Topic | Part 1 (deep, architect level) | Part 2 (reference Q&A and snippets) |
|---|---|---|
| Boundaries, consistency, saga, outbox, idempotency | A1 to A10 | P2.1 (Ref-Q1 to Ref-Q13) |
| Service-to-service security | B1 to B8 | P2.2 (Ref-S1 to Ref-S8): Istio and NetworkPolicy YAML |
| Service discovery | C1 to C7 | P2.3 (Ref-D1 to Ref-D6): probe YAML |
| Timeouts, retries, bulkhead, fallback | D1 to D4, D8 to D10 | P2.4 (Ref-R1 to Ref-R10): Resilience4j and Istio YAML |
| Circuit breaker | D5 to D7 | P2.5 (Ref-CB1 to Ref-CB9): Resilience4j config |
| Helm | E1 to E8 | P2.6 (Ref-H1 to Ref-H9): chart tree, hooks, Deployment template |
| HPA and scaling | F1 to F10 | P2.7 (Ref-K1 to Ref-K10): HPA and KEDA manifests |
| Scenarios | G (SC1 to SC15, architect level) | P2.8 (Ref-SC1 to Ref-SC15, classic set) |
| SOLID and design patterns | I1 to I6 | not covered in the earlier guide |
| Checklist and numbers | H | P2.9 cheat sheet |

**Suggested study order:** read Part 1 sections A to F, then the scenarios in G (answer each aloud before reading the answer), then I, then skim Part 2 for the snippets and the classic scenarios.

## Contents

**Part 1: Architect notes**

- A. Architectural judgement (A1 to A10)
- B. Service-to-service security (B1 to B8)
- C. Service discovery (C1 to C7)
- D. Resilience: timeouts, retries, circuit breaker, bulkhead, shedding (D1 to D10)
- E. Helm and delivery (E1 to E8)
- F. HPA and scaling (F1 to F10)
- G. 15 scenario questions (SC1 to SC15)
- H. Architect checklist and numbers
- I. Design principles (SOLID) and patterns: Adapter, Singleton, Factory, Observer (I1 to I6)

**Part 2: Foundations and quick-reference Q&A (earlier guide)**

- P2.1 Core concepts (Ref-Q1 to Ref-Q13)
- P2.2 Service-to-service security (Ref-S1 to Ref-S8)
- P2.3 Service discovery (Ref-D1 to Ref-D6)
- P2.4 Resilience patterns (Ref-R1 to Ref-R10)
- P2.5 Circuit breaker deep dive (Ref-CB1 to Ref-CB9)
- P2.6 Helm deployment (Ref-H1 to Ref-H9)
- P2.7 Horizontal scaling and HPA (Ref-K1 to Ref-K10)
- P2.8 Classic scenario-based questions (Ref-SC1 to Ref-SC15)
- P2.9 Quick revision cheat sheet

---

# PART 1: ARCHITECT NOTES

Assumes you already know the basics. This part is about trade-offs, failure modes, internals, numbers, and how to reason out loud.

---

# A. Architectural Judgement

## A1. Sync call chains: what does depth do to availability and latency?

Availability multiplies down the chain, and tail latency grows with fan-out.

```
 Place-order flow: GW -> Order -> Pricing -> Risk -> Payment -> Ledger   (6 sync hops)
 each hop 99.9%   =>  0.999^6 = 99.40%   =>  ~52 h/yr of flow downtime
 (one 99.9% service alone allows ~8.8 h/yr)

 Fan-out tail latency: call N backends in parallel, each p99 = 1 s
   P(at least one exceeds 1 s) = 1 - 0.99^N
   N=10 -> 9.6%     N=50 -> 39.5%     N=100 -> 63%
```

**Levers, in order of usefulness:**
1. Remove hops from the synchronous path (accept durably first, process after).
2. Make hops optional (degrade instead of fail).
3. Cache or replicate data locally so you do not call at all.
4. Merge services that are always co-called and co-deployed.
5. Add redundancy per hop (multi-AZ, hedging for reads).

**Probe:** "Why not just make every service 99.99%?" Because you cannot test or operate to that, and the product of many 99.99% services is still lower. Reduce the number of things that must be up.

---

## A2. How do you draw service boundaries beyond "one per bounded context"?

Use **invariants and change coupling**, not entities.

- An **invariant that must hold atomically** (balance never negative, units allotted never exceed available units) lives inside **one** service and one local transaction. If a boundary forces you to enforce it across two services, the boundary is wrong or you must accept compensation and a pending state.
- **Change coupling:** look at Git history and release logs. If two services change together in more than about 30% of releases, they are one service pretending to be two.
- **Distributed-monolith indicators:** co-deploy requirements, call-graph depth above 3, a shared schema, a "common" library that carries domain logic, synchronous request/response between two services for every user action.
- **Team topology:** a service should be ownable by one team. A service that needs three teams' approval to change is a coordination problem.

**Probe:** "Order and Payment are always called together. Merge them?" Not necessarily. Ask whether they have different scaling, compliance, or availability needs and different owners. If not, merge. If yes, keep them separate but **remove the sync coupling** (order accepted, payment as an async step).

---

## A3. Classify invariants before choosing a consistency mechanism.

| Invariant class | Example | Mechanism |
|---|---|---|
| Hard, single-owner | Balance cannot go negative | One service, local ACID, optimistic version or row lock |
| Hard, cross-service | Total allotment cannot exceed an IPO quota | Single owner of the counter (reservation service); others ask it. Do not replicate and "sync" |
| Bounded-stale | Portfolio value shown to user | Event-fed projection, show an "as of" timestamp |
| Eventual | Analytics, notifications | Async events, at-least-once, idempotent consumers |

The mistake to call out: replicating a hard invariant (quota, limit, stock count) into several services and reconciling later. That produces over-allotment. Give it a single owner and make others call or reserve against it.

---

## A4. Saga pitfalls an architect must name: isolation anomalies and pivot steps

Sagas give atomicity and durability but **not isolation**. Other transactions can see intermediate state.

**Anomalies:** lost update (another saga overwrites your intermediate result), dirty read (reads data a compensation will later reverse), non-repeatable read.

**Countermeasures (Richardson):**
- **Semantic lock:** a `PENDING` flag on the aggregate that other sagas respect (reject, wait, or treat as unavailable).
- **Commutative updates:** design operations so order does not matter (`+500` / `-200`, not `set balance`).
- **Pessimistic view:** reorder steps so risky dirty reads happen less.
- **Reread value / version file:** verify the value has not changed before overwriting.

**Step ordering (very important):**

```
 compensatable steps  ->  PIVOT (point of no return)  ->  retryable steps
 e.g. reserve units   ->  debit customer             ->  confirm allotment, notify
      (cheap undo)        (hard to undo)                  (can retry until success)

 Put cheap-to-undo and likely-to-fail steps first. Put hard-to-undo, customer-visible steps last.
 After the pivot, only steps that can be retried to success remain.
```

Other requirements: persist saga state (survives orchestrator crash), per-step timeouts, **idempotent and out-of-order-tolerant compensations** (a compensation can arrive before the action it compensates because of retries and reordering, so it must handle "nothing to undo yet" by recording a tombstone), and a stuck-saga escalation path.

---

## A5. Outbox vs CDC vs polling relay: ordering, duplicates, growth

```
 TX { business rows + outbox row }  -- commit -->  relay  -->  Kafka (key = aggregateId)
```

| Relay | Pros | Cons |
|---|---|---|
| Polling publisher | Simple, no extra infra | Latency, DB load, ordering breaks with multiple pollers (use a single poller per shard or `SELECT ... FOR UPDATE SKIP LOCKED` per aggregate partition) |
| CDC (Debezium on WAL) | Low latency, preserves commit order per table | Operational complexity, connector lag, schema coupling to the outbox table |

**Points that show depth:**
- Ordering is only per partition key. Use `aggregateId` as the key so one aggregate's events stay ordered.
- Delivery is at-least-once. The relay can crash after publish and before marking sent, so consumers need an **inbox** table (processed event IDs) or naturally idempotent writes.
- Outbox table growth: purge or partition by time, do not let it become a hot table.
- Kafka "exactly-once" (transactions) holds only inside Kafka (read, process, write to Kafka). It does not cover your database or HTTP side effects.
- Relay lag is a metric you alert on, because it is invisible business delay.

---

## A6. Idempotency design in depth

Basic idempotency keys are not enough. The details that fail in production:

- **Key scope:** `(client or tenant, operation, key)`. A global key space lets one client replay another's key.
- **Request fingerprint:** store a hash of the payload. Same key with a different payload returns `422`, not the old response.
- **In-progress state:** a second request arrives while the first is running. Return `409` or wait on the result. Do not run twice.
- **Atomicity:** the key insert and the business write must be in the **same transaction**. Otherwise a crash between them either loses idempotency or loses the work.
- **External side effects:** you cannot make a remote bank call "transactional" with your DB. Pass the **same reference** to the bank so the bank deduplicates, and design for **unknown outcome** (see SC3).
- **TTL:** longer than the longest client retry window plus replay by queues (hours to days), not minutes.
- Store and replay the **response**, so the retried caller gets the same answer.

---

## A7. Event ordering, retry topics, and schema evolution

- Kafka orders per **partition**. Same business key means same partition.
- **Non-blocking retry topics break per-key ordering** (message B overtakes failed message A). For ordered streams, either (a) block on the key (pause/park that key, not the partition), (b) carry a **per-aggregate sequence/version** and have the consumer apply only `last+1`, buffering or parking others, or (c) make handlers **state-based and commutative** (apply by max version).
- **Event-carried state transfer** (event holds full state) lets consumers be state-based and tolerant of reordering. **Notification events** (just an ID) force a callback, creating coupling and load.
- **Schema registry compatibility:** BACKWARD (new schema can read old data) lets consumers upgrade first. FORWARD lets producers upgrade first. FULL is safest. Enforce in CI.
- Never change the meaning of a field; add a new one. Use **upcasters** for stored events.

---

## A8. Read-your-writes with async projections (CQRS)

User places an order, the UI immediately lists orders from the read model, and it is missing.

Options:
- Return a **version/offset token** with the write; the read API waits (bounded) until the projection has reached it, or routes to the write model.
- **Optimistic UI** with local state merged until the projection catches up.
- **Session-sticky read from the write store** for a short window after a write.
- Show an explicit "processing" state instead of pretending consistency.

---

## A9. Where to put orchestration: edge, domain service, or no one?

- **Gateway/BFF aggregation:** fine for read composition. Do not put write workflows or business rules there.
- **Domain orchestrator** (workflow engine, for example Temporal/Camunda, or a saga service) for multi-step write flows with timeouts and compensation. It gives visibility, retries, and durable state.
- **Choreography** for loosely related reactions (notify, analytics). Becomes unmaintainable when it encodes a business process nobody can see end to end.
- Avoid service-to-service chains where A calls B calls C for every request. If it is a workflow, make it one.

---

## A10. Safe rollout across independently deployed services

- **Expand/contract** for schemas and APIs (additive first, remove later after zero traffic).
- **Consumer-driven contract tests** gate the provider build.
- **Decouple deploy from release** with feature flags, so code goes out dark and is switched on gradually.
- **N-1 compatibility rule:** any version must work with the previous and next version of its neighbours and its schema.
- **Shadow traffic / dark launch** for risky rewrites (compare responses without affecting users).

---

# B. Service-to-Service Security

## B1. Walk me through exactly how Service A securely calls Service B.

```
 End user --HTTPS--> [Gateway/Ingress]
   1. TLS terminated, JWT validated (sig via JWKS, iss, aud, exp), rate limit, WAF
   2. Inbound x-user-* headers STRIPPED; gateway sets verified context (or mints internal token)
                         |
                         v  (mesh mTLS, workload identity)
 +---------------+  3. NetworkPolicy: A's pod IP may reach B:8080 (L3/L4)
 | A: Order      |  4. mTLS handshake: A proves spiffe://td/ns/orders/sa/order
 |  [sidecar]    |     B's sidecar verifies cert chain to trust bundle; encrypted channel
 +-------+-------+  5. AuthorizationPolicy at B's sidecar: principal order may POST /payments
         |          6. Request carries user context (verified JWT or internal signed token)
         v          7. B's app: authorise user vs resource ("does this user own account X?")
 +---------------+  8. B calls Bank with its OWN credential (workload identity / short-lived)
 | B: Payment    |
 +---------------+
```

**What each control actually proves**

| Control | Proves | Does NOT prove |
|---|---|---|
| NetworkPolicy | Packet may reach the pod | Who sent it |
| mTLS | Caller workload identity, channel confidentiality/integrity | Caller is allowed to do this; which user |
| AuthorizationPolicy (mesh) | This service identity may call this route | User-level permission |
| JWT / internal token | On whose behalf, with which scopes | That the calling service is legitimate (needs mTLS) |
| App authorisation | This user may touch this resource | Anything about transport |

Defence in depth means a failure of any one layer is not a breach. "mTLS is enough" is the wrong answer: it authenticates, it does not authorise.

---

## B2. How does workload identity really work (SPIFFE/Istio style)? What breaks it?

```
 Pod starts -> sidecar generates key pair -> sends CSR to istiod over SDS, presenting its K8s
 ServiceAccount token -> istiod validates token with the API server -> issues short-lived X.509
 SVID (default ~24h) with SAN spiffe://<trust-domain>/ns/<ns>/sa/<sa> -> rotated automatically
```

- Identity is bound to the **ServiceAccount**, not IP or hostname. Pod IPs are recycled constantly, which is why IP allow-lists are unsound.
- **Trust domain / trust bundle:** multi-cluster needs a shared root or federated bundles. Plan root CA rotation with **overlapping trust bundles**.
- **Failure modes:** control plane down for longer than cert lifetime means certs expire and east-west traffic dies (see SC8). Clock skew breaks validation. A sidecar or node compromise yields that workload's identity (blast radius is that identity's AuthorizationPolicy, so keep identities narrow: one ServiceAccount per service, never `default`).
- Sidecar vs **ambient** (node-level ztunnel + optional waypoint): ambient cuts per-pod overhead but moves identity enforcement to the node component. Know the trade-off.

---

## B3. Identity propagation: which identity do you carry between services?

There are three identities in play: the **calling service**, the **end user**, and sometimes the **original client/app**.

| Pattern | Use when | Risk |
|---|---|---|
| Forward the user's JWT as is | Simple, user-scoped calls | Token has audience = gateway; every downstream holds a powerful, replayable token (confused deputy) |
| **Token exchange (RFC 8693)** at each trust boundary | Downstream needs narrower `aud`/scope | Extra hop to STS; needs caching |
| **Internal signed context token** minted at the edge ("passport"), short TTL (minutes) | Many internal hops, avoid re-validating external token | You own the minting service; keep key rotation tight |
| Service's own **client-credentials** token | System-initiated actions (batch, reconciliation) | Must not be used to "act as" a user |

**Rules:**
- Downstream authorises on **both**: the calling service identity (mTLS) **and** the user claims. Use the `act` (actor) claim to record "service X acting for user Y".
- **Never trust plain headers** like `X-User-Id`. An internal attacker or buggy service can forge them. Strip them at the edge and accept only cryptographically verified context.
- Token lifetime vs revocation: JWTs cannot be revoked. Use short TTL plus a `jti` denylist or introspection for high-risk operations only.
- Token size grows with claims; large JWTs in every hop cost bandwidth and header limits. Pass references or a minimal internal token.

---

## B4. Where does authorisation live? Mesh, service, or central PDP?

```
 Coarse (who may call what)  -> mesh AuthorizationPolicy (cheap, uniform, no code)
 Domain (who may see what)   -> inside service (needs data: ownership, relationships)
 Cross-cutting rules         -> policy engine (OPA/Cedar) as library or sidecar with
                                policy bundles pulled periodically
```

**Central online PDP trade-offs:** consistent policy, but a hot-path network dependency (latency, availability, blast radius). Prefer **local evaluation** (embedded or sidecar OPA with pushed bundles) so the PDP outage does not stop traffic. Decide **fail-open vs fail-closed per operation class** (SC15). Keep policy as code in Git with tests, and log decisions for audit.

---

## B5. How do you introduce mTLS STRICT and default-deny across 80 live services without an outage?

```
 Phase 0  Inventory & telemetry: who calls whom, which clients are outside the mesh
 Phase 1  PeerAuthentication PERMISSIVE mesh-wide (accepts plaintext + mTLS), inject sidecars gradually
 Phase 2  Observe: dashboards for plaintext traffic by source/destination; fix each source
 Phase 3  STRICT per namespace, lowest risk first; canary a few services per wave
 Phase 4  Default-deny AuthorizationPolicy in audit mode (dry-run), review denies, then enforce
 Phase 5  Egress control (default-deny egress, allow-list via egress gateway)
 Rollback per wave: switch that namespace back to PERMISSIVE (keep it fast: it is config)
```

**Gotchas that cause real incidents:**
- Non-mesh callers (cron jobs, legacy VMs, other clusters, monitoring scrapers).
- **kubelet probes** cannot do mTLS; the injector rewrites probes, so verify they still work.
- **Jobs/CronJobs** never finish because the sidecar keeps running (use native sidecars or the quit endpoint).
- **Startup race:** app container calls out before the sidecar is ready (hold application until proxy ready).
- Headless/StatefulSet and TCP protocols (databases, Kafka) need explicit protocol and port settings.
- Per-hop latency and CPU/memory overhead; account for it in capacity planning.

---

## B6. What are the real operational risks of a service mesh?

- **Control plane outage as a time bomb:** certs have a TTL (hours). If the CA cannot issue before expiry, everything fails at once. Mitigate with HA control plane, expiry alerts, overlapping roots, and a practised break-glass.
- **Config push storms:** a large mesh pushing config to every sidecar on each change causes CPU spikes and stale configs. Scope sidecar config (`Sidecar` resource) so each proxy only knows its dependencies.
- **Sidecar as a failure domain:** OOM, misconfig, or version skew breaks traffic with errors that look like app bugs.
- **Double behaviour:** retries, timeouts, and breakers in both mesh and app (D9).
- **Debuggability:** an extra hop in every call. Require good proxy access logs and trace propagation.

---

## B7. Securing asynchronous (Kafka/event) communication

- **Authentication and ACLs per principal** (mTLS or SASL): each service may produce/consume only its topics and consumer groups.
- User context across async: the original JWT will have **expired by the time it is consumed**. Carry a **signed context/claims header** (JWS) or the minimal identifiers and re-authorise by policy with the actor recorded.
- **Sensitive data:** field-level or envelope encryption for PII, since brokers, DLQs, and replay tooling are wide-access surfaces. Avoid putting PII in keys.
- Schema registry and topic-creation permissions are part of the attack surface; restrict them.
- DLQ and replay tooling can resurrect sensitive messages and re-trigger side effects, so treat them as privileged.

---

## B8. Secrets, cloud credentials, and egress

- Prefer **workload identity to cloud APIs** (IRSA/Workload Identity) over static keys. No long-lived credentials in pods.
- Dynamic, short-lived DB credentials (Vault) bound to workload identity. Rotation must not require redeploys (file mounts and reload, not env vars; env vars leak through crash dumps and `/proc`).
- Kubernetes Secret is base64 only: enable etcd encryption, tight RBAC, avoid secrets in Helm values and Git (External Secrets / SOPS / CSI driver).
- **Egress:** default-deny, allow-list destinations through an egress gateway. It limits exfiltration and C2 after a compromise, and makes third-party dependencies explicit.

---

# C. Service Discovery

## C1. Kubernetes discovery: data path and propagation delays

```
 Pod Ready --> endpoint controller --> EndpointSlice --> kube-proxy sync (iptables/IPVS)
                                                      --> ingress/mesh config push
 each stage: ~100 ms to several seconds, NOT atomic, NOT ordered with SIGTERM

 Client: DNS (CoreDNS) -> ClusterIP -> node rules (DNAT) -> pod IP (only Ready endpoints)
```

- EndpointSlices (default up to 100 endpoints per slice) replaced single large Endpoints objects, reducing update fan-out.
- **Termination race:** on delete, SIGTERM and endpoint removal happen in parallel. Traffic can still be routed to a terminating pod for seconds (preStop sleep plus graceful drain, see SC15 and E6).
- **Readiness vs discovery:** an unready pod is removed from endpoints but not restarted.

---

## C2. kube-proxy modes and scaling limits

| Mode | Behaviour | Issue at scale |
|---|---|---|
| iptables | Linear rule chains per Service/endpoint | Rule sync time and packet-path cost grow with thousands of Services/endpoints |
| IPVS | Hash-based, O(1) lookup | Needs kernel modules; still conntrack-based |
| eBPF (e.g. Cilium kube-proxy replacement) | In-kernel service load balancing | Operational and kernel version requirements |

Also: **conntrack table exhaustion** produces random drops under high connection churn. LB is **per connection**, not per request.

---

## C3. DNS in Kubernetes: why you get mysterious 5-second delays

- `ndots:5` means any name with fewer than 5 dots (for example `api.example.com`, which has 2) is tried against each search domain first: `api.example.com.<ns>.svc.cluster.local`, `...svc.cluster.local`, `...cluster.local`, then the real name. Multiple failed lookups per call.
- Parallel A/AAAA UDP lookups can hit a **conntrack race** and one packet is dropped, so the resolver waits its **5 s** timeout before retrying.
- CoreDNS saturation under high QPS or an expensive upstream.
- **Fixes:** NodeLocal DNSCache, trailing-dot FQDNs for external names (or lower `ndots`), cache in the client, reduce external lookups, scale CoreDNS, `single-request-reopen` options where applicable.
- **JVM caching:** `networkaddress.cache.ttl` may cache successful lookups for a long time (forever under a security manager). After pod IPs change the app keeps calling dead IPs. Set it explicitly (for example 10 to 30 s) and set `negative.ttl`.

---

## C4. Long-lived connections defeat load balancing (gRPC / HTTP/2 / pools)

```
 Before scale-out: 5 pods, each holds N long-lived connections from clients
 HPA adds 15 pods...  clients keep their existing connections -> new pods get ~0 traffic
 old pods still at 90% CPU, new pods at 2%
```

**Fixes:**
- L7-aware balancing (Envoy/mesh balances per request across HTTP/2 streams).
- Headless Service plus client-side LB with periodic re-resolution.
- Server-side **max connection age with grace** (gRPC `MAX_CONNECTION_AGE`), so clients reconnect and rebalance.
- Recycle connection pools (DB, Redis) deliberately.

Also affects scaling signals: **average** CPU hides the hot pods.

---

## C5. Client-side registry (Eureka/Consul) vs platform-native: the real trade-offs

- **CAP stance:** Eureka is AP (serves stale rather than nothing, with self-preservation). Consul is CP for its KV/catalog via Raft, plus health checks.
- **Staleness stack** (Eureka defaults): heartbeat 30 s, eviction after about 90 s, server response cache, client fetch interval 30 s, client LB cache. Total window for a dead instance to remain visible is **minutes**, so you need **client retries on a different instance plus circuit breaker**.
- **Registry outage:** clients use the cached list (good), but new instances are invisible and dead ones stay.
- **In Kubernetes** a second registry creates two sources of truth that disagree (pod killed but still registered). Prefer native Services plus mesh. Use Consul/Eureka only for cross-platform (VMs plus K8s) estates.

---

## C6. Health semantics: what belongs in readiness, liveness, startup?

- **Liveness:** the process only (deadlock detection). Never check dependencies. A DB blip would restart every pod.
- **Readiness:** can this instance serve **now**: local init done, critical config loaded, warm enough. Including *downstream* checks here is dangerous: when a shared dependency blips, **all** pods go unready, endpoints drop to zero, and a partial degradation becomes a total outage.
- **Startup:** protect slow-starting JVMs from liveness restarts.
- **Envoy panic threshold** (default: if fewer than about 50% of hosts are healthy, route to all hosts) is an intentional behaviour. Know it so unexpected traffic to "unhealthy" hosts is not a surprise.
- Use `readinessGates` for external readiness (load balancer registration) and a controlled **drain state** that fails readiness before shutdown.

---

## C7. Multi-cluster and multi-region discovery, locality, and failover

```
 Region A cluster  <--east-west gateway (mTLS)-->  Region B cluster
   svc payment (local endpoints)  +  remote endpoints (lower priority)

 Locality LB: prefer same zone -> same region -> remote
 Failover requires OUTLIER DETECTION/health checks enabled, or the proxy never ejects a bad zone
```

- **Topology-aware routing** reduces cross-AZ latency and cost, but can overload a small zone (uneven zone sizes). Watch for hot spots.
- Mesh multi-primary vs primary-remote, or MCS (`ServiceImport`) for plain Kubernetes. Shared trust domain/roots needed.
- Test failover regularly. Untested failover usually fails on capacity (the surviving region cannot absorb load) or hard-coded dependencies.

---

# D. Resilience

## D1. Little's law: why slow is worse than down, and how to size

```
 Concurrency (L) = Throughput (λ) x Latency (W)

 Payment-svc: 500 req/s, Bank latency 200 ms  ->  L = 100 in-flight calls   (pool of 200: fine)
 Bank degrades to 30 s, still 500 req/s        ->  L = 15,000 needed        (pool 200: saturated in <1 s)
```

Consequences:
- Thread/connection pools saturate almost immediately; the service looks "down" including its health endpoints.
- Liveness restarts then remove capacity and concentrate load: a **death spiral**.
- Size pools from `λ x p99 latency x headroom`, and **bound queues** (an unbounded queue turns overload into unbounded latency).
- Isolate the management/health port on its own thread pool.

---

## D2. Timeouts: the layered model and the bugs that hide

Layers: DNS, connect, TLS handshake, **pool acquisition**, request/response, and an overall **deadline**.

```
 Client 5 s | Gateway 4 s | Order 3 s | Payment 2 s | Bank 1.5 s     (inner < outer)
 Better: propagate the DEADLINE (gRPC does; else a header like x-deadline-ms) and each hop
         computes remaining = deadline - now; refuses if too little left.
```

**Setting values:** from the percentile of **successful** calls (p99 plus margin), not from the incident worst case. Different per operation (read vs write).

**Common bugs:**
- **No pool-acquisition timeout:** threads queue forever on the HTTP client pool, so the downstream timeout never fires.
- **Client gives up, server keeps working** (no cancellation), so wasted work plus retries equals overload. Propagate cancellation, set server-side deadlines and DB statement timeouts.
- **Idle-timeout mismatch:** LB idle 60 s vs app keep-alive 75 s causes resets on reused connections (intermittent 502). The app's keep-alive must be longer than the LB's.
- Timeouts on async/non-blocking clients that do not actually cancel the underlying I/O.
- Defaults of "infinite" in many clients.

---

## D3. Retries: when they help, when they kill you

**Safe-retry matrix**

| Failure | Retry? |
|---|---|
| Connection refused / connect timeout (request never sent) | Yes, even for non-idempotent calls |
| 503 / 429 with `Retry-After` | Yes, honour the header |
| Read timeout on idempotent call | Yes, with backoff |
| Read timeout on non-idempotent call | Only with an idempotency key; the outcome is **unknown** |
| 4xx business/validation | Never |
| Circuit open (`CallNotPermitted`) | Do not hammer; fail fast or fallback |

**Mechanics:** exponential backoff with **full jitter** (`sleep = rand(0, min(cap, base * 2^n))`), small attempt count, and **deadline awareness** (do not retry if the remaining deadline is shorter than expected latency).

**Retry budget:** allow retries up to a fraction of normal traffic (for example 10%) via a token bucket (gRPC retry throttling, Envoy retry budgets). This turns retries into a bounded cost instead of a multiplier.

**Amplification:**

```
 GW(3) -> Order(3) -> Payment(3) -> Bank        3^3 = 27x load on Bank when it is struggling
 Rule: retry at ONE layer (usually the one nearest the failing call, with a budget); the others
       propagate errors. Mesh default retries (e.g. Istio default of 2 attempts) stack on top of
       app retries, so you get 9x from "3 and 3" without noticing.
```

**Hedging:** send a second request to another replica after p95 latency, cancel the loser. Reads only, with a budget. Cuts tail latency, costs load.

---

## D4. Metastable failures and retry storms

A system enters a state that **persists after the trigger is gone**, sustained by its own recovery behaviour.

```
 trigger: dependency slow 90 s
    -> timeouts -> retries -> 3x load                \
    -> queues full of requests whose callers gave up  >  sustaining loop, even after
    -> caches cold / pools drained / pods restarting  /   dependency is healthy again
```

**Mitigations:**
- **Load shedding** at the point of saturation (return 503 fast).
- **Drop expired work:** check the request deadline when dequeued. Do not process requests nobody is waiting for. Prefer **LIFO or adaptive queues** under overload.
- Retry budgets and circuit breakers to cut the amplification.
- Ramp traffic to cold instances (slow start) instead of full load at once.
- Operational: a **kill switch to disable retries or shed a traffic class**, and a runbook to "drain and refill" (cut the load to near zero, let the system recover, then restore gradually).

---

## D5. Circuit breaker design: what to measure and how to tune

```
        failure/slow rate >= threshold               wait elapsed (e.g. 30 s)
 CLOSED ------------------------------> OPEN ---------------------------> HALF-OPEN
   ^                                      (fail fast)                      (N probe calls)
   |__________ probes OK ________________________________________________|
                                         probes fail -> OPEN again
```

- Measure **failure rate and slow-call rate** (a call over, say, 2 s counts). Exceptions alone miss the most dangerous mode: latency.
- **Count-based** window for steady traffic; **time-based** for variable traffic.
- **minimumNumberOfCalls** matters at low traffic: with 2 calls, one failure is a 50% failure rate. Pick a minimum that gives statistical meaning.
- **Half-open:** limited probes (for example 5 to 10). Too few and one unlucky probe re-opens it (flapping). Too many and you stampede a recovering service.
- **Do not count** 4xx business/validation errors. **Do count** timeouts, connection errors, 5xx, 429/503.
- Needs real **timeouts** underneath; otherwise calls hang and are never recorded as failures.

---

## D6. Circuit breaker placement, partial failure, and per-instance vs per-service

- Breaker **per downstream dependency** (and per critical operation), not one global breaker.
- **State is per caller pod, in memory.** Do not share it through a central store; that adds a dependency to your resilience layer. It means each pod learns independently; new pods start CLOSED (a scale-out adds callers that have not learned yet).
- **Partial failure** (1 bad pod or one bad AZ out of N): an app-level service breaker sees a partial failure rate and either never opens (threshold 50%, failure 33%) or opens and cuts **100%** of traffic for a 33% problem. The right tools are **instance-level**: mesh **outlier detection** (eject the bad hosts), **retry to a different host**, and **locality failover**. Keep the service-level breaker for "the whole dependency is sick".

```
 33% of Payment pods bad:
   service breaker (threshold 50%)  -> stays CLOSED, users see 33% errors     (wrong tool)
   outlier detection (5xx streak)   -> ejects bad pods, errors -> ~0          (right tool)
   retry on different host          -> masks transient errors, adds 1.33x load
```

---

## D7. Circuit breaker x retry x timeout x bulkhead: composition and failure of the breaker itself

Resilience4j default order (outermost to innermost): `Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( call ) ) ) ) )`.

- Retry outside the breaker so each attempt is counted and an open breaker short-circuits the retries.
- **Do not retry `CallNotPermittedException`.**
- TimeLimiter inside so slow calls become recorded failures.
- Bulkhead innermost so it limits actual concurrent calls.

**Ways the breaker itself causes outages:**
- Misclassification (4xx counted) opens on bad user input.
- Window or minimum calls too small causes flapping.
- Self-invocation inside the same Spring bean bypasses the proxy, so the annotation does nothing.
- Opening on a **non-critical** dependency with no fallback, turning a feature failure into a request failure.
- Deploys or scale-outs resetting state, causing bursts into a sick dependency.

Operate it: expose state gauge, calls by outcome, failure rate; alert on state transitions; allow **manual force-open** (maintenance or emergency isolation).

---

## D8. Fail-open vs fail-closed, and fallback correctness

| Operation class | Dependency down | Policy |
|---|---|---|
| Money movement, trades | Authz, limits, ledger | **Fail closed** (reject or pend). Never fabricate state |
| Sensitive reads | Entitlement service | Fail closed or serve cached decision within a short TTL |
| Non-sensitive reads | Recommendations, pricing display | **Fail open** with stale cache and an "as of" label |
| Notifications, analytics | Anything | Async, drop or queue, never block |

- Stale data must have a **staleness bound** and be labelled.
- Log every fail-open decision (audit).
- **Static stability:** the data plane keeps working with last known config when the control plane is down.
- Fallbacks need their own tests. An untested fallback often throws.

---

## D9. Mesh-level vs application-level resilience: ownership split

| Concern | Prefer |
|---|---|
| mTLS, timeouts (coarse), outlier detection, locality failover, traffic shifting | Mesh (uniform, any language, no redeploy) |
| Fallbacks, business-aware retry decisions, idempotency, compensation | Application |
| Retries | **One owner.** Pick mesh or app, disable the other (Istio retries by default) |
| Timeouts | Mesh timeout must be **greater than** the app's per-try timeouts, otherwise the mesh cuts calls the app thinks are fine |

Mesh cannot do fallbacks or know business semantics. Mesh adds its own failure modes (B6).

---

## D10. Isolation: bulkheads, cells, and criticality tiering

- **Per-dependency bulkheads** (separate pools/semaphores). Semaphore bulkhead is cheap; **thread-pool bulkhead** gives stronger isolation but breaks `ThreadLocal` context (trace IDs, security context) and adds context switches.
- Separate **connection pools per dependency**, and a **separate pool/port for health and admin** endpoints.
- **Criticality tiers:** classify every dependency as critical (request fails without it), important (degraded), or optional (best effort). Optional dependencies must be async or behind a bulkhead plus fallback so they cannot take down the critical path (SC1).
- **Cell-based architecture / shuffle sharding:** partition users or tenants into cells, each with its own full stack, so a bad deploy or poison request hits only a fraction (blast-radius reduction).
- **Verify resilience** with fault injection. Inject **slowness** (more revealing than "down"), run game days, define a steady-state hypothesis, test retry amplification and failover capacity.

---

# E. Helm and Delivery

## E1. Chart architecture for 80 services

- A **library chart** (Deployment, Service, HPA, PDB, probes, security context, topology spread) plus **thin per-service charts** that supply values. Standards are enforced once.
- Define a **values contract** with `values.schema.json` so bad values fail at lint time, not at 2 a.m.
- Layer values: `base -> environment -> cluster/region -> (secrets from outside Git)`.
- **Image by digest** (immutable), not by mutable tag. Chart version and `appVersion` are different things; version and promote charts like artifacts (OCI registry).
- Umbrella charts couple release cadence; use them for platform bundles, not for independently released services.
- Avoid logic-heavy templates (conditionals everywhere). If a template needs a programming language, the chart is too generic.

---

## E2. Helm apply semantics and the pitfalls that bite in production

- Upgrade is a **three-way strategic merge** (old manifest, new manifest, live state). Out-of-band edits get partially reverted or preserved in non-obvious ways.
- **`replicas` ownership conflict:** if the Deployment template hardcodes `replicas` and an HPA is active, every upgrade resets the count. Omit `replicas` when HPA is enabled.
- **`--reuse-values` trap:** reuses old values and ignores new chart defaults, so new keys are missing. Prefer passing the full values set (or `--reset-then-reuse-values`).
- **Immutable fields:** Deployment `selector`, Job spec, PVC spec. Changing them fails the upgrade. Treat selector labels as permanent.
- **Release history lives in Secrets** in the namespace (size limited, roughly 1 MiB). Large charts or many revisions need `--history-max`.
- `--atomic` rolls back on failure but implies `--wait`; waiting on resources that never become Ready (a PDB or HPA misconfiguration, a Job) hangs until `--timeout`.
- **CRDs:** installed from `crds/` on first install only. Never upgraded or deleted by Helm, so manage them separately.
- Argo CD/Flux typically **render** charts (`helm template`) and apply, so there is no Helm release history and Helm hooks map to the tool's own hook model. Rollback is by Git.

---

## E3. Hooks: when they help, how they betray you

- Hook resources are **not part of the release** (no automatic cleanup except via `helm.sh/hook-delete-policy`). A Job with a fixed name fails on re-run (Jobs are immutable) unless you use `before-hook-creation`.
- A **pre-upgrade migration** runs while **old pods are still serving**, so the migration must be backward compatible (N-1). If the hook fails, the release is failed and the new version never rolls out, but the migration may be half-applied.
- Migrations in the app's startup race when several replicas boot simultaneously. Use a single Job or the tool's lock (Flyway/Liquibase lock).
- Long migrations and hook timeouts: prefer a separate pipeline stage with its own monitoring over a hook that blocks the release.
- Hooks do not run with `helm template`, and behave differently under GitOps controllers. Test your actual delivery path.

---

## E4. Rollback truth table: what Helm restores and what it does not

| Restored by `helm rollback` | NOT restored |
|---|---|
| Image, env, resources, probes, ConfigMaps as rendered in that revision | **Database schema and data** |
| Service/Ingress/HPA/PDB definitions | PVC contents, CRDs, secrets from external stores |
| | Messages already published, side effects, caches, feature-flag state |

- Rollback creates a **new revision** that re-applies old content.
- Therefore design for **N-1 compatibility** and prefer **roll-forward** with a fast fix when the data layer moved.
- Use **progressive delivery** (Argo Rollouts/Flagger): canary, automated analysis (error rate, latency SLOs), auto-abort. It catches issues before a full rollout makes rollback expensive.

---

## E5. Configuration rollouts: the "ConfigMap changed but pods did not restart" problem

- Changing a ConfigMap/Secret does not restart pods. Add a checksum annotation so the Deployment changes:

```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

- Better: **versioned immutable ConfigMaps** (name includes hash) so config and code roll together and roll back together.
- Config that is hot-reloaded needs its own safety (validation, last-known-good).

---

## E6. Zero-downtime chart defaults (what a good library chart enforces)

```yaml
strategy: { type: RollingUpdate, rollingUpdate: { maxSurge: 25%, maxUnavailable: 0 } }
terminationGracePeriodSeconds: 60          # > preStop + longest request
lifecycle: { preStop: { exec: { command: ["sleep", "10"] } } }   # let endpoints propagate
readinessProbe / livenessProbe / startupProbe   # different semantics (C6)
resources.requests set (needed by scheduler, HPA)   # memory limit = request; CPU limit debated
topologySpreadConstraints across zones and nodes
PodDisruptionBudget (maxUnavailable: 1 or 20%; NOT minAvailable = replicas)
priorityClassName for critical services
```

**Trap:** a PDB with `minAvailable` equal to replicas (or 100%) blocks node drains and Cluster Autoscaler scale-down forever.

---

## E7. Push (CI runs `helm upgrade`) vs pull (GitOps)

- **Pull (Argo/Flux):** Git is the desired state, drift detection and self-heal, audit trail, rollback by revert, no cluster credentials in CI. Cost: another system, hooks and ordering semantics differ, secrets need a pattern.
- **Fleet management:** ApplicationSets / ring deployments (canary cluster, then region, then rest) limit blast radius.
- **Promotion:** artifact promotion (same chart and digest through environments with different values), not rebuilding per environment.
- Decide who owns rollback (platform vs service team) and make it one command or one revert.

---

## E8. Testing and supply chain of charts

- `helm lint`, `helm template | kubeconform` (schema validation), unit tests (`helm-unittest`), and an ephemeral cluster install (kind) with `helm test`.
- **Policy as code** (OPA/Conftest/Kyverno): no `latest` tag, requests/limits and probes required, non-root, no privileged, signed images.
- Sign charts/images (cosign), pin by digest, generate SBOMs.

---

# F. HPA and Scaling

## F1. HPA control loop: exact semantics

```
 kubelet/cAdvisor -> metrics-server (scrape ~15-60 s) -> HPA controller (loop every 15 s)
   desired = ceil( currentReplicas x currentMetric / targetMetric )
   - within ~10% tolerance of target: no change
   - several metrics: compute each, take the MAX
   - pods not ready / no metrics yet: treated conservatively (assumed 0% usage when scaling up,
     100% when scaling down), which damps the ratio
   - defaults: scale-up policy up to +100% or +4 pods per 15 s;
               scale-down stabilization 300 s (uses the highest recommendation in the window)
```

**Effective reaction time** is the sum of: metric lag, loop interval, scheduling, possible node provisioning, image pull, application start, warm-up, readiness. Typically **minutes**, not seconds (F4). HPA is a **trend follower**, not a spike absorber.

---

## F2. Choosing the scaling signal (the most important HPA design decision)

| Signal | Good when | Danger |
|---|---|---|
| CPU % of request | CPU-bound services | I/O-bound services stay at low CPU while saturated; JVM startup spikes; limit throttling distorts |
| **In-flight concurrency per pod** | I/O-bound, request/response (best general signal) | Needs instrumentation and a measured per-pod capacity |
| RPS per pod | Predictable cost per request | Cost per request varies |
| Queue depth / consumer lag | Consumers (KEDA) | Capped by partitions |
| Latency | SLO-aware | **Scaling out on latency when the dependency is slow adds load and worsens it** |

**Sizing from Little's law:** `pods = ceil( peakRPS x p95Latency / targetConcurrencyPerPod ) x headroom`.

**Anti-pattern:** scaling callers when the **bottleneck is a downstream** (DB, partner API). More pods means more pressure and a worse outage (F6).

---

## F3. Requests, limits, and what HPA % actually means

- Utilisation is relative to **requests**, not limits. Requests too low means HPA sees 300% and over-scales; too high means under-scaling and wasted nodes. Derive requests from load tests and real p95 usage.
- **CPU limits cause CFS throttling:** latency spikes while average utilisation looks fine. Many teams set memory limit = request and omit CPU limits (trade-off: noisy neighbours, so use requests properly).
- **JVM:** container-aware heap (`-XX:MaxRAMPercentage`), explicit CPU count awareness, JIT warm-up. A fresh JVM delivers a fraction of steady-state throughput for its first minute or more.
- Memory is a poor HPA signal (the JVM does not release memory), so use it for VPA/requests tuning, not scaling.

---

## F4. Cold-start economics and spike handling

```
 spike at t=0
 t+30..60 s  metrics catch up
 t+75 s      HPA decides +N pods
 t+90 s      pods Pending -> (no capacity) Cluster Autoscaler/Karpenter provisions node: +60-180 s
 t+..        image pull, JVM start, warm-up: +30-120 s
 t+4..6 min  new pods Ready, and delivering ~30-60% of steady-state capacity at first
```

**Mitigations (combine):**
- `minReplicas` set from the **SLO and N+1 / AZ-loss** requirement, not from average load.
- **Scheduled/predictive scaling** before known events (KEDA cron, or pre-scale scripts).
- **Headroom:** target utilisation 50 to 60%, not 80%.
- **Overprovisioning** with low-priority "pause" pods that are preempted by real pods (warm node capacity).
- Faster start: smaller images, pre-pulled images, AppCDS/CRaC/native, lazy init, warm-up endpoint hit before readiness.
- **Slow-start / warmup** in the LB or mesh so new pods ramp up traffic instead of getting a full share instantly.
- **Admission control and queue-based load levelling** to absorb the spike while scaling catches up.

---

## F5. Scale-down safety

- Stabilization window and rate-limited policies (for example max 2 pods or 10% per minute).
- PDB and graceful drain: SIGTERM handling, preStop sleep, finish in-flight, close long-lived connections gracefully.
- **Kafka consumers:** scale-down triggers a rebalance. Use cooperative-sticky assignment and static membership to avoid rebalance storms and duplicate processing; ensure idempotent handlers.
- Do not scale down into a known daily peak; combine with scheduled floors.
- Flapping (up, down, up) costs more (cold starts) than carrying extra capacity briefly.

---

## F6. Capacity coupling: scaling the stateless tier moves the bottleneck

```
 DB max_connections 500 (shared by 7 services)
 Order: 8 pods x pool 20 = 160 today; HPA max 40 -> 800 (> 500)  => outage when scaling "works"
```

- Allocate a **connection budget per service**; derive `maxReplicas = budget / poolSize`.
- Use a pooler (PgBouncer/RDS Proxy). Know the caveat: transaction pooling breaks session state, advisory locks, and some prepared-statement usage.
- Pool size should come from `concurrency x fraction of time in DB`, not from "20 because default".
- Bounded pool wait with **fail-fast** so callers do not queue forever.
- Same coupling applies to: Kafka partitions (max useful consumers), partner API rate limits (use a global limiter, not per-pod), cache and hot-key limits.

---

## F7. HPA, VPA, KEDA, Cluster Autoscaler/Karpenter: how they interact

```
 traffic up -> HPA adds pods -> some Pending -> CA/Karpenter adds nodes -> pods schedule
 traffic down -> HPA removes pods -> nodes underused -> CA consolidates (PDBs/local storage/
                 annotations can block it)
```

- HPA and VPA must not act on the **same resource metric** (they fight). Use VPA in recommendation mode for requests, HPA for replicas.
- KEDA builds HPAs from event sources and scales to zero (watch cold-start latency for user-facing paths).
- Node provisioning latency dominates; Karpenter-style just-in-time provisioning is faster than node-group autoscaling but needs capacity planning for instance types, spot interruption handling, and quotas.
- ResourceQuotas, LimitRanges, and priority/preemption influence whether scale-out actually happens.

---

## F8. HPA during rollouts and GitOps

- During a rolling update, `maxSurge` temporarily adds pods; new-version pods are cold and old ones are draining. Metrics are noisy. Avoid deploying at peak and tune surge conservatively.
- `replicas` ownership: HPA owns it. Helm, Argo, or Flux must not override it (omit the field or ignore the diff).
- Canary with HPA: each version's Deployment may have its own HPA, or use a rollout controller aware of scale.
- A deploy that crashes pods causes HPA to compute on unready pods. Combine with progressive delivery that aborts on SLO breach.

---

## F9. HPA troubleshooting runbook

| Symptom | Likely causes |
|---|---|
| TARGETS `<unknown>` | metrics-server down/unreachable, **no resource requests**, custom metrics adapter issue |
| Not scaling despite load | Metric is not the bottleneck (I/O-bound), already at max, within tolerance, stabilization window, pods not Ready |
| Scaled but latency still bad | New pods Pending (no nodes), cold JVM, **connection pinning** (C4), downstream saturated |
| Scales up then flaps down | Aggressive scale-down policy, bursty metric, window too short |
| Resets after deploy | Helm/GitOps overriding `replicas` |
| Over-scales | Requests too low, startup CPU spike counted, throttling |
| Pods Pending | Node capacity, quotas, anti-affinity/topology constraints, PV zone |

Commands: `kubectl describe hpa`, `kubectl get hpa -w`, `kubectl top pods`, events, and metrics for `container_cpu_cfs_throttled_*`.

---

## F10. Capacity planning with AZ-loss survivability

```
 Required pods at peak (from F2 formula)           P = 24
 3 AZs, must survive loss of one AZ at peak:       remaining 2 AZs must hold 24
 => per-AZ = 12, total = 36   (i.e. run at about 67% utilisation of total capacity)
```

Plus: warm headroom for scale-up latency, and the cost trade-off stated explicitly (reliability is capacity you pay for even when idle). Combine with PDB, topology spread, and tested AZ failover.

---

# G. 15 Scenario Questions

Each: situation, what the interviewer is really testing, a strong answer, and the trap.

---

## SC1. Product wants 99.99% for "place order". The flow has six synchronous hops, each at 99.9%. What do you do?

**Testing:** availability math, ability to redesign rather than just "add retries".

**Answer:**
- Math: `0.999^6 = 99.4%`. Target of 99.99% allows ~52 min/yr; the current design gives ~52 h/yr.
- Classify each hop: which are required to **accept** the order versus to **complete** it?

```
 BEFORE (sync):  GW -> Order -> Pricing -> Risk -> Payment -> Ledger -> response
 AFTER:          GW -> Order  [validate + durable accept (DB + outbox)] -> 202 Accepted
                              |  events
                              v
                    Pricing(snapshot cached)  Risk(pre-trade limits local)  Payment  Ledger
                    (async workflow, saga, status via polling/push)
```

- Pricing: use a **cached price snapshot** with version, not a live call. Risk: **local limit state** updated via events (the hard invariant, if needed, lives in one reservation service). Ledger: async via outbox.
- Availability of the accept path now equals GW + Order + its datastore, multi-AZ. Define the SLO on **acceptance** (99.99%) and a separate SLO on **completion time** (p99 under N seconds).
- Add criticality tiers and bulkheads for anything left synchronous.
- Negotiate with product what "available" means (accepted vs completed), and manage via error budgets.

**Trap:** answering "retries and circuit breakers". They do not fix multiplicative availability.

---

## SC2. A dependency was down for 90 seconds. It recovered, but your system stayed down for 25 minutes until you restarted everything. Why, and how do you prevent it?

**Testing:** metastable failures, retry amplification, queue behaviour.

**Answer (feedback loop):**

```
 dependency slow -> timeouts -> retries (3 layers) -> load x N on recovering dependency
 queues hold requests whose callers already gave up -> workers burn time on dead work
 pools exhausted, caches cold, liveness restarts remove capacity -> still overloaded
 => the load itself sustains the failure after the trigger is gone
```

**Fixes:**
1. Retry at one layer with a **budget**, jitter, and deadline awareness.
2. **Deadline propagation** and **drop expired requests on dequeue**; bounded queues, LIFO under overload.
3. **Load shedding** at saturation (fail fast, 503/429).
4. Circuit breakers (with slow-call detection) so callers stop feeding the sick service; **limited half-open probes**.
5. Slow-start or ramp traffic to restarted/cold instances.
6. Liveness must not depend on the dependency (restarts worsen it).
7. Runbook and kill switch: disable retries or shed a traffic class, drain, then refill gradually.
8. Game day: inject **slowness** (not just outage) and verify recovery after removal.

**Trap:** "add more pods". Under metastable load, scale-out cold pods can make it worse.

---

## SC3. Your Payment service calls a bank. The call times out after 2 s. Did the customer get debited?

**Testing:** unknown outcomes, idempotency with external systems, reconciliation.

**Answer:** A timeout is **neither success nor failure**; model three states: `SUCCESS`, `FAILED`, `UNKNOWN`.

```
 1. Persist intent first:  payment(id, bankRef=UNIQUE, status=INITIATED)   [DB tx]
 2. Call bank with bankRef (bank deduplicates on it)
      ok       -> SUCCESS
      declined -> FAILED (definitive)
      timeout  -> UNKNOWN (do NOT fail, do NOT blindly retry the debit)
 3. UNKNOWN resolution:
      - status-inquiry API with backoff (same bankRef)
      - fallback: end-of-day reconciliation file from the bank
      - until resolved: funds shown as pending/held, customer told "processing"
 4. Resolve to SUCCESS or FAILED -> continue saga or compensate
```

Also: alert on UNKNOWN rate and age; manual-resolution queue with SLA; breaker plus unknown count to stop sending when the bank is degraded; never auto-refund an UNKNOWN (it may have debited).

**Trap:** retrying with a new reference ID (double debit) or marking it failed (customer charged, order cancelled).

---

## SC4. A purchase saga debits the customer, then allotment fails and the refund is queued. Meanwhile the customer's loan auto-debit bounced because of the temporarily lower balance. How should the saga have been designed?

**Testing:** saga isolation, step ordering, pivot transaction.

**Answer:** The saga exposed intermediate state (a dirty read of a debit that would later be reversed). Redesign:

```
 BEFORE: debit -> allot units -> confirm      (allot fails -> refund; customer-visible damage in between)
 AFTER:  reserve units (cheap undo, can fail)  ->  validate everything else
         ->  debit (PIVOT)  ->  confirm allotment + notify (retryable until success)
```

- Put steps likely to fail and cheap to undo **first**; the customer-visible, hard-to-undo debit goes **late**, ideally right before only-retryable steps.
- If a debit must precede, represent it as a **hold/authorisation** (semantic lock), and make downstream consumers (EMI engine) aware of it (available vs ledger balance).
- Compensation must be **idempotent**, retried until success, and carry priority and SLA. Include a customer-impact policy (waive the bounce penalty automatically).
- Record saga state and expose **status** so support can see "pending refund".

**Trap:** adding a distributed lock across services (reintroduces coupling and failure modes).

---

## SC5. A Risk service consumes account events. After you added retry topics, it raised a false limit breach because a debit was processed before the credit that preceded it. Fix it.

**Testing:** ordering semantics, retry topology, state-based consumers.

**Answer:**
- Cause: **retry topics break per-key ordering**; multiple relay instances or partitions can also reorder.
- Options in increasing robustness:
  1. Key by `accountId`; single-threaded per key; use **blocking retry on the key** (park the key, continue others) with bounded attempts, then DLQ.
  2. **Per-aggregate sequence number** in each event. Consumer applies only `lastApplied + 1`; buffers or parks out-of-order events.
  3. Make the handler **state-based**: events carry the full resulting state/version; apply if `version > current`, ignore otherwise (commutative, idempotent).
- Producer side: outbox relay must preserve order per key (no concurrent relays for the same key).
- Risk breach logic should be computed from **authoritative state** (balance and limit versions), not from a sequence of deltas that can arrive in any order.

**Trap:** "use one partition" (kills throughput and still breaks under retries).

---

## SC6. Security mandates mTLS everywhere and default-deny authorisation across 80 live services in one quarter, with no outage. How do you roll it out?

**Testing:** migration planning, mesh operational pitfalls (B5).

**Answer:** Phased and reversible, as in B5:

```
 Inventory + telemetry -> PERMISSIVE + sidecar injection waves -> find plaintext callers -> fix
 -> STRICT per namespace (canary services first) -> AuthorizationPolicy in audit/dry-run
 -> enforce default-deny -> egress control
```

Specific hazards to name: non-mesh clients (Jobs, VMs, scrapers), kubelet probes, Jobs that never complete due to sidecar, sidecar-startup race, TCP/headless services, overhead and capacity, cross-cluster trust. Define **success metrics** (percent of traffic mTLS, denied-request rate) and an **instant rollback** (switch the namespace back to PERMISSIVE). Do it service-by-service with owners, not as a big bang.

**Trap:** flipping STRICT mesh-wide on a Friday.

---

## SC7. Payment trusts an `X-User-Id` header from Order. A pentest shows any pod can call Payment and impersonate a user. How do you fix it properly?

**Testing:** identity propagation, confused deputy, defence in depth.

**Answer:**
1. **Authenticate the caller:** mTLS plus `AuthorizationPolicy` so only Order's identity can call Payment's specific routes.
2. **Authenticate the user context cryptographically:** replace the header with a **signed token** (user JWT, exchanged token with `aud=payment`, or an internal passport minted at the edge). Payment verifies signature, issuer, audience, expiry.
3. **Authorise both:** "service Order may call this route" **and** "user U may act on account A" (resource-level check in Payment). Record actor in the `act` claim.
4. **Strip inbound identity headers at the edge** and never accept them from internal callers.
5. NetworkPolicy default-deny for defence in depth; audit logging with both identities.

**Trap:** "Order is trusted because it is inside the cluster". Order can be compromised or buggy, and can then act for any user (confused deputy).

---

## SC8. At 02:10 every east-west call starts failing with TLS errors. The mesh control plane had been unhealthy for a day. What happened and how do you stop it recurring?

**Testing:** mesh failure modes and operational discipline.

**Answer:**
- Workload certs (about 24 h lifetime) could not be renewed while the control plane/CA was down; they expired and the data plane lost trust at once. It looked healthy until TTL ran out, then failed everywhere simultaneously.
- **Immediate:** restore the control plane and CA; if impossible, a documented break-glass (for example temporarily relax to PERMISSIVE for critical paths, which itself needs the control plane, so have a tested static fallback or an ability to apply config out of band).
- **Prevention:**
  - Alert on **time-to-expiry** of workload certs and the root/intermediate, and on control-plane health (**not just sidecar health**).
  - HA control plane, spread across zones; capacity-plan for config pushes.
  - Set cert TTL against **MTTR**: if recovery can take 6 hours, 24 h TTL leaves little buffer.
  - **Root CA rotation** with overlapping trust bundles, rehearsed.
  - Game day: stop the control plane and watch what fails and when.

**Trap:** treating the mesh as stateless infrastructure with no time-based failure.

---

## SC9. After traffic growth, services show random 5-second latency spikes and some calls hit dead pod IPs after deployments. Diagnose.

**Testing:** DNS and caching internals.

**Answer (two separate problems):**
1. **5 s spikes:** classic UDP **conntrack race** on parallel A/AAAA lookups (resolver retries after 5 s) and/or `ndots:5` multiplying lookups for external names, and CoreDNS saturation. Check CoreDNS metrics and latency, node `conntrack` `insert_failed`, packet captures, and the resolv.conf options. Fix: **NodeLocal DNSCache**, trailing-dot FQDNs for external hosts or lower `ndots`, scale/tune CoreDNS and caching, reduce lookup volume (client DNS caching, connection reuse).
2. **Dead IPs after deploys:** the JVM (or HTTP client) **cached resolved IPs** beyond pod lifetime (`networkaddress.cache.ttl`, client-side connection pools holding stale endpoints). Fix: explicit short TTL, rely on the **ClusterIP** (stable) rather than resolving pod IPs, recycle pools, retries on connect failure to a different host.

Instrument: DNS latency histogram per service, error counts, connection-reset counts around deploys.

**Trap:** blaming the network or the app without separating the two.

---

## SC10. HPA scaled your gRPC service from 5 to 20 pods, but old pods are still at 90% CPU, new pods at 2%, and HPA keeps scaling toward max. Why?

**Testing:** connection pinning, misleading averages.

**Answer:**
- gRPC/HTTP/2 multiplexes over **long-lived connections**; kube-proxy balances **per connection**, so existing clients stay pinned to old pods. New pods receive almost nothing.
- HPA uses **average** utilisation. A few hot pods plus many idle ones averages to a value above the target, so it scales further, wasting money without helping.

**Fixes:** L7 load balancing (mesh/Envoy or client-side LB via headless service with re-resolution), **max connection age** with grace so clients periodically reconnect, per-pod hot-spot monitoring (alert on skew, not just average), and a scaling signal based on concurrency per pod with a **max** or high-percentile aggregation if hot pods matter.

**Trap:** raising `maxReplicas`.

---

## SC11. A market-open event raises traffic 15x within a minute. CPU-based HPA reacts too late and CPU stayed low while latency exploded. Design the scaling.

**Testing:** signal choice, capacity maths, cold start, admission control.

**Answer:**
- CPU stayed low because threads were **blocked on I/O**; use **in-flight concurrency** or RPS-per-pod as the signal (F2).
- **Capacity maths:** peak 6,000 rps, p95 120 ms, target 40 concurrent per pod: `6000 x 0.12 / 40 = 18` pods; add 30% headroom, about 24; to survive loss of one of 3 AZs, total about **36** (F10).
- **Pre-scale** on a schedule before the event (KEDA cron) and keep the floor through the peak; HPA handles the residual.
- **Cold start:** warm-up before readiness, slow-start in LB, overprovisioning pods, prepulled images.
- **Absorb the spike:** admission control and per-client rate limiting at the edge, queue-based load levelling for non-interactive work, degrade optional features via flags.
- **Dependencies:** scale or pool DB/cache ahead of time, verify connection budget (F6).
- Prove it with a **load test** at 1.5x projected peak, including an AZ-loss run.

**Trap:** lowering the CPU target to 30% and calling it done.

---

## SC12. HPA scaled Order from 8 to 40 pods; the system got slower and the DB started refusing connections. Explain and fix.

**Testing:** capacity coupling and backpressure.

**Answer:**

```
 8 pods x 20 conns = 160  ->  40 pods x 20 = 800   vs DB max_connections 500 (shared with 6 services)
```

- The tier you scaled is not the bottleneck; scaling multiplied connection pressure and lock contention.
- Fix: per-service **connection budget**; `maxReplicas = budget / poolSize`; reduce pool size using `concurrency x DB time fraction`; add a **pooler** (and know its caveats); **bounded pool wait** that fails fast with 503 (backpressure) instead of queueing; cache and read replicas for read-heavy paths; split write-heavy flows to async.
- Process: scale on the **true bottleneck signal** (DB saturation, pool wait time) and add automatic **protection** (concurrency limit at the service) so scale-out cannot take the DB down.

**Trap:** raising `max_connections` (memory per connection and context switching make it worse).

---

## SC13. A release adds a NOT NULL column and a code change. Delivery is Helm via Argo CD with a pre-upgrade migration hook. The new pods crash, you roll back, and the old version now fails against the new schema. Also, replicas reset to 3 during the incident. What went wrong and what is the right process?

**Testing:** expand/contract, hooks semantics, GitOps ownership.

**Answer:**
- **Schema/code coupling:** the migration ran while old pods served and the rollback restored old code but not the schema; a NOT NULL column without a default breaks old writers.
- **Process, three releases:**

```
 R1 EXPAND   : add column NULLABLE (or with default); code writes old+new; reads old
 R2 SWITCH   : backfill; read new; keep dual-write; feature flag controls the switch
 R3 CONTRACT : make NOT NULL / drop old after N-1 versions are gone and flag stable
 Each release is individually rollback-safe (N-1 compatible).
```

- **Hook mechanics:** hooks are not release-managed (cleanup via delete policy), Jobs are immutable, concurrent starts can race; under Argo CD the Helm hook maps to Argo's hook phases, so verify behaviour. Run migrations as a **single, locked job** step before rollout, with monitoring and its own timeout.
- **Replicas reset:** the template hardcoded `replicas` while the HPA also owned it, or Argo self-heal reverted the HPA's change. Omit `replicas` (or configure ignore-differences) when HPA is on.
- **Rollout safety:** canary/progressive delivery with automated abort, and **roll-forward** capability, because rollback does not cover data.

**Trap:** "just roll back" for anything with a schema change.

---

## SC14. One of three AZs has noisy-neighbour issues, and 33% of Payment calls fail. A teammate says "the circuit breaker should handle it". Does it?

**Testing:** choosing the right resilience tool for partial failure.

**Answer:** No. A service-level breaker is the wrong tool.

- With threshold 50%, it never opens, users see 33% errors. If you lower the threshold to 30%, it opens and rejects **100%** of traffic, turning a partial failure into a total outage.
- Right tools: **mesh outlier detection** (eject hosts with consecutive 5xx or latency anomalies), **retry on a different host** (retry budget applied, since retries add about 1.33x load), **locality failover** and zone-aware routing (and removing the bad AZ from rotation), health-based load balancing, and capacity that survives losing that zone (F10).
- Keep the service breaker for the whole-dependency-sick case.
- Observability to detect this: per-pod and per-AZ error and latency breakdowns, not just service averages.

**Trap:** one control for every failure shape.

---

## SC15. Your central authorisation (entitlement) service is down. What happens to the platform, and what should have been designed?

**Testing:** fail-open vs fail-closed, PDP architecture, static stability.

**Answer:** If every request makes a synchronous call to the PDP, the platform fails with it. Design so the PDP is **not a runtime hard dependency**:

```
 request -> service -> local policy engine (OPA/Cedar, in-process or sidecar)
                          ^ policy + entitlement data bundles pushed/pulled periodically
                          ^ decision cache (short TTL, stale-while-revalidate)
 PDP/control plane down -> local engine keeps deciding with last known bundle (bounded staleness)
```

- **Per operation class:** money movement and sensitive writes **fail closed** (reject or pend) once bundle staleness exceeds a limit; non-sensitive reads may **fail open** from cache with an audit log.
- Bound staleness (for example entitlements revoked can lag by up to X minutes; make X a business decision and have a fast revocation path for high-risk changes via push).
- Circuit breaker plus fallback to cached decisions; alert on bundle age.
- Test by taking the PDP down in staging and checking that critical paths behave per policy.

**Trap:** assuming "authorisation must be real-time, so call it each time" without quantifying staleness.

---

# H. Architect Checklist and Numbers

**Design review questions to ask about any new service or flow**

1. What is the sync dependency chain and its multiplied availability? What can move async?
2. Which invariants are hard, and who is the single owner of each?
3. What happens on **unknown outcome** (timeout) for every external side effect?
4. What are the timeouts, deadlines, and retry owner? Where is the retry budget?
5. Which dependencies are critical/optional, and what is the fallback and its correctness bound?
6. How is it isolated (bulkhead, cell), and what is the blast radius of a bad deploy?
7. How is the caller identified, and how is the user context carried and verified? What fails closed?
8. What is the scaling signal, per-pod capacity, cold-start time, and the downstream connection budget?
9. Is every release N-1 compatible, and what is the rollback story for data?
10. What are the SLOs, alerts, and the runbook for overload (kill switches, shedding)?

**Numbers and formulas worth memorising**

| Item | Value |
|---|---|
| Chain availability | product of each hop (0.999^6 = 99.4%) |
| Fan-out tail | 1 - 0.99^N (N=100 -> 63%) |
| Little's law | concurrency = rate x latency |
| Retry amplification | attempts^depth (3^3 = 27) |
| HPA formula | ceil(current x currentMetric / target) |
| HPA loop / tolerance / scale-down window | 15 s / 10% / 300 s (defaults) |
| Pods needed | ceil(peakRPS x p95 / concurrencyPerPod) x headroom |
| AZ-loss sizing (3 AZ) | total = required x 1.5 |
| DB connection budget | maxReplicas x poolSize <= budget |
| Eureka staleness window | up to a few minutes (30 s heartbeat, ~90 s eviction, caches) |
| Mesh cert TTL vs MTTR | TTL must comfortably exceed worst-case control-plane recovery |

**Common traps interviewers use**

- "mTLS is enough" (it authenticates; it does not authorise or carry user identity).
- "Add retries" for an availability problem (multiplies load, needs idempotency, creates metastable failure).
- "A circuit breaker fixes partial failure" (use outlier detection and locality failover).
- "HPA will handle the spike" (reaction time is minutes, and the signal may be wrong).
- "Scale out the service" when a downstream is the bottleneck.
- "Roll back" after a schema change.
- "Exactly-once" (at-least-once plus idempotent handlers; Kafka EOS stops at Kafka's boundary).
- Dependency checks in liveness or readiness probes.

---

# I. Design Principles (SOLID) and Patterns

## I1. SOLID (Robert C. Martin): the five principles with architect-level readings

| | Principle | One line |
|---|---|---|
| S | Single Responsibility | A module has one reason to change (one actor) |
| O | Open/Closed | Open for extension, closed for modification |
| L | Liskov Substitution | A subtype must be usable wherever the base type is, with no surprises |
| I | Interface Segregation | Clients should not depend on methods they do not use |
| D | Dependency Inversion | High-level policy and low-level detail both depend on abstractions |

### S: Single Responsibility

- **Misreading:** "a class does one thing." That produces hundreds of one-method classes.
- **Correct reading:** one **reason to change**, meaning one **actor** (a stakeholder or group that requests changes). Group things that change for the same reason; separate things that change for different reasons.

```java
// Violation: three actors (Finance, Compliance/Marketing, Platform) in one class
class Statement {
    BigDecimal computeFees() {...}   // Finance changes this
    String renderPdf() {...}         // Compliance/Marketing changes this
    void saveToDb() {...}            // Platform/DBA changes this
}
```

- **Architecture level:** this is the service boundary and bounded-context rule. A service that changes for two different teams' reasons violates SRP. The change-coupling test in A2 is SRP measured empirically.
- **Trap:** splitting by verbs instead of by actors and rate of change.

### O: Open/Closed

Add behaviour by adding code, not by editing tested code.

```java
// Violation: every new payment mode edits this method
BigDecimal fee(Payment p) { if (p.mode == UPI) ... else if (p.mode == NEFT) ... }

// Open/Closed: new mode = new class, existing code untouched
interface FeePolicy { boolean supports(Mode m); BigDecimal fee(Payment p); }
class UpiFee implements FeePolicy {...}
class NeftFee implements FeePolicy {...}
// Spring injects List<FeePolicy>; the caller selects the one that supports(mode)
```

- **Architecture level:** additive API and event evolution; new consumers subscribe without changing the producer; plug-in style extension points.
- **Trap:** speculative extension points. Introduce the abstraction at the second real variation, not the first.

### L: Liskov Substitution

Code written against the base type must work with any subtype **without knowing the difference**. This is about **behavioural contracts**, not just signatures.

Rules: a subtype must not strengthen preconditions, must not weaken postconditions, must preserve invariants, and must not throw unexpected exceptions.

```java
interface Wallet { void debit(BigDecimal amt); }     // contract: debits, or throws InsufficientFunds
class ReadOnlyWallet implements Wallet {
    public void debit(BigDecimal amt) { throw new UnsupportedOperationException(); }  // LSP violation
}
```

Classic example: Square extends Rectangle, where setting width also changes height and breaks callers that assumed independent setters.

- **Architecture level:** contract compatibility. A new service version, or an alternate implementation (a second payment gateway adapter), must honour the old semantics: same error behaviour, same idempotency guarantees, same ordering. Consumer-driven contract tests are LSP checks across services.
- **Probe:** "the mock gateway passes tests but production breaks." The mock violated the real contract (timeouts, partial failures, duplicates).

### I: Interface Segregation

```java
// Fat interface
interface AccountService { open(); close(); debit(); credit(); statement(); kycUpdate(); adminFreeze(); }

// Segregated by client role
interface AccountReader { Balance balance(AccountId id); }
interface AccountWriter { void debit(...); void credit(...); }
interface AccountAdmin  { void freeze(...); }
```

- **Architecture level:** consumer-specific APIs: BFF per client type, separate gRPC services or proto files per consumer group, CQRS read vs write APIs, consumer-driven contracts. A fat shared API makes every consumer a stakeholder in every change (the cause of lockstep releases).
- **Trap:** one large shared client SDK exposing every endpoint. Every service that imports it must rebuild and redeploy when any endpoint changes.

### D: Dependency Inversion

1. High-level policy must not depend on low-level detail; both depend on abstractions.
2. Abstractions must not depend on details; details depend on abstractions.

```
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

- The key point is **who owns the interface**. If it lives beside the bank client, you only added a layer. It belongs to the domain side, shaped by what the domain needs.
- **DIP is not dependency injection.** DI is a wiring mechanism; DIP is a rule about the direction of dependencies and interface ownership. You can use DI and still violate DIP.
- **Architecture level:** hexagonal (ports and adapters), clean architecture, **anti-corruption layer** (ACL) toward partners and legacy systems. Depend on contracts and events, never on another service's database or internals.

### SOLID mapped to service design

| Principle | Service-level equivalent |
|---|---|
| SRP | Service boundary = one actor / one reason to change |
| OCP | Additive API and event evolution; extend by adding consumers |
| LSP | Backward-compatible versions and alternate implementations honour the same behavioural contract |
| ISP | BFF, CQRS, consumer-driven contracts, no fat shared SDK |
| DIP | Domain owns its ports; ACL isolates partners and legacy systems |

### SOLID interview probes

1. "SRP means one method per class?" No. One reason to change (one actor).
2. "DI vs DIP?" Mechanism vs rule about dependency direction and interface ownership.
3. "An LSP violation that compiles?" A subtype throwing `UnsupportedOperationException`, or tightening a precondition.
4. "OCP vs YAGNI?" Add extension points when the second variation appears.
5. "Where does ISP appear in distributed systems?" BFFs, CQRS, per-consumer contracts.
6. "Can SOLID be overdone?" Yes: abstraction without a real axis of change adds indirection and cognitive load.

---

## I2. Adapter pattern

**Intent:** convert one interface into the one the client expects, so incompatible components can work together without changing either.

```
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
            HdfcResp resp = client.initiate(toHdfc(r));       // map domain -> partner model
            return switch (resp.code()) {                      // map partner codes -> domain outcomes
                case "00" -> PaymentResult.success(resp.ref());
                case "51" -> PaymentResult.failed(Reason.INSUFFICIENT_FUNDS);
                default   -> PaymentResult.failed(Reason.UNKNOWN_PARTNER_ERROR);
            };
        } catch (TimeoutException e) {
            return PaymentResult.unknown(r.id());               // timeout is UNKNOWN, not FAILED (SC3)
        }
    }
}
```

**Architect-level points**
- It is the implementation of **DIP** and the **anti-corruption layer**: partner models and error codes stop at the adapter, and the domain stays clean.
- The adapter is the natural place for **boundary resilience**: timeouts, retry, circuit breaker, bulkhead, idempotency reference, and mapping of failures to domain outcomes (including UNKNOWN).
- **Object adapter** (composition) is preferred over class adapter (inheritance) in Java.
- Multiple providers (HDFC, ICICI, NPCI) each get one adapter behind the same port. Selection by a factory (I4). This enables provider failover and A/B routing.
- **Service level:** a gateway/adapter service, or a sidecar, that translates a legacy protocol (SOAP/MQ/ISO 8583) to your event or REST model.

**Not the same as**

| Pattern | Difference |
|---|---|
| Facade | Simplifies a subsystem with a new, easier interface; does not need to match an existing target interface |
| Decorator | Same interface in and out; adds behaviour (logging, caching, retry) |
| Proxy | Same interface; controls access (lazy load, security, remote) |
| Adapter | **Different** interface; translates between two |

**Pitfalls:** business logic leaking into the adapter; leaky abstraction (partner concepts exposed through the port); an adapter per use case instead of per integration; no contract tests against the real partner (LSP violation, I1).

---

## I3. Singleton pattern

**Intent:** one instance per scope, with a global access point.

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
        if (instance == null) { synchronized (Cache.class) { if (instance == null) instance = new Cache(); } }
        return instance;
    }
}
```

**Architect-level points**
- **Scope is per JVM (more precisely, per classloader), not per cluster.** In Kubernetes with 10 replicas you have 10 "singletons".

```
 Pod A: [scheduler singleton]   Pod B: [scheduler singleton]   Pod C: [scheduler singleton]
   -> the "single" nightly job runs 3 times
 Fix: leader election (Kubernetes Lease), distributed lock (ShedLock, DB or Redis lock),
      or a single-replica worker, or partition ownership (Kafka consumer group)
```

- **Hidden global mutable state:** hard to test, hidden coupling, thread-safety bugs, lifecycle problems. This is why the classic static singleton is considered an anti-pattern in modern code.
- **Prefer container-managed singleton scope** (Spring beans are singleton by default): same single instance, but injected (DIP), mockable, with managed lifecycle. The beans must be **stateless or thread-safe**.
- Legitimate uses: configuration holders, connection pools, metrics registries, caches, circuit breaker registries. All are **per pod**, so each pod learns independently (D6).
- State that must be global across the cluster belongs in an external store, not in a singleton.

**Probes:** "how do you make a singleton thread-safe?"; "does Spring singleton equal the GoF singleton?" (no: one per container/context, not enforced by class); "how do you run a job once in a cluster?"; "singleton and serialization/reflection/classloaders" (enum solves the first two).

---

## I4. Factory patterns

**Intent:** encapsulate object creation so callers depend on an abstraction and not on concrete classes.

| Variant | Idea |
|---|---|
| Simple factory | One method with a `switch` that returns the right implementation (not a GoF pattern) |
| Factory Method | Subclass decides which class to instantiate |
| Abstract Factory | Creates a **family** of related objects without specifying concrete classes |

```
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

**Architect-level points**
- A `switch` factory violates **OCP** (edit on every new type); a **registry/auto-wired map** does not.
- **Abstract Factory** use: per-environment or per-region families (a bank client + auditor + notifier for India vs Singapore), per-tenant resource sets, test vs production implementations.
- Factory vs Strategy: the factory **chooses and creates**; the strategy is the **interchangeable behaviour** itself. They are commonly combined.
- In microservices: provider selection (primary/secondary bank), per-tenant client creation, feature-flagged implementation selection, and failover (the factory returns the healthy adapter, backed by a circuit breaker).
- **Pitfalls:** a god factory that knows everything; hidden dependencies created via `new` inside the factory (hard to test); creation logic mixed with business rules; factories everywhere when DI already solves it.

**Probes:** "Factory Method vs Abstract Factory?"; "Factory vs Builder?" (Builder constructs one complex object step by step; Factory selects which type); "how do you avoid `if/else` on type?"

---

## I5. Observer pattern

**Intent:** a subject notifies registered observers of state changes without knowing who they are (one-to-many, loose coupling).

```
 Subject (OrderService) --publish OrderPlaced--> [Event bus / listener list]
                                                    |-> Observer: InventoryReserver
                                                    |-> Observer: NotificationSender
                                                    |-> Observer: AuditLogger
 Subject does not know the observers; new observer = no change to the subject (OCP)
```

```java
// In-process (Spring)
applicationEventPublisher.publishEvent(new OrderPlaced(order.id()));

@Component class NotificationSender {
    @TransactionalEventListener(phase = AFTER_COMMIT)       // run only if the DB transaction committed
    void on(OrderPlaced e) { ... }
}
```

(`java.util.Observable` is deprecated since Java 9; use listeners, `PropertyChangeListener`, `Flow` / reactive streams, or framework events.)

**In-process observer vs distributed pub/sub**

| | In-process observer | Kafka / message bus |
|---|---|---|
| Coupling | Same process, compile-time types | Contract/schema only |
| Delivery | Immediate, in order, lost on crash | Durable, at-least-once, replayable |
| Failure | Observer exception can break the subject (if synchronous) | Consumer failure is isolated (retry/DLQ) |
| Transactions | Can share the DB transaction (careful) | No shared transaction: need **outbox** |
| Ordering | Call order | Per partition only |

**Architect-level points**
- Event-driven microservices are a **distributed Observer**, but you inherit new problems: at-least-once delivery (idempotent consumers), ordering (A7), the dual-write problem (A5 outbox), schema evolution, and eventual consistency.
- **Transaction timing:** if an observer sends an email or publishes to Kafka inside the transaction, a rollback leaves a phantom notification. Use `AFTER_COMMIT` or the outbox.
- **Pitfalls:** lapsed listener (an observer is never deregistered, causing a memory leak); synchronous observers adding latency or failing the subject; hidden control flow ("who reacts to this?" is hard to trace); notification cascades (observer triggers another event, creating cycles); unordered or racy updates; no backpressure with slow observers.
- Prefer async observers with bounded executors, isolated failures, and observability (trace the event through listeners).
- Related: **Pub/Sub** (adds a broker between publisher and subscriber), **Event Sourcing**, **Reactive streams** (Observer with backpressure).

**Probes:** "Observer vs Pub/Sub?"; "what if an observer throws?"; "how do you guarantee the notification only happens if the DB commit succeeded?"; "how does this pattern appear across services?" (outbox + Kafka).

---

## I6. How the principles and patterns fit together

```
 DIP  ---> Adapter (implements a domain-owned port; ACL around partners)
 OCP  ---> Factory/registry (add types without editing), Observer (add listeners without editing)
 SRP  ---> separates "create" (Factory), "translate" (Adapter), "react" (Observer), "decide" (domain)
 LSP  ---> every Adapter/implementation must honour the port's behavioural contract
 ISP  ---> small role-specific ports, so adapters stay small and mockable
```

**Worked example: payment provider integration**
1. Domain defines the `PaymentGateway` port (DIP, ISP).
2. `HdfcAdapter` and `IciciAdapter` implement it, translating models and errors, with timeouts and idempotency at the boundary (Adapter, LSP).
3. `GatewayFactory` selects the adapter by provider/region/health (Factory, OCP).
4. Payment outcome is published as `PaymentCompleted` through an outbox to Kafka, and Notification, Ledger, and Audit subscribe independently (Observer / pub-sub).
5. The scheduler for reconciliation runs once per cluster using a lease (Singleton, cluster-aware).

**Quick comparison for "which pattern?" questions**

| Need | Pattern |
|---|---|
| Make a partner or legacy API fit my interface | Adapter |
| Add behaviour around an object without changing it | Decorator |
| Control access / lazy / remote | Proxy |
| Simplify a complex subsystem | Facade |
| Choose which implementation to create | Factory |
| Swap an algorithm at runtime | Strategy |
| Notify many parties of a change | Observer / Pub-Sub |
| Exactly one instance in a process | Singleton (prefer container-managed) |
| Exactly one across the cluster | Leader election / distributed lock |


---

# PART 2: FOUNDATIONS AND QUICK-REFERENCE Q&A

The earlier guide, kept intact. Use it for definitions, diagrams, and copy-paste YAML. Item IDs are prefixed `Ref-`.

---

# P2.1 Core Concepts

> Deeper treatment in Part 1: sections A1 to A10 (availability maths, boundaries by invariants, saga isolation, outbox/CDC, idempotency depth, ordering, read-your-writes, rollout safety).

## Ref-Q1. What is a microservice architecture, and when should you NOT use it?

**Answer.** An architecture where an application is split into small, independently deployable services. Each service owns one business capability, owns its data, and communicates over the network (HTTP/gRPC/messaging).

```
 MONOLITH                              MICROSERVICES

+------------------------+            +---------+   +----------+   +---------+
| UI | Orders | Payments |            | Order   |   | Payment  |   | Wealth  |
| Users | Reports | KYC  |   ----->   | Service |   | Service  |   | Service |
|  ONE codebase          |            +----+----+   +----+-----+   +----+----+
|  ONE deployment        |                 |             |              |
|  ONE database          |             [Order DB]    [Pay DB]      [Wealth DB]
+------------------------+
```

**Benefits:** independent deploys, independent scaling, team autonomy, fault isolation, technology freedom.

**Costs (say these in the interview, it shows maturity):**
- Network is unreliable, so every call can be slow or fail.
- Distributed transactions are hard (no single ACID transaction).
- Operational overhead: CI/CD, monitoring, tracing, service discovery, security for each service.
- Testing and debugging across services is harder.

**When NOT to use:** small team (under ~8 people), unclear domain, early-stage product, no DevOps maturity. Start with a **modular monolith** and split later when boundaries are proven.

> Interview line: "Microservices trade code complexity for operational complexity. I adopt them when organisational scaling (many teams) is the real problem."

---

## Ref-Q2. How do you decide service boundaries?

**Answer.** Use **Domain-Driven Design**: one service per **bounded context**, aligned with a business capability and a team.

Example (banking/wealth platform):

```
 Bounded Contexts                  Wrong split (by technical layer)
 +-----------+ +-----------+       +-----------+ +-----------+ +-----------+
 | Customer  | | Mutual    |       | All       | | All       | | All       |
 | KYC       | | Funds     |       | Controllers| | Services  | | DAOs      |
 +-----------+ +-----------+       +-----------+ +-----------+ +-----------+
 | Payments  | | IPO       |       (every feature change touches all 3)
 +-----------+ +-----------+
```

**Signs of wrong boundaries (a "distributed monolith"):**
- Services must be deployed together (lock-step releases).
- Very chatty calls between two services (A calls B ten times per request).
- Two services share one database.
- A change in one service forces changes in several others.

**Rule of thumb:** high cohesion inside a service, loose coupling between services. If two things always change together, they belong together.

---

## Ref-Q3. Why "database per service"? How do you handle joins and reporting?

**Answer.** If services share a database, you get hidden coupling (schema change breaks others) and cannot deploy or scale independently. Each service owns its data and exposes it only via API or events.

**How to get cross-service data:**

| Need | Technique |
|---|---|
| Show order + customer on one screen | **API Composition** (gateway/BFF calls both and merges) |
| Frequent complex queries | **CQRS read model**: a denormalised view built from events |
| Analytics and reporting | **CDC (Change Data Capture)** or events into a data lake/warehouse |

```
 Order Svc --(event)--> Kafka --(consumer)--> Reporting DB (denormalised)
 Customer Svc --(event)--^
```

---

## Ref-Q4. Synchronous vs asynchronous communication. When to use which?

| | Synchronous (REST / gRPC) | Asynchronous (Kafka / RabbitMQ) |
|---|---|---|
| Coupling | Temporal coupling: both must be up | Decoupled in time |
| Latency | Immediate response | Eventual |
| Failure impact | Cascades to caller | Buffered in broker |
| Use for | Queries, "need answer now" | Commands that can wait, notifications, events, workflows |
| Needs | Timeout, retry, circuit breaker | Idempotent consumers, DLQ, ordering strategy |

```
 SYNC                         ASYNC
 A ---request---> B           A --event--> [Broker] --event--> B
 A <--response--- B           A continues immediately; B processes when ready
```

**Rule:** use sync when the user is waiting for the answer; use async for everything that can be eventually consistent (emails, ledger updates, analytics, downstream notifications).

---

## Ref-Q5. API Gateway vs BFF vs Service Mesh. What is the difference?

```
 Internet                                   Inside cluster
 Mobile --> [Mobile BFF] --+
 Web    --> [Web BFF]    --+--> [API Gateway] --> Order Svc <==mesh==> Payment Svc
                                                  (north-south)       (east-west)
```

| Component | Traffic | Responsibilities |
|---|---|---|
| **API Gateway** | North-south (client to cluster) | Routing, authN (JWT validation), rate limiting, TLS termination, request aggregation |
| **BFF** (Backend for Frontend) | Client-specific | One backend per client type (mobile/web) that shapes the payload |
| **Service Mesh** (Istio/Linkerd) | East-west (service to service) | mTLS, retries, timeouts, circuit breaking, traffic splitting, telemetry, done by sidecar proxies |

---

## Ref-Q6. Explain CAP theorem and eventual consistency in microservices.

**Answer.** In a network partition you must choose **Consistency** or **Availability** (partition tolerance is not optional in distributed systems).

- Money ledger inside one service/DB: CP, strong consistency (ACID).
- Across services: usually AP, **eventual consistency** via events and sagas.

Example: user buys mutual fund. Payment is debited immediately (strong, inside Payment DB). The "units allotted" view in the Portfolio service updates a few seconds later when the event arrives. UI should show "Order processing" instead of lying.

---

## Ref-Q7. What is the Saga pattern? Choreography vs Orchestration.

**Answer.** A saga is a sequence of **local transactions**, each publishing an event or command. If a step fails, **compensating transactions** undo previous steps (no distributed 2PC).

**Orchestration (central coordinator):**

```
                 +-------------------+
                 | Order Orchestrator|
                 +---+-----+-----+---+
          1.reserve  |     | 2.debit   | 3.allot units
                     v     v           v
              [Inventory] [Payment]  [Portfolio]

 Failure at step 3 -> orchestrator sends: refund (Payment), release (Inventory)
```

**Choreography (event-driven, no coordinator):**

```
 OrderCreated --> Payment Svc --PaymentDone--> Portfolio Svc --UnitsAllotted--> Order Svc
                      |                              |
                      +--PaymentFailed--> Order Svc  +--AllotFailed--> Payment Svc (refund)
```

| | Orchestration | Choreography |
|---|---|---|
| Visibility | Easy to see the flow | Flow scattered across services |
| Coupling | Orchestrator knows all participants | Loose |
| Risk | Orchestrator can become a god-service | Cyclic dependencies, hard to debug |
| Best for | Complex flows (more than 3 steps) | Simple flows |

**Critical points:** compensations must be **idempotent**, and some actions cannot be undone (email sent), so order steps so that irreversible ones come last.

---

## Ref-Q8. What is the dual-write problem and the Transactional Outbox pattern?

**Problem:** a service must update its DB **and** publish an event. If the DB commit succeeds but the broker publish fails (or the reverse), data is inconsistent.

```
 BAD:   BEGIN; update order; COMMIT;  --> publish to Kafka (crash here = event lost)
```

**Solution: Outbox.** Write business data and the event row in the **same local DB transaction**. A separate relay publishes the outbox rows to the broker.

```
 +-------------------- Order Service ---------------------+
 |  BEGIN TX                                              |
 |    INSERT INTO orders ...                              |
 |    INSERT INTO outbox (event_type, payload, status)    |
 |  COMMIT                                                |
 +----------------------+---------------------------------+
                        |  poller / CDC (Debezium)
                        v
                     [Kafka] ---> consumers (at-least-once)
```

Delivery is **at-least-once**, so consumers must be **idempotent**.

---

## Ref-Q9. What is idempotency and how do you implement it?

**Answer.** An operation is idempotent if doing it N times has the same effect as once. Needed because retries, timeouts, and broker redeliveries cause duplicates. "Exactly-once" end to end is a myth; the practical answer is **at-least-once + idempotent processing**.

**REST: Idempotency-Key header**

```
 POST /payments
 Idempotency-Key: 7c1f-...-a9
 {"amount": 5000, "to": "ACC123"}

 Server:
   1. SELECT from idempotency_store WHERE key = 7c1f...
   2. found  -> return stored response (do NOT debit again)
   3. absent -> INSERT key (unique constraint), process, store response
```

**Kafka consumer:** keep a `processed_event_id` table (unique constraint) or use natural idempotent updates (`UPSERT`, `SET balance = X where version = Y`).

GET, PUT, DELETE are naturally idempotent; POST is not, so it needs a key.

---

## Ref-Q10. What are CQRS and Event Sourcing?

**CQRS:** separate the write model (commands) from the read model (queries).

```
 Command --> [Write Model / DB] --events--> [Projector] --> [Read Model / DB] <-- Query
```

Use when read and write loads or shapes differ greatly (dashboards, search).

**Event Sourcing:** store the **sequence of events** as the source of truth, and rebuild state by replaying (`AccountOpened, Deposited 500, Withdrawn 200` gives balance 300). Gives a perfect audit trail, but adds complexity (event versioning, snapshots, eventual consistency). Do not use it unless audit/temporal queries justify it.

---

## Ref-Q11. How do you version APIs and deploy breaking changes safely?

- **Additive changes** (new optional field) are backward compatible. Consumers must ignore unknown fields (tolerant reader).
- **Breaking changes:** version the API (`/v2/orders`, or header/media-type), run v1 and v2 side by side, migrate consumers, then retire v1.
- **Consumer-driven contract testing (Pact):** each consumer publishes the contract it needs; the provider's CI verifies it so a breaking change fails the build.
- **DB changes: expand and contract.**

```
 1. EXPAND  : add new column (nullable), deploy code that writes both old+new
 2. MIGRATE : backfill old rows
 3. SWITCH  : read from new column
 4. CONTRACT: drop old column in a later release
```

---

## Ref-Q12. What is observability? Explain logs, metrics, traces.

```
 Request --> Gateway --> Order --> Payment --> Bank
              |  traceId=abc123 propagated in headers (W3C traceparent)
              v
 Logs   : what happened      (structured JSON, include traceId)   -> ELK/Loki
 Metrics: how much / how fast (RED: Rate, Errors, Duration)         -> Prometheus/Grafana
 Traces : where time was spent across services (spans)              -> Jaeger/Tempo/Zipkin
```

- **RED** for services: Rate, Errors, Duration.
- **USE** for resources: Utilisation, Saturation, Errors.
- Always propagate a **correlation/trace ID** across HTTP calls and Kafka headers.
- Alert on SLO burn rate, not on every CPU blip.

---

## Ref-Q13. Deployment strategies: rolling, blue-green, canary.

```
 ROLLING    : v1 v1 v1 v1  ->  v2 v1 v1 v1  ->  v2 v2 v1 v1  ->  v2 v2 v2 v2
 BLUE-GREEN : [Blue v1 live] [Green v2 idle] -> switch router -> [Green live], keep Blue for rollback
 CANARY     : 95% traffic v1, 5% v2 -> watch error rate/latency -> 25% -> 50% -> 100%
```

| | Pros | Cons |
|---|---|---|
| Rolling | No extra capacity, K8s default | Slow rollback, mixed versions run together |
| Blue-green | Instant rollback | Double infrastructure |
| Canary | Lowest blast radius, real traffic validation | Needs good metrics and traffic splitting (mesh/ingress) |

---

# P2.2 Service-to-Service Security

> Deeper treatment in Part 1: section B (B1 to B8), plus scenarios SC6 to SC8 and SC15.

## Ref-S1. Service A calls Service B inside the cluster. How do you make sure the call is secure?

**Answer. Think in layers (defence in depth, zero trust):** "never trust the network, even inside the cluster".

```
 Client --HTTPS + JWT--> [API Gateway]
                          (1) validate JWT, rate limit, WAF
                              |
                              | mTLS  (identity = spiffe://prod/ns/orders/sa/order-svc)
                              v
                     +----------------+         mTLS          +----------------+
                     | Order Service  |---------------------->| Payment Service|
                     |  [sidecar]     |                       |  [sidecar]     |
                     +----------------+                       +----------------+

 (2) NetworkPolicy        : only order-svc pods may reach payment-svc:8080
 (3) mTLS                 : both sides prove identity, traffic encrypted
 (4) AuthorizationPolicy  : order-svc may POST /payments, nothing else
 (5) JWT propagation      : the end user's identity/claims travel with the call
 (6) Secrets              : creds from Vault/External Secrets, never in the image
```

| Layer | Question it answers | Tool |
|---|---|---|
| Network | Can this pod even reach that pod? | Kubernetes NetworkPolicy (default deny) |
| Transport | Is the channel encrypted and are both ends authenticated? | mTLS (Istio/Linkerd or cert-manager) |
| Service identity | Which service is calling? | SPIFFE ID / ServiceAccount cert, or OAuth2 client credentials |
| Authorisation | Is this caller allowed this operation? | Istio AuthorizationPolicy, OPA, scopes in JWT |
| User context | On whose behalf? | JWT propagation or token exchange |

---

## Ref-S2. Explain mTLS step by step. How is it different from normal TLS?

**Normal TLS:** only the **server** proves identity (client verifies the server cert). **mTLS:** **both** present certificates.

```
 Order-svc (client)                              Payment-svc (server)
     | ---- ClientHello ----------------------------> |
     | <--- ServerHello + server cert --------------- |
     | verify server cert against trusted CA          |
     | ---- client cert ----------------------------> |
     |                       verify client cert (CA)  |
     | <=========== encrypted session ==============> |
```

**With a service mesh:** the sidecar proxies (Envoy) do the handshake, so app code speaks plain HTTP to localhost. The control plane (istiod) acts as the CA, issues **short-lived** certs (hours) per workload, and **rotates automatically**.

**Interview points:** short-lived certs reduce the blast radius of a leaked key; identity is bound to the workload (ServiceAccount), not the IP (pod IPs change constantly).

---

## Ref-S3. JWT propagation vs Client Credentials vs Token Exchange. Which one when?

| Scenario | Mechanism |
|---|---|
| Pure machine-to-machine (batch job calls Reporting svc) | **OAuth2 Client Credentials**: service gets its own token from the auth server |
| Service acts on behalf of a logged-in user | **Propagate the user's JWT** (forward the `Authorization` header) |
| Downstream needs narrower scope/audience | **Token Exchange (RFC 8693)**: swap the user's token for a new one with a limited `aud`/scope |

```
 User --JWT(aud=gateway)--> Gateway --> Order Svc
                                          |  token exchange: aud=payment, scope=pay:write
                                          v
                                       Payment Svc validates: signature, exp, aud, scope
```

**Pitfalls**
- **Confused deputy:** a service forwards a powerful user token to everything. Fix with audience-restricted tokens.
- Always validate `iss`, `aud`, `exp`, signature (via JWKS), and scopes at **each** service, not only at the gateway.
- Keep JWTs short-lived (5 to 15 minutes).

---

## Ref-S4. If the API Gateway already validates the JWT, why validate again in services?

**Answer.** Perimeter-only security means one compromised pod (or one misrouted call) has free run of the cluster. Each service should:
1. Verify the caller's **identity** (mTLS).
2. Verify the **token** (or trust a mesh-verified token, `RequestAuthentication`).
3. Enforce its **own authorisation** (business-level: "this user owns this account").

The gateway handles coarse checks; **the service enforces fine-grained, resource-level authorisation** because only it knows the data.

---

## Ref-S5. Show an Istio policy that enforces mTLS and allows only Order service to call Payment.

```yaml
# 1. Require mTLS for the whole namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: payments
spec:
  mtls:
    mode: STRICT          # plaintext rejected
---
# 2. Only order-svc's identity may call POST /payments
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

Once any ALLOW policy exists on a workload, everything not matched is **denied**.

---

## Ref-S6. How does a Kubernetes NetworkPolicy help? Show default deny.

```yaml
# Default deny all ingress in the namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: payments
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
---
# Allow only order-svc pods to reach payment-svc on 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-order
  namespace: payments
spec:
  podSelector:
    matchLabels: { app: payment-svc }
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: { name: orders }
          podSelector:
            matchLabels: { app: order-svc }
      ports:
        - port: 8080
```

NetworkPolicy works at **L3/L4 (IP/port)** and needs a CNI that enforces it (Calico, Cilium). It does **not** encrypt or authenticate, so combine it with mTLS.

---

## Ref-S7. How do you manage secrets (DB passwords, API keys)?

- Kubernetes `Secret` is only **base64**, not encryption. Enable etcd encryption at rest and restrict RBAC.
- Better: **HashiCorp Vault**, AWS Secrets Manager, or **External Secrets Operator** syncing into pods.
- **Never** bake secrets into images, Git, or Helm values files.
- Prefer **dynamic, short-lived credentials** (Vault issues a DB user valid for 1 hour).
- Rotate regularly and make rotation not require a redeploy (mount as files, reload).

```
 Pod --(ServiceAccount token)--> Vault --(verify via K8s API)--> returns short-lived DB cred
```

---

## Ref-S8. How would you secure service-to-service calls WITHOUT a service mesh?

- **OAuth2 Client Credentials** (Spring: `WebClient` with `ServerOAuth2AuthorizedClientExchangeFilterFunction`). Service A fetches a token (cached until expiry), and Service B is an OAuth2 resource server validating JWT via JWKS.
- **mTLS with cert-manager** issuing certs to each pod, and the app/ingress configured for client-cert auth.
- NetworkPolicies for network restriction.
- Trade-off: this puts security logic in every service (library upgrades, language differences). A mesh moves it to infrastructure, giving uniform enforcement.

---

# P2.3 Service Discovery

> Deeper treatment in Part 1: section C (C1 to C7), plus scenarios SC9 and SC10.

## Ref-D1. What is service discovery and why is it needed?

**Answer.** In the cloud, instances are dynamic: pods scale, crash, and move, so **IPs change constantly**. Hard-coding addresses is impossible. Service discovery maintains a live registry of "service name to healthy instance addresses".

```
 order-svc wants "payment-svc"
         |  lookup
         v
   [Registry / DNS]  --->  10.1.4.12:8080, 10.1.7.3:8080, 10.1.9.21:8080  (healthy only)
```

---

## Ref-D2. Client-side vs Server-side discovery.

```
 CLIENT-SIDE (Eureka + Spring Cloud LoadBalancer)
   Order-svc --(1) fetch list--> [Eureka Registry]
   Order-svc --(2) pick instance itself, call directly--> Payment instance #2

 SERVER-SIDE (Kubernetes Service, AWS ALB)
   Order-svc --> [Load balancer / kube-proxy] --> Payment instance (LB chooses)
```

| | Client-side | Server-side |
|---|---|---|
| Who picks instance | Caller (library) | Infrastructure |
| Extra hop | No | Yes (usually cheap) |
| Language coupling | Needs a client library | None, works with any language |
| Examples | Netflix Eureka, Consul + client LB | Kubernetes Service, Envoy |

In Kubernetes, server-side discovery is the default and Eureka is usually unnecessary.

---

## Ref-D3. How does service discovery work in Kubernetes?

```
 order-svc pod calls:  http://payment-svc.payments.svc.cluster.local:8080
        |
        | (1) CoreDNS resolves name -> ClusterIP 10.96.34.7 (stable virtual IP)
        v
 (2) kube-proxy (iptables/IPVS rules on the node) picks one backend
        |
        v
 (3) Pod IPs come from EndpointSlices -> ONLY pods that are READY
     10.1.4.12  10.1.7.3  10.1.9.21
```

- **Service** gives a stable name + virtual IP + load balancing.
- **Endpoints/EndpointSlice** are updated automatically as pods come and go.
- DNS format: `<service>.<namespace>.svc.cluster.local`. Same namespace: just `payment-svc`.
- A pod that fails its **readiness probe** is removed from endpoints (no traffic).

Gotcha: kube-proxy balances **per connection**, so a long-lived HTTP/2 or gRPC connection pins to a single pod and load is uneven. Fix with a mesh/L7 proxy or client-side gRPC load balancing via a headless service.

---

## Ref-D4. What is a Headless Service and when is it used?

`clusterIP: None`. DNS returns **all pod IPs** instead of one virtual IP.

```
 Normal Service : payment-svc  -> 10.96.34.7 (one VIP)
 Headless       : payment-svc  -> 10.1.4.12, 10.1.7.3, 10.1.9.21 (A records)
 StatefulSet    : kafka-0.kafka-headless, kafka-1.kafka-headless (stable per-pod DNS)
```

Use for **StatefulSets** (Kafka, databases, where each pod has an identity) and for client-side load balancing (gRPC).

---

## Ref-D5. Eureka / Consul: how do registration and health checks work? What are the risks?

```
 Payment instance --register (name, ip, port)--> [Eureka]
 Payment instance --heartbeat every 30s-------> [Eureka]   (miss 3 -> evicted ~90s)
 Order-svc --fetch registry (cached, refreshed every 30s)--> [Eureka]
```

**Risks to mention:**
- **Stale registry:** the caller still sees a dead instance for up to ~a minute, causing failed calls, so you need **client retries + circuit breaker**.
- **Self-preservation mode:** if many heartbeats are missed (network partition), Eureka stops evicting to avoid wiping the registry.
- Registry is a critical component, so run it **clustered**; clients cache the last-known list so a registry outage does not stop traffic.

---

## Ref-D6. Liveness vs Readiness vs Startup probes. How do they relate to discovery?

| Probe | Question | On failure |
|---|---|---|
| **Startup** | Has the app finished starting? | Keep waiting; disables the others until success (for slow JVM apps) |
| **Readiness** | Can it serve traffic **now**? | **Removed from Service endpoints** (no traffic), NOT restarted |
| **Liveness** | Is it stuck/deadlocked? | Container is **restarted** |

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
  periodSeconds: 5          # allows up to 150s to start
```

**Common mistake:** putting downstream dependency checks (DB, other services) in the **liveness** probe. When the DB blips, every pod restarts, which turns a small outage into a big one. Liveness checks only the process itself.

**Graceful shutdown:** on pod termination, K8s sends SIGTERM and removes the pod from endpoints **at the same time** (not in order). Add `preStop: sleep 10` and handle SIGTERM (finish in-flight requests) to avoid 502/503 during rollouts.

---

# P2.4 Resilience Patterns

> Deeper treatment in Part 1: section D (D1 to D10), plus scenarios SC1, SC2, SC3 and SC14.

## Ref-R1. Why does one slow service bring down the whole system? (Cascading failure)

**Key insight: slow is worse than down.** A dead service fails fast; a slow one holds your threads hostage.

```
 Payment-svc: Tomcat pool = 200 threads, normal Bank call = 50 ms
 Bank becomes slow (30 s per call, no timeout):

  t=0s    busy threads:   5
  t=10s   busy threads: 200  <-- all blocked waiting on Bank
  t=11s   new requests queue up; /health cannot get a thread
          -> liveness probe fails -> pod restarted
          -> traffic shifts to remaining pods -> they die too
          -> Order-svc (calling Payment) now exhausts ITS threads ...  (cascade)
```

**Defence stack:** Timeout (bound the wait), Circuit Breaker (stop calling a sick service), Bulkhead (isolate resources), Retry with backoff (for transient blips only), Fallback (degrade gracefully), Rate limit/Load shedding (protect yourself).

---

## Ref-R2. How do you choose timeouts? What types exist?

**Types:** connection timeout (establish TCP, keep small: 1 to 2 s), read/response timeout (wait for data), overall request/deadline timeout.

**How to pick:** base it on the downstream's observed **p99 latency plus margin** (for example p99 = 400 ms, so timeout ~ 1 s). Never leave defaults: many HTTP clients default to **infinite**.

**Timeout budget across a call chain, inner must be smaller than outer:**

```
 Client      timeout 5 s
  Gateway    timeout 4 s
   Order     timeout 3 s  (call to Payment)
    Payment  timeout 2 s  (call to Bank)

 If inner > outer, the caller gives up while the callee keeps working: wasted work,
 and retries then pile more load onto the callee.
```

Better: propagate a **deadline** (gRPC does this natively) so each hop knows how much time is left.

```yaml
# Resilience4j TimeLimiter + Spring RestClient style config
resilience4j.timelimiter.instances.bank:
  timeoutDuration: 2s
  cancelRunningFuture: true
```

---

## Ref-R3. When and how should you retry? What is a retry storm?

**Retry only when:**
- Error is **transient** (timeout, 503, connection reset), never for 400/401/404 or business errors.
- Operation is **idempotent** (or protected by an idempotency key).

**How:** exponential backoff **plus jitter** (randomness) so clients do not retry in sync.

```
 attempt 1 fails -> wait ~100ms*rand
 attempt 2 fails -> wait ~200ms*rand
 attempt 3 fails -> wait ~400ms*rand -> give up (max 3 attempts)

 Without jitter:  1000 clients all retry at exactly t+1s -> synchronized spike (thundering herd)
```

**Retry storm / amplification:**

```
 Gateway(3 tries) -> Order(3 tries) -> Payment(3 tries) -> Bank (struggling)
 1 user request can become 3 x 3 x 3 = 27 calls to Bank, which finishes it off.
```

**Fixes:** retry at **one layer only** (usually the closest to the failing call), use a **retry budget** (for example retries at most 10% of traffic), combine with a circuit breaker, and stop retrying when the deadline is exhausted.

```yaml
resilience4j.retry.instances.bank:
  maxAttempts: 3
  waitDuration: 200ms
  enableExponentialBackoff: true
  exponentialBackoffMultiplier: 2
  enableRandomizedWait: true
  retryExceptions: [java.io.IOException, java.util.concurrent.TimeoutException]
  ignoreExceptions: [com.bank.BusinessValidationException]
```

---

## Ref-R4. What is the Bulkhead pattern?

Named after ship compartments: isolate resources so a failure in one area cannot sink everything.

```
 WITHOUT bulkhead               WITH bulkhead
 +-------------------------+    +-------------------------+
 | one shared thread pool  |    | pool A: Bank     (20)   |
 | 200 threads             |    | pool B: Email    (10)   |
 | Email slow -> ALL starve|    | pool C: Reports  (10)   |
 +-------------------------+    | Email slow -> only B    |
                                +-------------------------+
```

- **Semaphore bulkhead:** limits concurrent calls (cheap, same thread).
- **Thread-pool bulkhead:** dedicated pool with queue (stronger isolation, more overhead).
- Also applied at infrastructure level: separate connection pools per dependency, separate K8s node pools or namespaces, CPU/memory limits per pod.

```yaml
resilience4j.bulkhead.instances.email:
  maxConcurrentCalls: 10
  maxWaitDuration: 0ms      # reject immediately when full (fail fast)
```

---

## Ref-R5. What are fallback strategies?

When the call fails or the circuit is open, return something useful:

| Strategy | Example |
|---|---|
| Cached/stale data | Show last known NAV or price with an "as of 10:05" label |
| Default value | Recommendations service down, so show generic top funds |
| Degrade a feature | Hide "similar products" section, rest of page works |
| Queue for later | Notification service down, put message on a queue |
| Fail with clear error | For payments: do NOT fake success. Return "try again" |

**Rule:** a fallback must never produce a **wrong financial result**. Reads can degrade; money movement must fail safe.

---

## Ref-R6. Rate limiting, load shedding, and backpressure. What is the difference?

- **Rate limiting:** cap requests per client/time (token bucket) to protect fairness and quota. Return `429 Too Many Requests` with `Retry-After`.
- **Load shedding:** when overloaded, deliberately drop low-priority requests to keep the system alive for high-priority ones (return 503 quickly, not slowly).
- **Backpressure:** a slow consumer tells the producer to slow down (bounded queues, reactive streams, Kafka consumer lag as a signal).

```
 Token bucket: bucket holds N tokens, refilled at R/sec; each request takes 1 token;
               empty bucket -> reject (429)
```

---

## Ref-R7. In what order should resilience decorators be applied?

Resilience4j default aspect order (outermost to innermost):

```
 Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( actual call ) ) ) ) )
```

- Retry is outermost so each attempt goes through the breaker (a retry that hits an OPEN breaker fails fast and counts).
- TimeLimiter wraps the call so a slow call is cut and **recorded as a failure** by the breaker.
- Bulkhead is innermost so it limits real concurrent calls.

---

## Ref-R8. App-level resilience (Resilience4j) vs Mesh-level (Istio). Which one?

| | App-level (Resilience4j) | Mesh-level (Istio/Envoy) |
|---|---|---|
| Fallback logic | Yes (business-aware) | No (only returns error) |
| Language support | JVM only | Any language |
| Consistency | Each team configures | Central policy |
| Change without redeploy | No | Yes (apply YAML) |

Practical combo: **mesh for timeouts, retries, outlier detection, mTLS** and **app-level for fallbacks and business-aware decisions**. Careful not to **double-retry** at both layers.

```yaml
# Istio: retries + timeout + outlier detection
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata: { name: payment }
spec:
  hosts: [payment-svc]
  http:
    - route: [{ destination: { host: payment-svc } }]
      timeout: 3s
      retries: { attempts: 2, perTryTimeout: 1s, retryOn: "5xx,connect-failure" }
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata: { name: payment }
spec:
  host: payment-svc
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

---

## Ref-R9. What is request hedging?

Send a second identical request to another replica if the first has not replied within the p95 latency, and take whichever finishes first. It reduces **tail latency**, but increases load, so use it only for idempotent reads and with a budget.

---

## Ref-R10. How do you prove resilience actually works?

- **Chaos engineering:** inject failures (kill pods, add latency, drop packets) with Chaos Mesh, Litmus, or Istio fault injection, first in staging, then carefully in prod.
- **Load/soak tests** with a degraded dependency.
- **Game days:** rehearse incidents.
- Verify that alerts fire, breakers open, and fallbacks return correct data.

```yaml
# Istio fault injection: 5s delay on 50% of calls to Bank
http:
  - fault:
      delay: { percentage: { value: 50 }, fixedDelay: 5s }
    route: [{ destination: { host: bank-adapter } }]
```

---

# P2.5 Circuit Breaker Deep Dive

> Deeper treatment in Part 1: D5 to D8 and scenario SC14.

## Ref-CB1. Explain the circuit breaker and its states.

Like an electrical fuse: after enough failures, stop sending calls so the sick service can recover and callers fail fast instead of piling up.

```
                 failure rate >= threshold (e.g. 50%)
      +--------+ ---------------------------------> +--------+
      | CLOSED |                                    |  OPEN  |
      | calls  |                                    | calls  |
      | flow   |                                    | fail   |
      +--------+ <---------------------------+      | FAST   |
          ^                                  |      +----+---+
          |                                  |           | after waitDuration (e.g. 30s)
          | probes succeed                   |           v
          |                              +---+--------------------+
          +------------------------------| HALF-OPEN              |
                                         | allow N trial calls    |
                                         +----------+-------------+
                                                    | probes fail
                                                    +--> back to OPEN
```

- **CLOSED:** normal; calls pass, results recorded in a sliding window.
- **OPEN:** calls rejected immediately (`CallNotPermittedException`); no load on the downstream.
- **HALF-OPEN:** limited trial calls decide whether to close or reopen.

---

## Ref-CB2. Count-based vs time-based sliding window. Key config parameters?

```yaml
resilience4j.circuitbreaker.instances.bank:
  slidingWindowType: COUNT_BASED          # or TIME_BASED
  slidingWindowSize: 20                   # last 20 calls (or last 20 seconds)
  minimumNumberOfCalls: 10                # don't evaluate before 10 calls
  failureRateThreshold: 50                # open if >= 50% fail
  slowCallDurationThreshold: 2s           # call slower than this counts as "slow"
  slowCallRateThreshold: 80               # open if >= 80% are slow
  waitDurationInOpenState: 30s            # time before HALF-OPEN
  permittedNumberOfCallsInHalfOpenState: 5
  automaticTransitionFromOpenToHalfOpenEnabled: true
  recordExceptions: [java.io.IOException, java.util.concurrent.TimeoutException]
  ignoreExceptions: [com.bank.BusinessValidationException]
```

- **Count-based:** last N calls (good for steady traffic).
- **Time-based:** last N seconds (better for variable traffic).
- **minimumNumberOfCalls** prevents opening on 1 failure out of 2 calls at low traffic.
- **Slow-call threshold** is critical, because a slow service is more dangerous than a dead one.

---

## Ref-CB3. What should count as a failure?

- **Count:** timeouts, connection errors, 5xx, 429 or 503 from downstream.
- **Do NOT count:** 4xx client errors (400, 404, 409), validation/business exceptions. Otherwise bad user input would "break" a healthy dependency.
- Use `recordExceptions` / `ignoreExceptions` (or a `recordFailurePredicate`) explicitly.

---

## Ref-CB4. What happens in HALF-OPEN? What is the recovery stampede risk?

If HALF-OPEN allowed unlimited calls, the full traffic would slam the recovering service and kill it again. So only **N probe calls** are permitted; the rest still fail fast. If the probes succeed (failure rate under threshold), the breaker closes; otherwise it returns to OPEN for another wait period.

Also mitigate with gradual ramp-up (load balancer slow start) and jittered wait times across instances.

---

## Ref-CB5. Where do you place the circuit breaker? Per service, per endpoint, per instance?

- **One breaker per downstream dependency** (and often per critical operation) so a failing `/reports` endpoint does not open the breaker for `/payments`.
- Too coarse: healthy features get blocked. Too fine: low volume per breaker, so it never gets enough data.
- **Each pod has its own breaker state** (in-memory), so pods open at slightly different times. That is acceptable; do not share state via a central store (adds a dependency to your resilience layer).
- Mesh-level **outlier detection** ejects individual bad **instances** (host level), while app-level breakers protect against a bad **service**. They complement each other.

---

## Ref-CB6. Circuit breaker vs Timeout vs Retry. Why do you need all three?

```
 Timeout        : "How long do I wait for ONE call?"          (limits damage of a single call)
 Retry          : "Should I try ONE more time?"               (helps transient blips)
 Circuit breaker: "Should I even try, given the recent past?" (protects from sustained failure)
```

- Without timeouts, the breaker never sees failures (calls just hang).
- Retry without a breaker amplifies load on a dying service.
- Breaker without retry means transient errors hurt more than necessary.

**Order:** Retry wraps CircuitBreaker wraps TimeLimiter. When the breaker is open, the retry should **not** keep retrying (`ignoreExceptions: CallNotPermittedException`, or at least back off).

---

## Ref-CB7. What should the application do when the circuit is open?

Return a **fallback** quickly (cached data, default, degraded response, or clear 503 with `Retry-After`). Log the state transition, emit a metric, and alert. For money-moving flows, fail safe, never fake success.

```java
@CircuitBreaker(name = "bank", fallbackMethod = "bankFallback")
@Retry(name = "bank")
public PaymentResult pay(PaymentRequest r) { return bankClient.pay(r); }

PaymentResult bankFallback(PaymentRequest r, Throwable t) {
    return PaymentResult.pending(r.id());   // accept & process later via queue
}
```

---

## Ref-CB8. The circuit breaker is not opening during an outage (or opens too early). How to troubleshoot?

**Not opening:**
- No timeouts, so calls hang and are never recorded as failures.
- Failures are exceptions that are in `ignoreExceptions`, or returned as HTTP 500 **responses** (not exceptions) that the client does not convert to exceptions.
- `minimumNumberOfCalls` is too high for the traffic.
- Wrong breaker name (annotation not applied: self-invocation inside the same class bypasses the Spring proxy).

**Opens too early / flaps:**
- Window too small, threshold too low, `minimumNumberOfCalls` too small.
- 4xx counted as failures.
- Wait duration too short, so it flips OPEN, HALF-OPEN, OPEN repeatedly.

**Use metrics:** `resilience4j_circuitbreaker_state`, `..._calls_total{kind}`, failure rate, and slow-call rate; alert on state transitions.

---

## Ref-CB9. How do circuit breakers behave with multiple replicas and autoscaling?

- Each replica has its own breaker, and new pods start CLOSED (they re-learn). During HPA scale-out, new pods may send traffic to a still-sick dependency briefly until their window fills.
- Mitigate with mesh outlier detection (shared at the proxy per client pod, but evaluated per source), sensible `minimumNumberOfCalls`, and not scaling the **caller** aggressively when the **dependency** is the bottleneck (scaling out callers only adds more pressure).

---

# P2.6 Helm Deployment

> Deeper treatment in Part 1: section E (E1 to E8) and scenario SC13.

## Ref-H1. What is Helm and what problem does it solve?

Helm is the **package manager for Kubernetes**. Instead of maintaining 10+ raw YAML files per service per environment, you ship a **chart** (templated manifests + default values) and install it as a versioned **release**.

```
 order-chart/
 |-- Chart.yaml          # name, version, appVersion, dependencies
 |-- values.yaml         # default config
 |-- values-prod.yaml    # prod overrides (often kept in a separate config repo)
 |-- templates/
 |   |-- deployment.yaml
 |   |-- service.yaml
 |   |-- ingress.yaml
 |   |-- hpa.yaml
 |   |-- configmap.yaml
 |   |-- _helpers.tpl    # reusable named templates
 |   `-- NOTES.txt
 `-- charts/             # packaged subchart dependencies

 helm install order ./order-chart -f values-prod.yaml -n orders
        |
        v   renders templates + values  ->  K8s manifests  ->  applied to cluster
        v   release "order" revision 1 recorded (in a Secret in the namespace)
```

Benefits: templating, per-env config, versioning, one-command **upgrade/rollback**, reusable across 80 services.

---

## Ref-H2. How do values, templates, and environment overrides work? What is the precedence?

```yaml
# values.yaml
replicaCount: 2
image: { repository: reg.io/order-svc, tag: "1.4.0" }
resources:
  requests: { cpu: 500m, memory: 512Mi }
autoscaling: { enabled: false, minReplicas: 2, maxReplicas: 10, targetCPU: 60 }
```

```yaml
# templates/deployment.yaml (snippet)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-order
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}      # omit when HPA owns replicas
  {{- end }}
  template:
    spec:
      containers:
        - name: order
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          resources: {{- toYaml .Values.resources | nindent 12 }}
```

**Precedence (lowest to highest):** chart `values.yaml`, then parent chart values, then `-f file1 -f file2` (later files win), then `--set key=val`. So `--set` beats everything.

```
 helm upgrade --install order ./order-chart -n orders \
      -f values.yaml -f values-prod.yaml --set image.tag=1.4.1
```

---

## Ref-H3. Essential Helm commands and flags to know.

| Command | Purpose |
|---|---|
| `helm lint` | Static check of chart |
| `helm template` | Render locally, no cluster (CI validation) |
| `helm install / upgrade --install` | Idempotent deploy |
| `helm diff upgrade` (plugin) | Preview changes before applying |
| `helm history <rel>` | List revisions |
| `helm rollback <rel> <rev>` | Roll back to a revision |
| `helm uninstall` | Remove release |
| `helm get values / manifest` | Inspect what was deployed |

**Critical flags:** `--atomic` (auto-rollback if upgrade fails), `--wait` (wait until pods are Ready), `--timeout`, `--create-namespace`, `--history-max 10`.

```
 helm upgrade --install order ./order-chart -n orders --atomic --wait --timeout 5m
```

---

## Ref-H4. How does Helm track releases and decide what to change?

- Each release revision is stored as a **Secret** (type `helm.sh/release.v1`) in the release namespace, containing chart, values, and rendered manifest.
- On `upgrade`, Helm 3 does a **three-way strategic merge** between: the old manifest, the new manifest, and the **live cluster state**. So manual `kubectl edit` changes can be preserved or reverted depending on the diff, which is a reason to avoid manual edits (use GitOps).
- Rollback creates a **new revision** that re-applies an old one (history only grows).

---

## Ref-H5. What are Helm hooks? Give a use case.

Hooks run Jobs/Pods at lifecycle points: `pre-install`, `pre-upgrade`, `post-upgrade`, `pre-delete`, `test`.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migrate
  annotations:
    "helm.sh/hook": pre-upgrade,pre-install
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: reg.io/order-svc:{{ .Values.image.tag }}
          command: ["java", "-jar", "app.jar", "--migrate-only"]
```

Use case: run DB migration (Flyway/Liquibase) **before** new pods start. Caveat: migrations must be **backward compatible** (expand/contract) because old pods still run during a rolling update and rollback will not undo the migration.

---

## Ref-H6. How do you manage 80 microservices with Helm? (Umbrella chart, library chart, dependencies)

- **One common library chart** (templates for Deployment/Service/HPA/probes) reused by every service chart, so a standard is enforced once and each service only has a small `values.yaml`.
- **Umbrella chart:** a parent chart listing services as `dependencies` for deploying a whole platform together. Downside: couples release cadence. Many teams prefer **independent charts per service**, deployed by CI/CD or GitOps.
- **GitOps (ArgoCD/Flux):** Git is the source of truth; the controller syncs Helm charts, giving drift detection, audit trail, and rollback by `git revert`.

```
 Git (charts + env values) --> ArgoCD --> renders Helm --> cluster
                                 ^ continuously compares desired vs live (drift = auto-heal)
```

---

## Ref-H7. How do you handle secrets with Helm?

- Never commit plain secrets in `values.yaml` (and note `helm get values` can expose them).
- Options: **External Secrets Operator** / **Vault Agent** (chart only references a secret name), **sops + helm-secrets** (encrypted values in Git), **Sealed Secrets**.
- Chart should accept `existingSecret: name` rather than embedding values.

---

## Ref-H8. A `helm upgrade` failed halfway. What happens? How do you roll back? What does rollback NOT undo?

- Without `--atomic`, the release is marked `failed` and partial resources may exist. With `--atomic`, Helm auto-rolls back to the previous good revision.
- Manual: `helm history order` then `helm rollback order <good-revision> --wait`.
- **Rollback does NOT undo:** database migrations (hence expand/contract), data in PVCs, CRDs (Helm does not manage CRD upgrades from `crds/`), and external side-effects, messages already published, etc.

```
 rev1 OK -> rev2 (upgrade fails) -> rollback -> rev3 (= content of rev1)
```

---

## Ref-H9. What does a production-ready Deployment template include?

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 25%, maxUnavailable: 0 }   # zero downtime
  template:
    spec:
      terminationGracePeriodSeconds: 45
      topologySpreadConstraints:                        # spread across zones/nodes
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector: { matchLabels: { app: order } }
      containers:
        - name: order
          resources:
            requests: { cpu: 500m, memory: 512Mi }      # required for HPA % and scheduling
            limits:   { memory: 768Mi }                 # CPU limit often omitted to avoid throttling
          readinessProbe: {...}
          livenessProbe:  {...}
          startupProbe:   {...}
          lifecycle:
            preStop: { exec: { command: ["sleep", "10"] } }
---
apiVersion: policy/v1
kind: PodDisruptionBudget          # keep capacity during node drains
spec:
  minAvailable: 70%
  selector: { matchLabels: { app: order } }
```

---

# P2.7 Horizontal Scaling and HPA

> Deeper treatment in Part 1: section F (F1 to F10) and scenarios SC10 to SC12.

## Ref-K1. How does the Horizontal Pod Autoscaler work?

```
  +--------------------+  scrape ~15s  +-----------------------------+
  | metrics-server     |<--------------| kubelet / cAdvisor (pods)   |
  | (or Prometheus     |               +-----------------------------+
  |  adapter / KEDA)   |
  +---------+----------+
            | metrics
            v
  +--------------------+   desired = ceil( current * currentMetric / targetMetric )
  |  HPA controller    |
  |  (loop every 15s)  |   Example: 4 pods, CPU 90%, target 60%
  +---------+----------+            desired = ceil(4 * 90 / 60) = 6
            | updates scale subresource
            v
  Deployment replicas: 4 --> 6   (new pods scheduled; if no node capacity -> Pending
                                  -> Cluster Autoscaler adds a node)
```

HPA scales the **number of pods**; it does not make a single pod bigger (that is VPA).

---

## Ref-K2. Show an HPA manifest (autoscaling/v2) with scale-up/scale-down behaviour.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: order-hpa }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: order }
  minReplicas: 3
  maxReplicas: 30
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 60 }   # % of REQUESTS
    - type: Pods
      pods:
        metric: { name: http_requests_per_second }
        target: { type: AverageValue, averageValue: "100" }
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - { type: Percent, value: 100, periodSeconds: 30 }   # can double every 30s
    scaleDown:
      stabilizationWindowSeconds: 300                        # wait 5 min of low load
      policies:
        - { type: Pods, value: 2, periodSeconds: 60 }        # remove max 2 pods/min
```

With multiple metrics, HPA computes a desired count for each and takes the **highest**.

---

## Ref-K3. Why must you set resource requests for HPA? What are tolerance and stabilization?

- `averageUtilization: 60` means 60% **of the container's CPU request**. No request means HPA cannot compute utilisation (shows `<unknown>`).
- **Tolerance:** HPA ignores changes within about **10%** of target to avoid jitter.
- **Stabilization window:** default **300 s for scale-down**, 0 for scale-up. This prevents flapping (scale in/out/in).
- Scale up fast, scale down slow: protects against traffic that returns right after a dip.

---

## Ref-K4. Scaling on custom or external metrics (queue lag, RPS). What is KEDA?

CPU is a poor signal for I/O-bound or consumer services. Better signals: **requests per second per pod**, **latency**, **Kafka consumer lag**, queue depth.

- **Prometheus Adapter** exposes Prometheus metrics to HPA (custom/external metrics API).
- **KEDA** (event-driven autoscaling) wraps HPA with 60+ scalers (Kafka, SQS, cron) and can **scale to zero**.

```yaml
# KEDA: scale consumers by Kafka lag
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
spec:
  scaleTargetRef: { name: settlement-consumer }
  minReplicaCount: 2
  maxReplicaCount: 20          # never exceed the partition count!
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: kafka:9092
        consumerGroup: settlement
        topic: trades
        lagThreshold: "1000"
```

**Kafka rule:** consumers beyond the number of **partitions** sit idle, so max replicas should not exceed partitions.

---

## Ref-K5. HPA vs VPA vs Cluster Autoscaler vs KEDA.

| Component | Scales | Trigger |
|---|---|---|
| **HPA** | Number of pods | CPU/memory/custom metrics |
| **VPA** | Size (requests/limits) of pods | Historical usage (restarts pods to apply) |
| **Cluster Autoscaler / Karpenter** | Number of **nodes** | Pending pods that do not fit |
| **KEDA** | Pods, event-driven (incl. 0) | External event sources |

```
 Traffic up -> HPA adds pods -> pods Pending (no room) -> Cluster Autoscaler adds node
                                                          -> pods scheduled (1-3 min delay!)
```

Do not use HPA and VPA on the **same metric** (CPU/memory); they fight.

---

## Ref-K6. HPA is not scaling. How do you troubleshoot?

Checklist (`kubectl describe hpa order-hpa` and `kubectl top pods`):

1. **TARGETS shows `<unknown>`:** metrics-server not installed/unhealthy, or no resource **requests** set.
2. **Already at maxReplicas.**
3. **Pods Pending:** no node capacity (cluster autoscaler lag/limits, quota).
4. **Bottleneck is not CPU:** app is waiting on DB/IO, CPU stays low even under heavy load. Use RPS/latency/lag metrics.
5. **CPU limits cause throttling:** pods slow without showing high utilisation vs request. Check `container_cpu_cfs_throttled_periods_total`.
6. **Helm/GitOps fighting HPA:** `replicas:` is hard-coded in the Deployment, so every sync resets the replica count. Remove `replicas` when HPA is enabled.
7. **Recently scaled / stabilization window** still active.
8. **Pods not Ready:** HPA ignores not-yet-ready pods and skews calculations.

---

## Ref-K7. Scale-up is too slow for a traffic spike. How do you improve it?

Timeline of a cold scale-up:

```
 metric spike -> scrape lag (~15-60s) -> HPA decision (15s) -> schedule pod -> (new node? 1-3 min)
   -> pull image -> JVM start + warm-up (30-90s) -> readiness passes -> traffic
```

Fixes:
- **Higher `minReplicas`** or **scheduled scaling** (KEDA cron) before known peaks (IPO opening, market open, salary day).
- Lower the target utilisation (for example 50%) to keep headroom.
- Faster startup: smaller images, pre-pulled images, CDS/AppCDS or GraalVM native image, lazy initialisation, `startupProbe` tuned.
- **Overprovisioning with low-priority "pause" pods** so nodes are already warm; they are evicted when real pods need room.
- Scale on a **leading** metric (RPS, queue depth) rather than lagging CPU.
- Add **rate limiting / queue-based load levelling** to absorb the spike while scaling.

---

## Ref-K8. Scaling pods made things worse: DB connections exhausted. Why?

```
 Before: 5 pods x pool 20 = 100 connections    (DB max_connections = 200)  OK
 After HPA: 30 pods x pool 20 = 600 connections  -> DB rejects, latency explodes
```

- **Scaling the stateless tier just moves the bottleneck to the stateful tier.**
- Size pools as: `replicas_max x pool_size <= DB max_connections` (with headroom).
- Use a connection pooler (**PgBouncer / RDS Proxy**), read replicas, caching, and cap `maxReplicas` based on downstream capacity.
- Scale based on whole-system capacity, not only the service in front.

---

## Ref-K9. How do you keep availability during scale-down, node drains, and rollouts?

- **PodDisruptionBudget:** limits voluntary disruptions (drain) to keep `minAvailable`.
- **Graceful shutdown:** handle SIGTERM, stop accepting new work, finish in-flight, `terminationGracePeriodSeconds` greater than max request time, `preStop` sleep so endpoints update first.
- **topologySpreadConstraints / anti-affinity:** do not put all replicas on one node/zone.
- `maxUnavailable: 0` and `maxSurge: 25%` for rolling updates.
- Slow scale-down policy (do not drop 50% of pods at once).

---

## Ref-K10. Stateless vs stateful: what must be true for horizontal scaling to work?

- Service must be **stateless**: no in-memory sessions or local files. Use external stores (Redis for session/cache, S3 for files, DB for state).
- **Sticky sessions** defeat even load distribution. Prefer token-based auth.
- Background jobs/schedulers need a **leader election or distributed lock** (ShedLock) or each replica runs the same job (duplicates).
- Caches: local caches diverge across pods; use a distributed cache or accept short TTL staleness.

---

# P2.8 15 Scenario-Based Questions

> This is the classic scenario set. The harder architect-level set is Part 1 section G (SC1 to SC15). Scenario IDs here are prefixed Ref- to avoid clashing with those.

## Ref-SC1. The downstream bank gateway suddenly takes 30 seconds per call. What happens to your Payment service, and how do you design against it?

**What happens:** threads block, pool exhausts within seconds, health endpoints starve, pods restart, and the failure cascades to Order and Gateway (see Ref-R1).

**Design:**

```
 Order -> Payment-svc [ TimeLimiter 2s -> CircuitBreaker -> Bulkhead(20) ] -> Bank
                                  |
                                  +-- OPEN: fallback -> mark txn PENDING, queue for async retry
```

1. **Timeout** (about 2 s) so threads are freed.
2. **Circuit breaker** with slow-call threshold so it opens when most calls exceed 2 s.
3. **Bulkhead** so the bank adapter cannot consume all threads.
4. **Fallback:** do not fake success. Return `PENDING`, publish to a queue, reconcile later.
5. Liveness probe independent from the bank dependency.
6. Alert on breaker state change and p99.

---

## Ref-SC2. After a 2-minute outage of Payment service, it keeps crashing every time it comes back. Why, and what do you do?

**Cause: retry storm / thundering herd.** All callers retried (3 layers x 3 attempts), and queued traffic hits the freshly restarted pod, so it is overloaded before it warms up.

**Fix:**
- Retry in **one layer** with **exponential backoff + jitter** and a retry budget.
- **Circuit breaker** half-open with limited probes.
- **Readiness probe** that only passes after warm-up; load balancer **slow-start**.
- **Rate limit / load shedding** on Payment to protect itself (return 503 fast).
- Scale out before reopening traffic; ramp traffic gradually (canary weight).

---

## Ref-SC3. A user taps "Pay" twice (or the client retries on timeout) and money is debited twice. How do you prevent it?

**Answer: idempotency.**

```
 Client generates Idempotency-Key (UUID) per payment intent, resends SAME key on retry
 Server:
   INSERT INTO idem(key, status) VALUES (:k,'IN_PROGRESS')    -- UNIQUE(key)
     duplicate -> return stored result (or 409 if still in progress)
     new       -> process payment -> store response -> status DONE
```

Also: database unique constraint on business key (for example `client_order_ref`), disable the button in UI after click (UX only, not a guarantee), and make downstream calls to the bank carry the same key (bank-side idempotency/reference). TTL the keys (24 to 48 h).

---

## Ref-SC4. A mutual fund purchase: money was debited, but unit allotment failed. How do you keep the system consistent?

Use an **orchestrated saga** with compensation:

```
 1. Order Svc     : create order (PENDING)
 2. Payment Svc   : debit customer                 compensation: refund
 3. Portfolio Svc : allot units                    compensation: reverse allotment
 4. Order Svc     : mark COMPLETED

 Step 3 fails ->  Orchestrator: refund (step 2 compensation) -> order = FAILED_REFUNDED
```

Details that interviewers like:
- Each step is a local transaction + **outbox event**; consumers idempotent.
- Compensation is **retried until success** (it must not fail permanently). If it cannot, route to manual reconciliation queue.
- Persist **saga state** (state machine) so it survives crashes.
- Add a **timeout** on each step (stuck order auto-escalates).
- Daily **reconciliation job** compares ledger vs allotments and flags mismatches.

---

## Ref-SC5. The order was saved to the DB, but the "OrderCreated" event never reached Kafka. How do you guarantee both?

**Transactional Outbox + CDC (Ref-Q8).** Write order row and outbox row in one DB transaction; Debezium (or a poller) publishes outbox rows to Kafka; consumers deduplicate by event ID.

```
 TX { orders, outbox }  --commit-->  Debezium reads WAL  -->  Kafka  -->  consumers (idempotent)
```

Alternative if you cannot: publish first, then DB inside a transactional listener, but that still has windows. Outbox is the standard answer.

---

## Ref-SC6. A pod in the cluster is compromised. How do you limit what the attacker can reach?

Zero-trust layers:

```
 compromised pod (notification-svc)
    X  NetworkPolicy: default deny; only listed paths open     -> cannot even connect to DB/payment
    X  mTLS STRICT: attacker has no valid cert for other IDs    -> cannot impersonate order-svc
    X  AuthorizationPolicy: notification-svc not allowed on /payments
    X  RBAC: ServiceAccount token has minimal K8s API permissions
    X  Short-lived secrets: stolen DB creds expire in 1h
    X  Pod Security: non-root, read-only FS, no privileged
```

Plus runtime detection (Falco), audit logs, image scanning, egress restrictions (so it cannot exfiltrate), and rotating credentials after an incident.

---

## Ref-SC7. IPO opens at 10:00 and traffic jumps 20x within 60 seconds. HPA is too slow. What do you do?

```
 10:00 spike ---> HPA reacts (scrape+decision+node+JVM warm-up = 3-5 min) -> too late
```

1. **Pre-scale:** schedule higher `minReplicas` (KEDA cron) 15 minutes before; pre-warm caches and connection pools.
2. **Load test** the IPO flow in advance to know per-pod capacity.
3. **Queue-based load levelling:** accept the bid into Kafka quickly (return "received"), process asynchronously at a controlled rate.
4. **Rate limiting & load shedding** at the gateway (protect core), with fair per-user limits.
5. **Cache** read-heavy data (IPO details), CDN for static.
6. **Scale dependencies** (DB read replicas, connection pooler) and cap `maxReplicas` using DB limits.
7. Degrade non-essential features (recommendations, analytics) via feature flags.
8. Use RPS/latency-based HPA metrics (leading indicators).

---

## Ref-SC8. HPA scaled Order service from 5 to 40 pods and the whole system slowed down. Why?

The bottleneck was downstream (DB connections, a rate-limited third-party API, or a Kafka partition limit). More callers just increased pressure (see Ref-K8).

**Approach:** find the actual constraint with traces and metrics (DB active connections, pool wait time, downstream latency). Fix: connection pooler, caps in `maxReplicas`, caching, bulkheads and rate limits toward the dependency, scale the dependency or make the work asynchronous. Scale on **saturation of the real bottleneck**, not blindly on CPU.

---

## Ref-SC9. How do you roll out a breaking API change across 80 services with zero downtime?

```
 Phase 1 EXPAND   : Provider supports old + new (v1 and v2, or new optional fields)
 Phase 2 MIGRATE  : Consumers move to v2 one team at a time (contract tests in CI)
 Phase 3 OBSERVE  : Metrics show v1 traffic = 0 for N days
 Phase 4 CONTRACT : Remove v1, drop old DB column
```

- **Consumer-driven contracts (Pact)** so the provider CI fails if it breaks a consumer.
- Tolerant reader (ignore unknown fields), never reuse or repurpose a field.
- **Canary** deploy the provider change; feature flags to switch behaviour.
- Events: add a **schema registry** with compatibility rules (BACKWARD/FULL) for Avro/Protobuf.
- Never "big bang" release 80 services together; that is a distributed monolith smell.

---

## Ref-SC10. `helm upgrade` applied a DB migration, then the new pods crash. You roll back. What breaks?

Rollback restores the old image/config, but the **migration stays applied**. If the old code cannot work with the new schema, you are down.

**Prevention:**
- **Expand/contract migrations:** only additive changes in the release that ships with code (add nullable column, add table); destructive changes (drop/rename) in a **later** release after the old code is gone.
- Run migration as a **pre-upgrade hook** or separate job, validated in staging with the previous app version against the new schema.
- Use `--atomic` for chart resources, but remember it does not undo the schema.
- Backups/point-in-time recovery plan; test roll-forward ("fix forward") as often as rollback.

---

## Ref-SC11. The circuit breaker to a downstream service opens, then flips between OPEN and HALF-OPEN repeatedly (flapping). Why and how to fix?

**Causes:** downstream is only partially recovered (can serve a few probes but not full load), or `waitDurationInOpenState` is too short, or probe count too small so a single failure re-opens it, or low traffic makes the failure-rate window noisy.

**Fixes:**
- Increase `waitDurationInOpenState` (and use exponential growth if supported).
- Increase `permittedNumberOfCallsInHalfOpenState` (for example 10) so the decision is statistically meaningful.
- Tune `minimumNumberOfCalls`, window size, and thresholds to traffic volume.
- Fix the root cause (downstream capacity), and ramp traffic gradually (mesh traffic shifting/slow start).
- Verify only real failures count (no 4xx).

---

## Ref-SC12. Kafka consumer lag keeps growing and one partition has stopped moving. What is wrong?

Likely a **poison message**: the consumer throws on one record and retries it forever, blocking that partition (ordering means it cannot skip).

```
 partition 3: [ok][ok][POISON][ok][ok]...   <- consumer stuck on POISON, lag grows
```

**Fix:**
- **Retry topics with backoff** (`orders.retry.1m`, `.10m`) and a **Dead Letter Topic (DLT)** after N attempts; alert and replay later.
- Distinguish **non-retryable** errors (deserialisation, validation) straight to DLT vs transient errors with retry.
- Idempotent consumers (safe to replay), correct `max.poll.interval.ms` (slow processing triggers rebalances and duplicates).
- Scale consumers up to the number of partitions; lag-based autoscaling with KEDA.

---

## Ref-SC13. A non-critical Notification service became slow and it took down the Checkout flow. How could this happen and how do you prevent it?

**How:** Checkout called Notification **synchronously** with no timeout and a shared thread pool. Slow notifications consumed all threads, so checkout stalled.

```
 FIX:
 Checkout --(event)--> [Kafka] --> Notification Svc     (async, decoupled)
 If sync is required: short timeout + bulkhead + circuit breaker + fallback (skip silently)
```

Principle: **classify dependencies** into critical vs non-critical. Non-critical ones must never be able to fail the critical path: make them async, isolate with a bulkhead, and degrade gracefully.

---

## Ref-SC14. A customer says "my SIP order took 40 seconds". The call touches 12 services. How do you find the root cause?

```
 1. Get the traceId (from the user's request ID / gateway log).
 2. Open the trace in Jaeger/Tempo: waterfall of spans.

   Gateway      |==|                                            120ms
   Order        |==========|                                    900ms
   Payment         |======================================|    38s  <-- find it
     Bank call                |==============================|  35s  <-- the culprit
```

3. Drill into the slow span: attributes (DB query text, downstream host, retry count).
4. Cross-check **metrics** (p99 latency, error rate, saturation: thread pool, DB pool wait) and **logs** filtered by `traceId`.
5. Check for retries/timeouts misconfiguration (timeout too long, retried 3 x 10s?), GC pauses, noisy neighbour, CPU throttling.
6. Fix and add an alert/SLO so it is detected before the customer calls.

Requires **trace context propagation** everywhere (HTTP headers, Kafka headers, async executors) and consistent structured logging.

---

## Ref-SC15. During a rolling deployment, users see sporadic 502/503 errors for a few seconds. Why?

**Causes and fixes:**

```
 Pod termination race:
   SIGTERM sent  --------------------------->  app stops accepting immediately
   endpoint removal propagates (kube-proxy/ingress) takes 1-5 s  ...  requests still routed -> 502
```

- Add `preStop: sleep 10` so the pod keeps serving while endpoints are removed, then handle SIGTERM gracefully (finish in-flight, `server.shutdown=graceful`).
- `terminationGracePeriodSeconds` greater than preStop + max request time.
- **Readiness probe** so new pods get traffic only when truly ready (and warm).
- `maxUnavailable: 0`, `maxSurge: 25%`.
- **PDB** for node drains.
- Keep-alive mismatch: ingress/LB idle timeout vs app keep-alive timeout (app should have a longer one), otherwise connections get reset.
- Stale discovery entries (Eureka) call for client retries on idempotent requests plus a circuit breaker.

---

# P2.9 Quick Revision Cheat Sheet

> The architect-level cheat sheet, checklist and numbers are in Part 1 section H.

| Topic | One-liner to remember |
|---|---|
| Microservices | Independent deploy + own data. Cost = distributed-system complexity |
| Boundaries | Bounded context (DDD); chatty calls or shared DB means wrong split |
| Consistency | Saga + outbox + idempotency; no distributed 2PC |
| Sync vs async | Sync when user waits; async for everything else |
| S2S security | NetworkPolicy + mTLS + AuthorizationPolicy + JWT + secrets (Vault) |
| mTLS | Both sides present certs; mesh auto-rotates short-lived certs |
| Discovery (K8s) | CoreDNS to ClusterIP to kube-proxy to Ready pods (EndpointSlice) |
| Probes | Readiness removes from traffic; liveness restarts; startup protects slow boot |
| Timeout | Always set; inner less than outer; based on p99 plus margin |
| Retry | Only transient + idempotent; backoff + jitter; one layer; budget |
| Circuit breaker | CLOSED, OPEN, HALF-OPEN; count slow calls; ignore 4xx |
| Bulkhead | Isolate pools per dependency |
| Decorator order | Retry(CircuitBreaker(RateLimiter(TimeLimiter(Bulkhead(call))))) |
| Helm | Chart + values = release; `upgrade --install --atomic --wait`; rollback does not undo DB |
| HPA formula | `ceil(current x currentMetric / targetMetric)`, needs requests, takes max across metrics |
| HPA behaviour | Scale up fast, scale down slow (300 s stabilization default) |
| HPA failure checks | metrics-server, requests, maxReplicas, Pending pods, replicas hard-coded |
| Scaling limits | DB connections, Kafka partitions, downstream rate limits |
| Zero-downtime deploy | preStop sleep, graceful shutdown, maxUnavailable 0, PDB, readiness |

**Common follow-up traps interviewers use**
- "Is mTLS enough?" No: it proves identity, not permission. You still need authorisation.
- "Can retries hurt?" Yes: amplification and duplicates without idempotency.
- "Will HPA fix a slow DB?" No: it can make it worse.
- "Does rollback fix a bad migration?" No.
- "Liveness checks the database?" Wrong: it causes mass restarts.
- "Exactly-once?" Practically: at-least-once + idempotent consumers.
