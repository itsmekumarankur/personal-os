import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 5. SPRING CACHING (@Cacheable, @CacheEvict) - how it works and how it fails
 *
 * Analogy: a student keeps answers on a sticky note. Ask the same question again -> read the note, don't redo the maths.
 *
 * HOW: Spring wraps your bean in a PROXY. The proxy checks the cache before calling your method.
 * This demo builds that proxy by hand with java.lang.reflect.Proxy (same trick Spring uses for @Cacheable/@Transactional/@Async).
 *
 * Scenarios:
 *   1. hit and miss                    2. TTL (expiry): data gets stale otherwise
 *   3. @CacheEvict on update           4. SELF-INVOCATION: this.method() skips the proxy, so NO caching
 *   5. CACHE STAMPEDE: 8 threads miss at once -> 8 slow calls. sync=true makes it 1.
 *   6. MUTABLE VALUE TRAP: cache hands out the SAME object; a caller who modifies it corrupts the cache for everyone.
 *
 * Real Spring version: spring_snippets/CacheSnippets.java
 * Run: java CachingProxyDemo.java
 */
public class CachingProxyDemo {

    @Retention(RetentionPolicy.RUNTIME) @interface Cacheable { String cache(); long ttlMs() default 0; boolean sync() default false; }
    @Retention(RetentionPolicy.RUNTIME) @interface CacheEvict { String cache(); }

    interface PriceService {
        @Cacheable(cache = "prices", ttlMs = 250) double getPrice(String symbol);
        @Cacheable(cache = "pricesSync", sync = true) double getPriceSync(String symbol);
        @CacheEvict(cache = "prices") void updatePrice(String symbol, double newPrice);
        double getPriceWithFee(String symbol);
        @Cacheable(cache = "symbols") List<String> topSymbols();
    }

    static class PriceServiceImpl implements PriceService {
        final AtomicInteger backendCalls = new AtomicInteger();
        final Map<String, Double> db = new ConcurrentHashMap<>(Map.of("INFY", 1500.0));

        private double slowLookup(String s) {
            backendCalls.incrementAndGet();
            try { Thread.sleep(100); } catch (InterruptedException ignored) { }      // pretend: slow database / API
            return db.get(s);
        }

        public double getPrice(String s) { return slowLookup(s); }
        public double getPriceSync(String s) { return slowLookup(s); }
        public void updatePrice(String s, double p) { db.put(s, p); }
        public double getPriceWithFee(String s) { return getPrice(s) * 1.01; }       // <-- this.getPrice(): bypasses the proxy!
        public List<String> topSymbols() { return new ArrayList<>(List.of("INFY", "TCS")); }
    }

    static class CacheHandler implements InvocationHandler {
        record Entry(Object value, long expiresAt) { boolean fresh() { return System.currentTimeMillis() < expiresAt; } }

        final Object target;
        final Map<String, Entry> store = new ConcurrentHashMap<>();
        final Map<String, Object> locks = new ConcurrentHashMap<>();
        volatile boolean trace;

        CacheHandler(Object target) { this.target = target; }

        public Object invoke(Object proxy, Method m, Object[] args) throws Throwable {
            CacheEvict evict = m.getAnnotation(CacheEvict.class);
            Cacheable cacheable = m.getAnnotation(Cacheable.class);
            if (evict != null) {
                store.keySet().removeIf(k -> k.startsWith(evict.cache() + ":"));
                if (trace) System.out.println("      [proxy] evicted cache '" + evict.cache() + "'");
                return call(m, args);
            }
            if (cacheable == null) return call(m, args);
            String key = cacheable.cache() + ":" + Arrays.toString(args);
            Entry e = store.get(key);
            if (e != null && e.fresh()) { if (trace) System.out.println("      [proxy] HIT  " + key); return e.value(); }
            if (cacheable.sync()) {
                synchronized (locks.computeIfAbsent(key, k -> new Object())) {      // single-flight: one loader, others wait
                    e = store.get(key);
                    if (e != null && e.fresh()) return e.value();
                    return load(key, cacheable, m, args);
                }
            }
            if (trace) System.out.println("      [proxy] MISS " + key + " -> calling real method");
            return load(key, cacheable, m, args);
        }

