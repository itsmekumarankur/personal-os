# Spring Boot Interview Preparation: 20 Essential Questions

The goal is to understand Spring Boot logically, not memorize definitions. Think like an architect: understand how the application works, why a feature exists, where it can fail, and how you would fix it in production.

This guide covers 10 fundamental questions followed by 10 scenario-based questions. Explanations use simple language and ASCII diagrams, with interview-ready answers.

# Part 1 — 10 Core Spring Boot Interview Questions

## Q1. What is Spring Boot, and how is it different from Spring?

**Simple explanation:** Spring is the toolbox; Spring Boot gives you a ready-to-use toolbox with sensible defaults.

Without Spring Boot, you may need to configure many things manually. Spring Boot automates much of that setup so you can focus on business logic.

```text
WITHOUT SPRING BOOT              WITH SPRING BOOT
-------------------              ----------------
Configure libraries              Use starter dependencies
Configure web server              Embedded Tomcat available
Wire components manually          Auto-configuration
Package and deploy                Run using java -jar
          |                                |
          v                                v
More setup work                   Faster application setup
```

**Important concepts**

- **Auto-configuration:** Sets up common components based on dependencies and configuration.
- **Starters:** Groups of related dependencies, such as `spring-boot-starter-web`.
- **Embedded server:** The application can run with an embedded Tomcat server.
- **Production support:** Spring Boot Actuator provides health and metrics endpoints.

**Interview-ready answer:** Spring Boot simplifies Spring application development through auto-configuration, starter dependencies, embedded servers, and production-ready integrations.

## Q2. How does Spring Boot auto-configuration work?

Imagine a hotel receptionist who checks what facilities you need and arranges them automatically. If you already have a facility, the receptionist doesn't arrange another one unnecessarily.

Spring Boot follows a similar approach.

```text
        Application starts
                |
                v
     Check classpath and properties
                |
                v
       Evaluate conditions
                |
       +--------+--------+
       |                 |
   Conditions pass   Conditions fail
       |                 |
       v                 v
 Create/configure    Skip configuration
 required beans
       |
       v
 Application ready
```

For example, adding JPA and a database driver may enable database-related auto-configuration, provided the required conditions are satisfied.

Key annotations and mechanisms:

- `@EnableAutoConfiguration` enables this process.
- `@ConditionalOnClass` checks whether a class is available.
- `@ConditionalOnMissingBean` allows your own bean to replace a default.
- `--debug` helps inspect the auto-configuration conditions report.

**Interview-ready answer:** Spring Boot evaluates conditional configuration based on the classpath, properties, and existing beans. It creates suitable defaults and backs off when the relevant conditions are not satisfied.

## Q3. What does `@SpringBootApplication` do? What are starters?

`@SpringBootApplication` combines three major annotations.

```text
       @SpringBootApplication
                 |
       +---------+----------+
       |         |          |
       v         v          v
@Configuration  @Enable    @Component
                Auto       Scan
                Configuration
       |         |          |
       v         v          v
 Define beans   Configure   Find Spring
                defaults    components
```

**Component scanning matters.** Spring generally scans the package containing your main application class and its subpackages.

Example:

```text
com.example.shop
├── ShopApplication.java
├── controller/
├── service/
└── repository/
```

This layout allows the main application class to discover those components.

A starter is a convenient bundle of dependencies. For example, `spring-boot-starter-web` brings in the libraries commonly needed for a web application.

**Interview trap:** A bean may not be discovered if its package lies outside the component scan, or if it is otherwise excluded from registration.

## Q4. What are IoC and Dependency Injection? Why is constructor injection preferred?

**IoC (Inversion of Control)** means Spring manages the creation and lifecycle of application objects instead of every class creating its own dependencies.

**Dependency Injection (DI)** is how Spring supplies those dependencies.

```text
Without dependency injection

OrderService
     |
     +---- creates ----> OrderRepository
                          (tightly coupled)


With dependency injection

Spring Container
     |
     +---- creates ----> OrderRepository
     |
     +---- injects ----> OrderService
                              |
                              v
                         Uses repository
```

