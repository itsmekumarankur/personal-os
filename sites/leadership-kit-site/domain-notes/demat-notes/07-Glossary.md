# Glossary — Key Concepts

[← Back to Index](00-INDEX.md)

The vocabulary that shows up across every integration in this note set — worth knowing cold.

---

## Identity & account terms

| Term | Plain-language definition |
|---|---|
| **DP ID** | Depository Participant ID — identifies *which bank/broker* (BIMBO Bank, in this case) the demat account sits under. |
| **Client ID** | The customer's unique ID *within* that DP. Together, **DP ID + Client ID** uniquely identify one demat account. |
| **Transaction ID** | A temporary reference NSDL gives BIMBO Bank the moment an order is created — used to match the later success/failure callback to the right customer. |

## Security & trust terms

| Term | Plain-language definition |
|---|---|
| **JWT Token** | A short-lived security token BIMBO Bank uses to securely talk to MOFSL's systems. |
| **Digital Signature** | Cryptographic proof that a payload or callback genuinely came from the claimed sender and wasn't altered in transit. |
| **Consent** | The customer's explicit agreement to open the account / share KYC data — a mandatory gate before any NSDL or MOFSL call goes out. |

## Systems & infrastructure terms

| Term | Plain-language definition |
|---|---|
| **Winsoft** | External system where MOFSL stores Demat account details — checked whenever a status check comes back `EXISTS`. |
| **ESB Mule** | The integration/middleware layer that every MOFSL and NSDL API call is routed through. |

## Product / account-type terms

| Term | Plain-language definition |
|---|---|
| **3-in-1 Account** | MOFSL's combined Trading + Demat + linked Bank account, opened in a single onboarding journey. |
| **PIS** (Public Issue System) | The NRI-specific compliance trading lane required under RBI/FEMA rules — see [05-PIS-NRI-Trading-Lane.md](05-PIS-NRI-Trading-Lane.md). |
| **DIS** (Demat Instruction Slip) | Digital authorization to transfer or sell shares out of a demat account — like a cheque, but for shares. See [06-Service-Requests-PDF-Platform.md](06-Service-Requests-PDF-Platform.md). |
| **Pledge** | Using shares as collateral for a loan — conceptually identical to pledging gold. See [06-Service-Requests-PDF-Platform.md](06-Service-Requests-PDF-Platform.md). |

---

## Quick-recall table

| If you see... | It means... |
|---|---|
| Status = `EXISTS` | Customer already has the account; check Winsoft for details |
| Status = `IN_PROGRESS` | Journey was started but not finished — return resume link |
| `redirectUrl` present | Customer needs to continue on an external portal (MOFSL/NSDL) |
| Digital signature mismatch | Reject — payload/callback may be tampered with |
| `hasConsent: false` | Stop — request never reaches the depository/broker |
