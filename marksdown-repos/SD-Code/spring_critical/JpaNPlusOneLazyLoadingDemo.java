import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 4. SPRING DATA JPA / HIBERNATE - the four things that bite everybody
 *
 *   A) N+1 SELECTS      1 query for 5 customers + 1 query PER customer for their orders = 6 queries.
 *                       With 1000 customers = 1001 queries. Looks fine in dev, kills production.
 *   B) FIXES            JOIN FETCH / @EntityGraph (1 query)  or  @BatchSize (a few queries using IN (...)).
 *   C) LAZY LOADING     orders are fetched only when touched. Touch them after the session/transaction closed
 *                       and you get LazyInitializationException. Fix: map to a DTO inside the transaction.
 *   D) PERSISTENCE CONTEXT: entities loaded in a session are TRACKED.
 *        - same id twice = 1 SQL (first-level cache)
 *        - change a field and commit = UPDATE is issued automatically ("dirty checking"), NO save() needed.
 *
 * The fake database counts every SQL statement so you can SEE the difference.
 * Real Spring Data version: spring_snippets/JpaSnippets.java
 *
 * Run: java JpaNPlusOneLazyLoadingDemo.java
 */
public class JpaNPlusOneLazyLoadingDemo {

    static int queryCount;

    static void sql(String s) { queryCount++; System.out.println("      SQL #" + queryCount + ": " + s); }

    record OrderRow(int id, int customerId, int amount) { }

    static final Map<Integer, String> CUSTOMER_TABLE = new LinkedHashMap<>();
    static final List<OrderRow> ORDER_TABLE = new ArrayList<>();

    static {
        String[] names = {"Asha", "Vikram", "Neha", "Ravi", "Meera"};
        for (int i = 0; i < names.length; i++) {
            CUSTOMER_TABLE.put(i + 1, names[i]);
            ORDER_TABLE.add(new OrderRow(i * 2 + 1, i + 1, 100 * (i + 1)));
            ORDER_TABLE.add(new OrderRow(i * 2 + 2, i + 1, 50 * (i + 1)));
        }
    }

    static class LazyInitializationException extends RuntimeException {
        LazyInitializationException(String m) { super(m); }
    }

    static class Customer {
        final int id;
        String name;
        List<OrderRow> orders;                 // null = not loaded yet (a lazy collection)
        final Session session;

        Customer(int id, String name, Session session) { this.id = id; this.name = name; this.session = session; }

        List<OrderRow> orders() {
            if (orders == null) {
                if (!session.open) {
                    throw new LazyInitializationException("failed to lazily initialize a collection of role: Customer.orders, could not initialize proxy - no Session");
                }
                session.loadOrdersFor(this);
            }
            return orders;
        }
    }

    static class Session {
        boolean open = true;
        int batchSize = 1;                     // @BatchSize(size = N)
        final Map<Integer, Customer> cache = new LinkedHashMap<>();
        final Map<Integer, String> snapshot = new HashMap<>();

        Customer register(int id, String name) {
            Customer c = new Customer(id, name, this);
            cache.put(id, c);
            snapshot.put(id, name);            // remember the original state for dirty checking
            return c;
        }

        Customer find(int id) {
            if (cache.containsKey(id)) { System.out.println("      (first-level cache hit, no SQL)"); return cache.get(id); }
            sql("select * from customer where id = " + id);
            return register(id, CUSTOMER_TABLE.get(id));
        }

        List<Customer> findAll() {
            sql("select * from customer");
            List<Customer> list = new ArrayList<>();
            CUSTOMER_TABLE.forEach((id, name) -> list.add(register(id, name)));
            return list;
        }

        List<Customer> findAllJoinFetch() {
            sql("select c.*, o.* from customer c left join orders o on o.customer_id = c.id");
            List<Customer> list = new ArrayList<>();
            CUSTOMER_TABLE.forEach((id, name) -> {
                Customer c = register(id, name);
                c.orders = ORDER_TABLE.stream().filter(o -> o.customerId() == id).collect(Collectors.toList());
                list.add(c);
            });
            return list;
        }

        void loadOrdersFor(Customer first) {
            List<Customer> group = new ArrayList<>();
            for (Customer c : cache.values()) {
                if (c.orders == null && group.size() < batchSize) group.add(c);   // with batchSize 1 only 'first' qualifies
            }
            if (!group.contains(first)) group.add(0, first);
            String ids = group.stream().map(c -> String.valueOf(c.id)).collect(Collectors.joining(", "));
            sql("select * from orders where customer_id " + (group.size() == 1 ? "= " + ids : "in (" + ids + ")"));
            for (Customer c : group) {
                c.orders = ORDER_TABLE.stream().filter(o -> o.customerId() == c.id).collect(Collectors.toList());
            }
        }

        void commit() {
            boolean any = false;
            for (Customer c : cache.values()) {                                    // dirty checking: compare with snapshot
                if (!c.name.equals(snapshot.get(c.id))) {
                    sql("update customer set name = '" + c.name + "' where id = " + c.id);
                    any = true;
                }
            }
            if (!any) System.out.println("      (flush: nothing changed, no SQL)");
        }

        void close() { open = false; }
    }

    static void header(String t) { queryCount = 0; System.out.println("\n" + t); }

    public static void main(String[] args) {
        header("A) THE N+1 PROBLEM: list customers and print their order counts");
        Session s = new Session();
        for (Customer c : s.findAll()) System.out.println("      " + c.name + " has " + c.orders().size() + " orders");
        System.out.println("   => " + queryCount + " queries for 5 customers (1 + N). For 1000 customers it would be 1001.");

        header("B1) FIX with JOIN FETCH / @EntityGraph");
        s = new Session();
        for (Customer c : s.findAllJoinFetch()) System.out.println("      " + c.name + " has " + c.orders().size() + " orders");
        System.out.println("   => " + queryCount + " query. (Caution: join-fetching a collection + pagination = paging in memory.)");

        header("B2) FIX with @BatchSize(size = 10): orders loaded in groups");
        s = new Session();
        s.batchSize = 10;
        for (Customer c : s.findAll()) System.out.println("      " + c.name + " has " + c.orders().size() + " orders");
        System.out.println("   => " + queryCount + " queries (1 + ceil(5/10)). No query rewrite needed, great as a global default.");

        header("C) LAZY LOADING after the transaction ended (typical when a controller touches an entity)");
        s = new Session();
        Customer asha = s.find(1);
        s.close();                                                               // @Transactional method returned
        try {
            System.out.println("      controller calls asha.orders() ...");
            asha.orders();
        } catch (LazyInitializationException e) {
            System.out.println("      LazyInitializationException: " + e.getMessage());
        }
        System.out.println("   FIX: inside the transaction convert to a DTO (name + order count) and return only the DTO.");
        s = new Session();
        Customer inside = s.find(1);
        record CustomerSummary(String name, int orders) { }
        CustomerSummary dto = new CustomerSummary(inside.name, inside.orders().size());
        s.close();
        System.out.println("      returned DTO: " + dto);

        header("D) PERSISTENCE CONTEXT: first-level cache and dirty checking");
        s = new Session();
        Customer v = s.find(2);
        s.find(2);
        System.out.println("      changing name in memory, NOT calling save():");
        v.name = "Vikram J.";
        s.commit();
        System.out.println("   => Hibernate noticed the change and issued the UPDATE by itself.");
        System.out.println("\nTip: set spring.jpa.open-in-view=false so lazy loading cannot silently happen in the web layer,\n"
                + "and watch SQL counts in tests (Hibernate Statistics / datasource-proxy) to catch N+1 before production.");
    }
}