Example:

```java
@Service
public class OrderService {
    private final OrderRepository repository;

    public OrderService(OrderRepository repository) {
        this.repository = repository;
    }
}
```

Why constructor injection?

- Makes required dependencies explicit.
- Supports `final` fields.
- Makes unit testing easier.
- Helps reveal circular dependencies early.

**Interview-ready answer:** IoC gives Spring control over object creation; DI supplies the required dependencies. Constructor injection is generally preferred because it makes dependencies explicit and supports immutable, testable classes.

## Q5. What is the Spring bean lifecycle? What are bean scopes?

A **bean** is an object managed by the Spring container.

```text
Spring container starts
          |
          v
Create bean
          |
          v
Inject dependencies
          |
          v
Initialization callbacks
(e.g. @PostConstruct)
          |
          v
Bean is ready for use
          |
          v
Container shuts down
          |
          v
Destruction callbacks
(e.g. @PreDestroy)
```

Common scopes:

| Scope | Meaning |
|---|---|
| `singleton` | One bean instance per Spring container; default scope |
| `prototype` | A new instance each time Spring requests that bean |
| `request` | One instance per HTTP request |
| `session` | One instance per HTTP session |

**Critical production issue:** Singleton beans are shared across concurrent requests. Do not store request-specific mutable data in a singleton service field.

For example, two customers calling the same service must not overwrite a shared `currentCustomerId` field.

**Interview-ready answer:** The container creates and initializes beans, manages their dependencies, and invokes applicable lifecycle callbacks. Scope determines how instances are created and shared.

## Q6. How does a REST API request flow through Spring Boot?

Suppose a customer calls `POST /orders` to place an order. How does that request reach the database?

```text
 Client
   |
   | POST /orders + JSON
   v
+---------------------+
| Embedded Tomcat     |
| Receives HTTP       |
+---------------------+
          |
          v
+---------------------+
| DispatcherServlet   |
| Finds the handler   |
+---------------------+
          |
          v
+---------------------+
| Controller          |
| Validates input     |
+---------------------+
          |
          v
+---------------------+
| Service             |
| Business rules      |
+---------------------+
          |
          v
+---------------------+
| Repository          |
| Database operations |
+---------------------+
          |
          v
       Database
          |
          v
 Java object -> JSON -> HTTP response
```

**What does each component do?**

- `@RestController`: Handles web requests and returns response data.
- `@PostMapping`: Maps a POST request to a Java method.
- `@RequestBody`: Converts incoming JSON into a Java object.
- `@PathVariable`: Reads a value from the URL path, such as `/orders/123`.
- `@RequestParam`: Reads a query parameter, such as `/orders?status=PAID`.
- `@Service`: Holds business logic.
- `@Repository`: Handles persistence operations.

**Interview-ready answer:** Spring MVC uses the `DispatcherServlet` as its front controller. It routes the request to the appropriate handler, invokes the application layers, and converts the returned object into an HTTP response.

A useful architectural rule is to keep controllers thin, business logic in services, and persistence logic in repositories.

## Q7. How does `@Transactional` work, and why does it sometimes fail?

Imagine transferring ₹1,000 from Account A to Account B.

Both operations must succeed together. If the debit succeeds but the credit fails, the debit must be rolled back.

```text
Transfer ₹1,000
      |
      v
Begin transaction
      |
      v
Debit Account A
      |
      v
Credit Account B
      |
      +------ Success ------> COMMIT
      |
      +------ Failure ------> ROLLBACK
```

Spring commonly implements declarative transactions using proxies.

```java
@Transactional
public void transfer() {
    debitAccount();
    creditAccount();
}
```

When an external caller invokes the method through the Spring proxy, the proxy coordinates the transaction.

**Three common interview traps:**

1. **Self-invocation:** A method calling another `@Transactional` method on the same object can bypass the proxy.
2. **Checked exceptions:** By default, checked exceptions do not trigger rollback; configure `rollbackFor` when required.
3. **Caught exceptions:** If your code catches an exception and returns normally, Spring may not see a failure that should trigger rollback.

