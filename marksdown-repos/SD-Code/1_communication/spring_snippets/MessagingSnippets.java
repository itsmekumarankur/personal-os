package com.example.snippets;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@SpringBootApplication
public class MessagingSnippets {

    /*
    TOPIC: Kafka and RabbitMQ

    WHAT ARE WE LEARNING?
    How services communicate using messages instead of directly calling each other.

    KEY DIFFERENCE:
    Kafka    = Stores a stream of events that consumers can read.
    RabbitMQ = Routes messages to queues for processing.
    */

    // =========================================================== KAFKA

    /*
    1. KAFKA - SHARE EVENTS WITH MULTIPLE SERVICES

        Payment Service
            |
            v
        Kafka Topic ("payments")
            |
            +----------+
            |          |
            v          v
        Billing    Analytics
        Service     Service

    Different consumer groups receive their own copy of an event.
    */

    @Component
    static class PaymentEventProducer {
        private final KafkaTemplate<String, String> kafka;

        PaymentEventProducer(KafkaTemplate<String, String> kafka) {
            this.kafka = kafka;
        }

        void publish(String accountId, String json) {
            // Same accountId goes to the same partition, preserving order.
            kafka.send("payments", accountId, json);
        }
    }

    @Component
    static class BillingConsumer {
        @KafkaListener(topics = "payments", groupId = "billing")
        void onPayment(String json) {
            System.out.println("billing got " + json);
        }
    }

    @Component
    static class AnalyticsConsumer {
        @KafkaListener(topics = "payments", groupId = "analytics")
        void onPayment(String json) {
            System.out.println("analytics got " + json);
        }
    }

    // =========================================================== RABBITMQ

    /*
    2. RABBITMQ - ROUTE TASKS TO WORKERS

        Email Producer
            |
            v
        Exchange
            |
            v
        Email Queue
            |
            v
        Email Worker
            |
            v
        Send Email
    */

    @Component
    static class EmailRequestProducer {
        private final RabbitTemplate rabbit;

        EmailRequestProducer(RabbitTemplate rabbit) {
            this.rabbit = rabbit;
        }

        void send(String json) {
            rabbit.convertAndSend("notifications.exchange", "email", json);
        }
    }

    @Component
    static class EmailWorker {
        @RabbitListener(queues = "email.queue")
        void handle(String json) {
            System.out.println("sending email for " + json);
        }
    }

    // Kafka    = Durable event log; consumers can replay events.
    // RabbitMQ = Routes messages to queues for processing.

    public static void main(String[] args) {
        org.springframework.context.ConfigurableApplicationContext context =
                org.springframework.boot.SpringApplication.run(
                        MessagingSnippets.class, args);

        PaymentEventProducer paymentProducer =
                context.getBean(PaymentEventProducer.class);

        EmailRequestProducer emailProducer =
                context.getBean(EmailRequestProducer.class);

        paymentProducer.publish(
                "ACC101",
                "{\"paymentId\":\"PAY101\",\"amount\":500}");

        emailProducer.send(
                "{\"to\":\"user@example.com\",\"subject\":\"Payment Received\",\"body\":\"Your payment has been received.\"}");
        }
    }