/**
 * ADAPTER - make two incompatible interfaces work together.
 *
 * Real-life: a travel plug adapter. Your laptop (client) has a 3-pin plug,
 * the wall socket (existing system) is 2-pin. You do not rebuild either one,
 * you put an adapter in between.
 *
 * Here: our app talks to a PaymentProcessor, but the bank's old API and a
 * third-party SDK each have a different shape. Adapters translate the calls.
 *
 * Run: java AdapterDemo.java
 */
public class AdapterDemo {

    // ---- What OUR application expects (the "target" interface) ----
    interface PaymentProcessor {
        boolean pay(String user, int rupees);
    }

    // ---- Existing class we cannot / should not change (the "adaptee") ----
    static class LegacyBankApi {
        // different method name, different parameters, different units (paise)
        String makePayment(String accountNo, long paise) {
            System.out.println("  [LegacyBankApi] debit " + paise + " paise from " + accountNo);
            return "SUCCESS";
        }
    }

    // ---- Another incompatible third-party class ----
    static class ThirdPartySdk {
        int charge(double amountInRupees, String customerId) {
            System.out.println("  [ThirdPartySdk] charging " + amountInRupees + " to " + customerId);
            return 200; // HTTP-like status code
        }
    }

    // ---- Adapters: translate our interface into theirs ----
    static class LegacyBankAdapter implements PaymentProcessor {
        private final LegacyBankApi legacy = new LegacyBankApi();

        @Override
        public boolean pay(String user, int rupees) {
            String result = legacy.makePayment("ACC-" + user, rupees * 100L); // rupees -> paise
            return "SUCCESS".equals(result);                                  // string -> boolean
        }
    }

    static class SdkAdapter implements PaymentProcessor {
        private final ThirdPartySdk sdk = new ThirdPartySdk();

        @Override
        public boolean pay(String user, int rupees) {
            return sdk.charge(rupees, user) == 200;                           // status code -> boolean
        }
    }

    // ---- Client code only knows PaymentProcessor ----
    static void checkout(PaymentProcessor processor, String user, int rupees) {
        boolean ok = processor.pay(user, rupees);
        System.out.println("  checkout result: " + (ok ? "PAID" : "FAILED"));
    }

    public static void main(String[] args) {
        System.out.println("Using legacy bank:");
        checkout(new LegacyBankAdapter(), "ankur", 500);

        System.out.println("Using third-party SDK:");
        checkout(new SdkAdapter(), "ankur", 500);
    }
}
