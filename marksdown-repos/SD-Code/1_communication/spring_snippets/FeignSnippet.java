package com.example.snippets;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;


/**
 * TOPIC: Spring Cloud Feign
 
   WHAT ARE WE LEARNING?
   ---------------------
        How one service communicates with another service easily.
 
   HOW DOES IT WORK?
   -----------------
        1. We call a Java method:
            pricing.getPrice("AAPL");
        2. Feign automatically sends an HTTP request to the Pricing Service.
        3. The Pricing Service processes the request and returns the price.
        4. Feign gives the response back to our code.
 
   WHAT IS FALLBACK?
   -----------------
     -  If the Pricing Service fails, fallback provides an alternative response.
     -  In this example, getPrice() returns 0.0 when the fallback is triggered.
  
   SIMPLE EXAMPLE:
   ---------------
     Without Feign: Write HTTP communication code manually.
     With Feign:    Call a Java method; Feign handles the HTTP communication.
 
   REMEMBER:
   ---------
  -  Feign    = Messenger between services.
  -  Fallback = Backup plan when a service call fails.
 
 */

@SpringBootApplication
@EnableFeignClients                       // scan for @FeignClient interfaces and create proxies
public class FeignSnippet {

    record Price(String symbol, double price) {
    }

    record QuoteRequest(String symbol, int qty) {
    }

    // The interface IS the client. Spring Cloud creates the implementation at startup.
    // "pricing-service" is resolved through service discovery / load balancing - its 3d Party,
    // or pin a URL with:  url = "${pricing.url}"
    @FeignClient(name = "pricing-service", fallback = PricingFallback.class)
    interface PricingClient {

        @GetMapping("/prices/{symbol}")
        Price getPrice(@PathVariable("symbol") String symbol);

        @PostMapping("/quotes")
        Price createQuote(@RequestBody QuoteRequest request);
    }

    // Used when the call fails (needs spring.cloud.openfeign.circuitbreaker.enabled=true)
    @org.springframework.stereotype.Component
    static class PricingFallback implements PricingClient {
        public Price getPrice(String symbol) {
            return new Price(symbol, 0.0);   // safe, clearly "unknown" value
            /**
            If Pricing Service Fails:
            =============================
                If Pricing Service Fails:
                    |
                    v
                PricingFallback is called
                    |
                    v
                getPrice() returns 0.0
                    |
                    v
                OrderService calculates using price 0.0
            * 
            */
        }

        public Price createQuote(QuoteRequest request) {
            throw new IllegalStateException("pricing-service unavailable, cannot create quote now");
        }
    }

    @Service
    static class OrderService {
        private final PricingClient pricing;           // inject it like any bean

        OrderService(PricingClient pricing) {
            this.pricing = pricing;
        }

        double total(String symbol, int qty) {
            return pricing.getPrice(symbol).price() * qty;
            /**
             * 
             * total("AAPL", 5) is called
                    |
                    v
                        pricing.getPrice("AAPL")
                            |
                            v
                        Feign sends HTTP GET /prices/AAPL
                            |
                            v
                        Pricing Service returns price = 100
                            |
                            v
                        OrderService calculates 100 * 5
                            |
                            v
                        Returns Total = 500
             * 
            */
        }
    }

    public static void main(String[] args) {

           var context = SpringApplication.run(FeignSnippet.class, args);

            // Get OrderService from Spring
            OrderService orderService = context.getBean(OrderService.class);

            // Call total() to calculate the cost of 5 shares
            double total = orderService.total("AAPL", 5);

            System.out.println("Total Price: " + total);

        /**
         * 
         *         Spring Boot Initializes
                        |
                        v
                        Finds @FeignClient (PricingClient)
                            |
                            v
                            Creates Feign Proxy Automatically
                                |
                                v
                                Injects Proxy into OrderService
                                    |
                                    v
                                        total("AAPL", 5) is called
        */
    }


}


