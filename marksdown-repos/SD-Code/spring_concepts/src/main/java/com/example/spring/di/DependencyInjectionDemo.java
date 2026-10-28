package com.example.spring.di;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

/**
 * ================================================================
 * IoC + DEPENDENCY INJECTION - THE BIG IDEA
 * ================================================================
 *
 *   WITHOUT Spring (you control)       WITH Spring (IoC = control inverted)
 *   ----------------------------       ------------------------------------
 *   class PaymentService {             class PaymentService {
 *     n = new SmsNotifier();             PaymentService(NotificationService n) {...}
 *   }                                  }
 *   - tightly coupled                  - container creates and injects
 *   - hard to test / swap              - easy to test, easy to swap
 *
 * ================================================================
 * THE BEANS IN THE CONTAINER
 * ================================================================
 *
 *                 <<interface>>
 *             NotificationService
 *                  ^          ^
 *                  |          |
 *     +------------+--+    +--+---------------------+
 *     | EmailNotif...  |    | SmsNotificationService |
 *     | name:          |    | @Primary  (the default)|
 *     | "emailNotifier"|    +------------------------+
 *     +----------------+
 *
 *     PaymentService  (needs TWO NotificationService objects)
 *
 * ================================================================
 * HOW SPRING WIRES PaymentService
 * ================================================================
 *
 *   new AnnotationConfigApplicationContext(Email, Sms, Payment)
 *                          |
 *                          v
 *        Spring sees ONE constructor in PaymentService
 *        (@Autowired optional since Spring 4.3)
 *                          |
 *                          v
 *        Parameter 1: NotificationService defaultNotifier
 *           |
 *           |  2 candidates found: Email and Sms
 *           |  no @Qualifier -> pick the @Primary
 *           v
 *        injects SmsNotificationService
 *
 *        Parameter 2: @Qualifier("emailNotifier") NotificationService
 *           |
 *           |  asked for bean named "emailNotifier"
 *           v
 *        injects EmailNotificationService
 *
 *                          |
 *                          v
 *        new PaymentService(sms, email)   <- built BY SPRING
 *
 * ================================================================
 * WHAT main() DOES
 * ================================================================
 *
 *   ctx.getBean(PaymentService.class).pay("ankur", 500)
 *                          |
 *                          v
 *              +----------------------+
 *              |    PaymentService    |
 *              +----------+-----------+
 *                         |
 *          +--------------+---------------+
 *          |                              |
 *          v                              v
 *   defaultNotifier.send(..)       emailNotifier.send(..)
 *   -> SMS (@Primary)              -> EMAIL (@Qualifier)
 *          |                              |
 *          v                              v
 *   [SMS] Payment of 500 done      [EMAIL] Receipt for payment of 500
 *
 *   Console output:
 *     Paying 500 for ankur
 *       [SMS]   Payment of 500 done
 *       [EMAIL] Receipt for payment of 500
 *
 * ================================================================
 * @Primary vs @Qualifier
 * ================================================================
 *
 *   @Primary                         @Qualifier("name")
 *   --------                         ------------------
 *   set on the bean class            set on the injection point
 *   "default choice"                 "I want THIS one"
 *   used when nothing else is said   overrides @Primary
 *
 * ================================================================
 * KEY TAKEAWAY
 * ================================================================
 *
 *  IoC                   -> container creates objects, not you
 *  DI                    -> container passes them in via constructor
 *  Constructor injection -> preferred: final fields, easy unit tests
 *  Same type, many beans -> @Primary = default, @Qualifier = specific
 *  Coding to interface   -> PaymentService never names Sms or Email
 *
 * ================================================================

 
 */
public class DependencyInjectionDemo {

    interface NotificationService {
        void send(String message);
    }

    @Component("emailNotifier")
    static class EmailNotificationService implements NotificationService {
        public void send(String message) {
            System.out.println("  [EMAIL] " + message);
        }
    }

    @Component
    @Primary // used whenever someone asks for a NotificationService without a qualifier
    static class SmsNotificationService implements NotificationService {
        public void send(String message) {
            System.out.println("  [SMS]   " + message);
        }
    }

    @Component
    static class PaymentService {
        private final NotificationService defaultNotifier;
        private final NotificationService emailNotifier;

        // Single constructor => @Autowired is optional since Spring 4.3
        PaymentService(NotificationService defaultNotifier,
                       @Qualifier("emailNotifier") NotificationService emailNotifier) {
            this.defaultNotifier = defaultNotifier;
            this.emailNotifier = emailNotifier;
        }

        void pay(String user, int amount) {
            System.out.println("Paying " + amount + " for " + user);
            defaultNotifier.send("Payment of " + amount + " done");   // -> SMS (@Primary)
            emailNotifier.send("Receipt for payment of " + amount);   // -> Email (@Qualifier)
        }
    }

    public static void main(String[] args) {
        try (var ctx = new AnnotationConfigApplicationContext(
                EmailNotificationService.class,
                SmsNotificationService.class,
                PaymentService.class)) {

            ctx.getBean(PaymentService.class).pay("ankur", 500);
        }
    }
}
