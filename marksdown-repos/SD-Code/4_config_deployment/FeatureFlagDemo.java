import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 32. FEATURE FLAGS - change behaviour WITHOUT redeploying
 *
 * Deploy (put code in production) and Release (let users use it) become two separate decisions.
 *   - ship new code switched OFF, turn it on for testers, then 1%, 10%, 50%, 100% of users
 *   - something wrong? flip the KILL SWITCH. No rollback, no new deploy, effective in seconds
 *
 * Details that matter:
 *   - percentage rollout must be STICKY: the same user must always get the same answer
 *     (hash of flag + userId, not random per request)
 *   - rollout should be MONOTONIC: users who were on at 10% stay on at 50%
 *   - unknown flag => OFF (safe default). Remove flags once fully rolled out (flag debt is real).
 * Real tools: LaunchDarkly, Unleash, Flagsmith, Togglz, or Spring Cloud Config + @RefreshScope.
 *
 * Run: java FeatureFlagDemo.java
 */
public class FeatureFlagDemo {

    static class Flag {
        volatile boolean enabled = true;                    // master / kill switch
        volatile int rolloutPercent = 0;                    // 0..100
        final Set<String> allowList = ConcurrentHashMap.newKeySet();   // always on for these users
    }

    static class FlagService {
        private final Map<String, Flag> flags = new ConcurrentHashMap<>();

        Flag define(String name) {
            return flags.computeIfAbsent(name, k -> new Flag());
        }

        boolean isEnabled(String flagName, String userId) {
            Flag f = flags.get(flagName);
            if (f == null || !f.enabled) {
                return false;                                // unknown flag or killed => OFF
            }
            if (f.allowList.contains(userId)) {
                return true;                                 // testers and internal users
            }
            int bucket = Math.floorMod((flagName + ":" + userId).hashCode(), 100);   // stable bucket 0..99 per user+flag
            return bucket < f.rolloutPercent;
        }

        void kill(String flagName) {
            flags.get(flagName).enabled = false;
        }
    }

    static Set<String> usersWithFeature(FlagService service, String flag, int users) {
        Set<String> on = new HashSet<>();
        for (int i = 0; i < users; i++) {
            if (service.isEnabled(flag, "user-" + i)) {
                on.add("user-" + i);
            }
        }
        return on;
    }

