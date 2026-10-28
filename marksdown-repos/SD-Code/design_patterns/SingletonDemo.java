import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * SINGLETON - exactly ONE instance of a class for the whole application.
 *
 * Real-life: a country has one Prime Minister's office. Everybody who needs it
 * goes to the same one, nobody builds a second.
 *
 * Use for: configuration, connection pools, caches, loggers.
 * Note: in Spring you rarely write this yourself, beans are singletons by default
 * (one per container) and Spring manages them for you.
 *
 * Run: java SingletonDemo.java
 */
public class SingletonDemo {

    static final AtomicInteger CREATED = new AtomicInteger(); // counts constructor calls

    // ---- BAD: lazy "singleton" that is NOT thread-safe ----
    static class BrokenSingleton {
        private static BrokenSingleton instance;

        private BrokenSingleton() {
            pretendToDoSlowWork(); // widens the race window so the bug shows up reliably
            CREATED.incrementAndGet();
        }

        static BrokenSingleton getInstance() {
            if (instance == null) {          // two threads can both see null here...
                instance = new BrokenSingleton(); // ...and both create an object
            }
            return instance;
        }
    }

    static void pretendToDoSlowWork() {
        try {
            Thread.sleep(20);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    // Same slow constructor, but built the safe way (holder idiom, explained below)
    static class SafeSlowSingleton {
        private SafeSlowSingleton() {
            pretendToDoSlowWork();
            CREATED.incrementAndGet();
        }

        private static class Holder {
            static final SafeSlowSingleton INSTANCE = new SafeSlowSingleton();
        }

        static SafeSlowSingleton getInstance() {
            return Holder.INSTANCE;
        }
    }

    // ---- GOOD 1: initialization-on-demand holder (lazy + thread-safe, no locks) ----
    static class AppConfig {
        private AppConfig() {
            CREATED.incrementAndGet();
            System.out.println("  AppConfig created (only once)");
        }

        // The JVM loads Holder only when getInstance() is first called,
        // and class loading is guaranteed thread-safe.
        private static class Holder {
            static final AppConfig INSTANCE = new AppConfig();
        }

        static AppConfig getInstance() {
            return Holder.INSTANCE;
        }

        String currency() {
            return "INR";
        }
    }

    // ---- GOOD 2: enum singleton (simplest, also safe against reflection & serialization) ----
    enum AuditLog {
        INSTANCE;

        private final List<String> entries = Collections.synchronizedList(new ArrayList<>());

        void record(String entry) {
            entries.add(entry);
        }

        int size() {
            return entries.size();
        }
    }

    public static void main(String[] args) throws Exception {
        // 1) Same object every time
        AppConfig a = AppConfig.getInstance();
        AppConfig b = AppConfig.getInstance();
        System.out.println("Same AppConfig instance? " + (a == b) + " (currency=" + a.currency() + ")");

        // 2) Enum singleton shared state
        AuditLog.INSTANCE.record("login");
        AuditLog.INSTANCE.record("transfer");
        System.out.println("AuditLog entries via INSTANCE: " + AuditLog.INSTANCE.size());

        // 3) 20 threads ask for the "singleton" at the same moment
        System.out.println("20 threads, broken lazy singleton -> objects created: " + race(BrokenSingleton::getInstance)
                + "  (should be 1, but threads raced)");
        System.out.println("20 threads, holder-idiom singleton -> objects created: " + race(SafeSlowSingleton::getInstance)
                + "  (always 1)");
    }

    // Starts 20 threads together and returns how many objects the constructor produced
    static int race(Runnable getInstanceCall) throws InterruptedException {
        CREATED.set(0);
        Thread[] threads = new Thread[20];
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(getInstanceCall);
        }
        for (Thread t : threads) {
            t.start();
        }
        for (Thread t : threads) {
            t.join();
        }
        return CREATED.get();
    }
}
