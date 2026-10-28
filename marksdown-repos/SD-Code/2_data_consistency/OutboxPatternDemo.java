import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 Outbox Pattern:
- A service must save data in its database and tell a message broker about it. 
- These are two systems, so no single transaction covers both, and a crash in between leaves the order saved but nobody informed. 
- The fix is to save the event in an outbox table in the same database transaction as the order.
  
A separate relay then publishes it later and retries until it works.
 * ================================================================
 * OUTBOX PATTERN - THE BIG IDEA
 * ================================================================
 *
 *   Problem: DUAL WRITE
 *   Service must (1) save the order in DB
 *                (2) publish "OrderPlaced" to the broker
 *   Two systems -> no single transaction covers both.
 *
 *   WITHOUT OUTBOX
 *
 *      save order in DB  ---> OK
 *            |
 *            x  CRASH here
 *            |
 *      publish event     ---> never happens
 *
 *      Result: order exists, inventory never learns about it
 *              (INCONSISTENT)
 *
 *   WITH OUTBOX
 *
 *      +-------------- ONE DB TRANSACTION --------------+
 *      |  orders table  : insert order-3                |
 *      |  outbox table  : insert evt-3 (sent = false)   |
 *      +------------------------------------------------+
 *                     both or neither
 *                          |
 *                          v
 *      +--------------------------------+
 *      |  RELAY (separate process)      |
 *      |  read unsent outbox rows       |
 *      |  publish to broker             |
 *      |  mark row sent = true          |
 *      +---------------+----------------+
 *                      |
 *                      v
 *                   BROKER ---> CONSUMER (inventory)
 *
 * ================================================================
 * THE SCENARIOS IN main()
 * ================================================================
 *
 *  A) NO OUTBOX
 *     order saved -> crash -> no event
 *     => DB has order-1, broker has nothing  (WRONG)
 *
 *  B) WITH OUTBOX
 *
 *   1) Crash INSIDE the transaction
 *      order-2 + outbox row both ROLL BACK
 *      => orders=[], outbox=0  (consistent, neither)
 *
 *   2) Successful transaction
 *      order-3 + evt-3 saved together
 *      => orders=[order-3], outbox=1 (unsent)
 *
 *   3) Broker is DOWN when relay runs
 *      publish fails -> row stays unsent
 *      => nothing lost, event waits in the outbox
 *
 *   4) Broker back, relay CRASHES after publishing
 *      message published, but NOT marked sent
 *      => row still unsent
 *
 *   5) Relay restarts, publishes the unsent row AGAIN
 *      => broker now holds evt-3 TWICE (duplicate)
 *
 *   6) Consumer receives both copies
 *      first  evt-3 -> processed
 *      second evt-3 -> "duplicate ignored" (seen before)
 *      => exactly ONE inventory reservation
 *
 * ================================================================
 * WHY DUPLICATES HAPPEN (AT-LEAST-ONCE)
 * ================================================================
 *
 *   relay:   publish ---> [crash] ---> mark sent
 *                            ^
 *                  published but not marked,
 *                  so the next run publishes again
 *
 *   Better to send twice than to lose an event.
 *   So the CONSUMER must be idempotent:
 *
 *      seen = { }
 *      receive evt-3 -> not in seen -> process, add to seen
 *      receive evt-3 -> in seen     -> ignore
 *
 * ================================================================
 * KEY TAKEAWAY
 * ================================================================
 *
 *  Dual write      -> DB + broker cannot share one transaction
 *  Outbox table    -> event saved in the SAME transaction as the data
 *  Relay           -> separate process publishes unsent rows, retries
 *  Delivery        -> at-least-once (can be duplicated, never lost)
 *  Consumer        -> de-duplicate by event id (idempotent)
 *  Real relays     -> polling job, or Debezium change-data-capture
 *
 * ================================================================
 
 */
public class OutboxPatternDemo {

    static class OutboxRow {
        final String eventId;
        final String payload;
        boolean sent;

        OutboxRow(String eventId, String payload, boolean sent) {
            this.eventId = eventId;
            this.payload = payload;
            this.sent = sent;
        }
    }

