import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 33. THE 12-FACTOR APP (the cloud-native checklist), shown through four of its most important factors
 * The 12-Factor App is a checklist for building apps that run well in the cloud (Docker/Kubernetes).
 *
 *  I    Codebase      one repo per service, many deploys (dev/test/prod) from it
 *  II   Dependencies  declare them explicitly (pom.xml), never rely on "it's installed on that machine"
 *  III  Config        store config in the ENVIRONMENT                       <- Part 1
 *  IV   Backing svcs  treat DB/queue/cache as attached resources, swappable by changing a URL
 *  V    Build/release/run  strict separation, immutable artifacts
 *  VI   Processes     stateless; state lives in backing services            <- Part 2
 *  VII  Port binding  the app exports HTTP by listening on a port it is given
 *  VIII Concurrency   scale OUT by running more processes
 *  IX   Disposability fast startup, graceful shutdown                       <- Part 4
 *  X    Dev/prod parity keep environments as similar as possible
 *  XI   Logs          write events to stdout as a stream; the platform collects them   <- Part 3
 *  XII  Admin tasks   run one-off tasks (migrations) as separate processes
 */
public class TwelveFactorDemo {

    // =============================================================== Part 1: III. Config in the environment

    /*
    **1. Config → keep it in the environment**
        - Read `PORT` and `DATABASE_URL` from environment variables, with safe defaults for your laptop.
        - Same build runs in dev, test and prod. Only the environment changes.
        - Anti-pattern: `if (hostname.equals("prod-box-7"))` or config files baked into the image.
    *                 main()
    *                   |
    *                   v
    *             PART 1: CONFIG
    *                   |
    *                   v
    *         Read environment variables
    *                   |
    *                   v
    *            PORT or default
    *                   |
    *                   v
    *          DATABASE_URL or default
    *                   |
    *                   v
    *         Same application build works
    *            in different envs
    */

    static void part1Config() {
        System.out.println("PART 1 - CONFIG comes from the environment (same build everywhere)");
        String port = System.getenv().getOrDefault("PORT", "8080");
        String dbUrl = System.getenv().getOrDefault("DATABASE_URL", "jdbc:h2:mem:local");
        System.out.println("   PORT         = " + port + (System.getenv("PORT") == null ? "   (default; platform normally injects it)" : ""));
        System.out.println("   DATABASE_URL = " + dbUrl + (System.getenv("DATABASE_URL") == null ? "   (default for laptop)" : ""));
        System.out.println("   Anti-pattern: 'if (hostname.equals(\"prod-box-7\")) useProdDb();' or a config file baked into the image.\n");
    }

    // =============================================================== Part 2: VI. Stateless processes
    static class SessionStore {                                   // stands in for Redis (a backing service)
        final Map<String, String> sessions = new ConcurrentHashMap<>();
    }

    static class AppInstance {
        final String name;
        final Map<String, String> localMemorySessions = new ConcurrentHashMap<>();   // BAD: state inside the process
        final SessionStore shared;                                                    // GOOD: state outside

        AppInstance(String name, SessionStore shared) {
            this.name = name;
            this.shared = shared;
        }

        String loginBad(String user) {
            String token = UUID.randomUUID().toString().substring(0, 6);
            localMemorySessions.put(token, user);
            return token;
        }

        String whoAmIBad(String token) {
            return localMemorySessions.getOrDefault(token, "NOT LOGGED IN");
        }

        String loginGood(String user) {
            String token = UUID.randomUUID().toString().substring(0, 6);
            shared.sessions.put(token, user);
            return token;
        }

        String whoAmIGood(String token) {
            return shared.sessions.getOrDefault(token, "NOT LOGGED IN");
        }
    }

