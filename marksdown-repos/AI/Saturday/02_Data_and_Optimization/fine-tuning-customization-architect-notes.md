# 🧠 Fine-Tuning & Customization — Complete Architect Notes

> Architect thinking notes with key learnings and thought-provoking takeaways.

---

# 📐 Foundation & Mindset — When (and When NOT) to Fine-Tune

## 0. First: Don't Start With "How Do I Fine-Tune?"

Before jumping to solutions, figure out what's actually broken. It's like a doctor diagnosing before prescribing medicine — you wouldn't give antibiotics for a broken leg.

Most teams rush to fine-tuning because it sounds sophisticated. But often the problem is simpler: either the model lacks current information (needs RAG) or doesn't follow instructions well (needs better prompting).

**The most expensive solution is rarely the right first solution.** If you're a surgeon, you don't start with "let's operate" — you start with "what's wrong?" Same with AI. The technology choice is the LAST decision, not the first.

An architect should **not** start here:
```
"We have an LLM problem"
        |
        v
"Let's fine-tune it"
```

Instead:
```
             AI PROBLEM
                 |
                 v
        +-------------------+
        | What is actually  |
        | going wrong?      |
        +-------------------+
                 |
       +---------+---------+
       |                   |
       v                   v
   KNOWLEDGE            BEHAVIOR
   problem?             problem?
       |                   |
       v                   v
      RAG             Prompt / FT
```

**Architect Question:** Before choosing a technology, what should I diagnose?

**Answer:** Determine:
```
Is the model missing INFORMATION?
              OR
Is the model behaving incorrectly?
```
This single question prevents a huge number of bad AI architecture decisions.

---

## 1. Why Do We Need Fine-Tuning?

Instead of telling the model HOW to behave every single time (like giving instructions to a new employee every morning), you train it once so it "just knows" how to behave.

Fine-tuning bakes behavior into the model's weights. Prompt engineering is like giving verbal instructions each time — it works but costs more tokens and is less consistent.

**Prompting = telling. Fine-tuning = teaching.** If you have 1 million requests per day, even saving 100 tokens per request adds up to 100 million tokens daily — that's real money.

Suppose you have a powerful general-purpose LLM that can summarize, translate, write code, answer questions, reason, generate JSON, explain concepts. Why would you train it again? If prompting can tell it what to do, why spend money training it?

**Answer:** Because sometimes we don't want to **tell the model repeatedly**. We want the behavior to become part of its learned behavior.

**Prompt Engineering:**
```
Every request:  User → Huge System Prompt (+ Examples + Rules) → LLM → Response
```
Every request pays the cost.

**Fine-Tuning:**
```
TRAINING: Base LLM → Fine-tuning → Adapted Model
Every request: User → Adapted Model → Desired behavior
```
The behavior becomes more **baked into the model**.

---

## 2. The Most Important Architect Distinction

`KNOWLEDGE (facts) → RAG` and `BEHAVIOR (style/method) → Fine-tuning/Prompting`

RAG changes WHAT the model knows. Fine-tuning changes HOW the model thinks. If you fine-tune for knowledge, you're "baking in" facts that will become outdated. If you RAG for knowledge, you can update your database without retraining. Always separate facts from behavior.

**Memorize this:**
```
               LLM CUSTOMIZATION
                       |
             +---------+---------+
             |                   |
             v                   v
         KNOWLEDGE            BEHAVIOR
         "What?"              "How?"
             |                   |
             v                   v
            RAG             Fine-tuning
                                 |
                                 v
                          Prompt Engineering
                          may be enough first
```

**Knowledge examples:** What is today's NAV? / Today's interest rate? / Latest policy? / Customer's current balance? → These are **facts**.

**Behavior examples:** Always answer in compliance tone / Always produce this JSON format / Always follow this reasoning pattern / Always include a particular response structure → These are **behaviors**.

**Architect Mental Model:**
> **RAG changes what the model can see.**
> **Fine-tuning changes how the model behaves.**
> **Prompting tells the model what to do right now.**

That distinction is foundational.

