import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.function.Supplier;

/**
 * 8. CIRCULAR DEPENDENCIES - "OrderService needs PaymentService, and PaymentService needs OrderService"
 *
 * Analogy: two people each say "I'll get dressed after YOU open the door". Nobody moves.
 *
 * What the container does when it builds beans:
 *   CONSTRUCTOR injection: to build A it must FIRST have B; to build B it must FIRST have A -> impossible.
 *       Spring fails at startup with BeanCurrentlyInCreationException. This is GOOD: you find the design smell early.
 *   SETTER/FIELD injection: build A (empty), publish a half-ready "early reference", build B, give it the early A,
 *       then finish A. It "works", but objects are used before fully initialised. Spring Boot 2.6+ FORBIDS this by default.
 *
 * Proper fixes (best first):
 *   1. REDESIGN: extract the shared logic into a third bean both depend on (a cycle is usually a missing concept).
 *   2. EVENTS: one side publishes an event instead of calling the other directly.
 *   3. LAZY: inject a provider / @Lazy proxy so the second bean is looked up at first use, not at construction.
 *
 * A 40-line mini container reproduces the behaviour. Real Spring version: spring_snippets/CircularDependencySnippets.java
 * Run: java CircularDependencyDemo.java
 */
public class CircularDependencyDemo {

    @Retention(RetentionPolicy.RUNTIME) @interface Inject { }

    static class Container {
        final Map<String, Class<?>> classes = new HashMap<>();
        final Map<String, Function<Container, Object>> factories = new HashMap<>();
        final Map<String, Object> singletons = new HashMap<>();
        final Map<String, Object> earlyReferences = new HashMap<>();
        final List<String> creating = new ArrayList<>();
        final boolean allowCircular;

        Container(boolean allowCircular) { this.allowCircular = allowCircular; }

        Container register(Class<?> c) { classes.put(nameOf(c), c); return this; }
        Container register(String name, Function<Container, Object> factory) { factories.put(name, factory); return this; }

        static String nameOf(Class<?> c) { String n = c.getSimpleName(); return Character.toLowerCase(n.charAt(0)) + n.substring(1); }

        Object getBean(String name) {
            if (singletons.containsKey(name)) return singletons.get(name);
            if (creating.contains(name)) {
                if (allowCircular && earlyReferences.containsKey(name)) {
                    System.out.println("      (handing out EARLY reference of '" + name + "', not fully initialised yet)");
                    return earlyReferences.get(name);
                }
                throw new IllegalStateException("BeanCurrentlyInCreationException: " + String.join(" -> ", creating) + " -> " + name);
            }
            creating.add(name);
            try {
                Object bean;
                if (factories.containsKey(name)) {
                    bean = factories.get(name).apply(this);
                } else {
                    Constructor<?> ctor = classes.get(name).getDeclaredConstructors()[0];
                    Object[] args = new Object[ctor.getParameterCount()];
                    for (int i = 0; i < args.length; i++) args[i] = getBean(nameOf(ctor.getParameterTypes()[i]));
                    bean = ctor.newInstance(args);                                    // only now does the object exist
                    earlyReferences.put(name, bean);                                  // exposed before field injection
                    for (Field f : bean.getClass().getDeclaredFields()) {
                        if (f.isAnnotationPresent(Inject.class)) { f.setAccessible(true); f.set(bean, getBean(nameOf(f.getType()))); }
                    }
                }
                singletons.put(name, bean);
                return bean;
            } catch (ReflectiveOperationException e) {
                throw new RuntimeException(e);
            } finally {
                creating.remove(name);
                earlyReferences.remove(name);
            }
        }
    }

    // ---- 1. constructor cycle
    public static class CtorOrderService { public CtorOrderService(CtorPaymentService p) { } }
    public static class CtorPaymentService { public CtorPaymentService(CtorOrderService o) { } }

    // ---- 2. field-injection cycle
    public static class FieldOrderService { @Inject FieldPaymentService payments; }
    public static class FieldPaymentService { @Inject FieldOrderService orders; }

    // ---- 3. fix by redesign
    public static class PricingCalculator { double fee(double amount) { return amount * 0.02; } }
    public static class FixedOrderService { final PricingCalculator calc; public FixedOrderService(PricingCalculator c) { calc = c; } }
    public static class FixedPaymentService { final PricingCalculator calc; public FixedPaymentService(PricingCalculator c) { calc = c; } }

    // ---- 4. fix by lazy lookup
    public static class LazyOrderService {
        final Supplier<LazyPaymentService> payments;                                   // ObjectProvider / @Lazy idea
        public LazyOrderService(Supplier<LazyPaymentService> p) { payments = p; }
    }
    public static class LazyPaymentService { final LazyOrderService orders; public LazyPaymentService(LazyOrderService o) { orders = o; } }

    static void attempt(String title, Container c, String bean) {
        System.out.println("\n" + title);
        try {
            Object o = c.getBean(bean);
            System.out.println("   RESULT: created " + o.getClass().getSimpleName() + " OK");
        } catch (RuntimeException e) {
            System.out.println("   RESULT: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        attempt("1) Constructor injection cycle (Spring default behaviour)",
                new Container(false).register(CtorOrderService.class).register(CtorPaymentService.class), "ctorOrderService");

        attempt("2) Field injection cycle with allowCircular=true (old Spring / spring.main.allow-circular-references=true)",
                new Container(true).register(FieldOrderService.class).register(FieldPaymentService.class), "fieldOrderService");

        attempt("2b) Same field injection cycle with allowCircular=false (Spring Boot 2.6+ default)",
                new Container(false).register(FieldOrderService.class).register(FieldPaymentService.class), "fieldOrderService");

        attempt("3) FIX: extract a shared third bean, the cycle disappears",
                new Container(false).register(PricingCalculator.class).register(FixedOrderService.class).register(FixedPaymentService.class),
                "fixedOrderService");

        Container lazy = new Container(false)
                .register(LazyPaymentService.class)
                .register("lazyOrderService", c -> new LazyOrderService(() -> (LazyPaymentService) c.getBean("lazyPaymentService")));
        attempt("4) FIX: inject a lazy handle; the second bean is looked up at first use", lazy, "lazyPaymentService");
        System.out.println("   (lazy supplier resolves later: " + ((LazyPaymentService) lazy.getBean("lazyPaymentService")).orders.payments.get().getClass().getSimpleName() + ")");

        System.out.println("\nRule: if two services need each other, ask 'what concept is missing?' - usually a third class or an event.");
    }
}