    /*
    Stateless processes → don't keep state in the app (Factor VI)**
    - Bad: sessions stored in the instance's own memory. A load balancer sends your next request to another instance, and you're randomly logged out.
    - Good: sessions stored in a shared backing service (Redis). Any instance can serve any user.
    - Bonus: kill instance-1, start instance-3, and nothing is lost. Instances become disposable.
    *                 main()
    *                   |
    *                   v
    *           PART 2: STATELESS
    *                   |
    *                   v
    *       Create shared SessionStore
    *                   |
    *                   v
    *       Create instances instance-1, -2
    *                   |
    *                   v
    *            Test BAD design
    *                   |
    *                   v
    *          Login on instance-1
    *                   |
    *                   v
    *        Request to instance-2
    *                   |
    *                   v
    *          Session not found
    *           "NOT LOGGED IN"
    *                   |
    *                   v
    *            Test GOOD design
    *                   |
    *                   v
    *          Login on instance-1
    *   Save session in shared SessionStore (Redis)
    *                   |
    *                   v
    *        Request to instance-2
    *                   |
    *                   v
    *         Session found: ankur
    *                   |
    *                   v
    *           Kill instance-1
    *       Replace with instance-3
    *                   |
    *                   v
    *       Session still exists
    *         in shared store
    */
    static void part2Stateless() {
        System.out.println("PART 2 - STATELESS processes (a load balancer sends consecutive requests to different instances)");
        SessionStore redis = new SessionStore();
        AppInstance i1 = new AppInstance("instance-1", redis);
        AppInstance i2 = new AppInstance("instance-2", redis);

        String badToken = i1.loginBad("ankur");
        System.out.println("   session kept in process memory: login on instance-1, next request lands on instance-2 -> "
                + i2.whoAmIBad(badToken) + "   <- user is logged out at random");

        String goodToken = i1.loginGood("ankur");
        System.out.println("   session kept in shared store  : login on instance-1, next request lands on instance-2 -> "
                + i2.whoAmIGood(goodToken));

        AppInstance i3 = new AppInstance("instance-3 (replacement after instance-1 was killed)", redis);
        System.out.println("   instance-1 is killed and replaced by a new pod                                  -> "
                + i3.whoAmIGood(goodToken) + "   <- nothing lost, instances are disposable\n");
    }

    // =============================================================== Part 3: XI. Logs as event streams
    static void log(String level, String traceId, String message) {
        // One JSON object per line on stdout. The platform (Docker/Kubernetes + Loki/ELK/CloudWatch) collects and indexes it.
        System.out.println("   {\"ts\":\"" + Instant.now() + "\",\"level\":\"" + level + "\",\"service\":\"payments\",\"traceId\":\""
                + traceId + "\",\"msg\":\"" + message + "\"}");
    }
/***
3. Logs → write to stdout as a stream (Factor XI)**
- No log files or rotation inside the app.
- Emit one JSON line per event, with a `traceId`.
- The platform (Loki/ELK/CloudWatch) collects and indexes it, so you can search one request across all services and instances.
/*
 *                 main()
 *                   |
 *                   v
 *             PART 3: LOGS
 *                   |
 *                   v
 *            Generate traceId
 *                   |
 *                   v
 *         Write JSON logs to stdout
 *                   |
 *                   v
 *      Platform collects and indexes logs
 */


    static void part3Logs() {
        System.out.println("PART 3 - LOGS are an event stream on stdout (no log files, no log rotation inside the app)");
        String trace = UUID.randomUUID().toString().substring(0, 8);
        log("INFO", trace, "payment received amount=500");
        log("WARN", trace, "gateway slow, retrying attempt=2");
        log("INFO", trace, "payment completed");
        System.out.println("   Structured (JSON) lines with a traceId can be searched across ALL services and instances.\n");
    }

    // =============================================================== Part 4: IX. Disposability
    /**
    Disposability → start fast, stop gracefully (Factor IX)**
    - A shutdown hook runs when the platform sends SIGTERM.
    - Steps: stop accepting new requests, finish in-flight work (e.g., payments), close connections, flush logs, exit cleanly.
    - Spring Boot equivalent: `server.shutdown=graceful`.

    *       PART 4: DISPOSABILITY
    *             |
    *             v
    *       Register shutdown hook
    *             |
    *             v
    *       main() finishes
    *             |
    *             v
    *       JVM begins shutdown
    *             |
    *             v
    *       +--------------------------------+
    *       | Shutdown hook executes         |
    *       |                                |
    *       | 1. Receive shutdown signal     |
    *       | 2. Stop accepting new requests |
    *       | 3. Finish in-flight payments   |
    *       | 4. Close connections           |
    *       | 5. Flush logs                  |
    *       +----------------+---------------+
    *                        |
    *                        v
    *                   CLEAN EXIT
    * 
    */
    static void part4Disposability() {
        System.out.println("PART 4 - DISPOSABILITY (fast start, graceful stop). This JVM registers a shutdown hook;");
        System.out.println("         it runs when the platform sends SIGTERM (or when this demo ends).");
        List<String> inFlight = new ArrayList<>(List.of("payment-101", "payment-102"));
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\n   [shutdown hook] SIGTERM received");
            System.out.println("   [shutdown hook] 1. stop accepting new requests (readiness = false)");
            System.out.println("   [shutdown hook] 2. finish in-flight work: " + inFlight);
            inFlight.clear();
            System.out.println("   [shutdown hook] 3. close connections, flush logs, exit cleanly");
            System.out.println("   (Spring Boot: server.shutdown=graceful + spring.lifecycle.timeout-per-shutdown-phase=20s)");
        }));
    }

    public static void main(String[] args) {
        part1Config();
        part2Stateless();
        part3Logs();
        part4Disposability();
        System.out.println("\nDemo main() finished, JVM is exiting now...");
    }

}
