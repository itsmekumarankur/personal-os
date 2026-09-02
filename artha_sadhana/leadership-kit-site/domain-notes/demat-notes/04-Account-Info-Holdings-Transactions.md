# Account Info, Holdings & Transactions — Demat API Notes

[← Back to Index](00-INDEX.md) · Related: [PIS — NRI Trading Lane](05-PIS-NRI-Trading-Lane.md) · [Service Requests, PDF & Platform](06-Service-Requests-PDF-Platform.md) · [Open Items](08-Open-Items-To-Confirm.md)

---

## Part 1 — Account Info & Eligibility

The "who is this customer and what accounts do they have" layer — queried before most other flows run.

| Endpoint | Method | Description |
|---|---|---|
| `/api/demat/v1/accounts/debits` | GET | Get debit / linked bank accounts |
| `/api/demat/v1/accounts/pis` | GET | Get PIS-eligible accounts — checks if customer qualifies for the NRI trading lane. *Also listed under [PIS](05-PIS-NRI-Trading-Lane.md).* |
| `/api/demat/v1/accounts/iSec` | GET | Get ISEC-eligible accounts |
| `/api/demat/v1/details` | GET | Get full demat account details |
| `/api/demat/v1/detailsWithoutJointHolder` | GET | Same as above, excluding joint holder info |
| `/api/demat/v1/dematAccounts` | GET | List all demat accounts the customer holds |
| `/api/demat/v1/dematAccountExists` | GET | Check if a demat account already exists |
| `/api/demat/v1/getCRMDetails` | POST | Get demographics / KYC details. *Also counted under Service Requests in the source summary table — likely double-counted, see Open Items.* |

---

## Part 2 — Holdings & Transactions

What the customer owns, what they've done with it, and the downloadable proof.

| Endpoint | Method | Description |
|---|---|---|
| `/api/demat/v1/getHoldings` | POST | Get current demat holdings (shares) |
| `/api/demat/v1/getTransaction` | POST | Get transaction history |
| `/api/demat/v1/downloadHoldingsPdf` | POST | Download holdings as PDF. *Also listed under [PDF Reports](06-Service-Requests-PDF-Platform.md) — shared endpoint.* |
| `/api/demat/v1/downloadHoldingsExcel` | POST | Download holdings as Excel |
| `/api/demat/v1/holdingEmail` | POST | Send holdings statement via email |

---

## Functional grouping

```
Account Information
├── /details
├── /dematAccounts
├── /dematAccountExists
├── /accounts/iSec
├── /accounts/zerodha
├── /accounts/debits
├── /accounts/pis
└── /getCRMDetails

Holdings & Transactions
├── /getHoldings
├── /getTransaction
├── /holdingEmail
├── /downloadHoldingsPdf
└── /downloadHoldingsExcel
```

---

## Summary

| Category | Approx. APIs | Purpose |
|---|---:|---|
| Account Query | 8 | Retrieve eligible accounts, demat details, account info |
| Holdings & Transactions | 5 | View holdings, transaction history, download reports |

> Combined, these two areas cover ~13 of the platform's ~40+ documented endpoints — the "read layer" most other journeys depend on.

---

## Cross-references / duplicates flagged

- `accounts/pis` → shared with [PIS](05-PIS-NRI-Trading-Lane.md)
- `downloadHoldingsPdf` → shared with [PDF Reports](06-Service-Requests-PDF-Platform.md)
- `getCRMDetails` → possibly double-counted with Service Requests

Full discussion in [08-Open-Items-To-Confirm.md](08-Open-Items-To-Confirm.md).
