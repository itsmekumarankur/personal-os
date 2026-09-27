# Past Projects — Interview Prep Notes

> Three real-world ML systems: IDFC PFM categorization, PayPal fraud detection, PayPal risk scoring. Each demonstrates a different class of ML problem — categorize, detect, predict — all tied together by MLOps discipline.

---

## Project 1 — IDFC PFM: Transaction Categorization + Spend Insights

### 1. The Problem

A customer makes `₹2,500 paid to Swiggy`. The banking system initially only knows:
```
Merchant = Swiggy
Amount   = ₹2,500
Date     = 10-Sep
```

**PFM (Personal Financial Management)** wants to convert that into:
```
Category    = Food
Subcategory = Food Delivery
```

Then it can generate insights:
```
Monthly Food Spend = ₹8,500
Monthly Shopping   = ₹12,000
Monthly Travel     = ₹5,000
```
The ML model performs the categorization.

### 2. Architecture

```
                    CUSTOMER TRANSACTION
                            |
                            v
                  +--------------------+
                  | Transaction System |
                  | / Payment System   |
                  +---------+----------+
                            |
                            v
                    +---------------+
                    | Kafka / Event |
                    |     Bus       |
                    +-------+-------+
                            |
                            v
                +---------------------+
                | Feature Engineering |
                |     Pipeline        |
                +----------+----------+
                           |
                           v
                 +--------------------+
                 | Transaction        |
                 | Categorization ML  |
                 | Model              |
                 +---------+----------+
                           |
                 +---------+---------+
                 v                   v
        +----------------+   +----------------+
        | Category       |   | Confidence     |
        | Food           |   | 0.94           |
        +-------+--------+   +----------------+
                |
                v
        +--------------------+
        | PFM Transaction DB |
        +---------+----------+
                  |
                  v
        +--------------------+
        | Spend Analytics    |
        | / Insights Engine  |
        +---------+----------+
                  |
                  v
        +--------------------+
        | Mobile / Web App   |
        +--------------------+


              MLOps CONTROL PLANE
              -------------------

       Training Data
             |
             v
     +---------------+
     | Model Training|
     +-------+-------+
             |
             v
     +---------------+
     | Model Registry|
     | v1 / v2 / v3  |
     +-------+-------+
             |
             v
     +---------------+
     | CI/CD         |
     +-------+-------+
             |
             v
     Production Model

             ^
             |
     +-------+---------+
     | Model Monitoring|
     +-------+---------+
             |
       Accuracy / Drift
             |
       Drift detected?
             |
            YES
             |
             v
       Retraining Job
             |
             +------------> Model Registry
```

### 3. How It Works

**Step 1 — Transaction arrives.** Example: `Customer → ₹1,200 → Amazon`. The event goes into Kafka. Why Kafka? Because you don't want the transaction processing system to wait for ML processing.

**Step 2 — Feature generation.**
```
merchant       = Amazon
amount         = 1200
transaction_type = UPI
time           = 20:30
historical_merchant_category = Shopping
customer_history = Shopping
```

**Step 3 — ML prediction.** Model returns:
```
Category   = Shopping
Confidence = 96%
```
API:
```
POST /categorize
{ "merchant": "Amazon", "amount": 1200, "payment_type": "UPI" }

Response:
{ "category": "Shopping", "confidence": 0.96 }
```

**Step 4 — Store result.**
```
Transaction
     +--> Category
     +--> Subcategory
     +--> Confidence
```
Stored in PFM data store.

**Step 5 — Spend insights.** Analytics layer calculates:
```
Food       ₹8,500
Shopping   ₹12,000
Travel     ₹5,000
Bills      ₹15,000
```
Application shows: *"Your shopping expenditure increased 25% this month."*

### 4. The Important MLOps Part

The model is **not**: `Train once → Deploy → Done`.

```
Training → Model v1 → Production → Monitoring
                                        |
                              +---------+---------+
                              |         |         |
                          Accuracy↓  Data Drift  Prediction Drift
                              |         |         |
                              +---------+---------+
                                        v
                                   Retraining → Model v2
```

**Model Registry** = GitHub for ML models.
```
Model Registry: transaction-model
   +-- v1.0
   +-- v1.1
   +-- v2.0
   +-- v2.1
```
You know exactly which model is running in production.

### 5. What Is Drift?

Model trained in 2024 with merchants: UPI, Amazon, Flipkart, Swiggy, Zomato. In 2026, new merchants appear — QuickCommerce, digital subscriptions, new UPI merchants. The distribution changes.
```
Old data:  Amazon 20%, Flipkart 15%, Swiggy 10%
New data:  QuickCommerce merchants, Digital subscriptions, New UPI merchants
```
The model starts becoming less accurate. That's **model/data drift**.

