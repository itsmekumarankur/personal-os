# Other Brokers — Zerodha & ISEC Integration Notes

[← Back to Index](00-INDEX.md) · Related: [Account Info, Holdings & Transactions](04-Account-Info-Holdings-Transactions.md) · [Open Items](08-Open-Items-To-Confirm.md)

---

## Overview

Beyond MOFSL, the Demat API integrates with two more brokers: **Zerodha** (fully itemized) and **ISEC / ICICI Securities** (the largest integration surface, but barely documented in the source notes).

---

## Zerodha Integration

| Endpoint | Method | Description |
|---|---|---|
| `/api/demat/v1/accounts/zerodha` | GET | Get Zerodha-eligible accounts |
| `/api/demat/v2/accounts/zerodha` | GET | Same, V2 |
| `/zerodhaActivate` | POST | Activate the customer's Zerodha trading link |
| `/zerodhaDeactivate` | POST | Deactivate the customer's Zerodha trading link |
| `/zerodhaActivateStatus` | GET | Check the current activation state of the Zerodha link |
| `/api/demat/v1/zerodhaAccessDetails` | POST | Get Zerodha access/session details |

> ⚠ **Note:** `zerodhaAccessDetails` is also listed under [Platform & Internal](06-Service-Requests-PDF-Platform.md) — same endpoint, appears in both groupings depending on which lens you're documenting from.

### Typical Zerodha lifecycle
```
Check eligibility (accounts/zerodha)
        ↓
Activate (zerodhaActivate)
        ↓
Check status anytime (zerodhaActivateStatus)
        ↓
Get access/session details when needed (zerodhaAccessDetails)
        ↓
Deactivate when required (zerodhaDeactivate)
```

---

## ISEC (ICICI Securities) Integration

| What we know | Detail |
|---|---|
| Endpoint pattern | `/isec/*` |
| Approximate count | **~44 endpoints** |
| Itemized in source notes? | **No** — only a placeholder reference exists |
| Related endpoint elsewhere | `GET /api/demat/v1/accounts/iSec` (ISEC-eligible accounts) — see [Account Info](04-Account-Info-Holdings-Transactions.md) |

> 🚩 **This is the single biggest documentation gap across the entire Demat API.** Every other integration (NSDL, MOFSL, Zerodha) is fully itemized with endpoint, method, and purpose — ISEC is not. If you're formalizing this for an architecture review, this is the section to expand first. See [08-Open-Items-To-Confirm.md](08-Open-Items-To-Confirm.md).

---

## Broker comparison snapshot

| | MOFSL | NSDL | Zerodha | ISEC |
|---|---|---|---|---|
| Type | Broker (3-in-1) | Depository | Broker | Broker |
| Callback to BIMBO Bank? | No | Yes (success/failure) | Not documented | Not documented |
| Security | JWT | Digital signature | Not documented | Not documented |
| Endpoints documented | 3 | 6 | 6 | 0 of ~44 |
