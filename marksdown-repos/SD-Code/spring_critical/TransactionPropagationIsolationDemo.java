import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;

/**
 * 3. TRANSACTION PROPAGATION and ISOLATION - the part of @Transactional people get wrong
 *
 * (Rollback rules and self-invocation are already in spring_concepts/TransactionDemo. This is the NEXT level.)
 *
 * PROPAGATION = "what should happen when a transactional method is called from another transactional method?"
 *   REQUIRED      (default) join the caller's transaction, or start one if none. Like sharing one taxi.
 *   REQUIRES_NEW  suspend the caller's transaction and run in a brand new, independent one. Like taking a separate cab.
 *
 * Gotchas shown below:
 *   1. With REQUIRED, an AUDIT row is rolled back together with the failed business operation - you lose evidence.
 *   2. Using REQUIRES_NEW for the audit row keeps it even when the business transaction rolls back.
 *   3. If an inner REQUIRED method throws and the outer method CATCHES it, the shared transaction is already marked
 *      "rollback-only": the outer commit then fails with UnexpectedRollbackException. Nasty surprise.
 *   4. An inner REQUIRES_NEW failure only rolls back itself, so the outer can safely catch it and continue.
 *
 * ISOLATION = "how much of other people's in-flight work can I see?"
 *   READ_UNCOMMITTED -> dirty reads    READ_COMMITTED -> non-repeatable reads    REPEATABLE_READ -> stable snapshot
 *
 * Real Spring version: spring_snippets/TransactionSnippets.java
 * Run: java TransactionPropagationIsolationDemo.java
 */
public class TransactionPropagationIsolationDemo {

    static class UnexpectedRollback extends RuntimeException { UnexpectedRollback(String m) { super(m); } }

    static class Tx {
        final String name;
        final Map<String, Integer> writes = new LinkedHashMap<>();
        final List<String> auditWrites = new ArrayList<>();
        boolean rollbackOnly;
        Tx(String name) { this.name = name; }
    }

    static RuntimeException unchecked(Exception e) { return e instanceof RuntimeException r ? r : new RuntimeException(e); }

    /** A tiny database + transaction manager. */
    static class Db {
        final Map<String, Integer> accounts = new LinkedHashMap<>();
        final List<String> auditTable = new ArrayList<>();
        final Deque<Tx> stack = new ArrayDeque<>();
        int counter;

        Db() { accounts.put("A", 1000); accounts.put("B", 500); }

        Tx current() { return stack.peek(); }
        int balance(String acc) { Tx t = current(); return t != null && t.writes.containsKey(acc) ? t.writes.get(acc) : accounts.get(acc); }
        void setBalance(String acc, int v) { current().writes.put(acc, v); }
        void audit(String msg) { current().auditWrites.add(msg); }

        <T> T required(String label, Callable<T> body) {
            if (current() != null) {
                System.out.println("      [" + label + "] REQUIRED: joins existing " + current().name);
                try {
                    return body.call();
                } catch (Exception e) {
                    current().rollbackOnly = true;
                    System.out.println("      [" + label + "] threw -> shared " + current().name + " is now ROLLBACK-ONLY");
                    throw unchecked(e);
                }
            }
            return runNew(label, body);
        }

        <T> T requiresNew(String label, Callable<T> body) {
            if (current() != null) System.out.println("      [" + label + "] REQUIRES_NEW: suspends " + current().name + ", starts a new transaction");
            return runNew(label, body);
        }

        private <T> T runNew(String label, Callable<T> body) {
            Tx tx = new Tx("T" + (++counter) + "(" + label + ")");
            stack.push(tx);
            System.out.println("      BEGIN  " + tx.name);
            try {
                T result = body.call();
                if (tx.rollbackOnly) throw new UnexpectedRollback("Transaction silently rolled back because it has been marked as rollback-only");
                accounts.putAll(tx.writes);
                auditTable.addAll(tx.auditWrites);
                System.out.println("      COMMIT " + tx.name);
                return result;
            } catch (Exception e) {
                System.out.println("      ROLLBACK " + tx.name + "  (" + e.getClass().getSimpleName() + ": " + e.getMessage() + ")");
                throw unchecked(e);
            } finally {
                stack.pop();
            }
        }

