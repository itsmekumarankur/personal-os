
/*      
        OPTIMISTIC LOCKING - THE BIG IDEA
        * ================================================================
        *
        *   Problem: LOST UPDATE
        *   Two users read the same record, both change it,
        *   the last save silently overwrites the first.
        *
        *   Pessimistic : lock the row while editing
        *                 (safe, but others wait)
        *   Optimistic  : assume conflicts are rare, check the VERSION at save
        *
        *   SQL idea:
        *     UPDATE account
        *        SET balance = ?, version = version + 1
        *      WHERE id = ? AND version = ?      <-- expected version
        *
        *     rows updated = 1  -> success
        *     rows updated = 0  -> someone got there first -> reload + retry
        *
        *   JPA does this for you when you put @Version on a field.
        *
        * ================================================================
        * PART A: ALICE AND BOB, SAME ACCOUNT
        * ================================================================
        *
        *   Start: balance = 100, version = 2
        *
        *        ALICE                                BOB
        *          |                                   |
        *    read (100, v2)                      read (100, v2)
        *          |                                   |
        *    deposit 50                          withdraw 30
        *    save 150, expects v2                save 70, expects v2
        *          |                                   |
        *          v                                   |
        *    version is v2 -> OK                       |
        *    balance = 150, version = v3               |
        *                                              v
        *                                   version is now v3, Bob expected v2
        *                                   -> 0 rows updated -> CONFLICT
        *                                              |
        *                                              v
        *                                   reload (150, v3)
        *                                   reapply withdraw 30
        *                                   save 120, expects v3 -> OK
        *
        *   WITHOUT versions : Bob's save of 70 wipes Alice's deposit  -> 70  (WRONG)
        *   WITH versions    : conflict caught, retried                -> 120 (CORRECT)
        *
        * ================================================================
        * PART B: STRESS TEST (4 threads x 2000 increments, expected 8000)
        * ================================================================
        *
        *   NO VERSION CHECK                     OPTIMISTIC LOCKING
        *   ----------------                     ------------------
        *   read v                               read (value, version)
        *   (tiny sleep)                         (tiny sleep)
        *   write v + 1  (blind)                 update only if version unchanged
        *        |                                    |
        *        v                                    +-- OK -------> done
        *   threads overwrite each                    |
        *   other's work                              +-- CONFLICT -> reload, retry
        *        |                                         (counted in retries)
        *        v                                    |
        *   result << 8000                            v
        *   LOST UPDATES                         result = exactly 8000
        *                                        after many conflict retries
        *
        * ================================================================
        * PESSIMISTIC vs OPTIMISTIC
        * ================================================================
        *
        *   PESSIMISTIC                          OPTIMISTIC
        *   -----------                          ----------
        *   lock row while editing               no lock, check version at save
        *   SELECT ... FOR UPDATE                WHERE version = ?
        *   others wait                          others proceed, loser retries
        *   + no retries                         + no waiting, scales well
        *   - locks across network calls         - retries wasted if conflicts
        *     are dangerous                        are frequent
        *   best for HOT rows                    best when conflicts are RARE
        *
        * ================================================================
        * KEY TAKEAWAY
        * ================================================================
        *
        *  Lost update   -> last write silently overwrites the first
        *  Version       -> a counter bumped on every successful update
        *  Check at save -> WHERE version = expected; 0 rows = conflict
        *  On conflict   -> reload fresh data, reapply the change, retry
        *  JPA           -> @Version does all of this automatically
        *  Choose        -> optimistic for most web apps,
        *                   pessimistic only for constantly contended rows
        *
        * ================================================================
 
 */
public class OptimisticLockingDemo {

    record Row(int value, int version) {
    }

    // ---------------- naive store: last write wins ----------------
    static class NaiveStore {
        volatile int value = 0;
    }

    // ---------------- versioned store: UPDATE ... WHERE version = ? ----------------
    static class VersionedStore {
        private int value = 0;
        private int version = 1;

        synchronized Row read() {
            return new Row(value, version);
        }

        // returns true if "1 row was updated"
        synchronized boolean update(int expectedVersion, int newValue) {
            if (version != expectedVersion) {
                return false;                     // WHERE version = ? matched nothing
            }
            value = newValue;
            version++;
            return true;
        }
    }

    static void sleepTiny() {
        try {
            Thread.sleep(0, 200_000);             // widen the race window so the demo is reliable
        } catch (InterruptedException ignored) {
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("A) Two users edit the same account (balance 100)");
        VersionedStore account = new VersionedStore();
        account.update(1, 100);                                     // now value=100, version=2

        Row aliceRead = account.read();
        Row bobRead = account.read();
        System.out.println("   Alice reads " + aliceRead + ", Bob reads " + bobRead);

        boolean aliceOk = account.update(aliceRead.version(), aliceRead.value() + 50);   // deposit 50
        System.out.println("   Alice saves 150 -> " + (aliceOk ? "OK" : "CONFLICT"));

        boolean bobOk = account.update(bobRead.version(), bobRead.value() - 30);         // withdraw 30
        System.out.println("   Bob saves 70    -> " + (bobOk ? "OK" : "CONFLICT (someone changed it, version moved on)"));
        if (!bobOk) {
            Row fresh = account.read();
            account.update(fresh.version(), fresh.value() - 30);
            System.out.println("   Bob reloads " + fresh + ", reapplies his withdrawal -> " + account.read());
            System.out.println("   Correct final balance 120. Without versions Bob's save would have wiped Alice's deposit (70).");
        }

        System.out.println("\nB) Stress test: 4 threads each add 1, two thousand times (expected total 8000)");
        int threads = 4, perThread = 2000;

        NaiveStore naive = new NaiveStore();
        Thread[] ts = new Thread[threads];
        for (int i = 0; i < threads; i++) {
            ts[i] = new Thread(() -> {
                for (int j = 0; j < perThread; j++) {
                    int v = naive.value;               // read
                    sleepTiny();
                    naive.value = v + 1;               // write (blindly)
                }
            });
            ts[i].start();
        }
        for (Thread t : ts) t.join();
        System.out.println("   no version check : " + naive.value + "  <- lost updates!");

        VersionedStore versioned = new VersionedStore();
        int[] retries = {0};
        for (int i = 0; i < threads; i++) {
            ts[i] = new Thread(() -> {
                for (int j = 0; j < perThread; j++) {
                    while (true) {
                        Row r = versioned.read();
                        sleepTiny();
                        if (versioned.update(r.version(), r.value() + 1)) {
                            break;
                        }
                        synchronized (retries) {
                            retries[0]++;              // conflict detected: loop, reload, retry
                        }
                    }
                }
            });
            ts[i].start();
        }
        for (Thread t : ts) t.join();
        System.out.println("   optimistic locking: " + versioned.read().value() + "  <- exact, after " + retries[0] + " conflict retries");

        System.out.println("\nUse optimistic locking when conflicts are rare (most web apps). Use pessimistic locks (SELECT ... FOR UPDATE) "
                + "only for hot rows where retries would be constant.");
    }
}
