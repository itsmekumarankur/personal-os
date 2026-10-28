import java.util.HashMap;
import java.util.Map;

/**
 * 16. DATABASE PER SERVICE - and why a shared database is an anti-pattern
 *
 * Picture: two departments sharing ONE filing cabinet.
 *   - Accounts renames a drawer label; Orders still looks under the old label and finds nothing.
 *   - Orders reaches in and edits Accounts' papers, bypassing Accounts' rules.
 * Nobody can change anything without asking everybody. That is a "distributed monolith".
 *
 * Better: each service owns its data privately. Others get information only by ASKING the owner
 * (API) or by listening to the owner's EVENTS.
 *
 * Trade-off you accept: no cross-service JOINs and no cross-service ACID transactions.
 * You use API composition (see aggregator zip), events, and sagas instead.
 *
 * Run: java DatabasePerServiceDemo.java
 */
public class DatabasePerServiceDemo {

    // =====================================================================================
    // ANTI-PATTERN: one shared database
    // =====================================================================================
    static class SharedDatabase {
        final Map<Integer, Map<String, Object>> customers = new HashMap<>();

        void renameColumn(String from, String to) {                  // a normal "migration" by the Customer team
            customers.values().forEach(row -> row.put(to, row.remove(from)));
        }
    }

    static class OrderServiceUsingSharedDb {
        private final SharedDatabase db;

        OrderServiceUsingSharedDb(SharedDatabase db) {
            this.db = db;
        }

        String describeOrder(int customerId) {
            Object name = db.customers.get(customerId).get("cust_name");     // reads another team's table directly
            return "Order for customer: " + name;
        }

        void grantCredit(int customerId, int amount) {                       // writes another team's table directly
            db.customers.get(customerId).put("credit_limit", amount);        // bypasses the Customer service's rules!
        }
    }

    // =====================================================================================
    // GOOD: each service owns its data; others use the owner's API
    // =====================================================================================
    record CustomerDto(int id, String name) {                        // the PUBLIC contract
    }

    static class CustomerService {
        private final Map<Integer, Map<String, Object>> privateDb = new HashMap<>();   // only this service touches it

        CustomerService() {
            privateDb.put(7, new HashMap<>(Map.of("cust_name", "Ankur", "credit_limit", 5000)));
        }

        CustomerDto getCustomer(int id) {                            // API
            return new CustomerDto(id, (String) privateDb.get(id).get("cust_name"));
        }

        void renameColumnInternally() {                              // refactor storage freely
            privateDb.values().forEach(row -> row.put("full_name", row.remove("cust_name")));
        }

        // after the refactor the mapping changes, the API does not
        CustomerDto getCustomerAfterRefactor(int id) {
            return new CustomerDto(id, (String) privateDb.get(id).get("full_name"));
        }
    }

    static class OrderService {
        private final CustomerService customerApi;                                      // a dependency on an API, not a table
        private final Map<String, Map<String, Object>> orders = new HashMap<>();       // its OWN database

        OrderService(CustomerService customerApi) {
            this.customerApi = customerApi;
        }

        String placeOrder(String orderId, int customerId, boolean afterRefactor) {
            CustomerDto c = afterRefactor ? customerApi.getCustomerAfterRefactor(customerId)
                    : customerApi.getCustomer(customerId);
            // store only what the Order service needs, including a SNAPSHOT of the name at order time
            orders.put(orderId, Map.of("customerId", customerId, "customerNameAtOrderTime", c.name()));
            return "Order " + orderId + " placed for " + c.name();
        }
    }

    public static void main(String[] args) {
        System.out.println("A) SHARED DATABASE (anti-pattern)");
        SharedDatabase shared = new SharedDatabase();
        shared.customers.put(7, new HashMap<>(Map.of("cust_name", "Ankur", "credit_limit", 5000)));
        OrderServiceUsingSharedDb orderTeam = new OrderServiceUsingSharedDb(shared);
        System.out.println("   before migration: " + orderTeam.describeOrder(7));
        shared.renameColumn("cust_name", "full_name");
        System.out.println("   Customer team renames cust_name -> full_name ...");
        System.out.println("   after migration : " + orderTeam.describeOrder(7) + "   <- silently broken");
        orderTeam.grantCredit(7, -999_999);
        System.out.println("   Order team wrote credit_limit=" + shared.customers.get(7).get("credit_limit")
                + " directly, skipping Customer's validation rules");

        System.out.println("\nB) DATABASE PER SERVICE");
        CustomerService customers = new CustomerService();
        OrderService orders = new OrderService(customers);
        System.out.println("   before refactor: " + orders.placeOrder("o-1", 7, false));
        customers.renameColumnInternally();
        System.out.println("   Customer team renames its internal column ...");
        System.out.println("   after refactor : " + orders.placeOrder("o-2", 7, true) + "   <- Order service unaffected");

        System.out.println("\nWhat you gain: independent deploys, independent schema changes, independent scaling, clear ownership.");
        System.out.println("What you give up: JOINs across services and distributed transactions (use APIs, events, sagas).");
    }
}
