# Concurrency & Multithreading: Interview Questions

## Basics

**1. What is the difference between a process and a thread?**
- A **process** is a running program with its own separate memory.
- A **thread** is a smaller unit of work inside a process. All threads of a process **share the same heap memory**, but each has its own stack.

Threads are lighter and cheaper to create than processes. Sharing memory makes communication easy, but it also causes the classic concurrency bugs.

**2. What are the ways to create a thread in Java?**
- Extend `Thread` and override `run()`.
- Implement `Runnable` (preferred, because Java allows only one parent class).
- Implement `Callable`, which can return a value and throw checked exceptions.
- Use an `ExecutorService` (best in real projects) or, from Java 21, virtual threads.

**3. What happens if you call `run()` instead of `start()`?**
`start()` creates a **new thread** and runs `run()` inside it. Calling `run()` directly just executes it like a normal method call on the **current thread**, so there is no multithreading at all.

**4. What is the difference between `Runnable` and `Callable`?**

| | Runnable | Callable |
|---|---|---|
| Method | `void run()` | `V call()` |
| Returns value | No | Yes, via `Future` |
| Checked exceptions | Cannot throw | Can throw |

**5. What are the states of a thread?**
`NEW` → `RUNNABLE` → `BLOCKED` (waiting for a lock) / `WAITING` (waiting for another thread, no timeout) / `TIMED_WAITING` (e.g. `sleep(1000)`) → `TERMINATED`.

## Core Problems

**6. What is a race condition?**
When two or more threads read and change shared data at the same time, and the result depends on who runs first. For example, `count++` looks like one step but is really three: read, add, write. Two threads can both read 5 and both write 6, so one increment is lost.

**7. What does `synchronized` do?**
It allows only **one thread at a time** to run a block or method, using a lock (monitor) on an object. It gives two guarantees:
- **Mutual exclusion**: no two threads run the block together.
- **Visibility**: changes made inside the block are visible to the next thread that takes the same lock.

**8. What does `volatile` do? Does it make `count++` safe?**
`volatile` guarantees that every thread sees the **latest value** of a variable, and prevents certain instruction reordering. It does **not** make compound operations atomic, so `count++` is still unsafe with `volatile`. Use `AtomicInteger` or `synchronized` for that. `volatile` is good for simple flags such as `boolean running`.

**9. What is the Java Memory Model (JMM) and "happens-before"?**
Each CPU core may keep its own cached copy of variables, so one thread's write is not automatically seen by another. The JMM defines when a write is **guaranteed to be visible** to a later read. That guarantee is called **happens-before**. Examples:
- Unlocking a lock happens-before the next lock of the same lock.
- A write to a `volatile` variable happens-before every later read of it.
- `thread.start()` happens-before everything the new thread does.

**10. What is the difference between `synchronized` and `ReentrantLock`?**

| | synchronized | ReentrantLock |
|---|---|---|
| Release | Automatic | Manual (`unlock()` in `finally`) |
| Try without waiting | No | `tryLock()` and `tryLock(timeout)` |
| Interruptible while waiting | No | `lockInterruptibly()` |
| Fairness option | No | Yes |
| Multiple conditions | One wait set | Many `Condition` objects |

Use `synchronized` for simple cases. Use `ReentrantLock` when you need timeouts, fairness or interruption.

**11. What is the difference between `wait()` and `sleep()`?**
- `sleep()` pauses the thread for some time and **keeps holding its locks**. It belongs to `Thread`.
- `wait()` **releases the lock** and waits until another thread calls `notify()` or `notifyAll()`. It belongs to `Object` and must be called inside a `synchronized` block.

**12. Why should `wait()` always be inside a `while` loop?**
Because of **spurious wakeups** (a thread can wake without being notified) and because the condition may have changed again before the thread gets the lock back. So always re-check:
```java
synchronized (lock) {
    while (!conditionMet) {
        lock.wait();
    }
}
```

## Deadlock and Friends

**13. What is a deadlock? What are the conditions for it?**
Two or more threads wait for each other's locks forever. For example, Thread A holds Lock 1 and wants Lock 2, while Thread B holds Lock 2 and wants Lock 1. All four of these must be true:
1. **Mutual exclusion**: the resource can be held by only one thread.
2. **Hold and wait**: a thread holds one lock while asking for another.
3. **No preemption**: a lock cannot be forcibly taken away.
4. **Circular wait**: a cycle of threads each waiting on the next.

**14. How do you prevent or fix deadlocks?**
- Always take locks in the **same global order**.
- Use `tryLock()` with a timeout and back off if it fails.
- Hold locks for the **shortest time** and avoid calling unknown code while holding one.
- Prefer higher-level tools (`ConcurrentHashMap`, atomics, queues) over manual locks.
- To **find** one in production, take a thread dump with `jstack`. It reports "Found one Java-level deadlock".

**15. What is the difference between deadlock, livelock and starvation?**
- **Deadlock**: threads are stuck waiting and do nothing.
- **Livelock**: threads keep running and reacting to each other, but make no progress (like two people in a corridor who keep stepping aside in the same direction).
- **Starvation**: a thread never gets the CPU or the lock because others keep getting it first.

## Thread Pools and Executors

**16. Why use a thread pool instead of creating threads yourself?**
Creating a thread is expensive, and unlimited threads can crash the system. A pool **reuses a fixed set of threads**, controls how many run at once, and queues extra work. It also gives you better shutdown and error handling.

**17. What are the main parameters of `ThreadPoolExecutor`?**
- `corePoolSize`: threads always kept alive.
- `maximumPoolSize`: the upper limit of threads.
- `keepAliveTime`: how long extra (non-core) threads stay idle before dying.
- `workQueue`: where waiting tasks are held.
- `ThreadFactory` and `RejectedExecutionHandler`: how threads are named and what happens when the pool is full.

