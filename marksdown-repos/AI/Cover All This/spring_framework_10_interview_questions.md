# Spring Framework: 10 Interview Questions — Learning and Revision Guide

This guide covers ten core Spring Framework interview topics. For every question, use the same learning sequence:

1. **Why are we learning this?** Understand the real-world benefit and the problem it solves.
2. **Explanation with ASCII diagrams.** Visualize the flow and component relationships.
3. **Practical example.** Connect the concept to a Spring Boot application.
4. **Short memory map.** Revise the key ideas quickly before an interview.

## The 10-question roadmap

| # | Topic | What you will learn |
|---:|---|---|
| 1 | Inversion of Control (IoC) and Dependency Injection (DI) | How Spring creates and connects objects |
| 2 | Bean lifecycle and scopes | How Spring manages object creation and lifetime |
| 3 | Spring Boot auto-configuration | How Spring Boot reduces configuration work |
| 4 | Spring MVC and REST | How HTTP requests reach controllers and return responses |
| 5 | Aspect-Oriented Programming (AOP) | How to separate logging, security, and other cross-cutting concerns |
| 6 | Spring Data JPA and transactions | How to access databases and maintain data consistency |
| 7 | Spring Security | How to authenticate users and enforce permissions |
| 8 | Exceptions, validation, and profiles | How to handle errors and configure different environments |
| 9 | Spring Cloud and microservices | How to connect and manage distributed services |
| 10 | Testing, Actuator, and observability | How to verify and monitor applications |

---

## Question 1. What is Inversion of Control (IoC), and how does Spring manage dependencies using Dependency Injection (DI)?

### 1. Why are we learning this?

Every application contains objects that depend on other objects. For example, an `OrderService` needs a `PaymentService` to process a payment.

If every class creates its own dependencies, the code becomes tightly coupled. Changing an implementation or writing unit tests becomes harder.

**IoC solves the object-creation responsibility problem.** Spring manages the creation and wiring of objects, while Dependency Injection is the technique used to provide those dependencies.

### 2. Explanation with an ASCII diagram

**Without Spring:**

```text
OrderService
     |
     | creates using new
     v
PaymentService
```

`OrderService` decides which implementation to create.

**With Spring:**

```text
       Spring IoC Container
       /                 \\
      v                   v
OrderService         PaymentService
      ^                   |
      |___________________|
       Dependency injected
       through constructor
```

The process works like this:

1. Spring discovers bean definitions using annotations such as `@Component`, `@Service`, and `@Repository`, or Java configuration using `@Bean`.
2. Spring creates and manages the objects, called beans.
3. Spring resolves their dependencies.
4. Spring injects dependencies, preferably through constructors.
5. The application uses the resulting objects.

Example:

```java
@Service
class PaymentService {
    public void pay() {
        System.out.println("Payment processed");
    }
}

@Service
class OrderService {
    private final PaymentService paymentService;

    public OrderService(PaymentService paymentService) {
        this.paymentService = paymentService;
    }
}
```

Spring provides `PaymentService` when constructing `OrderService`.

**Benefits:** loose coupling, easier unit testing, simpler replacement of implementations, and better maintainability.

### 3. Short memory map

```text
IoC = Who controls object creation?
 |
 +-- Spring container creates beans
 +-- DI supplies dependencies
 +-- Constructor injection is preferred
 +-- Result: loose coupling + testability
```

**Interview memory line:** IoC transfers object-management responsibility to Spring; DI supplies the dependencies a class needs.

---

## Question 2. What is the bean lifecycle and bean scope in Spring?

### 1. Why are we learning this?

In a production application, you need to know when objects are created, when initialization occurs, whether objects are shared, and when cleanup happens.

For example, sharing a stateless payment service can be efficient. Sharing mutable, user-specific data in the same singleton bean can cause concurrency problems.

Bean lifecycle and scope help you manage resource usage, initialization, and application correctness.

### 2. Explanation with ASCII diagrams

**Bean lifecycle**

