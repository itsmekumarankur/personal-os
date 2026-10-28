import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 1. SPRING MVC REQUEST LIFECYCLE - "what happens between the browser and my @RestController method?"
 *
 * Think of a hospital:
 *   FILTER            = security gate at the hospital entrance. Runs BEFORE Spring MVC even starts.
 *   DISPATCHER SERVLET= the reception desk. Receives every request and routes it.
 *   HANDLER MAPPING   = the directory: "/orders/7 -> OrderController.get()"
 *   INTERCEPTOR       = the ward nurse: checks before (preHandle) and after (afterCompletion) the doctor sees you.
 *   HANDLER ADAPTER   = fills in the doctor's form: turns "7" in the URL into int id, JSON body into an object.
 *   CONTROLLER        = the doctor (your code).
 *   MESSAGE CONVERTER = writes the report: Java object -> JSON.
 *   EXCEPTION HANDLER = the complaints desk (@ControllerAdvice / @ExceptionHandler): turns a thrown
 *                       exception into a clean 404/400 instead of a stack trace.
 *
 * This file is a ~120-line imitation of that machinery (annotations + reflection), so you can SEE each stage.
 * Real Spring version: spring_snippets/MvcSnippets.java
 *
 * Run: java MvcRequestLifecycleDemo.java
 */
