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
import java.util.Set;

/**
 * 39. RESOURCE SERVER with ROLES and SCOPES - the difference between 401 and 403
 *
 *   401 Unauthorized = "I don't know who you are"  (no token / bad token / expired)   => AUTHENTICATION failed
 *   403 Forbidden    = "I know who you are, but you may not do this"                  => AUTHORIZATION failed
 *
 * ROLES  describe WHO the user is        (ROLE_ADMIN, ROLE_SUPPORT)   - used for user logins
 * SCOPES describe WHAT the token may do  (payments:read, payments:write) - used for apps / machine clients
 *
 * Here a real HTTP server protects 3 endpoints. Tokens are looked up in a map to keep this file short;
 * JwtDemo.java shows how a real token is verified. Spring version of the same rules: spring_snippets/.
 *
 * Run: java RoleScopeCheckDemo.java
 */
public class RoleScopeCheckDemo {

    record Principal(String name, Set<String> roles, Set<String> scopes) {
    }

    static final Map<String, Principal> TOKENS = Map.of(
            "tok-alice", new Principal("alice", Set.of("SUPPORT"), Set.of("payments:read")),
            "tok-bob", new Principal("bob", Set.of("ADMIN"), Set.of("payments:read", "payments:write")),
            "tok-reporting-app", new Principal("reporting-app", Set.of(), Set.of("payments:read")));

    static void send(HttpExchange ex, int status, String body) throws IOException {
        byte[] b = body.getBytes(StandardCharsets.UTF_8);
        ex.sendResponseHeaders(status, b.length);
        ex.getResponseBody().write(b);
        ex.close();
    }

    /** Authenticate (401) then authorize (403). Returns true if the request may continue. */
    static boolean guard(HttpExchange ex, String requiredRole, String requiredScope) throws IOException {
        String header = ex.getRequestHeaders().getFirst("Authorization");
        Principal p = (header != null && header.startsWith("Bearer ")) ? TOKENS.get(header.substring(7)) : null;
        if (p == null) {
            ex.getResponseHeaders().add("WWW-Authenticate", "Bearer");
            send(ex, 401, "401 who are you? (missing or invalid token)");
            return false;
        }
        if (requiredRole != null && !p.roles().contains(requiredRole)) {
            send(ex, 403, "403 " + p.name() + " lacks role " + requiredRole);
            return false;
        }
        if (requiredScope != null && !p.scopes().contains(requiredScope)) {
            send(ex, 403, "403 " + p.name() + " lacks scope " + requiredScope);
            return false;
        }
        ex.setAttribute("principal", p);
        return true;
    }

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);

        server.createContext("/payments", ex -> {                       // GET: needs scope payments:read
            if (!guard(ex, null, "payments:read")) return;
            send(ex, 200, "200 list of payments for " + ((Principal) ex.getAttribute("principal")).name());
        });
        server.createContext("/payments/refund", ex -> {                // POST: needs scope payments:write AND role ADMIN
            if (!guard(ex, "ADMIN", "payments:write")) return;
            send(ex, 200, "200 refund executed by " + ((Principal) ex.getAttribute("principal")).name());
        });
        server.createContext("/health", ex -> send(ex, 200, "200 UP"));  // public: no guard

        server.start();
        int port = server.getAddress().getPort();
        HttpClient client = HttpClient.newHttpClient();

        try {
            call(client, port, "GET", "/health", null, "public endpoint, no token");
            call(client, port, "GET", "/payments", null, "no token");
            call(client, port, "GET", "/payments", "tok-garbage", "bad token");
            call(client, port, "GET", "/payments", "tok-alice", "alice (SUPPORT) reads");
            call(client, port, "POST", "/payments/refund", "tok-alice", "alice tries refund");
            call(client, port, "POST", "/payments/refund", "tok-reporting-app", "reporting-app tries refund");
            call(client, port, "POST", "/payments/refund", "tok-bob", "bob (ADMIN) refunds");
            System.out.println("\nPrinciple of least privilege: reporting-app gets ONLY payments:read, so a leak of its token cannot move money.");
        } finally {
            server.stop(0);
            System.exit(0);
        }
    }

    static void call(HttpClient c, int port, String method, String path, String token, String label) throws Exception {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + path))
                .method(method, HttpRequest.BodyPublishers.noBody());
        if (token != null) b.header("Authorization", "Bearer " + token);
        HttpResponse<String> r = c.send(b.build(), HttpResponse.BodyHandlers.ofString());
        System.out.printf("%-30s %-5s %-18s -> %s%n", label, method, path, r.body());
    }
}
