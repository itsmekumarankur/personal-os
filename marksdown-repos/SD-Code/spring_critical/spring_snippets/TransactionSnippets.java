import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/**
 * 3. Propagation, isolation, readOnly. NOT compiled or run by the author.
 * Dependency: spring-boot-starter-data-jpa (or -jdbc)
 *
 * Remember: @Transactional works through a PROXY, so it only applies when the method is called FROM ANOTHER BEAN,
 * and the method must be public. Calling this.audit(...) inside the same class does NOT start a new transaction.
 * That is why AuditService below is a separate class.
 */
@Service
class TransferService {
    private final AuditService audit;
    private final AccountRepo accounts;

    TransferService(AuditService audit, AccountRepo accounts) { this.audit = audit; this.accounts = accounts; }

    @Transactional                                                        // REQUIRED by default; rolls back on RuntimeException/Error only
    public void transfer(String from, String to, long amount) {
        audit.record("transfer attempt " + from + "->" + to + " " + amount);   // committed independently (REQUIRES_NEW)
        accounts.debit(from, amount);
        accounts.credit(to, amount);                                      // if this throws, debit rolls back but the audit row stays
    }

    @Transactional(rollbackFor = Exception.class)                         // also roll back on CHECKED exceptions
    public void transferWithCheckedException(String from, String to, long amount) throws java.io.IOException { }

    @Transactional(readOnly = true)                                       // hint: no flush, can route to a read replica, cheaper
    public long balance(String account) { return accounts.balance(account); }

    @Transactional(isolation = Isolation.REPEATABLE_READ, timeout = 5)    // stricter snapshot + give up after 5 seconds
    public void monthEndReport() { }
}

@Service
class AuditService {
    private final AuditRepo repo;
    AuditService(AuditRepo repo) { this.repo = repo; }

    @Transactional(propagation = Propagation.REQUIRES_NEW)                // suspends the caller's transaction, commits on its own
    public void record(String message) { repo.save(message); }
}

interface AccountRepo { void debit(String a, long x); void credit(String a, long x); long balance(String a); }
interface AuditRepo { void save(String m); }

/*
 * The "outer catches inner" gotcha:
 *
 *   @Transactional public void outer() {
 *       try { inner.validate(); }                // inner is @Transactional (REQUIRED) and throws
 *       catch (Exception e) { /* swallow *\/ }
 *       repo.save(x);
 *   }                                             // -> UnexpectedRollbackException on commit
 *
 * Fixes: let the exception propagate, make inner non-transactional, or give inner REQUIRES_NEW if it must fail alone.
 *
 * Also: never call remote services (HTTP, Kafka) inside a long transaction. You hold a database connection the whole time.
 * Publish events AFTER commit:  @TransactionalEventListener(phase = AFTER_COMMIT)  (see the outbox pattern in 2_data_consistency).
 */
