# Security - topics 38 to 43

## Runnable demos (plain Java, JDK 17+, no dependencies): `java File.java`

| # | File | Topic | What you see |
|---|---|---|---|
| 38 | `JwtDemo.java` | JWT | Hand-built HS256 token; tampered payload, `alg=none`, expired and garbage tokens all rejected |
| 39 | `RoleScopeCheckDemo.java` | Resource server, roles and scopes | Real HTTP server: 401 vs 403, role check, scope check, least privilege |
| 40 | `ClientCredentialsDemo.java` | OAuth2 client credentials (and OIDC notes) | Auth server + API; token cache refreshes before expiry; wrong secret, wrong scope, expired token |
| 41 | `TokenPropagationDemo.java` | Token propagation | Gateway-like chain relays user identity; the "forgot to forward" bug |
| 42 | `SecretsDemo.java` | Secrets handling | Masked `Secret` type, env/file loading, fail-fast, log masking |
| 43 | `ValidationDemo.java` | Input validation | Annotation validation by reflection, SQL injection vs parameters, allow-lists |

## `spring_snippets/` (NOT compiled or run by the author)

| File | Topic |
|---|---|
| `ResourceServerConfig.java` | #38 #39 JWT resource server, scopes, roles claim mapping, `@PreAuthorize` |
| `OAuth2ClientSnippets.java` | #40 #41 client-credentials `RestClient`, relaying the user token, OIDC config notes |
| `ValidationSnippets.java` | #43 `@Valid`, Bean Validation, `@RestControllerAdvice` returning Problem Details |

## Honest limits
- `JwtDemo` uses HS256 with a shared secret for clarity. Production should use RS256/ES256 with a JWKS endpoint and verify `iss` and `aud`.
- Demos teach the mechanics; use a vetted library (Spring Security, Nimbus) and an identity provider (Keycloak, Auth0, Entra) in real systems. Never write your own crypto.
- If a snippet does not compile for your versions, send the error and it will be fixed.
