# JVM, Memory Management & GC: Interview Questions

## Basics

**1. What is the difference between JDK, JRE and JVM?**
- **JVM** runs your compiled bytecode.
- **JRE** is the JVM plus the standard libraries needed to run a Java program.
- **JDK** is the JRE plus developer tools such as `javac`, `jar`, `jstack` and `jmap`.

**2. How does Java achieve "write once, run anywhere"?**
`javac` compiles source code into bytecode (`.class` files), not machine code. Each OS has its own JVM that turns this bytecode into native instructions, so the same bytecode runs on any platform that has a JVM.

**3. What are the main parts of the JVM architecture?**
- **Class Loader** loads `.class` files.
- **Runtime Data Areas** are the memory: heap, stack, metaspace, PC register and native stack.
- **Execution Engine** has the interpreter, the JIT compiler and the garbage collector.

**4. How does class loading work?**
It has three steps: **Loading** (read the class), **Linking** (verify, prepare, resolve) and **Initialization** (run static blocks and set static values). Loaders follow the **parent delegation model**: a loader first asks its parent to load the class, and only loads it itself if the parent can't. The order is Bootstrap, then Platform, then Application. This stops anyone from replacing core classes like `java.lang.String`.

## Memory Management

**5. What is the difference between heap and stack memory?**

| | Stack | Heap |
|---|---|---|
| Stores | Local variables, method calls, references | Objects and arrays |
| Per thread? | Yes, one per thread | No, shared by all threads |
| Cleanup | Automatic when the method returns | Garbage collector |
| Error | `StackOverflowError` | `OutOfMemoryError` |

**6. How is the heap organised?**
It is split by object age:
- **Young Generation**: **Eden** plus two **Survivor** spaces (S0 and S1). New objects start in Eden.
- **Old Generation**: long-lived objects are promoted here.

This design works because of the **generational hypothesis**: most objects die young, so collecting only the small young area is fast and cheap.

**7. What is Metaspace? How is it different from PermGen?**
Both store class metadata (class structure, methods, constant pool). **PermGen** was part of the heap with a fixed size, and caused `OutOfMemoryError: PermGen space`. From Java 8, **Metaspace** replaced it. It lives in native memory and grows automatically, though you can cap it with `-XX:MaxMetaspaceSize`.

**8. What is the String Pool?**
It is a special area in the heap where the JVM keeps unique string literals, to save memory. `"abc" == "abc"` is `true` because both point to the same pooled object. `new String("abc")` creates a new object outside the pool. `intern()` moves a string into the pool.

## Garbage Collection

**9. What is garbage collection and how does the JVM decide what is garbage?**
GC automatically frees memory of objects nobody can reach any more. The JVM starts from **GC Roots**: local variables on thread stacks, static fields and active threads. It follows every reference from those roots, and anything it cannot reach is garbage. Java does **not** use reference counting, so circular references are not a problem.

**10. What is the difference between Minor GC, Major GC and Full GC?**
- **Minor GC** cleans the Young generation. It is frequent and fast.
- **Major GC** cleans the Old generation. It is slower.
- **Full GC** cleans the whole heap plus Metaspace. It is the most expensive and often causes long pauses.

**11. What does "Stop-the-World" mean?**
During some GC phases, the JVM pauses all application threads so the object graph doesn't change while GC inspects it. This causes latency spikes, and modern collectors work hard to reduce these pauses.

**12. How does Minor GC actually work?**
Live objects in Eden and the active Survivor space are **copied** into the other Survivor space, and the old spaces are wiped clean. Each time an object survives, its **age** increases. After a threshold (`-XX:MaxTenuringThreshold`), it is promoted to the Old generation.

**13. What are the main GC algorithms?**
- **Mark-Sweep**: mark live objects, then delete the dead ones. It leaves memory fragmented.
- **Mark-Sweep-Compact**: the same, but live objects are then moved together to remove gaps.
- **Copying**: copy live objects to a fresh area. It is fast and has no fragmentation, but needs extra space. Young GC uses it.

