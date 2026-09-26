# Architect-Level AI Fine-Tuning Interview Drill

## Interview Mode

- Ask **one question at a time**.
- Do **not** provide answers, hints, frameworks, or coaching before the candidate responds.
- Follow the source material in the **exact same order**.
- Questions should test architecture, leadership, trade-offs, evidence, ownership, scale, cost, risk, and business impact.
- Pause after every question so the candidate has enough time to think and respond.

---

## Question 1 — The Fundamental Architecture Test

A product manager comes to you and says:

> “Our LLM isn't performing well. We should fine-tune it.”

You are the architect responsible for approving the design.

**Do you approve the fine-tuning project?**

Don't tell me how you would fine-tune.

Instead, walk me through the questions you would ask BEFORE allowing the team to choose fine-tuning as the solution.

### Leadership Challenge

Imagine this is a **₹2 crore AI initiative** and five engineers have already spent three months preparing the fine-tuning pipeline.

Would that investment influence your architectural decision?

**Why or why not?**

**Pause here. Give your answer as if you are sitting in an Architecture Review Board interview.**

---

## Question 2 — Why Do We Need Fine-Tuning?

Imagine your team tells you:

> “We have a prompt that contains all the instructions the model needs. It works reasonably well, but the system prompt is becoming very large and we're handling millions of requests every day.”

You propose fine-tuning.

Now defend that decision.

### Architect Lens

Explain the fundamental difference between:

```text
PROMPT ENGINEERING
        vs
   FINE-TUNING
```

Specifically:

1. What is actually changing in each approach?
2. Why is prompting essentially “telling”, while fine-tuning is “teaching”?
3. At what point does repeating instructions become an architectural/cost problem rather than just a prompt-design problem?
4. If you have 1 million requests/day, and you save 100 tokens/request, what does that mean operationally and financially?
5. What evidence would you ask the team to provide before approving fine-tuning?

### Leadership Challenge

Your engineering team says:

> “Fine-tuning is obviously better because then we don't need to keep sending the instructions.”

Would you accept that argument?

Or would you challenge it?

What measurements, assumptions, and trade-offs would you demand before making the decision?

**Pause here. Answer as if I am interviewing you for a Principal Architect / VP Engineering role.**

---

## Question 3 — The Most Important Architect Distinction

You are designing an AI assistant for a bank.

The product team gives you these requirements:

1. Answer the customer's current interest rate.
2. Always respond in a professional banking tone.
3. Understand the bank's internal terminology and procedures.
4. Return responses in a specific JSON structure.

The team proposes:

> “Let's fine-tune the model on all our banking data. Then it will know everything.”

### Architect Challenge

Would you accept this architecture?

For each of the four requirements, tell me:

- Is this primarily knowledge, behavior, or something else?
- Should we use RAG, prompting, or fine-tuning?
- Why?
- Is the information likely to change?
- Who owns keeping the information correct after production deployment?

### Thought-Provoking Challenge

Suppose today's interest rate is **7%**.

You fine-tune the model using that information.

Six months later, the rate becomes **6.5%**.

Ask yourself:

> What exactly went wrong architecturally?

Was the model wrong?

Was the fine-tuning wrong?

Or did we put volatile knowledge into the wrong architectural layer?

### Leadership Lens

How would you explain the distinction to a senior business leader in **30 seconds**, without using terms like RAG, embeddings, LoRA, fine-tuning, or LLM?

**Pause here. Think deeply and answer as if you're defending this architecture to an Architecture Review Board.**

---

## Question 4 — Full Fine-Tuning

Your team tells you:

> “We have a 7B parameter model. We want to significantly change its behavior, so let's fully fine-tune all 7 billion parameters.”

You are the architect.

### Architect Challenge

Before approving this, explain what actually happens during full fine-tuning.

Walk through the memory requirements for:

- Model weights
- Gradients
- Adam optimizer state
- Activations
- Overall training footprint

For a **7B model in FP16**, approximately how much memory would you expect for each?

### Architectural Challenge

Someone says:

> “The model is only 7B parameters. 14 GB for FP16 weights. We have a 24 GB GPU, so it should fit.”

What's wrong with this reasoning?

What important components are they forgetting?

### Leadership Lens

Assume your CFO asks:

> “Why are we spending heavily on A100/H100 GPUs when we already have cheaper GPUs?”

How would you justify—or reject—the investment?

Explain the business and architectural reasoning.

