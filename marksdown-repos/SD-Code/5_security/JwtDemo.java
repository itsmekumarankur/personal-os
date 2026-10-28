import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * 38. JWT (JSON Web Token) - built by hand so there is no magic
 *
 * A JWT is three Base64URL parts joined by dots:   HEADER . PAYLOAD . SIGNATURE
 *   header    {"alg":"HS256","typ":"JWT"}
 *   payload   {"sub":"ankur","roles":["USER"],"exp":1700000000}      <- "claims"
 *   signature HMAC-SHA256(secret, header + "." + payload)
 *
 * KEY FACTS
 *   - The payload is only ENCODED, not encrypted: anyone can read it. Never put secrets in it.
 *   - The signature proves it was issued by someone who knows the key and was NOT modified.
 *   - Services verify the token WITHOUT calling the auth server => stateless, scales well.
 *   - Price: you cannot easily revoke one before it expires => keep access tokens SHORT (5-15 min).
 *   - HS256 = shared secret (both sides know it). Real systems usually use RS256/ES256:
 *     the auth server signs with a PRIVATE key, services verify with the PUBLIC key (JWKS endpoint).
 *
 * Run: java JwtDemo.java
 */
public class JwtDemo {

    static final byte[] SECRET = "demo-secret-at-least-32-bytes-long!!".getBytes(StandardCharsets.UTF_8);
    static final Base64.Encoder B64 = Base64.getUrlEncoder().withoutPadding();
    static final Base64.Decoder B64D = Base64.getUrlDecoder();

    // ------------------------------------------------------------------ tiny JSON helpers (flat objects only)
    static String json(Map<String, Object> m) {
        StringBuilder sb = new StringBuilder("{");
        m.forEach((k, v) -> {
            if (sb.length() > 1) sb.append(',');
            sb.append('"').append(k).append("\":");
            if (v instanceof Number) sb.append(v);
            else if (v instanceof String[] arr) {
                sb.append('[');
                for (int i = 0; i < arr.length; i++) sb.append(i > 0 ? "," : "").append('"').append(arr[i]).append('"');
                sb.append(']');
            } else sb.append('"').append(v).append('"');
        });
        return sb.append('}').toString();
    }

    static String claim(String payloadJson, String key) {          // naive reader, enough for this demo
        int i = payloadJson.indexOf("\"" + key + "\":");
        if (i < 0) return null;
        int start = i + key.length() + 3;
        char first = payloadJson.charAt(start);
        if (first == '"') return payloadJson.substring(start + 1, payloadJson.indexOf('"', start + 1));
        if (first == '[') return payloadJson.substring(start, payloadJson.indexOf(']', start) + 1);
        int end = start;
        while (end < payloadJson.length() && "0123456789".indexOf(payloadJson.charAt(end)) >= 0) end++;
        return payloadJson.substring(start, end);
    }