```text
Bean definition discovered
          |
          v
Object instantiated
          |
          v
Dependencies injected
          |
          v
Aware callbacks / before-init processors
          |
          v
@PostConstruct
          |
          v
After-init processors
          |
          v
Bean ready for use
          |
          v
Container shutdown
          |
          v
@PreDestroy (managed bean)
```

This is a simplified lifecycle. Spring also provides bean post-processors, initialization callbacks, and destruction callbacks.

**Bean scopes**

```text
Spring Container
      |
      +-- Singleton
      |      One instance per bean
      |      within the container
      |
      +-- Prototype
      |      New instance each time
      |      Spring is asked for the bean
      |
      +-- Web scopes
             Request / Session
```

Example:

```java
@Service
@Scope("singleton")
class AccountService {
}

@Component
@Scope("prototype")
class ReportBuilder {
}
```

- **Singleton:** the default scope; one instance per bean definition per container. It is not automatically thread-safe.
- **Prototype:** a new instance each time the container resolves the bean. Spring does not manage its complete destruction lifecycle.
- **Request:** one instance per HTTP request in a web application.
- **Session:** one instance per HTTP session.

You can configure beans through component annotations or Java configuration:

```java
@Configuration
class AppConfig {
    @Bean
    PaymentService paymentService() {
        return new PaymentService();
    }
}
```

`@PostConstruct` can initialize a bean after dependency injection. `@PreDestroy` can perform cleanup when the container shuts down for a managed singleton.

### 3. Short memory map

```text
Bean
 |
 +-- Lifecycle -> Create -> Inject -> Initialize -> Destroy
 |
 +-- Scope
       +-- Singleton -> Shared instance
       +-- Prototype -> New instance per lookup
       +-- Request   -> One per HTTP request
       +-- Session   -> One per HTTP session
```

**Interview memory line:** Lifecycle defines when a bean is created and initialized; scope defines how many instances are used and where they apply.

---

## Question 3. How does Spring Boot auto-configuration work? What are starters and application properties?

### 1. Why are we learning this?

Traditional Spring applications often require substantial manual configuration. In a real project, you do not want to configure every web component, database integration, and JSON converter from scratch.

Spring Boot reduces boilerplate and accelerates application development through sensible defaults and conditional configuration.

### 2. Explanation with an ASCII diagram

```text
       Spring Boot Application
                  |
                  v
           SpringApplication
                  |
                  v
       Auto-configuration imports
                  |
                  v
       Check dependencies and
       existing configuration
                  |
                  v
       Conditional bean creation
                  |
                  v
          Ready application
```

Auto-configuration uses conditions such as:

- Is a relevant library on the classpath?
- Does a required class exist?
- Has the application already defined its own bean?
- Is a particular configuration property enabled?

For example, with the web starter and an appropriate web application setup, Spring Boot can configure common web infrastructure automatically.

**Starters** are convenient dependency bundles.

```text
spring-boot-starter-web
        |
        +-- Spring MVC
        +-- Embedded web server
        +-- JSON support
        +-- Related dependencies
```

**Application properties** control configuration without changing Java code.

```properties
server.port=8081
spring.application.name=payment-service
```

The YAML equivalent is:

```yaml
server:
  port: 8081

spring:
  application:
    name: payment-service
```

Use `@SpringBootApplication` as the common entry-point annotation. It combines configuration, component scanning, and auto-configuration enablement.

### 3. Short memory map

```text
Spring Boot
 |
 +-- Starter     -> Dependencies
 +-- Auto-config -> Sensible defaults
 +-- Properties  -> Application settings
 +-- Custom bean -> Override defaults when appropriate
```

**Interview memory line:** Starters simplify dependency management, auto-configuration supplies conditional defaults, and properties customize application behavior.

---

## Question 4. How does Spring MVC process an HTTP request, and how do REST controllers work?

### 1. Why are we learning this?

When a mobile banking application requests an account balance, you need to understand how the request reaches Java code, how the business logic runs, and how the result becomes JSON.

