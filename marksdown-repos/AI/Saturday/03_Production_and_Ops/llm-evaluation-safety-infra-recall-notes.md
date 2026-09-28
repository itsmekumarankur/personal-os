# LLM Evaluation, Safety & AI Infrastructure — Architect Recall Notes


Your team launches an AI assistant for customers.

It works well in testing, so the business says:

> **“Let's take it to production.”**

A month later, a customer gets a **confident but incorrect answer**. Another request exposes sensitive information. Meanwhile, nobody can clearly explain why some answers are failing or how much each request costs.

As the Engineering Manager, you realize:

> **AI cannot be managed like a normal API.**

You need **evaluation to know whether it's actually working, safety controls to limit what it can do, and observability to understand failures, cost and latency.** Your notes frame production AI as a continuous loop of evaluation, safety, observability and improvement. ([github.com][1])

### Why I am reading this

**Because an AI system isn't production-ready just because the model works; as a leader, I need to know how we measure, secure and operate it safely at scale.**

### Leadership question

> **“How do we know this AI is safe and good enough for our business—not just technically working?”**

### One-line takeaway

> **For AI, production readiness means proving it works, controlling its risks, and continuously measuring it.**


> **Study rule:** Don't read the answer first. Read: **QUESTION → THINK → DRAW → ANSWER → RECALL**

---

## 0. THE BIG PICTURE

```
                         USER
                           |
                           v
                  +----------------+
                  | INPUT SAFETY   |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  |    ROUTER      |
                  +-------+--------+
                          |
             +------------+------------+
             v                         v
          SMALL LLM                LARGE LLM
             +------------+------------+
                          |
                          v
                     RAG / TOOLS
                          |
                          v
                     GENERATION
                          |
                          v
                  +----------------+
                  | OUTPUT SAFETY  |
                  +-------+--------+
                          |
                          v
                        USER

             Meanwhile...
        +-----------+-----------+
        v           v           v
     METRICS      TRACES      EVALS
        +-----------+-----------+
                    v
              CONTINUOUS IMPROVEMENT
```

**Beginner:** `USER → LLM → ANSWER`
**Architect:** `USER → Safety → Routing → Retrieval → Tools → LLM → Validation → Observability → Evaluation → Answer`

---

# PART 1 — 🧪 LLM EVALUATION & SAFETY

## 10.1 Why Is LLM Evaluation Hard?

```
Traditional Software:           LLM:
INPUT → FUNCTION → OUTPUT       INPUT → LLM → Answer A / Answer B / Answer C
Same input = Same output        Different valid answers exist
assert(actual == expected)      Cannot use exact equality
```

**THE THREE EVALUATION LAYERS:**
```
                 EVALUATION
       +-------------+-------------+
       v             v             v
  BENCHMARKS     LLM-AS-JUDGE    HUMANS
   Cheap/Fast      Scalable       Gold signal
   Generic         Flexible       Expensive
```

---

## 10.2 Benchmarks

```
PUBLIC BENCHMARK   → "What can this model generally do?"
YOUR EVAL SET      → "What can this model do for MY application?"
```

| Benchmark | Main purpose |
|---|---|
| MMLU | Broad knowledge |
| GSM8K | Mathematical reasoning |
| MATH | Advanced mathematics |
| HumanEval | Code generation |
| MBPP | Code generation |
| HellaSwag | Commonsense reasoning |
| TruthfulQA | Truthfulness |
| MT-Bench | Conversational/instruction quality |

**Why benchmarks mislead:** Contamination · Task mismatch · Saturation · Static snapshot

**Build your own eval set** (even 50–100 examples):
```
Internal Wealth Assistant Eval Dataset
   +--------------+--------------+
   v              v              v
Easy cases    Normal cases    Edge cases
 30 cases       40 cases       30 cases
```
Don't only test the happy path.

---

## 10.3 LLM-as-Judge

```
100,000 answers → LLM JUDGE → Scores / comparisons
```

**Four judge modes:**
```
1. Pointwise:      Answer → Judge → Score = 4/5
2. Pairwise:       Question → Answer A / Answer B → Judge → A / B / TIE
3. Reference-based: Generated + Expected → Judge → Alignment?
4. Rubric-based:   Correct? Grounded? Safe? → SCORE
```