**Order of events:** use core threads first, then fill the queue, and only when the queue is full create threads up to the maximum. If that is also full, the task is rejected. Many people wrongly think the pool grows before the queue fills.

**18. Why do many guidelines say to avoid `Executors.newFixedThreadPool()` and `newCachedThreadPool()`?**
- `newFixedThreadPool` uses an **unbounded queue**, so tasks can pile up and cause `OutOfMemoryError`.
- `newCachedThreadPool` has **no limit on threads**, so a burst of tasks can create thousands of threads.

In production, create `ThreadPoolExecutor` directly with a **bounded queue** and a clear rejection policy.

**19. How do you decide the size of a thread pool?**
- **CPU-heavy tasks**: about the number of CPU cores (cores + 1).
- **I/O-heavy tasks** (DB, network calls): more threads, roughly `cores × (1 + wait time / compute time)`.

Treat this as a starting point, then load-test and adjust. Use **separate pools** for different kinds of work so a slow downstream service doesn't block everything.

**20. What is `Future`, and how is `CompletableFuture` better?**
A `Future` lets you get a result later, but `get()` **blocks**, and you can't easily chain steps. `CompletableFuture` lets you chain and combine async steps without blocking:
```java
CompletableFuture.supplyAsync(() -> fetchUser(id))
    .thenApply(user -> user.getName())
    .thenCombine(fetchOrders(id), (name, orders) -> build(name, orders))
    .exceptionally(ex -> fallback());
```
You can run tasks in parallel (`allOf`, `anyOf`) and handle errors in the chain.

## Concurrent Collections and Utilities

**21. How does `ConcurrentHashMap` work, and how is it different from `Hashtable` or `synchronizedMap`?**
`Hashtable` and `synchronizedMap` lock the **whole map** for every operation, so threads queue up. `ConcurrentHashMap` (Java 8+) locks only at the **bucket level** and uses **CAS** (compare-and-swap) for many updates, so many threads can read and write at once. Reads are mostly lock-free. It does not allow `null` keys or values.

**22. What are atomic classes and CAS?**
`AtomicInteger`, `AtomicLong` and similar classes update values safely **without locks**. They use the CPU's **Compare-And-Swap**: "set the value to X only if it is still Y; otherwise retry". It is fast under low or medium contention. Under very heavy contention, `LongAdder` performs better.

**23. What is `ThreadLocal`, and what is its danger?**
It gives **each thread its own copy** of a variable, useful for things like a user context or request ID. The danger is in **thread pools**: threads are reused, so if you don't call `remove()`, old data leaks into the next request and can cause memory leaks.

**24. What are `CountDownLatch`, `CyclicBarrier` and `Semaphore`?**
- **CountDownLatch**: one or more threads wait until a count reaches zero (e.g. wait for 5 services to start). **Single use.**
- **CyclicBarrier**: a group of threads wait for **each other** at a point, then all continue. **Reusable.**
- **Semaphore**: allows up to N threads at a time. Useful for limiting access, such as maximum 10 concurrent calls to a partner API.

**25. How would you implement a producer-consumer pattern?**
Use a `BlockingQueue` (such as `ArrayBlockingQueue`). Producers call `put()`, which waits if the queue is full. Consumers call `take()`, which waits if it is empty. The queue handles all locking and waiting, so you don't write `wait/notify` yourself. A bounded queue also gives **back-pressure**, so a fast producer can't overwhelm a slow consumer.

## Modern Java and Scenario Questions

**26. What are virtual threads (Java 21), and when should you use them?**
Virtual threads are very lightweight threads managed by the JVM, not the OS. You can run **hundreds of thousands** of them. When one blocks on I/O, the JVM parks it and uses the underlying OS thread for another. They are ideal for **I/O-heavy servers** with the simple "one thread per request" style. They don't help CPU-bound work, and you should avoid holding `synchronized` locks around blocking calls (this can pin the carrier thread).

**27. Two users click "Pay" at the same time for the same order. How do you prevent a double payment?**
- Use an **idempotency key** per payment request, with a **unique constraint** in the database, so a second attempt fails or returns the first result.
- Use **optimistic locking** (a version column) or a DB row lock (`SELECT ... FOR UPDATE`) on the order.
- A JVM `synchronized` block alone is **not enough** because the service runs on multiple instances. You need a DB-level or distributed lock.

**28. A service freezes and CPU is low. How do you investigate?**
Low CPU with a frozen service usually means threads are **blocked**, not busy.
1. Take 2-3 thread dumps a few seconds apart (`jstack <pid>`).
2. Look for threads in `BLOCKED` or `WAITING` on the same lock or resource.
3. Check for a deadlock report at the bottom of the dump.
4. Check whether the thread pool is exhausted, for example all threads waiting on a slow DB or HTTP call with no timeout.
5. Fix by adding timeouts, fixing the lock order, or separating pools.

**29. Is `i++` thread-safe on a `volatile int`? How about `HashMap` in multiple threads?**
- `volatile int i; i++` is **not safe** (read-modify-write is not atomic).
- `HashMap` is **not thread-safe**. Concurrent writes can lose data or corrupt the structure. Use `ConcurrentHashMap`.

**30. What is the difference between concurrency and parallelism?**
- **Concurrency**: handling many tasks in overlapping time periods (switching between them). It is about *structure*.
- **Parallelism**: actually running tasks at the *same instant* on multiple cores. It is about *execution*.

A single-core machine can be concurrent but not parallel.