```text
External caller
      |
      v
 Spring proxy
      |
      v
 methodA()
      |
      +---- this.methodB()
                   |
                   v
             Proxy bypassed
             Transaction advice
             may not execute
```

**Interview-ready answer:** `@Transactional` provides transaction management through Spring's transaction infrastructure, commonly proxy-based. I check proxy invocation, exception rollback rules, transaction boundaries, and whether the database operations participate in the same transaction.

Important: a database transaction does not automatically make a multi-service distributed workflow atomic.

## Q8. What is the N+1 query problem? Explain lazy and eager loading.

Suppose you fetch 100 customers and then access each customer's orders.

```text
Fetch 100 customers
       |
       v
1 SQL query
       |
       v
Loop through customers
       |
       +--> Customer 1 orders: query 2
       +--> Customer 2 orders: query 3
       +--> Customer 3 orders: query 4
       +--> ...
       +--> Customer 100 orders
                    |
                    v
             101 queries total
```

This is the **N+1 problem**: one query fetches the parent records, followed by N additional queries for related data.

**Lazy loading:** Fetch related data only when it is accessed.

**Eager loading:** Fetch related data immediately as part of the loading strategy.

Potential fixes:

- Use `JOIN FETCH` when fetching the required relationship.
- Use `@EntityGraph` to specify which relationships to load.
- Use DTO projections when the API needs only selected fields.
- Check SQL logs and query counts rather than assuming a fix worked.

Example:

```java
@Query("select c from Customer c join fetch c.orders")
List<Customer> findCustomersWithOrders();
```

**Important:** Fetch joins can produce duplicate parent rows and interact badly with pagination for collection relationships. For large datasets, consider batch fetching or a two-step query strategy.

**Interview-ready answer:** I identify N+1 through query metrics or SQL logs, then choose a targeted fetching strategy based on the access pattern. I avoid switching every relationship to eager loading because that can create excessive joins and memory usage.

## Q9. How do profiles and externalized configuration work?

A service should run in development, testing, and production without rebuilding the application for each environment.

```text
               Same application JAR
                       |
           +-----------+-----------+
           |           |           |
           v           v           v
         DEV          TEST        PROD
           |           |           |
       Local DB     Test DB     Real DB
       Debug logs   Test logs   Prod logs
```

Typical configuration files:

```text
application.yml
application-dev.yml
application-test.yml
application-prod.yml
```

Activate a profile with:

```bash
java -jar app.jar --spring.profiles.active=prod
```

Read configuration using:

```java
@Value("${app.timeout}")
private int timeout;
```

For a group of related properties, `@ConfigurationProperties` is generally cleaner and supports type-safe binding.

**Architect-level concerns:**

- Do not package database passwords or API secrets into source code.
- Use environment-specific configuration and a secrets manager.
- Validate required properties at startup.
- Understand property-source precedence when troubleshooting unexpected values.

**Interview-ready answer:** Profiles select environment-specific configuration, while externalized properties separate deployment settings from application code. This lets us promote the same artifact across environments with controlled configuration changes.

## Q10. How does Spring Security work with JWT?

Think of security as two separate questions:

- **Authentication:** Who are you?
- **Authorization:** What are you allowed to do?

```text
HTTP request
     |
     v
Security filter chain
     |
     v
Validate JWT
     |
     +---- Invalid/missing credentials
     |              |
     |              v
     |             401
     |
     v
Identify authenticated user
     |
     v
Check roles/permissions
     |
     +---- Insufficient permission
     |              |
     |              v
     |             403
     |
     v
Controller executes
```

A typical JWT flow:

1. The user authenticates.
2. The server issues a signed token.
3. The client sends it in `Authorization: Bearer <token>`.
4. Security filters validate the token and establish the authentication context.
5. Authorization rules determine whether the user can perform the operation.

Example:

```java
@PreAuthorize("hasRole('ADMIN')")
@GetMapping("/admin/reports")
public Report getReport() {
    // ...
}
```

**Architect-level concerns:**