### Thought-Provoking Challenge

If the behavior change we want is relatively small, why should we rewrite all 7 billion parameters?

What evidence would you require before allowing a team to choose full fine-tuning over parameter-efficient approaches?

**Pause here. Answer as the architect—not as the ML engineer implementing the training job.**

---

## Question 5 — LoRA: The Big Idea

Your team says:

> “Full fine-tuning is too expensive. Let's use LoRA.”

As the architect, you don't want to accept LoRA simply because it's cheaper.

### Architect Challenge

Explain the fundamental architectural idea behind LoRA.

Reason through:

```text
FULL FINE-TUNING

W  ───────────────→  W_new
│
└── Update the entire weight matrix


LoRA

W  ───────────────→  W  (FROZEN)
                       +
                    ΔW
                       │
                    B × A
                       ↓
                  SMALL UPDATE
```

Explain:

1. What does LoRA actually freeze?
2. What does it train?
3. What does `ΔW = B × A` represent?
4. Why does this dramatically reduce the number of trainable parameters?
5. What does LoRA rank `r` mean conceptually?
6. Why can a `4096 × 4096` matrix with 16.7M parameters be represented by roughly 65K trainable parameters at rank 8?
7. What fundamental assumption is LoRA making about the change required by fine-tuning?

### Thought-Provoking Challenge

Why should a small number of trainable parameters be enough to change the behavior of a model containing billions of parameters?

Don't answer “Because LoRA is efficient.”

Explain the underlying reason.

### Evidence Lens

Your ML engineer says:

> “LoRA trains only 0.4% of the parameters, so we're getting almost the same quality for a fraction of the cost.”

Would you accept that statement?

What would you ask them to measure?

### Leadership Lens

How would you explain to your CTO in 30 seconds:

> Why are we not retraining the whole model?

Do it without using the words **LoRA, low-rank, parameters, gradients, or matrices**.

**Pause here. Think it through and answer as if I'm interviewing you for an Architect / VP Engineering role.**

---

## Question 6 — Why Is LoRA So Powerful?

Imagine you operate a platform serving multiple business domains:

```text
                    BASE MODEL
                       7B
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
       BANKING        TRADING       INSURANCE
          │             │             │
      Adapter A      Adapter B      Adapter C
```

Your team says:

> “We'll keep one base model and create separate LoRA adapters for each business domain.”

### Architect Challenge

Why is this architecture potentially much better than maintaining three completely separate fine-tuned models?

Compare:

```text
OPTION A
────────────────────────────
Banking Model       14 GB
Trading Model       14 GB
Insurance Model     14 GB
                     ↓
                   42 GB


OPTION B
────────────────────────────
Base Model          14 GB
Banking Adapter       ~small
Trading Adapter       ~small
Insurance Adapter     ~small
                     ↓
                ~14 GB + adapters
```

Explain the architectural advantage, not just the memory saving.

Think about:

- Model lifecycle
- Deployment
- Versioning
- Cost
- Reusability
- Multi-tenancy
- Isolation
- Rollback
- Operational complexity

### Thought-Provoking Challenge

Suppose:

```text
Base Model v1
    │
    ├── Banking Adapter v1
    ├── Trading Adapter v7
    └── Insurance Adapter v3
```

Tomorrow you upgrade the base model to:

```text
Base Model v2
```

What happens to all your adapters?

Can you simply reuse them?

Or have you created a hidden dependency between the base-model lifecycle and adapter lifecycle?

### Scale Lens

Imagine **500 enterprise customers**, each with their own adapter.

Can your serving infrastructure actually support swapping adapters dynamically at request time?

What new architectural problems appear?

Think about:

- Adapter loading
- Memory management
- Caching
- Latency
- Concurrency
- Tenant isolation
- Adapter versioning
- Failure handling

### Leadership Challenge

One adapter starts producing poor-quality answers.

The CTO asks:

> “Who owns the quality of this model?”

How would you design the operating model so that ownership is unambiguous?

### Final Challenge

What is the deeper architectural principle behind:

> One base model + many specialized adapters?

Don't answer merely “It saves GPU memory.”

**Pause here. Answer as if you're defending a multi-tenant AI platform architecture to a CTO.**

---

## Question 7 — LoRA Merge

Your team has trained a LoRA adapter successfully.

They tell you:

> “Let's merge the adapter into the base model before production. It will simplify serving and improve inference efficiency.”

