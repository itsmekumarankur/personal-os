# Demat API — Complete Notes (Index)

Consolidated notes covering MOFSL, NSDL, Zerodha, ISEC, Account Info, Holdings, PIS, Service Requests, PDF Reports, Platform/Internal APIs, the full glossary, and every open item flagged for follow-up.

These notes were built from three source documents (MOFSL flow, Demat API overview, NSDL flow) plus follow-up clarifications, and mirror the structure of the interactive memory map.

> **How to use this folder:** keep all files together in one folder — each file is self-contained but cross-references the others by filename. Open in Obsidian, VS Code, Typora, or any markdown viewer that supports `[links](like-this.md)`.

---

## 📂 Files in this set

| File | Covers | Endpoints/Items |
|---|---|---|
| [01-MOFSL-Integration.md](01-MOFSL-Integration.md) | 3-in-1 broker account opening | 3 |
| [02-NSDL-Integration.md](02-NSDL-Integration.md) | Depository account creation, callbacks | 6 |
| [03-Other-Brokers-Zerodha-ISEC.md](03-Other-Brokers-Zerodha-ISEC.md) | Zerodha lifecycle + ISEC gap | 7 |
| [04-Account-Info-Holdings-Transactions.md](04-Account-Info-Holdings-Transactions.md) | Account queries, holdings, statements | 13 |
| [05-PIS-NRI-Trading-Lane.md](05-PIS-NRI-Trading-Lane.md) | NRI-specific RBI/FEMA trading route | 4 |
| [06-Service-Requests-PDF-Platform.md](06-Service-Requests-PDF-Platform.md) | DIS, pledge, reports, internal/health | 10 |
| [07-Glossary.md](07-Glossary.md) | Every key term, defined plainly | 12 |
| [08-Open-Items-To-Confirm.md](08-Open-Items-To-Confirm.md) | Unresolved questions for the team | 5 |

**Total: 60 endpoints/concepts across 8 functional areas + glossary + open items.**

---

## 🏦 NSDL vs MOFSL — at a glance

| | NSDL | MOFSL |
|---|---|---|
| **Type** | Depository (holds shares) | Broker (Trading + Demat) |
| **Account type** | Demat account only | 3-in-1 (Trading + Demat + Bank) |
| **Who validates the customer first** | BIMBO Bank, heavily, before NSDL is even called | MOFSL — BIMBO Bank just redirects |
| **Callback** | Yes — explicit success/failure callbacks | None — MOFSL owns the journey end-to-end |
| **Security mechanism** | Digital signature | JWT token |

---

## 📊 API distribution by category

| Category | Approx. count | Notes |
|---|---:|---|
| Account Info & Eligibility | 8 | Eligible accounts, KYC/demographics |
| Holdings & Transactions | 5 | Holdings, history, downloads |
| NSDL Integration | 6 | Account opening + 2 callbacks + internal pre-check |
| MOFSL Integration | 3 | Status + Redirect (V1/V2) |
| Zerodha Integration | 6 | Activation lifecycle + access |
| ISEC Integration | ~44 | Largest surface — **not itemized**, see Open Items |
| PIS (NRI trading) | 4 | Broker + holding updates |
| Service Requests | 3 | DIS, pledge |
| PDF / Report Generation | 3 | CMR, statement, holdings (1 shared) |
| Platform / Internal | 4 | Health, redirect, internal ingestion |

**Overall coverage:** the Demat API spans **~40+ itemized endpoints** (60 if you count glossary terms and flagged items as map nodes), covering the complete demat account lifecycle — opening, querying, holding, trading support, and reporting — across four broker/depository integrations.

---

## ⚠️ Known duplicates / cross-references

A few endpoints legitimately serve two purposes and appear in more than one file. They're each noted where they appear, and rounded up in full in [08-Open-Items-To-Confirm.md](08-Open-Items-To-Confirm.md):

- `downloadHoldingsPdf` → Holdings **and** PDF Reports
- `zerodhaAccessDetails` → Other Brokers **and** Platform/Internal
- `accounts/pis` → Account Info **and** PIS
- `getCRMDetails` → Account Info, possibly double-counted under Service Requests too

---

## 🗺️ Companion artifact

There's also an interactive, expandable/collapsible visual version of this same content — the **memory map** — if you'd rather click through it than read it linearly.
