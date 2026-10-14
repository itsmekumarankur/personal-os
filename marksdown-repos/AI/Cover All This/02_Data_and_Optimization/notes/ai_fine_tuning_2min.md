# AI Fine-Tuning 


Your team says:

> **“Our AI needs to behave differently for our business, so let's fine-tune the model.”**

You approve it without asking further questions.

Three months later, you've spent significant GPU time, engineering effort, and money—only to discover that some of the requirements could have been solved with **prompting or retrieving current information**, rather than changing the model itself. Your notes specifically frame this as the key architectural decision: **knowledge vs. behavior**, and when fine-tuning is actually justified. ([GitHub][1])

As an Engineering Manager, understanding fine-tuning helps you ask:

> **“What problem are we actually trying to solve—and is changing the model really the right investment?”**

### Why I am reading this

**Because fine-tuning is an architecture and investment decision—not simply an ML implementation decision.**

### Leadership question

> **“Are we changing the model because we need to change its behavior, or because we don't know a better way to provide the right information?”**

### One-line takeaway

> **Don't fine-tune because the model isn't perfect—fine-tune when changing the model's behavior is actually the business requirement.**

<img width="798" height="541" alt="Screenshot from 2026-09-27 06-52-35" src="https://github.com/user-attachments/assets/d9beb730-50e4-440c-ac73-c859518c5f40" />

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