As the architect, you need to decide whether to **merge or keep the adapter separate**.

### Architect Challenge

Explain what happens during a merge:

```text
BEFORE MERGE

Base Model W ────────────────┐
                             +
Adapter ΔW = B × A ──────────┘
                             │
                             ↓
                       W + B × A
                             │
                             ↓
                         INFERENCE


AFTER MERGE

W_new = W + B × A
        │
        ↓
   SINGLE MODEL
        │
        ↓
     INFERENCE
```

Explain:

1. What does `W_new = W + B×A` mean?
2. What changes operationally after merging?
3. Why might inference become simpler or faster?
4. What flexibility do we lose?
5. Is merging reversible in the same practical sense as simply swapping an adapter?

### Thought-Provoking Challenge

Why is merging fundamentally a trade-off between flexibility and efficiency?

### Production Scenario

You have:

```text
Base Model v1
    │
    ├── Banking Adapter
    ├── Insurance Adapter
    └── Trading Adapter
```

You merge the Banking adapter.

Two weeks later, the Banking team says:

> “We need to go back to the previous behavior immediately.”

What is your rollback strategy?

What if you have already discarded the original adapter and only retained the merged model?

### Time Lens

Imagine the business changes its desired behavior every few weeks.

Would you still merge?

What characteristics of the workload would drive that decision?

Think about:

- Request volume
- Latency requirements
- Number of adapters
- Frequency of behavior changes
- Deployment frequency
- Rollback requirements
- Infrastructure capability

### Leadership Challenge

Your CTO says:

> “I don't care about the technical elegance. Tell me which architecture gives us the lowest operational risk.”

How would you answer?

### Final Architect Question

When should an architect merge a LoRA adapter, and when should they deliberately keep it separate?

**Pause here. Answer as if you're making the production architecture decision—not merely explaining how model merging works.**

---

## Question 8 — QLoRA

Your ML team says:

> “LoRA is still too memory-intensive for our environment. Let's use QLoRA and fine-tune a 7B model on a much smaller GPU.”

You are the architect.

### Architect Challenge

Explain the fundamental difference between LoRA and QLoRA.

```text
LoRA
──────────────────────────────
Base Model
   │
   └── FP16 / higher precision
          +
       LoRA Adapter
          ↓
       Training


QLoRA
──────────────────────────────
Base Model
   │
   └── 4-bit quantized + FROZEN
          +
       LoRA Adapter
          ↓
       Training
```

Explain:

1. What exactly is being quantized?
2. Why is the base model kept frozen?
3. Why is the LoRA adapter kept at higher precision?
4. How does 4-bit quantization reduce memory?
5. Why can this make fine-tuning possible on significantly smaller GPUs?
6. What is the fundamental trade-off introduced by quantization?

### Cost Lens

For a 7B model:

```text
7B × 2 bytes
       ↓
   ~14 GB
```

versus:

```text
7B × 0.5 bytes
       ↓
   ~3.5 GB
```

What does this approximately **75% reduction in model-weight memory** mean from an architectural perspective?

Does lower training cost automatically mean lower total system cost?

Why or why not?

### Thought-Provoking Challenge

Your engineer says:

> “QLoRA is obviously better because we get huge memory savings.”

Would you approve it immediately?

What might you be giving up?

Think about:

- Model quality
- Quantization error
- Training stability
- Inference behavior
- Latency
- Production hardware
- Operational complexity
- Evaluation requirements

### Evidence Lens

Suppose:

```text
                QUALITY
                  │
          ┌───────┴────────┐
          ↓                ↓
        LoRA             QLoRA
        92%               89%

        COST
          │
          ↓
        LoRA  ───────── $$
        QLoRA ───────── $
```

Which one do you choose?

What additional information do you need before making the decision?

### Production Challenge

Your team says:

> “We successfully fine-tuned a 7B model with QLoRA on an 8 GB GPU.”

Would you consider that production-ready evidence?

What production tests would you require before approving deployment?

### Leadership Lens

Your CFO asks:

> “Why should we invest in expensive GPU infrastructure if QLoRA lets engineers train models on consumer-grade GPUs?”

How would you explain the difference between:

```text
EXPERIMENTATION
      vs
PRODUCTION
```

and why the cheapest GPU for training is not necessarily the best architecture for serving millions of requests?

### Final Architect Question

What conditions would make you choose QLoRA over LoRA?

What evidence would convince you that the memory savings are worth the quality trade-off?

