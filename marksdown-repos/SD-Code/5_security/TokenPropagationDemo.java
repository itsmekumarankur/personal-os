import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/**
 * 41. TOKEN PROPAGATION - passing the user's identity down a call chain
 *
 *   browser --(Bearer user-token)--> order-service --(?)--> payment-service --(?)--> ledger-service
 *
 * Problem: when order-service calls payment-service, WHO is calling? Two answers:
 *   A) PROPAGATE (relay) the user's token => downstream sees the real user and enforces per-user rules
 *      (alice may only see HER payments). Used when the action is "on behalf of the user".
 *   B) USE the service's OWN token (client credentials) => downstream knows "order-service" is calling
 *      but has lost the end user. Used for system jobs, or combined with an extra X-User header.
 *   Often a mix: propagate the user token for user-scoped data; own token for background work.
 *
 * Must-know risks: only relay tokens over trusted internal links, check the audience (aud) so a token for
 * order-service is not accepted by everyone, and keep the chain short. Production fix for deep chains:
 * OAuth2 TOKEN EXCHANGE (RFC 8693) - swap the user token for a narrower one per hop.
 *
 * Spring: a WebClient/RestClient interceptor copies the Authorization header (see spring_snippets/).
 * Run: java TokenPropagationDemo.java
 */
public class TokenPropagationDemo {

    static final Map<String, String> TOKEN_TO_USER = Map.of("tok-alice", "alice", "tok-bob", "bob");
    static final Map<String, String> PAYMENTS = Map.of("alice", "alice's payments: [100, 250]", "bob", "bob's payments: [999]");

    static void reply(HttpExchange ex, int status, String body) throws IOException {
        byte[] b = body.getBytes(StandardCharsets.UTF_8);
        ex.sendResponseHeaders(status, b.length);
        ex.getResponseBody().write(b);
        ex.close();
    }

    static HttpServer start(String name, com.sun.net.httpserver.HttpHandler handler) throws IOException {
        HttpServer s = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        s.createContext("/", handler);
        s.start();
        return s;
    }

    public static void main(String[] args) throws Exception {
        HttpClient http = HttpClient.newHttpClient();

        // ---- payment-service: authenticates the token and returns data for THAT user only
        HttpServer payment = start("payment", ex -> {
            String h = ex.getRequestHeaders().getFirst("Authorization");
            String token = h == null ? null : h.replace("Bearer ", "");
            String user = token == null ? null : TOKEN_TO_USER.get(token);
            if (user == null) {
                reply(ex, 401, "payment-service: 401 no valid user token");
                return;
            }
            reply(ex, 200, "payment-service saw user '" + user + "' -> " + PAYMENTS.get(user));
        });
        String paymentUrl = "http://127.0.0.1:" + payment.getAddress().getPort();

        // ---- order-service: PROPAGATES the incoming Authorization header downstream
        HttpServer orderPropagating = start("order-propagating", ex -> {
            String incoming = ex.getRequestHeaders().getFirst("Authorization");
            HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(paymentUrl + "/payments"));
            if (incoming != null) b.header("Authorization", incoming);                 // <- the propagation line
            try {
                reply(ex, 200, "order-service(propagate) -> " + http.send(b.build(), HttpResponse.BodyHandlers.ofString()).body());
            } catch (Exception e) {
                reply(ex, 502, "downstream error");
            }
        });

        // ---- order-service variant that FORGETS to propagate (the classic bug)
        HttpServer orderForgetful = start("order-forgetful", ex -> {
            try {
                reply(ex, 200, "order-service(forgot) -> " + http.send(
                        HttpRequest.newBuilder(URI.create(paymentUrl + "/payments")).build(), HttpResponse.BodyHandlers.ofString()).body());
            } catch (Exception e) {
                reply(ex, 502, "downstream error");
            }
        });

        try {
            String propagating = "http://127.0.0.1:" + orderPropagating.getAddress().getPort();
            String forgetful = "http://127.0.0.1:" + orderForgetful.getAddress().getPort();

            System.out.println("1) Token propagated: downstream enforces the REAL user's data boundaries");
            System.out.println("   alice calls -> " + get(http, propagating, "tok-alice"));
            System.out.println("   bob   calls -> " + get(http, propagating, "tok-bob"));

            System.out.println("\n2) Anonymous caller: relayed as-is, rejected by payment-service");
            System.out.println("   nobody calls -> " + get(http, propagating, null));

            System.out.println("\n3) Bug: order-service forgets to forward the header -> downstream cannot identify the user");
            System.out.println("   alice calls -> " + get(http, forgetful, "tok-alice"));

            System.out.println("\nIn Spring Cloud Gateway / Feign / RestClient this is one interceptor or filter, written once.");
        } finally {
            System.exit(0);
        }
    }

    static String get(HttpClient http, String url, String token) throws Exception {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(url));
        if (token != null) b.header("Authorization", "Bearer " + token);
        return http.send(b.build(), HttpResponse.BodyHandlers.ofString()).body();
    }
}
