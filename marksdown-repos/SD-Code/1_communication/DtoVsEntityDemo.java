import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.StringJoiner;

/**
 * 
 * We are learning why DTOs and Entities should be separate in microservices. 
 * An Entity stores a service’s internal database data, including sensitive fields, while a DTO exposes only the data that other services need.
 * Even if the internal database structure changes, the DTO keeps the API contract stable, 
 * preventing other services from breaking and protecting sensitive information. 
 * In simple words: keep internal data private and share only the required data through DTOs.
 * 
         BAD APPROACH: Returning Entity Directly

              Account Service
                    |
                    v
              Account Entity
          +--------------------+
          | id                 |
          | ownerName          |
          | passwordHash       |  <-- Sensitive!
          | balancePaise       |
          | fraudFlag          |  <-- Internal!
          +--------------------+
                    |
                    v
              API Response
                    |
                    v
             Other Services
          Internal data exposed!
          Changes may break clients


        GOOD APPROACH: Returning DTO

              Account Service
                    |
                    v
              Account Entity
          +--------------------+
          | id                 |
          | ownerName          |
          | passwordHash       |
          | balancePaise       |
          | fraudFlag          |
          +--------------------+
                    |
                    v
              Entity -> DTO
                    |
                    v
              Account DTO
          +--------------------+
          | id                 |
          | owner              |
          | balance            |
          +--------------------+
                    |
                    v
              API Response
                    |
                    v
             Other Services
          Only required data shared
          Internal changes stay hidden

 */
public class DtoVsEntityDemo {

    // ---- Internal entity, version 1 ----
    static class AccountEntityV1 {
        Long id = 42L;
        String ownerName = "Ankur";
        String passwordHash = "$2a$10$abc...secret-hash";   // must NEVER leave the service
        long balancePaise = 100_000;                         // stored in paise
        int version = 7;                                     // optimistic-lock counter
        boolean fraudFlag = false;                           // internal risk decision
    }

    // ---- Same entity after an internal refactor (renamed + new internal field) ----
    static class AccountEntityV2 {
        Long id = 42L;
        String ownerName = "Ankur";
        String passwordHash = "$2a$10$abc...secret-hash";
        long balanceMinorUnits = 100_000;                    // RENAMED
        int version = 7;
        boolean fraudFlag = false;
        double internalRiskScore = 0.12;                     // NEW
    }

    // ---- The public contract ----
    record AccountDto(String id, String owner, String balance) {
        static AccountDto from(AccountEntityV1 e) {
            return new AccountDto(String.valueOf(e.id), e.ownerName, String.format("%.2f", e.balancePaise / 100.0));
        }

        static AccountDto from(AccountEntityV2 e) {          // mapper adapts; the CONTRACT stays the same
            return new AccountDto(String.valueOf(e.id), e.ownerName, String.format("%.2f", e.balanceMinorUnits / 100.0));
        }
    }

    // tiny reflection-based JSON, only to print objects
    static String toJson(Object o) throws Exception {
        StringJoiner json = new StringJoiner(",", "{", "}");
        for (Field f : o.getClass().getDeclaredFields()) {
            if (Modifier.isStatic(f.getModifiers()) || f.isSynthetic()) {
                continue;
            }
            f.setAccessible(true);
            Object v = f.get(o);
            String value = (v instanceof Number || v instanceof Boolean) ? String.valueOf(v) : "\"" + v + "\"";
            json.add("\"" + f.getName() + "\":" + value);
        }
        return json.toString();
    }

    public static void main(String[] args) throws Exception {
        System.out.println("1) BAD: API returns the entity directly");
        System.out.println("   " + toJson(new AccountEntityV1()));
        System.out.println("   -> leaks passwordHash, version, fraudFlag to every caller\n");

        System.out.println("2) The owning team refactors storage (rename + add a field). Entity JSON changes:");
        System.out.println("   " + toJson(new AccountEntityV2()));
        System.out.println("   -> consumers that read 'balancePaise' are now broken, with no warning\n");

        System.out.println("3) GOOD: API returns a DTO. Only the promised fields, same shape before and after the refactor:");
        System.out.println("   before refactor: " + toJson(AccountDto.from(new AccountEntityV1())));
        System.out.println("   after  refactor: " + toJson(AccountDto.from(new AccountEntityV2())));

        System.out.println("\nRules:");
        System.out.println("  - one service OWNS its entities; others only see DTOs/events (the contract)");
        System.out.println("  - map at the boundary (MapStruct or hand-written mappers)");
        System.out.println("  - use different DTOs for requests and responses (clients must not be able to set 'version' or 'fraudFlag')");
        System.out.println("  - don't share entity JARs between services; share contracts (OpenAPI / .proto / event schemas) instead");
    }
}