    // ------------------------------------------------------------------ sign
    static String hmac(String data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(SECRET, "HmacSHA256"));
        return B64.encodeToString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
    }

    static String issue(String subject, String[] roles, long ttlSeconds) throws Exception {
        String header = B64.encodeToString("{\"alg\":\"HS256\",\"typ\":\"JWT\"}".getBytes(StandardCharsets.UTF_8));
        Map<String, Object> claims = new LinkedHashMap<>();
        claims.put("sub", subject);
        claims.put("roles", roles);
        claims.put("iat", Instant.now().getEpochSecond());
        claims.put("exp", Instant.now().getEpochSecond() + ttlSeconds);
        String payload = B64.encodeToString(json(claims).getBytes(StandardCharsets.UTF_8));
        return header + "." + payload + "." + hmac(header + "." + payload);
    }

    // ------------------------------------------------------------------ verify
    record Verified(boolean valid, String reason, String payloadJson) {
    }

    static Verified verify(String token) {
    /**
    *              +-------------------------------+
    *              | 3. Verification scenarios     |
    *              +---------------+---------------+
    *                              |
    *          +-------------------+--------------------+
    *          |                   |                    |
    *          v                   v                    v
    *    +-------------+    +---------------+    +----------------+
    *    | Valid JWT   |    | Tampered JWT  |    | alg = none     |
    *    |             |    |               |    |                |
    *    | Original    |    | Change roles  |    | Change header  |
    *    | signature   |    | to ADMIN      |    | Remove signing |
    *    +------+------+    +-------+-------+    +--------+-------+
    *           |                   |                     |
    *           v                   v                     v
    *    Signature valid?    Signature mismatch?    Algorithm rejected?
    *           |                   |                     |
    *           v                   v                     v
    *       ACCEPTED             REJECTED              REJECTED
    */
        try {
            String[] parts = token.split("\\.", -1);          // -1 keeps a trailing empty signature part
            if (parts.length != 3) return new Verified(false, "malformed token", null);
            String headerJson = new String(B64D.decode(parts[0]), StandardCharsets.UTF_8);
            if (!headerJson.contains("\"HS256\"")) {
                return new Verified(false, "rejected algorithm (never trust the alg from the token, e.g. 'none')", null);
            }
            byte[] expected = hmac(parts[0] + "." + parts[1]).getBytes(StandardCharsets.UTF_8);
            // constant-time comparison: avoids leaking how many leading characters matched
            if (!MessageDigest.isEqual(expected, parts[2].getBytes(StandardCharsets.UTF_8))) {
                return new Verified(false, "signature mismatch (token was tampered with or signed by someone else)", null);
            }
            String payload = new String(B64D.decode(parts[1]), StandardCharsets.UTF_8);
            long exp = Long.parseLong(claim(payload, "exp"));
            if (Instant.now().getEpochSecond() >= exp) return new Verified(false, "expired", payload);
            return new Verified(true, "ok", payload);
        } catch (Exception e) {
            return new Verified(false, "malformed token (" + e.getClass().getSimpleName() + ")", null);
        }
    }

    static void show(String label, String token) {
        Verified v = verify(token);
        System.out.println("   " + label + " -> " + (v.valid() ? "ACCEPTED, user=" + claim(v.payloadJson(), "sub")
                + " roles=" + claim(v.payloadJson(), "roles") : "REJECTED: " + v.reason()));
    }

    public static void main(String[] args) throws Exception {

    /**
    *              +-------------------------------+
    *              | 1. Generate JWT               |
    *              |                               |
    *              | issue("ankur",                |
    *              |       ["USER","MANAGER"], 900)|
    *              +---------------+---------------+
    *                              |
    *                              v
    *              +-------------------------------+
    *              | Build JWT Header              |
    *              | {"alg":"HS256","typ":"JWT"}   |
    *              +---------------+---------------+
    *                              |
    *                              v
    *              +-------------------------------+
    *              | Build JWT Payload              |
    *              | sub   = ankur                  |
    *              | roles = USER, MANAGER          |
    *              | iat   = issued-at time         |
    *              | exp   = current time + 900 sec |
    *              +---------------+---------------+
    */
        String token = issue("ankur", new String[]{"USER", "MANAGER"}, 900);
        String[] p = token.split("\\.");

        System.out.println("1) A token (3 parts):");
        System.out.println("   header   : " + p[0] + "  =  " + new String(B64D.decode(p[0])));
        System.out.println("   payload  : " + p[1].substring(0, 30) + "...  =  " + new String(B64D.decode(p[1])));
        System.out.println("   signature: " + p[2]);
        System.out.println("   Anyone can decode header and payload. Only the key holder can create a valid signature.\n");
    /**
     *              +-------------------------------+
     *              | Base64URL encode header       |
     *              | Base64URL encode payload      |
     *              +---------------+---------------+
     *                              |
     *                              v
     *              +-------------------------------+
     *              | Sign header.payload            |
     *              | HMAC-SHA256 using SECRET       |
     *              +---------------+---------------+
     *                              |
     *                              v
     *              +-------------------------------+
     *              | Assemble JWT                   |
     *              | HEADER.PAYLOAD.SIGNATURE       |
     *              +---------------+---------------+
     *                              |
     *                              v
     *              +-------------------------------+
     *              | 2. Split token into 3 parts   |
     *              | p[0] = Header                 |
     *              | p[1] = Payload                |
     *              | p[2] = Signature              |
     *              +---------------+---------------+
     *                              |
     *                              v
     *              +-------------------------------+
     *              | Print token components        |
     *              | Decode header and payload     |
     *              | Print signature               |
     *              +---------------+---------------+
     * 
    */
        System.out.println("2) Verification outcomes:");
        show("valid token                         ", token);

        String forgedPayload = B64.encodeToString(("{\"sub\":\"ankur\",\"roles\":[\"ADMIN\"],\"iat\":1,\"exp\":"
                + (Instant.now().getEpochSecond() + 9999) + "}").getBytes(StandardCharsets.UTF_8));
        show("attacker edits payload to ADMIN     ", p[0] + "." + forgedPayload + "." + p[2]);

        String noneHeader = B64.encodeToString("{\"alg\":\"none\",\"typ\":\"JWT\"}".getBytes(StandardCharsets.UTF_8));
        show("attacker uses alg=none, no signature", noneHeader + "." + p[1] + ".");
        /**
        *              +--------------------------------+
        *              | 4. Create expired JWT          |
        *              | issue("ankur", ["USER"], -1)   |
        *              +----------------+---------------+
        *                               |
        *                               v
        *                       Verify expiration
        *                               |
        *                               v
        *                           REJECTED
        *
        *              +--------------------------------+
        *              | 5. Verify garbage input        |
        *              | "not-a-jwt"                    |
        *              +----------------+---------------+
        *                               |
        *                               v
        *                       Token has 3 parts?
        *                               |
        *                               v
        *                           REJECTED
        *
        *              +--------------------------------+
        *              | 6. Print security takeaways    |
        *              | - Verify signature             |
        *              | - Check expiration              |
        *              | - Pin allowed algorithm         |
        *              | - Validate iss/aud in production|
        *              | - Use HTTPS                    |
        *              +----------------+---------------+
        *                               |
        *                               v
        *                              END
        * 
        */

        String expired = issue("ankur", new String[]{"USER"}, -1);
        show("expired token                       ", expired);
        show("garbage                             ", "not-a-jwt");

        System.out.println("\n3) Takeaways: verify signature, verify exp (and iss/aud in real systems), pin the algorithm, "
                + "keep tokens short-lived, send over HTTPS only, never log them.");
    }
}