**14. Which garbage collectors are available and when would you use each?**

| Collector | Best for |
|---|---|
| **Serial** | Small apps, single CPU |
| **Parallel** | Throughput-focused batch jobs |
| **G1** (default since Java 9) | General-purpose servers, balanced pauses |
| **ZGC** | Very large heaps, ultra-low pauses (under about 10 ms) |
| **Shenandoah** | Low-pause, similar goal to ZGC |

CMS was removed in Java 14.

**15. How does G1 GC work?**
G1 divides the heap into many equal-sized **regions** instead of fixed Young/Old blocks. Any region can play the role of Eden, Survivor or Old. G1 tracks how much garbage each region holds and collects the "most garbage first", staying within a pause-time goal set with `-XX:MaxGCPauseMillis`. That is how it keeps pauses predictable.

## Scenario and Senior-Level Questions

**16. Can Java have memory leaks even with a garbage collector?**
Yes. A leak happens when objects are still *reachable* but no longer *needed*. Common causes:
- Static collections that keep growing (caches without eviction)
- Listeners or callbacks that are never unregistered
- Unclosed resources (connections, streams)
- `ThreadLocal` values not removed in thread pools
- Inner classes holding hidden references to outer objects

**17. What are the types of OutOfMemoryError?**
- `Java heap space`: the heap is full, usually a leak or an undersized heap.
- `Metaspace`: too many classes loaded, often from classloader leaks or heavy dynamic proxying.
- `GC overhead limit exceeded`: the JVM spends almost all its time in GC and reclaims almost nothing.
- `unable to create native thread`: the OS thread limit has been hit.

**18. What are Strong, Soft, Weak and Phantom references?**
- **Strong**: the normal reference. The object is never collected while it exists.
- **Soft**: collected only when memory is low. Good for caches.
- **Weak**: collected at the next GC. Used by `WeakHashMap`.
- **Phantom**: used to run clean-up actions after an object is collected.

**19. Your production service is slow, and GC logs show frequent Full GCs. How do you investigate?**
1. Enable GC logs (`-Xlog:gc*`) and check how often GC runs and how long the pauses are.
2. Check whether the heap keeps filling up after each GC. If it does, suspect a leak.
3. Take a **heap dump** (`jmap -dump` or `-XX:+HeapDumpOnOutOfMemoryError`) and open it in Eclipse MAT or VisualVM to find the biggest objects and their reference chains.
4. Use `jstack` for thread dumps and `jstat -gcutil` for live GC stats.
5. Fix the leak or tune the heap size and GC choice, then re-test under load.

**20. Which JVM flags do you commonly use for memory tuning?**
- `-Xms` / `-Xmx`: initial and max heap size. Setting them equal avoids resize pauses.
- `-XX:+UseG1GC` / `-XX:+UseZGC`: choose the collector.
- `-XX:MaxGCPauseMillis=200`: pause-time goal for G1.
- `-XX:MaxMetaspaceSize`: cap Metaspace.
- `-XX:+HeapDumpOnOutOfMemoryError`: automatic dump when memory runs out.
- `-Xss`: thread stack size.

**21. What is the JIT compiler?**
At first the JVM **interprets** bytecode, which is slow. It watches for "hot" methods that run often, and the **JIT (Just-In-Time) compiler** compiles them into optimised native code. This is why Java apps are slower at startup and get faster after **warm-up**. Optimisations include inlining and **escape analysis**, which lets objects that never leave a method live on the stack instead of the heap.

**22. How would you choose between G1 and ZGC for a payments platform?**
- If the heap is moderate (a few GB to tens of GB) and pauses of 100-200 ms are acceptable, **G1** is a safe default.
- If the service is latency-sensitive (API timeouts, trading) or has a very large heap, **ZGC** keeps pauses very low, at the cost of some extra CPU and memory.

Test with production-like load and compare p99 latency before deciding.