- A JWT must be verified, not merely decoded.
- Check expiry, issuer, audience where applicable, and signing algorithm.
- Store passwords using a suitable password-hashing algorithm such as BCrypt.
- A signed JWT is not necessarily encrypted.
- Stateless authentication does not eliminate the need for token revocation, key rotation, or refresh-token controls.

**Interview-ready answer:** Spring Security processes requests through a filter chain, establishes the authenticated identity, and applies authorization rules before allowing protected operations.

# Part 2 — 10 Scenario-Based Spring Boot Interview Questions

These questions test whether you can diagnose problems, reason about trade-offs, and design production-ready systems rather than simply define annotations.

## Scenario 1. Your Spring Boot application starts, but a service bean is not found. How would you debug it?

**Question:** You see `NoSuchBeanDefinitionException` when the application starts. What would you investigate?

```text
Application starts
       |
       v
Spring needs OrderService
       |
       v
Is the bean registered?
       |
   +---+---+
   |       |
  No      Yes
   |       |
   v       v
Check scan  Check injection
package     type/qualifier
   |
   v
Check @Service, conditions,
profiles, exclusions
```

**Logical investigation order:**

1. Is the class annotated with `@Service`, `@Component`, or another appropriate stereotype?
2. Is it within the component-scan boundary?
3. Is a profile or conditional configuration preventing registration?
4. Are multiple beans of the same type creating an ambiguity?
5. Is the bean declared in a configuration class that is itself discovered?

**Architect's answer:** I would inspect the bean registration and application context first, rather than adding annotations randomly. I would fix the component-scan boundary or explicit bean configuration and add a context-startup test.

## Scenario 2. Two requests update the same singleton service, and customer data gets mixed up. Why?

**Question:** A service stores `currentCustomerId` in a field. Under concurrent load, one customer's request uses another customer's ID.

```text
Request A ----+
              |
              v
      Shared singleton service
      currentCustomerId = A
              |
Request B ----+--> currentCustomerId = B
              |
              v
Request A reads B's ID
       |
       v
Incorrect customer data
```

**Root cause:** Spring singleton scope means one shared instance, not one instance per request. Multiple threads can execute methods on that instance concurrently.

**Fix:**

- Keep request-specific values in method parameters and local variables.
- Avoid mutable per-request state in singleton fields.
- Use appropriate concurrency controls only when shared mutable state is genuinely required.

**Architect's answer:** I would make the service stateless. Synchronization is not the first choice for request-specific data because it can serialize traffic and reduce throughput.

## Scenario 3. Money is debited, but the credit fails. Why did `@Transactional` not roll back?

**Question:** A transfer method debits one account, calls a credit method annotated with `@Transactional`, and then encounters an exception.

```text
Transfer request
      |
      v
Debit succeeds
      |
      v
Credit fails
      |
      v
Exception caught?
      |
  +---+---+
  |       |
 Yes      No
  |       |
  v       v
May hide  Check rollback
failure   rules and proxy
      |
      v
Check actual transaction
and database boundaries
```

**What I would investigate:**

- Is the transactional method called through the Spring proxy?
- Is it a self-invocation?
- Is the exception a checked exception?
- Was the exception caught and swallowed?
- Are both account updates using the same transaction manager and transaction?
- Does the database operation actually participate in the transaction?

**Architect's answer:** I would verify the actual transaction boundary and rollback behavior with an integration test. For transfers across separate services or databases, I would design an explicit distributed workflow, such as a saga, rather than assume a local transaction can roll everything back.

## Scenario 4. An API becomes slow after the customer table grows to one million rows. How would you investigate?

**Question:** The API used to return quickly but now takes several seconds. How do you identify the bottleneck?

```text
Incoming request
       |
       v
Measure total latency
       |
       v
+---------------------+
| Where is time spent?|
+---------------------+
    |       |       |
    v       v       v
Database  Network  Application
    |
    v
Inspect SQL, query plan,
indexes, N+1, row count
    |
    v
Apply targeted fix
    |
    v
Benchmark again
```

**Investigation:**

