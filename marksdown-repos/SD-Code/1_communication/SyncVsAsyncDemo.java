import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 2. SYNCHRONOUS vs ASYNCHRONOUS COMMUNICATION
 *
 * Synchronous (phone call): you call, you WAIT on the line until the answer comes.
 *   - simple, immediate answer
 *   - the caller is blocked, and if anything in the chain is down, the caller fails too
 *
 * Asynchronous (WhatsApp / post box): you drop a message and move on. Someone picks it up later.
 *   - caller gets a quick "received", no waiting
 *   - receiver can be slow or temporarily down, the message waits (and can be retried)
 *   - result is not immediate (you must notify or let the client poll)
 *
 * Run: java SyncVsAsyncDemo.java
 */
public class SyncVsAsyncDemo {

    static long t0;

    static void log(String msg) {
        System.out.printf("  [%5d ms] %s%n", System.currentTimeMillis() - t0, msg);
    }

    static void work(String what, long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        log(what);
    }

    // ------------------------------------------------------------------ SYNC
    static String placeOrderSync(boolean notificationServiceDown) {
        work("inventory reserved", 300);
        work("payment charged", 300);
        if (notificationServiceDown) {
            work("notification service FAILED", 300);
            throw new RuntimeException("notification-service unavailable");   // whole order request fails
        }
        work("notification sent", 300);
        return "200 OK order confirmed";
    }

    // ------------------------------------------------------------------ ASYNC
    static final BlockingQueue<String> QUEUE = new LinkedBlockingQueue<>();   // stands in for Kafka/RabbitMQ
    static final AtomicInteger notificationFailuresLeft = new AtomicInteger(2);

    static String placeOrderAsync(String orderId) {
        QUEUE.add(orderId);                          // just drop the message
        return "202 Accepted (we are processing your order)";
    }

    static Thread startWorker() {
        Thread worker = new Thread(() -> {
            try {
                String orderId = QUEUE.take();
                log("worker picked up " + orderId);
                work("inventory reserved", 300);
                work("payment charged", 300);
                while (true) {                       // retry until notification works
                    if (notificationFailuresLeft.getAndDecrement() > 0) {
                        work("notification service down, will retry in 500 ms", 100);
                        Thread.sleep(500);
                    } else {
                        work("notification sent, order " + orderId + " fully done", 300);
                        break;
                    }
                }
            } catch (InterruptedException ignored) {
            }
        });
        worker.start();
        return worker;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("A) SYNC, everything healthy: the customer waits for all three steps");
        t0 = System.currentTimeMillis();
        String r = placeOrderSync(false);
        log("customer receives: " + r);

        System.out.println("\nB) SYNC, notification service down: customer sees an ERROR, but money was already taken!");
        t0 = System.currentTimeMillis();
        try {
            placeOrderSync(true);
        } catch (RuntimeException e) {
            log("customer receives: 500 Error (" + e.getMessage() + ")  <- payment already charged");
        }

        System.out.println("\nC) ASYNC, same notification outage: customer is answered at once, retries happen in background");
        t0 = System.currentTimeMillis();
        Thread worker = startWorker();
        String answer = placeOrderAsync("order-77");
        log("customer receives: " + answer);
        worker.join();

        System.out.println("\nRule of thumb: use SYNC when the caller needs the answer now (get a price, check a balance);"
                + "\nuse ASYNC for work that can finish later or must survive downstream outages (notifications, settlement, emails).");
    }
}
