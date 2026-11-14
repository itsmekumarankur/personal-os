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

    /** The @Async proxy. 
     * 
     * Ye code **Spring ke `@Async` mechanism ko manually simulate** kar raha hai using a **Proxy**. 
     * Simple words mein, jab koi method call hota hai, Proxy pehle check karta hai ki method par `@Async` annotation hai ya nahi.
     * Agar nahi hai, toh method normally same thread mein execute hota hai. 
     * Agar `@Async` hai, toh Proxy current user ka context (`CURRENT_USER`) capture karta hai aur, agar required ho, 
     * us context ko new worker thread mein copy karta hai—ye `TaskDecorator` jaisa kaam karta hai. 
     * Phir actual method ko direct run karne ke bajaye **Thread Pool** mein submit kar deta hai, isliye caller ko wait nahi karna padta. 
     * Agar method `CompletableFuture` return karta hai, toh Proxy future ke through success ya error caller tak bhej deta hai. 
     * Lekin agar method `void` return karta hai, toh caller ko koi result ya exception directly nahi milta; error ko sirf configured exception 
     * handler handle karta hai. **Main lesson: Proxy `@Async` method calls ko intercept karke unhe background thread mein bhejta hai, 
     * context copy karta hai, aur method ke return type ke hisaab se result ya exception handle karta hai.**
     * 
    */
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


/**
 * 
 * HENGLISH SUMMARY:
 This code is teaching how Spring's `@Async` works internally and what four problems can happen when we execute methods asynchronously using a separate thread pool. Normally, jab hum kisi method ko call karte hain, toh caller wait karta hai jab tak method complete nahi hota. Lekin `@Async` lagane par Spring Proxy method ko ek separate thread par execute karne ke liye TaskExecutor (Thread Pool) ko de deta hai, aur caller apna next work immediately continue kar sakta hai. Lekin ismein 4 important traps hain: (1) Context Loss: Main thread mein logged-in user, SecurityContext, transaction ya Trace ID stored hai, toh woh automatically worker thread mein transfer nahi hota; iske liye `TaskDecorator` use karte hain. (2) Lost Exceptions: Agar `void @Async` method fail ho jaata hai, toh caller ko exception directly pata nahi chalta; isliye `CompletableFuture` ya `AsyncUncaughtExceptionHandler` use karna chahiye. (3) Pool Exhaustion: Agar saare threads busy hain aur queue bhi full ho gayi, toh naye tasks reject ho sakte hain; iske liye `AbortPolicy` task ko reject karta hai, jabki `CallerRunsPolicy` caller se hi task execute karwata hai, jisse back-pressure create hota hai. (4) Thread Pool Sizing: Production mein unlimited threads ya unbounded queue nahi rakhni chahiye, warna server memory exhaustion ka shikaar ho sakta hai. Code ka main purpose ye samjhana hai ki `@Async` sirf method ko background mein run karne ka feature nahi hai; production mein context propagation, exception handling, thread pool capacity aur back-pressure ko properly manage karna bhi zaroori hai.
 * 
*/


/**
                          JAVA / SPRING @Async
                                  |
                                  v
                    Caller calls an @Async method
                                  |
                                  v
                       +-------------------+
                       |  SPRING PROXY     |
                       | intercepts call   |
                       +-------------------+
                                  |
                  Caller returns immediately
                  and continues other work
                                  |
                    Task submitted to
                                  v
                       +-------------------+
                       |   THREAD POOL     |
                       | TaskExecutor      |
                       +-------------------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
              WORKER THREAD               CALLER THREAD
              (task-1/task-2)             continues work
                    |
                    v
              Execute @Async Method
                    |
     +--------------+---------------+----------------+
     |              |               |                |
     v              v               v                v

  A) WORKS      B) CONTEXT       C) EXCEPTIONS    D) POOL LIMIT
                 LOSS
     |              |               |                |
     v              v               v                v
 Method runs     ThreadLocal      void method      Threads busy?
 elsewhere       data does NOT    exception may         |
                 automatically    be lost/logged       v
 Caller is       move to new          |            Queue full?
 FREE!           thread               |                |
                    |           +-----+-----+     +----+-----+
                    v           |           |     |          |
              TaskDecorator   void       Future   SPACE     FULL
              copies:          |           |       |          |
              - User           v           v       v          v
              - Security     Handler   Completable  QUEUE    REJECT /
              - Trace ID     logs it     Future              BACK-PRESSURE
              - Transaction               |
                                          v
                                   Caller knows
                                   SUCCESS / ERROR


                  WHEN THREAD POOL IS FULL
                  ========================

                       +------------------+
                       |  NEW TASK ARRIVES |
                       +--------+---------+
                                |
                         +------+------+
                         |             |
                         v             v
                    AbortPolicy   CallerRunsPolicy
                         |             |
                         v             v
                    REJECT TASK    Caller executes
                    Fail Fast       the task itself
                                       |
                                       v
                                  Slows caller
                                  = BACK-PRESSURE


                    GOLDEN RULE FOR @Async
                    ======================

        +------------------------------------------------+
        |  @Async is NOT just "run in background"        |
        |                                                |
        |  ✓ Copy important context                      |
        |  ✓ Handle exceptions properly                  |
        |  ✓ Use bounded thread pool + queue             |
        |  ✓ Define rejection/back-pressure policy       |
        |  ✓ Monitor thread pool metrics                 |
        +------------------------------------------------+

     MEMORY TRICK:
     --------------------------------------------------
     @Async → PROXY → THREAD POOL → 4 TRAPS
                                  |
                 CONTEXT • EXCEPTION • CAPACITY • REJECTION
 * 
*/