---

# ⚙️ Core Techniques — Full FT, LoRA, QLoRA & PEFT

## 3. Full Fine-Tuning

Imagine needing to change one lightbulb in a skyscraper. Full fine-tuning is like rewiring the entire building. It works, but it's massive overkill for most problems.

Full fine-tuning updates ALL 7+ billion parameters. The memory requirements aren't just the model weights — you need gradients (for learning), optimizer state (for tracking updates), and activations (for forward passes).

**Memory = Weights + Gradients + Optimizer State + Activations**

For a 7B model in FP16: Weights 14GB, Gradients 14GB, Adam optimizer 56GB, Activations several GB. Total: ~85GB+ per GPU. That's why you need expensive A100/H100 GPUs.

**Think:** A model has 7,000,000,000 parameters. Your requirement is: "Always generate our specific JSON format." Would you modify all 7 billion parameters? Probably not.

```
Need to change one room → Renovate entire building → 💰💰💰
```

**Full Fine-Tuning Architecture:**
```
                 BASE MODEL (7B parameters)
                    |
                    v
        +------------------------+
        | Update ALL parameters  |
        +------------------------+
                    |
                    v
             New model
```

**Why Is It Expensive?** This is where an architect should think beyond "The model is 7B parameters." Training memory is much more than model weights.
```
              GPU MEMORY
     +------------+-------------+
     v            v             v
  Weights      Gradients     Optimizer
    14 GB         14 GB        56 GB
                                  |
                                  v
                         HUGE MEMORY COST
              + Activations
```
Approximate 7B fp16 example:
```
Weights       ~14 GB
Gradients     ~14 GB
Adam state    ~56 GB
Activations   several GB
--------------------------
Total         ~85 GB+
```

> **The model size is NOT the training memory requirement.**

**Why Does Optimizer State Matter?** Adam needs information about previous updates:
```
Weight → Gradient → Momentum → Variance
```
You are effectively maintaining: `W + gradients + optimizer state + activations`

**Architect Decision:** Full fine-tuning makes sense when:
```
             FULL FT
       +--------+---------+
       v        v         v
Huge data   Major       Foundation
            capability   model work
            shift
```
Otherwise: `Task-specific customization → Prefer PEFT → LoRA / QLoRA`

---

## 4. LoRA — The Big Idea

Instead of changing the entire model, LoRA is like adding a small sticky note with instructions on top of the original text. The original text stays unchanged, but the sticky note modifies how you read it.

Instead of updating W (the full weight matrix), LoRA learns `ΔW = B × A`, where A and B are tiny matrices. The original W stays frozen — you only train these small adapters.

**W_new = W + (B × A)** where B and A are tiny compared to W.

A 4096×4096 matrix has 16.7 million parameters. With LoRA rank=8, you only train: A: 8×4096 = 32,768; B: 4096×8 = 32,768. Total: ~65K parameters. That's a **99.6% reduction** in trainable parameters!

**Architect Question:** Instead of changing `W`, can we learn only `ΔW`? And even better: can ΔW be represented using much smaller matrices? That's the key insight behind LoRA.

**Traditional Fine-Tuning:**
```
W → Update everything → W'
```

**LoRA:**
```
              Frozen W
                |
                v
              +---+
              | + |
              +---+
                ^
                |
              ΔW
                |
           +----+----+
           |         |
           A         B
        small      small
```
Mathematically:
```
ΔW = B × A
W_new = W + B×A
```

**Example:**
Original: `W = 4096 × 4096 ≈ 16.7 million parameters`
LoRA: `A = 8 × 4096`, `B = 4096 × 8` → A + B ≈ 65K parameters
So instead of training 16.7M, you train approximately 65K. That's an enormous reduction.

**What Is "Rank"?** The key LoRA parameter: `r = rank` (e.g., 4, 8, 16, 32, 64)
```
Low rank  → Less capacity, Less memory, Lower complexity
Higher rank → More capacity, More parameters, Potentially more overfitting
```

