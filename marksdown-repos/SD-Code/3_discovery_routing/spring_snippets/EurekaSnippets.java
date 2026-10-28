package com.example.snippets;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

/**
 * Topics 27 and 28: service registry (Eureka) and client-side load balancing.
 * NOT compiled in the sandbox it was written in. Runnable concept demos: ServiceRegistryDemo, LoadBalancerDemo.
 *
 * Three separate Spring Boot apps are involved; they are shown together here for reading.
 *
 * -------------------------------------------------------------------------------------------
 * 1) REGISTRY SERVER   (dependency: spring-cloud-starter-netflix-eureka-server)
 *
 *    application.yml
 *      server.port: 8761
 *      eureka:
 *        client:
 *          register-with-eureka: false       # the registry does not register itself
 *          fetch-registry: false
 *
 * 2) EVERY SERVICE     (dependency: spring-cloud-starter-netflix-eureka-client)
 *    It registers itself automatically under spring.application.name and sends heartbeats.
 *
 *    application.yml of orders-service
 *      spring.application.name: orders-service          # the logical name other services use
 *      eureka:
 *        client:
 *          service-url:
 *            defaultZone: http://localhost:8761/eureka
 *        instance:
 *          lease-renewal-interval-in-seconds: 10        # heartbeat every 10 s (default 30)
 *          lease-expiration-duration-in-seconds: 30     # evict after 30 s without heartbeat (default 90)
 *          prefer-ip-address: true
 *
 * Consul alternative: spring-cloud-starter-consul-discovery (same ideas, plus a key-value store and health checks).
 * On Kubernetes you often skip Eureka: the platform's Service + DNS ("http://orders-service") does discovery.
 * -------------------------------------------------------------------------------------------
 */
public class EurekaSnippets {

    // ---------------------------------------------------------------- 1) the registry
    @SpringBootApplication
    @EnableEurekaServer
    static class RegistryApplication {
        public static void main(String[] args) {
            SpringApplication.run(RegistryApplication.class, args);
        }
    }

    // ---------------------------------------------------------------- 3) a CALLER with client-side load balancing
    @SpringBootApplication
    static class PaymentsApplication {

        // @LoadBalanced makes the builder understand LOGICAL names: "orders-service" is looked up in the
        // registry and each call is sent to one healthy instance (round-robin by default).
        @Bean
        @LoadBalanced
        RestClient.Builder loadBalancedRestClientBuilder() {
            return RestClient.builder();
        }

        @Bean
        RestClient ordersClient(RestClient.Builder builder) {
            return builder.baseUrl("http://orders-service").build();       // NOT a real host name
        }

        @Service
        static class OrderLookup {
            private final RestClient ordersClient;

            OrderLookup(RestClient ordersClient) {
                this.ordersClient = ordersClient;
            }

            String find(String id) {
                return ordersClient.get().uri("/orders/{id}", id).retrieve().body(String.class);
            }
        }
    }
}
