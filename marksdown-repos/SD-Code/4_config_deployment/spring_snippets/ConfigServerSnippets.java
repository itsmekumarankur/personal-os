/*
 * 31. Spring Cloud Config Server: central, git-backed configuration. NOT compiled or run by the author.
 *
 * ---------------- config-server (a tiny Spring Boot app) ----------------
 * dependency: org.springframework.cloud:spring-cloud-config-server
 *
 *   @SpringBootApplication
 *   @EnableConfigServer
 *   public class ConfigServerApp { public static void main(String[] a){ SpringApplication.run(ConfigServerApp.class, a);} }
 *
 * application.yml of the config server:
 *   server.port: 8888
 *   spring.cloud.config.server.git.uri: https://github.com/your-org/config-repo
 *   # repo files:  payment-service.yml, payment-service-prod.yml, application.yml (shared by all)
 *
 * ---------------- each microservice (client) ----------------
 * dependency: org.springframework.cloud:spring-cloud-starter-config
 * application.yml:
 *   spring:
 *     application.name: payment-service
 *     config.import: "optional:configserver:http://config-server:8888"
 *
 * ---------------- change config WITHOUT restart ----------------
 * dependency: spring-boot-starter-actuator; expose "refresh": management.endpoints.web.exposure.include=refresh
 *
 *   @RefreshScope               // bean is rebuilt when refreshed
 *   @RestController
 *   class FeeController {
 *       @Value("${app.fee-rate}") double feeRate;
 *       ...
 *   }
 *
 *   1. edit payment-service-prod.yml in git, commit
 *   2. POST http://payment-service/actuator/refresh   -> new value live, no redeploy
 *      (Spring Cloud Bus can broadcast the refresh to every instance at once.)
 *
 * Alternative in Kubernetes: ConfigMap + env vars (see ../kubernetes). Pick ONE source of truth per setting.
 */
public class ConfigServerSnippets {
}