**Architect Thought:** Don't memorize "LoRA uses two matrices." Understand:
> **LoRA assumes the useful change required by fine-tuning can often be represented as a low-dimensional update.**

That is the architectural idea.

---

## 5. Why LoRA Is So Powerful

Think of LoRA like having one powerful engine (the base model) that can be customized for different vehicles (adapters). You don't build a new engine for each car — you just add different attachments.

One base model can serve multiple fine-tuned behaviors by swapping small LoRA adapters. This is perfect for multi-tenant systems where different customers need different behaviors.

**One base model + Many adapters = Massive cost savings.**

Imagine a platform serving: Banking customers (compliance tone), Trading customers (precision, numbers), Insurance customers (empathy, clarity). With LoRA, you store ONE 7B model (14GB) and three adapters (~65KB each). Without LoRA, you'd need three 14GB models. That's 42GB vs 14GB — huge difference!

**Traditional:**
```
Customer A → FULL MODEL A
Customer B → FULL MODEL B
Customer C → FULL MODEL C
```
Very expensive.

**With LoRA:**
```
                   BASE MODEL
                       |
             +---------+---------+
             v         v         v
          LoRA A    LoRA B    LoRA C
          Banking   Insurance  Trading
```
One base model. Many adapters.

**Multi-Tenant Architecture:**
```
                    Request
                       |
                       v
                +-------------+
                | Router      |
                +-------------+
                  /    |    \
                 v      v      v
             LoRA-A  LoRA-B  LoRA-C
                \      |      /
                  +----+----+
                       |
                       v
                  Base Model
```
You can potentially support `Tenant A → Adapter A`, `Tenant B → Adapter B`, `Tenant C → Adapter C` without maintaining an entirely separate model for each tenant.

---

## 6. LoRA Merge

After training, you can "merge" the sticky note into the original book. Once merged, it's just one book — no extra notes needed. This makes deployment simpler and faster.

Before inference, you can compute `W_new = W + B×A` and merge the adapter into the base weights. This eliminates the adapter computation during inference, reducing latency.

**Merge = Trade flexibility for efficiency.**

During training: Base (frozen) + Adapter (trainable) → extra computation. After merging: Merged Model → normal inference (no overhead). This matters because: Before merge, each request loads base + adapter; after merge, each request loads just the merged model. For high-volume production, merged models are faster. But you lose the ability to quickly swap adapters.

During training:
```
W frozen
   +
B × A
   |
   v
trained adapter
```
After training: `W_new = W + B×A` — you can merge the update into the base weights.
```
Before merge:  Base + LoRA → extra adapter computation
After merge:   Merged Model → normal inference
```

**Architect Insight:** Architecture is not just about training. Ask:
```
How do I TRAIN it? → How do I STORE it? → How do I DEPLOY it?
→ How do I SCALE it? → How do I OPERATE it?
```
LoRA performs very well across these dimensions.

---

## 7. QLoRA

QLoRA takes the LoRA idea further — it's like compressing the original book to 1/4 its size while still keeping the sticky note instructions. The book becomes much smaller, so you can fit it on cheaper, smaller devices.

QLoRA compresses the frozen base model to 4-bit precision (from 16-bit) and keeps the LoRA adapter in higher precision. This reduces memory by ~4x for the base model.

**4-bit quantization = ~75% memory savings.**

7B model: FP16 = 14GB, 4-bit = 3.5GB. This means you can fine-tune a 7B model on a consumer GPU with 8GB VRAM! But the adapter still needs gradients and optimizer state in high precision. Total memory is still more than 3.5GB, but significantly less than 14GB.

**Next Architect Question:** LoRA solves "I don't want to update the whole model." But the frozen model still consumes memory. So ask: "If the weights are frozen, why must they occupy full fp16 precision?" That leads to QLoRA.

**QLoRA Architecture:**
```
                 BASE MODEL
                    |
              Quantize to 4-bit
                    |
                    v
              +-----------+
              | 4-bit NF4 |
              |  Frozen   |
              +-----------+
                    |
                    +------+
                           |
                      LoRA Adapter (bf16 / fp16)
                           |
                           v
                       Training
```
So:
```
LoRA:   Base = fp16, Adapter = fp16
QLoRA:  Base = 4-bit NF4, Adapter = higher precision
```

