import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.reflect.RecordComponent;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/**
 * 43. INPUT VALIDATION - never trust anything that crosses a trust boundary
 *
 * Validate at the EDGE (controller / gateway), as soon as data enters the service:
 *   - type, length, range, format, allow-list of values  ("allow-list" beats "block-list")
 *   - reject with 400 and a clear field-level message; never echo raw input into HTML/SQL/logs unescaped
 * Validation does NOT replace the other defences:
 *   - SQL injection  -> parameterized queries / JPA, never string concatenation   (Part 2 below)
 *   - XSS            -> output encoding in the UI
 *   - mass assignment-> use dedicated request DTOs, never bind JSON straight onto entities
 *
 * Part 1 re-creates what Bean Validation (@NotBlank, @Size, @Pattern, @Min...) does, using annotations + reflection,
 * so you see there is no magic. Real Spring version: spring_snippets/ValidationSnippets.java
 *
 * Run: java ValidationDemo.java
 */
public class ValidationDemo {

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.RECORD_COMPONENT)
    @interface NotBlank {
    }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.RECORD_COMPONENT)
    @interface Max {
        int value();
    }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.RECORD_COMPONENT)
    @interface Min {
        long value();
    }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.RECORD_COMPONENT)
    @interface Matches {
        String value();
    }

    /** The request DTO: rules are declared next to the data they protect. */
    record TransferRequest(
            @NotBlank @Matches("[A-Z]{2}\\d{10}") String toAccount,
            @Min(1) long amountPaise,
            @NotBlank @Max(140) String note) {
    }

    static List<String> validate(Record r) throws Exception {
        List<String> errors = new ArrayList<>();
        for (RecordComponent c : r.getClass().getRecordComponents()) {
            Object v = c.getAccessor().invoke(r);
            String field = c.getName();
            if (c.isAnnotationPresent(NotBlank.class) && (v == null || v.toString().isBlank())) {
                errors.add(field + ": must not be blank");
                continue;
            }
            Matches m = c.getAnnotation(Matches.class);
            if (m != null && v != null && !Pattern.matches(m.value(), v.toString())) {
                errors.add(field + ": must match " + m.value());
            }
            Max max = c.getAnnotation(Max.class);
            if (max != null && v != null && v.toString().length() > max.value()) {
                errors.add(field + ": length must be <= " + max.value());
            }
            Min min = c.getAnnotation(Min.class);
            if (min != null && ((Number) v).longValue() < min.value()) {
                errors.add(field + ": must be >= " + min.value());
            }
        }
        return errors;
    }

    static void handle(TransferRequest req) throws Exception {
        List<String> errors = validate(req);
        System.out.println("   input : " + req);
        System.out.println("   result: " + (errors.isEmpty() ? "200 OK, processed" : "400 Bad Request " + errors));
    }

    // ---------------------------------------------------------------- Part 2: why parameterized queries matter
    static String vulnerableSql(String user) {
        return "SELECT * FROM users WHERE name = '" + user + "'";           // string concatenation = injection
    }

    static String parameterizedSql(String user) {
        return "SELECT * FROM users WHERE name = ?   -- bound parameter: [" + user + "] is DATA, never SQL";
    }

    public static void main(String[] args) throws Exception {
        System.out.println("PART 1 - declarative validation at the edge");
        handle(new TransferRequest("IN1234567890", 50_000, "rent"));
        handle(new TransferRequest("bad-account", 50_000, "rent"));
        handle(new TransferRequest("IN1234567890", -5, "x".repeat(200)));
        handle(new TransferRequest("", 0, " "));

        System.out.println("\nPART 2 - injection: validation helps, parameterization fixes");
        String attack = "x' OR '1'='1";
        System.out.println("   vulnerable   : " + vulnerableSql(attack));
        System.out.println("                  -> WHERE name = 'x' OR '1'='1'  is always true: every user row is returned");
        System.out.println("   parameterized: " + parameterizedSql(attack));

        System.out.println("\nPART 3 - allow-list beats block-list");
        List<String> allowedSortFields = List.of("date", "amount");          // user may only choose from these
        for (String sort : List.of("amount", "amount; DROP TABLE payments")) {
            System.out.println("   sort=" + sort + " -> " + (allowedSortFields.contains(sort) ? "accepted" : "rejected (not in allow-list)"));
        }
        System.out.println("\nAlso: limit request body size and string lengths (DoS), validate file uploads by content not extension,"
                + "\nand return generic error messages to clients while logging details server-side.");
    }
}
