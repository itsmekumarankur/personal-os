import java.io.IOException;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

/**
 * 31. EXTERNALIZED CONFIGURATION: profiles, environment variables, command line
 *
 * Rule: the SAME build artifact (one JAR / one Docker image) must run in dev, test and prod.
 * Only the CONFIGURATION changes, and it comes from OUTSIDE the code.
 *
 * Spring Boot looks in many places and the HIGHER one wins (simplified order, lowest to highest):
 *      1. built-in defaults                 (in code)
 *      2. application.properties/.yml       (shared file)
 *      3. application-{profile}.properties  (profile specific file, e.g. -prod)
 *      4. environment variables             (APP_FEE_RATE  ==  app.fee.rate)
 *      5. command-line arguments            (--server.port=9090)
 *
 * This file re-implements that rule in ~40 lines so you can SEE the layering.
 * Real Spring Boot snippets (YAML, @ConfigurationProperties, Config Server): spring_snippets/
 *
 * Run: java ExternalizedConfigDemo.java
 */
public class ExternalizedConfigDemo {

    interface Source {
        String name();

        String get(String key);
    }

    static Source fromMap(String name, Map<String, String> values) {
        return new Source() {
            public String name() {
                return name;
            }

            public String get(String key) {
                return values.get(key);
            }
        };
    }

    static Source fromFile(String name, Path file) throws IOException {
        Properties p = new Properties();
        if (Files.exists(file)) {
            p.load(new StringReader(Files.readString(file)));
        }
        Map<String, String> m = new HashMap<>();
        p.forEach((k, v) -> m.put((String) k, (String) v));
        return fromMap(name, m);
    }

    // relaxed binding: app.fee.rate  ->  APP_FEE_RATE
    static Source fromEnvironment(Map<String, String> environment) {
        return new Source() {
            public String name() {
                return "environment variable";
            }

            public String get(String key) {
                return environment.get(key.toUpperCase().replace('.', '_').replace('-', '_'));
            }
        };
    }

    static Source fromCommandLine(String[] args) {
        Map<String, String> m = new HashMap<>();
        for (String a : args) {
            if (a.startsWith("--") && a.contains("=")) {
                m.put(a.substring(2, a.indexOf('=')), a.substring(a.indexOf('=') + 1));
            }
        }
        return fromMap("command-line argument", m);
    }

    static class Config {
        private final List<Source> highToLow;

        Config(List<Source> highToLow) {
            this.highToLow = highToLow;
        }

        String describe(String key) {
            for (Source s : highToLow) {                     // first (highest priority) source that has the key wins
                String v = s.get(key);
                if (v != null) {
                    boolean secret = key.contains("password");
                    return String.format("%-22s = %-30s  <- %s", key, secret ? "****** (masked)" : v, s.name());
                }
            }
            return String.format("%-22s = (not set)", key);
        }
    }

    static Config build(Path dir, Map<String, String> environment, String[] args) throws IOException {
        Source cli = fromCommandLine(args);
        Source env = fromEnvironment(environment);
        Source appFile = fromFile("application.properties", dir.resolve("application.properties"));
        Source defaults = fromMap("built-in default",
                Map.of("server.port", "8080", "app.fee.rate", "0.02", "app.gateway.url", "http://localhost:9000"));

        // which profile is active? (itself comes from config: cli > env > file)
        String profile = cli.get("spring.profiles.active");
        if (profile == null) profile = env.get("spring.profiles.active");
        if (profile == null) profile = appFile.get("spring.profiles.active");

        List<Source> highToLow = new ArrayList<>(List.of(cli, env));
        if (profile != null) {
            highToLow.add(fromFile("application-" + profile + ".properties", dir.resolve("application-" + profile + ".properties")));
        }
        highToLow.add(appFile);
        highToLow.add(defaults);
        System.out.println("   active profile: " + (profile == null ? "(none)" : profile));
        return new Config(highToLow);
    }

    static void show(String title, Config config) {
        System.out.println(title);
        for (String key : List.of("server.port", "app.fee.rate", "app.gateway.url", "app.db.password")) {
            System.out.println("   " + config.describe(key));
        }
        System.out.println();
    }

    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("config-demo");
        Files.writeString(dir.resolve("application.properties"),
                "app.fee.rate=0.025\napp.gateway.url=http://sandbox.gateway.local\n");
        Files.writeString(dir.resolve("application-prod.properties"),
                "server.port=8443\napp.gateway.url=https://pay.example.com\n");

        System.out.println("Files shipped with the app:");
        System.out.println("   application.properties       : app.fee.rate=0.025, app.gateway.url=http://sandbox.gateway.local");
        System.out.println("   application-prod.properties  : server.port=8443, app.gateway.url=https://pay.example.com\n");

        System.out.println("Run 1: laptop, nothing special");
        show("   result:", build(dir, Map.of(), new String[]{}));

        System.out.println("Run 2: production, switched on by an environment variable (SPRING_PROFILES_ACTIVE=prod)");
        show("   result:", build(dir, Map.of("SPRING_PROFILES_ACTIVE", "prod"), new String[]{}));

        System.out.println("Run 3: production + the platform injects APP_FEE_RATE and a SECRET, operator adds --server.port=9090");
        show("   result:", build(dir,
                Map.of("SPRING_PROFILES_ACTIVE", "prod", "APP_FEE_RATE", "0.03", "APP_DB_PASSWORD", "s3cr3t-from-secret-store"),
                new String[]{"--server.port=9090"}));

        System.out.println("Notes:");
        System.out.println("  - same code, three behaviours, zero rebuilds");
        System.out.println("  - secrets (db password) come from the environment / secret store, never from files in git");
        System.out.println("  - Spring Cloud Config Server adds ONE more source: a central git-backed config service the app pulls at startup");

        try (var files = Files.list(dir)) {
            files.forEach(f -> f.toFile().delete());
        }
        dir.toFile().delete();
    }
}