### 6. Retraining

Monitoring detects: `Accuracy < threshold` or `Data distribution changed significantly`.
```
             Drift
               |
               v
       Retraining Pipeline → Training Dataset → Train Model → Evaluate Model
                                                              |
                                                    Accuracy > threshold?
                                                       /       \
                                                     NO         YES
                                                     |           |
                                                  Reject       Register → Deploy
```

### 7. What You Can Say in an Interview

Don't say: *"I built the complete ML platform."*

Instead:
> **"I was involved in introducing the early MLOps practices around the PFM transaction-categorization models. The key idea was to move from a static model deployment approach toward a lifecycle where model versions were tracked, production performance was monitored, and degradation or drift could trigger retraining."**

Then explain:
> **"The transaction flow itself was event-driven. Transactions were consumed, features were generated, the categorization model predicted the category, and the result was persisted for the PFM insights layer."**

That's credible and technically strong.

---

## Project 2 — PayPal: Fraud Detection Framework

### 8. The Problem

The objective isn't *"What category is this transaction?"* It is: **"Is this transaction suspicious?"**

Example:
```
Customer normally:  India, ₹500–₹5,000, UPI, Normal hours
Suddenly:           US, ₹2,50,000, New merchant, 3:00 AM, New device
```
The fraud engine should flag it.

### 9. Architecture

```
                  PAYMENT REQUEST
                        |
                        v
              +-------------------+
              | Payment Gateway   |
              +---------+---------+
                        |
                        v
              +-------------------+
              | Fraud Detection   |
              | Engine            |
              +---------+---------+
                        |
             +----------+----------+
             v                     v
       +-----------+         +-------------+
       | Real-time |         | Customer /  |
       | Features  |         | Transaction |
       +-----+-----+         | History     |
             |               +------+------+
             +----------+-----------+
                        |
                        v
              +-------------------+
              | Rule Engine       |
              +---------+---------+
                        |
                        v
             +--------------------+
             | Risk Decision      |
             +--------------------+
               /       |        \
              v        v         v
          APPROVE    REVIEW      DECLINE
             |         |          |
             v         v          v
          Payment   Fraud Ops   Block
```

### 10. Example

Transaction: `Amount = $4,000, Country = US, Device = New, Merchant = New, Customer = India, Time = 3 AM`

Rules:
```
Rule 1: New device + high amount        → suspicious
Rule 2: New country + high amount       → suspicious
Rule 3: Multiple transactions within 1 minute → suspicious
```

Each rule produces a signal:
```
Rule 1 → +30
Rule 2 → +25
Rule 3 → +40
Total  = 95
```
Score bands:
```
0 - 30   → LOW
31 - 70  → MEDIUM
71 - 100 → HIGH
```
Decision: `HIGH → Manual Review / Decline`

### 11. Why Rules Instead of ML?

Rules provide **explainability**. You can say: *"Transaction was flagged because it came from a new device and unusual geography."* ML might simply say: `Fraud probability = 0.92`.

Rules are useful for:
- Regulatory requirements
- Explainability
- Immediate policy changes
- Deterministic controls
- Known fraud patterns

Usually real systems use **rules + ML**, not only one.

### 12. Global Payment Flow

```
                Global Transactions
        +---------------+---------------+
        v               v               v
      US Region       EU Region       APAC
        +---------------+---------------+
                        v
                Fraud Platform
             +----------+----------+
             v                     v
        Rule Engine          Risk Models
             +----------+----------+
                        v
                  Risk Decision
```

Key architectural concepts: low latency, high availability, regional processing, idempotency, fault tolerance, auditability.

Fraud detection cannot take 5 seconds if you're trying to authorize a payment synchronously.

### 13. What You Can Say

> **"My contribution was around the fraud-detection framework, particularly the data models and rule-based detection layer. The architecture evaluated transaction and customer signals in real time, applied configurable fraud rules, generated risk indicators, and routed suspicious transactions for review."**

If asked *"Did you build the ML model?"*:
> **"No, my involvement was more on the platform and detection-framework side rather than developing the underlying ML algorithms."**

That is a much safer answer.

---

## Project 3 — PayPal: Transaction Risk Scoring MLOps

### 14. The Problem

Here the ML model produces a risk score:
```
0.01 → Very Low Risk
0.35 → Medium Risk
0.92 → Very High Risk
```

### 15. Architecture

