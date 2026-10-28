import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URI;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 1. Spring MVC pieces from MvcRequestLifecycleDemo. NOT compiled or run by the author.
 * Dependency: spring-boot-starter-web
 */
class OrderNotFoundException extends RuntimeException {
    OrderNotFoundException(long id) { super("order " + id + " does not exist"); }
}

@RestController
@RequestMapping("/orders")
class OrderController {
    @GetMapping("/{id}")                                         // HandlerMapping
    Order get(@PathVariable long id) {                           // HandlerAdapter converts "7" -> long
        if (id > 100) throw new OrderNotFoundException(id);
        return new Order(id, "INFY");
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    Order create(@RequestBody CreateOrder body) {                // HttpMessageConverter: JSON -> object (Jackson)
        return new Order(1, body.symbol());
    }

    record Order(long id, String symbol) { }
    record CreateOrder(String symbol, int qty) { }
}

/** Complaints desk: one place that turns exceptions into clean HTTP responses. */
@RestControllerAdvice
class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail notFound(OrderNotFoundException e) {
        ProblemDetail p = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, e.getMessage());
        p.setType(URI.create("https://api.example.com/problems/not-found"));
        return p;
    }

    @ExceptionHandler(Exception.class)                           // safety net: never leak internals
    ProblemDetail unexpected(Exception e) {
        log.error("Unhandled exception", e);                      // full detail in the server log only
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Something went wrong");
    }
}

/** FILTER: servlet level, runs for EVERY request, before Spring MVC. Good for correlation ids, auth, CORS. */
@Component
class RequestIdFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
        String id = java.util.UUID.randomUUID().toString();
        res.setHeader("X-Request-Id", id);
        org.slf4j.MDC.put("requestId", id);
        try { chain.doFilter(req, res); } finally { org.slf4j.MDC.clear(); }
    }
}

/** INTERCEPTOR: MVC level, only for matched handlers, knows the handler method. Good for auditing, per-endpoint rules. */
@Component
class AuditInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        // return false to stop the request here
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res, Object handler, Exception ex) {
        // runs after the response is produced, even if the controller threw
    }
}

@Configuration
class WebConfig implements WebMvcConfigurer {
    private final AuditInterceptor audit;
    WebConfig(AuditInterceptor audit) { this.audit = audit; }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(audit).addPathPatterns("/orders/**");
    }
}
