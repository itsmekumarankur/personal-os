import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * 19. COMPENSATING TRANSACTIONS
 *
 * A DATABASE ROLLBACK erases work that nobody else has seen yet.
 * Across services, step 1 has already COMMITTED and may have been SEEN (statement, email, event).
 * You cannot erase it. You can only do a NEW action that cancels its effect: a compensating transaction.
 *
 * Banking example: debit A, then crediting B fails -> post a REVERSAL entry to A.
 *   - The ledger is append-only: history shows debit AND reversal (auditors love this).
 *   - The compensation must be IDEMPOTENT: it may be retried after a crash or timeout.
 *   - Some side effects cannot be undone (an email already sent); compensation = a correction email.
 *
 * Run: java CompensatingTransactionDemo.java
 */
public class CompensatingTransactionDemo {

    record Entry(String txnId, String account, int amount, String memo) {
    }

    static class Ledger {
        private final List<Entry> entries = new ArrayList<>();
        private final Set<String> alreadyReversed = new HashSet<>();
        private int counter = 0;

        String post(String account, int amount, String memo) {
            String id = "T" + (++counter);
            entries.add(new Entry(id, account, amount, memo));
            return id;
        }

        int balance(String account) {
            return entries.stream().filter(e -> e.account().equals(account)).mapToInt(Entry::amount).sum();
        }

        // Idempotent compensation: reversing the same transaction twice has no extra effect
        boolean reverse(String originalTxnId) {
            if (!alreadyReversed.add(originalTxnId)) {
                System.out.println("  reversal of " + originalTxnId + " already done, ignoring duplicate request");
                return false;
            }
            Entry original = entries.stream().filter(e -> e.txnId().equals(originalTxnId)).findFirst().orElseThrow();
            post(original.account(), -original.amount(), "REVERSAL of " + originalTxnId);
            return true;
        }

        void print() {
            entries.forEach(e -> System.out.printf("    %-3s %-3s %+6d  %s%n", e.txnId(), e.account(), e.amount(), e.memo()));
        }
    }

    static boolean accountBFrozen = true;

    static void creditAccountB(Ledger ledger, int amount) {
        if (accountBFrozen) {
            throw new IllegalStateException("account B is frozen");
        }
        ledger.post("B", amount, "transfer in from A");
    }

    public static void main(String[] args) {
        Ledger ledger = new Ledger();
        ledger.post("A", 1000, "opening balance");

        System.out.println("Transfer 300 from A to B");
        String debitTxn = ledger.post("A", -300, "transfer out to B");          // step 1 COMMITS
        System.out.println("  step 1 done. A's balance is now " + ledger.balance("A")
                + "  (anyone reading A's balance right now sees the reduced amount)");

        try {
            creditAccountB(ledger, 300);                                          // step 2 fails
        } catch (IllegalStateException e) {
            System.out.println("  step 2 FAILED: " + e.getMessage() + "  -> run compensation");
            ledger.reverse(debitTxn);
        }
        System.out.println("  A's balance after compensation: " + ledger.balance("A"));

        System.out.println("\nThe compensation request is retried (timeout, redelivered message, crash recovery):");
        ledger.reverse(debitTxn);                                                 // duplicate, must be a no-op
        System.out.println("  A's balance is still: " + ledger.balance("A") + " (not 1300)");

        System.out.println("\nLedger (nothing was deleted or edited; the mistake and its fix are both visible):");
        ledger.print();

        System.out.println("\nSide effects you cannot undo:");
        System.out.println("  email 'Your transfer succeeded' was already sent  ->  compensation: send 'Sorry, that transfer was cancelled'");
        System.out.println("  parcel already shipped                              ->  compensation: create a return shipment + refund");
    }
}
