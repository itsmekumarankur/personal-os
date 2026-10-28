import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;

/**
 * 22. CQRS - Command Query Responsibility Segregation
 *
 * Use DIFFERENT models for writing and reading.
 *
 *   COMMAND side (write): careful, validated, normalised data, protects business rules.
 *   QUERY side (read):    pre-computed, flat, shaped exactly like the screen needs (fast, no joins).
 *   A PROJECTOR listens to events from the write side and keeps the read model up to date.
 *
 * Picture: a restaurant. Taking an order (command) is a careful process; the menu board and
 * the "today's totals" sheet (queries) are separate, pre-made, easy to read.
 *
 * Price you pay: the read model is updated a moment LATER (eventual consistency, next demo).
 *
 * Run: java CqrsDemo.java
 */
public class CqrsDemo {

    record Item(String sku, int qty, int unitPrice) {
    }

    record OrderPlaced(String orderId, String customerId, List<Item> items) {
    }

    // ---------------------------------------------------------------- WRITE MODEL
    static class OrderCommandService {
        private final Map<String, List<Item>> orderLines = new HashMap<>();          // normalised storage
        private final Map<String, String> orderCustomer = new HashMap<>();
        private final BlockingQueue<OrderPlaced> events;

        OrderCommandService(BlockingQueue<OrderPlaced> events) {
            this.events = events;
        }

        void placeOrder(String orderId, String customerId, List<Item> items) {
            if (items.isEmpty() || items.stream().anyMatch(i -> i.qty() <= 0)) {     // business rules live here
                throw new IllegalArgumentException("order needs at least one item with qty > 0");
            }
            orderLines.put(orderId, items);
            orderCustomer.put(orderId, customerId);
            events.add(new OrderPlaced(orderId, customerId, items));                // tell the world (outbox in real life)
        }
    }

    // ---------------------------------------------------------------- READ MODELS
    record OrderSummary(String orderId, String customerName, int itemCount, int total) {
    }

    static class OrderQueryService {
        final Map<String, OrderSummary> summaryByOrder = new ConcurrentHashMap<>();   // view 1: order detail screen
        final Map<String, Integer> totalByCustomer = new ConcurrentHashMap<>();       // view 2: "top customers" report

        String getSummary(String orderId) {
            OrderSummary s = summaryByOrder.get(orderId);
            return s == null ? "not found (yet)" : s.toString();
        }
    }

    // ---------------------------------------------------------------- PROJECTOR
    static Thread startProjector(BlockingQueue<OrderPlaced> events, OrderQueryService query,
                                 Map<String, String> customerNames) {
        Thread t = new Thread(() -> {
            try {
                while (true) {
                    OrderPlaced e = events.take();
                    Thread.sleep(300);                                               // projection lag (async processing)
                    int total = e.items().stream().mapToInt(i -> i.qty() * i.unitPrice()).sum();
                    int count = e.items().stream().mapToInt(Item::qty).sum();
                    String name = customerNames.getOrDefault(e.customerId(), "?");
                    query.summaryByOrder.put(e.orderId(), new OrderSummary(e.orderId(), name, count, total));
                    query.totalByCustomer.merge(name, total, Integer::sum);
                }
            } catch (InterruptedException ignored) {
            }
        });
        t.setDaemon(true);
        t.start();
        return t;
    }

    public static void main(String[] args) throws Exception {
        BlockingQueue<OrderPlaced> events = new LinkedBlockingQueue<>();
        OrderCommandService commands = new OrderCommandService(events);
        OrderQueryService queries = new OrderQueryService();
        startProjector(events, queries, Map.of("c1", "Ankur", "c2", "Meera"));

        System.out.println("1) COMMAND: place an order (writes normalised data + emits an event)");
        commands.placeOrder("o-1", "c1", List.of(new Item("book", 2, 300), new Item("pen", 5, 20)));
        commands.placeOrder("o-2", "c2", List.of(new Item("laptop", 1, 50_000)));
        commands.placeOrder("o-3", "c1", List.of(new Item("bag", 1, 800)));

        System.out.println("\n2) QUERY immediately: the read model has not caught up yet");
        System.out.println("   o-1 -> " + queries.getSummary("o-1"));

        System.out.println("\n3) ... 1.2 seconds later, the projector has processed the events ...");
        Thread.sleep(1200);
        System.out.println("   o-1 -> " + queries.getSummary("o-1"));
        System.out.println("   o-2 -> " + queries.getSummary("o-2"));
        System.out.println("   spend per customer (a second read model, no JOIN needed): " + new java.util.TreeMap<>(queries.totalByCustomer));

        System.out.println("\n4) Invalid command is rejected on the write side only");
        try {
            commands.placeOrder("o-4", "c1", new ArrayList<>());
        } catch (IllegalArgumentException e) {
            System.out.println("   rejected: " + e.getMessage());
        }

        System.out.println("\nWhy: reads and writes scale independently, read models can live in a different store (Elasticsearch, Redis),"
                + "\nand each query gets a model shaped exactly for it. Use it where the read/write needs truly differ, not everywhere.");
    }
}
