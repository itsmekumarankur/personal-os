import java.time.Instant;
import java.util.Arrays;
import java.util.UUID;

/**
 * 25. DISTRIBUTED ID GENERATION - UUID vs Snowflake-style IDs
 *
 * With many service instances you cannot just use a single database counter (it is a bottleneck
 * and a single point of failure). You need IDs that are unique WITHOUT coordination.
 *
 * UUID v4  : 128-bit random. Zero coordination, collision chance negligible. But random, so not sortable by
 *            time, big (16 bytes), and random inserts fragment database indexes.
 * Snowflake: 64-bit number = [ 41 bits time | 10 bits machine id | 12 bits sequence ].
 *            Roughly time-ordered, compact (fits a long), 4096 ids per millisecond per machine.
 *            Needs each machine to have a distinct machine id, and a sane clock.
 * Also seen: UUIDv7 / ULID (time-ordered UUID-like ids), DB sequences with ranges (hi/lo), Flickr ticket servers.
 *
 * Run: java DistributedIdDemo.java
 */
public class DistributedIdDemo {

    static class Snowflake {
        static final long EPOCH = 1_700_000_000_000L;        // our own "time zero" (Nov 2023)
        static final int NODE_BITS = 10, SEQ_BITS = 12;
        static final long MAX_SEQ = (1L << SEQ_BITS) - 1;

        private final long nodeId;
        private long lastTimestamp = -1;
        private long sequence = 0;

        Snowflake(long nodeId) {
            if (nodeId < 0 || nodeId >= (1L << NODE_BITS)) {
                throw new IllegalArgumentException("nodeId must be 0.." + ((1L << NODE_BITS) - 1));
            }
            this.nodeId = nodeId;
        }

        synchronized long nextId() {
            long now = System.currentTimeMillis();
            if (now < lastTimestamp) {
                throw new IllegalStateException("clock moved backwards, refusing to generate ids");
            }
            if (now == lastTimestamp) {
                sequence = (sequence + 1) & MAX_SEQ;
                if (sequence == 0) {                           // 4096 ids used up in this millisecond: wait for the next
                    while (now <= lastTimestamp) {
                        now = System.currentTimeMillis();
                    }
                }
            } else {
                sequence = 0;
            }
            lastTimestamp = now;
            return ((now - EPOCH) << (NODE_BITS + SEQ_BITS)) | (nodeId << SEQ_BITS) | sequence;
        }

        static void describe(long id) {
            long seq = id & MAX_SEQ;
            long node = (id >> SEQ_BITS) & ((1L << NODE_BITS) - 1);
            long ts = (id >> (NODE_BITS + SEQ_BITS)) + EPOCH;
            System.out.printf("   id %d%n     binary   : %s%n     timestamp: %s%n     node id  : %d%n     sequence : %d%n",
                    id, String.format("%64s", Long.toBinaryString(id)).replace(' ', '0'),
                    Instant.ofEpochMilli(ts), node, seq);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("1) Anatomy of a Snowflake id (node 5)");
        Snowflake.describe(new Snowflake(5).nextId());

        System.out.println("\n2) Three 'machines' generate 200,000 ids each, concurrently, with no coordination");
        int perNode = 200_000;
        long[][] results = new long[3][perNode];
        Thread[] threads = new Thread[3];
        long start = System.nanoTime();
        for (int n = 0; n < 3; n++) {
            final int node = n;
            threads[n] = new Thread(() -> {
                Snowflake gen = new Snowflake(node + 1);
                for (int i = 0; i < perNode; i++) {
                    results[node][i] = gen.nextId();
                }
            });
            threads[n].start();
        }
        for (Thread t : threads) t.join();
        double seconds = (System.nanoTime() - start) / 1e9;

        long[] all = new long[3 * perNode];
        for (int n = 0; n < 3; n++) {
            System.arraycopy(results[n], 0, all, n * perNode, perNode);
        }
        Arrays.sort(all);
        int duplicates = 0;
        for (int i = 1; i < all.length; i++) {
            if (all[i] == all[i - 1]) duplicates++;
        }
        boolean ordered = true;
        for (int n = 0; n < 3; n++) {
            for (int i = 1; i < perNode; i++) {
                if (results[n][i] <= results[n][i - 1]) ordered = false;
            }
        }
        System.out.printf("   generated %,d ids in %.2f s, duplicates: %d, each node's ids strictly increasing: %s%n",
                all.length, seconds, duplicates, ordered);

        System.out.println("\n3) UUID v4: unique, but random (no time order)");
        UUID[] uuids = new UUID[5];
        for (int i = 0; i < uuids.length; i++) {
            uuids[i] = UUID.randomUUID();
            System.out.println("   created #" + (i + 1) + ": " + uuids[i]);
        }
        UUID[] sorted = uuids.clone();
        Arrays.sort(sorted);
        boolean sameOrder = Arrays.equals(uuids, sorted);
        System.out.println("   sorting them gives creation order? " + sameOrder + "  (random ids scatter across a B-tree index)");

        System.out.println("\n4) Size: UUID = 128 bits (16 bytes, 36 chars as text), Snowflake = 64 bits (8 bytes, fits a Java long / BIGINT)");

        System.out.println("\nChoosing: UUID for 'just make it unique', public-facing ids that must not be guessable, or no machine registry."
                + "\nSnowflake/ULID/UUIDv7 when you want sortable ids and good index locality (events, orders, ledger rows).");
    }
}
