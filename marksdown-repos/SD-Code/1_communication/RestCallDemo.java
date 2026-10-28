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
import java.util.concurrent.Executors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 1. REST BETWEEN SERVICES
 *
 * Two tiny services run inside this one program, each on its own HTTP port:
 *
 *   caller (main) --POST /orders--> order-service --GET /prices/{symbol}--> pricing-service
 *
 * order-service is both a SERVER (to the caller) and a CLIENT (to pricing-service).
 * It shows the three things every service-to-service call must handle:
 *   1. Check the HTTP status (404 is an answer, not an exception)
 *   2. Set a timeout (see the resilience zip for why)
 *   3. Translate the downstream failure into a sensible answer for ITS caller
 *
 * Uses only the JDK's built-in HttpServer and java.net.http.HttpClient.
 * In Spring you would use RestClient / WebClient (see spring_snippets/RestClientSnippets.java).
 *
 * Run: java RestCallDemo.java
 */
public class RestCallDemo {

    // ---------- tiny helpers ----------
    static void reply(HttpExchange ex, int status, String json) throws IOException {
        byte[] body = json.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().add("Content-Type", "application/json");
        ex.sendResponseHeaders(status, body.length);
        ex.getResponseBody().write(body);
        ex.close();
    }

    static String field(String json, String name) {          // super-simple JSON field reader
        Matcher m = Pattern.compile("\"" + name + "\"\\s*:\\s*\"?([^\",}]+)").matcher(json);
        return m.find() ? m.group(1) : null;
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    // ---------- service 1: pricing-service ----------
    static HttpServer startPricingService() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.setExecutor(Executors.newCachedThreadPool());
        server.createContext("/prices/", ex -> {
            String symbol = ex.getRequestURI().getPath().substring("/prices/".length());
            switch (symbol) {
                case "INFY" -> reply(ex, 200, "{\"symbol\":\"INFY\",\"price\":1523.40}");
                case "SLOWCO" -> {                              // pretend this symbol is very slow to price
                    sleep(2000);
                    reply(ex, 200, "{\"symbol\":\"SLOWCO\",\"price\":10.00}");
                }
                default -> reply(ex, 404, "{\"error\":\"unknown symbol\"}");
            }
        });
        server.start();
        return server;
    }

    // ---------- service 2: order-service (calls pricing-service) ----------
    static HttpServer startOrderService(String pricingBaseUrl) throws IOException {
        HttpClient http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(500))          // time allowed to open the connection
                .build();

        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.setExecutor(Executors.newCachedThreadPool());
        server.createContext("/orders", ex -> {
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            String symbol = field(body, "symbol");
            int qty = Integer.parseInt(field(body, "qty"));

            HttpRequest request = HttpRequest.newBuilder(URI.create(pricingBaseUrl + "/prices/" + symbol))
                    .timeout(Duration.ofMillis(500))              // total time allowed for the response
                    .GET()
                    .build();
            try {
                HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() == 404) {
                    reply(ex, 400, "{\"error\":\"cannot order unknown symbol " + symbol + "\"}");
                } else if (response.statusCode() != 200) {
                    reply(ex, 502, "{\"error\":\"pricing-service returned " + response.statusCode() + "\"}");
                } else {
                    double price = Double.parseDouble(field(response.body(), "price"));
                    reply(ex, 201, String.format("{\"symbol\":\"%s\",\"qty\":%d,\"total\":%.2f}", symbol, qty, price * qty));
                }
            } catch (HttpTimeoutException e) {
                reply(ex, 503, "{\"error\":\"pricing-service is too slow, try again later\"}");
            } catch (Exception e) {
                reply(ex, 503, "{\"error\":\"pricing-service unreachable\"}");
            }
        });
        server.start();
        return server;
    }

    public static void main(String[] args) throws Exception {
        HttpServer pricing = startPricingService();
        String pricingUrl = "http://127.0.0.1:" + pricing.getAddress().getPort();
        HttpServer orders = startOrderService(pricingUrl);
        String ordersUrl = "http://127.0.0.1:" + orders.getAddress().getPort();

        HttpClient caller = HttpClient.newHttpClient();
        String[][] cases = {
                {"Happy path", "{\"symbol\":\"INFY\",\"qty\":10}"},
                {"Unknown symbol (downstream 404)", "{\"symbol\":\"NOPE\",\"qty\":1}"},
                {"Slow dependency (timeout)", "{\"symbol\":\"SLOWCO\",\"qty\":1}"},
        };
        for (String[] c : cases) {
            HttpRequest req = HttpRequest.newBuilder(URI.create(ordersUrl + "/orders"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(c[1]))
                    .build();
            long t0 = System.currentTimeMillis();
            HttpResponse<String> resp = caller.send(req, HttpResponse.BodyHandlers.ofString());
            System.out.printf("%-34s -> HTTP %d in %4d ms  %s%n", c[0], resp.statusCode(),
                    System.currentTimeMillis() - t0, resp.body());
        }

        // Pricing service stops: connection refused
        pricing.stop(0);
        HttpRequest req = HttpRequest.newBuilder(URI.create(ordersUrl + "/orders"))
                .POST(HttpRequest.BodyPublishers.ofString("{\"symbol\":\"INFY\",\"qty\":1}")).build();
        HttpResponse<String> resp = caller.send(req, HttpResponse.BodyHandlers.ofString());
        System.out.printf("%-34s -> HTTP %d  %s%n", "Pricing service is down", resp.statusCode(), resp.body());

        orders.stop(0);
        System.exit(0);
    }
}
