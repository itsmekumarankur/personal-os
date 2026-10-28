import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
TOPIC: API VERSIONING AND CONTRACT DESIGN

                OLD CLIENT
                    |
                    | GET /v1/accounts/42
                    v
             +----------------+
             | ACCOUNT SERVICE|
             +----------------+
                    |
                    v
       {"id":42,"balance":1000}
                    |
                    v
             OLD CLIENT WORKS
                    |
                    v
       SAFE CHANGE: ADD status field
       {"id":42,"balance":1000,"status":"ACTIVE"}
                    |
                    v
             OLD CLIENT STILL WORKS
             (ignores unknown fields)


BREAKING CHANGE:
================

             OLD CLIENT
                    |
                    | Expects balance = number
                    v
       {"balance":{"amount":1000,"currency":"INR"}}
                    |
                    v
                CLIENT BREAKS!
          (expected number, got object)


CORRECT SOLUTION:
=================

       OLD CLIENT                  NEW CLIENT
           |                           |
           v                           v
     GET /v1/...                 GET /v2/...
           |                           |
           v                           v
     +-----------+               +-----------+
     |   /v1     |               |    /v2    |
     | balance:  |               | balance:  |
     |   1000    |               | {amount:  |
     |           |               |  1000,    |
     |           |               | currency: |
     |           |               |  "INR"}    |
     +-----------+               +-----------+
           |                           |
           v                           v
       OLD CLIENT                  NEW CLIENT
       STILL WORKS                 WORKS


REMEMBER:
=========
    SAFE CHANGE    = Add an optional field.
    BREAKING CHANGE = Rename/remove a field, change its type or meaning.
    VERSIONING     = Keep /v1 working; introduce /v2 for breaking changes.
    DEPRECATION    = Warn clients that /v1 will eventually be retired.

 */
public class ApiVersioningDemo {

    static boolean v1HasExtraStatusField = false;       // flips during the demo (a SAFE change)

    static void reply(HttpExchange ex, int status, String json, String... headers) throws IOException {
        byte[] body = json.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().add("Content-Type", "application/json");
        for (int i = 0; i < headers.length; i += 2) {
            ex.getResponseHeaders().add(headers[i], headers[i + 1]);
        }
        ex.sendResponseHeaders(status, body.length);
        ex.getResponseBody().write(body);
        ex.close();
    }

    static HttpServer startAccountService() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);

        // v1: balance is a plain number
        server.createContext("/v1/accounts/42", ex -> {
            String extra = v1HasExtraStatusField ? ",\"status\":\"ACTIVE\"" : "";
            reply(ex, 200, "{\"id\":42,\"name\":\"Ankur\",\"balance\":1000" + extra + "}",
                    "Deprecation", "true",
                    "Sunset", "Sat, 31 Oct 2027 00:00:00 GMT",
                    "Link", "</v2/accounts/42>; rel=\"successor-version\"");
        });

        // v2: BREAKING change, balance became an object with a currency
        server.createContext("/v2/accounts/42", ex ->
                reply(ex, 200, "{\"id\":42,\"name\":\"Ankur\",\"balance\":{\"amount\":1000,\"currency\":\"INR\"}}"));

        server.start();
        return server;
    }

    // ---- an OLD client written against v1: expects balance to be a number ----
    static String oldClientReadsBalance(String json) {
        Matcher name = Pattern.compile("\"name\"\\s*:\\s*\"([^\"]+)\"").matcher(json);
        Matcher balance = Pattern.compile("\"balance\"\\s*:\\s*(\\d+)").matcher(json);   // number only!
        if (!name.find() || !balance.find()) {
            return "CLIENT BROKEN: could not parse response";
        }
        return "client shows: " + name.group(1) + " has balance " + balance.group(1);
    }

    // ---- a NEW client written against v2 ----
    static String newClientReadsBalance(String json) {
        Matcher amount = Pattern.compile("\"amount\"\\s*:\\s*(\\d+)").matcher(json);
        Matcher currency = Pattern.compile("\"currency\"\\s*:\\s*\"([^\"]+)\"").matcher(json);
        if (!amount.find() || !currency.find()) {
            return "CLIENT BROKEN: could not parse response";
        }
        return "client shows: balance " + amount.group(1) + " " + currency.group(1);
    }

    public static void main(String[] args) throws Exception {
        HttpServer server = startAccountService();
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        HttpClient http = HttpClient.newHttpClient();

        System.out.println("1) Old client calls /v1:");
        HttpResponse<String> r1 = http.send(HttpRequest.newBuilder(URI.create(base + "/v1/accounts/42")).build(),
                HttpResponse.BodyHandlers.ofString());
        System.out.println("   body: " + r1.body());
        System.out.println("   headers: Deprecation=" + r1.headers().firstValue("Deprecation").orElse("-")
                + ", Sunset=" + r1.headers().firstValue("Sunset").orElse("-")
                + ", Link=" + r1.headers().firstValue("Link").orElse("-"));
        System.out.println("   " + oldClientReadsBalance(r1.body()));

        System.out.println("\n2) SAFE change: server ADDS an optional 'status' field to /v1. Old client is a tolerant reader:");
        v1HasExtraStatusField = true;
        HttpResponse<String> r2 = http.send(HttpRequest.newBuilder(URI.create(base + "/v1/accounts/42")).build(),
                HttpResponse.BodyHandlers.ofString());
        System.out.println("   body: " + r2.body());
        System.out.println("   " + oldClientReadsBalance(r2.body()) + "   <- still works");

        System.out.println("\n3) BREAKING change shipped on the SAME path (what NOT to do): old client reads the v2 shape:");
        HttpResponse<String> r3 = http.send(HttpRequest.newBuilder(URI.create(base + "/v2/accounts/42")).build(),
                HttpResponse.BodyHandlers.ofString());
        System.out.println("   body: " + r3.body());
        System.out.println("   " + oldClientReadsBalance(r3.body()));

        System.out.println("\n4) The right way: breaking shape lives at /v2, new client opts in, /v1 stays until clients migrate:");
        System.out.println("   " + newClientReadsBalance(r3.body()));

        System.out.println("\nVersioning styles: URL (/v1/..) is simplest and most visible; header (Accept: application/vnd.bank.v2+json) "
                + "keeps URLs clean. Pick one and be consistent.");
        server.stop(0);
    }
}
