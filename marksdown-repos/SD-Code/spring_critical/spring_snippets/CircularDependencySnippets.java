import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.annotation.Lazy;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;

/**
 * 8. Breaking circular dependencies. NOT compiled or run by the author.
 *
 * Error you will see:
 *   "The dependencies of some of the beans in the application context form a cycle:
 *    orderService -> paymentService -> orderService"
 * Spring Boot 2.6+ refuses cycles by default (spring.main.allow-circular-references=false). Do not switch that on to "fix" it.
 */

// ----- the problem
// @Service class OrderService   { OrderService(PaymentService p) {...} }
// @Service class PaymentService { PaymentService(OrderService o) {...} }

// ----- Fix 1 (best): extract the shared concept
@Service
class FeeCalculator {
    double fee(double amount) { return amount * 0.02; }
}

@Service
class OrderServiceFixed {
    private final FeeCalculator fees;
    OrderServiceFixed(FeeCalculator fees) { this.fees = fees; }
}

@Service
class PaymentServiceFixed {
    private final FeeCalculator fees;
    PaymentServiceFixed(FeeCalculator fees) { this.fees = fees; }
}

// ----- Fix 2: replace a direct call with an event
record PaymentCompleted(long orderId) { }

@Service
class PaymentServiceEvents {
    private final ApplicationEventPublisher events;
    PaymentServiceEvents(ApplicationEventPublisher events) { this.events = events; }
    void pay(long orderId) { events.publishEvent(new PaymentCompleted(orderId)); }       // does not know OrderService exists
}

@Service
class OrderServiceEvents {
    @EventListener
    void onPaid(PaymentCompleted e) { /* mark order paid */ }
}

// ----- Fix 3 (last resort): look the other bean up lazily
@Service
class OrderServiceLazy {
    private final ObjectProvider<PaymentServiceLazy> payments;       // resolved at first use, not at construction
    OrderServiceLazy(ObjectProvider<PaymentServiceLazy> payments) { this.payments = payments; }
    void pay() { payments.getObject(); }
}

@Service
class PaymentServiceLazy {
    private final OrderServiceLazy orders;
    PaymentServiceLazy(@Lazy OrderServiceLazy orders) { this.orders = orders; }          // @Lazy injects a proxy instead
}
