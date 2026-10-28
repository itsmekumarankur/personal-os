import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

/**
 * 6. @Async AND THREAD POOLS - four traps
 *
 * @Async = "run this method on another thread and let me continue". Like handing a parcel to a courier.
 * Spring does it with a PROXY that submits your method to a TaskExecutor (thread pool). Imitated here.
 *
 *   A) WORKS: the caller returns immediately, the work happens on "task-N".
 *   B) CONTEXT LOSS: ThreadLocal data (logged-in user, trace id, transaction, SecurityContext) does NOT follow the
 *      work to the new thread. Fix: a TaskDecorator that copies it.
 *   C) LOST EXCEPTIONS: a void @Async method that throws is only logged; the caller never knows.
 *      Fix: return CompletableFuture, or register an AsyncUncaughtExceptionHandler.
 *   D) POOL EXHAUSTION: bounded pool + bounded queue. When full: reject (error) or CallerRuns (back-pressure).
 *      Never use an unbounded pool/queue in production: that is how servers run out of memory.
 *
 * Real Spring version: spring_snippets/AsyncSnippets.java
 * Run: java AsyncExecutorDemo.java
 */
public class AsyncExecutorDemo {

    @Retention(RetentionPolicy.RUNTIME) @interface Async { }

    static final ThreadLocal<String> CURRENT_USER = new ThreadLocal<>();
    static final AtomicInteger THREAD_IDS = new AtomicInteger();