**Memory Intuition:** 7B model:
```
FP16:  7B × 2 bytes   → ~14 GB
4-bit: 7B × 0.5 bytes → ~3.5 GB
```
Approximately 4× compression for the raw weights.

**QLoRA Adds:**

**1. Double Quantization:** Quantization → Quantization constants → quantize those too. Saves additional memory.

**2. Paged Optimizers:**
```
GPU memory → full → GPU → memory pressure → CPU / Unified Memory
```
Helps avoid GPU OOM during spikes, at a possible performance cost.

**Architect View:** Think of LoRA and QLoRA as solving **different layers of the memory problem**:
```
Full FT: Train all weights + Gradients for all + Optimizer state for all → Huge memory
   ↓
LoRA: Freeze base + Train tiny adapter
   ↓
QLoRA: Also compress frozen base
```

---

## 8. PEFT — The Bigger Family

LoRA is one way to add sticky notes. There are other ways too — you can add virtual tokens that guide the model, insert small modules between layers, or scale activations. LoRA is just the most popular one.

PEFT (Parameter-Efficient Fine-Tuning) includes: LoRA (low-rank matrices), Prefix Tuning (virtual tokens before input), Prompt Tuning (trainable embeddings), Adapter Layers (inserted modules), IA³ (activation scaling vectors), DoRA (separates magnitude and direction).

**Default to LoRA/QLoRA unless you have a specific constraint.** Different PEFT methods trade off: Memory usage, Latency, Capacity, Training stability. For 90% of use cases, LoRA is the best balance.

```
                 PEFT
      +-----------+-----------+
     LoRA       Prompt      Adapter
      |          Tuning       |
     DoRA      Prefix       IA³
```

**Prefix Tuning:** `Input → [Virtual tokens] → Transformer layers` — Virtual trainable representations guide the model.

**Prompt Tuning:** `Input → [Trainable embeddings] → Transformer` — Similar idea but generally simpler.

**Adapter Layers:** `Transformer → Adapter → Transformer → Adapter` — Inserting trainable modules.

**IA³:** `Activation → Scaling vector → Rescaled activation` — Extremely parameter efficient.

**DoRA:** LoRA decomposes updates. DoRA additionally separates:
```
Weight
 |
 +----------------+
 |                |
Magnitude       Direction
```
This can improve learning capacity in some settings.

**Architect Decision:** Don't memorize five PEFT algorithms. Ask:
```
What constraint am I optimizing?
     +-------+-------+
     v       v       v
Memory   Latency   Capacity
     +-------+-------+
             v
      Choose PEFT method
```
For most practical systems: `DEFAULT → LoRA / QLoRA`

---

# 🧬 Training Process — Instruction Tuning, Data & Evaluation

## 9. Instruction Tuning

Raw LLMs are like brilliant but awkward savants — they know facts but don't know how to "talk to people." Instruction tuning teaches them the conversation rules: listen to the user, understand the task, and respond helpfully.

Base models are trained to predict the next token. Instruction-tuned models are trained to follow instructions. This transforms the model from a "text completer" to an "assistant."

**Instruction tuning = "How to be helpful" training.**

Base model: "The capital of France is..." → "The capital of France is Paris."
Instruction-tuned: User: "What's the capital of France?" → Model: "The capital of France is Paris."

It's not just about the answer — it's about recognizing that the user ASKED a question and expects a direct response, not a continuation.

**Important Thought Experiment:** A pretrained model has consumed huge amounts of text. But what was its objective? `Predict next token`. Not necessarily: understand request + execute request + return useful answer.

**Pretraining:**
```
"The capital of France is" → "Paris"
```
The model learns: `P(next token | previous tokens)`

**Instruction Tuning:** Now provide `Instruction + Desired Response`. Example:
```
Instruction: "Summarize this paragraph in one sentence."
Response: "........."
```
Thousands/millions of examples teach:
```
REQUEST → Understand task → Execute task → Generate appropriate response
```