    /** A pretend database with an all-or-nothing transaction. */
    static class Database {
        List<String> orders = new ArrayList<>();
        List<OutboxRow> outbox = new ArrayList<>();

        void transaction(Runnable work) {
            List<String> ordersBackup = new ArrayList<>(orders);
            List<OutboxRow> outboxBackup = new ArrayList<>();
            for (OutboxRow r : outbox) {
                outboxBackup.add(new OutboxRow(r.eventId, r.payload, r.sent));
            }
            try {
                work.run();
            } catch (RuntimeException e) {                    // ROLLBACK: restore both tables
                orders = ordersBackup;
                outbox = outboxBackup;
                throw e;
            }
        }
    }

    static class Broker {
        final List<String> messages = new ArrayList<>();
        boolean down = false;

        void publish(OutboxRow row) {
            if (down) {
                throw new IllegalStateException("broker unavailable");
            }
            messages.add(row.eventId + ":" + row.payload);
        }
    }

    // ------------------------------------------------------------ relay
    static boolean crashAfterPublish = false;

    static void relay(Database db, Broker broker) {
        for (OutboxRow row : db.outbox) {
            if (row.sent) {
                continue;
            }
            try {
                broker.publish(row);
                if (crashAfterPublish) {                                  // process dies BEFORE marking sent
                    crashAfterPublish = false;
                    throw new IllegalStateException("relay crashed after publishing");
                }
                row.sent = true;
            } catch (IllegalStateException e) {
                System.out.println("    relay problem: " + e.getMessage() + " (row stays unsent, will retry)");
                return;
            }
        }
    }

    // ------------------------------------------------------------ idempotent consumer
    static class InventoryConsumer {
        private final Set<String> seen = new HashSet<>();
        int reservations = 0;

        void handle(String message) {
            String eventId = message.substring(0, message.indexOf(':'));
            if (!seen.add(eventId)) {
                System.out.println("    consumer: duplicate " + eventId + " ignored");
                return;
            }
            reservations++;
            System.out.println("    consumer: processed " + message);
        }
    }

    public static void main(String[] args) {
        System.out.println("A) WITHOUT outbox (dual write): save, then publish, crash in between");
        Database db1 = new Database();
        Broker broker1 = new Broker();
        db1.orders.add("order-1");                                         // committed
        System.out.println("   order saved. *** service crashes before publishing ***");
        System.out.println("   orders in DB: " + db1.orders + ", events published: " + broker1.messages
                + "   <- INCONSISTENT, inventory never learns about order-1");

        System.out.println("\nB) WITH outbox");
        Database db = new Database();
        Broker broker = new Broker();
        InventoryConsumer consumer = new InventoryConsumer();

        System.out.println("  1) crash INSIDE the transaction: both writes roll back together");
        try {
            db.transaction(() -> {
                db.orders.add("order-2");
                db.outbox.add(new OutboxRow("evt-2", "OrderPlaced order-2", false));
                throw new IllegalStateException("crash before commit");
            });
        } catch (IllegalStateException e) {
            System.out.println("    orders=" + db.orders + ", outbox rows=" + db.outbox.size() + "   <- consistent (neither)");
        }

        System.out.println("  2) successful transaction: order + outbox row saved atomically");
        db.transaction(() -> {
            db.orders.add("order-3");
            db.outbox.add(new OutboxRow("evt-3", "OrderPlaced order-3", false));
        });
        System.out.println("    orders=" + db.orders + ", outbox rows=" + db.outbox.size() + " (unsent)");

        System.out.println("  3) broker is DOWN when the relay runs: nothing lost, event waits in the outbox");
        broker.down = true;
        relay(db, broker);
        System.out.println("    published so far: " + broker.messages);

        System.out.println("  4) broker back, but the relay crashes right after publishing (before marking sent)");
        broker.down = false;
        crashAfterPublish = true;
        relay(db, broker);
        System.out.println("  5) relay restarts and publishes the still-unsent row again (at-least-once => duplicate)");
        relay(db, broker);
        System.out.println("    broker now holds: " + broker.messages);

        System.out.println("  6) consumer receives both copies, but de-duplicates by event id");
        broker.messages.forEach(consumer::handle);
        System.out.println("    inventory reservations made: " + consumer.reservations + " (exactly one)");
    }
}
