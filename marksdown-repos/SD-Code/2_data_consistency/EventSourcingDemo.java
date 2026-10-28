import java.util.ArrayList;
import java.util.List;

/**
 * 21. EVENT SOURCING - store the EVENTS, not just the current state
 *
 * Normal approach: a row says balance = 700. How did it get there? Unknown.
 * Event sourcing: store every fact that happened: Opened, Deposited 1000, Withdrawn 300 ...
 * Current state = replay the events from the start.
 *
 *  + perfect audit trail (a ledger, like a bank passbook)
 *  + "time travel": rebuild the state at any past moment
 *  + new read models can be built later from the same history
 *  - more complex; events are immutable forever (fix mistakes with NEW events, never edits);
 *    long histories need SNAPSHOTS for speed
 *
 * Run: java EventSourcingDemo.java
 */
public class EventSourcingDemo {

    sealed interface AccountEvent permits Opened, Deposited, Withdrawn {
    }

    record Opened(String owner) implements AccountEvent {
    }

    record Deposited(int amount, String memo) implements AccountEvent {
    }

    record Withdrawn(int amount, String memo) implements AccountEvent {
    }

    /** The state is DERIVED by applying events. */
    static class Account {
        String owner;
        int balance;
        int version;                                          // number of events applied

        void apply(AccountEvent e) {
            if (e instanceof Opened o) {
                owner = o.owner();
            } else if (e instanceof Deposited d) {
                balance += d.amount();
            } else if (e instanceof Withdrawn w) {
                balance -= w.amount();
            }
            version++;
        }

        static Account replay(List<AccountEvent> events, int upToVersion) {
            Account a = new Account();
            for (int i = 0; i < Math.min(upToVersion, events.size()); i++) {
                a.apply(events.get(i));
            }
            return a;
        }
    }

    record Snapshot(int version, String owner, int balance) {
    }

    static class EventStore {
        final List<AccountEvent> events = new ArrayList<>();
        Snapshot snapshot;                                    // optional speed-up

        void append(AccountEvent e) {
            events.add(e);
            if (events.size() % 4 == 0) {                      // snapshot every 4 events
                Account a = Account.replay(events, events.size());
                snapshot = new Snapshot(a.version, a.owner, a.balance);
            }
        }

        // COMMAND side: decide using current state, then append an event
        void withdraw(int amount, String memo) {
            Account current = Account.replay(events, events.size());
            if (amount > current.balance) {
                throw new IllegalStateException("insufficient funds: balance " + current.balance + ", asked " + amount);
            }
            append(new Withdrawn(amount, memo));
        }

        Account loadWithSnapshot() {
            Account a = new Account();
            int start = 0;
            if (snapshot != null) {
                a.owner = snapshot.owner();
                a.balance = snapshot.balance();
                a.version = snapshot.version();
                start = snapshot.version();
            }
            for (int i = start; i < events.size(); i++) {
                a.apply(events.get(i));
            }
            System.out.println("    (loaded using " + (events.size() - start) + " event(s) after snapshot at version " + start + ")");
            return a;
        }
    }

    public static void main(String[] args) {
        EventStore store = new EventStore();
        store.append(new Opened("Ankur"));
        store.append(new Deposited(1000, "salary"));
        store.append(new Withdrawn(300, "rent"));
        store.append(new Deposited(250, "refund"));
        store.append(new Withdrawn(100, "groceries"));

        System.out.println("1) The stored history (this IS the database):");
        for (int i = 0; i < store.events.size(); i++) {
            System.out.println("   v" + (i + 1) + "  " + store.events.get(i));
        }

        Account now = Account.replay(store.events, store.events.size());
        System.out.println("\n2) Current state = replay everything: owner=" + now.owner + ", balance=" + now.balance);

        System.out.println("\n3) Time travel: balance after each version");
        for (int v = 1; v <= store.events.size(); v++) {
            System.out.println("   as of v" + v + ": balance " + Account.replay(store.events, v).balance);
        }

        System.out.println("\n4) Commands are validated against current state, and produce events");
        try {
            store.withdraw(5000, "car");
        } catch (IllegalStateException e) {
            System.out.println("   rejected: " + e.getMessage());
        }

        System.out.println("\n5) A mistake is fixed with a NEW event, history is never edited:");
        store.append(new Deposited(100, "CORRECTION: groceries was charged by mistake"));
        System.out.println("   balance now: " + Account.replay(store.events, store.events.size()).balance);

        System.out.println("\n6) Snapshots avoid replaying a long history:");
        Account fast = store.loadWithSnapshot();
        System.out.println("   balance via snapshot + tail: " + fast.balance
                + " (same answer as full replay: " + Account.replay(store.events, store.events.size()).balance + ")");
    }
}
