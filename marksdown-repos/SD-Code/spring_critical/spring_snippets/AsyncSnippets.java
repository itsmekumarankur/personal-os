import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;
import org.slf4j.MDC;
import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.TaskDecorator;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.security.task.DelegatingSecurityContextAsyncTaskExecutor;
import org.springframework.stereotype.Service;

/**
 * 6. @Async with a properly sized pool. NOT compiled or run by the author.
 * Dependency: spring-boot-starter (spring-security-core for the security-context executor wrapper).
 *
 * Defaults to remember: without your own executor Spring Boot provides one with core=8 and an UNBOUNDED queue
 * (older Spring used one new thread per task). Configure it explicitly.
 */
@Configuration
@EnableAsync
class AsyncConfig implements AsyncConfigurer {

    @Bean("notificationExecutor")
    ThreadPoolTaskExecutor notificationExecutor() {
        ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(4);
        ex.setMaxPoolSize(8);
        ex.setQueueCapacity(100);                                          // bounded queue
        ex.setThreadNamePrefix("notify-");                                 // readable thread dumps and logs
        ex.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());   // back-pressure instead of dropping work
        ex.setTaskDecorator(mdcCopyingDecorator());                        // carry log context to the worker thread
        ex.setWaitForTasksToCompleteOnShutdown(true);                      // graceful shutdown
        ex.setAwaitTerminationSeconds(20);
        return ex;
    }

    static TaskDecorator mdcCopyingDecorator() {
        return runnable -> {
            var context = MDC.getCopyOfContextMap();
            return () -> {
                if (context != null) MDC.setContextMap(context);
                try { runnable.run(); } finally { MDC.clear(); }
            };
        };
    }

    /** Keeps the logged-in user (SecurityContext) on async threads. */
    @Bean("securityAwareExecutor")
    Executor securityAwareExecutor(ThreadPoolTaskExecutor notificationExecutor) {
        return new DelegatingSecurityContextAsyncTaskExecutor(notificationExecutor);
    }

    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {   // only used for void @Async methods
        return (ex, method, params) -> System.err.println("Async failure in " + method.getName() + ": " + ex.getMessage());
    }
}

@Service
class NotificationService {

    @Async("notificationExecutor")                                          // fire and forget (void)
    public void sendSms(String to) { }

    @Async("notificationExecutor")                                          // caller can handle the result or failure
    public CompletableFuture<String> sendEmail(String to) {
        return CompletableFuture.completedFuture("queued");
    }
}

/*
 * Rules:
 *  - @Async only works on public methods called from ANOTHER bean (proxy), same as @Transactional and @Cacheable.
 *  - The new thread has NO transaction of the caller. If the async method needs one, annotate it with @Transactional itself.
 *    And do not start async work inside a transaction that may still roll back: use @TransactionalEventListener(AFTER_COMMIT).
 *  - Java 21 + Boot 3.2: spring.threads.virtual.enabled=true switches executors to virtual threads (good for blocking I/O).
 */
