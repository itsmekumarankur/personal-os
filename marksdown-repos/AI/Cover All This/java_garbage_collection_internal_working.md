# Java Garbage Collection (GC) -- Internal Working Explained

A practical guide to how Java allocates objects, identifies garbage,
moves surviving objects, and reclaims memory. It uses simple examples
and ASCII diagrams.

## 1. Why do we need Garbage Collection?

Java objects are generally allocated on the heap. When an object is no
longer reachable from the application, it becomes eligible for garbage
collection. The JVM reclaims its memory automatically.

``` java
public class Main {
    public static void main(String[] args) {
        Employee e1 = new Employee("Ankur");
        Employee e2 = new Employee("Rahul");

        e1 = null;
    }
}
```

Before `e1 = null`:

``` text
STACK / ROOTS                 HEAP
+------+                      +----------------+
| e1 --|--------------------->| Employee Ankur |
+------+                      +----------------+
| e2 --|--------------------->| Employee Rahul |
+------+                      +----------------+
```

After `e1 = null`:

``` text
STACK / ROOTS                 HEAP
+------+                      +----------------+
| null |                      | Employee Ankur |  <- unreachable
+------+                      +----------------+
| e2 --|--------------------->| Employee Rahul |
+------+                      +----------------+
```

The Ankur object is eligible for GC, but it is not necessarily collected
immediately.

**Key point:** GC determines reachability, not whether an object is
logically useful to the business.

## 2. Java memory areas

A simplified JVM memory picture:

``` text
              JVM MEMORY
    +--------------------------------+
    |              HEAP              |
    |       Objects and arrays       |
    |       Main GC-managed area     |
    +--------------------------------+
    |              STACK             |
    |   Method frames and local refs |
    +--------------------------------+
    |            METASPACE           |
    |          Class metadata        |
    +--------------------------------+
```

-   **Heap:** stores most Java objects and arrays; managed by the
    garbage collector.
-   **Stack:** stores per-thread method frames, local variables and
    references. Stack references can be GC roots.
-   **Metaspace:** stores class metadata and is managed outside the
    ordinary Java heap.

Example:

``` java
public static void main(String[] args) {
    Employee e1 = new Employee("Ankur");
}
```

``` text
       STACK                         HEAP
+----------------+             +-------------------+
| e1 ------------|------------>| Employee Object   |
+----------------+             | name = "Ankur"    |
                               +-------------------+
```

This is a conceptual model. JIT optimizations can change where values
are physically represented.

## 3. Heap generations

The generational hypothesis says that most objects die young, while a
smaller number survive for a long time.

For example: - Request objects and temporary responses may live only for
one API call. - Configuration, application-wide caches and long-lived
session data may survive much longer.

Traditional generational heap layout:

``` text
                 JAVA HEAP
    +--------------------------------------+
    |             YOUNG GENERATION         |
    |                                      |
    |   +---------+  +------+  +------+    |
    |   |  EDEN   |  |  S0  |  |  S1  |    |
    |   +---------+  +------+  +------+    |
    +--------------------------------------+
    |             OLD GENERATION           |
    |   Long-lived objects                 |
    +--------------------------------------+
```

-   **Eden:** where most new objects are allocated.
-   **Survivor S0 and S1:** hold objects that survive young collections.
-   **Old Generation:** holds objects promoted from the young generation
    and, depending on collector and allocation conditions, some objects
    allocated directly there.

This is the traditional generational picture. Collectors such as G1 use
heap regions rather than one contiguous Eden/Survivor/Old layout. Not
all modern collectors use exactly this physical structure.

## 4. Where does a new object get created?

Consider:

``` java
Employee e1 = new Employee("Ankur");
Employee e2 = new Employee("Rahul");
Employee e3 = new Employee("Amit");
```

Objects are generally allocated in Eden:

``` text
             EDEN
    +--------------------------------+
    | [Employee: Ankur]              |
    | [Employee: Rahul]              |
    | [Employee: Amit]               |
    |                                |
    +--------------------------------+
```

