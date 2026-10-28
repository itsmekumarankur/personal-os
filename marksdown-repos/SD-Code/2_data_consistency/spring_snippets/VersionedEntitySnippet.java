package com.example.snippets;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Version;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Topic 24: optimistic locking with JPA @Version. NOT compiled in the sandbox it was written in.
 * Runnable concept demo: OptimisticLockingDemo.java
 *
 * What Hibernate does for you:
 *   UPDATE account SET balance=?, version=? WHERE id=? AND version=?      (version = the value you loaded)
 * If another transaction changed the row meanwhile, 0 rows match and Spring throws
 * OptimisticLockingFailureException (ObjectOptimisticLockingFailureException).
 */
public class VersionedEntitySnippet {

    @Entity
    static class Account {
        @Id
        Long id;

        long balance;

        @Version                    // Hibernate maintains this column automatically
        long version;
    }

    interface AccountRepository extends JpaRepository<Account, Long> {
    }

    @Service
    static class AccountService {
        private final AccountRepository repo;

        AccountService(AccountRepository repo) {
            this.repo = repo;
        }

        // One attempt = one transaction. On conflict the whole transaction is thrown away and redone.
        @Transactional
        public void deposit(long accountId, long amount) {
            Account a = repo.findById(accountId).orElseThrow();
            a.balance += amount;                               // dirty checking will issue the UPDATE ... WHERE version = ?
        }
    }

    // Retry OUTSIDE the transaction (each retry must start a fresh transaction).
    @Service
    static class DepositFacade {
        private final AccountService service;

        DepositFacade(AccountService service) {
            this.service = service;
        }

        public void depositWithRetry(long accountId, long amount) {
            int attempts = 0;
            while (true) {
                try {
                    service.deposit(accountId, amount);
                    return;
                } catch (OptimisticLockingFailureException e) {
                    if (++attempts >= 3) {
                        throw e;                               // give up: tell the user "please retry"
                    }
                }
            }
        }
        // Alternative: spring-retry @Retryable(retryFor = OptimisticLockingFailureException.class, maxAttempts = 3)
    }

    // REST layer tip: map the exception to HTTP 409 Conflict (or 412 with ETag/If-Match for client-held versions).
}
