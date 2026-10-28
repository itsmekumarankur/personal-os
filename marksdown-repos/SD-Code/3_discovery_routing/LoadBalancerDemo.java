import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

/**
We are learning client-side load balancing — how a service chooses which server instance should handle each request. 
The code demonstrates three strategies: Round Robin (take turns), Random (pick a random healthy server),
 and Least Connections (prefer the server handling fewer active requests). It also shows how to skip unhealthy servers 
 and what happens when all servers are down. 
In real applications, tools like Spring Cloud LoadBalancer can handle this automatically.
 */
public class LoadBalancerDemo {

    static class Instance {
        final String name;
        final boolean slow;                                 // a slow instance finishes requests much later
        volatile boolean healthy = true;
        final AtomicInteger active = new AtomicInteger();   // requests currently in progress
        int totalServed = 0;

        Instance(String name, boolean slow) {
            this.name = name;
            this.slow = slow;
        }
    }

    interface Strategy {
        Instance choose(List<Instance> instances);
    }

    static class RoundRobin implements Strategy {
        private final AtomicInteger counter = new AtomicInteger();

        public Instance choose(List<Instance> instances) {
            for (int tries = 0; tries < instances.size(); tries++) {
                Instance candidate = instances.get(Math.floorMod(counter.getAndIncrement(), instances.size()));
                if (candidate.healthy) {                      // skip unhealthy
                    return candidate;
                }
            }
            throw new NoSuchElementException("no healthy instance available");
        }
    }

    static class RandomChoice implements Strategy {
        private final Random random = new Random(42);        // fixed seed so the output is repeatable

        public Instance choose(List<Instance> instances) {
            List<Instance> healthy = instances.stream().filter(i -> i.healthy).toList();
            if (healthy.isEmpty()) {
                throw new NoSuchElementException("no healthy instance available");
            }
            return healthy.get(random.nextInt(healthy.size()));
        }
    }

    static class LeastConnections implements Strategy {
        private final AtomicInteger tieBreaker = new AtomicInteger();

        public Instance choose(List<Instance> instances) {
            List<Instance> healthy = instances.stream().filter(i -> i.healthy).toList();
            if (healthy.isEmpty()) {
                throw new NoSuchElementException("no healthy instance available");
            }
            int fewest = healthy.stream().mapToInt(i -> i.active.get()).min().getAsInt();
            List<Instance> candidates = healthy.stream().filter(i -> i.active.get() == fewest).toList();
            return candidates.get(Math.floorMod(tieBreaker.getAndIncrement(), candidates.size()));   // rotate among ties
        }
    }

    static List<Instance> freshInstances() {
        return List.of(new Instance("A (slow)", true), new Instance("B", false), new Instance("C", false));
    }

    static void simulate(String title, Strategy strategy, int requests, boolean bFailsHalfway) {
        List<Instance> instances = freshInstances();
        System.out.println(title);
        for (int r = 1; r <= requests; r++) {
            if (bFailsHalfway && r == requests / 2 + 1) {
                instances.get(1).healthy = false;
                System.out.println("   --- instance B becomes unhealthy ---");
            }
            Instance chosen = strategy.choose(instances);
            chosen.totalServed++;
            chosen.active.incrementAndGet();
            if (!chosen.slow) {
                chosen.active.decrementAndGet();             // fast instances finish immediately
            }                                                // the slow one stays busy (its requests pile up)
        }
        Map<String, Integer> served = new LinkedHashMap<>();
        instances.forEach(i -> served.put(i.name, i.totalServed));
        System.out.println("   requests served: " + served);
        System.out.println("   still in progress on slow A: " + instances.get(0).active.get() + "\n");
    }

    public static void main(String[] args) {
        simulate("1) ROUND ROBIN, 9 requests: perfectly even, even though A is slow", new RoundRobin(), 9, false);
        simulate("2) ROUND ROBIN with B failing halfway: B is skipped, traffic shifts to A and C", new RoundRobin(), 8, true);
        simulate("3) RANDOM (seeded), 9 requests: roughly even, not exact", new RandomChoice(), 9, false);
        simulate("4) LEAST CONNECTIONS, 9 requests: slow A is given less work as its queue builds up", new LeastConnections(), 9, false);

        System.out.println("5) Everything unhealthy:");
        List<Instance> dead = freshInstances();
        dead.forEach(i -> i.healthy = false);
        try {
            new RoundRobin().choose(dead);
        } catch (NoSuchElementException e) {
            System.out.println("   " + e.getMessage() + " -> caller should fail fast / use fallback, not hang");
        }

        System.out.println("\nSpring Cloud LoadBalancer does this for you: use an @LoadBalanced client with http://orders-service/... "
                + "\nand it resolves the name through the registry and rotates between healthy instances (round-robin by default).");


        /**
         * 
         HOW THE STRATEGIES WORK:
========================

1. ROUND ROBIN
   Request 1 --> A
   Request 2 --> B
   Request 3 --> C
   Request 4 --> A

   Takes turns between servers.

2. RANDOM
   Request --> Random healthy server

   Any healthy server can be selected.

3. LEAST CONNECTIONS
   A = 5 active requests
   B = 1 active request
   C = 2 active requests

   Next request --> B

   Prefers the server with the fewest active requests.


IF A SERVER FAILS:
==================

   A = Healthy
   B = DOWN       <-- Skip B
   C = Healthy

   Requests --> A or C

   If ALL servers are down:
   --> Fail fast; do not wait forever.


REMEMBER:
=========
Client-side LB = The client chooses the server.
Round Robin     = Take turns.
Random          = Pick randomly.
Least Connections = Prefer the least busy server.
         * 
        */
    }
}
