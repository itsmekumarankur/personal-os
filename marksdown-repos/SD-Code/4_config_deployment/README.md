# Configuration and deployment - topics 31 to 37

## Runnable demos (plain Java, JDK 17+, no dependencies): `java File.java`

| # | File | Topic | What you see |
|---|---|---|---|
| 31 | `ExternalizedConfigDemo.java` | Externalized config, profiles | Same code, 3 runs: defaults < file < profile file < env var < command line; secret masked |
| 32 | `FeatureFlagDemo.java` | Feature flags | Allow-list, sticky 10% then 50% rollout (monotonic), live kill switch |
| 33 | `TwelveFactorDemo.java` | 12-factor app | Env config, stateless vs in-memory sessions, JSON logs on stdout, graceful shutdown hook |
| 37 | `BlueGreenCanaryDemo.java` | Blue-green and canary | Instant flip and rollback; canary 5/25/50/100 with auto-rollback on a buggy v2 |

## Deployment files (NOT built or run by the author; only YAML syntax checked)

| # | File | Topic |
|---|---|---|
| 34 | `docker/Dockerfile`, `docker/.dockerignore` | Multi-stage build, non-root user, container-aware JVM, healthcheck, PID 1 signal handling |
| 35 | `docker/docker-compose.yml` | App + Postgres + Kafka locally, env config, health-gated startup |
| 36 | `kubernetes/01..05-*.yaml` | ConfigMap, Secret template, Deployment (rolling update, probes, limits), Service, HPA |
| 37 | `kubernetes/06-canary-notes.md` | How blue-green / canary map to Kubernetes |

## `spring_snippets/` (NOT compiled or run by the author)

| File | Topic |
|---|---|
| `application.yml` | #31 shared defaults + dev/prod profiles, secret from env, graceful shutdown, probes |
| `PaymentProperties.java` | #31 `@ConfigurationProperties` with validation (fail fast) |
| `ConfigServerSnippets.java` | #31 Spring Cloud Config Server, client import, `/actuator/refresh` |
| `FeatureFlagSnippet.java` | #32 property flag with `@RefreshScope` |

If something does not work for your versions, send the error and it will be fixed.
