import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * 30. AGGREGATOR / COMPOSITE - one endpoint that combines data from several services
 *
 * A "customer profile" page needs account details (service 1), recent transactions (service 2)
 * and offers (service 3). The aggregator calls them and builds ONE response.
 *
 * Key design choices shown:
 *   - call independent services IN PARALLEL (total time ~ the slowest, not the sum)
 *   - separate CRITICAL data (no account = no page) from OPTIONAL data (no offers = page still works)
 *   - give every call a time limit and a fallback for the optional parts
 *
 * Because there are no cross-service JOINs in a database-per-service world, this is how
 * "joins" are done: at the API layer.
 *
 * Run: java AggregatorDemo.java
 */
public class AggregatorDemo {

    static boolean accountServiceDown = false;
    static long offersLatency = 500;

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    // ---- three downstream services with different speeds ----
    static String accountService() {
        sleep(300);
        if (accountServiceDown) {
            throw new IllegalStateException("account-service unavailable");
        }
        return "Ankur, balance 1,23,456";
    }

    static List<String> transactionService() {
        sleep(400);
        return List.of("Rent -25000", "Salary +90000");
    }

    static List<String> offerService() {
        sleep(offersLatency);
        return List.of("5% fuel cashback");
    }

    // ---- A) naive sequential aggregator ----
    static String sequential() {
        return accountService() + " | " + transactionService() + " | " + offerService();
    }

    // ---- B) parallel aggregator with critical vs optional parts ----
    static String parallel(ExecutorService pool, long optionalTimeoutMs) {
        CompletableFuture<String> account = CompletableFuture.supplyAsync(AggregatorDemo::accountService, pool);          // CRITICAL
        CompletableFuture<List<String>> txns = CompletableFuture.supplyAsync(AggregatorDemo::transactionService, pool);   // CRITICAL
        CompletableFuture<List<String>> offers = CompletableFuture.supplyAsync(AggregatorDemo::offerService, pool)        // OPTIONAL
                .completeOnTimeout(List.of("(offers unavailable right now)"), optionalTimeoutMs, TimeUnit.MILLISECONDS)
                .exceptionally(ex -> List.of("(offers unavailable right now)"));

        CompletableFuture.allOf(account, txns, offers).join();       // waits for all; throws if a critical one failed
        return account.join() + " | " + txns.join() + " | " + offers.join();
    }

    static void timed(String title, java.util.function.Supplier<String> action) {
        long t0 = System.currentTimeMillis();
        String result;
        try {
            result = action.get();
        } catch (CompletionException e) {
            result = "FAILED FAST -> 502 Bad Gateway (" + e.getCause().getMessage() + ")";
        }
        System.out.printf("%s%n   %4d ms  %s%n%n", title, System.currentTimeMillis() - t0, result);
    }

    public static void main(String[] args) {
        ExecutorService pool = Executors.newCachedThreadPool();

        timed("A) SEQUENTIAL: 300 + 400 + 500 ms add up", AggregatorDemo::sequential);

        timed("B) PARALLEL: total is about the slowest call (500 ms)", () -> parallel(pool, 1000));

        offersLatency = 2000;
        timed("C) PARALLEL, offers service is very slow (2 s). Optional part times out at 300 ms, page still renders",
                () -> parallel(pool, 300));

        accountServiceDown = true;
        timed("D) PARALLEL, CRITICAL account service is down: the aggregator cannot build a meaningful page",
                () -> parallel(pool, 300));

        System.out.println("Production add-ons: circuit breaker per downstream, caching of slow-changing parts, "
                + "and returning partial data with a flag telling the UI which sections are missing.");
        pool.shutdownNow();
    }
}
