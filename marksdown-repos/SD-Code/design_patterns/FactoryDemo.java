import java.util.Map;
import java.util.function.Supplier;

/**
 * FACTORY - one place decides WHICH object to create; callers just ask for what they need.
 *
 * Real-life: you tell the restaurant "one coffee". You do not go into the kitchen and
 * decide which machine, beans and cup to use. The kitchen (factory) handles it.
 *
 * Benefit: callers depend on an interface, not on concrete classes (no scattered
 * "new EmailSender()" / if-else chains), and adding a new type touches only the factory.
 *
 * Run: java FactoryDemo.java
 */
public class FactoryDemo {

    // ---- Product interface ----
    interface Notifier {
        void send(String to, String message);
    }

    // ---- Concrete products ----
    static class EmailNotifier implements Notifier {
        public void send(String to, String message) {
            System.out.println("  [EMAIL -> " + to + "] " + message);
        }
    }

    static class SmsNotifier implements Notifier {
        public void send(String to, String message) {
            System.out.println("  [SMS   -> " + to + "] " + message);
        }
    }

    static class PushNotifier implements Notifier {
        public void send(String to, String message) {
            System.out.println("  [PUSH  -> " + to + "] " + message);
        }
    }

    // ---- Simple Factory ----
    static class NotifierFactory {
        // Registry of "how to build each type". Adding WhatsApp = one new line here.
        private static final Map<String, Supplier<Notifier>> REGISTRY = Map.of(
                "email", EmailNotifier::new,
                "sms", SmsNotifier::new,
                "push", PushNotifier::new
        );

        static Notifier create(String type) {
            Supplier<Notifier> supplier = REGISTRY.get(type.toLowerCase());
            if (supplier == null) {
                throw new IllegalArgumentException("Unknown notifier type: " + type);
            }
            return supplier.get();
        }
    }

    // ---- Client: never says "new EmailNotifier()" ----
    static void alertCustomer(String channel, String customer, String text) {
        Notifier notifier = NotifierFactory.create(channel);
        notifier.send(customer, text);
    }

    public static void main(String[] args) {
        alertCustomer("email", "ankur@example.com", "Your statement is ready");
        alertCustomer("sms", "+91-9XXXXXXXXX", "OTP 482913");
        alertCustomer("push", "device-77", "Salary credited");

        try {
            alertCustomer("fax", "nobody", "hello");
        } catch (IllegalArgumentException e) {
            System.out.println("  error: " + e.getMessage());
        }
    }
}