1. Break down latency across application, database, and external dependencies.
2. Check query execution plans, indexes, connection-pool usage, and returned row counts.
3. Look for N+1 queries, full table scans, and unnecessary entity loading.
4. Check whether pagination is implemented correctly.
5. Measure again after each change.

**Architect's answer:** I would use evidence from traces, database metrics, and query plans before adding caching or increasing infrastructure. A million rows alone does not prove that the database is the bottleneck.

## Scenario 5. Your API throws `LazyInitializationException` after the service returns.

**Question:** The controller accesses `customer.getOrders()`, but the persistence session is already closed. How would you fix it?

```text
Service fetches Customer
          |
          v
Customer returned
          |
          v
Persistence context closes
          |
          v
Controller accesses orders
          |
          v
LazyInitializationException
```

**Root cause:** The association was configured for lazy loading, but the related data was accessed after the persistence context became unavailable.

**Possible fixes:**

- Fetch the required association explicitly using a fetch join or entity graph.
- Map the result to a DTO within the appropriate transaction boundary.
- Use a dedicated query for the data needed by the API.

**Architect's answer:** I would define the data required by the use case and fetch it deliberately. I would not make every association eager or expose persistence entities directly as API contracts.

## Scenario 6. Your application works locally but fails in production because the database connection is incorrect.

**Question:** The same JAR works on a developer's laptop but fails after deployment. How would you debug it?

```text
       Application JAR
              |
              v
     Load configuration
              |
              v
   Which profile is active?
              |
              v
   Which DB URL is loaded?
              |
              v
   Check credentials, DNS,
   network, TLS and permissions
              |
              v
       Database connection
```

**Logical approach:**

1. Confirm the active Spring profile.
2. Check the effective database URL and connection settings without exposing secrets.
3. Verify environment variables and secret injection.
4. Check network access, DNS, TLS certificates, and database permissions.
5. Confirm connection-pool settings and database availability.

**Architect's answer:** I would compare the effective configuration between environments, validate connectivity, and ensure secrets are injected securely. I would not fix a production configuration problem by hard-coding production credentials into the application.

## Scenario 7. Your API returns HTTP 401 for one request and HTTP 403 for another. What is the difference?

**Question:** A user can log in but cannot access an admin endpoint. How would you investigate?

```text
             Request
                |
                v
       Authentication check
                |
         +------+------+
         |             |
       Fails         Succeeds
         |             |
         v             v
        401       Authorization check
                       |
                 +-----+-----+
                 |           |
               Fails       Passes
                 |           |
                 v           v
                403       Controller
```

- **401 Unauthorized:** The request lacks valid authentication credentials.
- **403 Forbidden:** The authenticated identity does not have sufficient permission, although security configurations can also deliberately return 403 in other situations.

**What I would check:**

- Is the JWT valid, unexpired, and signed by a trusted key?
- Is the security context populated correctly?
- Does the user have the required role or authority?
- Is there a difference between `ROLE_ADMIN` and an authority such as `ADMIN`?
- Are method-level security and URL-level security consistent?

**Architect's answer:** I would trace the authentication and authorization decisions separately. I would not solve an authorization problem by weakening the security rules for everyone.

## Scenario 8. An external payment provider is slow, and your Spring Boot application starts running out of threads.

**Question:** Your payment API calls an external provider. When that provider becomes slow, your own API also becomes slow. Why?

```text
Incoming requests
        |
        v
Payment API
        |
        v
External provider
        |
        v
Slow response
        |
        v
Request threads wait
        |
        v
Thread/connection pools fill up
        |
        v
Other requests become slow
```

**What would you do?**

- Set connection and response timeouts.
- Use bounded connection and thread pools.
- Apply circuit-breaker and bulkhead patterns where appropriate.
- Use bounded retries with backoff for transient failures.
- Make payment operations idempotent so retries do not create duplicate charges.
- Monitor timeout rates, latency percentiles, and pool saturation.

**Architect's answer:** I would isolate the dependency, bound resource consumption, and define failure behavior. For payment operations, I would avoid blindly retrying a request whose outcome is unknown; I would reconcile the transaction using an idempotency key or provider status check.

