package com.example.snippets;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/**
 * Topic 20: transactional outbox with Spring + JPA + Kafka. NOT compiled in the sandbox it was written in.
 * Runnable concept demo: OutboxPatternDemo.java
 *
 * Needs @EnableScheduling on your application class.
 * Production-grade alternative to the polling relay below: Debezium (change data capture) reading the outbox table.
 */
public class OutboxSnippet {

    @Entity
    static class OrderEntity {
        @Id
        String id;
        String customerId;
        long amount;
    }

    @Entity
    static class OutboxEvent {
        @Id
        String eventId = UUID.randomUUID().toString();     // consumers de-duplicate on this
        String aggregateId;
        String type;
        String payload;                                      // JSON
        boolean sent;
    }

    interface OrderRepository extends JpaRepository<OrderEntity, String> {
    }

    interface OutboxRepository extends JpaRepository<OutboxEvent, String> {
        List<OutboxEvent> findTop100BySentFalseOrderByEventIdAsc();     // in real code order by a created_at / sequence column
    }

    // ---------- 1) ONE local transaction writes the business row AND the outbox row ----------
    @Service
    static class OrderService {
        private final OrderRepository orders;
        private final OutboxRepository outbox;

        OrderService(OrderRepository orders, OutboxRepository outbox) {
            this.orders = orders;
            this.outbox = outbox;
        }

        @Transactional                                       // both inserts commit together, or neither does
        public void placeOrder(OrderEntity order) {
            orders.save(order);

            OutboxEvent event = new OutboxEvent();
            event.aggregateId = order.id;
            event.type = "OrderPlaced";
            event.payload = "{\"orderId\":\"" + order.id + "\",\"amount\":" + order.amount + "}";
            outbox.save(event);
            // NO call to Kafka here. If Kafka were down, the order would still be saved safely.
        }
    }

    // ---------- 2) A separate relay publishes unsent rows and marks them sent ----------
    @Component
    static class OutboxRelay {
        private final OutboxRepository outbox;
        private final KafkaTemplate<String, String> kafka;

        OutboxRelay(OutboxRepository outbox, KafkaTemplate<String, String> kafka) {
            this.outbox = outbox;
            this.kafka = kafka;
        }

        @Scheduled(fixedDelay = 1000)
        @Transactional
        public void publishPending() {
            for (OutboxEvent e : outbox.findTop100BySentFalseOrderByEventIdAsc()) {
                try {
                    // .get() waits for the broker's acknowledgement before we mark the row as sent
                    kafka.send("orders", e.aggregateId, e.payload).get();
                    e.sent = true;                           // if we crash before commit, the row is re-sent later (at-least-once)
                } catch (Exception ex) {
                    return;                                  // broker down: stop, retry on the next tick
                }
            }
        }
    }

    // ---------- 3) Consumers must be idempotent (see IdempotencyDemo in the resilience zip) ----------
}