**Pause here. Answer as if you're defending the GPU architecture and model-training strategy to both your CTO and CFO.**

---

## Question 9 — PEFT: The Bigger Family

Your team says:

> “We don't necessarily need LoRA. Let's evaluate other Parameter-Efficient Fine-Tuning techniques such as Prefix Tuning, Prompt Tuning, Adapter Layers, IA³, and DoRA.”

As the architect, your job is not to choose the most sophisticated technique.

Your job is to determine whether there is a real architectural constraint that requires something other than LoRA.

### Architect Challenge

What is PEFT actually trying to solve?

Think from first principles about the common idea connecting:

- LoRA
- Prefix Tuning
- Prompt Tuning
- Adapter Layers
- IA³
- DoRA

### Architect's Decision Lens

Would you select a PEFT method purely based on memory, latency, capacity, and complexity?

What is missing?

What would you need to know about your actual workload before choosing?

### Boundary Lens

Your ML engineer says:

> “DoRA is newer, so it must be better than LoRA.”

How would you challenge that statement?

Another engineer says:

> “LoRA is the industry standard, so let's just use LoRA everywhere.”

Would you accept that statement?

What constraint are you actually trying to solve?

### Evidence Lens

Suppose:

```text
LoRA
Accuracy      = 91%
Training Cost = $100
Latency       = 100 ms
```

and another PEFT method gives:

```text
Accuracy      = 92%
Training Cost = $180
Latency       = 130 ms
```

Which one wins?

What business or architectural factors determine the winner?

### Leadership Challenge

Imagine your engineering team spends six weeks experimenting with five PEFT techniques.

At the end they say:

> “We learned a lot, but we haven't selected one yet.”

How would you determine whether that experimentation was valuable or simply technical curiosity disguised as architecture?

### Thought-Provoking Question

Why is having a default architecture valuable for an engineering organization?

When should an architect deliberately break the default?

Give 2–3 concrete constraints that could justify moving away from LoRA/QLoRA.

**Pause here. Answer as if you're establishing the PEFT strategy for an enterprise AI platform.**

---

## Question 10 — Instruction Tuning

Imagine you take a powerful base language model that has been pretrained on enormous amounts of text.

You give it:

> “What are the steps to open a savings account?”

Instead of giving you a clean answer, imagine the model continues the text in an awkward way because it fundamentally behaves like a text completer, not necessarily like an assistant.

### Architect Challenge

Why do we need instruction tuning if the base model already knows the information?

Explain the difference between:

```text
BASE MODEL
    ↓
“I understand language patterns.”

          VS

INSTRUCTION-TUNED MODEL
    ↓
“I understand requests and know how to respond.”
```

Explain:

1. What does pretraining primarily teach?
2. What does instruction tuning add?
3. Why can a model know the correct answer but still fail to behave like an assistant?
4. What exactly are we teaching when we train on instruction → response examples?
5. How is this different from simply putting instructions into a prompt?

### Thought-Provoking Challenge

The model responds to:

> “Convert ₹10,000 to USD.”

with:

> “Currency conversion is the process of converting one currency into another...”

What actually failed?

Is this primarily a knowledge problem, reasoning problem, instruction-following problem, or alignment problem?

Defend your classification.

### Evidence Lens

Your team says:

> “After instruction tuning, the model sounds much more helpful.”

Would you accept “sounds more helpful” as an evaluation criterion?

How would you determine whether the model learned instruction following?

### Architect's Boundary Question

Does instruction tuning necessarily teach the model what responses are safe, honest, and desirable?

If not, what additional architectural concept does that lead us toward?

### Leadership Challenge

Your CTO asks:

> “Why can't we just use a bigger pretrained model instead of instruction tuning a smaller one?”

How would you answer?

Explain the trade-off and identify when a larger base model might actually be preferable.

### Final Architect Question

Complete this mental model:

```text
PRETRAINING
    ↓
“I know language patterns.”

     +

INSTRUCTION TUNING
    ↓
“I understand requests
and know how to respond.”

     +

        ??????
    ↓
“I understand what responses are
preferred, safe, honest and desirable.”
```

What belongs in `??????`, and why?

**Pause here. Answer as if I'm testing whether you understand the architecture of an AI system—not merely the terminology of instruction tuning.**

---

## Question 11 — Instruction Tuning vs Alignment

Imagine you have three versions of the same model:

