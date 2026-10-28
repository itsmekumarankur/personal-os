import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 32. Simplest real-world feature flag in Spring: a property + @RefreshScope. NOT compiled or run by the author.
 *
 * Flip `features.new-checkout=true` in config, call POST /actuator/refresh, behaviour changes with no restart.
 * For percentage rollouts, per-user targeting, audit trail and a UI, use Unleash / LaunchDarkly / Flagsmith
 * (their SDKs expose the same shape as FeatureFlagDemo.isEnabled(flag, userId)).
 */
@RefreshScope
@RestController
public class FeatureFlagSnippet {

    @Value("${features.new-checkout:false}")      // safe default: OFF
    private boolean newCheckout;

    @GetMapping("/checkout")
    public String checkout() {
        return newCheckout ? "new checkout flow" : "old checkout flow";
    }
}
