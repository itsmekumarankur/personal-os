# Design Patterns - Simple Java Examples

Four classic patterns, one runnable file each. Plain Java, no dependencies, JDK 17+.

| File | Pattern | One-line idea | Real-life picture |
|---|---|---|---|
| `AdapterDemo.java` | Adapter | Translate one interface into another | Travel plug adapter |
| `SingletonDemo.java` | Singleton | Exactly one instance, globally accessible | One Prime Minister's office |
| `FactoryDemo.java` | Factory | One place decides which object to build | Ordering "a coffee", kitchen decides how |
| `ObserverDemo.java` | Observer | Subscribers are notified when something changes | YouTube channel subscribers |

## Run

```
java AdapterDemo.java
java SingletonDemo.java
java FactoryDemo.java
java ObserverDemo.java
```

(Single-file source launch, no separate compile step needed.)

## Where you meet them in Spring

- Adapter: `HandlerAdapter`, `JpaVendorAdapter`
- Singleton: default bean scope
- Factory: `BeanFactory`, `ApplicationContext`, `FactoryBean`
- Observer: `ApplicationEventPublisher` + `@EventListener`