        void show() { System.out.println("   RESULT: accounts=" + accounts + "  audit=" + auditTable); }
    }

    static void scenario(String title, java.util.function.Consumer<Db> body) {
        System.out.println("\n" + title);
        Db db = new Db();
        try {
            body.accept(db);
        } catch (RuntimeException e) {
            System.out.println("   caller sees: " + e.getClass().getSimpleName() + " - " + e.getMessage());
        }
        db.show();
    }

    static void debitAndFail(Db db) {
        db.setBalance("A", db.balance("A") - 200);
        throw new IllegalStateException("credit failed: account B is frozen");
    }

    // ------------------------------------------------------------------ isolation levels
    enum Level { READ_UNCOMMITTED, READ_COMMITTED, REPEATABLE_READ }

    static class IsoReader {
        final Level level; Integer snapshot;
        IsoReader(Level level) { this.level = level; }
        int read(int committed, Integer uncommittedByWriter) {
            return switch (level) {
                case READ_UNCOMMITTED -> uncommittedByWriter != null ? uncommittedByWriter : committed;
                case READ_COMMITTED -> committed;
                case REPEATABLE_READ -> { if (snapshot == null) snapshot = committed; yield snapshot; }
            };
        }
    }

    public static void main(String[] args) {
        System.out.println("################ PROPAGATION ################");

        scenario("1) Everything REQUIRED: the audit row dies together with the failed transfer",
                db -> db.required("transfer", () -> {
                    db.required("audit", () -> { db.audit("transfer A->B 200 attempted"); return null; });
                    debitAndFail(db);
                    return null;
                }));

        scenario("2) Audit uses REQUIRES_NEW: the audit row SURVIVES the rollback (this is what you want)",
                db -> db.required("transfer", () -> {
                    db.requiresNew("audit", () -> { db.audit("transfer A->B 200 attempted"); return null; });
                    debitAndFail(db);
                    return null;
                }));

        scenario("3) GOTCHA: inner REQUIRED throws, outer catches and carries on -> commit explodes",
                db -> db.required("outer", () -> {
                    try {
                        db.required("inner-validation", () -> { throw new IllegalArgumentException("coupon expired"); });
                    } catch (IllegalArgumentException e) {
                        System.out.println("      [outer] caught '" + e.getMessage() + "', continuing as if nothing happened");
                    }
                    db.setBalance("A", db.balance("A") - 50);
                    return null;
                }));

        scenario("4) Inner REQUIRES_NEW throws, outer catches -> outer commits normally",
                db -> db.required("outer", () -> {
                    try {
                        db.requiresNew("optional-bonus", () -> { throw new IllegalArgumentException("bonus service down"); });
                    } catch (IllegalArgumentException e) {
                        System.out.println("      [outer] caught '" + e.getMessage() + "', continuing");
                    }
                    db.setBalance("A", db.balance("A") - 50);
                    return null;
                }));

        System.out.println("\n################ ISOLATION ################");
        System.out.println("Balance is 100. A writer changes it to 50 but has NOT committed. Reader reads, writer commits, reader reads again.\n");
        System.out.printf("%-18s %-26s %-26s %s%n", "isolation level", "1st read (writer pending)", "2nd read (writer committed)", "what happened");
        for (Level level : Level.values()) {
            IsoReader reader = new IsoReader(level);
            int first = reader.read(100, 50);
            int second = reader.read(50, null);
            String note = switch (level) {
                case READ_UNCOMMITTED -> "DIRTY READ: saw 50 which might still be rolled back";
                case READ_COMMITTED -> "NON-REPEATABLE READ: same row, two different values";
                case REPEATABLE_READ -> "stable: same value inside my transaction";
            };
            System.out.printf("%-18s %-26d %-26d %s%n", level, first, second, note);
        }
        System.out.println("\nDefaults: PostgreSQL/Oracle = READ_COMMITTED, MySQL InnoDB = REPEATABLE_READ. @Transactional(isolation=DEFAULT) uses the database's default.");
        System.out.println("Higher isolation = fewer anomalies but more locking/conflicts. Money transfers also need locking or optimistic @Version (see 2_data_consistency).");
    }
}