    static String thread() { return Thread.currentThread().getName(); }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException ignored) { } }

    interface Notifier {
        @Async void sendSms(String to);
        @Async void failingJob();
        @Async CompletableFuture<String> sendEmail(String to);
    }

    static class NotifierImpl implements Notifier {
        public void sendSms(String to) {
            sleep(30);
            System.out.println("      [" + thread() + "] SMS to " + to + ", acting for user=" + CURRENT_USER.get());
        }
        public void failingJob() { throw new IllegalStateException("SMS gateway timeout"); }
        public CompletableFuture<String> sendEmail(String to) {
            if (to.startsWith("bad")) throw new IllegalArgumentException("invalid address " + to);
            return CompletableFuture.completedFuture("email queued for " + to);
        }
    }

    interface Work { Object run() throws Throwable; }

    static Object invoke(Object target, Method m, Object[] a) throws Throwable {
        try { return m.invoke(target, a); } catch (InvocationTargetException e) { throw e.getCause(); }
    }

    /** The @Async proxy. */
    @SuppressWarnings("unchecked")
    static Notifier asyncProxy(Notifier target, ExecutorService pool, boolean copyContext, Consumer<Throwable> uncaughtHandler) {
        return (Notifier) Proxy.newProxyInstance(Notifier.class.getClassLoader(), new Class<?>[]{Notifier.class}, (p, m, a) -> {
            if (!m.isAnnotationPresent(Async.class)) return invoke(target, m, a);
            String userAtCallTime = CURRENT_USER.get();                               // captured on the CALLER's thread
            Work work = () -> {
                if (copyContext) CURRENT_USER.set(userAtCallTime);                    // the "TaskDecorator"
                try { return invoke(target, m, a); } finally { CURRENT_USER.remove(); }
            };
            if (m.getReturnType() == CompletableFuture.class) {
                CompletableFuture<String> future = new CompletableFuture<>();
                pool.execute(() -> {
                    try { future.complete(((CompletableFuture<String>) work.run()).join()); }
                    catch (Throwable t) { future.completeExceptionally(t); }
                });
                return future;
            }
            pool.execute(() -> {
                try { work.run(); } catch (Throwable t) { if (uncaughtHandler != null) uncaughtHandler.accept(t); }
            });
            return null;                                                              // void: caller gets nothing back
        });
    }

    static ThreadPoolExecutor pool(int core, int max, int queue, RejectedExecutionHandler policy) {
        return new ThreadPoolExecutor(core, max, 0, TimeUnit.SECONDS, new ArrayBlockingQueue<>(queue),
                r -> new Thread(r, "task-" + THREAD_IDS.incrementAndGet()), policy);
    }

    public static void main(String[] args) throws Exception {
        Thread.currentThread().setName("main");
        CURRENT_USER.set("ankur");
        Notifier service = new NotifierImpl();

        System.out.println("A) @Async: caller returns at once, work runs elsewhere");
        ThreadPoolExecutor p = pool(2, 2, 10, new ThreadPoolExecutor.AbortPolicy());
        Notifier async = asyncProxy(service, p, true, null);
        System.out.println("      [" + thread() + "] calling sendSms ...");
        async.sendSms("+91-98xxxxxx");
        System.out.println("      [" + thread() + "] ...returned immediately, doing other work");
        p.shutdown(); p.awaitTermination(2, TimeUnit.SECONDS);

        System.out.println("\nB) CONTEXT LOSS: ThreadLocal user on the worker thread");
        p = pool(1, 1, 10, new ThreadPoolExecutor.AbortPolicy());
        System.out.println("   without decorator:");
        asyncProxy(service, p, false, null).sendSms("customer-1");
        p.shutdown(); p.awaitTermination(2, TimeUnit.SECONDS);
        p = pool(1, 1, 10, new ThreadPoolExecutor.AbortPolicy());
        System.out.println("   with TaskDecorator that copies the user:");
        asyncProxy(service, p, true, null).sendSms("customer-1");
        p.shutdown(); p.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("   (Same story for the SecurityContext, MDC logging ids, and the current transaction.)");

        System.out.println("\nC) LOST EXCEPTIONS");
        p = pool(1, 1, 10, new ThreadPoolExecutor.AbortPolicy());
        Notifier voidStyle = asyncProxy(service, p, false, t -> System.out.println("      [default handler] ERROR logged: " + t.getMessage()));
        voidStyle.failingJob();
        System.out.println("      [main] void method: no exception here, caller believes everything is fine");
        Thread.sleep(100);
        Notifier futureStyle = asyncProxy(service, p, false, null);
        futureStyle.sendEmail("bad@@address").whenComplete((ok, err) ->
                System.out.println("      [main-callback] CompletableFuture style: caller IS told -> " + (err == null ? ok : err.getMessage())));
        Thread.sleep(100);
        p.shutdown(); p.awaitTermination(2, TimeUnit.SECONDS);

        System.out.println("\nD) POOL EXHAUSTION: core=2, max=3, queue=2, and 7 slow tasks arrive together");
        for (boolean callerRuns : new boolean[]{false, true}) {
            RejectedExecutionHandler policy = callerRuns ? new ThreadPoolExecutor.CallerRunsPolicy() : new ThreadPoolExecutor.AbortPolicy();
            ThreadPoolExecutor tpe = pool(2, 3, 2, policy);
            List<String> outcome = Collections.synchronizedList(new ArrayList<>());
            for (int i = 1; i <= 7; i++) {
                final int id = i;
                try {
                    tpe.execute(() -> { sleep(200); outcome.add("task " + id + " ran on " + thread()); });
                } catch (RejectedExecutionException e) {
                    outcome.add("task " + id + " REJECTED (RejectedExecutionException)");
                }
            }
            tpe.shutdown(); tpe.awaitTermination(3, TimeUnit.SECONDS);
            Collections.sort(outcome);
            System.out.println("   policy = " + (callerRuns ? "CallerRunsPolicy (slows the caller = back-pressure)" : "AbortPolicy (fail fast)"));
            outcome.forEach(o -> System.out.println("      " + o));
        }
        System.out.println("\nRule of thumb: threads beyond 'core' are created only AFTER the queue is full. Size pools for the work type,"
                + "\nname the threads, expose pool metrics, and on Java 21+ consider virtual threads for blocking I/O.");
    }
}
