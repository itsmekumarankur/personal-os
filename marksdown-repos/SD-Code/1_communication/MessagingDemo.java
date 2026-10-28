import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 3. MESSAGING (Kafka-style): topics, partitions, consumer groups, offsets
 *
 * A tiny in-memory broker that behaves like Kafka's core model:
 *
 *   TOPIC      = a named log of messages ("payments"), split into PARTITIONS (separate lines).
 *   PRODUCER   = writes messages. The KEY decides the partition (same key -> same partition ->
 *                ORDER is preserved for that key).
 *   CONSUMER GROUP = a team that shares the work. Each partition is read by ONE member of the group,
 *                so adding members splits the work. A different group gets its OWN full copy of the stream.
 *   OFFSET     = a bookmark per group per partition ("I have read up to message #N"), so a consumer that
 *                crashes or restarts continues where the group left off.
 *
 * Real Kafka/RabbitMQ snippets are in spring_snippets/.
 *
 * Run: java MessagingDemo.java
 */
public class MessagingDemo {

    record Message(String key, String value) {
        @Override
        public String toString() {
            return key + ":" + value;
        }
    }

    static class Topic {
        final String name;
        final List<List<Message>> partitions = new ArrayList<>();

        Topic(String name, int partitionCount) {
            this.name = name;
            for (int i = 0; i < partitionCount; i++) {
                partitions.add(new ArrayList<>());
            }
        }

        int send(String key, String value) {
            int p = Math.floorMod(key.hashCode(), partitions.size());      // same key -> same partition
            partitions.get(p).add(new Message(key, value));
            return p;
        }
    }

    static class ConsumerGroup {
        final String groupId;
        final Topic topic;
        final List<String> members = new ArrayList<>();
        final Map<Integer, Integer> committedOffsets = new HashMap<>();    // partition -> next offset to read
        Map<String, List<Integer>> assignment = new LinkedHashMap<>();

        ConsumerGroup(String groupId, Topic topic) {
            this.groupId = groupId;
            this.topic = topic;
        }

        void join(String member) {
            members.add(member);
            rebalance("'" + member + "' joined");
        }

        void leave(String member) {
            members.remove(member);
            rebalance("'" + member + "' left/crashed");
        }

        private void rebalance(String reason) {
            assignment = new LinkedHashMap<>();
            for (String m : members) {
                assignment.put(m, new ArrayList<>());
            }
            for (int p = 0; p < topic.partitions.size() && !members.isEmpty(); p++) {
                assignment.get(members.get(p % members.size())).add(p);    // spread partitions over members
            }
            System.out.println("  [" + groupId + "] rebalance (" + reason + "): " + assignment);
        }

        void poll(String member) {
            for (int p : assignment.get(member)) {
                List<Message> log = topic.partitions.get(p);
                int from = committedOffsets.getOrDefault(p, 0);
                List<Message> batch = new ArrayList<>(log.subList(from, log.size()));
                committedOffsets.put(p, log.size());                          // commit offset
                System.out.printf("  [%s] %-3s reads partition %d (offset %d..%d): %s%n",
                        groupId, member, p, from, log.size() - 1, batch.isEmpty() ? "nothing new" : batch);
            }
        }
    }

    public static void main(String[] args) {
        Topic payments = new Topic("payments", 3);

        System.out.println("1) Producer sends 9 messages. The KEY chooses the partition:");
        String[] keys = {"acc-1", "acc-2", "acc-3", "acc-1", "acc-2", "acc-3", "acc-1", "acc-2", "acc-3"};
        for (int i = 0; i < keys.length; i++) {
            int p = payments.send(keys[i], "txn" + (i + 1));
            System.out.printf("  send %-5s txn%d -> partition %d%n", keys[i], i + 1, p);
        }
        System.out.println("  Notice: each account always lands in the SAME partition, so its transactions stay in order.");

        System.out.println("\n2) Two groups read the same topic independently:");
        ConsumerGroup billing = new ConsumerGroup("billing", payments);
        ConsumerGroup analytics = new ConsumerGroup("analytics", payments);
        billing.join("c1");
        billing.join("c2");
        analytics.join("a1");
        billing.poll("c1");
        billing.poll("c2");
        analytics.poll("a1");
        System.out.println("  -> 'billing' members SPLIT the partitions; 'analytics' gets its own COMPLETE copy.");

        System.out.println("\n3) More messages arrive and a third billing consumer joins (scale out):");
        payments.send("acc-1", "txn10");
        payments.send("acc-2", "txn11");
        payments.send("acc-3", "txn12");
        billing.join("c3");
        billing.poll("c1");
        billing.poll("c2");
        billing.poll("c3");

        System.out.println("\n4) Consumer c2 crashes. Its partition moves to someone else, which continues from the committed offset:");
        payments.send("acc-1", "txn13");
        payments.send("acc-2", "txn14");
        payments.send("acc-3", "txn15");
        billing.leave("c2");
        billing.poll("c1");
        billing.poll("c3");

        System.out.println("\nKey rules: max useful consumers in a group = number of partitions; ordering is guaranteed only within a partition.");
    }
}
