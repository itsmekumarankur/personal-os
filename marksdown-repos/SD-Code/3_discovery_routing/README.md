# Service discovery and routing - topics 26 to 30

## Runnable demos (plain Java, JDK 17+, no dependencies): `java File.java`

| # | File | Topic | What you see |
|---|---|---|---|
| 26 | `ApiGatewayDemo.java` | API Gateway | Real HTTP gateway + 2 services: open route, 401 at the edge, path routing, identity header, 504 on slow backend, 404 |
| 27 | `ServiceRegistryDemo.java` | Registry and discovery | Register, heartbeat, crash then TTL eviction, graceful deregistration, stale client cache, autoscaled instance |
| 28 | `LoadBalancerDemo.java` | Client-side load balancing | Round-robin (skips unhealthy), random, least-connections with a slow instance |
| 29 | `BffDemo.java` | Backend for Frontend | Same backends, mobile BFF returns 224 chars, web BFF returns 3,828 chars |
| 30 | `AggregatorDemo.java` | Aggregator | Sequential 1205 ms vs parallel 504 ms; optional part times out gracefully; critical failure fails fast |

## `spring_snippets/` (NOT compiled or run by the author)

| File | Topic |
|---|---|
| `gateway-application.yml` | #26 Spring Cloud Gateway routes, retry, circuit breaker, rate limiter, timeouts |
| `AuthGlobalFilter.java` | #26 custom global filter (edge auth + request id) |
| `EurekaSnippets.java` | #27 and #28 Eureka server/client config and `@LoadBalanced` `RestClient` |

If a snippet does not compile for your versions, send the error and it will be fixed.