```text
                    MODEL EVOLUTION
                          │
                          ↓
                 PRETRAINING
                          │
                          ↓
              “I understand language
                 and patterns.”
                          │
                          ↓
              INSTRUCTION TUNING
                          │
                          ↓
              “I can follow requests.”
                          │
                          ↓
                    ALIGNMENT
                          │
                          ↓
              “I should produce
               preferred responses.”
```

### Architect Challenge

Explain the fundamental difference between:

> Instruction tuning

and

> Alignment / preference optimization

Distinguish them in terms of:

1. Capability
2. Behavior
3. Preferences
4. Safety
5. What constitutes a “good” response

### Thought-Provoking Scenario

A model has the technical capability to answer a request, but the aligned model refuses or redirects it because the response would be unsafe.

What is the architectural distinction between:

> “Can do it”

and

> “Should do it”?

### Evidence Lens

Your team says:

> “Our instruction-tuned model performs extremely well on our task, so we don't need alignment.”

Would you agree?

What failure modes would you look for?

Conversely:

> “Alignment will make the model capable of performing the task.”

Would you agree?

Explain why alignment cannot magically create a capability that the underlying model does not possess.

### Boundary Lens

Which layer is primarily responsible for deciding that a technically correct response should not be given because it is unsafe?

Where would you draw the architectural boundary?

### Leadership Challenge

A production incident occurs:

> The model gives a response that is technically correct but unsafe.

Your CTO asks:

> “Whose failure is this?”

Would you classify it as model capability failure, instruction-tuning failure, alignment failure, prompt-engineering failure, guardrail failure, system-architecture failure, or multiple layers failing simultaneously?

How would you investigate before assigning ownership?

### Final Architect Question

If a model can do something, does that mean the production system should allow it to do that thing?

**Pause here. Answer as if I'm testing whether you understand the boundary between AI capability, instruction following, alignment, and production responsibility.**

---

## Question 12 — Dataset Design

Your ML team tells you:

> “We have created 100,000 high-quality instruction/response examples. They are clean, grammatically correct, perfectly formatted, and reviewed by experts. Let's fine-tune the model.”

You are the architect.

### Architect Challenge

Would you approve the dataset?

What makes a fine-tuning dataset architecturally good?

Think through:

- Diversity
- Quality
- Realism
- Consistency
- Held-out evaluation data

### Thought-Provoking Scenario

Suppose training data contains only beautifully written requests:

```text
“Please provide the current status
of my mutual fund investment.”
```

But production users actually write:

```text
“mf status?”
“where is my money”
“need my sip details plz”
“my sip stopped??”
“acct investment not showing”
```

What did the dataset teach the model incorrectly about the real world?

### Evidence Lens

Your data science team says:

> “We don't need production traffic. We already have expert-created examples, and they're much better.”

Would you challenge that?

What production data would you want to sample?

Should every production example go directly into the training dataset?

Why or why not?

### Failure Lens

Suppose training data is:

```text
90% normal requests
10% edge cases
```

but production traffic is:

```text
60% normal requests
40% edge cases
```

What happens?

What does this tell you about training-data distribution versus production-data distribution?

### Leadership Challenge

You're responsible for a banking AI platform.

Your team asks for another three months to create more training data.

The business asks:

> “Why can't we launch now? The model already has 95% accuracy.”

How would you respond?

What questions would you ask before deciding whether that 95% is meaningful?

### Architect's Deep Question

If the dataset systematically excludes messy user behavior, rare cases, ambiguous inputs, or production failures:

**Who is actually responsible for the model's eventual failure—the model or the architect who designed the dataset?**

Defend your answer.

**Pause here. Answer as if you're reviewing the training-data strategy for a production banking AI system.**

---

## Question 13 — Training Loss ≠ Business Success

Your ML engineer says:

> “Excellent news. Our training loss dropped dramatically. The model is now achieving 99% accuracy on our training dataset.”

The team recommends moving toward production.

### Architect Challenge

Do you approve?

What does training loss actually tell you?

What does it not tell you?

### Thought-Provoking Scenario

Suppose:

```text
Training Performance
        ↓
       99%

Test Performance
        ↓
       60%
```

What immediately comes to your mind?

Is the model learning, memorizing, overfitting, underfitting, or suffering from bad evaluation data?

Defend your diagnosis.

### Architect's Boundary Question

Where would you draw the line between:

> “The model learned the underlying pattern”

and

> “The model memorized the training examples”?

