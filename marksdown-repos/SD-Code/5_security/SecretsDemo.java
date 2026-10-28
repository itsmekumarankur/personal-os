import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

/**
 * 42. SECRETS HANDLING - where secrets live, how to read them, how not to leak them
 *
 * RULES
 *   1. Never in source code or git (history is forever, even after you delete the file).
 *   2. Never baked into a Docker image (anyone with the image has the secret).
 *   3. Inject at runtime: environment variable, mounted file (Kubernetes Secret / Docker secret),
 *      or fetch from a secret manager (Vault, AWS Secrets Manager, GCP Secret Manager) at startup.
 *   4. FAIL FAST at startup if a required secret is missing (do not run half-configured).
 *   5. MASK in logs and toString(). Never log tokens, passwords, card numbers.
 *   6. Rotate regularly; design so rotation needs a restart/refresh, not a code change.
 *   7. One secret per purpose and per environment; least privilege.
 *
 * Mounted FILE is preferred over env vars when possible: env vars leak via process dumps, crash reports,
 * child processes and `docker inspect`. Convention: PASSWORD_FILE=/run/secrets/db_password
 *
 * Run: java SecretsDemo.java
 */
public class SecretsDemo {

    // ------------------------------------------------------------- 1. a value type that cannot be logged by accident
    static final class Secret {
        private final String value;

        Secret(String value) {
            this.value = value;
        }

        String reveal() {                 // explicit, greppable call: every use is deliberate
            return value;
        }

        @Override
        public String toString() {
            return "******";
        }
    }

    record DbConfig(String url, String user, Secret password) {      // record toString() calls Secret.toString()
    }

    // ------------------------------------------------------------- 2. load: file first, then env var, else FAIL FAST
    static Secret load(String name, Map<String, String> env) throws Exception {
        String filePath = env.get(name + "_FILE");
        if (filePath != null) {
            return new Secret(Files.readString(Path.of(filePath)).strip());
        }
        String direct = env.get(name);
        if (direct != null && !direct.isBlank()) {
            return new Secret(direct);
        }
        throw new IllegalStateException("Required secret " + name + " is not set (set " + name + " or " + name + "_FILE). Refusing to start.");
    }

    // ------------------------------------------------------------- 3. masking free text before logging
    static String mask(String logLine) {
        return logLine
                .replaceAll("(?i)(password|secret|token|authorization)(\\s*[=:]\\s*)(\\S+)", "$1$2******")
                .replaceAll("\\b(\\d{4})\\d{8}(\\d{4})\\b", "$1********$2");      // card number: keep first and last 4
    }

    public static void main(String[] args) throws Exception {
        System.out.println("1) Secret type: logging the whole config object is safe");
        DbConfig cfg = new DbConfig("jdbc:postgresql://db:5432/pay", "payments", new Secret("S3cr3t!"));
        System.out.println("   log: " + cfg);
        System.out.println("   only code that calls reveal() can see it: " + cfg.password().reveal().length() + " characters\n");

        System.out.println("2) Loading from an env var");
        System.out.println("   " + load("DB_PASSWORD", Map.of("DB_PASSWORD", "from-env")) + "  (loaded, printed masked)");

        System.out.println("\n3) Loading from a mounted file (Kubernetes Secret volume / Docker secret)");
        Path file = Files.createTempFile("db_password", ".txt");
        Files.writeString(file, "from-mounted-file\n");
        Secret fromFile = load("DB_PASSWORD", Map.of("DB_PASSWORD_FILE", file.toString()));
        System.out.println("   " + fromFile + "  value length " + fromFile.reveal().length() + " (trailing newline stripped)");
        Files.delete(file);

        System.out.println("\n4) Missing secret -> fail fast at startup");
        try {
            load("PAYMENT_API_KEY", Map.of());
        } catch (IllegalStateException e) {
            System.out.println("   STARTUP ABORTED: " + e.getMessage());
        }

        System.out.println("\n5) Masking accidental leaks in free-text logs");
        String[] lines = {
                "calling gateway with token=eyJhbGciOiJIUzI1NiJ9.abc.def",
                "login attempt user=ankur password=hunter2",
                "charging card 4111111111111111 amount=50"};
        for (String l : lines) {
            System.out.println("   before: " + l);
            System.out.println("   after : " + mask(l));
        }

        System.out.println("\nAlso: run secret scanners (gitleaks, trufflehog) in CI and as a pre-commit hook; "
                + "\nif a secret ever hits git, ROTATE it - deleting the commit is not enough.");
    }
}
