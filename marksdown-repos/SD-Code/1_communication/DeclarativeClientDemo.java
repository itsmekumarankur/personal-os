import com.sun.net.httpserver.HttpServer;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

/**
 * 
FEIGN-STYLE DECLARATIVE CLIENTS - how "just write an interface" works

We are learning how Feign-style declarative clients allow one service to call another service by simply calling a Java interface method, 
without writing the HTTP communication code each time. 
A proxy object is automatically created at runtime; it reads annotations such as @GET and @POST, builds the HTTP request,
 sends it to the remote service, and returns the response. 
In simple words: write an interface, call a method, and the proxy handles the HTTP communication behind the scenes.
        Application Code
              |
              v
    client.getPrice("INFY")
              |
              v
    PricingClient Interface
       @GET("/prices/{symbol}")
              |
              v
       Generated Proxy
      (Java Reflection)
              |
              v
       Builds HTTP Request
    GET /prices/INFY
              |
              v
       HTTP Client
              |
              v
       Pricing Service
              |
              v
        HTTP Response
       {"price":1523.40}
              |
              v
       Proxy returns result
              |
              v
       Application receives
          the response
 */
public class DeclarativeClientDemo {

    // ---- our own tiny annotations (Feign / Spring MVC provide the real ones) ----
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface GET {
        String value();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface POST {
        String value();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.PARAMETER)
    @interface PathVar {
        String value();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.PARAMETER)
    @interface Body {
    }

    // ---- THE CLIENT: only a contract, no code ----
    interface PricingClient {
        @GET("/prices/{symbol}")
        String getPrice(@PathVar("symbol") String symbol);

        @POST("/quotes")
        String requestQuote(@Body String json);
    }

    // ---- the "framework": turns an annotated interface into a working client ----
    @SuppressWarnings("unchecked")
    static <T> T createClient(Class<T> api, String baseUrl) {
        HttpClient http = HttpClient.newHttpClient();
        return (T) Proxy.newProxyInstance(api.getClassLoader(), new Class<?>[]{api}, (proxy, method, args) -> {
            if (method.getDeclaringClass() == Object.class) {
                return "proxy-of-" + api.getSimpleName();
            }
            HttpRequest.Builder request;
            if (method.isAnnotationPresent(GET.class)) {
                String path = fillPathVariables(method, args, method.getAnnotation(GET.class).value());
                request = HttpRequest.newBuilder(URI.create(baseUrl + path)).GET();
            } else {
                String path = method.getAnnotation(POST.class).value();
                String body = findBody(method, args);
                request = HttpRequest.newBuilder(URI.create(baseUrl + path))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body));
            }
            System.out.println("  [proxy] " + method.getName() + "() became an HTTP call");
            return http.send(request.build(), HttpResponse.BodyHandlers.ofString()).body();
        });
    }

    static String fillPathVariables(Method m, Object[] args, String template) {
        var paramAnnotations = m.getParameterAnnotations();
        for (int i = 0; i < args.length; i++) {
            for (var a : paramAnnotations[i]) {
                if (a instanceof PathVar pv) {
                    template = template.replace("{" + pv.value() + "}", String.valueOf(args[i]));
                }
            }
        }
        return template;
    }

    static String findBody(Method m, Object[] args) {
        var paramAnnotations = m.getParameterAnnotations();
        for (int i = 0; i < args.length; i++) {
            for (var a : paramAnnotations[i]) {
                if (a instanceof Body) {
                    return String.valueOf(args[i]);
                }
            }
        }
        return "";
    }

    public static void main(String[] args) throws Exception {
        // a fake pricing service to talk to
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/prices/", ex -> {
            String path = ex.getRequestURI().getPath();
            byte[] out = ("{\"requested\":\"" + path + "\",\"price\":1523.40}").getBytes(StandardCharsets.UTF_8);
            ex.sendResponseHeaders(200, out.length);
            ex.getResponseBody().write(out);
            ex.close();
        });
        server.createContext("/quotes", ex -> {
            String in = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            byte[] out = ("{\"quoteFor\":" + in + ",\"valid\":true}").getBytes(StandardCharsets.UTF_8);
            ex.sendResponseHeaders(201, out.length);
            ex.getResponseBody().write(out);
            ex.close();
        });
        server.start();
        String baseUrl = "http://127.0.0.1:" + server.getAddress().getPort();

        // Using the client: looks like a normal method call
        PricingClient client = createClient(PricingClient.class, baseUrl);
        System.out.println("Client object is a generated proxy: " + client);

        System.out.println("\nclient.getPrice(\"INFY\"):");
        System.out.println("  response: " + client.getPrice("INFY"));

        System.out.println("\nclient.requestQuote(json):");
        System.out.println("  response: " + client.requestQuote("{\"symbol\":\"INFY\",\"qty\":5}"));

        System.out.println("\nWhy teams like it: the interface IS the documentation of the remote API, and the HTTP plumbing "
                + "(URL building, headers, serialization, timeouts, retries) lives in one place.");
        server.stop(0);
    }
}