**What Does Instruction Tuning Teach?**
```
Instruction Tuning
        +--> Task recognition
        +--> Format compliance
        +--> Generalization
        +--> Conversation structure
```

**Base vs Instruct Model:**

Base:
```
User: "Summarize this paragraph..."
Model: "Summarize the following..." "Summarize the next..." "Here is another example..."
```
It may continue the pattern.

Instruction Tuned:
```
User: "Summarize this paragraph..."
Model: Actual summary
```
The fundamental behavior has changed.

---

## 10. Instruction Tuning vs Alignment

Instruction tuning teaches "how to respond to requests." Alignment teaches "what kind of responses are good." The first is about capability, the second about values and preferences.

Pretraining → Learn language patterns. Instruction Tuning → Learn request-response patterns. Preference Optimization → Learn preferred responses among good ones.

**Instruction tuning = Capability. Alignment = Values.**

Imagine asking about a controversial topic. A base model might generate neutral text. An instruction-tuned model might generate a helpful answer. An aligned model might additionally consider safety, helpfulness, and honesty before responding.

```
             PRETRAINING
                  |
                  v
             BASE MODEL
                  |
                  v
        INSTRUCTION TUNING / SFT
                  |
                  v
        Instruction Following
                  |
                  v
          RLHF / DPO
                  |
                  v
       Preference / Alignment
```
Think:
```
Pretraining              → "What language patterns exist?"
Instruction tuning       → "How should I respond to requests?"
Preference optimization  → "Which valid response is preferred?"
```

---

## 11. Dataset Design

If you train a model on only perfect, well-written examples, it will fail in the real world where users write messy, incomplete queries. Your training data should mirror reality — typos, sloppy grammar, incomplete sentences, and all.

A good dataset must be: Diverse (many task types), High-quality (accurate labels), Realistic (matches production inputs), Consistent (same pattern across examples), With held-out evaluation data.

**Garbage in = Garbage out. Your model learns patterns, not intentions.**

Bad dataset: 1000 examples of perfectly formatted requests. Real world: "hey need help with my acct plz". Your model won't understand because it was trained on a different reality. Always sample real production traffic to build your dataset.

**Architect Question:** Suppose I give the model 100,000 examples. Is that automatically good? **No.** The model doesn't learn "This is a good dataset." It learns patterns from what you give it.

**Garbage In → Garbage Out:**
```
Poor Dataset → Poor Training Signal → Poor Model Behavior

High-quality + Diverse + Realistic + Consistent Examples
→ Better Training Signal → Better Generalization
```

**What Makes a Good Dataset?**
```
             DATASET
      +---------+---------+
      v         v         v
 Diversity   Quality   Realism
      +---------+---------+
                v
          Consistency
                v
          Held-out Eval
```

**Diversity:**
Bad: `"Summarize..."` × 4
Good: Summarization, Translation, Extraction, Classification, Reasoning, Messy inputs, Short inputs, Long inputs, Different phrasings, Edge cases

**Why Realistic Inputs?**
Production users don't say: *"Please extract the scheme code from the following well-formatted financial statement."*
They say: *"hey i invested 20k in that abc fund folio 12345 what is scheme code??"*
Your training data should represent reality.

**Held-Out Evaluation:**
Never:
```
Train → Test on same data → "Wow! 99% accuracy!"  ← Meaningless
```
Instead:
```
             DATASET
        +-------+-------+
        v               v
     TRAIN             EVAL
        v               |
     Model              |
        +-------<-------+
                v
          Generalization?
```
The evaluation data must remain unseen during training.

---

## 12. Training Loss ≠ Business Success

A student can ace practice tests by memorizing answers but fail the real exam because they didn't understand the concepts. Same with AI — low training loss just means it memorized the training examples, not that it'll work in production.

Models can overfit to training data, achieving low loss but poor generalization. Always evaluate on held-out test data that was never seen during training.

**Low training loss = Memorization. Good test performance = Learning.**

