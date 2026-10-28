import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.client.AuthorizedClientServiceOAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizeRequest;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientProviderBuilder;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.web.client.RestClient;

/**
 * 40 + 41. OAuth2 client credentials and token propagation with RestClient. NOT compiled or run by the author.
 * Dependencies: spring-boot-starter-oauth2-client (+ resource-server for propagation).
 *
 * application.yml of order-service:
 *   spring.security.oauth2.client:
 *     registration:
 *       payments:                                      # registration id used in code below
 *         provider: auth
 *         client-id: order-service
 *         client-secret: ${ORDER_CLIENT_SECRET}        # from env / secret store, NEVER literal
 *         authorization-grant-type: client_credentials
 *         scope: payments:read
 *     provider:
 *       auth:
 *         token-uri: https://auth.example.com/realms/payments/protocol/openid-connect/token
 *
 * Human login (OIDC, authorization code + PKCE) is the same registration style with
 * authorization-grant-type: authorization_code, scope: openid,profile and issuer-uri on the provider.
 */
@Configuration
class OAuth2ClientConfig {

    // ---------- 40. client credentials: the manager fetches, caches and refreshes the token for you
    @Bean
    OAuth2AuthorizedClientManager authorizedClientManager(ClientRegistrationRepository registrations,
                                                         OAuth2AuthorizedClientService clientService) {
        var manager = new AuthorizedClientServiceOAuth2AuthorizedClientManager(registrations, clientService);
        manager.setAuthorizedClientProvider(OAuth2AuthorizedClientProviderBuilder.builder().clientCredentials().build());
        return manager;
    }

    @Bean
    RestClient paymentClientWithOwnToken(RestClient.Builder builder, OAuth2AuthorizedClientManager manager) {
        ClientHttpRequestInterceptor addServiceToken = (request, body, execution) -> {
            var authorized = manager.authorize(OAuth2AuthorizeRequest.withClientRegistrationId("payments").principal("order-service").build());
            request.getHeaders().setBearerAuth(authorized.getAccessToken().getTokenValue());
            return execution.execute(request, body);
        };
        return builder.baseUrl("http://payment-service").requestInterceptor(addServiceToken).build();
    }

    // ---------- 41. propagation: relay the CALLER's JWT to the downstream service
    @Bean
    RestClient paymentClientPropagatingUserToken(RestClient.Builder builder) {
        ClientHttpRequestInterceptor relay = (request, body, execution) -> {
            var auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth instanceof JwtAuthenticationToken jwt) {
                request.getHeaders().set(HttpHeaders.AUTHORIZATION, "Bearer " + jwt.getToken().getTokenValue());
            }
            return execution.execute(request, body);
        };
        return builder.baseUrl("http://payment-service").requestInterceptor(relay).build();
    }
}
// Feign alternative: implement feign.RequestInterceptor and copy the Authorization header from the current request.
// Async hand-offs (@Async, Kafka) lose the SecurityContext: pass the identity explicitly in the message.
