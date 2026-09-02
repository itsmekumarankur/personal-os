# The Mutual Fund Domain, End to End
### Optimus · WinSoft · Valuefy — A Single Source of Truth

> Everything about how Optimus, WinSoft and Valuefy work together to onboard, invest, hold, redeem and lend against mutual funds — clustered by topic, framed as questions, and built to be read once and referenced forever.
>
> Companion markdown to `MF_Domain_Single_Source_of_Truth.html`. **10 topic clusters · 90+ Q&A · 20 worked scenarios · 3 core systems.**

---

## Table of Contents

1. [Foundations — AMC, Scheme, Portfolio, NAV](#1-foundations--amc-scheme-portfolio-nav)
2. [System Landscape — Optimus, WinSoft & Valuefy](#2-system-landscape--optimus-winsoft--valuefy)
3. [Investment Registry — Customer → Portfolio → Folio](#3-investment-registry--customer--portfolio--folio)
4. [Pre-Order Gatekeeping & Permissions](#4-pre-order-gatekeeping--permissions)
5. [KYC, FATCA & Onboarding](#5-kyc-fatca--onboarding)
6. [Order Placement & Lifecycle](#6-order-placement--lifecycle)
7. [Order & Portfolio Scenarios](#7-order--portfolio-scenarios)
8. [Post-Order, Holdings & Transaction Status](#8-post-order-holdings--transaction-status)
9. [Loan Against Mutual Fund (LAMF)](#9-loan-against-mutual-fund-lamf)
10. [COTS Reference — WinSoft & Valuefy](#10-cots-reference--winsoft--valuefy)

---

## 1. Foundations — AMC, Scheme, Portfolio, NAV

> **Before you dive in, sit with these:**
> - When you "invest in a mutual fund," where does your money actually go — and who decides what to buy with it?
> - If one AMC has 100 schemes, is there one common pool of money or 100 separate ones?
> - Two people invest in the same scheme on different days — why do they end up owning different numbers of units?
> - When the market goes up, what exactly goes up: the AMC's value, the NAV, or your units?

### What is an AMC, and how is it different from a scheme?

**AMC = Asset Management Company.** It's the company that creates and manages mutual fund schemes — but it never holds your money as its own. Think of it as the kitchen, not the dish.

```
AMC — the company (e.g. "XYZ Mutual Fund")
   ↓ creates many
Schemes — individual products (Large Cap, Debt, Hybrid…)
   ↓ each has its own
Portfolio — the actual stocks/bonds/cash held by that scheme
```

A single AMC never has one shared basket of money for all its schemes. **SBI Mutual Fund with 100 schemes means 100 separate portfolios**, not one giant pool split 100 ways.

| Role in the kitchen analogy | Real-world term |
|---|---|
| The company / kitchen | AMC |
| The dish / recipe | Scheme |
| The actual ingredients in the dish | Portfolio |
| The chef | Fund Manager |
| The customer | Investor |
| Price per plate | NAV |

> **If the AMC fails:** scheme assets are held under a separate regulatory structure — the AMC manages them, it doesn't own them like company cash. That separation is what protects investor money from an AMC's own business troubles.

### What is a scheme, and what's actually inside its portfolio?

A **scheme** is a specific investment product with a defined objective — "invest mostly in large companies," "invest in bonds," "balance equity and debt." That objective drives everything: its risk level, its rules, and what its portfolio is allowed to hold.

The **portfolio** is the actual basket sitting inside the scheme:

| Scheme type | Typical portfolio holdings |
|---|---|
| Equity scheme | HDFC Bank, Infosys, Reliance, TCS, ICICI Bank, a small cash buffer |
| Debt scheme | Government bonds, corporate bonds, treasury bills, cash |

**Scheme = the investment plan / rules. Portfolio = the actual holdings living inside that plan.** One AMC running 50 schemes means 50 portfolios being tracked independently — never a shared basket.

### How does money actually flow from investor to portfolio?

1. **Investors put money into a scheme** — Ravi → ₹10,000, Neha → ₹20,000, Amit → ₹30,000
2. **The scheme pools the money** — Ravi + Neha + Amit → one common pool of ₹60,000
3. **The fund manager invests per the scheme's objective** — a large-cap scheme's pooled money goes into large-cap stocks; investors never pick the individual stock.

The **fund manager** takes day-to-day buy/sell decisions, but always inside the scheme's mandate and regulator rules. The AMC appoints the fund manager; the investor never chooses each stock directly.

### If I invest ₹5,000, what do I actually end up owning?

You don't own individual stocks directly. You own **units** of the scheme — a proportionate share of whatever the scheme's portfolio is worth.

```
You invest ₹5,000
   ↓ at NAV ₹10/unit
You receive 500 units
   ↓
500 units = your proportional share of the scheme's portfolio
```

Worked example: total scheme assets ₹1,00,000, total units 10,000 → NAV = 1,00,000 / 10,000 = ₹10 per unit. At that NAV, ₹5,000 buys exactly 500 units.

### What exactly is NAV, and why does it move?

**NAV = price per unit of the scheme.**

```
NAV = (Total value of scheme assets − expenses/liabilities) / total units
```

Worked example: portfolio market value ₹10,00,000, minus expenses ₹20,000 → net assets ₹9,80,000. Total units 98,000 → NAV = 9,80,000 / 98,000 = **₹10**.

**Why it moves:** NAV is a pure reflection of the underlying portfolio. If the stocks or bonds inside the portfolio rise, net assets rise, and NAV rises — and the reverse is equally true.

```
Stocks/bonds in the portfolio move → Portfolio value moves → Net assets move → NAV moves
```

> Two people investing the same rupee amount on different days get a **different number of units**, because each day's NAV is different. Your unit count is fixed at purchase — what changes daily afterward is the NAV, and therefore your investment's current value, not your unit count.

### Two real-life analogies that make this click instantly

- **School lunch box business:** AMC = the lunch company · Scheme = one lunch plan · Portfolio = the actual food items in that lunch · Fund manager = the chef deciding ingredients · NAV = price per lunch unit · Investor = the person buying lunch units.
- **Apartment builder:** AMC = the builder · Scheme = one apartment project · Portfolio = the actual flats/assets in that project · Units = your proportional ownership of the project.

**Mastery questions for this section:**
- If one AMC has 50 schemes, why must each scheme have completely separate portfolio tracking?
- If NAV increases, does your number of units increase too — or only your investment's value?
- Why is understanding a scheme's "objective" critical before you ever look at its past returns?

---
## 2. System Landscape — Optimus, WinSoft & Valuefy

> **Before you dive in, sit with these:**
> - If Optimus isn't the source of truth for anything, what is its actual job?
> - Why do you need two downstream systems (WinSoft and Valuefy) instead of one?
> - What does it mean for a banking app to "cache" master data instead of always calling live?

### What is the overall business domain and which systems power it?

The domain is **Wealth Management**, specifically MF Investments. **Optimus** is the core customer-facing application, and it integrates with two key downstream systems:

| System | Owns |
|---|---|
| **WinSoft (WMS)** | Customer master data (KYC, FATCA), Investment Accounts, Folios, order placement & execution with RTAs, order status |
| **Valuefy** | Portfolio valuation, NAV tracking, returns calculation, goal-based recommendations, personalized fund suggestions |

### What is Optimus's architectural philosophy regarding data?

**Optimus is a pass-through and orchestration layer — never a source of truth.**

| System | Source of truth for |
|---|---|
| WinSoft | Customer master, KYC, accounts, folios, transactions |
| Valuefy | Portfolio valuation, analytics, recommendations |
| CBS (Core Banking System) | Savings account details |

> Optimus orchestrates the journey and decides what the customer sees next — but every fact it shows ultimately traces back to one of these three systems of record.

### What's the precise division of labor between WinSoft and Valuefy?

- **WinSoft (Transactional):** system of record for CRUD operations, order execution, and RTA communication.
- **Valuefy (Analytical):** system of insight for NAV, returns, recommendations, dashboards and valuation.

One executes and remembers what happened; the other tells you what it's currently worth and what to do next.

### What are the key customer-facing journeys in Optimus?

- **DIY (Do-It-Yourself):** customer manually browses and selects funds from lists or categories.
- **ACE / Journey:** a guided, simplified investment path for specific customer segments.
- **Goals-Based Investing:** customer invests toward predefined financial goals (Wedding, Retirement). Goals are configured in both WinSoft and Valuefy.
- **Carting:** aggregates multiple funds (SIP and/or Lump Sum) into a single basket before checkout.

### How is master data (fund lists, RTA codes) managed?

A scheduled **"key dump"** process syncs master data from WinSoft and Valuefy into Optimus's own database, enabling fast local validations without a live call on every check.

This is what lets Optimus power fund-discovery and search UIs, and validate things like "is this RTA code valid?" — without hitting WinSoft in real time for every screen load.

### What are the known integration pain points or architectural gaps?

1. **No native async support in WinSoft** — Optimus runs a Kafka workaround to protect against order loss when WinSoft is briefly unavailable.
2. **Pull-based status tracking** instead of real-time push or webhook updates — Optimus has to poll for the latest order status rather than being told.

Both of these surface repeatedly later — in Order Placement and in the LAMF system design — as the architectural debt that any future "Pulse" platform is meant to retire.

### Customer, Investment Account (Portfolio) and Folio — what's the actual difference?

- **Customer:** identified by a **UCIC** (Unique Customer Identification Code). Has a savings account with the bank.
- **Investment Account (IA) / Portfolio Code:** a bridge between the bank and the RTA world. A customer can have multiple IAs — it's the primary container for MF investments at the bank level.
- **Folio:** an account with a specific RTA (e.g. CAMS, KFinTech) for a specific fund. One Investment Account can hold multiple Folios, each linked to a different fund/RTA combination.

```
One Customer (UCIC)
   ↓ can have many
Investment Accounts / Portfolio Codes (P1, P2, P3…)
   ↓ each can have many
Folios (one per fund-house/RTA relationship)
```

### How does Optimus fetch a customer's investment details at the start of an order journey?

Optimus calls a composite `investment/v2` API, which internally calls two WinSoft APIs:

1. **PSM Folio for UCIC:** fetches all existing folios for the customer.
2. **PSP Folio for UCIC:** fetches all portfolios (IAs) along with KYC/FATCA information.

Optimus aggregates this, groups folios under their respective portfolios, and caches it for the journey.

**Mastery questions for this section:**
- Why would a bank deliberately design its customer-facing app to own zero source-of-truth data?
- What breaks if the "key dump" master-data sync runs late, or fails silently for a day?
- If WinSoft and Valuefy ever disagree on a number, which one should the UI trust, and why?

---

## 3. Investment Registry — Customer → Portfolio → Folio

> **Before you dive in, sit with these:**
> - Is "Portfolio Code" the same thing as "Folio"? (It isn't — and confusing the two is the single most common mistake.)
> - Who decides when a brand-new folio needs to be created — the customer, Optimus, or WinSoft?
> - What does an empty `folios: []` response actually tell you?

### Investment Account vs Folio — the exact distinction

**Investment Account (Portfolio Code):** a high-level relationship with the RTA (Registrar & Transfer Agent — CAMS/KFintech). Created when a customer first registers with the RTA. On the bank side, the Portfolio Code is the main identifier for MF investments — it acts like a bridge between BIMBO Bank and the RTA world.

**Folio:** a specific holding account for a single mutual fund scheme — the customer's unique number inside one mutual fund house/RTA (e.g. an HDFC MF folio number, an SBI MF folio number). One customer with one Investment Account can have multiple folios.

> **Portfolio Code = bank-side identity. Folio = MF house / RTA-side identity.** If an API response shows `folios: []`, it means the investment account relationship exists, but the customer has no fund-specific holdings yet — a perfectly valid "new investor" state, not an error.

### The full big picture, end to end

```
Customer (UCIC)
   ↓ one customer can have many
Investment Accounts / Portfolio Codes — P1, P2, P3…
   ↓ one portfolio can have many
Folios — one per fund house / RTA (HDFC, SBI, ICICI…)
   ↓ if a needed folio isn't present
Create New Folio in WinSoft
```

Side flows that plug into this spine:
- `UCIC → PSP Folio API → Portfolio + KYC/FATCA`
- `UCIC → PSM Folio API → Existing folios + ISIN + RTA`
- `Goal ID → mapped to Folio` (for goal-based investments)

### The two read APIs

**PSP Folio for UCIC:**
```
UCIC → PSP Folio API → WinSoft → Portfolios + KYC/FATCA status
```
Returns all portfolio codes (IAs) belonging to the customer, along with KYC and FATCA status. This is the call that powers the onboarding/permission picture.

**PSM Folio for UCIC:**
```
UCIC → PSM Folio API → WinSoft → Folio details (ISIN, RTA code)
```
Returns all existing folios for the customer, with fund details, ISIN, and RTA code — the transactional, fund-specific view.

### When and how a new folio gets created

A new folio is needed when a customer wants to invest in a fund belonging to an RTA where no folio yet exists.

```
Investment order placed
   ↓
Check: does a folio already exist for this fund/RTA?
   ↓ Found → use it      Not found ↓
WinSoft Create Folio API → new folio created
```

**Who triggers it?** **Optimus** does, during the pre-order check — the customer never sees a separate "create folio" step.

```
Optimus → Pre-order check → WinSoft → Create Folio
```

Optimus asks WinSoft to create the folio if needed, transparently, as part of getting the order ready.

### How does Goal-based investing map onto this hierarchy?

When a customer invests toward a goal (e.g. Child Education, Retirement), the **Goal ID is mapped to a specific folio** in WinSoft, so that goal transactions and holdings can be tracked properly.

```
Goal ID ↔ Folio
```

This mapping is what later lets the system answer "how much of my Retirement goal is in Axis Bluechip?" — it's revisited in detail in the Folio Switch scenario in Section 7.

**Mastery questions for this section:**
- If PSP Folio and PSM Folio ever disagree — say one shows a complete IA and the other can't find the matching folio — whose problem is that, and what should Optimus do about it?
- Could a single cart order ever span two different Investment Accounts (Portfolio Codes) for the same customer? Why or why not?
- Why does the system track Folio at this granularity instead of just "customer owns ₹X of Fund Y"?

---
## 4. Pre-Order Gatekeeping & Permissions

> **Before you dive in, sit with these:**
> - Why would a system check for a signature before checking KYC status, when KYC sounds like the "bigger" requirement?
> - What's actually being computed at app launch, before the customer has even chosen a fund?
> - What happens to a non-Savings-Account customer who tries to navigate straight to the MF section?

### What happens at app launch, before any fund is even selected?

App launch triggers **permission calculation** for the logged-in customer:

1. **Permission derivation** based on business metrics, customer profile, and registration data.
2. System calls: Optimus → WinSoft (fetch Investment Accounts & Folios), and Optimus → Valuefy (check holdings summary).

These inputs determine permissions such as access to Wealth tabs and buy/sell capability — all computed before the customer even opens the Mutual Fund tab.

### What is the full pre-order validation sequence?

Before publishing an order to Kafka, Optimus runs through, in order:

| Step | Check | Detail |
|---|---|---|
| 1 | Authentication & Customer Validation | Is the authenticated user a valid BIMBO Bank customer? |
| 2 | Account Ownership | Does the provided savings account and portfolio code (IA) belong to this customer? |
| 3 | Master Data Check | Validate fund details — RTA code, fund ID, type — against internal cached master data. |
| 4 | KYC / FATCA Status | Checked via a dedicated KYC Status API, and cross-verified from the PSP Folio for UCIC WinSoft API. |
| 5 | Folio Existence Check | PSM Folio for UCIC; if absent, triggers folio creation. |

One-line version: `Customer → Account → Fund → KYC/FATCA → Folio → Kafka`

If all checks pass, the order publishes to Kafka. If any fail, the order is rejected with a validation error.

### Why is the signature check performed before the KYC status check?

This is a deliberate **fail-fast** design. The signature is required both for e-signing KYC documents and for transaction authentication — so if the signature is missing, the customer can't complete KYC or purchase anyway, no matter what else passes.

Checking it first avoids wasting resources on downstream KYC checks that would be useless without a signature, and gives the fastest possible feedback ("you need a signature") instead of a slower, more confusing failure later.

### What happens to a customer with no Savings Account at all?

Wealth services are restricted to liability (Savings Account) customers. A non-SA customer who navigates directly to Mutual Funds is **blocked at the menu level** — they never see the "Select a fund" screen, and no investment-account or signature APIs are ever called.

```
Login → Wealth permission check → Fail → Access denied
```

### What does the RTA code in an order actually identify, and where does it come from?

The RTA code identifies the specific Registrar & Transfer Agent (e.g. CAMS, KFintech). It matters because different fund houses use different RTAs, and a customer may exist with one RTA but not another — so the system has to know exactly which RTA to query. The RTA code is typically derived from the mutual fund the customer is attempting to purchase.

**Mastery questions for this section:**
- If the cheapest check (signature) runs first but the most expensive check (folio existence, a live WinSoft call) runs last, is that purely about cost — or also about which failures are most common?
- What should the user actually see when validation fails at step 3 (Master Data) versus step 4 (KYC/FATCA)? Should the messaging differ?
- Permission calculation happens at app launch — what happens if a customer's KYC status changes mid-session? Does the cached permission ever get re-evaluated before the next login?

---
## 5. KYC, FATCA & Onboarding

> **Before you dive in, sit with these:**
> - If a customer drops off mid-KYC and comes back tomorrow, what exactly is remembered, and what is lost?
> - Why is Aadhaar mandatory from Digilocker, but PAN can be manually uploaded?
> - If Optimus's UI says "KYC In Progress" but WinSoft says "Y" — which one wins, and why does that even make sense?

### KYC mechanics

#### Who owns what in the KYC journey?

- **WinSoft is the system of record** for final KYC and FATCA compliance status.
- The **KYC journey itself is hosted by Optimus**; WMS stores only the final outcome (KYC Complete/Incomplete, FATCA Complete/Incomplete).
- The KYC/FATCA status stored in WinSoft is a critical input for calculating customer permissions in Optimus ("can this customer buy?") — computed at app launch.
- WinSoft exposes APIs (likely part of the PSP Folio response) that surface the KYC/FATCA flags Optimus uses to gate order placement. If incomplete, Optimus redirects to the right onboarding flow.

#### How is the KYC/FATCA journey managed across sessions?

- **State Management:** KYC is a multi-step workflow. If a customer drops off, Optimus saves the "initial stage" milestone so the journey can resume.
- **System of Record:** the final KYC/FATCA completion status is sent to and stored in WinSoft.
- **Journey Trigger:** the KYC/FATCA screen appears after the customer enters the investment amount and clicks "swipe to invest," but before final order submission.

#### What triggers the transition from one KYC stage to the next?

The transition is **manually triggered by an API call** from the Optimus frontend after each stage completes successfully. Example: Email Verification → Liveliness.

1. User enters email, receives OTP
2. Frontend calls `verify-email-otp`
3. Backend validates OTP
4. Backend updates internal KYC stage to `LIVELINESS_PENDING`
5. Frontend navigates to liveliness screen

The backend maintains a **state machine**, so users can resume later from the last completed stage rather than starting over.

#### Why is Aadhaar mandatory from Digilocker, but PAN can be manually uploaded?

| Aadhaar | PAN |
|---|---|
| Anchors biometric KYC (CKYC); Digilocker gives a digitally signed XML required for biometric match and CKYC submission. Manual upload lacks a verifiable digital signature. | Primarily a tax identity document; PAN can be validated independently via NSDL. Manual upload with OCR extraction is sufficient — the requirement is the PAN data, not a digitally signed container. |

#### What role does Mule play in the Digilocker flow?

Mule acts as a **middleware / event bridge**:

1. User consents in Digilocker webview
2. Digilocker sends data to a callback URL hosted on Mule
3. Mule receives and optionally transforms the payload
4. Mule calls the internal Optimus/MF Compliance endpoint `/digilocker/callback`
5. Optimus stores the data in a temporary cache

Mule handles external integration plumbing and decouples Digilocker from internal banking systems.

#### What happens if the liveliness check score is below threshold?

The user cannot proceed. The frontend shows an error ("Liveliness check failed. Please try again."), and the user is forced to retake the selfie. **This is a hard gate — no manual override, no alternate path.**

It protects against fraud patterns like photo-of-a-photo attacks and replay attempts.

#### When the system "generates the KYC document," what exactly goes into the PDF?

The PDF generation service combines:

1. **Customer Demographics** — name, address (from Windsor/CDP)
2. **FATCA / TNC Data** — tax residency, occupation, income, PEP status (from forms stored in CDP)
3. **Biometric / Liveliness Proof** — selfie image (stored in Omnidocs)
4. **Identity Proofs** — Aadhaar XML and PAN details (from Digilocker cache or manual upload)
5. **Bank & Product Details** — bank name, UCIC, MF product information

This compiled PDF is sent to the e-sign platform (**SignDesk**).

#### After e-sign, what exactly gets uploaded to CVL?

A complete KYC submission package:

1. E-signed KYC PDF
2. Supporting documents — Aadhaar XML, PAN image/certified copy
3. Liveliness selfie (proof of In-Person Verification)
4. Signed application form (often embedded in the KYC PDF)

This forms the official regulatory KYC record sent to the KRA (KYC Registration Agency).

#### Why use UCIC as the primary key instead of an internal user ID?

**UCIC (Universal Customer Identification Code)** is a bank-wide unique customer identifier spanning all products — Savings, Loans, Wealth — and is stored in the Core Banking System (CBS).

Using it instead of an internal ID: core systems (WinSoft, CBS, RAS) are already keyed on UCIC, it avoids cross-reference lookups, ensures the correct legal customer entity is used, and acts as the common language across every downstream system.

#### If a signature was missing during pre-checks and later uploaded, do all checks restart?

**No — the flow is stateful.** Once the signature upload succeeds and RAS confirms completion, the state machine resumes from the point of failure: it proceeds directly to the KYC status check, and previously successful checks are not re-run.

### Ten scenarios that stress-test the KYC design

*Each of these was originally posed as a question, then answered in a follow-up. They're combined here so you get the question and the resolved answer in one place.*

#### Scenario 1 — The "Almost There" Customer: KYC and FATCA done, but no signature on file

**Setup:** Ravi has a Savings Account and completed KYC (Aadhaar, PAN, e-sign) and FATCA in a previous session — but his signature was never captured in CBS.

**What happens when he tries to buy:**

1. Check existing folios (`portfolios/{UCIC}`) — ✅ Folios found
2. Check signature (Internal RAS API) — ❌ signature_available = false
3. STOP — redirected to the Signature Upload screen: "Your signature is not updated. Please upload signature."
4. Ravi uploads signature → RAS/update-signature succeeds
5. Since FATCA/TNC/KYC are already OK in WMS, Ravi proceeds straight to Payment / Order Confirmation

> **Key insight:** pre-checks run in sequence and fail fast. Signature is checked before KYC status, so a missing signature blocks everything else even when KYC is otherwise complete.

#### Scenario 2 — The International Investor's Dilemma: what does an NRI provide that a domestic investor doesn't?

**Setup:** Priya is an NRI, tax resident of both India and the USA, with SA and signature already on file, making her first-ever MF purchase.

**What Priya provides that domestic investors don't:**

1. **Multi-country tax residency declaration** — she selects India (default) + USA (additional)
2. **Foreign Tax Identification Number (TIN)** — for the USA, a 9-digit SSN, format-validated by the system
3. **Enhanced details** — residency type, occupation, source of income, Politically Exposed Person (PEP) status

**When this happens:** immediately after the signature check passes but the FATCA check fails.

**Where data is stored:** submitted immediately via the `fatca/update` endpoint to Windsor; Windsor then publishes the permanent record to CDP (Customer Data Platform).

A domestic investor simply selects "India only" and skips the foreign TIN entry entirely.

#### Scenario 3 — The Mid-Flow Dropout: does a half-filled FATCA form survive an app close?

**Setup:** Arjun passes signature check, fails FATCA, starts the FATCA form, selects USA, enters his US TIN/SSN — then closes the app before hitting submit.

**Day 2, he reopens the app and tries again. Does he see a pre-filled form?**

> **No. Arjun starts from scratch.** The blank FATCA form is shown again — USA selection and SSN re-entry are both required again.

| Aspect | FATCA / TNC Form | KYC Stages |
|---|---|---|
| State management | Stateless | Stateful |
| Data persistence | On final submit only | Intermediate persistence |
| Drop-off handling | Data lost | Resume supported |

> **Logic:** FATCA is a binary gate — partial data is never stored, "until unless customer submits, those intermediary values are not stored."

#### Scenario 4 — The Source of Truth Challenge: Optimus's UI says "In Progress," WinSoft says "Y"

**Setup:** Optimus shows KYC as "In Progress" at the Digilocker stage, but `portfolios/{UCIC}` on Windsor returns `UCIC1MF_KYC: "Y"`.

**Which status does the pre-check trust?** Windsor — always. **Business rule: if Windsor says "Y," trading is allowed regardless of the UI's intermediate state.**

This separates two different "sources of truth": Optimus owns the *journey orchestration* state (what screen to show), while Windsor owns the *regulatory truth* (can this person legally trade). Pre-checks only ever consult the regulatory truth.

#### Scenario 5 — The Manual Intervention: Aadhaar fetched fine, but PAN isn't in Digilocker

**What happens:** Aadhaar fetched successfully; PAN missing → manual upload allowed, with OCR + validation performed, and the journey continues normally.

> **The asymmetry:** missing Aadhaar breaks the flow entirely (it's the biometric anchor); missing PAN has a graceful alternative path (it's just a tax-identity document that can be OCR'd from an upload).

#### Scenario 6 — The Liveliness Expiry: 25 hours between liveliness and e-sign

**Setup:** a customer completed liveliness and Digilocker consent 25 hours ago, but never finished e-sign. They return to complete the purchase.

**What breaks:** Aadhaar/PAN data is cached for only **24 hours**. That cache has expired, which blocks KYC PDF generation — the customer is forced back to Digilocker to re-fetch.

> **Design insight:** a security-driven TTL deliberately limits how long intermediate KYC data is allowed to sit in cache.

#### Scenario 7 — The Pre-Check Permissions Gate: a customer with no Savings Account

Covered in Section 4 (Pre-Order Gatekeeping): blocked entirely at the menu level, no fund screen, no API calls triggered. Wealth services are restricted to liability (SA) customers.

#### Scenario 8 — The Asynchronous Black Box: is KYC really "complete" once submitted to CVL?

**Setup:** Optimus submits the e-signed KYC document to CVL (the KRA) and updates Windsor with `cv_submitted_flg: "Y"`. The purchase order then proceeds.

**Is KYC 100% complete from Optimus's perspective?** Optimus's view: yes, KYC complete. But that's a hidden risk — **CVL can still reject the submission asynchronously**, and Optimus has no responsibility to poll or check for that rejection.

```
E-sign → CVL Submit → Windsor Flag = Y → Trading Allowed
                                            ↓ (possible, later, silently)
                                       CVL rejects later
```

**Monitoring owner:** Windsor, not Optimus.

#### Scenario 9 — The Data Flow for E-Sign: where does the liveliness selfie actually travel?

From capture to final KYC submission, the selfie passes through several systems, each adding a different purpose:

| Stage | Purpose |
|---|---|
| Capture (app) | Biometric proof |
| Liveness check (3rd party) | Fraud prevention |
| Storage (Omnidocs) | Audit trail |
| PDF generation | Regulatory format |
| E-sign (SignDesk) | Legal consent |
| CVL submission | KRA filing |

#### Scenario 10 — The "Ghost" Investment Account: what does an empty `folios: []` response mean?

**Setup:** the first pre-check calls `portfolios/{UCIC}` and gets a successful response with `folios: []`.

**Interpretation:** this is a **valid state**, not an error — it simply means the customer has no holdings yet. Pre-checks continue normally; this is exactly the "new investor" path. The same API call doubles as both an existence check and the data source for whatever comes next in the journey.

### FATCA tax residency, demystified

#### What does "additional country of tax residency" actually mean?

It is **not** about where you're travelling. It's about which country has the right to ask you to pay tax or report income/assets — "Apart from India, does any other country also consider you taxable there?"

If someone selects USA as an additional tax residency, it usually means the US may treat them as taxable there because of citizenship, a green card, or meeting the US substantial-presence test.

**Easy analogy:** your home address tells you where you live; tax residency tells you which country can ask tax questions about you. A person can live in India while another country still says "from a tax point of view, you also belong in our system."

#### Why does FATCA ask this, and why is TIN needed?

FATCA exists to help identify people with tax obligations connected to the US — foreign financial institutions are generally required to identify and report certain accounts held by US account holders. So the platform is really asking: *are you only taxable in India, or also taxable somewhere else like the USA?*

**TIN (Taxpayer Identification Number)** is the exact tax identity used by that country to track you. Country name alone isn't enough — the financial institution needs the precise tax identity linked to that country. AMFI/CAMS/KFin forms make TIN (or equivalent) mandatory if the country issues one, and if a person is tax resident in more than one country outside India, a TIN must be kept for each.

> Without TIN, the declaration just says "I may be taxable in USA." With TIN, it becomes "I may be taxable in USA, and this is my exact US tax identity" — like the difference between knowing someone's country and knowing their passport number.

#### Arjun's FATCA decision tree, visually

```
"Are you tax resident in any country other than India?"
   ↓
No → simple path      Yes ↓
Mention country name (e.g. USA)
   ↓
Mention tax ID for that country (TIN / SSN)
   ↓
System now knows: which country + which tax identity
```

USA specifically draws extra attention because FATCA is heavily focused on identifying US-linked persons and accounts — selecting USA as additional tax residency makes the system require US tax-ID details more carefully than most other jurisdictions.

**One-line summary:** additional country of tax residency means another country may also treat you as taxable, and TIN is needed so that country-specific tax identity can be properly recorded for compliance.

### Designing the KYC orchestration system

#### What's the real "output" of onboarding?

Is the output "user registered," or **"user is eligible to place an MF buy order"**? For an MF buy app, it's the latter — onboarding's real job is to answer, precisely, whether the user can proceed, and if not, exactly what blocker remains.

Not all checks are equal:

| Check | Type |
|---|---|
| Signature missing | Recoverable blocker |
| KYC failed | Hard blocker |
| FATCA incomplete | Blocker |
| Folio missing | Maybe a create-on-first-buy path, not a true blocker |

#### The proposed architecture — an Onboarding Orchestrator

**Main idea:** don't let the app call five different systems and decide the flow itself. Instead: `App → Onboarding Orchestrator → all checks → one decision`.

```json
{
  "overall_status": "BLOCKED",
  "next_step": "UPLOAD_SIGNATURE",
  "completed_checks": ["FOLIO_EXISTS"],
  "pending_checks": ["SIGNATURE", "FATCA", "TNC", "KYC"]
}
```

This keeps mobile/web journeys simple — the app never has to reason about five independent systems.

```
User App
   ↓
Onboarding Orchestrator
   ↓ fans out to
Portfolio/Folio Service · Signature Service (RAS) · Compliance Service (KYC/FATCA/TNC) · Draft State Store · Eligibility Decision Engine · Journey Tracker / Audit Log
```

#### The four building blocks of the orchestrator

**Eligibility Decision Engine** — contains the business rules, evaluated in order:

```
If signature missing -> next step = upload signature
Else if KYC not valid -> next step = complete KYC
Else if FATCA incomplete -> next step = complete FATCA
Else if TNC not accepted -> next step = accept TNC
Else -> eligible for buy
```

**Compliance Aggregator** — normalizes wildly different downstream representations ("Y", true, false, null, expired, pending) into one standard internal vocabulary: `COMPLETED` `PENDING` `FAILED` `NOT_AVAILABLE` `IN_PROGRESS`.

**Draft State Store** — needed for interrupted onboarding. If Arjun fills FATCA partially and closes the app, the store keeps: `journey_id, user_id, current_step=FATCA, draft_payload={additional_tax_country: USA, tin_entered: true}, submission_status=DRAFT, last_updated_at` — so the next login can resume.

**Response contract** — one unified onboarding response, instead of scattered screen-level logic:

```json
{
  "user_id": "U123",
  "journey_status": "BLOCKED",
  "primary_blocker": "FATCA",
  "next_step": "COMPLETE_FATCA",
  "checks": {
    "folio": "COMPLETED", "signature": "COMPLETED",
    "kyc": "COMPLETED", "fatca": "PENDING", "tnc": "COMPLETED"
  },
  "resume_supported": true
}
```

#### The onboarding state machine

```
NOT_STARTED
   ↓
PRECHECK_IN_PROGRESS
   ↓ branches to
BLOCKED_SIGNATURE · BLOCKED_KYC · BLOCKED_FATCA · BLOCKED_TNC · READY_FOR_BUY
```

For interrupted journeys specifically: `BLOCKED_FATCA → FATCA_DRAFT_SAVED → FATCA_SUBMITTED → READY_FOR_BUY`.

**Minimal database entities:** `onboarding_journey` (journey_id, user_id, status, primary_blocker, current_step, started_at, updated_at), `onboarding_check_status` (per check_type/check_status/source), `onboarding_draft` (per-step draft payloads), `onboarding_audit_log` (event_type, event_details, timestamp).

#### Five decisions that make this design hold up

1. **Central orchestration** — don't spread rules across app + backend + downstream.
2. **Normalized statuses** — every dependent API response converts into one internal model.
3. **Resumable journeys** — partial onboarding must never be lost.
4. **Auditability** — every decision must be explainable: "why was the user blocked?"
5. **Idempotent step submission** — uploading a signature or submitting FATCA twice must behave safely.

**Mastery questions for this section:**

*Resilience & UX*
- If you only show one blocker at a time, the user may fix it and immediately hit another — should the backend surface every blocker up front instead?
- If downstream systems disagree (compliance API says KYC=Y, internal cache says pending), what source-of-truth and timestamp rules resolve it?

*Operability*
- How would an ops team debug a stuck journey without a structured event log like: clicked buy → folio passed → signature passed → FATCA incomplete → redirected → draft saved → app closed?
- Where exactly should business rules live — in the UI, or only in the Decision Engine — and what breaks if that boundary blurs?

---
## 6. Order Placement & Lifecycle

> **Before you dive in, sit with these:**
> - Why does Optimus respond to the customer immediately, before the order has actually reached WinSoft?
> - What's the real difference between "WinSoft doesn't support async" and "Optimus pretends WinSoft is async"?
> - If a cart has one SIP and one Lump Sum item, is that one order or two?

### What's the basic shape of an order's journey?

```
Optimus → sends order request → WinSoft → forwards to correct RTA → CAMS / KFintech / other RTA
```

Optimus places orders by calling a WinSoft API directly (`Optimus → Sync API → WinSoft`).

### What types of orders exist, and how does a combined cart order work?

- **Lump Sum** — one-time purchase.
- **SIP** — repeated investment with a start date, frequency, and installment amount.
- **Combined Order** — a cart with both SIP and Lump Sum items in one request.

```
One Optimus request — Line 1: Lump Sum, Line 2: SIP
   ↓ WinSoft splits internally
Lump Sum endpoint & SIP endpoint, called separately
```

For SIPs specifically: WinSoft reads start date, frequency, and amount; if it's a "Same Day SIP," the first debit happens immediately.

### How does an order get routed to the right RTA, and how is it tracked?

```
Order comes in
   ↓
WMS checks the fund's RTA code
   ↓ branches to
CAMS   or   KFintech
```

For each transaction line, WinSoft generates a unique Order ID and returns it to Optimus — tracking is **line-item level**, not cart level:

```
Cart Order
-------------------
Line 1 -> Order ID 101
Line 2 -> Order ID 102
-------------------
```

### The current pain point — and the Kafka workaround

The current flow is **synchronous**: `Optimus → WinSoft API → RTA`. If WinSoft is down, the order call can fail outright, with real risk of order loss.

**Current safety workaround:** Optimus pushes orders into an internal Kafka topic, queues them safely, and sends them to WinSoft later — Kafka is a temporary protection layer bolted on because WinSoft's API itself is synchronous.

```
Customer request → mutualfund/order → Optimus validates & publishes to internal Kafka → Optimus replies with a transaction ID immediately
```

A Kafka consumer inside Optimus then makes the actual synchronous HTTP call to WinSoft, and Optimus tracks the result in its internal transaction table.

### Where is this headed — the "Pulse" / Wealth Core vision?

The new Wealth Core system ("**Pulse**") is being built from scratch. The intent: Optimus publishes order messages directly to a Kafka topic *owned by Pulse*; Pulse consumes and processes asynchronously — removing the need for Optimus's internal Kafka-to-HTTP bridge entirely.

```
Optimus → Publish to Kafka → Pulse / resilient topic → WinSoft → RTA
```

**Why this is better:** no direct dependency on a live synchronous call, safer if WinSoft is temporarily down, reduced order-loss risk, and easier retries.

### How does carting actually work, and how is it different from goal-based orders?

**Carting:** entirely an Optimus-side feature — WinSoft is unaware a cart ever existed. At checkout, if the cart has both SIPs and Lump Sums, Optimus makes two separate API calls: SIPs via the MF SIP Plans API, Lump Sums via the Orders MF API. After placement, the cart dissolves and each transaction is tracked individually.

**Goal-based orders:** use a different endpoint (`goals/v2/create`). Goal metadata and recommendations come from Valuefy, and the Goal ID is passed to WinSoft during order placement — which then maps that Goal ID to a specific folio, enabling per-goal tracking.

**Mastery questions for this section:**
- If the consumer pod that picks an order off Kafka crashes right after it commits, how does the retry avoid creating a duplicate order at WinSoft?
- Once Pulse exists, does Optimus still need its own internal transaction table — or does that responsibility move too?
- Why is cart state owned entirely by Optimus instead of being synced into WinSoft as a "draft order"?

---
## 7. Order & Portfolio Scenarios

> **Before you dive in, sit with these:**
> - For a brand-new investor, in what exact order do PSP Folio, Create IA, and PSM Folio get called?
> - If the Optimus pod processing a Kafka order crashes right after sending the customer a 200 OK, what state is that order actually in?
> - Is "Direct vs Regular plan" a UI toggle, or a completely separate instrument with its own ISIN?

Twenty scenarios that take the architecture from sections 3–6 and run it through real edge cases. Grouped by theme rather than original numbering.

### Group A — First purchase & onboarding mechanics

#### Scenario 1 — The First-Time DIY Investor (Lump Sum)

**Setup:** a fully onboarded new customer, never invested before, picks a fund and a ₹10,000 Lump Sum, then clicks "Invest Now."

**What happens:** the system discovers the need for an Investment Account and Folio *just in time*, during order pre-checks — not at login.

> **Key insight:** PSP Folio (returning portfolios + KYC data) runs first. Since it returns empty, Optimus triggers Create IA. It then calls PSM Folio to check for a fund-specific folio, which also returns empty — WinSoft creates the folio automatically when it processes the order.

#### Scenario 2 — The SIP Cart with Existing Folio

**Setup:** an existing investor with portfolio `INV_ACC_001` and a folio for "XYZ Mutual Fund" starts a new SIP in "PQR Debt Fund" and adds a lump sum to the existing XYZ fund — both via "Add to Cart."

> **Key insight:** a single cart checkout request splits internally at WinSoft. The critical pre-processing step is folio enrichment for existing holdings; SIPs and Lump Sums are routed to two different WinSoft endpoints.

#### Scenario 3 — The KYC-Dropoff & FATCA Pending Case

**Setup:** a customer started KYC three days ago, dropped off after Aadhaar authentication (status `KYC_IN_PROGRESS`, stage `PAN_VERIFICATION`), never did FATCA, and now tries to place a lump sum order.

> **Key insight:** a lightweight `kyc-status` call gives early awareness on the homepage, but the **definitive block happens during the PSP Folio call at the final "Swipe to Invest" step** — ensuring the most up-to-date compliance status from WinSoft (the source of truth) gates any order, not a stale earlier check.

#### Scenario 4 — The "Same-Day SIP" Edge Case

**Setup:** on the 5th, one customer starts an SIP with first debit on the 7th; another selects "today" (the 5th) as first debit date.

> **Key insight:** the `sipDate` field is a plain date in the payload — Optimus only adds a UI label for "same-day debit." All business logic for the first installment, NAV applicability, and debit timing lives entirely inside WinSoft.

### Group B — Order resilience & data integrity

#### Scenario 5 — Post-Order: Tracking & Status Reconciliation

**Setup:** a customer placed a lump sum order 2 hours ago and checks "My Portfolio → Transactions" anxiously.

**Resolution:** the Transactions screen always makes a **fresh call** to WinSoft's transactions API — it does not rely on the internal table populated when the Kafka event was published. There's **no caching**, because statuses are too dynamic. The "Order ID" the customer sees ultimately traces back to: Optimus's initial Transaction ID → WinSoft/RTA's generated Order ID, fetched via the pull API.

#### Scenario 8 — System Failure During Order Placement

**Setup:** a customer places an SIP order; Optimus validates, generates a Transaction ID, publishes to its internal Kafka topic, sends a 200 OK — and immediately after, the consuming Optimus pod crashes.

**What the customer sees:** a successful confirmation (the 200 OK already went out) — the order sits in Optimus's DB in a pending/queued state, accepted but not yet executed at WinSoft.

**On consumer restart:** Kafka's consumer-group offset semantics ensure the message is re-delivered rather than lost; idempotent processing (keyed on the Transaction ID) prevents it from being executed twice.

**If Optimus published directly to a Pulse Kafka topic instead:** the same crash would matter much less — Pulse, not Optimus's own consumer, would own reliable delivery and retry, removing Optimus's internal Kafka-to-HTTP bridge as a point of failure.

#### Scenario 9 — The Multi-Investment Account Holder

**Setup:** a high-net-worth customer has two Investment Accounts — `INV_ACC_PERSONAL` and `INV_ACC_HUF` — and wants to invest ₹50,000 from each into the same fund.

The list of Investment Accounts in the UI is primarily populated by the **PSP Folio** call (portfolio-level data). During pre-order validation, Optimus verifies the submitted `portfolioCode` genuinely belongs to this customer before accepting the order.

> A single cart order cannot span two different portfolios — each Investment Account is validated and processed independently, which is consistent with the Investment Registry hierarchy where a Folio always sits under exactly one Portfolio Code.

#### Scenario 10 — The Master Data Dependency

**Setup:** every order payload carries an `rtaCode`, `fundName`, `nav` etc. — all Optimus local master data.

**Source of truth:** WinSoft (and, by extension, the RTAs) for fund list, RTA codes and categories. The "key dump" is a scheduled batch sync from WinSoft into Optimus's database, not a real-time API.

> **Risk:** if a fund is **INACTIVE at the RTA but still ACTIVE in Optimus's cache**, Optimus's local master-data check will pass — the order will only be rejected later, at **WinSoft**, when the live call discovers the fund is actually inactive. This is the staleness risk inherent in any cached master-data design.

#### Scenario 13 — The "PSP Folio" vs "PSM Folio" Data Discrepancy

**Setup:** a rare race condition — PSP Folio returns `KYC_STATUS=COMPLETE`, but PSM Folio fails because the customer's IA record hasn't fully propagated between WinSoft's internal modules.

**User experience:** a generic error ("We are unable to process your request at the moment. Please try again.") — the order doesn't go through, and "Swipe to Invest" fails or shows a loading error.

**Root cause:** a WinSoft-internal data consistency issue. WinSoft likely runs separate modules for Client Management/Onboarding (PSP — KYC, FATCA, Investment Account record) and Transaction Processing (PSM — folios, transactions). Create IA writes to the Client Management module; a subsequent PSM Folio call can fail if that data hasn't yet replicated to the Transaction module.

> **The right failure handling is Queue and Retry, not Fail-Fast.** Optimus should log the PSM Folio failure, still publish the order event to Kafka tagged `PENDING_FOLIO_VALIDATION`, retry with delay, and either proceed on success or mark FAILED and alert after retries exhaust. The system is designed for eventual consistency — Kafka decoupling absorbs temporary downstream inconsistencies without hurting perceived reliability.

### Group C — Holdings, goals & compliance

#### Scenario 6 — The Goal-Based Investment Flow

**Setup:** a customer uses the Goals journey, picks "Child's Education," sets a target amount/date, gets a recommended 3-fund equity+debt portfolio, accepts and invests.

**vs a DIY order:** **Valuefy** provides the goal list, risk profile and fund recommendations — called as the customer builds the goal. The final "Place Order" call hits a different endpoint (`goals/v2/create` instead of `mf/order`), and critically carries the **Goal ID** — which WinSoft later uses for folio tagging, enabling per-goal progress tracking.

#### Scenario 11 — The Folio Switch: same fund held under two different goals

**Setup:** two goals, "Retirement" (G1) and "Vacation" (G2), both invested years ago into the same fund (Axis Bluechip) — resulting in two separate folios, FOLIO_A (tagged G1) and FOLIO_B (tagged G2). The customer clicks "Switch" from the holdings page.

**Identifying the source folio** is the critical step. Valuefy's holdings response for "Axis Bluechip" must be an *array*, not a single line item — each object is a unique folio-level holding enriched with goal metadata:

```json
[
  { "fundName": "Axis Bluechip", "folioId": "FOLIO_A", "goalId": "G1", "goalName": "Retirement", "units": 150, "currentValue": 30000 },
  { "fundName": "Axis Bluechip", "folioId": "FOLIO_B", "goalId": "G2", "goalName": "Vacation", "units": 50, "currentValue": 10000 }
]
```

Clicking "Switch" on the Retirement line gives the frontend the exact context: `folioId=FOLIO_A, goalId=G1`. The switch payload to WinSoft's `/switch` endpoint must include `sourceFolioId`, `sourceFundRtaCode`, `targetFundRtaCode`, the switch amount/units, and — crucially — `goalId: "G1"`, so the new units inherit the same goal tag and the goal's asset allocation stays intact.

> A "holding" is really a **fund + folio + goal tuple**. UI and backend must always operate at this granularity for any transaction action — never at fund level alone.

#### Scenario 15 — The Nomination Flow

Nomination status is part of the onboarding profile, fetched via **PSP Folio**. SEBI mandates nomination or an explicit opt-out:

```
nominationStatus = PENDING
   ↓
Optimus blocks the order, redirects to nomination flow
   ↓
Optimus calls /update-nomination → success → order proceeds
```

Nomination is **folio-level**: a new folio requires nomination as mandatory; an existing folio that already has nomination on file needs no further action.

#### Scenario 16 — The Corporate Action Impact: Dividend Payout

**Setup:** a fund declares a dividend; the customer chose "Payout," not "Reinvestment."

**WinSoft is the system of record** for dividend credits in transaction history. Cash is configured at folio creation, typically credited to the linked savings account via CBS. On the ex-dividend date, NAV drops, Valuefy reflects the reduced NAV immediately, the cash component appears separately, and on actual payout the cash converts into a transaction-history entry.

> Corporate actions split value into a fund component and a cash component — Valuefy handles valuation, WinSoft handles the transactional record.

#### Scenario 19 — The Family Portfolio View

**Setup:** a primary user views and manages the consolidated portfolio of linked family members (spouse, children).

- **Linked members** are managed centrally by IAM, exposed via JWT claims.
- **Fetching family data** most likely uses an impersonation pattern, or a dedicated family-group API in WinSoft.
- **Placing an order on a family member's behalf** still requires the primary user's authentication and OTP, with explicit legal delegation/consent. The payload carries `targetUcic` and `targetPortfolioCode`.

> Authorization lives centrally — wealth systems act on trusted claims rather than re-implementing their own family-linkage logic.

#### Scenario 20 — The Direct Plan vs Regular Plan Selection

**Setup:** every fund has a Direct variant (lower expense ratio) and a Regular variant (includes distributor commission) — a choice that materially affects returns.

1. **Master data representation:** Direct and Regular are separate instruments with separate ISINs, not a toggle on one instrument.
2. **UI logic:** which plan is shown is filtered based on the distribution channel (DIY vs through a Relationship Manager).
3. **Folio implications:** a Regular-plan folio is not the same as a Direct-plan folio — starting in a new plan always means a new folio, even for the same underlying fund.

> Direct vs Regular is enforced through **data modeling, not a UI toggle**.

### Group D — Advanced products & edge cases

#### Scenario 7 — The Redemption Request

**Setup:** an investor wants to redeem 50% of units from a fund held for a year.

"Current Value" and available units on the redemption screen come from **Valuefy**. Currently, the redemption API call from Optimus to WinSoft is processed **synchronously** — same pattern, same risk profile as the purchase order flow before the Kafka workaround. The **Folio ID** from the holding is critical in the redemption payload to identify exactly which holding instance is being redeemed.

#### Scenario 12 — The Cart Abandonment & Session Recovery

**Setup:** a user adds a Lump Sum and an SIP to the cart, closes the app, and returns a week later.

**Cart persistence:** the cart is Optimus-only, stored in Optimus's DB keyed by `userId`, likely with a 7–30 day TTL to clean up stale carts. On login, Optimus fetches the active cart and repopulates the UI.

> **NAV is never locked in at cart addition.** The cart stores only the fund identifier and the amount/units — NAV is applied by the RTA at order execution time, based on cut-off rules. Fund-status validation is re-run in full at order placement; if the fund has gone `INACTIVE` or `CLOSED_FOR_NEW_INVESTMENT` in the meantime, the user sees an error and the item may be auto-removed from the cart.

The window between cart save and order placement is a deliberate "weak link" — the definitive validation always happens at WinSoft when the order API is actually called. **A cart is a draft intent, not a reservation** — there's no financial commitment until final submission, by design.

#### Scenario 14 — The Multi-RTA Investment

**Setup:** one Investment Account holds folios across multiple RTAs (CAMS, KFintech, etc).

The master fund dump includes an `rtaCode` (and likely an `rtaIdentifier`) per fund. Each folio returned by PSM Folio carries its own `folioNumber` and `rtaCode` to avoid ambiguity. When placing an order, Optimus calls a single generic endpoint (`POST /mf/order`) — **WinSoft selects the correct adapter internally** and handles RTA-specific authentication, formatting and error mapping.

> WinSoft abstracts RTA complexity using an Adapter Pattern at enterprise scale — Optimus never needs to know which RTA-specific quirks apply.

#### Scenario 17 — The STP (Systematic Transfer Plan): Equity to Debt

**Setup:** a customer wants to auto-transfer ₹10,000/month from "Axis Equity Fund" (source folio) into "ICICI Debt Fund" (target folio).

STP is treated as a **first-class recurring product** with its own API contract — not a manual redeem+purchase pair triggered repeatedly by the app:

```json
{
  "stpType": "EQUITY_TO_DEBT",
  "sourceFolioId": "FOLIO_EQUITY",
  "sourceFundRtaCode": "...",
  "targetFolioId": "FOLIO_DEBT",
  "targetFundRtaCode": "...",
  "transferAmount": 10000,
  "frequency": "MONTHLY",
  "startDate": "2023-12-05",
  "numberOfInstallments": 12
}
```

WinSoft requires dedicated logic for STP due to tax, eligibility and redemption rules, plus extra validations: same UCIC and IA on both legs, sufficient units in the source folio, holding-period checks, and cut-off timing.

#### Scenario 18 — Real-Time NAV vs Cut-Off Time Order

**Setup:** equity funds cut off at, say, 3:00 PM — orders before that get today's NAV, after get tomorrow's.

**Enforcement:** final authority sits with the RTA, mediated by WinSoft. The critical async gap: Optimus must pass `orderReceivedAt`, and WinSoft must honor the customer's original intent even if processing is delayed by queueing — e.g. an order placed at 2:58 PM that WinSoft only processes at 3:05 PM due to queue delay must still get the pre-cut-off NAV. **SIPs sidestep this** entirely since they're scheduled well ahead of time.

> Cut-off time is a business SLA, not just a timestamp — user intent has to flow end-to-end, surviving any async delay introduced by the Kafka layer.

**Mastery questions for this section:**

*Data integrity*
- How would you redesign cart-to-order validation so a fund going inactive mid-week is caught earlier than the final submit click?
- What's the minimum data the system needs to preserve to fully explain why a redemption used FOLIO_A and not FOLIO_B?

*Resilience*
- Which of these twenty scenarios disappear entirely once Pulse replaces the Kafka-to-HTTP bridge — and which ones are actually orthogonal to that migration?
- If WinSoft's PSP and PSM modules can fall out of sync internally, should Optimus ever treat WinSoft as a single logical system, or always as two?

---
## 8. Post-Order, Holdings & Transaction Status

> **Before you dive in, sit with these:**
> - Why doesn't Optimus simply push order-status updates to the customer the moment they change?
> - Which system tells you "what you hold," and which tells you "what happened to your order"?

### How does order status tracking actually work?

- **Pull model:** WinSoft does not push status updates.
- **Customer trigger:** when the customer views transactions or portfolio, Optimus calls WinSoft to fetch the latest statuses.
- **No caching** — statuses are too dynamic to safely cache.
- **Order ID:** the final order number is generated by WinSoft or the RTA, fetched via pull APIs.

### What's the holdings & redemption data flow?

- **Data source:** holdings data comes from Valuefy, synced with WinSoft transaction data.
- **Actions available:** redeem (full or partial), switch funds, or invest more.
- **Redemption:** currently processed via synchronous calls to downstream systems.

### Transaction & Order Status Master

**WinSoft is the authoritative source** for the lifecycle status of all orders.

```
Received → Pending at RTA → Processed → (or) Failed / Completed
```

- **Polling model:** WinSoft does NOT push status updates to Optimus — Optimus must poll WinSoft's transaction status API.
- **Customer-facing APIs:** power "My Transactions" / "Track Order." Every page view triggers a fresh call to WinSoft — no caching, because statuses are dynamic.
- **Data sync for holdings:** once an order is executed at the RTA and units are allotted, WinSoft updates its records, which are then synced to Valuefy (the portfolio and analytics system).

**Mastery questions for this section:**
- If WinSoft never pushes status changes, what's the realistic lag between "order completed at the RTA" and "customer sees it as completed" — and is that lag acceptable for a redemption versus a SIP installment?
- How would adopting a push/webhook model (once available) change the design of "My Transactions," beyond just removing the polling call?

---
## 9. Loan Against Mutual Fund (LAMF)

> LAMF is not "loan + lien on units." It's a fusion of a lending system, an investment-holding system, a risk engine, partner integrations, a real-time valuation system, and a journey/pledge orchestration layer — plus collections and liquidation control. This section designs it revision-first: business questions before boxes, fifteen named problems, then the architecture.

> **Before you dive in, sit with these:**
> - Is the bank lending against mutual fund *units*, or against their rupee *value* — and why does that distinction change the entire design?
> - Should offer generation and pledge confirmation be the same step, or two separate ones?
> - What's actually the harder engineering problem: disbursing the loan, or managing collateral risk for the life of the loan?

### Business understanding questions an architect must ask first

1. **What exactly is the bank lending against?** Mutual fund units, mutual fund value, only approved schemes, only demat holdings, or both SOA (Statement of Account) and demat? This changes custody, pledge flow, and integration design.
2. **Term loan or overdraft/credit line?** One of the biggest design splitters — a term loan disburses a fixed amount once; an OD/line lets the customer withdraw as needed with interest only on the used amount.
3. **Who controls the mutual fund holdings?** Already inside the wealth platform, discovered via RTA/CAMS/KFintech/MF Central/depository, or manually declared? This affects trust, eligibility, fraud checks and reconciliation.
4. **Do we allow all schemes?** Or exclude debt-only, hybrid-only, selected-equity-only, no ELSS, no locked-in or lien-marked schemes — this becomes a scheme eligibility service problem.
5. **What is the LTV policy?** e.g. liquid fund up to 80%, debt fund 70%, equity fund 50% — meaning loan logic is never one rule, it's a policy engine.
6. **What happens when NAV falls?** Alert the customer, block fresh drawdown, ask for top-up collateral, or auto-liquidate pledged units? This is the heart of risk design.
7. **Who performs pledge marking?** Directly by the bank, or via RTA, BSE Star MF / NSE NMF, registrar, or wealth platform partner? Without understanding this, the design is fake.
8. **When is money actually disbursed?** After eKYC, holdings fetch, eligibility, pledge confirmation, loan agreement, mandate/eSign, fraud checks — the exact order matters.
9. **Can the customer keep transacting in the pledged folio/scheme?** Redeem unpledged units, SIP more, switch, continue receiving dividends? These define the collateral control model, not side questions.
10. **What is the source of truth for outstanding collateral value?** Yesterday's NAV, latest available NAV, an internal cached valuation, or a partner valuation feed? If this is weak, risk management breaks entirely.

### First principles: what is LAMF, stripped to its essence?

```
Customer has MF units
   ↓
Bank marks lien / pledge on those units
   ↓
Bank gives loan up to allowed % of value
   ↓
If MF value falls too much → margin call / sell / liquidation to protect the bank
```

The system is really solving five core problems: **(1)** identify holdings, **(2)** decide eligibility, **(3)** lock collateral, **(4)** give/manage the loan, **(5)** continuously manage risk.

### High-level design — the system map, end to end

```
Customer App
   ↓
Journey Orchestrator
   ↓ fans out to
Customer Profile/KYC · MF Holdings · Scheme Eligibility Engine · Valuation Engine ·
Loan Policy Engine · Pledge Orchestration · Loan Management System · Agreement/eSign ·
Disbursement · Risk & Margin Monitoring · Notifications · Collections/Liquidation
```

**Typical customer flow:**

1. Open Loan Against MF → fetch holdings → show eligible schemes + drawing power
2. Customer selects schemes/folios to pledge
3. Run eligibility + valuation + policy checks → generate sanction offer
4. Customer accepts terms, eSigns
5. Create pledge/lien request → receive pledge confirmation
6. Create loan account/line → disburse money
7. Ongoing NAV monitoring + margin management

### Fifteen named design problems

#### Problem #1 — How do we model holdings?

**Thought-provoking questions:** is a holding identified by folio+scheme, or ISIN+demat account, or both? Can the same customer hold the same scheme across multiple folios? Can one folio contain both pledged and unpledged units? Do we store units as the source of truth, or only market-value snapshots? What if a partner sends delayed holding data?

**Better model:**

```
Customer
 -> Investment Account
    -> Folio / Demat Account
       -> Scheme Holding
          - scheme_id, folio_no
          - units_total, units_available, units_pledged
          - latest_nav, market_value
          - last_sync_time
```

> **Architect insight:** never model collateral only in rupee amount. Always preserve units, the NAV used, the valuation timestamp, and the haircut/LTV rule applied — because disputes will happen ("why did you allow only this much loan?"), and full explainability requires all four.

#### Problem #2 — How do we decide eligible collateral?

**Questions:** are ELSS funds excluded for lock-in? Closed-ended schemes excluded? Low-liquidity/high-volatility funds excluded? Only "approved AMC + approved scheme" combinations allowed? Can risk teams change eligibility without a code deployment? *(That last one matters most.)*

**Design answer:** a policy-driven **Scheme Eligibility Engine**.

```
Input:  scheme_id, amc_id, fund_type, lock_in_flag,
        volatility_bucket, regulatory_status, operational_support_flag
Output: eligible/ineligible, max_ltv, risk_bucket, reason_code
```

> Don't hardcode `if scheme_type == EQUITY then 50%` — this logic changes constantly. Build a policy table / rule engine instead.

#### Problem #3 — How do we calculate drawing power?

```
Collateral Value = units × latest eligible NAV
Drawing Power    = sum(collateral value × allowed LTV)
```

**Real architectural questions:** which NAV do we use? What if it's stale, or today's NAV isn't published yet? Do we apply a buffer haircut beyond LTV? Scheme level or portfolio level? Recalculate on every page load, or use a cached result?

**Better design — a Valuation Engine** combining Holdings + NAV feed + Eligibility policy + Haircut/LTV rules = Drawing Power, split into: **NAV Ingestion Service** (latest NAVs) → **Valuation Service** (scheme-level values) → **Loan Policy Engine** (LTV rules) → **Offer Engine** (final sanctioned amount) — separated because NAV and policy change at very different speeds.

#### Problem #4 — Should this be synchronous or asynchronous?

**Ask yourself:** can the user get an instant offer, or do external partner dependencies make the journey slow? Possible slow steps: holdings fetch, pledge creation, OTP/authorization, lien confirmation, document execution, loan account creation in LOS/LMS.

**Best practical design:** sync for user-facing immediate checks, async for external finalization.

```
App → sync: fetch holdings, estimate eligibility, show offer
App → async: pledge request, partner confirmation, loan activation
```

**Why:** the customer wants a fast response, but external systems are slow and failure-prone — design the journey as a state machine, not one long API chain.

#### Problem #5 — Why do we need a journey state machine?

Because LAMF is not one transaction — it's a multi-step business process.

**Sample states:** `INITIATED` `HOLDINGS_FETCHED` `ELIGIBILITY_COMPUTED` `OFFER_ACCEPTED` `AGREEMENT_SIGNED` `PLEDGE_REQUESTED` `PLEDGE_CONFIRMED` `LOAN_ACCOUNT_CREATED` `DISBURSED` `ACTIVE` `MARGIN_SHORTFALL` `LIQUIDATION_IN_PROGRESS` `CLOSED` `FAILED`

**Thought-provoking questions:** if pledge succeeds but disbursement fails, what happens? If the agreement is signed but the pledge is rejected, do we restart or roll back? If the customer exits mid-app, where do we resume? Can support safely replay the journey?

#### Problem #6 — How do we design pledge orchestration?

**Business reality:** pledge isn't a simple DB update — it involves external confirmation and legal control.

```
Customer selects holdings
   ↓
Pledge Orchestrator creates pledge request
   ↓
Sent to partner / RTA / exchange / depository
   ↓
Customer authorization / OTP / consent
   ↓
External confirmation received
   ↓
Internal collateral ledger updated
```

**Key questions:** is pledge creation idempotent? How do we avoid duplicate pledges on retry? What if the partner says "accepted" but the callback never comes — or comes twice? What if the internal DB update fails after external success?

> **Design answer:** an idempotency key per pledge request, external reference mapping, a callback event store, a reconciliation job, and a compensation workflow for stuck states.

#### Problem #7 — How do we model the collateral ledger?

Don't only store "loan amount" — store collateral as its **own ledger**:

```
Collateral Account
 - customer_id, loan_account_id
 - scheme_id, folio_no
 - pledged_units, pledge_reference
 - valuation_at_pledge, current_valuation
 - lien_status, liquidation_status
```

**Why separate it:** later you must answer exactly what units are locked, which pledge created this lien, which units were released, which were liquidated, and what their value was when the loan was granted. Without a dedicated collateral ledger, audit becomes painful.

#### Problem #8 — How do we manage risk after disbursement?

This is the true heart of the system — once the loan is active, risk is dynamic because MF value changes continuously.

**Core questions:** how often do we revalue collateral? What threshold triggers an alert, blocks drawdown, or triggers forced liquidation? Do we need human approval before liquidation? Can the customer add more schemes as top-up collateral?

```
Daily / periodic NAV refresh
   ↓
Recompute collateral value
   ↓
Compare against outstanding loan
   ↓ → healthy / warning / shortfall / liquidation zone
```

| LTV | Zone |
|---|---|
| ≤ 70% | Healthy |
| 70–75% | Warning |
| 75–80% | Freeze further drawdown |
| > 80% | Liquidation trigger |

> Risk is not just a cron job — it needs valuation freshness, threshold rules, alerting, an action workflow, an audit trail, and integration with collections.

#### Problem #9 — How do we design liquidation safely?

Sensitive because it directly affects customer assets.

**Questions:** can liquidation be automatic? Is partial liquidation allowed? Which schemes get sold first — cheapest units, or most liquid? What if the market is closed, or the partner rejects redemption due to an operational issue?

**Better design — a Liquidation Strategy Engine.** Inputs: shortfall amount, eligible pledged schemes, liquidity priority, tax/customer-fairness rules, operational constraints. Output: a redemption plan.

```
Risk breach
   ↓
Compute shortfall amount
   ↓
Choose units to redeem
   ↓
Send redemption / invoke enforcement flow
   ↓
Receive proceeds → adjust loan outstanding
```

> **Architect-level thought:** liquidation strategy is a business policy, not just technical logic — keep it configurable.

#### Problem #10 — How do we design the LOS vs LMS split?

A very common mistake is mixing onboarding with loan servicing — keep them separate:

| LOS — Loan Origination System (before disbursal) | LMS — Loan Management System (after activation) |
|---|---|
| Application, eligibility, offer generation, documents, pledge initiation, sanction decision | Account creation, interest accrual, statements, repayment, overdue, foreclosure, collections |

> Origination and servicing evolve at different speeds, and LMS is often an external enterprise platform — splitting them avoids coupling two systems with very different change cadences.

#### Problem #11 — How do we expose APIs?

Think in terms of **journey APIs**, not raw database APIs.

| Group | Example APIs |
|---|---|
| Discovery | `getEligibleHoldings(customerId)`, `getLoanEstimate(customerId)` |
| Offer | `createLoanApplication()`, `recomputeOffer()`, `acceptOffer()` |
| Pledge | `initiatePledge()`, `getPledgeStatus()` |
| Loan | `getLoanAccount()`, `drawdown()`, `repay()`, `getMarginStatus()` |
| Risk | `getCollateralSnapshot()`, `getShortfallAlerts()` |

#### Problem #12 — What domain events should exist?

This is event-heavy architecture by nature:

`HoldingsSynced` `NAVUpdated` `EligibilityComputed` `LoanOfferGenerated` `OfferAccepted` `AgreementSigned` `PledgeRequested` `PledgeConfirmed` `LoanCreated` `DisbursementCompleted` `MarginShortfallDetected` `TopUpCollateralAdded` `LiquidationTriggered` `LiquidationCompleted` `LoanClosed`

**Why events matter:** notifications, audit, CRM, collections, analytics, risk dashboards, and reconciliation all react to these — events are the contract that keeps those consumers decoupled from the core loan flow.

#### Problem #13 — Where can this system break? Five failure scenarios an architect should actively hunt for

| Case | Failure mode |
|---|---|
| 1 | Holdings shown to the user are stale, but the pledge request uses old units — the customer now sees more drawing power than is actually possible. |
| 2 | Pledge confirmed externally, but internal state remains pending — the loan stays blocked even though collateral is already locked. |
| 3 | Loan disbursed before pledge confirmation due to a race condition — a major control failure. |
| 4 | NAV crashes sharply, but the margin job runs late — risk goes unaddressed for that window. |
| 5 | Customer repays fully, but lien release is delayed — a terrible customer experience. |

These are exactly the places where a strong architect's design choices show.

#### Problem #14 — What should be strongly consistent vs eventually consistent?

| Strong consistency needed for | Eventual consistency acceptable for |
|---|---|
| Pledge confirmation before activation · loan disbursal control · outstanding balance · collateral units locked · repayment posting | Dashboards · reporting · notifications · analytics · recommendation widgets · historical aggregation |

#### Problem #15 — What data stores would you use?

| Store | Used for |
|---|---|
| **OLTP relational DB** | Applications, journey states, loan accounts, collateral ledger, repayment ledger, audit references |
| **Cache** | Latest NAV lookup, eligibility rules snapshot, active offer summary |
| **Event bus** | Callbacks, risk triggers, notifications, reconciliation workflows |
| **Search / analytics store** | Ops dashboard, customer support search, portfolio risk monitoring |

### The rough end-to-end LAMF architecture

```
Customer App
   ↓
Journey Orchestrator
   ↓ fans out to
KYC/CKYC · Holdings · Valuation Engine · Policy Engine · eSign Service · Agreement Service
   ↓ (Holdings → RTA/DP · Valuation → NAV Feed · Policy → Risk Rules)
Pledge Orchestrator
   ↓
External Pledge Partner
   ↓
Loan Origination System (LOS)
   ↓
Loan Management System (LMS)
   ↓ fans out to
Disbursement Service · Margin Engine · Collections / Liquidation
```

### Six discussion points that signal architect-level depth

1. **"Collateral is not money, it is units."** The system must preserve unit-level traceability, not just a rupee figure.
2. **"Offer generation and pledge confirmation should be separated."** Displayed eligibility is preliminary; enforceable eligibility only exists after a successful pledge.
3. **"This must be state-machine driven."** External partner calls make the journey long-running and failure-prone — a single API chain can't model that safely.
4. **"Risk monitoring is a first-class subsystem."** Not a support job bolted on afterward.
5. **"Collateral ledger must be separate from loan ledger."** Pledged-asset lifecycle and loan lifecycle are related, but not identical.
6. **"Policy engine should control eligibility, LTV, and liquidation thresholds."** Because business rules in this space change often, and should never require a deployment to change.

### One clean way to present this whole design out loud

> "I would design Loan Against Mutual Fund as a collateralized lending platform with five core capabilities: holdings discovery, eligibility and valuation, pledge orchestration, loan servicing, and continuous risk monitoring. The key architectural principle is that mutual fund units are the true collateral, so I would maintain a separate collateral ledger and state-machine-driven journey. Because external pledge partners and valuation feeds are involved, I would keep customer-facing eligibility synchronous where possible, but move pledge confirmation, callbacks, reconciliation, and margin workflows into asynchronous orchestration. The hardest part is not disbursal — it is ongoing collateral risk management and safe liquidation."

### The ultra-short summary

```
Loan Against MF system =
  holdings system
  + policy engine
  + valuation engine
  + pledge workflow
  + loan system
  + risk monitoring
  + liquidation control
```

> **The deepest architect insight:** do not design this as "loan journey only." Design it as **"collateral lifecycle + loan lifecycle + risk lifecycle"** — three lifecycles running in parallel, not one.

### Very thought-provoking questions for deeper mastery

**Product / business side**
- Why would a customer choose Loan Against MF instead of just redeeming units?
- Which customer segments are most suitable for this product?
- What schemes create high operational risk but low revenue value?
- How do we avoid lending against volatile assets at the wrong time?
- Should the customer see only approved holdings, or all holdings with reasons for ineligibility?

**Risk side**
- Should LTV depend only on scheme type, or also customer credit profile?
- One uniform margin rule, or dynamic risk buckets?
- What happens if NAV is stale for two days?
- Can drawdown continue while a warning threshold is breached?
- Should liquidation be rule-based, or maker-checker approved?

**Operations side**
- How will support see exactly where a journey is stuck?
- How do we safely replay failed callback-driven steps?
- What's the reconciliation process with the RTA / pledge partner?
- How do we release a lien safely after full repayment?
- Which SLAs matter most — offer generation, pledge marking, disbursal, or lien release?

**Architecture side**
- Which parts must be synchronous for UX, and which must be async for resilience?
- What idempotency keys exist across loan app, pledge request, disbursement, and callbacks?
- Where do we need transactional guarantees, and where is eventual consistency acceptable?
- How do we design auditability for a regulator / dispute / ops inquiry?
- What domain events are contract-worthy and stable enough for other systems to consume?

---
## 10. COTS Reference — WinSoft & Valuefy

A consolidated reference for the two off-the-shelf systems everything in this document ultimately calls into — what each one owns, the APIs each exposes, and the architectural implications of depending on them.

### WinSoft (WMS)

**What WinSoft owns end to end:** WinSoft is the primary Wealth Management System, handling core transactional operations: customer master data (KYC, FATCA), Investment Accounts, Folios, order placement & execution with RTAs, and order status.

**Master Data Provider for Fund Metadata** — WinSoft maintains and distributes the static **Fund Catalog**: Fund Name, RTA Code (critical for routing), ISIN, Fund Category (Equity/Debt/Hybrid/etc.), and allowed transaction types (SIP, Lump Sum). A defined **"key dump"** process periodically syncs this into Optimus's local database, enabling local validation and powering fund-discovery/search UIs without a real-time WinSoft call.

**Goals Configuration & Tracking** — WinSoft stores a Goals Master (predefined goal types like Wedding, Retirement, Child Education) shown in the Optimus app, and maintains the Goal-to-Folio mapping that enables per-goal progress reporting.

#### Summary of WinSoft's APIs (inferred from context)

| Category | API | Consumer / when called |
|---|---|---|
| Customer/Portfolio Data | PSP Folio for UCIC — fetch portfolios & KYC status | App launch, pre-order checks |
| Customer/Portfolio Data | PSM Folio for UCIC — fetch existing folios & holdings | Pre-order checks (folio check) |
| Customer/Portfolio Data | Create IA — create new Investment Account | Onboarding / first investment |
| Customer/Portfolio Data | Create Folio — create new folio with an RTA | First investment in a new fund house |
| Order Placement | MF Order API — place Lump Sum order | Order journey (sync call) |
| Order Placement | MF SIP Plans API — register a new SIP | Order journey (sync call) |
| Post-Order | Transactions API — fetch status of all orders | "My Transactions" / Track Order UI |
| Master Data | Fund Master Data Dump — bulk sync of fund metadata | Periodic "key dump" process |
| Goals | Goals Master API — fetch list of available goals | Goals journey UI |
| Permissions | APIs to check investment account existence & holdings | App launch (permission calculation) |

#### Key architectural implications of depending on WinSoft

1. **System of Record:** WinSoft is the single source of truth for all investment records — Portfolios, Folios, Orders, KYC Status. Valuefy derives its holdings data from WinSoft.
2. **Synchronous Coupling:** the current synchronous order API creates tight coupling and a single point of failure, necessitating the Kafka workaround inside Optimus — a recognized architectural flaw.
3. **Polling-Based Status:** no push mechanism for order status means Optimus cannot provide real-time notifications and must rely on user-initiated polling.
4. **Critical Path:** WinSoft is in the critical path for every transaction flow — Buy, SIP, Redeem, Switch. Its availability directly impacts customer-facing functionality.
5. **Upstream Dependency:** WinSoft itself depends on downstream RTAs (CAMS, KFintech, etc.) to ultimately execute orders and update holdings — making it part of a longer transactional chain than it first appears.

### Valuefy

**What Valuefy owns end to end:** Valuefy handles analytics, insights, and holdings data — it's the system of *insight*, sitting beside WinSoft's system of *record*. It provides:

- Portfolio valuation
- NAV tracking
- Returns calculation
- Goal-based recommendations
- Personalized fund suggestions

Valuefy gets its underlying data from WinSoft via batch syncs — it never originates transactional truth, only derives analytical views from it. This is exactly why, in the Folio Switch scenario (Section 7), Valuefy had to be told to expose folio-granular (not just fund-level) data: it can only ever report what WinSoft hands it, at whatever granularity WinSoft provides.

**Mastery questions for this section — and to close out the whole document with:**
- If WinSoft is the system of record and Valuefy only derives from it, what's the worst-case staleness window between "WinSoft knows" and "Valuefy shows" — and does any scenario in this document depend on that window being small?
- Given WinSoft is in the critical path for every transaction type, what would actually change for Optimus's architecture if WinSoft offered native async order placement tomorrow?
- Across everything in this document — onboarding, ordering, holdings, LAMF — which single architectural decision (Optimus owning zero source-of-truth data) shows up most often as the reason a scenario resolves the way it does?

---

*Compiled as a single reference document for the Optimus MF domain — onboarding, ordering, holdings and Loan Against Mutual Fund. Companion to `MF_Domain_Single_Source_of_Truth.html`.*