### Pointer bumping

A common fast allocation technique is pointer bumping. The JVM maintains
a pointer to the next free location in a contiguous allocation area.

``` text
EDEN MEMORY
+----------+----------+----------+----------+
| Object 1 | Object 2 | Object 3 |   FREE   |
+----------+----------+----------+----------+
                                 ^
                                 |
                         Allocation pointer
```

When an object is allocated, the JVM reserves space and advances the
pointer. This avoids searching for a free block for every allocation.

### TLAB -- Thread-Local Allocation Buffer

Multiple threads allocating through one shared pointer could contend
with each other. HotSpot therefore commonly gives each thread a small
allocation buffer inside Eden.

``` text
                    EDEN
    +--------------------------------------+
    | Thread 1 TLAB                        |
    | +----------------------+             |
    | | Object A | Object B  |             |
    | +----------------------+             |
    |                                      |
    | Thread 2 TLAB                        |
    | +----------------------+             |
    | | Object C | Object D  |             |
    | +----------------------+             |
    +--------------------------------------+
```

**Memory trick:** TLAB = each thread gets its own small allocation area.

## 5. What happens when Eden becomes full?

When an allocation cannot be satisfied in Eden, the JVM may trigger a
young-generation collection. This is commonly called a **Minor GC** in
traditional terminology.

Suppose Eden contains five objects:

``` text
EDEN
+-------------------+
| Employee A        |
| Employee B        |
| Employee C        |
| Employee D        |
| Employee E        |
+-------------------+
```

Some references are removed:

``` java
e1 = null;
e3 = null;
e5 = null;
```

Assume B and D remain reachable. The collector identifies live objects
and reclaims the others.

## 6. How Minor GC works internally

### 6.1 Marking: find reachable objects

The JVM begins from **GC Roots** and follows references.

Common GC roots include: - References in active Java thread stacks. -
References held by static fields of loaded classes. - JNI handles. -
Certain JVM internal references.

``` text
             GC ROOTS
          (active stack frames)

             e2       e4
              |        |
              v        v
         +---------+ +---------+
         | Rahul   | | Ravi    |
         | Employee| | Employee|
         +---------+ +---------+
```

Objects reachable from GC roots are live. Objects that cannot be reached
are eligible for collection.

GC does not merely count references. This correctly handles circular
references:

``` text
Employee A ------> Employee B
     ^                  |
     |                  |
     +------------------+
```

If no GC root can reach either object, both are collectible despite
referring to each other.

### 6.2 Copying: move live objects

Before collection:

``` text
       EDEN
    +-------------------+
    | A  DEAD           |
    | B  LIVE           |
    | C  DEAD           |
    | D  LIVE           |
    | E  DEAD           |
    +-------------------+

       S0: EMPTY
       S1: EMPTY
```

After copying the survivors:

``` text
       EDEN
    +-------------------+
    |      EMPTY        |
    +-------------------+

       S0
    +-------------------+
    | Employee B        |
    | Employee D        |
    +-------------------+

       S1
    +-------------------+
    |      EMPTY        |
    +-------------------+
```

The collector: 1. Identifies live objects. 2. Copies survivors to a
Survivor space. 3. Reclaims the Eden allocation area. 4. Discards the
dead objects by not copying them.

Copying works well for young objects because typically only a small
percentage survive.

### 6.3 Survivor spaces alternate

On a later young collection, the collector examines Eden and the
currently occupied Survivor space. It copies survivors into the other
Survivor space.

``` text
       BEFORE NEXT GC
    EDEN:  F, G, H
    S0:    B, D
    S1:    EMPTY

       AFTER NEXT GC
    EDEN:  EMPTY
    S0:    EMPTY
    S1:    B, D, F, H
```

S0 and S1 take turns: - One is the source (From Space). - The other is
the destination (To Space). - Their roles swap after collection.

## 7. Object aging and promotion

Objects that survive young collections have an age. Their age increases
as they survive successive young collections.

