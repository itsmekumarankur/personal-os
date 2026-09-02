# PIS — NRI Trading Lane

[← Back to Index](00-INDEX.md) · Related: [Account Info, Holdings & Transactions](04-Account-Info-Holdings-Transactions.md) · [Service Requests, PDF & Platform](06-Service-Requests-PDF-Platform.md) · [Glossary](07-Glossary.md)

---

## What is PIS, in plain terms?

**PIS = Public Issue System.** It's the system that handles **NRI (Non-Resident Indian) stock trading** specifically.

RBI requires NRIs to route their share buying/selling through a special **PIS bank account**, so the bank can track and report these trades to RBI for compliance under **FEMA regulations**.

It's **not** for regular resident Indian investors — it's an NRI-specific compliance layer that sits alongside normal trading.

---

## API Inventory

| Endpoint | Method | Description |
|---|---|---|
| `/api/demat/v1/accounts/pis` | GET | "Is this customer an NRI who qualifies for the PIS lane?" — checks eligibility. *Same endpoint also listed under [Account Info](04-Account-Info-Holdings-Transactions.md).* |
| `/api/demat/v1/sr/pisHoldingUpdate` | POST | Updates the record of what shares an NRI customer currently holds within the PIS system |
| `/api/demat/v1/pis/brokerDetails` | POST | Fetches which broker is linked to this customer's PIS account — PIS trades still route through a broker, just with extra RBI tracking |
| `/api/demat/v1/sr/pisBroker` | POST | A service request to **set or change** that broker mapping for the PIS account |

---

## Why this exists (the regulatory "why")

- NRIs are legally allowed to invest in Indian listed shares, but RBI wants visibility into the flow of foreign-linked capital.
- A dedicated PIS bank account becomes the single funnel through which all NRI equity trades pass.
- The bank (BIMBO Bank, in this case) acts as the compliance checkpoint — verifying, reporting, and reconciling these trades under FEMA.

---

## One-line summary

> **PIS = the NRI compliance trading lane.** Same stock market, same brokers — but every trade gets tracked through a dedicated account so the bank can report it to RBI.

---

## Related concepts

See [07-Glossary.md](07-Glossary.md) for: **PIS**, **DIS**, **Pledge** — these three terms are often confused with each other but mean very different things:

| Term | What it actually is |
|---|---|
| **PIS** | The NRI-specific *trading route* (compliance lane) |
| **DIS** | A *digital instruction slip* to transfer/sell shares (see [Service Requests](06-Service-Requests-PDF-Platform.md)) |
| **Pledge** | Using shares as *loan collateral* (see [Service Requests](06-Service-Requests-PDF-Platform.md)) |
