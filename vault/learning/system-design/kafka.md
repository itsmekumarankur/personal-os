---
tags: [system-design, kafka, event-driven, messaging, distributed]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/advanced-architects-lab/kafka-design]
---

# Kafka — Event-Driven Architecture

Kafka is a distributed log. Producers append events; consumers read from any offset. The log is the source of truth.

## Core Model

```
Producer → Topic (partitioned, replicated) → Consumer Group
```

- **Topic**: a named, ordered, durable log. Partitioned for parallelism.
- **Partition**: the unit of parallelism and ordering. Within a partition, ordering is guaranteed. Across partitions, it isn't.
- **Consumer group**: multiple consumers can read the same topic independently. Within a group, each partition is consumed by exactly one consumer — this gives parallel consumption without duplicate processing.
- **Offset**: the position of a consumer in a partition. Consumers control their own offset — they can replay, seek, or pause.

## Why Kafka Works for High-Throughput Systems

- **Sequential disk writes**: Kafka writes to disk, not memory — but sequential writes are fast. No random access.
- **Zero-copy**: uses OS sendfile() — data goes from disk to network without copying to userspace.
- **Retention**: Kafka keeps events for a configurable duration (default 7 days). Consumers can replay.
- **Decoupling**: producers don't know about consumers. Add a new consumer without touching the producer.

## Key Design Decisions

**How many partitions?**
More partitions = more parallelism = more throughput. But also more file handles, more replication overhead, longer leader failover. Start conservatively; you can increase but never decrease.

**Replication factor?**
3 is the standard for production. With 3 replicas, you can lose 1 broker and still have a quorum.

**At-least-once vs. exactly-once?**
- At-least-once: default. Consumers may process duplicates if they crash after processing but before committing offset. Handle with idempotent consumers.
- Exactly-once: Kafka Transactions API. Correct, but adds latency and complexity. Use only when duplicate processing has real consequences (financial ledgers).

## Kafka at IDFC / Optimus

Optimus runs event-driven on Kafka. Wealth platform events (order placement, demat update, NAV fetch) flow through Kafka topics. The 80+ microservices consume events without tight coupling. CloudWatch and X-Ray provide observability on top.

The idfc-coder request batching also uses SQS (not Kafka) — simpler queue semantics fit better for the bounded, request-response pattern there.

## Kafka vs. SQS

| | Kafka | SQS |
|---|---|---|
| Ordering | Per-partition | FIFO queue (optional) |
| Retention | Days/weeks (replay) | 14 days max, consumed once |
| Throughput | Very high | High |
| Consumer model | Pull, offset-based | Pull, visibility timeout |
| Replay | Yes | No |

SQS for simple task queues. Kafka for event streams where replay and multiple consumers matter.

## Related

- [[learning/system-design/distributed-transactions]] — Saga choreography uses Kafka events
- [[learning/system-design/load-balancer]] — Kafka has its own partition leader-election
