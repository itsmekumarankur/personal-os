# Loan Management System (LMS) – Backend (LAMF)

This repository contains the **backend implementation** of a **Loan Management System (LMS)** for an **NBFC** operating exclusively in **Loan Against Mutual Funds (LAMF)**.

The system models the **end-to-end lifecycle of a loan**, including loan product configuration, loan application submission and eligibility validation, loan approval, collateral pledging, and ongoing loan health monitoring based on Mutual Fund NAV changes.

This project was built with a focus on **domain understanding, correctness, API design, and clear engineering tradeoffs**.

## Quick Summary
The system models **real-world lending workflows** including:
- Loan product configuration with LTV-based risk rules
- Loan application submission and eligibility validation
- Loan approval and disbursement
- Collateral (Mutual Fund units) pledging
- Ongoing loan health monitoring based on NAV changes

The focus of this implementation is on **correct domain modeling, clean APIs, strong data consistency, and clear engineering tradeoffs**.

This repository represents the **core backend engine** of the LMS and is intended to be consumed by:
- An internal admin dashboard
- External fintech / B2B partners via APIs

---

## Functional Scope

### 1. Loan Products
- Admin can create loan products
- Configure:
  - Interest Rate (APR)
  - Max LTV
  - Margin Call LTV
  - Liquidation LTV
  - Allowed Mutual Fund categories
- Activate / deactivate loan products

---

### 2. Loan Applications
- Persist all loan applications with lifecycle states:
  - CREATED
  - VALIDATED
  - APPROVED
  - REJECTED
- View all applications and application details

Loan applications represent **requests**, not disbursed loans.

---

### 3. Create New Loan Application (API-Critical)
- Public API exposed for **fintech / B2B partners**
- Automatically performs:
  - Input validation
  - Eligibility validation using LTV logic

This is the **only non-admin API**.

---

### 4. Loan Approval & Disbursement
- Admin approves VALIDATED applications
- Approval results in:
  - Loan creation
  - Collateral pledging
  - Application status update
- Loan amount is assumed to be **disbursed instantly**

---

### 5. Collateral Management
- Mutual Fund units are pledged as collateral
- NAV is mocked
- Collateral value and loan health are recalculated on NAV updates
- Liquidation is represented as a **loan state change only**

---

## Core Business Flow

- Loan Application Submitted
- ↓
- Input Validation (fail-fast)
- ↓
- Eligibility Validation (LTV-based)
- ↓
- VALIDATED or REJECTED
- ↓
- (Admin Approval)
- ↓
- Loan Created + Collateral Pledged
- ↓
- Ongoing Loan Health Monitoring (NAV-based)


---

## Validation Logic

### Input Validation (Fail Fast)
- Mutual Fund units must be positive
- Mutual Fund units must not already be pledged
- Loan product must exist and be ACTIVE

Invalid input results in **request failure** and **no data persistence**.

---

### Eligibility Validation (Business Rule)
- NAV is fetched (mocked)
- Collateral value = Σ(units × NAV)
- Eligible amount = collateral value × max LTV

- If:
  requestedAmount > eligibleAmount

→ Application is **REJECTED** (persisted for audit)

- Otherwise:
→ Application is **VALIDATED**

---

### Loan Approval
- Only VALIDATED applications can be approved
- Approval creates:
  - Loan record
  - Collateral records
- Loan starts in **ACTIVE** state

---

### Loan Health Monitoring
- NAV updates trigger recalculation of collateral value
- Loan LTV is recalculated as: LTV = outstandingAmount / totalCollateralValue

  
| Condition | Loan Status |
|---------|-------------|
| LTV ≤ maxLTV | ACTIVE |
| maxLTV < LTV ≤ marginCallLTV | MARGIN_CALL |
| LTV > liquidationLTV | LIQUIDATION_TRIGGERED |

Liquidation is simulated via state change only.

---

## Key Assumptions & Design Decisions

### Interest Rate
- Stored as **Annual Percentage Rate (APR)**
- Interest accrual and repayments are **out of scope**
- Outstanding amount equals principal at loan creation

---

### Authentication & Authorization
- JWT / authentication is intentionally not implemented
- APIs are structured (`/api/admin/**`) to support RBAC later

---

### Single-Tenant Assumption
- System models a **single NBFC**
- Multiple fintech partners can call APIs
- No multi-tenant isolation (`company_id`) implemented

---

### Mocked External Dependencies
- NAV values are mocked
- MF ownership verification is assumed
- Liquidation is simulated

---

## API Overview (Important Endpoints)

### Partner / Client API
- POST /api/loan-applications: Creates and validates a loan application.

---

### Admin APIs
- POST /api/admin/loan-products
- GET /api/admin/loan-products
- PATCH /api/admin/loan-products/{id}/status

- GET /api/admin/loan-applications
- GET /api/admin/loan-applications/{id}
- POST /api/admin/loan-applications/{id}/approve

- POST /api/admin/loans/{loanId}/nav

  ---

## Database Schema

The system uses **PostgreSQL** with a strongly consistent relational model.

### Tables

#### loan_products
- id (UUID, PK)
- name (unique)
- interest_rate
- max_ltv
- margin_call_ltv
- liquidation_ltv
- status
- created_at
- updated_at

**Indexes**
- `(status, updated_at DESC)` for efficient admin listing

---

#### loan_applications
- id (UUID, PK)
- customer_id
- loan_product_id
- requested_amount
- eligible_amount
- status
- created_at
- updated_at

---

#### loan_application_mf
- id (UUID, PK)
- application_id (FK)
- isin
- units

---

#### loans
- id (UUID, PK)
- application_id
- loan_product_id
- principal_amount
- interest_rate
- outstanding_amount
- status
- created_at

---

#### collaterals
- id (UUID, PK)
- loan_id
- isin
- units
- nav
- collateral_value
- status

---

## Why PostgreSQL (SQL over NoSQL)

- Strong relationships between entities
- Financial correctness requires **strong consistency**
- Referential integrity is critical
- Eventual consistency is not acceptable for loan data

---

## Non-Functional Considerations (Future Scope)

Although not implemented, the following were considered:

### Caching (Redis)
- Cache loan products (read-heavy)
- Idempotency for partner APIs

### Async Processing (Kafka / Queue)
- NAV ingestion events
- Margin call notifications
- Liquidation workflows

### Microservices
- Loan Service
- Collateral Service
- Risk Engine

Current implementation is a **modular monolith** for simplicity.

---

## Setup Instructions (Local)

### Prerequisites
- Java 17+
- Maven
- Docker & Docker Compose

---

### Start PostgreSQL (Docker)

```bash
docker compose up -d

---
## Run Backend
- mvn clean install
- mvn spring-boot:run

---

## Demo & Deployment

- Backend and database are demonstrated via local setup

- Full end-to-end functionality is shown in the demo video

- Demo Video: https://dummy-demo-link

```Due to infrastructure constraints, backend and database are not deployed to cloud services.```

---
## Testing

- Automated test cases were not implemented due to time constraints.

- Manually validated scenarios include:

- Invalid MF units

- LTV breach rejection

- Duplicate approval prevention

- NAV-driven loan health changes

- Transaction rollback on failure