/**
┌─────────────────────────────────────────────────────────────────────┐
│                         main() STARTS                               │
└─────────────────────────────────────────────────────────────────────┘
                                |
                                v
                    Set Thread Name = "main"
                    Set CURRENT_USER = "ankur"
                                |
                                v
                  Create NotifierImpl service
                                |
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        v                       v                        v


╔══════════════════════════════════════════════════════════════════════╗
║ A) @ASYNC – CALLER DOES NOT WAIT                                     ║
╚══════════════════════════════════════════════════════════════════════╝

        main thread
            |
            v
   Create Pool: 2 Threads + Queue(10)
            |
            v
   Create @Async Proxy
            |
            v
   main → sendSms()
            |
            v
       ┌───────────────┐
       │ ASYNC PROXY   │
       └───────┬───────┘
               |
               | Submit task
               v
        THREAD POOL                     MAIN THREAD
       ┌────────────┐                 ┌───────────────┐
       │  task-1    │                 │ Returns NOW!  │
       │ Send SMS   │                 │ Other work... │
       └────────────┘                 └───────────────┘
               |
               v
          Pool Shutdown


╔══════════════════════════════════════════════════════════════════════╗
║ B) CONTEXT LOSS – ThreadLocal DOES NOT MOVE AUTOMATICALLY           ║
╚══════════════════════════════════════════════════════════════════════╝

   MAIN THREAD                         WORKER THREAD
   ------------                        -------------
   CURRENT_USER="ankur"
          |
          | Submit @Async Task
          v
   ┌──────────────────────────────────────────────────┐
   │ WITHOUT TaskDecorator                            │
   └──────────────────────────────────────────────────┘
                          |
                          v
                CURRENT_USER = null ❌


   ┌──────────────────────────────────────────────────┐
   │ WITH TaskDecorator                               │
   └──────────────────────────────────────────────────┘
                          |
              Copy "ankur" before task starts
                          |
                          v
                CURRENT_USER = "ankur" ✅

   Same problem can happen with:
   SecurityContext + MDC Trace ID + Transaction Context


╔══════════════════════════════════════════════════════════════════════╗
║ C) LOST EXCEPTIONS – How does caller know about failure?            ║
╚══════════════════════════════════════════════════════════════════════╝

   1. VOID @Async METHOD
   --------------------

   main → failingJob()
              |
              v
        Worker Thread
              |
              v
        Exception happens 💥
              |
              v
       Exception Handler logs it
              |
              v
   MAIN DOES NOT GET EXCEPTION ❌
   "Caller thinks everything is fine"


   2. CompletableFuture METHOD
   --------------------------

   main → sendEmail("bad@@address")
              |
              v
        Worker Thread
              |
              v
        Exception happens 💥
              |
              v
   CompletableFuture gets ERROR
              |
              v
      whenComplete() callback
              |
              v
       CALLER KNOWS FAILURE ✅


╔══════════════════════════════════════════════════════════════════════╗
║ D) POOL EXHAUSTION – 7 tasks arrive together                        ║
╚══════════════════════════════════════════════════════════════════════╝

             THREAD POOL CONFIGURATION
             -------------------------
             Core Threads = 2
             Max Threads  = 3
             Queue Size   = 2

                      7 TASKS ARRIVE
                            |
             ┌──────────────┴──────────────┐
             v                             v

        AbortPolicy                   CallerRunsPolicy
        -----------                   ----------------

     Pool + Queue FULL              Pool + Queue FULL
            |                             |
            v                             v
       REJECT TASK ❌               MAIN THREAD RUNS TASK
       Fail Fast                   |
                                  v
                           Caller becomes slower
                                  |
                                  v
                            BACK-PRESSURE ✅


   HOW TASKS FILL THE POOL
   ======================

   Task 1 ──> Core Thread 1 ──> Running
   Task 2 ──> Core Thread 2 ──> Running
   Task 3 ──> Queue ──────────> Waiting
   Task 4 ──> Queue ──────────> Waiting
   Task 5 ──> Queue FULL → Create Thread 3
   Task 6 ──> Everything FULL → Reject / Caller Runs
   Task 7 ──> Everything FULL → Reject / Caller Runs


┌─────────────────────────────────────────────────────────────────────┐
│                           FINAL LESSON                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  @Async → Proxy → Thread Pool → Background Work                     │
│                                                                     │
│  But always handle:                                                 │
│                                                                     │
│  1. CONTEXT    → Copy ThreadLocal/Security context                  │
│  2. EXCEPTIONS → Use CompletableFuture or Exception Handler         │
│  3. CAPACITY   → Use bounded threads and queue                      │
│  4. REJECTION  → Fail fast OR apply back-pressure                   │
│                                                                     │
│  MEMORY: CONTEXT → ERROR → POOL → BACK-PRESSURE                     │
└─────────────────────────────────────────────────────────────────────┘
 * 
*/