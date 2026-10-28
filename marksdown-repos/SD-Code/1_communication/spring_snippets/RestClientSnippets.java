package com.example.snippets;

import org.springframework.http.HttpStatusCode;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

/**
 * 
- RestClient: The modern way to call another service in Spring. 
              It waits for the response before moving to the next step. 
              Easy to write and best for most new, normal REST API calls.
- RestTemplate: 
              The older way to call another service. 
              It also waits for the response, but it is now in maintenance mode. 
              You will commonly find it in existing projects.
- WebClient: 
              The non-blocking way to call another service. 
              While waiting for a response, your application can do other work. 
              Useful for reactive applications or calling multiple services in parallel.

Easy example to remember:

- `RestClient` = Wait for the parcel before continuing.
- `RestTemplate` = Same waiting approach, older tool.
- `WebClient` = Place the order and do other work while the parcel is on its way.

TOPIC: Calling Another Service Using REST in Spring

                    OUR SERVICE
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
        RestClient  RestTemplate  WebClient
          (New)       (Legacy)    (Reactive)
             |           |           |
             v           v           v
         Blocking    Blocking    Non-blocking
             |           |           |
             +-----------+-----------+
                         |
                         v
               PRICING SERVICE
             http://pricing-service
                         |
             +-----------+-----------+
             |                       |
             v                       v
      GET /prices/{symbol}      POST /quotes
             |                       |
             v                       v
        Get Price                Create Quote
             |                       |
             +-----------+-----------+
                         |
                         v
                  JSON RESPONSE
                         |
                         v
                  Price(symbol, price)


    KEY DIFFERENCE:
    ---------------
        RestClient   = Modern, blocking REST calls.
        RestTemplate = Older, blocking REST calls.
        WebClient    = Non-blocking, reactive REST calls.

    REMEMBER:
    ---------
        Blocking     = Wait for the response before continuing.
        Non-blocking = Can do other work while waiting.

        WebClient can also call multiple services in parallel:
        Mono.zip(getPrice("INFY"), getPrice("TCS"))

    TIMEOUTS:
    ---------
        RestClient  = Connection and read timeouts.
        WebClient   = Reactive timeout.

 */
public class RestClientSnippets {

    record Price(String symbol, double price) {
    }

    // ------------------------------------------------------------------ 1) RestClient (blocking, modern)
    @Component
    static class PricingClientWithRestClient {
        private final RestClient http;

        PricingClientWithRestClient(RestClient.Builder builder) {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(1000);        // ALWAYS set timeouts (see the resilience demos)
            factory.setReadTimeout(1000);

            this.http = builder
                    .baseUrl("http://pricing-service")      // with service discovery this is the logical name
                    .requestFactory(factory)
                    .build();
        }

        Price getPrice(String symbol) {
            return http.get()
                    .uri("/prices/{symbol}", symbol)
                    .retrieve()
                    .onStatus(HttpStatusCode::is4xxClientError, (request, response) -> {
                        throw new IllegalArgumentException("Unknown symbol " + symbol);
                    })
                    .body(Price.class);                     // JSON -> Price via Jackson
        }

        Price createQuote(Price request) {
            return http.post()
                    .uri("/quotes")
                    .body(request)                          // Price -> JSON
                    .retrieve()
                    .body(Price.class);
        }
    }

    // ------------------------------------------------------------------ 2) RestTemplate (legacy blocking)
    @Component
    static class PricingClientWithRestTemplate {
        private final RestTemplate restTemplate = new RestTemplate();

        Price getPrice(String symbol) {
            return restTemplate.getForObject("http://pricing-service/prices/{symbol}", Price.class, symbol);
        }
    }

    // ------------------------------------------------------------------ 3) WebClient (non-blocking)
    @Component
    static class PricingClientWithWebClient {
        private final WebClient web = WebClient.builder().baseUrl("http://pricing-service").build();

        Mono<Price> getPrice(String symbol) {
            return web.get()
                    .uri("/prices/{symbol}", symbol)
                    .retrieve()
                    .bodyToMono(Price.class)
                    .timeout(Duration.ofSeconds(1));        // reactive timeout
        }
        // Calling two services in parallel:
        //   Mono.zip(getPrice("INFY"), getPrice("TCS")).map(t -> ...)
    }

    public static void main(String[] args) {

        // Start Spring Boot
        var context = org.springframework.boot.SpringApplication.run(DemoApplication.class, args);

        // Get all three REST clients
        var restClient = context.getBean(PricingClientWithRestClient.class);
        var restTemplate = context.getBean(PricingClientWithRestTemplate.class);
        var webClient = context.getBean(PricingClientWithWebClient.class);

        // 1. Modern blocking call using RestClient
        Price price1 = restClient.getPrice("INFY");
        System.out.println("RestClient: " + price1);

        // 2. Legacy blocking call using RestTemplate
        Price price2 = restTemplate.getPrice("TCS");
        System.out.println("RestTemplate: " + price2);

        // 3. Non-blocking reactive call using WebClient
        webClient.getPrice("WIPRO").subscribe(price -> System.out.println("WebClient: " + price));

        // Keep the application running while the reactive call completes.
        // In a real Spring Boot application, the server normally keeps it alive.
    }
}
