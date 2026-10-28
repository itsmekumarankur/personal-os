import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

/**
 * 27. SERVICE REGISTRY AND DISCOVERY (Eureka / Consul idea)
 *
 * Problem: in the cloud, service instances come and go and get new IP addresses all the time
 * (autoscaling, crashes, deployments). You cannot hard-code "http://10.0.0.17:8080".
 *
 * Solution: a REGISTRY, like a phone book that keeps itself up to date.
 *   - an instance REGISTERS itself on startup (name + address)
 *   - it sends a HEARTBEAT every few seconds: "I'm still alive"
 *   - if heartbeats stop (crash), the registry EVICTS it after a time-to-live (TTL)
 *   - on graceful shutdown the instance DEREGISTERS at once
 *   - clients ask the registry "where is orders-service?" and CACHE the answer for a short while
 *
 * Because of heartbeat TTL and client caches, discovery data can be briefly STALE.
 * Clients must handle a dead address (timeout + retry on another instance).
 *
 * Run: java ServiceRegistryDemo.java
 */
public class ServiceRegistryDemo {

    static final long START = System.currentTimeMillis();

    static String t() {
        return String.format("t=%4d ms", System.currentTimeMillis() - START);
    }

    // --------------------------------------------------------------------- registry
    static class Registry {
        private static class Entry {
            final String address;
            volatile long lastHeartbeat;

            Entry(String address) {
                this.address = address;
                this.lastHeartbeat = System.currentTimeMillis();
            }
        }

        private final long ttlMillis;
        private final Map<String, Map<String, Entry>> services = new ConcurrentHashMap<>();

        Registry(long ttlMillis) {
            this.ttlMillis = ttlMillis;
        }

        void register(String service, String instanceId, String address) {
            services.computeIfAbsent(service, k -> new ConcurrentHashMap<>()).put(instanceId, new Entry(address));
        }

        void heartbeat(String service, String instanceId) {
            Entry e = services.getOrDefault(service, Map.of()).get(instanceId);
            if (e != null) {
                e.lastHeartbeat = System.currentTimeMillis();
            }
        }

        void deregister(String service, String instanceId) {
            services.getOrDefault(service, Map.of()).remove(instanceId);
        }

        List<String> lookup(String service) {                    // only instances with a fresh heartbeat
            long now = System.currentTimeMillis();
            List<String> alive = new ArrayList<>();
            services.getOrDefault(service, Map.of()).forEach((id, e) -> {
                if (now - e.lastHeartbeat <= ttlMillis) {
                    alive.add(id + "@" + e.address);
                }
            });
            Collections.sort(alive);
            return alive;
        }
    }

    // --------------------------------------------------------------------- a service instance
    static class ServiceInstance {
        final String service, id, address;
        final Registry registry;
        ScheduledFuture<?> heartbeatTask;

        ServiceInstance(Registry registry, String service, String id, String address) {
            this.registry = registry;
            this.service = service;
            this.id = id;
            this.address = address;
        }

        void start(ScheduledExecutorService scheduler, long heartbeatMillis) {
            registry.register(service, id, address);
            heartbeatTask = scheduler.scheduleAtFixedRate(() -> registry.heartbeat(service, id),
                    heartbeatMillis, heartbeatMillis, TimeUnit.MILLISECONDS);
        }

        void crash() {                                            // dies silently: no deregistration
            heartbeatTask.cancel(false);
        }

        void shutdownGracefully() {                               // tells the registry
            heartbeatTask.cancel(false);
            registry.deregister(service, id);
        }
    }

    // --------------------------------------------------------------------- client with a local cache
    static class DiscoveryClient {
        private final Registry registry;
        private final long refreshMillis;
        private final Map<String, List<String>> cache = new ConcurrentHashMap<>();
        private final Map<String, Long> cachedAt = new ConcurrentHashMap<>();

        DiscoveryClient(Registry registry, long refreshMillis) {
            this.registry = registry;
            this.refreshMillis = refreshMillis;
        }

        List<String> instances(String service) {
            long now = System.currentTimeMillis();
            if (!cache.containsKey(service) || now - cachedAt.get(service) > refreshMillis) {
                cache.put(service, registry.lookup(service));
                cachedAt.put(service, now);
            }
            return cache.get(service);
        }
    }

    static void show(String what, Registry registry, DiscoveryClient client) {
        System.out.println("  " + t() + " " + what);
        System.out.println("      registry says : " + registry.lookup("orders-service"));
        System.out.println("      client cache  : " + client.instances("orders-service"));
    }

    public static void main(String[] args) throws Exception {
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(4);
        Registry registry = new Registry(700);                   // evict after 700 ms without heartbeat
        DiscoveryClient client = new DiscoveryClient(registry, 600);   // client cache lives 600 ms

        ServiceInstance i1 = new ServiceInstance(registry, "orders-service", "i1", "10.0.0.1:8080");
        ServiceInstance i2 = new ServiceInstance(registry, "orders-service", "i2", "10.0.0.2:8080");
        ServiceInstance i3 = new ServiceInstance(registry, "orders-service", "i3", "10.0.0.3:8080");
        for (ServiceInstance i : List.of(i1, i2, i3)) {
            i.start(scheduler, 200);                             // heartbeat every 200 ms
        }

        show("three instances registered and heartbeating", registry, client);

        i2.crash();
        Thread.sleep(300);
        show("i2 CRASHED 300 ms ago (silent), TTL (700 ms) not reached yet: still listed, calls to it would fail", registry, client);

        Thread.sleep(800);
        show("1.1 s later: heartbeats stopped, registry evicted i2; client cache expired and refreshed", registry, client);

        i3.shutdownGracefully();
        show("i3 shut down GRACEFULLY (deregistered): registry updates instantly, client cache is briefly stale", registry, client);

        Thread.sleep(700);
        show("0.7 s later: client cache refreshed", registry, client);

        ServiceInstance i4 = new ServiceInstance(registry, "orders-service", "i4", "10.0.0.4:8080");
        i4.start(scheduler, 200);
        Thread.sleep(700);
        show("autoscaler started i4: it registered itself, nobody edited any config", registry, client);

        System.out.println("\nTakeaways: instances register themselves, heartbeats prove they are alive, TTL removes the dead, "
                + "\nand because caches can be stale, callers still need timeouts and retries on another instance.");
        scheduler.shutdownNow();
    }
}
