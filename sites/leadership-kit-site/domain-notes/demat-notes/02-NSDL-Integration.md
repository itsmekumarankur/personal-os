# NSDL Integration — Demat API Notes

[← Back to Index](00-INDEX.md) · Related: [MOFSL Integration](01-MOFSL-Integration.md) · [Glossary](07-Glossary.md) · [Open Items](08-Open-Items-To-Confirm.md)

---

## Why NSDL exists in this flow

NSDL is the **depository** — the only entity legally allowed to hold electronic share records in India. BIMBO Bank can't open a demat account on its own; it can only **collect customer details, validate them, hand off to NSDL, and record whatever NSDL sends back.**

This is the key difference from MOFSL: with NSDL, **BIMBO Bank owns more of the validation work upfront** and gets explicit success/failure callbacks. With MOFSL, the customer leaves the app and MOFSL handles everything end-to-end with no callback.

---

## API Inventory

| API | Endpoint | Direction | Purpose |
|---|---|---|---|
| Create Order (v1) | `POST /api/demat/v1/order/create` | BIMBO Bank → NSDL | Original order creation, no consent flag — **deprecated** |
| Create Order (v2) | `POST /api/demat/v2/order/create` | BIMBO Bank → NSDL | **Active version** — adds consent capture |
| Success Redirect | `POST /api/demat/v1/handleSuccessRedirect` | NSDL → BIMBO Bank | Callback on successful account creation |
| Failure Redirect | `POST /api/demat/v1/handleFailureRedirect` | NSDL → BIMBO Bank | Callback on failed account creation |
| Check Client ID | Internal, via ESB Mule client | BIMBO Bank → NSDL | Pre-check: does this customer already have an NSDL Client ID / DP ID |

> Only **v2 create-order** is in active use. v1 is legacy and kept here for reference only.

---

## Phase 1 — Create Order (BIMBO Bank-side)

**Trigger:** customer taps "open demat account," agrees to consent, enters their linked bank account number.

```http
POST /api/demat/v2/order/create
```

1. **Validate the customer**
   - UCIC (customer ID) must be valid and active
   - Consent flag must be `true`
   - A digital signature must already exist on file for this customer
   - *Any one of these failing stops the request — it never reaches NSDL*

2. **Validate the bank account**
   - Confirms the account is real
   - Confirms the customer actually owns it

3. **Assemble the request**
   - Pulls name, PAN, email, mobile from the customer database
   - Builds the NSDL payload with customer + bank account details
   - Digitally signs the payload so NSDL can verify it wasn't tampered with

4. **Call NSDL** — signed payload sent through the middleware/ESB layer

5. **NSDL response** — NSDL opens a *temporary* order and returns a **Transaction ID** (order reference)

6. **BIMBO Bank persists state** — Transaction ID is saved against the customer record, for correlating the eventual callback

7. **Hand off to NSDL's site** — BIMBO Bank builds a redirect URL, optionally fires an event to notify downstream systems that an account creation is in flight. Customer leaves the BIMBO Bank app at this point.

---

## Phase 2 — NSDL-side processing (no BIMBO Bank API involved)

This entire phase happens on **NSDL's own portal**, outside BIMBO Bank's systems:

- Customer fills in the remaining demat application fields (KYC, nominee details, etc.) directly on NSDL's site
- NSDL cross-checks PAN against income tax records
- NSDL validates KYC details against its own registries
- If everything checks out, NSDL provisions the account and generates a **DP ID** and **Client ID**

---

## Phase 3 — Callback and save

NSDL calls back to BIMBO Bank once the customer finishes on its site. Two possible outcomes:

### ✅ Success — `POST /api/demat/v1/handleSuccessRedirect`
- NSDL sends back: DP ID, Client ID, and a digital signature
- BIMBO Bank validates the signature first (confirms the callback genuinely came from NSDL, untampered)
- DP ID and Client ID are saved to the customer's record
- Status updated to `SUCCESS` — account is live for trading

### ❌ Failure — `POST /api/demat/v1/handleFailureRedirect`
- NSDL sends back: a failure reason, and a digital signature
- BIMBO Bank validates the signature
- Failure reason and error details are saved to the record
- Status updated to `FAILED` — customer is notified so they can correct the issue and retry

---

## Internal pre-check — Check NSDL Client ID

- Not customer-facing — called internally via the ESB Mule client
- Queries NSDL: does this customer already have a Client ID / DP ID
- Returns a simple boolean
- **Intent:** avoid kicking off a duplicate `order/create` for someone who already has an account
- ⚠ Open item — see [08-Open-Items-To-Confirm.md](08-Open-Items-To-Confirm.md): unclear whether this runs automatically before every `order/create` call, or is invoked manually elsewhere

---

## End-to-End Flow

```
Customer taps "Open Demat Account"
        ↓
Validate UCIC + Consent + Digital Signature   [fail → stop, no NSDL call]
        ↓
Validate Bank Account
        ↓
Assemble + Sign Payload
        ↓
POST /v2/order/create  →  NSDL
        ↓
NSDL returns Transaction ID (temporary order)
        ↓
BIMBO Bank saves Transaction ID, redirects customer to NSDL portal
        ↓
   [Customer completes KYC/nominee on NSDL's site — outside BIMBO Bank]
        ↓
NSDL calls back:
   ├── SUCCESS → /handleSuccessRedirect → save DP ID + Client ID → status: SUCCESS
   └── FAILURE → /handleFailureRedirect → save failure reason → status: FAILED
```

---

## Quick comparison with MOFSL

| | NSDL | MOFSL |
|---|---|---|
| Account type | Demat only | 3-in-1 (Trading + Demat + Bank) |
| Who validates customer first | BIMBO Bank (heavily) | MOFSL (BIMBO Bank just redirects) |
| Callback | Yes — success/failure | None |
| Security | Digital signature | JWT token |

---

## Open items raised against this flow

Full detail in [08-Open-Items-To-Confirm.md](08-Open-Items-To-Confirm.md):
1. **Error granularity** — does each Phase 1 validation failure return a distinct error code, or one generic response?
2. **Correlation key** — confirm the callbacks key off the same Transaction ID issued at order creation.
3. **Pre-check wiring** — confirm whether the Client ID pre-check runs automatically or is invoked manually.

---

## Glossary terms used here

See [07-Glossary.md](07-Glossary.md) for full definitions of: **DP ID**, **Client ID**, **Transaction ID**, **Digital Signature**, **Consent**, **ESB Mule**.
