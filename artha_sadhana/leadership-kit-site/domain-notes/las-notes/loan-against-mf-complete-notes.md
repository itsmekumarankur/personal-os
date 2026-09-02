# Loan Against Mutual Fund — Complete System Design Notes

A collateralized lending platform mapped end to end: holdings discovery, eligibility and valuation, pledge orchestration, loan servicing, and continuous risk management.

> **Core principle to hold onto throughout:** mutual fund units are the real collateral — not a rupee number. Every section below comes back to this in some form.

---

## Table of contents

- [A. Understand the business](#a-understand-the-business)
  - [A1. Business understanding questions](#a1-business-understanding-questions-10)
  - [A2. First-principles model](#a2-first-principles-model)
- [B. Architecture overview](#b-architecture-overview)
  - [B1. High-level components](#b1-high-level-components)
  - [B2. End-to-end flow](#b2-end-to-end-flow)
- [C. Journey & state](#c-journey--state)
  - [C1. Customer journey](#c1-customer-journey)
  - [C2. Sync vs async split](#c2-sync-vs-async-split)
  - [C3. Journey state machine](#c3-journey-state-machine)
- [D. Core subsystems](#d-core-subsystems)
  - [D1. Holdings data model](#d1-holdings-data-model)
  - [D2. Eligibility engine](#d2-eligibility-engine)
  - [D3. Valuation & drawing power](#d3-valuation--drawing-power)
  - [D4. Pledge orchestration](#d4-pledge-orchestration)
  - [D5. Collateral ledger](#d5-collateral-ledger)
  - [D6. Risk & margin monitoring](#d6-risk--margin-monitoring)
  - [D7. Liquidation engine](#d7-liquidation-engine)
  - [D8. LOS vs LMS split](#d8-los-vs-lms-split)
- [E. Interfaces & events](#e-interfaces--events)
  - [E1. API design](#e1-api-design)
  - [E2. Domain events](#e2-domain-events)
- [F. Resilience & consistency](#f-resilience--consistency)
  - [F1. Failure scenarios to hunt for](#f1-failure-scenarios-to-hunt-for)
  - [F2. Consistency model](#f2-consistency-model)
  - [F3. Data stores](#f3-data-stores)
- [G. Mastery layer](#g-mastery-layer)
  - [G1. Architect-level talking points](#g1-architect-level-talking-points)
  - [G2. Deep-mastery questions](#g2-deep-mastery-questions)
  - [G3. Interview-ready answer](#g3-interview-ready-answer)
  - [G4. Ultra-short summary](#g4-ultra-short-summary)

---

## A. Understand the business

Before drawing any boxes, an architect should interrogate the business model itself. Loan Against Mutual Fund (LAMF) is not "loan + lien on units" — it's a combination of a lending system, an investment holding system, a risk engine, a partner integration layer, a real-time valuation system, a journey/onboarding orchestrator, and a collections/liquidation control system, all at once.

### A1. Business understanding questions (10)

1. **What exactly is the bank lending against?**
   Units, value, only approved schemes, only demat holdings, or both SOA (statement of account) and demat? This single choice reshapes custody, pledge flow, and the entire integration design.

2. **Is this a term loan or an overdraft / credit line?**
   One of the biggest design splitters. A term loan disburses a fixed amount once. An OD/line lets the customer draw as needed, with interest charged only on the used amount. The system design diverges sharply depending on the answer.

3. **Who controls the mutual fund holdings?**
   Are they already inside the wealth platform, discovered via RTA / CAMS / KFintech / MF Central or the depository, or manually declared by the customer? This decides trust level, eligibility checks, fraud controls, and reconciliation effort.

4. **Do we allow all schemes?**
   Or only debt, hybrid, or selected equity funds — excluding ELSS, locked-in schemes, and lien-marked schemes? This becomes a dedicated **scheme eligibility service** problem, not a one-off check.

5. **What is the LTV (loan-to-value) policy?**
   Example: liquid fund up to 80%, debt fund 70%, equity fund 50%. Loan logic is never one rule — it has to become a policy engine.

6. **What happens when NAV falls?**
   Do we alert the customer, block fresh drawdown, ask for top-up collateral, or auto-liquidate pledged units? This is the heart of risk design.

7. **Who performs pledge marking?**
   Can the bank do it directly, or does it route through an RTA, BSE StarMF / NSE NMF, a registrar, or a wealth-platform partner? Skipping this question makes the rest of the design fictional.

8. **When is money disbursed?**
   After eKYC, holdings fetch, eligibility, pledge confirmation, loan agreement, mandate/eSign, and fraud checks — the exact ordering of these steps matters as much as the steps themselves.

9. **Can the customer keep transacting in the pledged folio?**
   Can they redeem unpledged units? Keep SIPs running? Switch schemes? Keep receiving dividends? These aren't side questions — they define the entire **collateral control model**.

10. **What is the source of truth for outstanding collateral value?**
    Yesterday's NAV, the latest available NAV, an internal cached valuation, or a partner valuation feed? Get this wrong and risk management breaks underneath everything else.

### A2. First-principles model

Think of LAMF like this:

```
Customer has MF units
        |
        v
Bank marks lien / pledge on those units
        |
        v
Bank gives loan up to allowed % of value
        |
        v
If MF value falls too much,
bank protects itself using margin call / sell / liquidation
```

So the system is really solving **five core problems**, in order:

1. Identify holdings
2. Decide eligibility
3. Lock collateral
4. Give / manage the loan
5. Continuously manage risk

---

## B. Architecture overview

### B1. High-level components

A **Journey Orchestrator** sits at the center, coordinating these specialist services:

- Customer Profile / KYC Service
- MF Holdings Service
- Scheme Eligibility Engine
- Valuation Engine
- Loan Policy Engine
- Pledge Orchestration Service
- Loan Management System
- Agreement / eSign Service
- Disbursement Service
- Risk & Margin Monitoring
- Notification Service
- Collections / Liquidation Service

### B2. End-to-end flow

```
Customer App
   |
   v
Journey Orchestrator
   |
   +--> Customer Profile / KYC Service
   +--> MF Holdings Service
   +--> Scheme Eligibility Engine
   +--> Valuation Engine
   +--> Loan Policy Engine
   +--> Pledge Orchestration Service
   +--> Loan Management System
   +--> Agreement / eSign Service
   +--> Disbursement Service
   +--> Risk & Margin Monitoring
   +--> Notification Service
   +--> Collections / Liquidation Service
```

Full rough end-to-end architecture, including external dependencies:

```
                   +----------------------+
                    |   Customer App       |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Journey Orchestrator |
                    +----------+-----------+
                               |
     --------------------------------------------------------------
     |            |             |            |          |           |
     v            v             v            v          v           v
+---------+  +----------+  +----------+  +--------+ +------+ +-----------+
| KYC/CKYC|  | Holdings |  | Valuation|  | Policy | |eSign | |Agreement  |
| Service |  | Service  |  | Engine   |  | Engine | |Svc   | |Service    |
+---------+  +----------+  +----------+  +--------+ +------+ +-----------+
                  |              |             |
                  v              v             v
               RTA/DP         NAV Feed     Risk Rules

                               |
                               v
                    +----------------------+
                    | Pledge Orchestrator  |
                    +----------+-----------+
                               |
                               v
                      External Pledge Partner
                               |
                               v
                    +----------------------+
                    | Loan Origination Sys |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Loan Mgmt System     |
                    +----------+-----------+
                               |
                  --------------------------------
                  |              |              |
                  v              v              v
           Disbursement     Margin Engine   Collections /
             Service                          Liquidation
```

---

## C. Journey & state

### C1. Customer journey

The typical end-to-end customer flow:

1. Customer opens Loan Against MF
2. Fetch customer's MF holdings
3. Show eligible schemes + drawing power
4. Customer selects schemes/folios to pledge
5. Run eligibility + valuation + policy checks
6. Generate sanction offer
7. Customer accepts terms, eSigns
8. Create pledge / lien request
9. Receive pledge confirmation
10. Create loan account / line
11. Disburse money
12. Ongoing NAV monitoring + margin management

### C2. Sync vs async split

This is a critical architecture decision: can the user get an instant offer, or are there external partner dependencies that make the journey slow?

**Possible slow steps:**
- Holdings fetch
- Pledge creation
- OTP / authorization
- Lien confirmation
- Document execution
- Loan account creation in LOS / LMS

**Best practical design** — split the journey into a synchronous front half and an asynchronous back half:

```
App
 |
 +--> sync: fetch holdings, estimate eligibility, show offer
 |
 +--> async: pledge request, partner confirmation, loan activation
```

**Why:** the customer wants a fast response, but external systems are slow and failure-prone. So design the journey as a **state machine**, not as one long API chain.

### C3. Journey state machine

LAMF is not one transaction — it's a multi-step business process that needs explicit state modeling.

```
INITIATED
HOLDINGS_FETCHED
ELIGIBILITY_COMPUTED
OFFER_ACCEPTED
AGREEMENT_SIGNED
PLEDGE_REQUESTED
PLEDGE_CONFIRMED
LOAN_ACCOUNT_CREATED
DISBURSED
ACTIVE
MARGIN_SHORTFALL
LIQUIDATION_IN_PROGRESS
CLOSED
FAILED
```

**Thought-provoking questions this state model has to answer:**
- If pledge succeeds but disbursement fails, what happens?
- If the agreement is signed but the pledge is rejected, do we restart or roll back?
- If the customer exits the app midway, where do they resume?
- Can the support team replay the journey safely?

---

## D. Core subsystems

### D1. Holdings data model

**Is holding identified by folio + scheme, or by ISIN + demat account, or both?** Some related questions worth resolving early:
- Can the same customer have the same scheme across multiple folios?
- Can one folio contain both pledged and unpledged units?
- Do we store units as the source of truth, or only market-value snapshots?
- What if a partner sends delayed holding data?

**Better model — a clean hierarchy:**

```
Customer
  -> Investment Account
      -> Folio / Demat Account
          -> Scheme Holding
              - scheme_id
              - folio_no
              - units_total
              - units_available
              - units_pledged
              - latest_nav
              - market_value
              - last_sync_time
```

> **Important architect insight:** do not model collateral only in rupee amount. Always preserve units, the NAV used, the valuation timestamp, and the haircut/LTV rule applied — because later disputes ("why did you allow only this much loan?") need full explainability.

### D2. Eligibility engine

Not all holdings are acceptable collateral. Key questions:
- Are ELSS funds excluded because of lock-in?
- Are closed-ended schemes excluded?
- Are low-liquidity / high-volatility funds excluded?
- Are only "approved AMC + approved scheme" combinations allowed?
- Can the risk team change eligibility without a code deployment? *(This last one is the important one.)*

**Design answer** — a Scheme Eligibility Engine driven by policy:

```
Input:
- scheme_id
- amc_id
- fund_type
- lock_in_flag
- volatility_bucket
- regulatory status
- operational support flag

Output:
- eligible / ineligible
- max_ltv
- risk_bucket
- reason_code
```

**Why this matters:** this logic will keep changing. Never hardcode something like `if scheme_type == EQUITY then 50%`. Build a policy table / rule engine instead.

### D3. Valuation & drawing power

This is where business and tech meet directly.

**Core formula:**
```
Collateral Value = units × latest eligible NAV
Drawing Power = sum(collateral value × allowed LTV)
```

**Real architectural questions:**
- Which NAV do we use?
- What if NAV is stale, or today's NAV isn't published yet?
- Do we apply a buffer haircut beyond LTV?
- Do we compute at scheme level or portfolio level?
- Do we recalculate on every page load, or use a cached result?

**Better design — a Valuation Engine:**
```
Holdings
   +
NAV feed
   +
Eligibility policy
   +
Haircut / LTV rules
   =
Drawing Power
```

**Suggested separation:**
- NAV Ingestion Service → gets latest NAVs
- Valuation Service → computes scheme-level values
- Loan Policy Engine → applies LTV rules
- Offer Engine → produces the final sanctioned amount

This separation matters because NAV and policy change at different speeds.

### D4. Pledge orchestration

The most domain-specific part of the whole system. Pledge is **not** a simple DB update — it involves external confirmation and legal control.

**Flow sketch:**
```
Customer selects holdings
      |
      v
Pledge Orchestrator creates pledge request
      |
      v
Send request to partner / RTA / exchange / depository
      |
      v
Customer authorization / OTP / consent
      |
      v
External confirmation received
      |
      v
Internal collateral ledger updated
```

**Key questions:**
- Is pledge creation idempotent?
- How do we avoid duplicate pledges on retry?
- What if the partner says "accepted" but the callback never comes?
- What if the callback comes twice?
- What if the internal DB update fails after external success?

**Design answer** — use: an idempotency key per pledge request, external reference mapping, a callback event store, a reconciliation job, and a compensation workflow for stuck states.

### D5. Collateral ledger

A common weak point in many designs: don't only store "loan amount." Store collateral as its own ledger, fully separate from the loan ledger.

**Good model:**
```
Collateral Account
  - customer_id
  - loan_account_id
  - scheme_id
  - folio_no
  - pledged_units
  - pledge_reference
  - valuation_at_pledge
  - current_valuation
  - lien_status
  - liquidation_status
```

**Why separate?** Because later you need to answer: what exact units are locked? Which pledge created this lien? Which units were released? Which were liquidated? What was their value when the loan was granted? Without a collateral ledger, audit becomes painful.

### D6. Risk & margin monitoring

The true heart of the system. Once a loan is active, risk is dynamic because MF value changes continuously.

**Core questions:**
- How often do we revalue collateral?
- What threshold triggers an alert?
- What threshold blocks drawdown?
- What threshold triggers forced liquidation?
- Do we need human approval before liquidation?
- Can the customer add more schemes as top-up collateral?

**Risk engine loop:**
```
Daily / periodic NAV refresh
        |
        v
Recompute collateral value
        |
        v
Compare against outstanding loan
        |
        +--> healthy
        +--> warning zone
        +--> shortfall zone
        +--> liquidation zone
```

**Example zone thresholds:**

| LTV reached | Zone | Action |
|---|---|---|
| ≤ 70% | Healthy | No action |
| 70–75% | Warning | Alert customer |
| 75–80% | Shortfall | Freeze further drawdown |
| > 80% | Liquidation | Trigger forced liquidation |

> **Important architect insight:** risk is not just a cron job. It needs valuation freshness, threshold rules, alerting, an action workflow, an audit trail, and integration with collections.

### D7. Liquidation engine

Sensitive because it affects customer assets directly.

**Questions:**
- Can liquidation be automatic?
- Is partial liquidation allowed?
- Which schemes should be sold first — cheapest units first, or most liquid first?
- What if the market is closed?
- What if the partner rejects redemption due to an operational issue?

**Better design — a Liquidation Strategy Engine:**
```
Inputs:
shortfall amount
eligible pledged schemes
liquidity priority
tax / customer fairness rules
operational constraints

Output:
redemption plan
```

**Flow:**
```
Risk breach
   |
   v
Compute shortfall amount
   |
   v
Choose units to redeem
   |
   v
Send redemption / invoke enforcement flow
   |
   v
Receive proceeds
   |
   v
Adjust loan outstanding
```

> **Architect-level thought:** liquidation strategy is a business policy, not only technical logic — keep it configurable.

### D8. LOS vs LMS split

A very common mistake is mixing onboarding with loan servicing in one system. Better to separate them clearly.

**LOS — Loan Origination System** (used before disbursal):
- Application
- Eligibility
- Offer generation
- Documents
- Pledge initiation
- Sanction decision

**LMS — Loan Management System** (used after loan activation):
- Account creation
- Interest accrual
- Statements
- Repayment
- Overdue handling
- Foreclosure
- Collections

**Why split?** Origination and servicing evolve differently, and LMS is often an external enterprise platform.

---

## E. Interfaces & events

### E1. API design

Think in terms of **journey APIs**, not raw database CRUD APIs.

**Discovery APIs**
- `getEligibleHoldings(customerId)`
- `getLoanEstimate(customerId)`

**Offer APIs**
- `createLoanApplication()`
- `recomputeOffer()`
- `acceptOffer()`

**Pledge APIs**
- `initiatePledge()`
- `getPledgeStatus()`

**Loan APIs**
- `getLoanAccount()`
- `drawdown()`
- `repay()`
- `getMarginStatus()`

**Risk APIs**
- `getCollateralSnapshot()`
- `getShortfallAlerts()`

### E2. Domain events

This is event-heavy architecture by nature.

**Critical domain events:**
```
HoldingsSynced
NAVUpdated
EligibilityComputed
LoanOfferGenerated
OfferAccepted
AgreementSigned
PledgeRequested
PledgeConfirmed
LoanCreated
DisbursementCompleted
MarginShortfallDetected
TopUpCollateralAdded
LiquidationTriggered
LiquidationCompleted
LoanClosed
```

**Why events matter** — because many systems react to them: notifications, audit, CRM, collections, analytics, risk dashboards, reconciliation.

---

## F. Resilience & consistency

### F1. Failure scenarios to hunt for

An architect should actively hunt breakpoints, not wait for them to surface in production.

1. **Stale holdings shown to the customer.** Holdings shown in the UI are stale, but the pledge request uses old units. The customer now sees more drawing power than is actually possible.

2. **Pledge confirmed externally, but internal state remains pending.** Now the loan is wrongly blocked even though the collateral is actually locked.

3. **Loan disbursed before pledge confirmation due to a race condition.** This is a major control failure — money leaves before collateral is genuinely secured.

4. **NAV crashes sharply, but the margin job runs late.** Risk remains unaddressed for the gap between the crash and the next risk-engine run.

5. **Customer repays fully, but lien release is delayed.** A terrible customer experience — the debt is gone, but the asset is still legally locked.

### F2. Consistency model

A brilliant interview question: what should be strongly consistent vs eventually consistent?

| Consistency level | Applies to |
|---|---|
| **Strong** | Pledge confirmation before activation, loan disbursal control, outstanding balance, locked collateral units, repayment posting |
| **Eventual** | Dashboards, reporting, notifications, analytics, recommendation widgets, historical aggregation |

### F3. Data stores

A practical, separated data-store design:

| Store type | Used for |
|---|---|
| **OLTP relational DB** | Applications, journey states, loan accounts, collateral ledger, repayment ledger, audit references |
| **Cache** | Latest NAV lookup, eligibility rules snapshot, active offer summary |
| **Event bus** | Callbacks, risk triggers, notifications, reconciliation workflows |
| **Search / analytics store** | Ops dashboard, customer support search, portfolio risk monitoring |

---

## G. Mastery layer

### G1. Architect-level talking points

The six points that make a design discussion sound architect-level rather than developer-level:

1. **"Collateral is not money, it is units."**
   The system must preserve unit-level traceability.

2. **"Offer generation and pledge confirmation should be separated."**
   Displayed eligibility is preliminary; enforceable eligibility only comes after a successful pledge.

3. **"This must be state-machine driven."**
   External partner calls make the journey long-running and failure-prone.

4. **"Risk monitoring is a first-class subsystem."** Not a support job bolted on afterward.

5. **"Collateral ledger must be separate from loan ledger."**
   Pledged-asset lifecycle and loan lifecycle are related but not identical.

6. **"Policy engine should control eligibility, LTV, and liquidation thresholds."**
   Because these business rules change often — code deploys shouldn't gate them.

### G2. Deep-mastery questions

**Product / business side**
- Why would a customer choose Loan Against MF instead of redeeming units?
- Which customer segments are most suitable for this product?
- Which schemes create high operational risk but low revenue value?
- How do we avoid giving a loan against volatile assets at the wrong time?
- Should the customer see only approved holdings, or all holdings with reasons for ineligibility?

**Risk side**
- Should LTV depend only on scheme type, or also on the customer's credit profile?
- Should we use one uniform margin rule, or dynamic risk buckets?
- What happens if NAV is stale for two days?
- Can we continue drawdown when the warning threshold is breached?
- Should liquidation be rule-based, or maker-checker approved?

**Operations side**
- How will the support team see where a journey is stuck?
- How will we replay failed callback-driven steps safely?
- What is the reconciliation process with the RTA / pledge partner?
- How will we release the lien safely after full repayment?
- Which SLAs matter most: offer generation, pledge marking, disbursal, or lien release?

**Architecture side**
- Which parts must be synchronous for UX, and which must be async for resilience?
- What idempotency keys will exist across loan app, pledge request, disbursement, and callbacks?
- Where do we need transactional guarantees, and where is eventual consistency acceptable?
- How will you design auditability for a regulator, dispute, or ops inquiry?
- What domain events are contract-worthy and stable enough for other systems to consume?

### G3. Interview-ready answer

A clean way to present this whole design verbally:

> "I would design Loan Against Mutual Fund as a collateralized lending platform with five core capabilities: holdings discovery, eligibility and valuation, pledge orchestration, loan servicing, and continuous risk monitoring. The key architectural principle is that mutual fund units are the true collateral, so I would maintain a separate collateral ledger and a state-machine-driven journey. Because external pledge partners and valuation feeds are involved, I would keep customer-facing eligibility synchronous where possible, but move pledge confirmation, callbacks, reconciliation, and margin workflows into asynchronous orchestration. The hardest part is not disbursal — it is ongoing collateral risk management and safe liquidation."

### G4. Ultra-short summary

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

**The deepest architect insight:** don't design it as "loan journey only." Design it as **collateral lifecycle + loan lifecycle + risk lifecycle.**

---

*Notes derived from a full system-design walkthrough of Loan Against Mutual Fund — covering business framing, architecture, journey/state modeling, the eight hardest subsystems, interfaces, resilience, and interview-grade talking points.*
