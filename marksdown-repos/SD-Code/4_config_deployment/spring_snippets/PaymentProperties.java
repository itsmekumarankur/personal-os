import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.validation.annotation.Validated;

/**
 * 31. Type-safe, validated configuration. NOT compiled or run by the author.
 *
 * Binds app.fee-rate, app.gateway-url, app.db.password from ANY source (yml, env var APP_FEE_RATE, --app.fee-rate=...).
 * @Validated => the app FAILS AT STARTUP if config is missing or silly, instead of failing at 3 a.m. in production.
 * Needs: spring-boot-starter-validation.
 */
@ConfigurationProperties(prefix = "app")
@Validated
public record PaymentProperties(
        @DecimalMin("0.0") @DecimalMax("0.10") double feeRate,
        @NotBlank String gatewayUrl) {
}

@Configuration
@EnableConfigurationProperties(PaymentProperties.class)
class PropertiesConfig {
}

// Usage: just inject it.
//   @Service class FeeService { FeeService(PaymentProperties props) {...}  props.feeRate() }
