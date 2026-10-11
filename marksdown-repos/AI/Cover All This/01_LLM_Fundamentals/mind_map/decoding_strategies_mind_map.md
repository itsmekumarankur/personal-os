# 🧠 Decoding Strategies — Mind Map

> **Mental Model:** `LLM → Logits → Probabilities → Decoding → Next Token`

## 1. Greedy Decoding

```text
Choose highest probability
        ↓
      argmax
```

**Pros:** Simple, fast, deterministic  
**Cons:** Repetitive, less diverse, locally optimal

> **Greedy = "Always choose the most likely."**

## 2. Temperature

```text
Temperature ↓ → Sharper distribution → More deterministic

Temperature ↑ → Flatter distribution → More diverse/random
```

Concept:

```text
softmax(logits / T)
```

> Temperature changes **sampling behavior**, not model knowledge.

## 3. Top-k

```text
All tokens
   ↓
Rank by probability
   ↓
Keep top K
   ↓
Sample
```

> **Top-k = fixed number of candidates.**

## 4. Top-p / Nucleus

```text
Sort tokens
   ↓
Accumulate probability
   ↓
Stop when cumulative P ≥ p
   ↓
Sample
```

> **Top-p = variable number of candidates.**

## 5. Greedy vs Sampling

```text
                 DECODING
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
       GREEDY              SAMPLING
          │                   │
     Highest P          Probability-based
                              │
                       ┌──────┴──────┐
                       ↓             ↓
                     Top-k         Top-p
                   Fixed K      Cumulative P
```

## Quick Comparison

| Strategy | Main idea | Behavior |
|---|---|---|
| Greedy | Highest probability | Deterministic |
| Temperature | Reshape distribution | Controls randomness |
| Top-k | Keep K candidates | Fixed candidate pool |
| Top-p | Keep probability mass p | Adaptive candidate pool |

## ⚡ 30-Second Recall

> **Greedy = highest**
>
> **Temperature = sharpness**
>
> **Top-k = fixed K**
>
> **Top-p = cumulative probability**
>
> **Sampling = controlled diversity**

### 🎯 Architect Question
> **"Do I want deterministic output, or controlled diversity?"**