If your model gets 99% on training data but 60% on test data, it's severely overfitting. The model hasn't learned the underlying pattern — it's just memorizing examples. Always reserve a separate test set that you only touch ONCE — at the end. If you use it for tuning, you're cheating.

You can have:
```
Training Loss → very low
while:
Production Performance → poor
```
Why? Because the model may have memorized superficial patterns.
```
Training examples → Memorization → Low training loss → ✗ → Poor real-world generalization
```

> **Always evaluate behavior on realistic held-out data.**

---

# 🏛️ Architecture Decision Framework — What to Build and When

## 13. The BIG Architecture Decision

If someone asks "should I fine-tune?" — STOP. First ask: Is the problem about facts (what's true) or behavior (how to act)? This single question saves millions in wasted engineering.

Facts/Knowledge → RAG or Prompting. Behavior → Prompting first, then Fine-tuning if needed.

**Facts change → retrieve. Behavior changes → teach.**

If you're building a customer service bot for a bank: Questions about interest rates → RAG (they change daily); Questions about account types → RAG (can change); Tone/personality → Fine-tuning (stable, learnable behavior); Response format → Prompting (easy to specify).

Suppose someone says: *"Our AI gives the wrong NAV."* What do you do? Don't immediately say `Fine-tune!` Think.

**Decision Framework:**
```
                    PROBLEM
                       |
                       v
              +----------------+
              | FACT or        |
              | BEHAVIOR?      |
              +----------------+
                /            \
             FACT           BEHAVIOR
              |                |
              v                v
        Is fact changing?   Can prompt
              |             describe it?
          +---+---+              |
         YES      NO             v
          |        |         Prompt first
          v        v
         RAG    Prompt
                   |
                   | insufficient?
                   v
                Fine-tune
```

**FACT Problem:** Example: "What is today's NAV?"
```
Customer → AI Application → Retrieve current NAV → Live API / DB → LLM → Answer
```
Not:
```
Customer → Fine-tuned model → Old NAV ❌
```

**Why Fine-Tuning Is Bad for Volatile Facts:**
```
Monday    NAV = ₹100 → Fine-tune model
Tuesday   NAV = ₹102 → Your model still has a learned association around ₹100
Wednesday NAV = ₹97  → Now what? Retrain?
Monday → Train, Tuesday → Train, Wednesday → Train...  Architecturally absurd.
```

**RAG Is Designed for This:**
```
                USER → Question → Retriever
          +-------+-------+
          v               v
       Vector DB       Live API
          +-------+-------+
                  v
             Context → LLM → Answer
```
The model doesn't need to **memorize** the current fact. It receives it at inference time.

---

## 14. Behavior Problem

When the model doesn't follow your rules, try telling it the rules more clearly first (better prompts). Only if that consistently fails, then teach it through fine-tuning.

Start with prompting. If that's insufficient, consider fine-tuning. The behavior must be: 1. Demonstrable with examples, 2. Stable over time, 3. Important enough to justify training.

**Prompt → If fails → Fine-tune.**

If the prompt "Always respond in a professional tone" doesn't work, ask: Is the prompt clear enough? Does it have examples? Is the model capable of professional tone (base model limitation)? If it's a base model limitation, fine-tuning might help. But often, it's just poorly written prompts.

Suppose: *"The model doesn't consistently use our compliance-approved tone."*
Now this is different.
```
Problem: HOW should the model respond?
Not: WHAT fact should it know?
```
Start:
```
Prompt → Few-shot examples → Measure compliance
```
If insufficient:
```
Prompt → ✗ Still inconsistent → Fine-tuning
```

---

## 15. Structured Extraction Example

If you need to extract data from messy text into neat JSON, fine-tuning is a good choice — BUT always add validation guards. Fine-tuning gets you 80% of the way, but validation ensures 100% correctness.

Fine-tuning is excellent for structured extraction, but production architecture should include: Schema validation, Business rule checks, Fallback mechanisms, Monitoring for drift.

**Fine-tuning = 80% solution. Validation = 100% reliability.**

Even with the best fine-tuning, the model WILL make mistakes on edge cases. If your system depends on 100% accuracy, you need: 1. Output parsing with validation, 2. Rejection of invalid outputs, 3. Retry with different prompting, 4. Fallback to human review. Always plan for the model to be wrong sometimes.

This is a strong fine-tuning candidate.

**Input:**
```
"i want to invest 20k in abc fund
folio 12345"
```
**Desired:**
```json
{
  "scheme_code": "ABC123",
  "folio_number": "12345",
  "amount": 20000
}
```
**Architecture:**
```
Messy Customer Text → Fine-tuned LLM → Structured JSON
→ Schema Validator → Downstream Service
```

**Notice something important:** Fine-tuning is not the only protection. Use:
```
Fine-tuning + Structured Output + Schema Validation + Business Rules
```
This is much stronger production architecture.

---

## 16. Fintech Example — Three Problems

Different problems need different solutions. One size doesn't fit all. Mix and match based on the specific problem.

Wrong NAV → Knowledge freshness → RAG/Live API. Wrong tone → Behavior → Prompt → Fine-tune. Bad JSON → Task skill → LoRA + validation.

In a real fintech system, you might use: RAG for market data, Prompt engineering for regulatory disclosures, LoRA for extracting trade details, Guardrails for safety checks. The system is a composition of techniques, not a single approach.

| Problem | Diagnosis | Preferred solution |
|---|---|---|
| Wrong today's NAV | Knowledge/freshness | RAG / live API |
| Wrong compliance tone | Behavior | Prompt → LoRA if needed |
| Bad JSON extraction | Task skill | LoRA/QLoRA + validation |

---

## 17. Production Architecture

In production, you don't just send user queries to the model. You have a whole pipeline: pre-processing, fetching context, routing to the right model, validating outputs, and logging everything.

User → Gateway → Orchestrator → [Prompt/RAG/Model] → LLM → Guardrails → Response. Each component has a specific job: Orchestrator routes and coordinates; Prompt adds instructions; RAG fetches context; Fine-tuned Model does the heavy lifting; Guardrails validates output.

**Architecture = Composition of specialized components.**

Most teams focus on the model and forget about: Monitoring (how do you know if the model degraded?), Logging (how do you debug failures?), Caching (how do you avoid repeated expensive calls?), A/B testing (how do you test new models?), Rollback (how do you quickly revert bad changes?).

The real answer isn't always `RAG OR Fine-tuning OR Prompt`. Often it is:
```
                    USER
                      |
                      v
                API Gateway
                      |
                      v
               AI Orchestrator
                      |
          +-----------+-----------+
          v           v           v
       Prompt        RAG      Fine-tuned
       Rules        Context       Model
          +-----------+-----------+
                      v
                     LLM
                      v
                Guardrails
             +--------+--------+
             v                 v
        Schema check      Safety check
             +--------+--------+
                      v
                   Response
```
This is how an architect should think.

---

## Key Takeaways

1. **Diagnose before prescribing** — Knowledge problem or behavior problem?
2. **RAG = what the model sees. Fine-tuning = how the model behaves. Prompting = what to do right now.**
3. **Full FT memory = Weights + Gradients + Optimizer State + Activations** (model size ≠ training memory)
4. **LoRA: W_new = W + B×A** — 99.6% reduction in trainable parameters
5. **QLoRA: 4-bit base + higher-precision adapter** — ~75% memory savings
6. **One base model + Many adapters** = multi-tenant cost savings
7. **Merge = Trade flexibility for efficiency**
8. **Default to LoRA/QLoRA** unless you have a specific constraint
9. **Instruction tuning = capability. Alignment = values.**
10. **Dataset: Diverse + Quality + Realistic + Consistent + Held-out eval**
11. **Low training loss ≠ business success** — always evaluate on held-out data
12. **Fact changing → RAG. Behavior problem → Prompt first, then fine-tune.**
13. **Fine-tuning = 80% solution. Validation = 100% reliability.**
14. **Production = composition of specialized components**, not a single technique
