package com.example.spring.events;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/**
 * 6. Application events (loose coupling)
 *
 * TransferService does not know who cares that a transfer happened.
 * New reactions (fraud check, loyalty points, analytics) are added by writing a new
 * listener, with ZERO change to TransferService (Open/Closed in action).
 *
 * By default listeners run synchronously in the publisher's thread, and in the same
 * transaction. Use @TransactionalEventListener(phase = AFTER_COMMIT) to react only
 * after a successful commit, and @Async to move listeners to another thread.
 */
public class EventsDemo {

    record TransferCompleted(String from, String to, int amount) {
    }

    @Component
    static class TransferService {
        private final ApplicationEventPublisher publisher;

        TransferService(ApplicationEventPublisher publisher) {
            this.publisher = publisher;
        }

        void transfer(String from, String to, int amount) {
            System.out.println("Transferring " + amount + " from " + from + " to " + to);
            publisher.publishEvent(new TransferCompleted(from, to, amount));
        }
    }

    @Component
    static class AuditListener {
        @EventListener
        void onTransfer(TransferCompleted e) {
            System.out.println("  [audit]   recorded transfer of " + e.amount());
        }
    }

    @Component
    static class NotificationListener {
        @EventListener
        void onTransfer(TransferCompleted e) {
            System.out.println("  [notify]  SMS to owner of " + e.from());
        }
    }

    public static void main(String[] args) {
        try (var ctx = new AnnotationConfigApplicationContext(
                TransferService.class, AuditListener.class, NotificationListener.class)) {

            ctx.getBean(TransferService.class).transfer("ACC-1", "ACC-2", 750);
        }
    }
}
