import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * 29. BACKEND FOR FRONTEND (BFF)
 *
 * Different clients need different things:
 *   Mobile app : small screen, slow/expensive network, wants a tiny summary in ONE call.
 *   Web portal : big screen, wants rich detail, filters, many transactions.
 *
 * One generic API either bloats mobile (downloads everything) or starves web.
 * Instead, each client type gets its own thin BFF service that:
 *   - calls the shared backend services,
 *   - combines and TRIMS the data into exactly the shape that client needs,
 *   - is owned by the same team as the client (so UI changes do not wait for backend teams).
 * A BFF contains no business rules: it only adapts and aggregates.
 *
 * Run: java BffDemo.java
 */
public class BffDemo {

    // ---------------- shared backend domain data (rich) ----------------
    record Account(String id, String holder, long balancePaise, String branch, String ifsc, String type, String openedOn) {
    }

    record Txn(String id, String date, String description, long amountPaise, String category, String merchant, String location) {
    }

    record Offer(String id, String title, String terms, String validTill) {
    }

    static int backendCalls;

    static class AccountService {
        Account get(String id) {
            backendCalls++;
            return new Account(id, "Ankur", 12_345_600, "Chennai Main", "IDFB0080001", "SAVINGS", "2015-04-12");
        }
    }

    static class TransactionService {
        List<Txn> latest(String accountId, int n) {
            backendCalls++;
            return IntStream.rangeClosed(1, n)
                    .mapToObj(i -> new Txn("t" + i, "2026-10-" + String.format("%02d", i), "Payment to merchant " + i,
                            -(i * 15_000L), i % 2 == 0 ? "FOOD" : "TRAVEL", "Merchant " + i, "Chennai, IN"))
                    .toList();
        }
    }

    static class OfferService {
        List<Offer> forCustomer(String accountId) {
            backendCalls++;
            return List.of(
                    new Offer("o1", "5% cashback on fuel", "Valid on transactions above 500 at partner outlets. Terms apply...", "2026-12-31"),
                    new Offer("o2", "Zero fee transfers", "Applicable to NEFT/IMPS up to 2 lakh per day. Terms apply...", "2026-11-30"),
                    new Offer("o3", "Travel insurance free", "On booking flights above 5000. Terms apply...", "2027-01-15"));
        }
    }

    static String rupees(long paise) {
        return String.format("INR %,.2f", paise / 100.0);
    }

    // ---------------- BFF for the MOBILE app: tiny summary ----------------
    static class MobileBff {
        private final AccountService accounts = new AccountService();
        private final TransactionService txns = new TransactionService();
        private final OfferService offers = new OfferService();

        String home(String accountId) {
            Account a = accounts.get(accountId);
            List<Txn> latest = txns.latest(accountId, 3);                 // only 3
            Offer topOffer = offers.forCustomer(accountId).get(0);        // only 1, no long terms
            String txnJson = latest.stream()
                    .map(t -> "{\"d\":\"" + t.description() + "\",\"a\":\"" + rupees(t.amountPaise()) + "\"}")
                    .collect(Collectors.joining(","));
            return "{\"name\":\"" + a.holder() + "\",\"bal\":\"" + rupees(a.balancePaise()) + "\",\"recent\":[" + txnJson
                    + "],\"offer\":\"" + topOffer.title() + "\"}";
        }
    }

    // ---------------- BFF for the WEB portal: rich detail ----------------
    static class WebBff {
        private final AccountService accounts = new AccountService();
        private final TransactionService txns = new TransactionService();
        private final OfferService offers = new OfferService();

        String dashboard(String accountId) {
            Account a = accounts.get(accountId);
            List<Txn> latest = txns.latest(accountId, 20);                // 20 with full detail
            List<Offer> all = offers.forCustomer(accountId);              // all offers with terms
            String txnJson = latest.stream()
                    .map(t -> "{\"id\":\"" + t.id() + "\",\"date\":\"" + t.date() + "\",\"description\":\"" + t.description()
                            + "\",\"amount\":\"" + rupees(t.amountPaise()) + "\",\"category\":\"" + t.category()
                            + "\",\"merchant\":\"" + t.merchant() + "\",\"location\":\"" + t.location() + "\"}")
                    .collect(Collectors.joining(","));
            String offerJson = all.stream()
                    .map(o -> "{\"title\":\"" + o.title() + "\",\"terms\":\"" + o.terms() + "\",\"validTill\":\"" + o.validTill() + "\"}")
                    .collect(Collectors.joining(","));
            return "{\"account\":{\"holder\":\"" + a.holder() + "\",\"balance\":\"" + rupees(a.balancePaise()) + "\",\"branch\":\""
                    + a.branch() + "\",\"ifsc\":\"" + a.ifsc() + "\",\"type\":\"" + a.type() + "\",\"openedOn\":\"" + a.openedOn()
                    + "\"},\"transactions\":[" + txnJson + "],\"offers\":[" + offerJson + "]}";
        }
    }

    public static void main(String[] args) {
        System.out.println("Without a BFF the mobile app itself would call 3 services over a slow network and download everything.\n");

        backendCalls = 0;
        String mobile = new MobileBff().home("acc-1");
        System.out.println("MOBILE BFF response (" + mobile.length() + " chars, client makes 1 call, BFF made " + backendCalls + " backend calls):");
        System.out.println("  " + mobile);

        backendCalls = 0;
        String web = new WebBff().dashboard("acc-1");
        System.out.println("\nWEB BFF response (" + web.length() + " chars, client makes 1 call, BFF made " + backendCalls + " backend calls):");
        System.out.println("  " + web.substring(0, 330) + " ... (truncated for display)");

        System.out.printf("%nPayload ratio: web is %.1fx larger than mobile. Same backends, two BFFs, each shaped for its client.%n",
                web.length() / (double) mobile.length());
        System.out.println("Do NOT put business rules in a BFF (they belong in the domain services), and do not make one BFF serve every client again.");
    }
}