        Object load(String key, Cacheable c, Method m, Object[] args) throws Throwable {
            Object v = call(m, args);
            store.put(key, new Entry(v, c.ttlMs() > 0 ? System.currentTimeMillis() + c.ttlMs() : Long.MAX_VALUE));
            return v;
        }

        Object call(Method m, Object[] args) throws Throwable {
            try { return m.invoke(target, args); } catch (InvocationTargetException ex) { throw ex.getCause(); }
        }
    }

    record Wired(PriceService proxy, PriceServiceImpl impl, CacheHandler handler) { }

    static Wired fresh(boolean trace) {
        PriceServiceImpl impl = new PriceServiceImpl();
        CacheHandler h = new CacheHandler(impl);
        h.trace = trace;
        PriceService proxy = (PriceService) Proxy.newProxyInstance(PriceService.class.getClassLoader(), new Class<?>[]{PriceService.class}, h);
        return new Wired(proxy, impl, h);
    }

    static int stampede(PriceService svc, boolean sync) throws Exception {
        CountDownLatch gate = new CountDownLatch(1);
        List<Thread> ts = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                try { gate.await(); } catch (InterruptedException ignored) { }
                if (sync) svc.getPriceSync("INFY"); else svc.getPrice("INFY");
            });
            ts.add(t); t.start();
        }
        gate.countDown();
        for (Thread t : ts) t.join();
        return 0;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("1) hit and miss");
        Wired w = fresh(true);
        System.out.println("      price = " + w.proxy().getPrice("INFY"));
        System.out.println("      price = " + w.proxy().getPrice("INFY"));
        System.out.println("   backend calls: " + w.impl().backendCalls.get() + " (2 requests)");

        System.out.println("\n2) TTL: after 250 ms the note is thrown away");
        Thread.sleep(300);
        w.proxy().getPrice("INFY");
        System.out.println("   backend calls: " + w.impl().backendCalls.get());

        System.out.println("\n3) @CacheEvict after an update, so readers do not see stale data");
        w.proxy().updatePrice("INFY", 1600.0);
        System.out.println("      price = " + w.proxy().getPrice("INFY"));

        System.out.println("\n4) SELF-INVOCATION trap");
        w = fresh(false);
        for (int i = 0; i < 3; i++) w.proxy().getPrice("INFY");
        System.out.println("   getPrice x3          -> backend calls: " + w.impl().backendCalls.get() + "  (cached)");
        w = fresh(false);
        for (int i = 0; i < 3; i++) w.proxy().getPriceWithFee("INFY");
        System.out.println("   getPriceWithFee x3   -> backend calls: " + w.impl().backendCalls.get() + "  (it calls this.getPrice(): @Cacheable ignored!)");
        System.out.println("   FIX: move the cached method to another bean and inject it, or inject the proxy of self.");

        System.out.println("\n5) CACHE STAMPEDE on a cold cache, 8 threads at once");
        w = fresh(false);
        stampede(w.proxy(), false);
        System.out.println("   without sync=true -> backend calls: " + w.impl().backendCalls.get());
        w = fresh(false);
        stampede(w.proxy(), true);
        System.out.println("   with    sync=true -> backend calls: " + w.impl().backendCalls.get());

        System.out.println("\n6) MUTABLE VALUE TRAP");
        w = fresh(false);
        List<String> first = w.proxy().topSymbols();
        first.add("HACKED");                                    // one careless caller...
        System.out.println("   another caller now reads: " + w.proxy().topSymbols() + "  <- cache was corrupted");
        System.out.println("   FIX: cache immutable objects (records, List.copyOf) or return copies.");

        System.out.println("\nAlso remember: cache keys must include everything that changes the answer (user, locale, tenant),"
                + "\nnever cache per-user data under a shared key, and give every cache a TTL and a size limit.");
    }
}
