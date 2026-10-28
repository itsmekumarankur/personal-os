import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.oauth2.server.resource.authentication.JwtGrantedAuthoritiesConverter;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/**
 * 38 + 39. Spring Security RESOURCE SERVER validating JWTs. NOT compiled or run by the author.
 *
 * Dependencies: spring-boot-starter-web, spring-boot-starter-security, spring-boot-starter-oauth2-resource-server
 *
 * application.yml (the public keys are fetched from the auth server's JWKS endpoint; no shared secret in this service):
 *   spring.security.oauth2.resourceserver.jwt:
 *     issuer-uri: https://auth.example.com/realms/payments     # validates signature, exp, iss
 *     # or: jwk-set-uri: https://auth.example.com/.well-known/jwks.json
 *
 * Spring automatically: 401 for missing/invalid token, 403 for authenticated but not allowed.
 */
@Configuration
@EnableMethodSecurity                       // enables @PreAuthorize
class ResourceServerConfig {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)                         // stateless bearer-token API, no browser cookies
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/payments/**").hasAuthority("SCOPE_payments:read")     // scope -> SCOPE_ prefix
                .requestMatchers(HttpMethod.POST, "/payments/*/refund").hasRole("ADMIN")
                .anyRequest().authenticated())                              // default deny
            .oauth2ResourceServer(o -> o.jwt(j -> j.jwtAuthenticationConverter(jwtAuthConverter())));
        return http.build();
    }

    /** Map a custom "roles" claim in the JWT to ROLE_* authorities (default Spring only maps "scope"). */
    @Bean
    JwtAuthenticationConverter jwtAuthConverter() {
        JwtGrantedAuthoritiesConverter roles = new JwtGrantedAuthoritiesConverter();
        roles.setAuthoritiesClaimName("roles");
        roles.setAuthorityPrefix("ROLE_");
        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(roles);
        // note: this replaces the default scope mapping; combine both converters if you need SCOPE_ and ROLE_ together
        return converter;
    }
}

@RestController
@RequestMapping("/payments")
class PaymentController {

    @GetMapping
    String list() { return "payments"; }

    // method-level rule, evaluated per call; can reference the logged-in user
    @PreAuthorize("hasRole('ADMIN')")
    @PostMapping("/{id}/refund")
    String refund(@PathVariable String id) { return "refunded " + id; }

    @PreAuthorize("#userId == authentication.name or hasRole('ADMIN')")      // users may read only their own data
    @GetMapping("/by-user/{userId}")
    String byUser(@PathVariable String userId) { return "payments of " + userId; }
}
