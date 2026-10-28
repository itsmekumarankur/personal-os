import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;

/**
 * 2. Writing your OWN starter / auto-configuration (shared library used by many microservices).
 * NOT compiled or run by the author.
 *
 * Library layout (two modules by convention):
 *   acme-audit-spring-boot-autoconfigure/   <- this code
 *   acme-audit-spring-boot-starter/         <- empty jar whose pom just depends on the autoconfigure module + the client lib
 *
 * Register the class in:
 *   src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
 * containing one line:
 *   com.acme.audit.AuditAutoConfiguration
 *
 * Any app that adds the starter dependency now gets an AuditClient bean automatically, unless it defines its own
 * or sets  acme.audit.enabled=false.
 * Debug: run with --debug and read the CONDITIONS EVALUATION REPORT, or use /actuator/conditions.
 */
@AutoConfiguration
@ConditionalOnClass(AuditClient.class)                                   // only if the client library is present
@ConditionalOnProperty(prefix = "acme.audit", name = "enabled", havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(AuditProperties.class)
class AuditAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean                                             // the user's own bean always wins
    AuditClient auditClient(AuditProperties props) {
        return new AuditClient(props.endpoint());
    }
}

@ConfigurationProperties(prefix = "acme.audit")
record AuditProperties(String endpoint) { }

class AuditClient {
    private final String endpoint;
    AuditClient(String endpoint) { this.endpoint = endpoint; }
}