This knowledge helps you design APIs, debug HTTP errors, and separate web concerns from business logic.

### 2. Explanation with an ASCII diagram

```text
Mobile App / Client
        |
        | HTTP request
        v
DispatcherServlet
        |
        v
Handler Mapping
        |
        v
Controller / REST Controller
        |
        v
Service Layer
        |
        v
Repository / Database
        |
        v
Controller returns result
        |
        v
HTTP Message Converter
        |
        v
JSON Response to Client
```

The `DispatcherServlet` is Spring MVC's front controller. It coordinates request processing.

Example:

```java
@RestController
@RequestMapping("/accounts")
class AccountController {

    private final AccountService accountService;

    AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    @GetMapping("/{id}")
    AccountDto getAccount(@PathVariable Long id) {
        return accountService.getAccount(id);
    }
}
```

What happens when the client calls `GET /accounts/101`?

1. The request reaches the `DispatcherServlet`.
2. Handler mapping identifies the appropriate controller method.
3. Spring binds the path variable to `id`.
4. The controller delegates business logic to `AccountService`.
5. The returned DTO is serialized into JSON by an HTTP message converter, typically Jackson in a standard Spring Boot web setup.

`@Controller` is commonly used for MVC views. `@RestController` combines `@Controller` and `@ResponseBody`, so returned values are written to the HTTP response body.

### 3. Short memory map

```text
HTTP Request
     |
     v
DispatcherServlet
     |
     v
Mapping -> Controller -> Service -> Repository
     |
     v
JSON / HTTP Response
```

**Interview memory line:** DispatcherServlet coordinates the request; controllers handle HTTP mapping, services execute business logic, and message converters serialize responses.

---

## Question 5. What is Aspect-Oriented Programming (AOP) in Spring?

### 1. Why are we learning this?

Several parts of an application need similar behavior: logging, performance measurement, transaction management, and certain authorization checks.

Repeating that code in every business method makes the application difficult to maintain. AOP lets you separate cross-cutting concerns from core business logic.

### 2. Explanation with an ASCII diagram

```text
Client
  |
  v
Spring AOP Proxy
  |
  +-- Before advice
  |
  v
Target Business Method
  |
  +-- After / Around advice
  |
  v
Return result
```

Example:

```java
@Aspect
@Component
class LoggingAspect {

    @Before("execution(* com.example.service.*.*(..))")
    public void logBefore() {
        System.out.println("Service method called");
    }
}
```

Important terminology:

- **Aspect:** a module containing cross-cutting behavior.
- **Advice:** the action to run, such as before, after, or around a method.
- **Pointcut:** an expression selecting the join points where advice applies.
- **Join point:** an execution point; in Spring's proxy-based AOP, advice typically applies to method executions.
- **Proxy:** the object that intercepts eligible calls and applies advice.

Spring AOP commonly uses JDK dynamic proxies or CGLIB-based proxies. Self-invocation—one method calling another method on the same object—typically bypasses proxy-based advice.

### 3. Short memory map

```text
AOP
 |
 +-- Aspect   -> Cross-cutting module
 +-- Advice   -> What to execute
 +-- Pointcut -> Where to execute
 +-- Proxy    -> Intercepts eligible calls
```

**Interview memory line:** Spring AOP applies cross-cutting behavior through proxies, separating infrastructure concerns from business logic.

---

## Question 6. How does Spring Data JPA work, and how does `@Transactional` manage transactions?

### 1. Why are we learning this?

Banking applications store critical information such as balances, transactions, and investment orders. You need reliable database access and transaction boundaries to prevent partial updates and inconsistent data.

Spring Data JPA reduces repetitive database-access code, while transaction management helps maintain data consistency.

### 2. Explanation with an ASCII diagram

```text
Controller
    |
    v
Service Layer
    |
    v
Spring Data JPA Repository
    |
    v
JPA Provider (e.g., Hibernate)
    |
    v
JDBC / Database Driver
    |
    v
Database
```

Define a repository:

```java
interface AccountRepository
        extends JpaRepository<Account, Long> {
}
```

