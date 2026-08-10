---
tags: [system-design, distributed-transactions, saga, 2pc, eventual-consistency]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/advanced-architects-lab/distributed-txns]
---

# Distributed Transactions

The problem: how do you maintain consistency across multiple services when a single logical operation spans all of them?

## Why This Is Hard

In a monolith, a DB transaction gives you ACID. In distributed systems, you have multiple databases, multiple services, and no shared transaction manager. Network partitions happen. Services fail mid-operation.

## Two-Phase Commit (2PC)

Coordinator asks all participants: "Can you commit?" (prepare phase). If all say yes, coordinator sends commit. If any say no, coordinator sends rollback.

**Problem:** Coordinator is a single point of failure. If the coordinator crashes after participants say "yes" but before "commit" is sent — participants are left in a blocking, locked state. Doesn't scale for high-throughput systems.

**Where 2PC still makes sense:** small, co-located systems with strong consistency requirements and controllable failure modes. Internal bank reconciliation with 2-3 services.

## Saga Pattern

Break the transaction into a sequence of local transactions, each publishing an event. If a step fails, run compensating transactions to undo previous steps.

Two flavors:
- **Choreography**: each service listens for events and reacts. No central orchestrator — more decoupled, but harder to track state.
- **Orchestration**: a saga orchestrator explicitly tells each service what to do next. Easier to reason about, single point of failure.

**Example from Optimus context:** MF purchase order — debit wallet → reserve units → update demat → confirm with AMFI. If demat update fails, compensate by releasing units and refunding wallet.

**Eventual consistency:** sagas accept temporary inconsistency. The system will become consistent, but not immediately.

## Idempotency

Critical for both patterns: every step must be safe to retry. If the payment service crashes after debiting but before confirming, the retry must not double-debit. Idempotency keys in the request header + deduplication in the service.

## Interactive Simulator Note

The `distributed_transactions_Interactive_Simulator.html` in the architect-kit lets you step through 2PC and saga scenarios to watch the state machine evolve. Use it when you need to rebuild intuition before a design interview.

## Related

- [[learning/system-design/kafka]] — Events that drive saga choreography
- [[learning/system-design/databases]] — Local transactions within each saga step
- [[learning/fintech/index]] — MF/demat workflows are saga use cases
