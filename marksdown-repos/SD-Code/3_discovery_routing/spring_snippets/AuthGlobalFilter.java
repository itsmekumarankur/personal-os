package com.example.snippets;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.UUID;

/**
 * Topic 26: a custom gateway filter (edge authentication + request id). NOT compiled in the sandbox it was written in.
 * Runs for EVERY route. Gateway code is reactive (Mono), not blocking.
 *
 * In real life prefer Spring Security's OAuth2 resource server on the gateway to validate JWTs properly
 * (see the security zip); this filter only shows the filter mechanism.
 */
@Component
public class AuthGlobalFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getURI().getPath();
        if (path.startsWith("/public/")) {
            return chain.filter(exchange);                       // open endpoints skip the check
        }

        String auth = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (auth == null || !auth.startsWith("Bearer ")) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();         // stop here: backend never sees the request
        }

        ServerHttpRequest withTraceId = exchange.getRequest().mutate()
                .header("X-Request-Id", UUID.randomUUID().toString())
                .build();
        return chain.filter(exchange.mutate().request(withTraceId).build());   // continue to the route
    }

    @Override
    public int getOrder() {
        return -1;                                               // run before the built-in routing filters
    }
}
