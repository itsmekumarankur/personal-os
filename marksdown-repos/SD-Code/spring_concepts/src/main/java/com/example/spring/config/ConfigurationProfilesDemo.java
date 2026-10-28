package com.example.spring.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.core.env.MapPropertySource;

import java.util.Map;

/**
       SPRING CONFIGURATION PROFILES DEMO
       ==================================

                    main()
                      |
          +-----------+-----------+
          |                       |
          v                       v
    runWith("dev")          runWith("prod")
          |                       |
          v                       v
   Active Profile: dev      Active Profile: prod
          |                       |
          v                       v
   +----------------+      +----------------+
   |   AppConfig    |      |   AppConfig    |
   | @Configuration |      | @Configuration |
   +-------+--------+      +-------+--------+
           |                       |
           v                       v
   @Profile("dev")          @Profile("prod")
           |                       |
           v                       v
   +----------------+      +----------------+
   | SandboxGateway  |      |   LiveGateway  |
   +--------+-------+      +--------+--------+
            |                       |
            v                       v
   Charge 1000               Charge 1000
            |                       |
            v                       v
   "SANDBOX: pretended        "LIVE: really
    to charge 1000"            charged 1000"


       FEE CALCULATOR CONFIGURATION
       ============================

              @Bean FeeCalculator
                      |
                      v
            @Value("${app.fee.rate:0.02}")
                      |
             +--------+---------+
             |                  |
             v                  v
       Property exists?    Property missing?
             |                  |
             v                  v
       Use configured       Use default
       property value       rate = 0.02
             |                  |
             +--------+---------+
                      |
                      v
              FeeCalculator(rate)
                      |
                      v
                fee(1000)
                      |
          +-----------+-----------+
          |                       |
          v                       v
      DEV PROFILE            PROD PROFILE
      Rate = 0.02            Rate = 0.005
          |                       |
          v                       v
      1000 x 0.02             1000 x 0.005
          |                       |
          v                       v
       Fee = 20                Fee = 5


       KEY SPRING ANNOTATIONS
       ======================

       @Configuration
             |
             v
       Defines configuration class

       @Bean
             |
             v
       Creates and registers an object
       in the Spring container

       @Profile("dev" / "prod")
             |
             v
       Selects the appropriate bean
       for the active environment

       @Value("${app.fee.rate:0.02}")
             |
             v
       Injects external configuration
       or uses the default value
 */
public class ConfigurationProfilesDemo {

    interface PaymentGateway {
        String charge(int amount);
    }

    static class SandboxGateway implements PaymentGateway {
        public String charge(int amount) {
            return "SANDBOX: pretended to charge " + amount;
        }
    }

    static class LiveGateway implements PaymentGateway {
        public String charge(int amount) {
            return "LIVE: really charged " + amount;
        }
    }

    static class FeeCalculator {
        private final double rate;

        FeeCalculator(double rate) {
            this.rate = rate;
        }

        double fee(int amount) {
            return amount * rate;
        }
    }

    @Configuration
    static class AppConfig {

        @Bean
        @Profile("dev")
        PaymentGateway sandboxGateway() {
            return new SandboxGateway();
        }

        @Bean
        @Profile("prod")
        PaymentGateway liveGateway() {
            return new LiveGateway();
        }

        // ${app.fee.rate:0.02} -> property if present, otherwise 0.02
        @Bean
        FeeCalculator feeCalculator(@Value("${app.fee.rate:0.02}") double rate) {
            return new FeeCalculator(rate);
        }
    }

    private static void runWith(String profile, Map<String, Object> properties) {
        try (var ctx = new AnnotationConfigApplicationContext()) {
            ctx.getEnvironment().setActiveProfiles(profile);
            ctx.getEnvironment().getPropertySources()
                    .addFirst(new MapPropertySource("demo-properties", properties));
            ctx.register(AppConfig.class);
            ctx.refresh();

            System.out.println("Profile '" + profile + "':");
            System.out.println("  " + ctx.getBean(PaymentGateway.class).charge(1000));
            System.out.println("  fee on 1000 = " + ctx.getBean(FeeCalculator.class).fee(1000));
        }
    }

    public static void main(String[] args) {
        runWith("dev", Map.of());                          // no property -> default 0.02
        runWith("prod", Map.of("app.fee.rate", "0.005"));  // property overrides the default
    }
}
