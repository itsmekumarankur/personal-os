import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
/**
 * ================================================================
 * OAUTH2 CLIENT CREDENTIALS FLOW - SERVICE TO SERVICE AUTHENTICATION
 * ================================================================
 *
 *  COMPONENTS:
 *
 *  +----------------------+       +-----------------------------+
 *  |    ORDER-SERVICE     |       |       AUTH SERVER            |
 *  |                      |       |                             |
 *  |  TokenCache          |       |  /oauth/token               |
 *  |  - Stores token      |       |  - Validates client ID      |
 *  |  - Checks expiry     |       |  - Validates client secret  |
 *  +----------+-----------+       |  - Issues access token      |
 *             |                   +-------------+---------------+
 *             |                                 |
 *             | 1. POST /oauth/token            |
 *             |    grant_type=client_credentials|
 *             |    client_id=order-service      |
 *             |    client_secret=order-secret   |
 *             |    scope=payments:read          |
 *             +-------------------------------->|
 *             |                                 |
 *             | 2. Validate credentials         |
 *             |    Invalid credentials -> 401   |
 *             |                                 |
 *             | 3. Return access token          |
 *             |<--------------------------------+
 *             |  access_token=abc12345          |
 *             |  expires_in=2 seconds           |
 *             |                                 |
 *             | 4. Cache token                  |
 *             |    Reuse until near expiry      |
 *             |                                 |
 *             |                                 |
 *             |       RESOURCE API CALL         |
 *             |                                 |
 *             | 5. GET /payments                |
 *             |    Authorization: Bearer abc123 |
 *             +--------------------------+      |
 *                                        |      |
 *                                        v      |
 *                         +-----------------------------+
 *                         |       PAYMENT SERVICE       |
 *                         |       Resource Server       |
 *                         |                             |
 *                         | 6. Extract Bearer token     |
 *                         | 7. Find issued token        |
 *                         | 8. Check token expiry       |
 *                         | 9. Check required scope     |
 *                         +--------------+--------------+
 *                                        |
 *                      +-----------------+-----------------+
 *                      |                 |                 |
 *                      v                 v                 v
 *                 Token invalid      Token expired     Scope missing
 *                    401                 401                403
 *
 *                      All checks pass
 *                           |
 *                           v
 *                 +----------------------+
 *                 | 200 OK               |
 *                 | Payments data        |
 *                 +----------------------+
 *
 * ================================================================
 * TOKEN CACHE BEHAVIOUR
 * ================================================================
 *
 * First API call:
 *   Order Service --> Auth Server --> Fetch token --> Cache token
 *   Order Service --> Payment Service --> 200 OK
 *
 * Next API calls (before refresh threshold):
 *   Order Service --> Reuse cached token --> Payment Service
 *   No additional token request is needed.
 *
 * Token approaching expiry:
 *   TokenCache detects expiry - 500 ms
 *          |
 *          v
 *   Fetch a new token --> Replace cached token --> Continue API calls
 *
 * ================================================================
 * IMPORTANT DISTINCTION
 * ================================================================
 *
 * Authentication: Is the client allowed to obtain a token?
 *                 Checked by the Auth Server.
 *
 * Authorization:  Can the token access the requested resource?
 *                 Checked by the Payment Service.
 *
 * 401 = Missing, invalid, or expired token.
 * 403 = Valid token, but insufficient permissions (scope).
 *
 * No human login is involved in Client Credentials flow.
 * In production, use HTTPS and store client secrets securely.
 */
 */
public class ClientCredentialsDemo {

    static final AtomicInteger tokenRequests = new AtomicInteger();

    // ------------------------------------------------------------- AUTH SERVER
    record IssuedToken(String clientId, String scope, long expiresAtMillis) {
    }

    static final Map<String, IssuedToken> issued = new ConcurrentHashMap<>();
    static final Map<String, String> REGISTERED_CLIENTS = Map.of("order-service", "order-secret");   // client_id -> secret
    static final long TTL_MILLIS = 2000;

    static Map<String, String> form(String body) {
        Map<String, String> m = new HashMap<>();
        for (String pair : body.split("&")) {
            String[] kv = pair.split("=", 2);
            m.put(URLDecoder.decode(kv[0], StandardCharsets.UTF_8), kv.length > 1 ? URLDecoder.decode(kv[1], StandardCharsets.UTF_8) : "");
        }
        return m;
    }

