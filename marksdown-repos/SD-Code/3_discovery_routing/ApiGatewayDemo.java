import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Executors;

/**
 * 26. API GATEWAY - the single front door
 *
 * Clients talk to ONE address. The gateway then:
 *   1. gives every request an id (for tracing)
 *   2. checks WHO you are (authentication) once, at the edge
 *   3. ROUTES by path: /orders/** -> orders-service, /payments/** -> payments-service
 *   4. protects with a timeout (slow service -> 504 instead of hanging the client)
 *   5. passes identity downstream (X-User header)
 * Other typical gateway jobs: rate limiting, TLS termination, CORS, response caching, circuit breaking.
 *
 * Here the gateway and two backend services are real HTTP servers in one program.
 * Spring Cloud Gateway version: spring_snippets/
 *
 * Run: java ApiGatewayDemo.java
 */
public class ApiGatewayDemo {

    static final Map<String, String> VALID_TOKENS = Map.of("Bearer token-ankur", "ankur");

    static void reply(HttpExchange ex, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().add("Content-Type", "application/json");
        ex.sendResponseHeaders(status, bytes.length);
        ex.getResponseBody().write(bytes);
        ex.close();
    }

    static String header(HttpExchange ex, String name) {
        String v = ex.getRequestHeaders().getFirst(name);
        return v == null ? "none" : v;
    }

    // ------------------------------------------------------------ a backend microservice
    static HttpServer startBackend(String name) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.setExecutor(Executors.newCachedThreadPool());
        server.createContext("/", ex -> {
            String path = ex.getRequestURI().getPath();
            if (path.endsWith("/slow")) {
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException ignored) {
                }
            }
            String requestBody = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            reply(ex, ex.getRequestMethod().equals("POST") ? 201 : 200,
                    "{\"servedBy\":\"" + name + "\",\"path\":\"" + path + "\",\"authenticatedUser\":\""
                            + header(ex, "X-User") + "\",\"requestId\":\"" + header(ex, "X-Request-Id")
                            + "\",\"receivedBody\":\"" + requestBody.replace("\"", "'") + "\"}");
        });
        server.start();
        return server;
    }

    // ------------------------------------------------------------ the gateway
    static HttpServer startGateway(Map<String, String> routes) throws IOException {
        HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofMillis(300)).build();
        HttpServer gateway = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        gateway.setExecutor(Executors.newCachedThreadPool());

        gateway.createContext("/", ex -> {
            String requestId = UUID.randomUUID().toString().substring(0, 8);
            String path = ex.getRequestURI().getPath();
            String method = ex.getRequestMethod();

            // (a) an open endpoint handled by the gateway itself
            if (path.equals("/public/health")) {
                reply(ex, 200, "{\"gateway\":\"UP\"}");
                return;
            }

            // (b) authentication at the edge
            String authorization = ex.getRequestHeaders().getFirst("Authorization");
            String user = authorization == null ? null : VALID_TOKENS.get(authorization);   // Map.of(...).get(null) would throw
            if (user == null) {
                System.out.println("    [gateway " + requestId + "] " + method + " " + path + " -> 401 (no valid token)");
                reply(ex, 401, "{\"error\":\"missing or invalid token\"}");
                return;
            }

            // (c) routing by first path segment
            String[] segments = path.split("/");                       // "/orders/1" -> ["", "orders", "1"]
            String backend = segments.length > 1 ? routes.get(segments[1]) : null;
            if (backend == null) {
                System.out.println("    [gateway " + requestId + "] " + method + " " + path + " -> 404 (no route)");
                reply(ex, 404, "{\"error\":\"no route for " + path + "\"}");
                return;
            }

            // (d) forward, adding identity + trace id, with a timeout
            byte[] body = ex.getRequestBody().readAllBytes();
            HttpRequest forward = HttpRequest.newBuilder(URI.create(backend + path))
                    .timeout(Duration.ofMillis(500))
                    .header("X-User", user)
                    .header("X-Request-Id", requestId)
                    .method(method, body.length == 0 ? HttpRequest.BodyPublishers.noBody()
                            : HttpRequest.BodyPublishers.ofByteArray(body))
                    .build();
            try {
                HttpResponse<String> response = client.send(forward, HttpResponse.BodyHandlers.ofString());
                System.out.println("    [gateway " + requestId + "] " + method + " " + path + " -> " + segments[1]
                        + "-service answered " + response.statusCode());
                reply(ex, response.statusCode(), response.body());
            } catch (HttpTimeoutException e) {
                System.out.println("    [gateway " + requestId + "] " + method + " " + path + " -> 504 (backend too slow)");
                reply(ex, 504, "{\"error\":\"upstream timed out\"}");
            } catch (Exception e) {
                reply(ex, 502, "{\"error\":\"bad gateway\"}");
            }
        });
        gateway.start();
        return gateway;
    }

    static void call(HttpClient client, String base, String label, String method, String path, String token, String body) throws Exception {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(base + path))
                .method(method, body == null ? HttpRequest.BodyPublishers.noBody() : HttpRequest.BodyPublishers.ofString(body));
        if (token != null) {
            b.header("Authorization", token);
        }
        HttpResponse<String> r = client.send(b.build(), HttpResponse.BodyHandlers.ofString());
        System.out.println(label + "\n    -> HTTP " + r.statusCode() + "  " + r.body() + "\n");
    }

    public static void main(String[] args) throws Exception {
        HttpServer orders = startBackend("orders-service");
        HttpServer payments = startBackend("payments-service");
        HttpServer gateway = startGateway(Map.of(
                "orders", "http://127.0.0.1:" + orders.getAddress().getPort(),
                "payments", "http://127.0.0.1:" + payments.getAddress().getPort()));
        String base = "http://127.0.0.1:" + gateway.getAddress().getPort();
        HttpClient client = HttpClient.newHttpClient();

        try {
            System.out.println("Everything below goes through ONE address: " + base + "\n");
            call(client, base, "1) GET /public/health, no token needed", "GET", "/public/health", null, null);
            call(client, base, "2) GET /orders/1 WITHOUT a token", "GET", "/orders/1", null, null);
            call(client, base, "3) GET /orders/1 with a token, routed to orders-service", "GET", "/orders/1", "Bearer token-ankur", null);
            call(client, base, "4) POST /payments/pay with a token, routed to payments-service", "POST", "/payments/pay", "Bearer token-ankur", "{\"amount\":500}");
            call(client, base, "5) GET /payments/slow, backend takes 2 s, gateway gives up after 500 ms", "GET", "/payments/slow", "Bearer token-ankur", null);
            call(client, base, "6) GET /reports/1, nothing routed here", "GET", "/reports/1", "Bearer token-ankur", null);

            System.out.println("Note: still validate the token INSIDE each service too (defence in depth). The gateway is not a substitute for service security.");
        } finally {
            System.exit(0);          // the servers use non-daemon threads, so exit explicitly
        }
    }
}