Spring Data JPA provides common operations such as `save()`, `findById()`, and `deleteById()` without requiring you to implement every method.

You can also define query methods:

```java
List<Account> findByStatus(String status);
```

**Transaction example:**

```text
Transfer ₹1,000
      |
      v
Debit Account A
      |
      v
Credit Account B
      |
      +---- Both succeed ----> Commit
      |
      +---- Failure ---------> Rollback*
```

*Rollback depends on transaction configuration and exception rules. By default, Spring rolls back for unchecked exceptions and Errors, but not every checked exception.*

Example:

```java
@Service
class TransferService {

    @Transactional
    public void transfer() {
        // Debit source account
        // Credit destination account
    }
}
```

The transaction should cover both database updates so that they succeed or fail together under the configured transaction manager.

Important interview points:

- `@Transactional` is commonly applied at the service layer.
- Spring usually manages transactions through proxies.
- By default, a runtime exception triggers rollback.
- Self-invocation can bypass proxy-based transaction interception.
- A transaction does not automatically make a distributed operation across multiple services atomic.

### 3. Short memory map

```text
Spring Data JPA
       |
       +-- Repository -> CRUD / Queries
       +-- Hibernate  -> ORM
       +-- Transaction
               |
               +-- Success -> Commit
               +-- Failure -> Rollback*
```

**Interview memory line:** Spring Data JPA simplifies persistence, while `@Transactional` defines a database transaction boundary and provides commit/rollback behavior.

---

## Question 7. How does Spring Security handle authentication, authorization, JWT, and OAuth2?

### 1. Why are we learning this?

A banking API must identify the caller and determine what that caller is allowed to do. A customer should not be able to access another customer's account or execute an administrator operation.

Spring Security provides mechanisms to authenticate identities and enforce access-control policies.

### 2. Explanation with an ASCII diagram

```text
Incoming HTTP Request
          |
          v
  Security Filter Chain
          |
          v
 Authentication Filter
          |
          v
 AuthenticationManager
          |
          v
 AuthenticationProvider
          |
          v
 Validate Credentials / Token
          |
          v
 SecurityContext
          |
          v
 Authorization Check
          |
     +----+----+
     |         |
  Allowed    Denied
     |         |
     v         v
 Controller   403 / 401*
```

*The actual response depends on whether authentication is missing or invalid, whether access is forbidden, and the configured authentication entry point and access-denied handler.*

**Authentication:** Who are you?

**Authorization:** What are you allowed to do?

For JWT-based APIs:

```text
User logs in
    |
    v
Authorization Server
    |
    v
Signed Access Token
    |
    v
Client sends:
Authorization: Bearer <token>
    |
    v
API validates token
    |
    v
Authorization rules
    |
    v
Protected resource
```

A JWT is a signed token containing claims such as issuer, subject, and expiry. The API must validate the signature and relevant claims. A signed JWT is not necessarily encrypted.

Spring Security can validate JWTs using resource-server support. In a typical OAuth2 setup, the authorization server issues tokens and the resource server protects APIs.

OAuth2 is an authorization framework. OpenID Connect adds an identity layer and is commonly used for login.

### 3. Short memory map

```text
Spring Security
       |
       +-- Authentication -> Who are you?
       +-- Authorization  -> What can you access?
       +-- Filter Chain    -> Intercepts requests
       +-- SecurityContext -> Current authentication
       +-- JWT             -> Token-based authentication
       +-- OAuth2 / OIDC   -> Delegated access / identity
```

**Interview memory line:** Spring Security authenticates requests through its filter chain and enforces authorization using configured rules and authorities.

---

## Question 8. How do you handle exceptions, validation, and configuration profiles in Spring Boot?

### 1. Why are we learning this?

Production applications receive invalid inputs, encounter missing records, and run across development, testing, and production environments.

You need consistent error responses, early input validation, and environment-specific configuration without changing application code.

### 2. Explanation with ASCII diagrams

**Exception handling**

