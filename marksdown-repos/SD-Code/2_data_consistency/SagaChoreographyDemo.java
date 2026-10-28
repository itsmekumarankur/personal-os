import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

/**
 * ================================================================
 * SAGA CHOREOGRAPHY - THE BIG IDEA
 * ================================================================

 When one business action spans several services, each with its own database, there is no single transaction to roll back. 
 - Instead, each service does its own local step and announces an event.
 - If something fails later, a compensating action undoes the earlier step, here a refund.

 
 *   Problem: Order + Payment + Inventory = 3 services, 3 databases
 *            -> one DB transaction cannot cover all of them
 *
 *   Solution: each service does its OWN small step, then shouts
 *             an event. Others listen and react. No boss.
 *
 *                    +---------------------+
 *                    |      EVENT BUS      |   (stands in for Kafka/RabbitMQ)
 *                    +---------------------+
 *                     ^   |      ^   |     ^   |
 *                     |   v      |   v     |   v
 *               +---------+ +----------+ +-----------+
 *               |  ORDER  | | PAYMENT  | | INVENTORY |
 *               | service | | service  | |  service  |
 *               +---------+ +----------+ +-----------+
 *
 * ================================================================
 * THE EVENT CHAIN
 * ================================================================
 *
 *   place order
 *       |
 *       v
 *   OrderCreated
 *       |
 *       v
 *   [PAYMENT hears it]
 *       |
 *       +-- not enough money --> PaymentFailed
 *       |                              |
 *       |                              v
 *       |                      [ORDER] CANCELLED
 *       |
 *       +-- money taken -------> PaymentCompleted
 *                                      |
 *                                      v
 *                              [INVENTORY hears it]
 *                                      |
 *                      +---------------+----------------+
 *                      |                                |
 *                 stock available                  out of stock
 *                      |                                |
 *                      v                                v
 *               InventoryReserved                InventoryFailed
 *                      |                                |
 *                      v                                v
 *              [ORDER] CONFIRMED              [PAYMENT] REFUND  <- compensating action
 *                                                       |
 *                                                       v
 *                                                PaymentRefunded
 *                                                       |
 *                                                       v
 *                                               [ORDER] CANCELLED
 *
 * ================================================================
 * THE 3 SCENARIOS IN main()   (wallet starts at 1000)
 * ================================================================
 *
 *  1) HAPPY PATH       book, 300
 *     Order -> Payment OK (wallet 700) -> Stock OK (book 5->4)
 *     => CONFIRMED
 *
 *  2) PAYMENT FAILS    book, 5000
 *     Order -> Payment says "insufficient funds"
 *     => CANCELLED (nothing to undo, nothing was taken)
 *
 *  3) STOCK FAILS      gold-coin, 200
 *     Order -> Payment OK (wallet 500) -> Stock = 0, FAIL
 *     -> Payment REFUNDS (wallet back to 700)
 *     => CANCELLED (money returned)
 *
 *  FINAL STATE:  order-1 CONFIRMED | order-2 CANCELLED | order-3 CANCELLED
 *                wallet = 700      | book stock = 4
 *
 * ================================================================
 * KEY TAKEAWAY
 * ================================================================
 *
 *  Saga            -> chain of local transactions, not one big one
 *  Choreography    -> services react to events, no central boss
 *  Compensation    -> undo by doing the opposite (refund), not rollback
 *  Loose coupling  -> services only know events, not each other
 *  Downside        -> the flow is spread out, harder to trace as it grows
 *                     (Orchestration fixes this with one coordinator)
 *
 * ================================================================
 */
public class SagaChoreographyDemo {
    interface Event {}
    record OrderCreated(String orderId, String item, int amount) implements Event { }
    record PaymentCompleted(String orderId, String item, int amount) implements Event { }
    record PaymentFailed(String orderId, String reason) implements Event {}
    record InventoryReserved(String orderId) implements Event {}
    record InventoryFailed(String orderId, String reason, int amount) implements Event {}
    record PaymentRefunded(String orderId) implements Event {}
    static class EventBus {
        private final Map<Class<?>, List<Consumer<Object>>> handlers = new HashMap<>();

        <T extends Event> void subscribe(Class<T> type, Consumer<T> handler) {
            handlers.computeIfAbsent(type, k -> new ArrayList<>()).add(e -> handler.accept(type.cast(e)));
        }

        void publish(Event event) {
            System.out.println("      ~ event published: " + event);
            for (Consumer<Object> h : handlers.getOrDefault(event.getClass(), List.of())) {
                h.accept(event);
            }
        }
    }

    // ---------------------------------------------------------------- Order service
    static class OrderService {
        final Map<String, String> status = new LinkedHashMap<>();
        private final EventBus bus;

        OrderService(EventBus bus) {
            this.bus = bus;
            bus.subscribe(PaymentFailed.class, e -> {
                status.put(e.orderId(), "CANCELLED (payment failed)");
            });
            bus.subscribe(InventoryReserved.class, e -> {
                status.put(e.orderId(), "CONFIRMED");
            });
            bus.subscribe(PaymentRefunded.class, e -> {
                status.put(e.orderId(), "CANCELLED (out of stock, payment refunded)");
            });
        }

        void placeOrder(String orderId, String item, int amount) {
            status.put(orderId, "PENDING");
            bus.publish(new OrderCreated(orderId, item, amount));
        }
    }

    // ---------------------------------------------------------------- Payment service
    static class PaymentService {
        int wallet = 1000;

        PaymentService(EventBus bus) {
            bus.subscribe(OrderCreated.class, e -> {
                if (e.amount() > wallet) {
                    bus.publish(new PaymentFailed(e.orderId(), "insufficient funds"));
                } else {
                    wallet -= e.amount();
                    bus.publish(new PaymentCompleted(e.orderId(), e.item(), e.amount()));
                }
            });
            bus.subscribe(InventoryFailed.class, e -> {          // COMPENSATING ACTION
                wallet += e.amount();
                bus.publish(new PaymentRefunded(e.orderId()));
            });
        }
    }

    // ---------------------------------------------------------------- Inventory service
    static class InventoryService {
        final Map<String, Integer> stock = new HashMap<>(Map.of("book", 5, "gold-coin", 0));

        InventoryService(EventBus bus) {
            bus.subscribe(PaymentCompleted.class, e -> {
                int left = stock.getOrDefault(e.item(), 0);
                if (left <= 0) {
                    bus.publish(new InventoryFailed(e.orderId(), "out of stock", e.amount()));
                } else {
                    stock.put(e.item(), left - 1);
                    bus.publish(new InventoryReserved(e.orderId()));
                }
            });
        }
    }

    public static void main(String[] args) {
        EventBus bus = new EventBus();
        OrderService orders = new OrderService(bus);
        PaymentService payments = new PaymentService(bus);
        InventoryService inventory = new InventoryService(bus);

        System.out.println("Scenario 1: everything works (book, 300)");
        orders.placeOrder("order-1", "book", 300);

        System.out.println("\nScenario 2: payment fails (book, 5000, wallet only has 700)");
        orders.placeOrder("order-2", "book", 5000);

        System.out.println("\nScenario 3: payment succeeds but item is out of stock (gold-coin, 200) -> refund");
        orders.placeOrder("order-3", "gold-coin", 200);

        System.out.println("\nFinal state:");
        orders.status.forEach((id, s) -> System.out.println("  " + id + " -> " + s));
        System.out.println("  wallet = " + payments.wallet + " (1000 - 300 for order-1; order-3 was refunded)");
        System.out.println("  book stock = " + inventory.stock.get("book"));
    }
}
