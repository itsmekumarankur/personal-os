# Data and consistency - topics 16 to 25

## Runnable demos (plain Java, JDK 17+, no dependencies): `java File.java`

| # | File | Topic | What you see |
|---|---|---|---|
| 16 | `DatabasePerServiceDemo.java` | Database per service | A shared-table column rename silently breaks another team; private data + API does not |
| 17 | `SagaChoreographyDemo.java` | Saga, choreography | Order/Payment/Inventory react to events; out-of-stock triggers an automatic refund |
| 18 | `SagaOrchestrationDemo.java` | Saga, orchestration | One orchestrator runs steps and undoes completed steps in reverse order on failure |
| 19 | `CompensatingTransactionDemo.java` | Compensating transactions | Append-only ledger reversal, idempotent when retried |
| 20 | `OutboxPatternDemo.java` | Outbox | Dual-write inconsistency vs outbox; broker outage, relay crash, duplicate, de-duplication |
| 21 | `EventSourcingDemo.java` | Event sourcing | State from replaying events, time travel, corrections by new events, snapshots |
| 22 | `CqrsDemo.java` | CQRS | Separate write model and read models, projector keeps views updated |
| 23 | `EventualConsistencyDemo.java` | Eventual consistency | A stale replica read, then read-your-writes using a version token |
| 24 | `OptimisticLockingDemo.java` | Optimistic locking | Lost updates (2027 of 8000) vs version-checked updates (exactly 8000) |
| 25 | `DistributedIdDemo.java` | Distributed ids | Snowflake layout, 600,000 ids from 3 nodes with zero duplicates, UUID is not sortable |

## `spring_snippets/` (NOT compiled or run by the author)

| File | Topic |
|---|---|
| `VersionedEntitySnippet.java` | #24 JPA `@Version`, conflict handling and retry |
| `OutboxSnippet.java` | #20 outbox table, one transaction, scheduled relay to Kafka |

If a snippet does not compile for your versions, send the error and it will be fixed.