``` text
Minor GC #1  -> Employee B age 1
Minor GC #2  -> Employee B age 2
Minor GC #3  -> Employee B age 3
Minor GC #4  -> Employee B age 4
                  |
                  v
          Promotion may occur
                  |
                  v
             OLD GENERATION
```

When an object's age reaches the applicable tenuring threshold, it may
be promoted to Old Generation. The threshold is not necessarily fixed at
15; it can be adjusted by the JVM and collector.

Promotion can also happen earlier: - Survivor space may not have enough
room. - Large objects may be allocated directly into old regions,
depending on the collector and allocation conditions.

``` text
          YOUNG GENERATION
    +----------------------------+
    | Eden: new objects           |
    | Survivor: surviving objects|
    +----------------------------+
                  |
          Age / promotion rules
                  |
                  v
           OLD GENERATION
    +----------------------------+
    | Long-lived objects          |
    +----------------------------+
```

**Why promote?** Objects that survive repeatedly are more likely to be
long-lived. Moving them out of the young area avoids copying them during
every young collection.

## 8. What happens when Old Generation fills up?

Old-generation collection depends on the collector.

A general mark-and-compact explanation:

### Mark

``` text
OLD GENERATION
+--------------------------------+
| A -----> B                     |
| C -----> D                     |
| E -----> F                     |
+--------------------------------+

Assume A, B, D and F are live.
Assume C and E are unreachable.
```

### Identify garbage

``` text
+--------------------------------+
| A | B | X | D | X | F          |
+--------------------------------+
          X = garbage
```

### Compact

A compacting collector can move live objects together:

``` text
BEFORE
+--------------------------------+
| A | B | X | D | X | F          |
+--------------------------------+

AFTER
+--------------------------------+
| A | B | D | F | FREE | FREE    |
+--------------------------------+
```

Compaction reduces fragmentation by bringing live objects together. Not
every collector compacts the entire heap this way: - Parallel GC uses
mark-and-compact for old-generation collection. - G1 evacuates selected
regions. - ZGC relocates objects concurrently.

## 9. Stop-The-World (STW)

A Stop-The-World pause occurs when application threads must pause for a
GC phase.

``` text
APPLICATION THREADS
Thread 1  RUNNING
Thread 2  RUNNING
Thread 3  RUNNING
Thread 4  RUNNING
       |
       v
STOP THE WORLD
Thread 1  PAUSED
Thread 2  PAUSED
Thread 3  PAUSED
Thread 4  PAUSED
       |
       v
GC PHASE
Mark / Evacuate / Compact
       |
       v
APPLICATION RESUMES
Thread 1  RUNNING
Thread 2  RUNNING
Thread 3  RUNNING
Thread 4  RUNNING
```

Not all GC work is stop-the-world. Some collectors perform significant
work concurrently while application threads continue executing.

Why it matters: if an API has a 200 ms latency target and experiences a
300 ms GC pause, the request may breach its latency target.

Production teams monitor: - GC pause duration. - GC frequency. - Heap
utilization. - Allocation rate. - Promotion rate. - Application latency,
especially p95 and p99.

## 10. Different Garbage Collectors

Different collectors optimize for different goals.

### 10.1 Serial GC

-   Uses one GC worker.
-   Collection pauses application threads.
-   Simple and suitable for small heaps or simple applications.
-   May be slow for large heaps because collection work is
    single-threaded.

``` text
APPLICATION THREADS
       |
       v
STOP THE WORLD
       |
       v
GC THREAD 1
[Mark] [Copy] [Compact]
```

### 10.2 Parallel GC

-   Uses multiple GC worker threads.
-   Focuses on throughput.
-   Collection phases pause application threads.
-   Often suitable for batch workloads.

``` text
APPLICATION
     |
     v
STOP THE WORLD
     |
     v
+------------------+
| GC Thread 1      |
| GC Thread 2      |
| GC Thread 3      |
| GC Thread 4      |
+------------------+
     |
     v
APPLICATION RESUMES
```