Consider:

```text
TRAINING     TEST
   99%        98%
   99%        90%
   99%        80%
   99%        60%
```

At what point would you become concerned?

Is there a universal threshold that applies to every model and task?

### Evidence Lens

Your team says:

> “Our training loss is excellent, therefore the model is ready.”

What evidence would you demand instead?

Think about:

- Training data
- Held-out test data
- Real-world data
- Business metrics
- Production performance

### Leadership Lens

The business tells you:

> “The model is 99% accurate, so why aren't customers happy?”

What questions would you ask before accepting the 99% number?

Could the metric itself be misleading?

### Production Scenario

Suppose:

```text
             TRAINING     TEST
Normal cases    99%        97%
Edge cases      98%        55%
```

Overall test accuracy is still 94%.

The team says:

> “94% is good enough.”

Would you approve production?

What additional analysis would you perform?

### Architect's Deep Question

If I gave you only one number—training loss—and asked whether the model should go to production, could you make that decision?

Why not?

What is the minimum evidence stack you would require before making a production recommendation?

**Pause here. Answer as if you're the architect accountable for the model's production outcome—not the ML engineer accountable only for the training run.**

---

## Question 14 — The BIG Architecture Decision

A product team approaches you with this requirement:

> “Our AI assistant needs to answer questions about interest rates, account types, products, policies, customer-specific information, and regulatory requirements. We believe fine-tuning the model on our banking data is the right approach.”

As the architect:

**How would you determine whether fine-tuning is actually the right architectural solution?**

**Pause and think.**

---

## Question 15 — Behavior Problem

Your banking assistant consistently fails to follow a requirement to respond in a specific professional tone and format.

The team immediately recommends fine-tuning the model.

**As the architect, what would you investigate and try before deciding that fine-tuning is necessary?**

**Pause and think.**

---

## Question 16 — Structured Extraction Example

You are designing a banking AI system that must extract customer information from unstructured documents and return it as strict JSON.

The team proposes fine-tuning the model to improve extraction accuracy.

**As the architect, how would you design the complete production solution so that a model error does not directly become a downstream business error?**

**Pause and think.**

---

## Question 17 — Fintech Example: Three Problems

You are designing a banking AI assistant and encounter these three production problems:

1. The assistant gives the **wrong NAV** for a mutual fund.
2. The assistant gives the **wrong tone** when communicating with customers.
3. The assistant produces **invalid JSON** for a downstream system.

**As the architect, how would you diagnose and solve each of these three problems, and why would you deliberately choose different approaches rather than applying one technique to all three?**

**Pause and think.**

---

## Question 18 — Production Architecture

You are taking an AI assistant from prototype to production.

The proposed architecture is:

**User → Gateway → Orchestrator → Prompt/RAG/Model → LLM → Guardrails → Response**

As the architect responsible for the system:

**What would you expect each layer to be responsible for, and what critical production capabilities would you add around this flow before approving it for a high-volume banking environment?**

**Pause and think.**

---

## Question 19 — The Ultimate Mental Model

You are asked to design an AI solution for a new business problem.

The team immediately starts discussing prompts, RAG, fine-tuning, model selection, and guardrails.

As the architect:

**How would you determine the simplest architecture that solves the actual problem, and how would you decide which layers are genuinely necessary rather than adding complexity by default?**

**Pause and think.**

---

## Question 20 — Architect's Diagnostic Questions

Before approving a fine-tuning initiative, you are given only this statement:

> “The model isn't performing well, so we need to fine-tune it.”

As the architect:

**What are the critical questions you would ask the team before allowing the project to proceed?**

**Pause and think.**

---

## Question 21 — Interview Recall: Architect Level

You are in a senior architecture interview, and the interviewer asks:

> “Explain the difference between RAG vs Fine-Tuning, Full Fine-Tuning vs LoRA, LoRA vs QLoRA, and Instruction Tuning vs Alignment. Then explain how dataset diversity and generalization affect your decision.”

**How would you answer this as an architect, focusing on the WHY, trade-offs, and decision criteria rather than simply defining each term?**

**Pause and think.**

---

## Interview Rule

**Do not reveal the answer before the candidate responds.**

The purpose of this drill is to build the candidate's ability to reason independently across:

- Architecture
- Leadership
- Cost
- Scale
- Evidence
- Failure
- Ownership
- Risk
- Business impact
- Production operations
- Technology trade-offs