    static void reply(HttpExchange ex, int status, String body) throws IOException {
        byte[] b = body.getBytes(StandardCharsets.UTF_8);
        ex.sendResponseHeaders(status, b.length);
        ex.getResponseBody().write(b);
        ex.close();
    }

    static void tokenEndpoint(HttpExchange ex) throws IOException {
        Map<String, String> f = form(new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
        if (!"client_credentials".equals(f.get("grant_type"))) {
            reply(ex, 400, "{\"error\":\"unsupported_grant_type\"}");
            return;
        }
        String secret = REGISTERED_CLIENTS.get(f.get("client_id"));
        if (secret == null || !secret.equals(f.get("client_secret"))) {
            reply(ex, 401, "{\"error\":\"invalid_client\"}");
            return;
        }
        tokenRequests.incrementAndGet();
        String token = UUID.randomUUID().toString().substring(0, 8);
        issued.put(token, new IssuedToken(f.get("client_id"), f.getOrDefault("scope", ""), System.currentTimeMillis() + TTL_MILLIS));
        reply(ex, 200, "{\"access_token\":\"" + token + "\",\"token_type\":\"Bearer\",\"expires_in\":" + TTL_MILLIS / 1000 + "}");
    }

    // ------------------------------------------------------------- RESOURCE SERVER (payment-service)
    static void paymentEndpoint(HttpExchange ex) throws IOException {
        String h = ex.getRequestHeaders().getFirst("Authorization");
        IssuedToken t = (h != null && h.startsWith("Bearer ")) ? issued.get(h.substring(7)) : null;
        if (t == null) {
            reply(ex, 401, "401 unknown token");
        } else if (System.currentTimeMillis() > t.expiresAtMillis()) {
            reply(ex, 401, "401 token expired");
        } else if (!t.scope().contains("payments:read")) {
            reply(ex, 403, "403 missing scope payments:read");
        } else {
            reply(ex, 200, "200 payments data for client " + t.clientId());
        }
    }

    // ------------------------------------------------------------- CLIENT (order-service) with a token cache
    static class TokenCache {
        private final HttpClient http = HttpClient.newHttpClient();
        private final String tokenUrl, clientId, clientSecret, scope;
        private String token;
        private long expiresAt;

        TokenCache(String tokenUrl, String clientId, String clientSecret, String scope) {
            this.tokenUrl = tokenUrl;
            this.clientId = clientId;
            this.clientSecret = clientSecret;
            this.scope = scope;
        }

        synchronized String get() throws Exception {
            if (token == null || System.currentTimeMillis() > expiresAt - 500) {      // refresh 500 ms BEFORE expiry
                String body = "grant_type=client_credentials&client_id=" + clientId + "&client_secret=" + clientSecret + "&scope=" + scope;
                HttpResponse<String> r = http.send(HttpRequest.newBuilder(URI.create(tokenUrl))
                        .header("Content-Type", "application/x-www-form-urlencoded")
                        .POST(HttpRequest.BodyPublishers.ofString(body)).build(), HttpResponse.BodyHandlers.ofString());
                if (r.statusCode() != 200) throw new IllegalStateException("token request failed: " + r.body());
                token = r.body().replaceAll(".*\"access_token\":\"([^\"]+)\".*", "$1");
                expiresAt = System.currentTimeMillis() + Long.parseLong(r.body().replaceAll(".*\"expires_in\":(\\d+).*", "$1")) * 1000;
                System.out.println("      (fetched NEW token " + token + ")");
            }
            return token;
        }
    }

    public static void main(String[] args) throws Exception {

        /*
            *                         START
            *                           |
            *                           v
            *              +--------------------------+
            *              | Create HTTP Server       |
            *              | Bind to 127.0.0.1        |
            *              | Random available port    |
            *              +------------+-------------+
            *                           |
            *                           v
            *              +--------------------------+
            *              | Register Endpoints       |
            *              | /oauth/token             |
            *              | /payments                |
            *              +------------+-------------+
            *                           |
            *                           v
            *              +--------------------------+
            *              | Start Server             |
            *              | Create HttpClient        |
            *              +------------+-------------+
        */
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/oauth/token", ClientCredentialsDemo::tokenEndpoint);
        server.createContext("/payments", ClientCredentialsDemo::paymentEndpoint);
        server.start();
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        HttpClient http = HttpClient.newHttpClient();

        try {
        /**
             *       +-----------------------------------------+
             *       | TEST 1: Wrong Client Secret             |
             *       |                                         |
             *       | TokenCache.get()                        |
             *       |       |                                 |
             *       |       v                                 |
             *       | Auth Server validates credentials       |
             *       |       |                                 |
             *       |       v                                 |
             *       | Invalid secret -> HTTP 401              |
             *       | Exception caught and printed            |
             *       +--------------------+--------------------+                         
             *                            
         * 
        */
            System.out.println("1) Wrong client secret -> auth server refuses");
            TokenCache bad = new TokenCache(base + "/oauth/token", "order-service", "WRONG", "payments:read");
            try {
                bad.get();
            } catch (IllegalStateException e) {
                System.out.println("   " + e.getMessage());
            }

            /**
            *       +-----------------------------------------+
            *       | TEST 2: Correct Credentials             |
            *       |                                         |
            *       | Create TokenCache                       |
            *       |       |                                 |
            *       |       v                                 |
            *       | Fetch access token (first call)         |
            *       |       |                                 |
            *       |       v                                 |
            *       | Cache token                             |
            *       |       |                                 |
            *       |       v                                 |
            *       | Call /payments three times              |
            *       |       |                                 |
            *       |       v                                 |
            *       | Same token reused -> 200 OK x 3         |
            *       | Token requests = 1                      |
            *       +--------------------+--------------------+
            * 
            */
            System.out.println("\n2) Correct credentials, token is cached and reused");
            TokenCache cache = new TokenCache(base + "/oauth/token", "order-service", "order-secret", "payments:read");
            for (int i = 1; i <= 3; i++) {
                System.out.println("   call " + i + " -> " + callPayments(http, base, cache.get()));
            }
            System.out.println("   token requests so far: " + tokenRequests.get() + " (3 API calls, 1 token)");

            /**
            *       +-----------------------------------------+
            *       | TEST 3: Token Expiry                    |
            *       |                                         |
            *       | Thread.sleep(2200)                      |
            *       |       |                                 |
            *       |       v                                 |
            *       | Cached token is near/past expiry        |
            *       |       |                                 |
            *       |       v                                 |
            *       | TokenCache.get() fetches new token      |
            *       |       |                                 |
            *       |       v                                 |
            *       | Call /payments -> 200 OK                |
            *       +--------------------+--------------------+
            * 
            */
            System.out.println("\n3) Wait for expiry; the cache fetches a fresh token automatically");
            Thread.sleep(2200);
            System.out.println("   call 4 -> " + callPayments(http, base, cache.get()));
            /**
            *       +-----------------------------------------+
            *       | TEST 4: Insufficient Scope              |
            *       |                                         |
            *       | Request token with inventory:read       |
            *       |       |                                 |
            *       |       v                                 |
            *       | Call /payments with that token          |
            *       |       |                                 |
            *       |       v                                 |
            *       | Missing payments:read scope             |
            *       |       |                                 |
            *       |       v                                 |
            *       | HTTP 403 Forbidden                      |
            *       +--------------------+--------------------+
            * 
            */
            System.out.println("\n4) Client asks for a smaller scope than the API needs -> 403");
            TokenCache narrow = new TokenCache(base + "/oauth/token", "order-service", "order-secret", "inventory:read");
            System.out.println("   call   -> " + callPayments(http, base, narrow.get()));

            /**
            *       +-----------------------------------------+
            *       | TEST 5: Use an Expired Token            |
            *       |                                         |
            *       | Get current cached token                |
            *       |       |                                 |
            *       |       v                                 |
            *       | Wait 2200 ms                            |
            *       |       |                                 |
            *       |       v                                 |
            *       | Send old token directly                 |
            *       | (bypasses TokenCache refresh)           |
            *       |       |                                 |
            *       |       v                                 |
            *       | HTTP 401 Unauthorized                   |
            *       +--------------------+--------------------+
            * 
            */
            System.out.println("\n5) Using an expired token directly -> 401");
            String old = cache.get();
            Thread.sleep(2200);
            System.out.println("   call   -> " + callPayments(http, base, old));

            System.out.println("\nSecrets: client_secret lives in a secret store / env var, never in git (see SecretsDemo.java).");
        } finally {
            server.stop(0);
            System.exit(0);
        }
    }

    static String callPayments(HttpClient http, String base, String token) throws Exception {
        return http.send(HttpRequest.newBuilder(URI.create(base + "/payments")).header("Authorization", "Bearer " + token).build(),
                HttpResponse.BodyHandlers.ofString()).body();
    }
}