public class MvcRequestLifecycleDemo {

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD) @interface Get { String value(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD) @interface Post { String value(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.PARAMETER) @interface PathVar { String value(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.PARAMETER) @interface Body { }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD) @interface Handles { Class<? extends Exception> value(); int status(); }

    record Request(String method, String path, Map<String, String> headers, String body) { }

    static class Response { int status = 200; String body = ""; }

    interface Filter { void doFilter(Request rq, Response rs, Runnable next); }

    interface Interceptor {
        boolean preHandle(Request rq, Response rs);
        void afterCompletion(Request rq, Response rs, Exception ex);
    }

    static class NotFound extends RuntimeException { NotFound(String m) { super(m); } }
    static class BadInput extends RuntimeException { BadInput(String m) { super(m); } }

    static void step(String who, String what) { System.out.printf("      %-22s %s%n", who, what); }

    static Map<String, Object> m(Object... kv) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (int i = 0; i < kv.length; i += 2) map.put((String) kv[i], kv[i + 1]);
        return map;
    }

    // ------------------------------------------------------------------ the application code (what YOU write)
    static class OrderController {
        @Get("/orders/{id}")
        public Map<String, Object> get(@PathVar("id") int id) {
            if (id > 100) throw new NotFound("order " + id + " does not exist");
            return m("id", id, "symbol", "INFY");
        }

        @Post("/orders")
        public Map<String, Object> create(@Body Map<String, String> body) {
            if (!body.containsKey("qty")) throw new BadInput("qty is required");
            return m("created", true, "qty", body.get("qty"));
        }

        @Get("/boom")
        public String boom() { throw new IllegalStateException("jdbc:postgresql://prod-db user=app password=hunter2"); }

        @Handles(value = NotFound.class, status = 404)
        public Map<String, Object> onNotFound(Exception e) { return m("error", "NOT_FOUND", "message", e.getMessage()); }

        @Handles(value = BadInput.class, status = 400)
        public Map<String, Object> onBadInput(Exception e) { return m("error", "BAD_REQUEST", "message", e.getMessage()); }
    }

    // ------------------------------------------------------------------ the framework (what SPRING does for you)
    static class Dispatcher {
        record Route(String httpMethod, Pattern pattern, List<String> varNames, Method method) { }

        final Object controller;
        final List<Route> routes = new ArrayList<>();
        final List<Interceptor> interceptors;

        Dispatcher(Object controller, List<Interceptor> interceptors) {
            this.controller = controller;
            this.interceptors = interceptors;
            for (Method md : controller.getClass().getDeclaredMethods()) {          // startup: build the "directory"
                if (md.isAnnotationPresent(Get.class)) routes.add(route("GET", md.getAnnotation(Get.class).value(), md));
                if (md.isAnnotationPresent(Post.class)) routes.add(route("POST", md.getAnnotation(Post.class).value(), md));
            }
        }

        static Route route(String http, String template, Method md) {
            List<String> names = new ArrayList<>();
            Matcher nm = Pattern.compile("\\{(\\w+)}").matcher(template);
            while (nm.find()) names.add(nm.group(1));
            return new Route(http, Pattern.compile(template.replaceAll("\\{\\w+}", "([^/]+)")), names, md);
        }

        void service(Request rq, Response rs) {
            step("DispatcherServlet", "received " + rq.method() + " " + rq.path());
            Route route = null;
            Matcher match = null;
            for (Route r : routes) {
                Matcher mt = r.pattern().matcher(rq.path());
                if (r.httpMethod().equals(rq.method()) && mt.matches()) { route = r; match = mt; break; }
            }
            if (route == null) {
                rs.status = 404; rs.body = "{\"error\":\"NO_HANDLER\"}";
                step("HandlerMapping", "no controller method matches -> 404");
                return;
            }
            step("HandlerMapping", "matched OrderController." + route.method().getName() + "()");
            for (Interceptor i : interceptors) i.preHandle(rq, rs);

            Exception failure = null;
            try {
                Object[] args = resolveArguments(route, match, rq);
                step("HandlerAdapter", "resolved arguments " + Arrays.toString(args));
                Object result = route.method().invoke(controller, args);
                rs.body = toJson(result);
                step("MessageConverter", "return value -> JSON " + rs.body);
            } catch (InvocationTargetException e) {
                failure = (Exception) e.getCause();
                resolveException(failure, rs);
            } catch (Exception e) {
                failure = e;
                resolveException(e, rs);
            }
            List<Interceptor> reversed = new ArrayList<>(interceptors);
            Collections.reverse(reversed);
            for (Interceptor i : reversed) i.afterCompletion(rq, rs, failure);
        }

        Object[] resolveArguments(Route route, Matcher match, Request rq) {
            Parameter[] params = route.method().getParameters();
            Object[] args = new Object[params.length];
            for (int i = 0; i < params.length; i++) {
                PathVar pv = params[i].getAnnotation(PathVar.class);
                if (pv != null) {
                    String raw = match.group(route.varNames().indexOf(pv.value()) + 1);
                    args[i] = params[i].getType() == int.class ? Integer.parseInt(raw) : raw;   // type conversion
                } else if (params[i].isAnnotationPresent(Body.class)) {
                    Map<String, String> body = new LinkedHashMap<>();
                    Matcher jm = Pattern.compile("\"(\\w+)\"\\s*:\\s*\"?([^\",}]*)\"?").matcher(rq.body() == null ? "" : rq.body());
                    while (jm.find()) body.put(jm.group(1), jm.group(2));
                    args[i] = body;                                                               // JSON -> object
                }
            }
            return args;
        }

        void resolveException(Exception ex, Response rs) {
            for (Method md : controller.getClass().getDeclaredMethods()) {
                Handles h = md.getAnnotation(Handles.class);
                if (h != null && h.value().isInstance(ex)) {
                    try {
                        rs.status = h.status();
                        rs.body = toJson(md.invoke(controller, ex));
                        step("ExceptionResolver", ex.getClass().getSimpleName() + " handled by " + md.getName() + "() -> " + rs.status);
                        return;
                    } catch (Exception e) { throw new RuntimeException(e); }
                }
            }
            rs.status = 500;                                                                      // unknown: never leak details
            rs.body = "{\"error\":\"INTERNAL\",\"message\":\"Something went wrong\"}";
            step("ExceptionResolver", "no handler for " + ex.getClass().getSimpleName() + " -> generic 500 (details only in server log)");
            step("server log", "ERROR " + ex.getMessage());
        }
    }

    static String toJson(Object o) {
        if (o instanceof Map<?, ?> map) {
            StringBuilder sb = new StringBuilder("{");
            map.forEach((k, v) -> sb.append(sb.length() > 1 ? "," : "").append('"').append(k).append("\":").append(toJson(v)));
            return sb.append('}').toString();
        }
        return (o instanceof Number || o instanceof Boolean) ? String.valueOf(o) : "\"" + o + "\"";
    }

    static void runFilters(List<Filter> fs, int i, Request rq, Response rs, Runnable terminal) {
        if (i == fs.size()) { terminal.run(); return; }
        fs.get(i).doFilter(rq, rs, () -> runFilters(fs, i + 1, rq, rs, terminal));
    }

    public static void main(String[] args) {
        Filter logging = (rq, rs, next) -> {
            step("Filter:logging", "before");
            next.run();
            step("Filter:logging", "after -> status " + rs.status);
        };
        Filter auth = (rq, rs, next) -> {
            if (rq.path().startsWith("/orders") && !rq.headers().containsKey("Authorization")) {
                rs.status = 401; rs.body = "{\"error\":\"UNAUTHORIZED\"}";
                step("Filter:auth", "no token -> 401, DispatcherServlet and controller are NEVER reached");
                return;
            }
            next.run();
        };
        Interceptor audit = new Interceptor() {
            public boolean preHandle(Request rq, Response rs) { step("Interceptor:audit", "preHandle (knows the matched handler)"); return true; }
            public void afterCompletion(Request rq, Response rs, Exception ex) {
                step("Interceptor:audit", "afterCompletion status=" + rs.status + (ex == null ? "" : " exception=" + ex.getClass().getSimpleName()));
            }
        };
        List<Filter> filters = List.of(logging, auth);
        Dispatcher dispatcher = new Dispatcher(new OrderController(), List.of(audit));
        Map<String, String> token = Map.of("Authorization", "Bearer abc");

        Object[][] requests = {
                {"1) happy path", new Request("GET", "/orders/7", token, null)},
                {"2) controller throws NotFound -> mapped to 404", new Request("GET", "/orders/500", token, null)},
                {"3) JSON body converted to a Map", new Request("POST", "/orders", token, "{\"symbol\":\"INFY\",\"qty\":5}")},
                {"4) validation error -> 400", new Request("POST", "/orders", token, "{\"symbol\":\"INFY\"}")},
                {"5) unexpected bug -> safe generic 500", new Request("GET", "/boom", token, null)},
                {"6) URL nobody handles -> 404", new Request("GET", "/nothing", token, null)},
                {"7) no token -> stopped by FILTER", new Request("GET", "/orders/7", Map.of(), null)},
        };
        for (Object[] r : requests) {
            System.out.println("\n" + r[0]);
            Response rs = new Response();
            runFilters(filters, 0, (Request) r[1], rs, () -> dispatcher.service((Request) r[1], rs));
            System.out.println("   => HTTP " + rs.status + " " + rs.body);
        }
        System.out.println("\nRemember: Filter = servlet level, sees EVERY request, knows nothing about controllers (security, logging, CORS).");
        System.out.println("          Interceptor = Spring MVC level, runs only for matched handlers, can see the handler method (auditing, locale).");
    }
}
