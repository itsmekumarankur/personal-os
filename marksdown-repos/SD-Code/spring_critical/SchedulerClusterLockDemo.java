import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 7. @Scheduled IN A CLUSTER - why your nightly job runs 3 times
 *
 * @Scheduled works per JVM. Deploy 3 instances and each one fires the job: 3 settlements, 3 emails, 3 refunds.
 *
 * Part A  fixedRate vs fixedDelay (a single scheduler thread, job takes 300 ms, period 200 ms)
 *           fixedRate  = "start every 200 ms measured from the previous START" -> runs back-to-back, never a pause
 *           fixedDelay = "wait 200 ms after the previous run FINISHES"          -> there is breathing room
 * Part B  3 instances, no lock   -> everybody runs
 * Part C  3 instances, DB lock (ShedLock idea: one row per job, "locked_until") -> exactly one runs per tick
 *           lockAtMostFor : if the winner crashes, the lock expires by itself (otherwise the job is stuck forever)
 *           lockAtLeastFor: keeps the lock a little after finishing so instances with clock skew don't run it again
 * Part D  crash scenario
 *
 * Time in B-D is simulated (virtual milliseconds) so the demo is exact and instant.
 * Real Spring version: spring_snippets/SchedulerSnippets.java
 * Run: java SchedulerClusterLockDemo.java
 */
public class SchedulerClusterLockDemo {

    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException ignored) { } }

    // ------------------------------------------------------------------ Part A
    static List<Long> runSchedule(boolean fixedRate) throws Exception {
        List<Long> starts = new ArrayList<>();
        long t0 = System.currentTimeMillis();
        ScheduledExecutorService ses = Executors.newSingleThreadScheduledExecutor();
        Runnable job = () -> { starts.add(Math.round((System.currentTimeMillis() - t0) / 100.0) * 100); sleep(300); };
        if (fixedRate) ses.scheduleAtFixedRate(job, 0, 200, TimeUnit.MILLISECONDS);
        else ses.scheduleWithFixedDelay(job, 0, 200, TimeUnit.MILLISECONDS);
        Thread.sleep(1450);
        ses.shutdownNow();
        return starts;
    }

    // ------------------------------------------------------------------ the lock table (like ShedLock's "shedlock" table)
    record Row(String lockedBy, long lockedUntil) { }

    static class LockTable {
        final Map<String, Row> rows = new HashMap<>();

        /** In SQL: UPDATE shedlock SET locked_until=?, locked_by=? WHERE name=? AND locked_until <= now  (rows updated == 1 means you won) */
        synchronized boolean acquire(String job, String instance, long now, long atMostFor) {
            Row r = rows.get(job);
            if (r != null && now < r.lockedUntil()) return false;
            rows.put(job, new Row(instance, now + atMostFor));
            return true;
        }

        synchronized void release(String job, String instance, long startedAt, long now, long atLeastFor) {
            Row r = rows.get(job);
            if (r != null && r.lockedBy().equals(instance)) rows.put(job, new Row(instance, Math.max(now, startedAt + atLeastFor)));
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("PART A: fixedRate vs fixedDelay (job duration 300 ms, period 200 ms, observed for ~1.4 s)");
        System.out.println("   fixedRate  starts at (ms): " + runSchedule(true) + "   -> next run starts the moment the last one ends");
        System.out.println("   fixedDelay starts at (ms): " + runSchedule(false) + "   -> 200 ms pause after each run");
        System.out.println("   (cron is wall-clock based: '0 0 2 * * *' = every day at 02:00 in the given zone.)");

        String[] instances = {"pod-A", "pod-B", "pod-C"};
        long[] ticks = {0, 1000, 2000};

        System.out.println("\nPART B: 3 instances, NO coordination");
        int runs = 0;
        for (long t : ticks) {
            for (String i : instances) { runs++; System.out.println("   t=" + t + "  " + i + " runs settlement"); }
        }
        System.out.println("   => settlement ran " + runs + " times instead of " + ticks.length + "  (customers charged multiple times!)");

        System.out.println("\nPART C: same cluster with a DB lock (atMostFor=900 ms, atLeastFor=500 ms, job takes 100 ms)");
        LockTable locks = new LockTable();
        runs = 0;
        for (int k = 0; k < ticks.length; k++) {
            long t = ticks[k];
            for (int n = 0; n < instances.length; n++) {
                String inst = instances[(n + k) % instances.length];            // arrival order varies a little per tick
                if (locks.acquire("settlement", inst, t, 900)) {
                    runs++;
                    System.out.println("   t=" + t + "  " + inst + " got the lock -> runs settlement");
                    locks.release("settlement", inst, t, t + 100, 500);
                } else {
                    System.out.println("   t=" + t + "  " + inst + " lock held by " + locks.rows.get("settlement").lockedBy() + " -> skips");
                }
            }
        }
        System.out.println("   => settlement ran " + runs + " times, once per tick");

        System.out.println("\nPART D: the winner CRASHES in the middle of the job (never releases the lock)");
        locks = new LockTable();
        System.out.println("   t=0     pod-A acquired the lock (expires at t=900) and then the pod was killed");
        locks.acquire("settlement", "pod-A", 0, 900);
        System.out.println("   t=300   pod-B tries: " + (locks.acquire("settlement", "pod-B", 300, 900) ? "acquired" : "denied, still locked until t=900"));
        System.out.println("   t=1000  pod-B tries: " + (locks.acquire("settlement", "pod-B", 1000, 900) ? "ACQUIRED - lock expired, job continues" : "denied"));
        System.out.println("   Without lockAtMostFor a crashed holder would block the job forever.");
        System.out.println("\nCaution: the lock stops DUPLICATE STARTS only. If a job is longer than lockAtMostFor two runs can overlap,"
                + "\nso keep jobs idempotent (see resilience_demos) and set lockAtMostFor above the worst-case run time.");
    }
}
