# MOFSL Integration — Demat API Notes

[← Back to Index](00-INDEX.md) · Related: [NSDL Integration](02-NSDL-Integration.md) · [Glossary](07-Glossary.md)

---

## What is MOFSL?

**MOFSL (Motilal Oswal Financial Services Ltd.)** is a brokerage firm — distinct from a depository like NSDL.

| | NSDL | MOFSL |
|---|---|---|
| **Type** | Depository (holds shares) | Broker (Trading + Demat) |
| **Account type** | Demat account only | 3-in-1 Account (Trading + Demat + Bank) |
| **Process ownership** | BIMBO Bank initiates, NSDL completes | BIMBO Bank redirects, MOFSL handles the full journey |
| **Callback** | Success/failure callbacks available | None — MOFSL owns the entire journey |
| **Security** | Digital signature required | JWT token required |

> **3-in-1 Account = Trading Account + Demat Account + Linked Bank Account** — all opened through a single MOFSL onboarding journey.

---

## API Inventory

| API | Endpoint | Purpose |
|---|---|---|
| Get Status | `GET /api/demat/v1/mofsl/status` | Check if the customer already has a MOFSL Trading/Demat account |
| Get Redirect URI (V1) | `POST /api/demat/v1/mofsl/redirecturi` | Generate redirect URL to MOFSL for account creation |
| Get Redirect URI (V2) | `POST /api/demat/v2/mofsl/redirecturi` | Same as V1 + consent validation + Kafka notification |

---

## 1. Get Status API

```http
GET /api/demat/v1/mofsl/status
```

**Purpose:** Checks whether the customer already has a MOFSL Trading and/or Demat account before starting a fresh account-opening journey.

**Input**
- UCIC (extracted from Auth Token)
- PAN (fetched from customer profile)

**Output**
```json
{
  "tradingStatus": "EXISTS",
  "dematStatus": "EXISTS",
  "redirectUrl": "https://..."
}
```

**Possible values**

| Field | Values |
|---|---|
| `tradingStatus` | `EXISTS`, `NOT_EXISTS` |
| `dematStatus` | `EXISTS`, `NOT_EXISTS`, `IN_PROGRESS`, `INITIATED`, `UNDETERMINED` |
| `redirectUrl` | Optional — present **only** when `dematStatus` is `IN_PROGRESS` |

**Internal flow**
1. Customer requests status from the BIMBO Bank app.
2. `demat-api` fetches the customer's PAN from their profile.
3. Calls the **MOFSL PAN Check API** via **ESB Mule** → returns `NOT_EXISTS` / `IN_PROGRESS` / `EXISTS`.
4. Branch on response:
   - **IN_PROGRESS** → return the Bitly resume link (an incomplete journey exists).
   - **EXISTS** → check Demat status in **Winsoft** (MOFSL's external system), then return the combined Trading + Demat status.

---

## 2. Get Redirect URI API — V1

```http
POST /api/demat/v1/mofsl/redirecturi
```

**Purpose:** Generates a redirect URL that sends the customer to the MOFSL portal to begin/continue 3-in-1 account opening.

**Input**
```json
{ "accountNumber": "..." }
```

**Output**
```json
{ "redirectUrl": "https://mofsl.com/openaccount?token=..." }
```

**Internal flow**
1. **Controller layer** validates the account number.
2. **Service layer:**
   - Requests a JWT token from MOFSL (short-lived, valid only for a limited time).
   - Builds the redirect request payload, mapping the account number.
   - Calls the **MOFSL Redirect API** via **ESB Mule**, sending the account number → receives the redirect URL.
3. Returns `redirectUrl` to the customer, who continues the journey on the MOFSL portal.
4. **No callback** — MOFSL handles the rest of the journey end-to-end; BIMBO Bank isn't notified of the outcome via this flow.

---

## 3. Get Redirect URI API — V2

```http
POST /api/demat/v2/mofsl/redirecturi
```

**Purpose:** Identical to V1, with two additions:
- Customer **consent validation**
- **Kafka notification** on redirect generation

**Input**
```json
{
  "accountNumber": "...",
  "hasConsent": true
}
```

**Output**
```json
{ "redirectUrl": "https://mofsl.com/openaccount?token=..." }
```

**Internal flow** — same as V1, with an extra **Controller-layer consent check** before proceeding to the Service layer, and a Kafka event fired once the redirect URL is generated (for downstream systems to react to).

---

## High-Level Flows

**Status check**
```
Customer → BIMBO Bank demat-api → Fetch PAN
        → MOFSL PAN Check API (ESB Mule)
        → NOT_EXISTS / IN_PROGRESS / EXISTS
        → if EXISTS: check Winsoft Demat status
        → Return combined Trading + Demat status
```

**Account creation**
```
Customer → BIMBO Bank App → POST /mofsl/redirecturi
        → Validate Account Number
        → Validate Consent (V2 only)
        → Generate JWT Token
        → Call MOFSL Redirect API (ESB Mule)
        → Receive Redirect URL
        → Return Redirect URL
        → Customer completes journey on MOFSL portal (outside BIMBO Bank)
```

---

## Glossary terms used here

See [07-Glossary.md](07-Glossary.md) for full definitions of: **3-in-1 Account**, **JWT Token**, **Winsoft**, **ESB Mule**, **Consent**.
