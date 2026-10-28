import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Supplier;

/**
 * 2. SPRING BOOT AUTO-CONFIGURATION - "how does adding a jar magically create beans?"
 *
 * Analogy: a hotel room that sets itself up depending on the guest.
 *   - If you bring your own kettle (your own bean), the hotel does NOT put one in the room (@ConditionalOnMissingBean).
 *   - If you ask for a sea view (a property), you get it (@ConditionalOnProperty).
 *   - The gym opens only if the equipment arrived (@ConditionalOnClass = jar is on the classpath).
 *
 * The actual mechanism is small:
 *   1. a "starter" dependency simply puts jars on the classpath
 *   2. Boot reads a list of auto-configuration classes (META-INF/spring/...AutoConfiguration.imports)
 *   3. each class has @Conditional checks; when they all pass, its @Bean methods run
 *   4. YOUR beans are registered first, so with @ConditionalOnMissingBean yours always WINS
 *
 * This demo imitates that and prints a "condition evaluation report" like `--debug` does in Spring Boot.
 * Real Spring version: spring_snippets/AutoConfigSnippets.java
 *
 * Run: java AutoConfigurationConditionalDemo.java
 */
public class AutoConfigurationConditionalDemo {

    record Ctx(Set<String> classpath, Map<String, String> props, Map<String, Object> beans) { }

    interface Condition { String failure(Ctx c); }          // null = condition passed, otherwise the reason it failed

    static Condition onClass(String cls) {
        return c -> c.classpath().contains(cls) ? null : "@ConditionalOnClass: " + cls + " is not on the classpath";
    }

    static Condition onMissingBean(String type) {
        return c -> c.beans().containsKey(type) ? "@ConditionalOnMissingBean: a " + type + " bean already exists (yours)" : null;
    }

    static Condition onProperty(String key, String expected, boolean matchIfMissing) {
        return c -> {
            String v = c.props().get(key);
            boolean ok = v == null ? matchIfMissing : v.equals(expected);
            return ok ? null : "@ConditionalOnProperty: " + key + "=" + v + " (needs " + expected + ")";
        };
    }

    record AutoConfig(String name, List<Condition> conditions, String beanType, Supplier<Object> factory) { }

    static final List<AutoConfig> AUTO_CONFIGS = List.of(
            new AutoConfig("DataSourceAutoConfiguration", List.of(onClass("org.h2.Driver"), onMissingBean("DataSource")),
                    "DataSource", () -> "H2 in-memory DataSource"),
            new AutoConfig("JacksonAutoConfiguration", List.of(onClass("com.fasterxml.jackson.databind.ObjectMapper"), onMissingBean("ObjectMapper")),
                    "ObjectMapper", () -> "default ObjectMapper (camelCase)"),
            new AutoConfig("MetricsAutoConfiguration", List.of(onProperty("management.metrics.enabled", "true", true)),
                    "MeterRegistry", () -> "SimpleMeterRegistry"),
            new AutoConfig("CacheAutoConfiguration", List.of(onClass("com.github.benmanes.caffeine.Caffeine"), onMissingBean("CacheManager")),
                    "CacheManager", () -> "CaffeineCacheManager"));

    static void run(String title, Set<String> classpath, Map<String, String> props, Map<String, Object> userBeans) {
        System.out.println("\n=== " + title);
        System.out.println("   classpath : " + classpath);
        System.out.println("   properties: " + props);
        System.out.println("   YOUR beans: " + userBeans);
        Map<String, Object> beans = new LinkedHashMap<>(userBeans);
        List<String> positive = new ArrayList<>(), negative = new ArrayList<>();
        Ctx ctx = new Ctx(classpath, props, beans);
        for (AutoConfig ac : AUTO_CONFIGS) {
            String reason = null;
            for (Condition c : ac.conditions()) {
                reason = c.failure(ctx);
                if (reason != null) break;
            }
            if (reason == null) {
                beans.put(ac.beanType(), ac.factory().get() + "  (auto)");
                positive.add(ac.name());
            } else {
                negative.add(ac.name() + "\n         did not match: " + reason);
            }
        }
        System.out.println("   Positive matches : " + positive);
        System.out.println("   Negative matches :");
        negative.forEach(n -> System.out.println("      - " + n));
        System.out.println("   FINAL BEANS:");
        beans.forEach((k, v) -> System.out.println("      " + k + " = " + v));
    }

    public static void main(String[] args) {
        Set<String> base = Set.of("org.h2.Driver", "com.fasterxml.jackson.databind.ObjectMapper");
        run("A) typical app with web + h2 starters", base, Map.of(), Map.of());
        run("B) you define your own DataSource: auto-config BACKS OFF", base, Map.of(),
                Map.of("DataSource", "PostgreSQL DataSource  (yours)"));
        run("C) property switches a feature off", base, Map.of("management.metrics.enabled", "false"), Map.of());
        run("D) you add the Caffeine jar: the cache config switches ON by itself",
                Set.of("org.h2.Driver", "com.fasterxml.jackson.databind.ObjectMapper", "com.github.benmanes.caffeine.Caffeine"),
                Map.of(), Map.of());
        System.out.println("\nTo see the REAL report in Spring Boot: run with --debug (or debug=true) and read the CONDITIONS EVALUATION REPORT.");
    }
}
