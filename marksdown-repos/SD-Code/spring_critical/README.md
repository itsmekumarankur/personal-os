# Spring - the next level of critical concepts

Already covered earlier (not repeated here): dependency injection, bean scopes and lifecycle, configuration and profiles,
AOP and proxies, `@Transactional` rollback rules and self-invocation, application events.
Microservice topics (REST clients, Feign, messaging, resilience, security, config, gateway) are in the other zips.

## Runnable demos (plain Java, JDK 17+, no dependencies): `java File.java`
Each file imitates the internal mechanism of Spring in a few lines, so you can SEE what the framework does.

| # | File | Concept | The "aha" |
|---|---|---|---|
| 1 | `MvcRequestLifecycleDemo` | Filter, DispatcherServlet, HandlerMapping, Interceptor, argument resolution, message converter, exception handler | A request is a relay race; a Filter can end it before Spring MVC even starts |
| 2 | `AutoConfigurationConditionalDemo` | Boot auto-configuration, `@Conditional*` | Adding a jar flips switches; YOUR bean always wins |
| 3 | `TransactionPropagationIsolationDemo` | `REQUIRED` vs `REQUIRES_NEW`, rollback-only trap, isolation levels | Audit row must use `REQUIRES_NEW`; catching an inner exception can still roll everything back |
| 4 | `JpaNPlusOneLazyLoadingDemo` | N+1, JOIN FETCH, `@BatchSize`, `LazyInitializationException`, dirty checking | 6 queries become 1 or 2; no `save()` needed for managed entities |
| 5 | `CachingProxyDemo` | `@Cacheable`, TTL, evict, stampede, self-invocation, mutable values | `this.method()` skips the cache; `sync=true` stops 8 simultaneous loads |
| 6 | `AsyncExecutorDemo` | `@Async`, thread pools, context loss, lost exceptions, rejection policy | ThreadLocal data and transactions do not travel to the worker thread |
| 7 | `SchedulerClusterLockDemo` | `@Scheduled`, fixedRate vs fixedDelay, ShedLock idea | 3 pods = 3 runs, unless a DB lock elects one |
| 8 | `CircularDependencyDemo` | Constructor vs field cycles, early references, fixes | A cycle usually means a missing third class |

Suggested reading order: 1, 2, 3, 4, 5, 6, 7, 8. Read the top comment, run it, then read `main()`.

## `spring_snippets/` - real Spring Boot 3 code (NOT compiled or run by the author)

| File | Matches demo |
|---|---|
| `MvcSnippets.java` | 1: controller, `@RestControllerAdvice` with `ProblemDetail`, filter, interceptor |
| `AutoConfigSnippets.java` | 2: your own starter and `AutoConfiguration.imports` |
| `TransactionSnippets.java` | 3: propagation, isolation, readOnly, rollbackFor |
| `JpaSnippets.java` | 4: `@EntityGraph`, fetch join, `@BatchSize`, DTO projection, OSIV off |
| `CacheSnippets.java` | 5: Caffeine/Redis, keys, `sync=true`, evict |
| `AsyncSnippets.java` | 6: bounded executor, decorators, security context, exception handler |
| `SchedulerSnippets.java` | 7: `@Scheduled` + ShedLock |
| `CircularDependencySnippets.java` | 8: extract, events, `@Lazy`/`ObjectProvider` |
| `TestingSnippets.java` | bonus: `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest`, `@MockitoBean` |
| `pom-dependencies.xml` | dependency list |

The snippets could not be compiled because Maven Central is blocked in the authoring sandbox. If one fails for your versions, send the error and it will be fixed.

## One idea behind most of these
`@Transactional`, `@Cacheable`, `@Async`, `@Scheduled`+locks and `@Retryable` all work through **proxies**.
So they share the same traps: they only fire on calls from OTHER beans (not `this.x()`), on public methods, and the
work may run in a different thread or transaction than you expect.
