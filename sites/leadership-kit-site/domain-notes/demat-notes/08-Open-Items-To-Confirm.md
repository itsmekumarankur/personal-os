# Open Items — Things to Confirm With the Team

[← Back to Index](00-INDEX.md)

Everything below is flagged as **unresolved in the source notes** — not yet verified against the actual controller code. Treat this as a checklist to work through with whoever owns the relevant repos.

---

## NSDL-related

- [ ] **Error granularity** — At the UCIC → consent → signature → bank account validation chain in [NSDL Phase 1](02-NSDL-Integration.md), does each failure return a distinct error code, or one generic "validation failed" response? *Matters for how frontend/QA differentiate failure messaging.*

- [ ] **Correlation key** — Confirm `handleSuccessRedirect` / `handleFailureRedirect` actually use the same **Transaction ID** issued at order creation to look up the right customer record, rather than some other identifier.

- [ ] **Pre-check wiring** — Confirm whether the **Check Client ID** pre-check runs automatically before every `order/create` call, or is a separate, manually-invoked check elsewhere in the codebase.

---

## ISEC-related

- [ ] **Itemization gap** — ISEC is counted at **~44 endpoints** but only a `/isec/*` placeholder exists in the source notes. This is the single biggest unknown in the whole API surface. Pull the real route list before this goes into a formal architecture doc.

---

## Duplicate / shared endpoints

- [ ] **`downloadHoldingsPdf`** — appears under both [Holdings & Transactions](04-Account-Info-Holdings-Transactions.md) and [PDF Reports](06-Service-Requests-PDF-Platform.md). Confirm if it's truly one shared controller method or two separate implementations.

- [ ] **`zerodhaAccessDetails`** — appears under both [Other Brokers](03-Other-Brokers-Zerodha-ISEC.md) and [Platform/Internal](06-Service-Requests-PDF-Platform.md). Same question.

- [ ] **`getCRMDetails`** — listed under [Account Info](04-Account-Info-Holdings-Transactions.md), but the original summary table also counts it toward Service Requests. Confirm intended ownership.

- [ ] **`accounts/pis`** — appears under both [Account Info](04-Account-Info-Holdings-Transactions.md) and [PIS](05-PIS-NRI-Trading-Lane.md). This one is expected/by-design (used from two contexts) — just flagging for completeness.

---

## Why this list matters

None of these are blockers for understanding the system conceptually — but they're exactly the kind of thing that causes confusion in a formal architecture doc, an onboarding session, or a security review. Worth a 15-minute sync with Narendra/Shreyas/Geetha (or whoever owns `demat-api` controllers) to close these out before this note set is shared more widely.
