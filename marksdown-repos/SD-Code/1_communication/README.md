# Communication - topics 1 to 7

## Runnable demos (plain Java, JDK 17+, no dependencies): `java File.java`

| # | File | Topic | What you see |
|---|---|---|---|
| 1 | `RestCallDemo.java` | REST between services | Two real HTTP services; status handling, timeout, downstream failure translated to a good answer |
| 2 | `SyncVsAsyncDemo.java` | Sync vs async | Same outage: sync customer gets an error after payment; async customer gets an instant "202 Accepted" and the retries happen later |
| 3 | `MessagingDemo.java` | Kafka-style messaging | Partitions, keys keep order, consumer groups split work, offsets survive a crash |
| 4 | `DeclarativeClientDemo.java` | Feign-style clients | An annotated interface becomes a working HTTP client via a proxy |
| 5 | `BinaryVsJsonDemo.java` | gRPC idea | Contract-first binary vs JSON: 30 vs 77 bytes, varints, why a shared contract matters |
| 6 | `ApiVersioningDemo.java` | API versioning | Safe additive change vs breaking change, /v1 + /v2, Deprecation/Sunset headers |
| 7 | `DtoVsEntityDemo.java` | DTO vs entity | Entity leaks internals and breaks on refactor; DTO stays stable |

## `spring_snippets/` (library code, NOT compiled or run by the author)

| File | Topic |
|---|---|
| `RestClientSnippets.java` | #1 `RestClient`, `RestTemplate`, `WebClient` with timeouts |
| `FeignSnippet.java` | #4 `@FeignClient`, fallback |
| `MessagingSnippets.java` | #3 Kafka (`KafkaTemplate`, `@KafkaListener`, groups) and RabbitMQ |
| `price.proto` + `GrpcSnippet.java` | #5 contract + server + client |

If a snippet does not compile for your versions, send the error and it will be fixed.
