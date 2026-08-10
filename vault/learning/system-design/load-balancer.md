---
tags: [system-design, load-balancer, request-lifecycle, consistent-hashing]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/advanced-architects-lab/load-balancer-design]
---

# Load Balancer — Design & Request Lifecycle

Distributes incoming requests across a pool of backend servers. The goal: maximize throughput, minimize latency, and handle server failures transparently.

## Request Lifecycle (Full Path)

1. Client resolves DNS — gets VIP (virtual IP) of the load balancer
2. TCP connection to LB (L4) or HTTP connection (L7)
3. LB selects backend server based on algorithm
4. LB establishes connection to backend (or reuses a pooled connection)
5. Request forwarded. Response returned to client.

## Algorithms

**Round Robin**: requests distributed sequentially. Simple. Fails when servers have different capacities or request weights vary.

**Least Connections**: route to the server with fewest active connections. Better when requests have variable processing time.

**Weighted Round Robin / Weighted Least Connections**: assign weights proportional to server capacity. Good for heterogeneous fleets.

**Consistent Hashing**: hash the client/session key and map to a ring. A server handles a consistent slice of the key space. When a server is added or removed, only that server's slice is redistributed — not the entire pool. Critical for stateful systems (caches, session affinity).

## L4 vs. L7 Load Balancing

| | L4 (TCP) | L7 (HTTP) |
|---|---|---|
| Sees | IP + ports only | Full HTTP headers, URL, cookies |
| Routing | By IP/port | By path, host, cookie, content |
| SSL | Passthrough | Termination (LB decrypts) |
| Speed | Faster (less inspection) | Slower (full packet inspection) |

AWS ALB (Application Load Balancer) = L7. Used in idfc-coder to route to the ECS Fargate wrapper service.

## Health Checks

LB probes backends every N seconds. If a backend fails K consecutive checks, remove it from rotation. Bring it back after M successful checks. This is active health checking.

## Connection Draining

When removing a backend (deploy, scale-in), don't kill active connections. Mark as "draining" — no new requests routed, existing requests complete. Then remove cleanly.

## Session Affinity (Sticky Sessions)

Some applications require the same user to always hit the same server (session state stored in memory). Implemented via a cookie or IP hash. Trade-off: reduces effective load distribution when one user has heavy traffic.

## Idfc-Coder Architecture Note

The idfc-coder pipeline: ALB → ECS Fargate wrapper → SageMaker endpoint (with SQS batching). The ALB handles L7 routing; auto-scaling on the ECS layer manages capacity (4–16 instances). This is the pattern for serving self-hosted LLM inference at variable load.

## Related

- [[learning/system-design/kafka]] — Message queues as an alternative to synchronous LB for async workloads
- [[learning/system-design/distributed-tracing]] — Observability across the request path
