---
tags: [leadership, cto, strategy, finance, iim]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/CTONotebook/iim_cto_course]
---

# CTO Playbook — IIM Course Notes

IIM executive program on the CTO role. Three modules covering archetypes, strategy, and financial fluency.

## Module 1 — CTO Archetypes

Four types of CTO:

1. **Infrastructure CTO**: focused on reliability, scalability, operational excellence. Keeps the lights on.
2. **Product CTO**: deeply embedded in product roadmap, close to customers, translates technical capability into features.
3. **Innovator CTO**: bets on emerging tech, builds internal R&D culture, often more comfortable with ambiguity.
4. **Business CTO**: commercial orientation, manages vendor relationships, translates tech to business value for the board.

Most real CTOs are hybrids. The IIM framing helps identify which archetype a specific situation demands — and which gaps to watch.

## Module 2 — Strategic Frameworks

**VRIO Analysis**: Value, Rarity, Imitability, Organization. For any technical capability or initiative, ask: does it create value? Is it rare? Is it hard to imitate? Is the org set up to capture it?

Applied to idfc-coder: Value (yes, $4.28M saved), Rarity (few banks have self-hosted LLM infra at this scale), Imitability (hard — model selection expertise + VPC infra + governance are compound moats), Organization (yes, engineering org now has the capability).

**Classify, Govern, Transform**: framework for technology portfolio decisions. Classify assets by strategic importance. Govern the important ones tightly. Transform the ones that are becoming liabilities.

## Module 3 — Financial Fluency for CTOs

**CAPEX vs. OPEX**: Capital expenditure (one-time, depreciated) vs. operating expenditure (recurring). Cloud computing converts CAPEX to OPEX — this affects how finance teams think about tech spend. CTOs who understand this can negotiate with the CFO.

**Working Capital**: current assets minus current liabilities. Tech investments that compress the cash conversion cycle (faster billing, faster settlement) directly improve working capital.

**Capital Budgeting**: NPV, IRR, payback period. The language for justifying large tech investments. Every AI initiative needs a financial case — idfc-coder's $4.28M / 6-month payback is an IRR-positive case.

**CFO-CTO Playbook**: how to translate "we need to build X" into financial language. Frame every investment as: cost, risk reduction, or revenue enablement. Quantify the optionality.

## idfc-coder as a CTO Case Study

`projects/architect-kit/learning/CTONotebook/projects/idfc-coder-cto-scenario-qa.html` contains a Q&A simulation of presenting the idfc-coder initiative to a board. Useful interview prep and real-world application of the module frameworks.

## Related

- [[learning/leadership/index]] — Domain entry point
- [[learning/business-strategy/index]] — Overlaps with strategy modules
- [[projects/architect-kit/status]] — Where these notes live
