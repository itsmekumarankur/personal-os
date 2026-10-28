# Spring Core Concepts - Sample Java Demos

Six small, runnable demos of the Spring ideas that matter most in interviews and in production.
Plain Spring Framework 6.1 (no Spring Boot magic), so you can see what the container is doing.
Requires JDK 17+ and Maven 3.8+.

| # | Demo | Concept | Pitfall it shows |
|---|---|---|---|
| 1 | `di/DependencyInjectionDemo` | IoC, constructor injection, `@Primary`, `@Qualifier` | Ambiguity between beans of the same type |
| 2 | `scope/BeanScopeLifecycleDemo` | Singleton vs prototype, `@PostConstruct`, `@PreDestroy` | Prototype injected into a singleton is created only once |
| 3 | `config/ConfigurationProfilesDemo` | `@Configuration`, `@Bean`, `@Profile`, `@Value` | Environment-specific beans and default values |
| 4 | `aop/AopDemo` | Aspects, proxies, `@Around` | Self-invocation bypasses the proxy |
| 5 | `tx/TransactionDemo` | `@Transactional`, rollback rules | Checked exceptions do not roll back by default; self-invocation |
| 6 | `events/EventsDemo` | `ApplicationEventPublisher`, `@EventListener` | Decoupling publisher from reactions |

## Run

Everything:

```
bash run-all.sh
```

One demo:

```
mvn -q compile exec:java -Dexec.mainClass=com.example.spring.tx.TransactionDemo
```

Or open the folder in IntelliJ / Eclipse / VS Code and run the `main` method of any demo.

## Spring Boot equivalents

| Plain Spring (here) | Spring Boot |
|---|---|
| `AnnotationConfigApplicationContext` | `SpringApplication.run(...)` + `@SpringBootApplication` |
| `ctx.getEnvironment().setActiveProfiles("prod")` | `spring.profiles.active=prod` |
| `@Value("${app.fee.rate:0.02}")` | Same, or `@ConfigurationProperties(prefix = "app.fee")` |
| `@EnableTransactionManagement`, manual `DataSource` | Auto-configured by `spring-boot-starter-data-jpa` / `-jdbc` |
| `@EnableAspectJAutoProxy` | Auto-configured by `spring-boot-starter-aop` |
