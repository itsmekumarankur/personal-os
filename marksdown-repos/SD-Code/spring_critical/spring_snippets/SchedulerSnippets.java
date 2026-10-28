import net.javacrumbs.shedlock.core.LockProvider;
import net.javacrumbs.shedlock.provider.jdbctemplate.JdbcTemplateLockProvider;
import net.javacrumbs.shedlock.spring.annotation.EnableSchedulerLock;
import net.javacrumbs.shedlock.spring.annotation.SchedulerLock;
import javax.sql.DataSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 7. @Scheduled in a cluster with ShedLock. NOT compiled or run by the author.
 * Dependencies: net.javacrumbs.shedlock:shedlock-spring and net.javacrumbs.shedlock:shedlock-provider-jdbc-template
 *
 * Table (one row per job name):
 *   CREATE TABLE shedlock(name VARCHAR(64) PRIMARY KEY, lock_until TIMESTAMP(3) NOT NULL,
 *                         locked_at TIMESTAMP(3) NOT NULL, locked_by VARCHAR(255) NOT NULL);
 */
@Configuration
@EnableScheduling
@EnableSchedulerLock(defaultLockAtMostFor = "PT10M")
class SchedulingConfig {
    @Bean
    LockProvider lockProvider(DataSource dataSource) {
        return new JdbcTemplateLockProvider(JdbcTemplateLockProvider.Configuration.builder()
                .withJdbcTemplate(new JdbcTemplate(dataSource))
                .usingDbTime()                                           // use the DB clock: avoids clock skew between pods
                .build());
    }
}

@Component
class SettlementJob {

    @Scheduled(cron = "0 0 2 * * *", zone = "Asia/Kolkata")               // every day 02:00 IST
    @SchedulerLock(name = "dailySettlement", lockAtMostFor = "PT30M", lockAtLeastFor = "PT1M")
    public void run() {
        // only ONE pod in the cluster executes this per trigger. Keep the work idempotent anyway.
    }

    @Scheduled(fixedDelayString = "PT30S")                                 // wait 30s AFTER the previous run finished
    @SchedulerLock(name = "pollPartnerFile", lockAtMostFor = "PT5M")
    public void poll() { }

    // fixedRate = start every N ms measured start-to-start; long jobs then run back to back, or pile up with a multi-thread scheduler.
}

/*
 * Config: spring.task.scheduling.pool.size=4 (default is ONE thread: a slow job delays every other @Scheduled job).
 * Alternatives: Kubernetes CronJob (one pod per run, simplest for heavy jobs), Quartz with a JDBC job store,
 * or a workflow engine for long, multi-step jobs.
 */
