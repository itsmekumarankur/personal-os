package com.example.spring.scope;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

/**
 * 2. Bean scopes and lifecycle
 *
 *  - singleton (default): ONE instance per container, shared everywhere
 *  - prototype: a NEW instance every time the bean is requested
 *  - Lifecycle: constructor -> dependency injection -> @PostConstruct -> ... -> @PreDestroy
 *    (Spring does NOT call @PreDestroy for prototype beans; it hands them over and forgets them)
 *
 * Classic pitfall: injecting a prototype into a singleton gives you only ONE prototype
 * (injection happens once). Use ObjectProvider to get a fresh one on every call.
 */
public class BeanScopeLifecycleDemo {

    @Component
    static class RateCache { // singleton by default
        RateCache() {
            System.out.println("  RateCache: constructor");
        }

        @PostConstruct
        void init() {
            System.out.println("  RateCache: @PostConstruct (load rates, open connections...)");
        }

        @PreDestroy
        void cleanup() {
            System.out.println("  RateCache: @PreDestroy (release resources)");
        }
    }

    @Component
    @Scope("prototype")
    static class TradeOrder {
        private static int counter = 0;
        final int id = ++counter;
    }

    @Component
    static class OrderService {
        private final TradeOrder injectedOnce;                   // pitfall
        private final ObjectProvider<TradeOrder> orderProvider;  // correct

        OrderService(TradeOrder injectedOnce, ObjectProvider<TradeOrder> orderProvider) {
            this.injectedOnce = injectedOnce;
            this.orderProvider = orderProvider;
        }

        void demo() {
            System.out.println("Direct injection (same instance every call):");
            System.out.println("  call 1 -> order id " + injectedOnce.id);
            System.out.println("  call 2 -> order id " + injectedOnce.id);

            System.out.println("ObjectProvider (fresh instance every call):");
            System.out.println("  call 1 -> order id " + orderProvider.getObject().id);
            System.out.println("  call 2 -> order id " + orderProvider.getObject().id);
        }
    }

    public static void main(String[] args) {
        System.out.println("--- starting container ---");
        var ctx = new AnnotationConfigApplicationContext(
                RateCache.class, TradeOrder.class, OrderService.class);

        System.out.println("--- singleton vs prototype ---");
        System.out.println("singleton same instance?  "
                + (ctx.getBean(RateCache.class) == ctx.getBean(RateCache.class)));
        System.out.println("prototype same instance?  "
                + (ctx.getBean(TradeOrder.class) == ctx.getBean(TradeOrder.class)));

        System.out.println("--- prototype inside singleton ---");
        ctx.getBean(OrderService.class).demo();

        System.out.println("--- closing container ---");
        ctx.close();
    }
}