Throughput is the proportion of total time spent doing application work
rather than GC work.

Example:

``` text
Total execution time = 100 seconds
Application work     = 95 seconds
GC work              =  5 seconds
Application throughput = 95%
```

### 10.3 G1 GC -- Garbage First

G1 is important for modern Java server applications. It is the default
collector in many modern HotSpot server configurations.

Unlike the traditional contiguous generational layout, G1 divides the
heap into many equally sized regions. Regions can have roles such as
Eden, Survivor, Old, Humongous or Free.

``` text
                    G1 HEAP
    +------+------+------+------+------+
    | Eden | Eden | S0   | Old  | Old  |
    +------+------+------+------+------+
    | Old  | Eden | Hum. | Old  | S1   |
    +------+------+------+------+------+
    | Eden | Old  | Old  | Hum. | Free |
    +------+------+------+------+------+
    | S0   | Old  | Eden | Free | Old  |
    +------+------+------+------+------+
```

G1 aims to prioritize regions that offer a high amount of reclaimable
memory for the collection effort.

Example:

``` text
Region A: 90% live, 10% garbage
Region B: 20% live, 80% garbage
Region C: 30% live, 70% garbage
Region D: 95% live,  5% garbage

G1 may prioritize B and C.
```

Simplified G1 lifecycle:

``` text
APPLICATION RUNNING
        |
        v
YOUNG COLLECTION
        |
        v
CONCURRENT MARKING
        |
        v
REMARK (short pause)
        |
        v
CLEANUP / REGION ACCOUNTING
        |
        v
MIXED COLLECTION
        |
        v
RECLAIM SELECTED OLD REGIONS
```

Important concepts: - **Concurrent marking:** identifies live objects
while the application runs. - **Remark:** completes marking with a
pause. - **Cleanup:** prepares and accounts for reclaimable regions. -
**Mixed GC:** collects young regions and selected old regions. -
**Remembered sets and write barriers:** track references between regions
so G1 can collect a region without scanning the entire heap for every
collection.

Memory trick: G1 = divide heap into regions, identify regions with lots
of garbage, reclaim efficiently.

### 10.4 ZGC

ZGC is designed for very low pause times, including for large heaps and
latency-sensitive applications.

It performs most expensive work concurrently with application execution.

``` text
APPLICATION THREADS
--------------------------------
Running   Running   Running
Running   Running   Running
--------------------------------

ZGC THREADS
--------------------------------
Concurrent marking
Concurrent relocation
Concurrent processing
--------------------------------
```

ZGC uses techniques including: - Colored pointers. - Load barriers. -
Concurrent marking. - Concurrent relocation. - Relocation sets.

A load barrier helps resolve references correctly when objects are
accessed, including during concurrent relocation.

ZGC still has short Stop-The-World phases, but its design aims to keep
pauses very low.

## 11. Minor GC vs Major GC vs Full GC

These terms are common in interviews, but usage is not fully consistent
across collectors and JVM tools.

  -----------------------------------------------------------------------
  Term                                Common meaning
  ----------------------------------- -----------------------------------
  Minor GC                            Young-generation collection

  Major GC                            Often used for old-generation
                                      collection

  Full GC                             Heap-wide collection, typically
                                      including young and old generations
  -----------------------------------------------------------------------

``` text
MINOR GC
+----------------------+
| Young Generation     |
| Eden + Survivors     |
+----------------------+

MAJOR GC (common usage)
+----------------------+
| Old Generation       |
+----------------------+

FULL GC
+----------------------+
| Young Generation     |
+----------------------+
| Old Generation       |
+----------------------+
| Heap-wide work       |
+----------------------+
```

Always interpret the actual collector and GC logs. Modern collectors
such as G1 have more specific event names and phases.

## 12. Memory leaks in Java

Java can have memory leaks even with GC.

GC removes unreachable objects, not objects that are no longer logically
needed but remain reachable.

Example:

``` java
public class EmployeeService {
    static List<Employee> employees = new ArrayList<>();

    public void addEmployee() {
        Employee e = new Employee();
        employees.add(e);
    }
}
```

The static list keeps references to every Employee:

``` text
             GC ROOT
                |
                v
        Static employees
                |
       +--------+--------+
       |        |        |
       v        v        v
    Employee Employee Employee
       A        B        C
```

All remain reachable, so GC cannot collect them.

Common causes: 1. Static collections that continuously grow. 2.
Incorrect cache eviction. 3. Listeners that are not unregistered. 4.
ThreadLocal values that are not cleaned up. 5. Long-lived references to
unnecessary objects. 6. Unbounded queues.

### Detecting a possible leak

Observe heap usage after collections:

``` text
Heap usage
  |
90%|                    /-------
   |                 /
70%|             /
   |          /
50%|      /
   |  ___/
30%|
   +--------------------------------> Time
```

Consistently rising post-GC live-set usage can indicate retained objects
or a memory leak. It is a signal to investigate, not proof by itself.

Useful tools: - Eclipse Memory Analyzer (MAT). - Java Flight Recorder
(JFR). - Java Mission Control (JMC). - VisualVM.

## 13. What happens when JVM runs out of memory?

Suppose: - Maximum heap = 4 GB. - Current heap usage = 3.9 GB. - A new
allocation needs 300 MB.

The JVM may attempt collection and retry allocation. If enough memory
cannot be made available, it can throw `OutOfMemoryError`.

``` text
             HEAP
+--------------------------------+
| Used memory       3.9 GB       |
| Free memory       0.1 GB       |
+--------------------------------+

New allocation: 300 MB
        |
        v
   GC attempt
        |
   +----+----+
   |         |
Enough?    Not enough
   |         |
   v         v
Continue  OutOfMemoryError
```

`OutOfMemoryError` does not always mean Java heap is full. Other causes
include: - Metaspace exhaustion. - Direct buffer memory exhaustion. -
Native thread exhaustion. - Native memory exhaustion.

## 14. Monitoring GC in production

Important metrics:

  Metric             What it tells you
  ------------------ -----------------------------------------
  Heap utilization   How much heap is used
  Allocation rate    How quickly objects are created
  GC frequency       How often collection happens
  GC pause time      How long application threads are paused
  Promotion rate     How quickly objects move to Old Gen
  Live-set size      Memory occupied by reachable objects
  Full GC count      Number of full heap collections

### Enable GC logging (Java 9+)

``` bash
java \
  -Xms2g \
  -Xmx4g \
  -Xlog:gc*:file=gc.log:time,uptime,level,tags \
  -jar application.jar
```

  Flag            Meaning
  --------------- ----------------------------
  `-Xms2g`        Initial heap size = 2 GB
  `-Xmx4g`        Maximum heap size = 4 GB
  `-Xlog:gc*`     Enable detailed GC logging
  `file=gc.log`   Write logs to a file

### Monitor GC with jstat

``` bash
jstat -gcutil <pid> 1000
```

This displays GC utilization statistics every 1,000 milliseconds.

### Take a heap dump

``` bash
jcmd <pid> GC.heap_dump heap.hprof
```

Analyze it with Eclipse MAT, VisualVM or other heap-dump tools.

Other useful monitoring tools: - Java Flight Recorder. - Java Mission
Control. - Prometheus and Grafana. - Micrometer JVM metrics.

## 15. Choosing a Garbage Collector

There is no universally best GC.

  Collector   Primary objective                Typical use
  ----------- -------------------------------- --------------------------------
  Serial      Simplicity                       Small applications
  Parallel    High throughput                  Batch workloads
  G1          Balance throughput and latency   General server applications
  ZGC         Very low pause times             Latency-sensitive applications

Practical starting points: - Ordinary Spring Boot microservices: start
with G1 and measure. - Batch processing: evaluate Parallel GC. - Very
large heaps or stringent latency requirements: evaluate ZGC.

