package com.example.spring.tx;

import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import javax.sql.DataSource;

/**
 * 5. @Transactional
 *
 * Money transfer = debit + credit. Both must succeed or neither.
 *
 * Shows:
 *  a) No @Transactional  -> failure after the debit leaves money "lost"
 *  b) @Transactional     -> RuntimeException rolls everything back
 *  c) Checked exception  -> by default does NOT roll back (needs rollbackFor)
 *  d) Self-invocation    -> @Transactional is ignored when called via 'this' (proxy bypassed)
 *
 * Rule of thumb: default rollback happens only for RuntimeException and Error.
 */
public class TransactionDemo {

    static class TransferFailedException extends Exception {
        TransferFailedException(String message) {
            super(message);
        }
    }

    @Configuration
    @EnableTransactionManagement
    static class TxConfig {
        @Bean
        DataSource dataSource() {
            return new DriverManagerDataSource("jdbc:h2:mem:bank;DB_CLOSE_DELAY=-1", "sa", "");
        }

        @Bean
        JdbcTemplate jdbcTemplate(DataSource ds) {
            return new JdbcTemplate(ds);
        }

        @Bean
        PlatformTransactionManager transactionManager(DataSource ds) {
            return new DataSourceTransactionManager(ds);
        }
    }

    @Service
    static class BankService {
        private final JdbcTemplate jdbc;

        BankService(JdbcTemplate jdbc) {
            this.jdbc = jdbc;
        }

        public void reset() {
            jdbc.execute("DROP TABLE IF EXISTS account");
            jdbc.execute("CREATE TABLE account (id VARCHAR(10) PRIMARY KEY, balance INT)");
            jdbc.update("INSERT INTO account VALUES ('A', 1000)");
            jdbc.update("INSERT INTO account VALUES ('B', 0)");
        }

        public String balances() {
            int a = jdbc.queryForObject("SELECT balance FROM account WHERE id='A'", Integer.class);
            int b = jdbc.queryForObject("SELECT balance FROM account WHERE id='B'", Integer.class);
            return "A=" + a + ", B=" + b + " (total " + (a + b) + ")";
        }

        private void debit(int amount) {
            jdbc.update("UPDATE account SET balance = balance - ? WHERE id='A'", amount);
        }

        private void credit(int amount) {
            jdbc.update("UPDATE account SET balance = balance + ? WHERE id='B'", amount);
        }

        // a) no transaction: each statement commits on its own
        public void transferWithoutTx(int amount) {
            debit(amount);
            throw new IllegalStateException("crash after debit");
        }

        // b) transactional: RuntimeException => rollback
        @Transactional
        public void transferWithTx(int amount) {
            debit(amount);
            throw new IllegalStateException("crash after debit");
        }

        // c1) checked exception, default rules => COMMIT (debit stays!)
        @Transactional
        public void transferCheckedDefault(int amount) throws TransferFailedException {
            debit(amount);
            throw new TransferFailedException("checked failure after debit");
        }

        // c2) checked exception with rollbackFor => rollback
        @Transactional(rollbackFor = Exception.class)
        public void transferCheckedRollbackFor(int amount) throws TransferFailedException {
            debit(amount);
            throw new TransferFailedException("checked failure after debit");
        }

        // d) self-invocation
        public void outerWithoutTx() {
            this.inner(); // proxy bypassed -> no transaction is started
        }

        @Transactional
        public void inner() {
            System.out.println("    transaction active inside inner()? "
                    + TransactionSynchronizationManager.isActualTransactionActive());
        }
    }

    interface ThrowingRunnable {
        void run() throws Exception;
    }

    private static void attempt(BankService bank, String title, ThrowingRunnable action) {
        bank.reset();
        System.out.println(title);
        try {
            action.run();
        } catch (Exception e) {
            System.out.println("    exception: " + e.getMessage());
        }
        System.out.println("    balances : " + bank.balances());
    }

    public static void main(String[] args) {
        try (var ctx = new AnnotationConfigApplicationContext(TxConfig.class, BankService.class)) {
            BankService bank = ctx.getBean(BankService.class);

            attempt(bank, "a) no @Transactional (partial update, money lost):",
                    () -> bank.transferWithoutTx(300));
            attempt(bank, "b) @Transactional + RuntimeException (rolled back):",
                    () -> bank.transferWithTx(300));
            attempt(bank, "c1) @Transactional + checked exception (NOT rolled back):",
                    () -> bank.transferCheckedDefault(300));
            attempt(bank, "c2) @Transactional(rollbackFor = Exception.class) (rolled back):",
                    () -> bank.transferCheckedRollbackFor(300));

            System.out.println("d) self-invocation pitfall:");
            System.out.println("  outerWithoutTx() calling this.inner():");
            bank.outerWithoutTx();
            System.out.println("  calling inner() through the proxy:");
            bank.inner();
        }
    }
}