**Pairwise is powerful** because relative judgment is easier to calibrate than absolute scores.

**LLM JUDGE BIASES:** Position bias · Verbosity bias · Self-preference bias · Style-over-substance

```
Answer A: "Correct answer."
Answer B: "Here is a beautifully structured, detailed, confident 800-word explanation..."
Weak judge prefers B. Even if A = factually correct, B = beautifully wrong.
```

**GOLDEN RULE:** Never assume your LLM judge is ground truth. Calibrate it:
```
HUMAN GOLD SET → LLM JUDGE → Compare with humans → Judge agreement
```

---

## 10.4 Human Evaluation

**Humans detect:** Subtle domain errors · Cultural problems · Novel failures · Real user satisfaction

**HUMAN EVAL DESIGN:**
```
Bad:    "Rate answer from 1–5."
Better: HUMAN REVIEW → Correct? Grounded? Safe? → Score
```

**INTER-RATER RELIABILITY:** If two reviewers disagree constantly, it could mean:
```
Ambiguous rubric → Reviewer A interpretation 1, Reviewer B interpretation 2 → Low agreement
```
> Low agreement can indicate a poorly defined evaluation rubric. (Cohen's Kappa measures agreement.)

**STRATEGIC HUMAN SAMPLING:**
```
PRODUCTION → Low confidence / Complaints / Edge cases → HUMAN REVIEW
```

---

## 10.5 Hallucination

```
WRONG + CONFIDENT + FLUENT = DANGEROUS
```

**Intrinsic hallucination** — contradicts provided source → **faithfulness failure**
```
SOURCE: "Exit load = 1%"   MODEL: "Exit load = 2%"
```

**Extrinsic hallucination** — claim not supported by source
```
SOURCE: "Exit load is applicable."   MODEL: "Exit load is exactly 1%."
```

**HALLUCINATION DETECTION:**
```
                  ANSWER
       +-------------+-------------+
       v             v             v
 Self-consistency    NLI       Citation check
 Multiple outputs   Entailment  Source exists?
       +-------------+-------------+
                     v
              RISK SIGNAL
```

**Self-consistency:** Ask same question N times; agreement is a signal.
```
A → 1%, A → 1%, A → 1%, A → 1.5%, A → 1%  →  4/5 agree; outlier deserves investigation
```
⚠️ Consistency is a **signal**, not proof of truth. A model can consistently repeat the same wrong answer.

**NLI / Entailment (for RAG):** Does the retrieved context entail the generated answer?
```
Context: "Exit load is 1%."  Generated: "Exit load is 1%."  → ENTAILED ✓
Context: "Exit load is 1%."  Generated: "Exit load is 3%."  → NOT ENTAILED ✗
```

**Citation verification:** Never trust "According to Policy.pdf..." just because a citation exists. Verify the source actually supports the claim.

---

## 10.6 Hallucination Mitigation

```
                HALLUCINATION
       +--------------+--------------+
       v              v              v
   Grounding       Prompting       Verification
      RAG        "Don't guess"     Second pass
       +--------------+--------------+
                      v
               Lower risk
```

**THE LAYERED DEFENSE:**
```
USER → RETRIEVAL → GENERATION → VERIFICATION → FINAL RESPONSE
```

**MITIGATION TECHNIQUES:** RAG · Explicit abstention ("If information is unavailable, say 'I don't know'") · Citations · Lower temperature · Structured output · Verification pass · Fine-tuning for abstention

**Architect insight:** The practical goal is **REDUCE + DETECT + CONTAIN + RECOVER**.

---

## 10.7 Guardrails

```
             UNTRUSTED PROCESSING ENGINE
INPUT ------>|          LLM          |------> OUTPUT
                        ^
                Safety layers outside model
```

**PRODUCTION GUARDRAIL ARCHITECTURE:**
```
USER → INPUT GUARDRAIL (PII, Injection, Scope, Rate limit)
     → LLM
     → OUTPUT GUARDRAIL (PII leakage, Toxicity, Fact check, Schema, Policy)
     → USER
```

**THREE TYPES:**
- **Input:** PII detection, Injection detection, Topic restriction, Rate limiting
- **Output:** PII leakage, Toxicity, Fact verification, Schema validation, Regulatory restrictions
- **Structural:** Untrusted RAG content, Tool permissions, Least privilege, Sandboxing

**🏦 FINTECH EXAMPLE:** *"Transfer ₹10 lakh from account A to account B."*
Never let LLM directly execute. Instead:
```
LLM → Intent extraction → Structured command → AUTHORIZATION SERVICE
    → POLICY ENGINE → TRANSACTION SERVICE → AUDIT LOG
```
The LLM should not become the authorization boundary.

---

## 10.8 Red Teaming

```
NORMAL QA:              RED TEAM:
Expected input          ATTACKER → Jailbreak / Injection / Data extraction
  → Expected output         / Goal hijacking / Multi-turn manipulation
                          → SYSTEM FAILURE?
```

**ATTACK CATEGORIES:**
- **Jailbreaking** — bypass safety
- **Prompt injection** — malicious instructions inside documents, websites, RAG results, tool responses
- **Data extraction** — retrieve system prompts, secrets, other users' info
- **Goal hijacking** (especially for agents) — user request → agent → Tool A ✓ / Tool B ✓ / Dangerous Tool ✗
- **Multi-turn erosion** — attack happens gradually across turns

**MANUAL vs AUTOMATED:**
```
HUMAN: Creative attacks, Novel patterns, Expensive
AI:    Massive scale, Regression, Fast
```
Tools mentioned: PyRIT, garak

**IMPORTANT:** Red teaming isn't one security test → done. It's every model/prompt/tool/RAG update → red team → regression testing.

---

## 10.9 Alignment

**BASE MODEL:** Internet-scale data → PRETRAINING → "Predict next token" → capability (≠ alignment)

**ALIGNMENT PIPELINE:**
```
BASE MODEL → SFT (learn examples) → Preference Optimization → RLHF / DPO / RLAIF → ALIGNED ASSISTANT
```

- **SFT:** Instruction → Good response
- **RLHF:** Human comparison → Preference data → Reward model → Reinforcement learning → Better preferred behavior
- **DPO:** Preferred + Rejected response → Direct preference optimization (avoids separate reward-model/full-RL pipeline)
- **RLAIF:** AI → preference (lower cost, higher scale; depends on AI judgment)
- **Constitutional AI:** Written principles → Model critiques/revises → Training data → Better aligned behavior

**KEY ALIGNMENT RECALL:**
```
PRETRAINING             = "What can the model do?"
SFT                     = "How should it follow instructions?"
PREFERENCE OPTIMIZATION = "Which behaviors are preferred?"
GUARDRAILS              = "What is allowed in this application?"
RED TEAMING             = "How can we break it?"
EVALUATION              = "Is it actually working?"
```

---

# PART 2 — 🏗️ AI INFRASTRUCTURE & OPS

> Moving from: **"Is the AI good and safe?"** to: **"Can I run it reliably at production scale?"**

## 11.1 Why LLM Serving Is Different

```
Normal REST API:  Request → Service → Response (100–500ms)

LLM:  Request → Prefill → Token 1 → Token 2 → ... → Token N
```

**Autoregressive generation:**
```
"I" → "I am" → "I am an" → "I am an AI" → "I am an AI architect"
```

**THREE BIG DIFFERENCES:** Autoregressive generation · KV cache · Dynamic/continuous batching

**KV CACHE:** Previous tokens → K/V cache → reuse previous computation (avoid recompute)
```
Short request:  [========]
Long request:   [==============================]
Very long:      [================================================]
GPU MEMORY = Model weights + KV cache + Activations/runtime overhead
```

**WHY NAIVE BATCHING FAILS:**
```
A → DONE
B → ───────────────────────────────
C → DONE
GPU waits for B   ← Waste
```

**CONTINUOUS BATCHING:**
```
A → DONE → Request D enters
B → ───────────────────────────────
C → DONE → Request E enters
```
> Finished requests are continuously replaced by new requests.

---

## 11.2 Serving Engines

**Why not just Flask + PyTorch + GPU?** Because production serving needs: batching, memory management, parallelism, scheduling, streaming, GPU utilization.

**vLLM:** PagedAttention + Continuous batching + Efficient KV-cache management

**PagedAttention (OS mental model):**
```
Traditional:  Request → [Large contiguous KV memory]
Paged:        Request → Page 1 / Page 2 / Page 7 / Page 11
```
Think: Virtual memory → PagedAttention → KV cache pages

**TGI:** Hugging Face ecosystem → Model serving, Continuous batching, Quantization, Tensor parallelism

**Triton:** Broader — PyTorch / ONNX / TensorFlow → MODEL SERVING. For LLMs, paired with TensorRT-LLM.

**QUICK RECALL:**
```
vLLM   → LLM-focused serving → PagedAttention + continuous batching
TGI    → Hugging Face ecosystem
Triton → General multi-model serving
```

---

## 11.3 Cost & Latency Optimization

```
                 LLM COST
       +------------+------------+
       v            v            v
    Model        Tokens        Traffic
     cost          |             |
    GPU/API     Input/output   Requests
```

**LEVER 1 — QUANTIZATION:** FP16 → INT8 → INT4 (smaller weights, lower memory, potentially faster; possible quality loss)
Methods: **GPTQ** (post-training), **AWQ** (activation-aware), **GGUF** (llama.cpp format), **bitsandbytes** (8-bit/4-bit tooling)

**LEVER 2 — SPECULATIVE DECODING:**
```
SMALL MODEL → "The quick brown fox" → BIG MODEL → VERIFY → Accept/reject
```
If many guesses accepted → Generation speed ↑

**LEVER 3 — MODEL ROUTING:**
```
USER QUERY → ROUTER → SIMPLE → SMALL MODEL → CHEAP/FAST
                   → COMPLEX → LARGE MODEL → EXPENSIVE
```

**ARCHITECT INSIGHT:** Instead of "How do I make the expensive model cheaper?" ask **"How often do I actually need the expensive model?"**

**Other optimizations:** Batching (higher GPU utilization) · Streaming (better perceived latency) · Max output tokens · Stop sequences

---

## 11.4 Caching

```
Traditional cache: GET /customer/123 → HIT/MISS → Response/Database (exact key)

LLM queries: "What is the exit load?"
             "What penalty applies for early redemption?"
             "How much do I pay if I redeem early?"
             → Different strings, semantically similar
```

**SEMANTIC CACHE:**
```
USER QUERY → EMBEDDING → Similarity search
                       → Similar     → Cached answer
                       → Not similar → LLM call
```

**THREE CACHE TYPES:** Exact-match · Semantic · KV / Prefix reuse

**⚠️ DANGEROUS EXAMPLE:**
```
"What is interest rate for 1 year?"
"What is interest rate for 5 years?"
Semantic similarity ≠ Business equivalence
→ Need: Semantic cache + Entity/parameter validation + Threshold
```

**KV CACHE REUSE:** Shared system prompt → Compute once → Reuse KV state → Request A/B/C

---

## 11.5 Observability

```
Wrong answer → TRACE:
   Query rewrite ✓
   Embedding ✓
   Retrieval ✗      ← Found it
   Reranking ✓
   Prompt ✓
   Generation ✓
```

**LLM OBSERVABILITY additionally needs:** Prompt · Completion · Tokens · Cost · Model · Latency breakdown · Retrieval · Evaluation · User feedback

**COMPLETE TRACE:**
```
trace_id = ABC123
query rewrite       12ms ✓
embedding            45ms ✓
vector search        38ms ✓
reranking           180ms ✓
prompt assembly       3ms ✓
LLM generation      2.1s ✓
faithfulness check  340ms ⚠
```

**🔥 THE SIX THINGS TO OBSERVE:** 1. TRACE · 2. PROMPT/COMPLETION · 3. TOKENS/COST · 4. LATENCY · 5. QUALITY/EVAL · 6. USER FEEDBACK

**TOKEN + COST OBSERVABILITY:** Request → Input tokens / Output tokens / Model / Cost / User/tenant
Enables: Cost per request / per customer / per model / per feature

**LATENCY IS NOT ONE NUMBER:**
```
Traditional: Request → Response = 2 seconds
LLM: Retrieval 100ms + Reranking 200ms + TTFT 700ms + Generation 1500ms = TOTAL
```

**TTFT (Time To First Token):** Request → 700ms → First token → 1.5s → Complete answer
→ TTFT ≠ Total latency

**USER FEEDBACK:** 👍 👎 Regenerate Edit Correction Abandon — tie to `trace_id`

**LANGSMITH vs LANGFUSE:**
```
LangSmith: LangChain ecosystem, Strong tracing, Dataset/eval tooling, Prompt experimentation
Langfuse:  Open-source-first, Framework agnostic, Self-hosting, Cost/usage analytics
```

---

## 🧠 COMPLETE AI PRODUCTION LOOP

```
                         USER
                           |
                    INPUT GUARDRAIL
                           |
                       ROUTER
             +-------------+-------------+
             v                           v
         SMALL MODEL                LARGE MODEL
             +-------------+-------------+
                           v
                     RAG / TOOLS
                           v
                        LLM
                           v
                    OUTPUT GUARDRAIL
                           v
                         USER
                           v
                     FEEDBACK
                           v
                    OBSERVABILITY
             +-------------+-------------+
             v                           v
          METRICS                       EVAL
             +-------------+-------------+
                           v
                    IMPROVEMENT
                           v
                     NEW VERSION
```

---

# 🎯 Interview Prep, Recall & Final Mental Models

## 🚨 AI Architect's Failure-Mode Map

```
                     FAILURE
      +-----------------+------------------+
      v                 v                  v
   QUALITY            SAFETY             COST
Hallucination       Injection          Too many tokens
Bad retrieval       Jailbreak          Big model
Wrong answer        PII leak           No caching
Bad judge           Tool abuse         Poor batching
```

```
FAILURE → OBSERVE → DIAGNOSE → MITIGATE → EVALUATE → RED-TEAM → DEPLOY
```

---

## 🎯 Interview Recall — 16 Questions

**Q1 — LLM gives different answers for same question. Broken?**
No. Generation is stochastic. Evaluate **quality distributions and task-specific metrics**, not exact string equality.

**Q2 — Is MMLU enough to select your banking model?**
No. Use public benchmarks for broad comparison, then create a **domain-specific evaluation dataset**.

**Q3 — Why use LLM-as-judge?**
To evaluate large numbers of outputs automatically and consistently for regression testing. Calibrate against human labels.

**Q4 — Why can LLM-as-judge fail?**
Position bias · Verbosity bias · Self-preference · Style bias

**Q5 — What is hallucination?**
Unsupported/incorrect generated claim. **Intrinsic** (contradicts source / faithfulness failure) vs **Extrinsic** (not supported by source).

**Q6 — How to reduce hallucination?**
RAG + Abstention + Citations + Verification + Structured output + Appropriate decoding

**Q7 — Why guardrails if model is aligned?**
Alignment reduces risk but isn't a sufficient security boundary. Use independent input/output/structural controls.

**Q8 — What is prompt injection?**
Untrusted content manipulates the model into unintended instructions. Critical in RAG, Agents, Tool outputs, Web content, Uploaded documents.

**Q9 — Red teaming vs QA?**
QA: "Does expected behavior work?" Red team: "How can I deliberately make the system fail?"

**Q10 — Why is LLM serving different from REST?**
Autoregressive + GPU-memory intensive + KV-cache dependent + Variable-length + Streaming

**Q11 — Why is KV cache important?**
Stores attention key/value tensors from previous tokens to avoid recomputation. Consumes GPU memory; major serving resource.

**Q12 — Why does continuous batching matter?**
Requests finish at different times. New capacity is immediately used by waiting requests instead of waiting for the whole static batch.

**Q13 — Why use vLLM?**
Efficient LLM serving via PagedAttention and continuous batching — improves GPU utilization and KV-cache management.

**Q14 — What is model routing?**
Sending each query to an appropriately sized model. Simple → Small; Complex → Large.

**Q15 — What is semantic caching?**
Caching based on semantic similarity, not exact string equality. Beware: similar meaning ≠ same business answer.

**Q16 — Most important observability difference for LLMs?**
Observe model behavior and quality, not just infrastructure. Traditional: CPU/Memory/Latency/Errors. LLM adds: Prompt · Completion · Tokens · Cost · Retrieval · Quality · User feedback.

---

## 🧠 FINAL ARCHITECT MEMORY MAP

```
                 PRODUCTION LLM
                       |
      +----------------+----------------+
      v                v                v
   EVALUATE          PROTECT          SERVE
 Benchmarks         Guardrails        vLLM
 LLM Judge          Red team          TGI
 Humans             Injection         Triton
      +----------------+----------------+
                       v
                   OPTIMIZE
       +---------------+---------------+
       v               v               v
   Quantization     Routing         Caching
       +---------------+---------------+
                       v
                  OBSERVE
       +---------------+---------------+
       v               v               v
     Trace           Cost            Quality
       +---------------+---------------+
                       v
                  IMPROVE
                       v
                     LOOP
```

---

## 🏆 The 10 Questions an AI Architect Should Always Ask

When someone says *"We want to build an LLM application."* — don't ask "Which model?" Ask:

```
1.  What does GOOD mean?
2.  How will we EVALUATE it?
3.  What can go WRONG?
4.  How will we DETECT hallucinations?
5.  What SAFETY boundaries exist?
6.  What happens if the model is ATTACKED?
7.  Which model is actually REQUIRED?
8.  What is our LATENCY target?
9.  What is our COST per request?
10. How will we OBSERVE production behavior?
```

**LLM User:** "Which model should I use?"
**AI Architect:** Quality · Safety · Reliability · Cost · Latency · Scalability · Observability · Governance → **SYSTEM DESIGN**

---

## 🔥 One-Line Recall for Each Concept

```
EVALUATION            → "How do I know it's actually good?"
BENCHMARK             → "How good is it generally?"
LLM-AS-JUDGE          → "Can I evaluate thousands automatically?"
HUMAN EVAL            → "What does real expert judgment say?"
HALLUCINATION         → "Did the model invent or unsupportedly claim something?"
RAG                   → "Can I ground the answer in trusted information?"
GUARDRAILS            → "What safety controls surround the model?"
RED TEAM              → "How can I deliberately break the system?"
ALIGNMENT             → "How was model behavior shaped toward preferred behavior?"
KV CACHE              → "What previous attention state can I reuse?"
CONTINUOUS BATCHING   → "Can I keep the GPU busy as requests finish?"
PAGEDATTENTION        → "Can I manage KV memory like pages?"
QUANTIZATION          → "Can I use fewer bits?"
SPECULATIVE DECODING  → "Can a small model draft while a big model verifies?"
MODEL ROUTING         → "Does every request really need the biggest model?"
SEMANTIC CACHE        → "Have I answered a meaningfully similar question before?"
OBSERVABILITY         → "Can I explain exactly what happened in production?"
```

---

## 🧠 THE FINAL MENTAL MODEL

```
                 ┌───────────────────┐
                 │      QUALITY      │
                 │  "Does it work?"  │
                 └─────────┬─────────┘
                           v
                 ┌───────────────────┐
                 │      SAFETY       │
                 │ "Can it hurt us?" │
                 └─────────┬─────────┘
                           v
                 ┌───────────────────┐
                 │   INFRASTRUCTURE  │
                 │ "Can it scale?"   │
                 └─────────┬─────────┘
                           v
                 ┌───────────────────┐
                 │       COST        │
                 │ "Can we afford it?"│
                 └─────────┬─────────┘
                           v
                 ┌───────────────────┐
                 │  OBSERVABILITY    │
                 │ "Can we operate?" │
                 └─────────┬─────────┘
                           v
                 ┌───────────────────┐
                 │    CONTINUOUS     │
                 │    IMPROVEMENT    │
                 └───────────────────┘
```

> **The real AI Architect question is never simply "Can the LLM answer?"**
>
> It is: **"Can I build a system around the LLM that is accurate, safe, scalable, observable, cost-efficient, and continuously improvable?"**
