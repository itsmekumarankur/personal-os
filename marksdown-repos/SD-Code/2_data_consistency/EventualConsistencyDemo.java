import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;

/**
 * 23. EVENTUAL CONSISTENCY - why reads can be stale
 *
 * Copies of data (replicas, caches, read models, other services) are updated a little AFTER the
 * original. For a short window, different readers see different answers. "Eventually" they agree.
 *
 * Picture: you update your address on the bank's app, but the SMS system still uses the old one
 * for a few seconds.
 *
 * Techniques to live with it:
 *   - read-your-writes: after a user writes, route THAT user's reads to the source of truth
 *     (or wait until the replica has caught up to the version they wrote)
 *   - show "processing..." instead of pretending it is instant
 *   - make operations idempotent and design UIs to tolerate old data
 *
 * Run: java EventualConsistencyDemo.java
 */
public class EventualConsistencyDemo {

    record Change(String key, int value, long version) {
    }

    static class Primary {
        final ConcurrentHashMap<String, Integer> data = new ConcurrentHashMap<>();
        volatile long version = 0;
        final BlockingQueue<Change> replicationLog = new LinkedBlockingQueue<>();

        long write(String key, int value) {
            data.put(key, value);
            long v = ++version;
            replicationLog.add(new Change(key, value, v));       // shipped to the replica asynchronously
            return v;                                             // a "version token" for the caller
        }

        Integer read(String key) {
            return data.get(key);
        }
    }

    static class Replica {
        final ConcurrentHashMap<String, Integer> data = new ConcurrentHashMap<>();
        volatile long appliedVersion = 0;

        Integer read(String key) {
            return data.get(key);
        }
    }

    static void startReplication(Primary primary, Replica replica, long lagMillis) {
        Thread t = new Thread(() -> {
            try {
                while (true) {
                    Change c = primary.replicationLog.take();
                    Thread.sleep(lagMillis);                      // network + apply delay
                    replica.data.put(c.key(), c.value());
                    replica.appliedVersion = c.version();
                }
            } catch (InterruptedException ignored) {
            }
        });
        t.setDaemon(true);
        t.start();
    }

    // Read-your-writes using a version token
    static Integer readAfterWrite(Primary primary, Replica replica, String key, long token) {
        if (replica.appliedVersion >= token) {
            return replica.read(key) ;                            // replica is fresh enough: cheap read
        }
        return primary.read(key);                                 // replica behind: go to the source of truth
    }

    public static void main(String[] args) throws Exception {
        Primary primary = new Primary();
        Replica replica = new Replica();
        startReplication(primary, replica, 400);

        primary.write("balance", 1000);
        Thread.sleep(600);                                        // let the first value replicate
        System.out.println("Starting state: primary=" + primary.read("balance") + ", replica=" + replica.read("balance"));

        System.out.println("\n1) User deposits 500 (new balance 1500), then immediately refreshes the screen");
        long token = primary.write("balance", 1500);
        System.out.println("   primary read : " + primary.read("balance"));
        System.out.println("   replica read : " + replica.read("balance") + "   <- STALE, replication has not arrived yet");

        System.out.println("\n2) Fix: read-your-writes using the version token returned by the write");
        System.out.println("   smart read   : " + readAfterWrite(primary, replica, "balance", token)
                + "   (replica behind, so we asked the primary)");

        System.out.println("\n3) A moment later the replica has caught up:");
        Thread.sleep(600);
        System.out.println("   replica read : " + replica.read("balance") + "   (eventually consistent)");
        System.out.println("   smart read   : " + readAfterWrite(primary, replica, "balance", token)
                + "   (replica is fresh enough now, cheap read)");

        System.out.println("\nTrade-off (CAP in practice): replicas and caches buy speed and availability; the price is a short window of stale reads.");
        System.out.println("Money movements must still be validated against the source of truth, never against a stale copy.");
    }
}