## Scenario 9. Your service works, but a recent code change breaks the application during deployment. How would you test it?

**Question:** How would you design a testing strategy for a Spring Boot microservice?

```text
        Spring Boot service
                 |
       +---------+---------+
       |         |         |
       v         v         v
     Unit    Integration   API/End-to-end
     tests      tests        tests
       |         |              |
       v         v              v
 Business    DB, Spring      Complete user
 logic       context,        workflows
 isolated    messaging
       |         |              |
       +---------+--------------+
                 |
                 v
          CI/CD quality gates
```

**Testing layers:**

- **Unit tests:** Test business logic without starting the entire Spring application.
- **`@WebMvcTest`:** Test MVC controllers and web-layer behavior.
- **`@DataJpaTest`:** Test JPA-related behavior with a suitable test database.
- **`@SpringBootTest`:** Test broader application integration.
- **Integration tests:** Verify database transactions, security, messaging, and external dependency boundaries.

For a payment service, I would specifically test duplicate requests, rollback behavior, concurrent updates, authorization failures, and provider timeouts.

**Architect's answer:** I would use a testing pyramid: many fast unit tests, targeted integration tests, and a smaller number of end-to-end tests. Critical business invariants must be tested at the layer where they can actually fail.

## Scenario 10. Your Spring Boot application is running, but users report intermittent failures. How would you diagnose the issue?

**Question:** The service appears healthy, but some requests fail or take several seconds. What would you inspect?

```text
User request
     |
     v
Application
     |
     +---- Logs: What failed?
     |
     +---- Metrics: How often?
     |
     +---- Traces: Where is the delay?
     |
     v
Correlate evidence
     |
     v
Identify bottleneck
     |
     v
Fix and verify
```

**Tools and concepts:**

- **Spring Boot Actuator:** Exposes health, metrics, and application information through configured endpoints.
- **Micrometer:** Provides instrumentation and metrics integration.
- **Distributed tracing:** Follows a request across multiple services.
- **Structured logs and correlation IDs:** Connect related events across application components.

I would inspect:

1. Error rate and latency at p50, p95, and p99.
2. Database connection-pool exhaustion.
3. Thread-pool saturation and deadlocks.
4. Garbage collection and memory pressure.
5. External API failures and timeout patterns.
6. Recent deployment or configuration changes.

**Architect's answer:** I would correlate logs, metrics, and traces to locate the failing component, then validate the hypothesis with evidence. A green health check alone does not prove that every business operation is functioning correctly.

# Final Revision: Connect the Concepts

```text
1. START
   @SpringBootApplication
          |
          v
2. DISCOVER
   Component scan + auto-configuration
          |
          v
3. CREATE
   IoC + dependency injection + bean lifecycle
          |
          v
4. SERVE
   Tomcat -> DispatcherServlet -> Controller
          |
          v
5. EXECUTE
   Service -> transaction -> Repository
          |
          v
6. PERSIST
   JPA -> SQL database
          |
          v
7. PROTECT
   Spring Security -> authentication/authorization
          |
          v
8. CONFIGURE
   Profiles + externalized properties
          |
          v
9. VERIFY
   Unit tests + integration tests
          |
          v
10. OPERATE
    Actuator + metrics + logs + traces
```

## The Architect's Method for Scenario Questions

For almost any Spring Boot interview scenario, follow this sequence:

1. **Clarify the symptom:** What exactly is failing?
2. **Trace the request:** Which layer could be responsible?
3. **Gather evidence:** Logs, metrics, traces, SQL, or configuration.
4. **Explain the root cause:** Why does the failure happen?
5. **Choose the fix:** Address the cause rather than hiding the symptom.
6. **Validate the fix:** Add tests and measure the production impact.

This approach demonstrates deeper understanding than simply naming annotations.

**Recommended preparation order:** First master IoC/DI, auto-configuration, request flow, transactions, and JPA. Then practice the concurrency, security, performance, and resilience scenarios. These are especially useful for Engineering Manager, Solution Architect, and senior backend interviews.