```text
HTTP Request
     |
     v
Controller / Service
     |
     v
Exception occurs
     |
     v
@RestControllerAdvice
     |
     v
@ExceptionHandler
     |
     v
Structured HTTP Error Response
```

Example:

```java
@RestControllerAdvice
class GlobalExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    ResponseEntity<String> handle(
            IllegalArgumentException ex) {
        return ResponseEntity.badRequest()
                .body(ex.getMessage());
    }
}
```

In production, use appropriate error codes and avoid exposing internal stack traces or sensitive implementation details to clients.

**Validation**

```text
Incoming JSON
     |
     v
DTO constraints
(@NotBlank, @Email, @Size)
     |
     v
@Valid
     |
     +---- Valid ----> Controller
     |
     +---- Invalid --> 400 response
```

Example:

```java
class CustomerRequest {
    @NotBlank
    private String name;

    @Email
    private String email;
}
```

Apply `@Valid` to the request body parameter to trigger applicable validation.

**Profiles and configuration**

```text
              Spring Boot App
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Dev Config Test Config Prod Config
          |         |         |
          v         v         v
       Dev DB     Test DB    Prod DB
```

Example:

```text
application.yml
application-dev.yml
application-test.yml
application-prod.yml
```

Select a profile with `spring.profiles.active` or the appropriate environment-specific configuration mechanism.

Use `@ConfigurationProperties` for structured, type-safe configuration binding. Keep secrets out of source control and use a suitable secret-management system.

### 3. Short memory map

```text
Reliable Spring API
       |
       +-- Exceptions -> @RestControllerAdvice
       +-- Validation -> @Valid + Constraints
       +-- Profiles   -> Dev / Test / Prod
       +-- Properties -> External configuration
       +-- Secrets    -> Secure secret storage
```

**Interview memory line:** Centralize exception handling, validate inputs at the API boundary, and externalize configuration for each environment.

---

## Question 9. How do you build microservices with Spring Cloud?

### 1. Why are we learning this?

A large banking application may have separate services for payments, accounts, customers, and investments. These services must communicate reliably even when instances change, configuration differs, or a downstream service fails.

Spring Cloud provides integrations and patterns for managing common distributed-system challenges.

### 2. Explanation with an ASCII diagram

```text
                 Mobile / Web Client
                         |
                         v
                    API Gateway
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
        Account Svc  Payment Svc  Investment Svc
             |           |           |
             v           v           v
          Account DB  Payment DB  Investment DB

       Shared Infrastructure
       ---------------------
       Service Discovery
       Config Server
       Circuit Breaker
       Distributed Tracing
```

The key components are:

| Component | Purpose |
|---|---|
| API Gateway | Routes requests and can apply cross-cutting policies |
| Service discovery | Lets services discover available instances dynamically |
| Config Server | Centralizes external configuration |
| Circuit breaker | Stops repeated calls to an unhealthy dependency for a period |
| Distributed tracing | Helps follow requests across service boundaries |

**Example: payment service calling account service**

```text
Payment Service
      |
      v
Circuit Breaker
      |
      v
Account Service
      |
      +---- Success ----> Continue payment flow
      |
      +---- Failure ----> Fail fast / fallback*
```

*A fallback is optional and must be appropriate for the business operation. A failed account-balance check should not be treated as a successful payment authorization.*

For service discovery, an implementation may use a registry such as Eureka. Spring Cloud Gateway handles API routing, while Spring Cloud Config can supply centralized configuration.

In distributed systems, a database transaction typically cannot atomically cover independent services. Business workflows may require patterns such as the Saga pattern, idempotency, retries with limits, and compensating actions.

### 3. Short memory map

```text
Spring Cloud
     |
     +-- Gateway     -> Route
     +-- Discovery   -> Locate
     +-- Config      -> Configure
     +-- Circuit     -> Isolate failures
     +-- Tracing     -> Follow requests
     +-- Saga        -> Coordinate workflows
```

**Interview memory line:** Spring Cloud helps manage service routing, discovery, configuration, resilience, and observability in distributed applications.

