import java.util.Random;

/**
        The demo shows three ways to release a new version (v2) safely.

        **A) Blue-Green: two copies, one switch**
        - Blue is the live v1. Green holds the new v2, tested with no real users.
        - Flip the router and all users move to v2 at once.
        - Problem found? Flip back and everyone is on v1 again. Rollback is one switch.

        **B) Canary with a healthy v2: widen slowly**
        - Send 5% of users to v2 and check the error rate (0.5%, well under the 5% limit).
        - Healthy, so go to 25%, then 50%, then 100%.
        - v2 is promoted safely.

        **C) Canary with a buggy v2: stop early**
        - Send 5% of users to v2 and the error rate is about 30%, above the 5% limit.
        - Automatic rollback to 0%.
        - Only about 50 of 1000 users saw the bug. A big-bang deploy would have hit all 1000.

        **Closing note**
        - Old and new versions run together, so database changes must be backward-compatible.
        - Good monitoring is what tells you whether to promote or roll back.

        **One-line summary:**
        - Blue-green is fast switch, fast undo, but everyone is exposed at once.
        - Canary is slow and careful, and a bug only hurts a few users.
 */
public class BlueGreenCanaryDemo {

    // =============================================================== Blue-green
    static class BlueGreenRouter {
        String live = "blue";

        String route() {
            return live.equals("blue") ? "v1 (blue)" : "v2 (green)";
        }

        void flip() {
            live = live.equals("blue") ? "green" : "blue";
        }
    }

    static void blueGreen() {
        System.out.println("A) BLUE-GREEN");
        BlueGreenRouter router = new BlueGreenRouter();
        System.out.println("   v2 is deployed to GREEN and smoke-tested internally. Users still on: " + router.route());
        router.flip();
        System.out.println("   router flipped. All users now on: " + router.route());
        router.flip();
        System.out.println("   problem found! flip back. All users on: " + router.route() + "   (rollback took one switch)\n");
    }

    // =============================================================== Canary
    static class CanaryResult {
        int canaryUsers, stableUsers, canaryRequests, canaryErrors;
    }

    static CanaryResult runStep(int canaryPercent, double canaryErrorRate, Random random) {
        CanaryResult r = new CanaryResult();
        for (int user = 0; user < 1000; user++) {
            int bucket = Math.floorMod(("user-" + user).hashCode(), 100);     // sticky: a user stays on one version
            boolean toCanary = bucket < canaryPercent;
            if (toCanary) {
                r.canaryUsers++;
            } else {
                r.stableUsers++;
            }
            for (int req = 0; req < 5; req++) {                              // each user makes 5 requests
                if (toCanary) {
                    r.canaryRequests++;
                    if (random.nextDouble() < canaryErrorRate) {
                        r.canaryErrors++;
                    }
                }
            }
        }
        return r;
    }

    static void canary(String title, double v2ErrorRate) {
        System.out.println(title);
        final double ROLLBACK_THRESHOLD = 0.05;                              // roll back above 5% errors
        Random random = new Random(7);                                       // fixed seed: repeatable output
        int[] steps = {5, 25, 50, 100};
        for (int percent : steps) {
            CanaryResult r = runStep(percent, v2ErrorRate, random);
            double rate = r.canaryRequests == 0 ? 0 : r.canaryErrors / (double) r.canaryRequests;
            System.out.printf("   step %3d%%: %4d users on v2, %4d requests, %3d errors (%.1f%% error rate)",
                    percent, r.canaryUsers, r.canaryRequests, r.canaryErrors, rate * 100);
            if (rate > ROLLBACK_THRESHOLD) {
                System.out.printf("  -> ABOVE %.0f%% threshold: AUTO-ROLLBACK to 0%%%n", ROLLBACK_THRESHOLD * 100);
                System.out.println("   Only " + r.canaryUsers + " of 1000 users (" + r.canaryUsers / 10.0 + "%) ever saw the bug. "
                        + "A big-bang deploy would have hit all 1000.\n");
                return;
            }
            System.out.println("  -> healthy, widen the rollout");
        }
        System.out.println("   v2 promoted to 100%. Canary finished safely.\n");
    }

    public static void main(String[] args) {
        blueGreen();
        canary("B) CANARY with a HEALTHY v2 (0.5% errors)", 0.005);
        canary("C) CANARY with a BUGGY v2 (30% errors)", 0.30);

        System.out.println("Both strategies need: backward-compatible DB changes (expand, migrate, contract), "
                + "\nbecause old and new versions run at the same time, and good monitoring to decide promote or rollback.");

        /**
        *
        *                             START
        *                               |
        *                               v
        *                 +---------------------------+
        *                 | main()                    |
        *                 +-------------+-------------+
        *                               |
        *             +-----------------+-----------------+
        *             |                 |                 |
        *             v                 v                 v
        *       A) BLUE-GREEN      B) CANARY          C) CANARY
        *                          (HEALTHY v2)       (BUGGY v2)
        *                          0.5% errors        30% errors
        *             |                 |                 |
        *             v                 v                 v
        *   BlueGreenRouter        canary(0.005)      canary(0.30)
        *   live = "blue"               |                 |
        *             |                 v                 v
        *             v            steps: 5 -> 25     steps: 5 -> 25
        *   v2 deployed to GREEN        -> 50 -> 100       -> 50 -> 100
        *   smoke-tested, no users      |                 |
        *   Users still on v1 (blue)    |                 |
        *             |                 |                 |
        *             v                 v                 v
        *   router.flip()          Step 5%            Step 5%
        *   live = "green"         error 0.5% < 5%    error ~30% > 5%
        *   ALL users -> v2             |                 |
        *             |                 v                 v
        *             v            healthy, widen     ABOVE threshold
        *   problem found!              |             AUTO-ROLLBACK to 0%
        *             |                 v                 |
        *             v            Step 25%                v
        *   router.flip()          healthy, widen     Only ~50 of 1000
        *   live = "blue"               |             users (~5%) saw bug
        *   ALL users -> v1             v                 |
        *   (rollback = 1 switch)  Step 50%               v
        *             |            healthy, widen     Big-bang would have
        *             |                 |             hit all 1000
        *             |                 v                 |
        *             |            Step 100%              |
        *             |            healthy                |
        *             |                 |                 |
        *             |                 v                 |
        *             |            v2 PROMOTED            |
        *             |            to 100%                |
        *             |                 |                 |
        *             +-----------------+-----------------+
        *                               |
        *                               v
        *                 Print closing note:
        *                 backward-compatible DB changes
        *                 + good monitoring
        *                               |
        *                               v
        *                              END

        * ================================================================
        * 
        */
    }
}