    public static void main(String[] args) throws Exception {
        FlagService service = new FlagService();
        Flag newCheckout = service.define("new-checkout");

        System.out.println("1) Code is deployed, flag at 0%, but QA is on the allow-list");
        newCheckout.allowList.add("qa-tester");
        System.out.println("   qa-tester sees new checkout: " + service.isEnabled("new-checkout", "qa-tester"));
        System.out.println("   user-1    sees new checkout: " + service.isEnabled("new-checkout", "user-1"));

        System.out.println("\n2) Roll out to 10% of 1000 users");
        newCheckout.rolloutPercent = 10;
        Set<String> at10 = usersWithFeature(service, "new-checkout", 1000);
        System.out.println("   users with the feature: " + at10.size() + " of 1000");
        String sample = at10.iterator().next();
        System.out.println("   sticky: " + sample + " gets the same answer every time -> "
                + service.isEnabled("new-checkout", sample) + ", " + service.isEnabled("new-checkout", sample)
                + ", " + service.isEnabled("new-checkout", sample));

        System.out.println("\n3) Increase to 50%");
        newCheckout.rolloutPercent = 50;
        Set<String> at50 = usersWithFeature(service, "new-checkout", 1000);
        System.out.println("   users with the feature: " + at50.size() + " of 1000");
        System.out.println("   everyone who had it at 10% still has it at 50%: " + at50.containsAll(at10));

        System.out.println("\n4) 100% live. A bug is reported while the app is RUNNING. An operator flips the kill switch:");
        newCheckout.rolloutPercent = 100;
        Thread operator = new Thread(() -> {
            try {
                Thread.sleep(250);
            } catch (InterruptedException ignored) {
            }
            service.kill("new-checkout");
            System.out.println("   >>> operator kills 'new-checkout' (no restart, no deploy)");
        });
        operator.start();
        for (int request = 1; request <= 6; request++) {
            boolean on = service.isEnabled("new-checkout", "user-5");
            System.out.println("   request " + request + " from user-5 -> " + (on ? "NEW checkout" : "old checkout (safe)"));
            Thread.sleep(100);
        }
        operator.join();

        System.out.println("\nHygiene: give flags owners and expiry dates, delete the flag and the old code path after full rollout, "
                + "\nand never nest many flags in the same code path (combinations become untestable).");
    /**
        * ================================================================
        * FEATURE FLAG DEMO - MAIN METHOD EXECUTION FLOW
        The crux of `main()`: **you can change who sees a feature, live, without redeploying.** 

        1. Deployed but hidden (0%).
            - The code is in production, but only `qa-tester` (on the allow-list) sees it. 
            - Everyone else gets the old behaviour.

        2. Release to 10%.
             - About 100 of 1000 users get it. 
             - The same user always gets the same answer, because the bucket comes from a hash of `flag + userId`, not a random number.

        3. Grow to 50%. 
             - The 100 users from 10% are still included. 
             - Raising the percentage never removes anyone, so no user sees the feature appear and disappear.

        4. Bug at 100%
             - so flip the kill switch.** While the app is running, another thread sets `enabled = false`. 
             - The next requests instantly fall back to the old checkout. There is no restart, no rollback and no new deploy.

        **One-line summary:** Deploy the code first, release it gradually, and if something breaks, turn it off in seconds.

        In Step 4 the two threads are there only to simulate a real operator flipping the switch while live traffic keeps flowing.
        * ================================================================
        *
        *                             START
        *                               |
        *                               v
        *                 +---------------------------+
        *                 | main()                    |
        *                 | create FlagService        |
        *                 | define("new-checkout")    |
        *                 +-------------+-------------+
        *                               |
        *                               v
        *        STEP 1: DEPLOYED, FLAG AT 0%
        *        allowList = { qa-tester }
        *                               |
        *               +---------------+---------------+
        *               |                               |
        *               v                               v
        *        qa-tester -> true               user-1 -> false
        *        (on allow-list)                 (0% rollout)
        *                               |
        *                               v
        *        STEP 2: ROLLOUT = 10%  (1000 users)
        *                               |
        *                               v
        *        ~100 users get the feature  (call this set at10)
        *                               |
        *                               v
        *        STICKY CHECK: same user asked 3 times
        *        -> same answer every time (hash, not random)
        *                               |
        *                               v
        *        STEP 3: ROLLOUT = 50%
        *                               |
        *                               v
        *        ~500 users get the feature  (call this set at50)
        *                               |
        *                               v
        *        MONOTONIC CHECK: at50.containsAll(at10) = true
        *        -> nobody loses the feature when % goes up
        *                               |
        *                               v
        *        STEP 4: ROLLOUT = 100%  +  BUG REPORTED
        *                               |
        *               +---------------+---------------+
        *               |                               |
        *               v                               v
        *        MAIN THREAD                     OPERATOR THREAD
        *        6 requests from user-5          sleep 250 ms
        *        one every 100 ms                       |
        *               |                               v
        *               v                        service.kill()
        *        t=0,100,200 ms                  enabled = false
        *        -> NEW checkout                 (no restart, no deploy)
        *               |                               |
        *               v                               |
        *        t=300,400,500 ms                       |
        *        -> old checkout (safe) <---------------+
        *               |
        *               v
        *        operator.join()
        *               |
        *               v
        *        Print hygiene tips
        *               |
        *               v
        *             END
        *

     * 
    */
            }
}


/**
 * ================================================================
 * isEnabled(flagName, userId) - DECISION FLOW
 * ================================================================
 *
 *                  isEnabled(flag, user)
 *                          |
 *                          v
 *              +------------------------+
 *              | flag exists AND        |--- NO ---> return false
 *              | enabled == true ?      |            (unknown or killed = OFF)
 *              +-----------+------------+
 *                          | YES
 *                          v
 *              +------------------------+
 *              | user in allowList ?    |--- YES --> return true
 *              +-----------+------------+            (testers, internal users)
 *                          | NO
 *                          v
 *              bucket = floorMod( hash(flag + ":" + user), 100 )
 *                          |
 *                          v
 *              +------------------------+
 *              | bucket < rolloutPercent|--- YES --> return true
 *              +-----------+------------+
 *                          | NO
 *                          v
 *                     return false
 *
 * Example: user-7 has bucket 23
 *    at 10% -> 23 < 10 ? NO   (off)
 *    at 50% -> 23 < 50 ? YES  (on)   <- stays on at 100% too
 *
 * ================================================================
 * KEY TAKEAWAY
 * ================================================================
 *
 * Deploy vs Release  -> ship code OFF, turn on gradually
 * Sticky             -> hash(flag + userId), never random
 * Monotonic          -> 10% users are still on at 50%
 * Kill switch        -> flip 'enabled', effective in seconds
 * Safe default       -> unknown flag = OFF
 * Hygiene            -> owners, expiry dates, delete after 100%
 *
 * ================================================================
 * 
*/