Do not choose based only on heap size. Measure allocation rate, live-set
size, pause-time distribution, CPU use and application latency.

## 16. Complete GC lifecycle

``` text
                 JAVA APPLICATION
                        |
                        v
                CREATE NEW OBJECT
                        |
                        v
                 +-------------+
                 |    EDEN     |
                 | New Objects |
                 +-------------+
                        |
                 Eden allocation pressure
                        |
                        v
                  YOUNG GC
                        |
                        v
               IDENTIFY LIVE OBJECTS
                        |
                +-------+-------+
                |               |
                v               v
           DEAD OBJECTS     LIVE OBJECTS
                |               |
                v               v
           RECLAIM SPACE    COPY TO SURVIVOR
                                |
                                v
                          OBJECT AGING
                                |
                      +---------+---------+
                      |                   |
                      v                   v
                Still Young          Promotion rule
                      |                   |
                      v                   v
                 SURVIVOR           OLD GENERATION
                                          |
                                          v
                                  OLD-GEN COLLECTION
                                          |
                                          v
                                 MARK / RECLAIM /
                                 EVACUATE / COMPACT
                                          |
                                          v
                                    FREE MEMORY
```

## 17. 60-second revision memory map

``` text
JAVA GARBAGE COLLECTION
|
+-- 1. OBJECT ALLOCATION
|      New objects -> Eden
|      TLAB -> faster per-thread allocation
|
+-- 2. IDENTIFY LIVE OBJECTS
|      Start from GC Roots
|      Trace reachable references
|      Unreachable -> eligible for GC
|
+-- 3. SURVIVOR SPACES
|      Copy live objects
|      S0 <-> S1 alternate
|      Increase object age
|
+-- 4. PROMOTION
|      Tenuring threshold / allocation conditions
|      Young Gen -> Old Gen
|
+-- 5. OLD-GEN COLLECTION
       Mark -> Reclaim / Evacuate / Compact
```

The most important object journey to remember:

**Creation → Eden → Young GC → Survivor → Aging → Old Generation →
Reclamation**

## 18. Interview knowledge check

1.  **Why does Java divide the heap into Young and Old Generation?**\
    Because most objects die young. Separating short-lived and
    long-lived objects makes collection more efficient.

2.  **Why are there two Survivor spaces?**\
    They alternate as From Space and To Space. Live objects are copied
    from one to the other during young collection.

3.  **How does JVM identify garbage?**\
    It starts from GC Roots and traverses reachable references. Objects
    that cannot be reached are eligible for collection.

4.  **Why is copying used in Young Generation?**\
    Most young objects die quickly, so copying only the small surviving
    set is efficient.

5.  **What is object promotion?**\
    Moving surviving objects from Young Generation into Old Generation
    based on age or allocation conditions.

6.  **Can Java have memory leaks even with GC?**\
    Yes. Objects that are no longer logically needed but remain
    reachable cannot be collected.

7.  **What is Stop-The-World?**\
    A pause during which application threads stop executing while the
    JVM performs a GC operation requiring that pause.

8.  **Why is G1 called Garbage First?**\
    It prioritizes regions that offer comparatively high amounts of
    reclaimable memory.

## 19. Recommended learning sequence

1.  Object allocation and TLAB.
2.  GC Roots and reachability analysis.
3.  Mark-Sweep, Copying and Mark-Compact algorithms.
4.  Generational GC: Eden, Survivor and Old Generation.
5.  G1 internals: regions, remembered sets, card tables and concurrent
    marking.
6.  ZGC internals: colored pointers, load barriers and concurrent
    relocation.
7.  GC tuning and troubleshooting: GC logs, heap dumps, allocation rate
    and latency.

**Recommendation:** Before jumping into G1 and ZGC internals, make sure
you can explain the complete journey of one Java object:

`Creation → Eden → Minor GC → Survivor → Aging → Old Generation → Reclamation`

Once this journey is clear, advanced Garbage Collectors become much
easier to understand.
