# Service Requests, PDF Reports & Platform/Internal — Demat API Notes

[← Back to Index](00-INDEX.md) · Related: [PIS — NRI Trading Lane](05-PIS-NRI-Trading-Lane.md) · [Account Info, Holdings & Transactions](04-Account-Info-Holdings-Transactions.md) · [Glossary](07-Glossary.md)

---

## Part 1 — Service Requests

Customer-initiated actions on existing holdings — transfers and collateral, mostly.

| Endpoint | Method | Description |
|---|---|---|
| `/api/demat/v1/sr/disIssuance` | POST | DIS (Demat Instruction Slip) issuance |
| `/api/demat/v1/getDISDetails` | POST | Get DIS details |
| `/api/demat/v1/pledgeRequest` | POST | Get pledge details |

### Plain-language definitions

**DIS = Demat Instruction Slip** — think of it like a "cheque," but for shares instead of money. To sell or transfer shares out of your demat account, you historically had to fill a physical slip authorizing the transfer. Now it's digital.

- **`disIssuance`** → Customer asking for a new DIS book/slip (or a digital DIS instruction) to authorize a share transfer/sale.
- **`getDISDetails`** → Checking the status/details of a DIS request already submitted — "did my transfer slip go through?"

**Pledge** → When someone has **pledged shares**, i.e. used their shares as collateral for a loan — similar to pledging gold for a gold loan, but with shares.

- **`pledgeRequest`** → Checking details when shares have been pledged this way.

---

## Part 2 — PDF / Report Generation

Documents the customer (or compliance) can download as proof.

| Endpoint | Method | Description |
|---|---|---|
| `/api/demat/v1/downloadCMRPdf` | POST | Download Client Master Report (CMR) — the standard identity document for a demat account, like a bank statement but for securities |
| `/api/demat/v1/downloadDematTransactionStatement` | POST | Download transaction statement |
| `/api/demat/v1/downloadHoldingsPdf` | POST | Download holdings PDF. *Same endpoint as in [Holdings & Transactions](04-Account-Info-Holdings-Transactions.md) — shared between the two categories.* |

---

## Part 3 — Platform & Internal

Infrastructure that keeps everything else running — not customer-facing.

| Endpoint | Method | Description |
|---|---|---|
| `/api/demat/v1/healthz` | GET | Health check |
| `/api/demat/v1/iDeASRedirect` | GET | IDeAS Redirect (NSDL Identity system) |
| `/api/demat/v1/zerodhaAccessDetails` | POST | Zerodha access details. *Same endpoint as in [Other Brokers](03-Other-Brokers-Zerodha-ISEC.md) — appears in both groupings.* |
| `/internal/api/demat/v1/clientIDs` | POST | Ingest Client IDs (internal-only) |

---

## Functional grouping

```
Service Requests
├── /sr/disIssuance
├── /getDISDetails
└── /pledgeRequest

PDF Reports
├── /downloadCMRPdf
├── /downloadDematTransactionStatement
└── /downloadHoldingsPdf   (shared with Holdings)

Platform / Internal
├── /healthz
├── /iDeASRedirect
├── /zerodhaAccessDetails  (shared with Other Brokers)
└── /clientIDs             (internal)
```

---

## One-line summary

> **DIS** = digital share-transfer authorization. **Pledge** = shares used as loan collateral. **PIS** = the NRI compliance trading lane (see [05-PIS-NRI-Trading-Lane.md](05-PIS-NRI-Trading-Lane.md)).