```
                   TRANSACTION
                        |
                        v
              +-------------------+
              | Event / Streaming |
              | Platform          |
              +---------+---------+
                        |
                        v
              +-------------------+
              | Feature Pipeline  |
              +---------+---------+
                        |
             +----------+----------+
             v                     v
      Transaction Features   Historical Features
             +----------+----------+
                        |
                        v
              +-------------------+
              | Risk Scoring Model|
              | Model v12         |
              +---------+---------+
                        |
                        v
                 Risk Score 0.87
                        |
                        v
              +-------------------+
              | Fraud Decision    |
              | Engine            |
              +---------+---------+
                 +------+------+
                 v             v
             APPROVE        REVIEW


                 MLOps
                 -----
 Training Data → Feature Pipeline → Model Training → Model Evaluation
 → Model Registry → Deployment → Production → Monitoring
      |
      +---- Performance degradation
      +---- Feature drift
      +---- Prediction drift
      |
      v
 Retraining
```

### 16. What Is Feature Pipeline Automation?

Model requires:
```
transaction_amount, customer_age, merchant_history, device_history,
transaction_frequency, country, previous_fraud_count
```
You don't want developers manually preparing this daily. Instead:
```
Raw Transactions → Feature Pipeline → Cleaning → Transformation
→ Aggregation → Validation → ML Features
```

Example — Raw:
```
Customer A: 10 transactions, ₹5,000 each
```
Pipeline calculates:
```
transactions_last_24h = 10
amount_last_24h       = ₹50,000
average_amount        = ₹5,000
```
These become ML features.

### 17. Production Monitoring

You don't just monitor `CPU, Memory, Latency`. You also monitor **model health**.
```
Model Performance:
  Precision          94%
  Recall             91%
  False Positive      6%
  Prediction Latency 45ms

Feature Drift:
  amount             NORMAL
  device_type        NORMAL
  country            DRIFT
  merchant_category  DRIFT
```

### 18. Why Model Degradation Matters

```
January:        Precision = 95%, Recall = 92%
Six months later: Precision = 82%, Recall = 76%
```
Something changed. Possible reasons:
```
New fraud pattern
New merchants
New payment methods
Customer behavior changed
Feature distribution changed
```
Therefore:
```
Monitoring → Detect degradation → Investigate → Retrain → Evaluate → Deploy
```

---

## Cross-Project Summary

### 19. The 3 Architectures Together

```
                 ML SYSTEM
        +-----------+-----------+
        v           v           v
     IDFC         PayPal       PayPal
     PFM          Fraud        Risk Score
        |           |           |
        v           v           v
   Categorize    Detect       Predict
   transaction   fraud        risk
        |           |           |
        v           v           v
   Food/Travel   Rules + ML   Risk Score
        +-----------+-----------+
                    v
                  MLOps
        +-----------+-----------+
        v           v           v
   Versioning   Monitoring   Retraining
```

### 20. The MLOps Lifecycle You Should Memorize

This is the **single most important diagram** for your interviews.

```
                 +----------------+
                 | Training Data  |
                 +-------+--------+
                         |
                         v
                 +----------------+
                 | Feature        |
                 | Engineering    |
                 +-------+--------+
                         |
                         v
                 +----------------+
                 | Model Training |
                 +-------+--------+
                         |
                         v
                 +----------------+
                 | Model          |
                 | Evaluation     |
                 +-------+--------+
                         |
                  Good Model?
                    /     \
                  NO       YES
                  |         |
                Reject      v
                       +----------+
                       | Registry |
                       +----+-----+
                            |
                            v
                       Deployment
                            |
                            v
                       Production
                            |
                            v
                     Monitoring
                       /    \
                      /      \
                Healthy      Drift
                   |           |
                   |           v
                   |       Retraining
                   |           |
                   +-----------+
```

**Remember this sentence:**
> **"MLOps is basically applying software engineering discipline to the complete ML lifecycle — data, features, training, model versioning, deployment, monitoring and retraining."**

---

## Key Takeaways Across All 3 Projects

1. **Three ML problem classes:** Categorize (IDFC PFM) · Detect (PayPal Fraud) · Predict (PayPal Risk Score)
2. **Event-driven architecture:** Kafka decouples transaction processing from ML inference
3. **Rules + ML together** — rules for explainability and regulatory compliance; ML for pattern detection
4. **MLOps is not optional** — Model Registry, Monitoring, Drift Detection, Retraining loop
5. **Drift is inevitable** — data distribution changes; accuracy degrades silently without monitoring
6. **Monitor model health, not just infrastructure** — Precision, Recall, Feature Drift
7. **Feature pipelines automate** cleaning → transformation → aggregation → validation
8. **Model Registry = GitHub for models** — know exactly which version is in production
9. **Interview honesty matters** — distinguish "I built the ML model" from "I built the platform around it"
10. **MLOps lifecycle = the master diagram** — data → features → training → evaluation → registry → deployment → monitoring → retraining