---

## Question 10. How do you test Spring applications and monitor them in production?

### 1. Why are we learning this?

Writing code is not enough. You need to verify that it behaves correctly, integrates with real dependencies, and continues to perform reliably after deployment.

Testing catches defects before release. Monitoring and observability help you detect production incidents, identify bottlenecks, and understand failures.

### 2. Explanation with ASCII diagrams

**Testing pyramid**

```text
              /\
             /  \
            / Full \       @SpringBootTest
           /--------\
          /  Slice   \     @WebMvcTest
         /   Tests    \    @DataJpaTest
        /--------------\
       /   Unit Tests   \  JUnit + Mockito
      /__________________\

     Many fast tests at the bottom;
     fewer expensive tests at the top.
```

Typical uses:

- **Unit tests:** test a single class without starting the Spring container.
- **Slice tests:** load a specific layer, such as the MVC or JPA layer.
- **Integration tests:** verify interactions across multiple components.
- **Testcontainers:** run real dependencies such as PostgreSQL or Kafka in containers for realistic integration tests.

**Production monitoring architecture**

```text
Spring Boot Application
          |
          v
Spring Boot Actuator
          |
          v
       Micrometer
          |
          v
      Prometheus
          |
          v
       Grafana
     Dashboards / Alerts
```

Actuator exposes operational endpoints such as:

- `/actuator/health` — health information.
- `/actuator/info` — application information.
- `/actuator/metrics` — available metrics.
- `/actuator/prometheus` — Prometheus-format metrics when the relevant registry is configured.

Expose only the endpoints you need and protect sensitive management endpoints.

**Three pillars of observability**

```text
           Observability
                 |
       +---------+---------+
       |         |         |
       v         v         v
    Metrics     Logs     Traces
       |         |         |
    How much?  What       Where did
               happened?  time go?
```

- **Metrics:** request rate, error rate, latency, memory usage.
- **Logs:** events, errors, contextual information, correlation IDs.
- **Traces:** the journey of a request through multiple services.

Spring Boot integrates with Micrometer for metrics and tracing. OpenTelemetry-compatible instrumentation and tracing backends help visualize distributed requests.

For an engineering leader, useful production signals include p95/p99 latency, error rates, saturation, payment failures, and service availability.

### 3. Short memory map

```text
Spring Production Readiness
       |
       +-- Unit Tests     -> JUnit / Mockito
       +-- Slice Tests    -> MVC / JPA
       +-- Integration    -> Testcontainers
       |
       +-- Actuator       -> Operational endpoints
       +-- Metrics        -> Micrometer / Prometheus
       +-- Dashboards     -> Grafana
       +-- Observability  -> Metrics + Logs + Traces
```

**Interview memory line:** Test at the lowest layer that proves the behavior, use realistic integration tests, and monitor production through health checks, metrics, logs, and distributed traces.

---

## Final revision: all 10 questions in one memory map

```text
                 SPRING FRAMEWORK
                        |
    +-------------------+-------------------+
    |                   |                   |
    v                   v                   v
 OBJECTS             WEB / LOGIC         OPERATIONS
    |                   |                   |
    +-- 1. IoC/DI        +-- 4. MVC           +-- 8. Errors
    +-- 2. Lifecycle     +-- 5. AOP           +-- 9. Cloud
    +-- 3. Boot         +-- 6. JPA           +-- 10. Tests
                        +-- 7. Security             / Monitoring
```

A faster recall sequence:

- **Questions 1–3 — Create and configure:** IoC, beans, Spring Boot.
- **Questions 4–7 — Process and protect:** MVC, AOP, JPA, Security.
- **Questions 8–10 — Operate and improve:** errors, Cloud, testing and monitoring.

## How to study

For each question:

1. Explain the business problem in your own words.
2. Draw the architecture from memory.
3. Explain how the components interact.
4. Give one practical example.
5. Finish with the memory map and interview memory line.

This prepares you for both conceptual questions and system-design follow-ups.
