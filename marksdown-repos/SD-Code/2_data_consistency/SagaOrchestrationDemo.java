import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

/**
    * ================================================================
    * SAGA ORCHESTRATION - THE BIG IDEA
    * ================================================================
    *
    *   Choreography : dancers react to each other, no boss
    *   Orchestration: a CONDUCTOR tells each musician when to play
    *
    *                    +---------------------------+
    *                    |       ORCHESTRATOR        |
    *                    |  knows the whole recipe   |
    *                    |  + the UNDO for each step |
    *                    +-------------+-------------+
    *                                  |
    *               +------------------+------------------+
    *               |                  |                  |
    *               v                  v                  v
    *        +-------------+    +-------------+    +-------------+
    *        |   STEP 1    |    |   STEP 2    |    |   STEP 3    |
    *        | reserve     |    | charge      |    | create      |
    *        | stock       |    | payment     |    | shipment    |
    *        +-------------+    +-------------+    +-------------+
    *        undo: stock++      undo: wallet       undo: (nothing)
    *                                 += price
    *
    * ================================================================
    * HOW THE ORCHESTRATOR RUNS A SAGA
    * ================================================================
    *
    *   for each step in order:
    *        |
    *        v
    *   run step.action()
    *        |
    *        +-- SUCCESS --> push step on "completed" stack --> next step
    *        |
    *        +-- FAILURE --> STOP
    *                          |
    *                          v
    *                 pop completed steps one by one
    *                 (LIFO = REVERSE order)
    *                 run each step's compensation
    *                          |
    *                          v
    *                 saga rolled back
    *
    *   completed stack example:   top -> [charge payment]
    *                                     [reserve stock]  <- bottom
    *   undo order:  charge payment first, then reserve stock
    *
    * ================================================================
    * THE 3 RUNS IN main()   (start: stock=5, wallet=1000)
    * ================================================================
    *
    *  RUN 1) HAPPY PATH                     price 300
    *     reserve stock   OK   (stock 5 -> 4)
    *     charge payment  OK   (wallet 1000 -> 700)
    *     create shipment OK
    *     => COMPLETED       state: stock=4, wallet=700
    *
    *  RUN 2) LAST STEP FAILS                price 300, courier DOWN
    *     reserve stock   OK   (stock 4 -> 3)
    *     charge payment  OK   (wallet 700 -> 400)
    *     create shipment FAIL (courier unavailable)
    *        <- undo charge payment   (wallet back to 700)
    *        <- undo reserve stock    (stock back to 4)
    *     => ROLLED BACK     state: stock=4, wallet=700 (as before run 2)
    *
    *  RUN 3) MIDDLE STEP FAILS              price 99,999
    *     reserve stock   OK   (stock 4 -> 3)
    *     charge payment  FAIL (insufficient funds)
    *        <- undo reserve stock    (stock back to 4)
    *     => ROLLED BACK     state: stock=4, wallet=700
    *     (step 3 never ran, so nothing to undo for it)
    *
    * ================================================================
    * CHOREOGRAPHY vs ORCHESTRATION
    * ================================================================
    *
    *   CHOREOGRAPHY                       ORCHESTRATION
    *   ------------                       -------------
    *   services react to events           coordinator gives commands
    *   no central component                one orchestrator
    *   flow spread across services         whole flow in ONE place
    *   + loose coupling                    + easy to read, monitor, change
    *   - hard to trace as it grows         - extra component that knows
    *                                         many services
    *
    * ================================================================
    * KEY TAKEAWAY
    * ================================================================
    *
    *  Saga            -> chain of local steps, each with an undo
    *  Orchestrator    -> one place that owns the flow
    *  Compensation    -> undo in REVERSE order (stack / LIFO)
    *  Failed step     -> never needs its own undo, it did not complete
    *  Production      -> persist saga progress so a crash can resume,
    *                     retry undos until they work, keep every step
    *                     and undo idempotent
    *  Real tools      -> Temporal, Camunda, Netflix Conductor,
    *                     AWS Step Functions
    *
    * ================================================================
 
 */
public class SagaOrchestrationDemo {

    // ---------------- fake services with state we can inspect ----------------
    static int stock = 5;
    static int wallet = 1000;
    static boolean courierDown = false;

    record Step(String name, Runnable action, Runnable compensation) {
    }

    static class Orchestrator {
        boolean run(String sagaName, List<Step> steps) {
            System.out.println("  saga '" + sagaName + "' started");
            Deque<Step> completed = new ArrayDeque<>();
            for (Step step : steps) {
                try {
                    System.out.println("  -> " + step.name());
                    step.action().run();
                    completed.push(step);                       // remember what to undo later
                } catch (RuntimeException e) {
                    System.out.println("  !! step '" + step.name() + "' FAILED: " + e.getMessage());
                    compensate(completed);
                    return false;
                }
            }
            System.out.println("  saga completed successfully");
            return true;
        }

        private void compensate(Deque<Step> completed) {
            while (!completed.isEmpty()) {                       // LIFO = reverse order
                Step step = completed.pop();
                System.out.println("  <- undo '" + step.name() + "'");
                // Real systems: retry compensation until it succeeds, and make it idempotent.
                step.compensation().run();
            }
            System.out.println("  saga rolled back via compensations");
        }
    }

    static List<Step> orderSteps(int price) {
        List<Step> steps = new ArrayList<>();
        steps.add(new Step("reserve stock",
                () -> stock--,
                () -> stock++));
        steps.add(new Step("charge payment",
                () -> {
                    if (price > wallet) {
                        throw new IllegalStateException("insufficient funds");
                    }
                    wallet -= price;
                },
                () -> wallet += price));
        steps.add(new Step("create shipment",
                () -> {
                    if (courierDown) {
                        throw new IllegalStateException("courier service unavailable");
                    }
                },
                () -> {
                }));
        return steps;
    }

    static void printState() {
        System.out.println("  state -> stock=" + stock + ", wallet=" + wallet);
    }

    public static void main(String[] args) {
        Orchestrator orchestrator = new Orchestrator();

        System.out.println("Run 1: everything works");
        printState();
        orchestrator.run("order-1", orderSteps(300));
        printState();

        System.out.println("\nRun 2: courier is down, the LAST step fails, earlier steps are undone in reverse");
        courierDown = true;
        orchestrator.run("order-2", orderSteps(300));
        printState();
        System.out.println("  (stock and wallet are exactly as before run 2)");

        System.out.println("\nRun 3: payment fails (step 2), only step 1 needs undoing");
        courierDown = false;
        orchestrator.run("order-3", orderSteps(99_999));
        printState();

        System.out.println("\nProduction notes: persist the saga's progress so a crash mid-saga can resume or compensate,"
                + "\nretry compensations until they succeed, and make every step and undo idempotent.");
    }
}
