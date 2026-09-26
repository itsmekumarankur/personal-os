# Decoding Strategies — A 5-Minute AI Architect Guide

> **Goal:** Understand how an LLM turns probability distributions into actual tokens, and how greedy decoding, temperature, top-k, top-p, beam search, and related techniques change output behavior.

---

## 1. The Model Does Not Directly Output Text

An LLM produces **logits** for possible next tokens.

Example:

```text
Prompt:
"The capital of India is"

             LLM
              |
              v
            Logits
              |
              v
          Probability
              |
      +-------+-------+
      |       |       |
    Delhi   Mumbai  Chennai
    0.91     0.03    0.01
```

The decoding strategy decides:

> **Which token should we actually choose?**

---

# 2. Greedy Decoding

Greedy decoding chooses the highest-probability token.

```text
Delhi       0.91  <--- choose
Mumbai      0.03
Chennai     0.01
```

Algorithm:

```text
Choose argmax(probability)
```

Advantages:

- simple
- deterministic
- fast

Disadvantages:

- can be repetitive
- can produce locally optimal but globally poor sequences
- less diverse

---

# 3. Temperature

Temperature modifies the probability distribution.

Conceptually:

```text
Low temperature
       |
       v
Sharper distribution
       |
       v
More deterministic
```

```text
High temperature
       |
       v
Flatter distribution
       |
       v
More diverse/random
```

Example:

```text
Temperature LOW

Delhi      ██████████
Mumbai     █
Chennai   


Temperature HIGH

Delhi      █████
Mumbai     ███
Chennai    ██
```

A simplified mathematical form is:

```text
softmax(logits / T)
```

where `T` is temperature.

Important:

> Temperature changes sampling probabilities; it does not add new knowledge to the model.

---

# 4. Top-k Sampling

Top-k limits sampling to the k most probable tokens.

Suppose:

```text
Delhi       0.45
Mumbai      0.20
Chennai     0.15
Bangalore   0.10
Pune        0.05
XYZ         0.05
```

With:

```text
top-k = 3
```

Only:

```text
Delhi
Mumbai
Chennai
```

remain candidates.

```text
All tokens
    |
    v
Rank by probability
    |
    v
Keep top K
    |
    v
Sample
```

This removes very unlikely candidates.

---

# 5. Top-p / Nucleus Sampling

Top-p does not use a fixed number of tokens.

Instead, it selects the smallest set whose cumulative probability reaches `p`.

Example:

```text
Delhi       0.45
Mumbai      0.20
Chennai     0.15
Bangalore   0.10
Pune        0.05
Others      0.05
```

If:

```text
top-p = 0.80
```

then:

```text
0.45 + 0.20 + 0.15 = 0.80
```

Candidate set:

```text
Delhi
Mumbai
Chennai
```

Conceptually:

```text
Probability distribution
        |
        v
Sort tokens
        |
        v
Accumulate probability
        |
        v
Stop at p
        |
        v
Sample
```

Top-p adapts the candidate set to the distribution.

---

# 6. Greedy vs Sampling

```text
                    Decoding
                       |
              +--------+--------+
              |                 |
           Greedy            Sampling
              |                 |
          Highest P        Probability-based
                                |
                    +-----------+-----------+
                    |                       |
                  Top-k                   Top-p
```

Think:

```text
Greedy
= "Always choose the most likely."

Sampling
= "Choose among plausible candidates."
```

---

# 7. Beam Search

Beam search keeps several candidate sequences instead of only one.

Suppose:

```text
Prompt
 |
 +--> A
 +--> B
 +--> C
```

Then each candidate is expanded:

```text
          Start
        /   |   \
       A    B    C
      / \  / \  / \
    A1 A2 B1 B2 C1 C2
```

Only the best `N` candidates are retained.

```text
Beam width = 3

Candidate 1 ----\
Candidate 2 -----+--> Keep best 3
Candidate 3 ----/
```

Beam search has historically been useful in tasks such as machine translation, but modern open-ended LLM chat commonly relies more on sampling or greedy-style decoding.

---

# 8. Repetition Penalties

A model can sometimes repeat phrases.

```text
"The system is fast and the system is fast
and the system is fast..."
```

Decoding can apply penalties to discourage repeated tokens or sequences.

Conceptually:

```text
Token already used frequently
          |
          v
Reduce its score
          |
          v
Alternative token becomes more likely
```

Common controls include:

- repetition penalty
- frequency penalty
- presence penalty

Exact behavior varies by inference implementation.

---

# 9. Stop Sequences

Sometimes generation should stop when a particular sequence appears.

Example:

```text
Generate SQL
     |
     v
SELECT ...
     |
     v
;
     |
     v
STOP
```

Applications may specify:

```text
stop = ["</answer>"]
```

Then:

```text
Generated output
      |
      v
Contains stop sequence?
      |
     YES
      |
      v
Stop generation
```

This is useful for structured application workflows.

---

# 10. Structured / Constrained Decoding

Sometimes free-form generation is not enough.

Suppose an API requires:

```json
{
  "name": "...",
  "age": 40
}
```

The application may need the model to follow a schema.

Conceptually:

```text
LLM probabilities
       |
       v
Constraint / Grammar
       |
       v
Valid tokens only
       |
       v
Generated output
```

This is useful for:

- JSON
- SQL
- function calls
- tool arguments
- domain-specific grammars

---

# 11. Decoding and Temperature Together

A common production setup might be:

```text
Temperature
     |
     v
Modify probability distribution
     |
     v
Top-p / Top-k filtering
     |
     v
Sample token
     |
     v
Repeat
```

For deterministic applications:

```text
Low / zero temperature
+
Greedy or constrained decoding
```

For creative generation:

```text
Higher temperature
+
Top-p sampling
```

The right setting depends on the task.

---

# 12. Decoding and Reliability

Important distinction:

```text
Model quality
      !=
Decoding strategy
```

Decoding can influence output behavior, but it cannot fundamentally fix:

- missing knowledge
- bad retrieval
- incorrect reasoning
- poor model training
- broken tools

Therefore:

```text
Bad model
   |
   +--> Change decoding
   |
   X
```

may not solve the underlying problem.

---

# 13. Architect's Cheat Sheet

| Strategy | Basic idea |
|---|---|
| Greedy | Pick highest-probability token |
| Temperature | Control distribution sharpness |
| Top-k | Sample from k highest-probability tokens |
| Top-p | Sample from smallest probability mass reaching p |
| Beam Search | Maintain multiple candidate sequences |
| Repetition Penalty | Reduce repeated generation |
| Stop Sequence | End generation on specified sequence |
| Constrained Decoding | Restrict output to valid structures |

---

## Final Mental Model

```text
                  LLM
                   |
                   v
                Logits
                   |
                   v
             Probability
                   |
                   v
            Decoding Layer
                   |
       +-----------+-----------+
       |           |           |
    Greedy      Top-k       Top-p
       |           |           |
       +-----------+-----------+
                   |
                   v
                Token
                   |
                   v
              Repeat
```

> **Decoding is the policy that turns the model's probability distribution into an actual sequence of tokens.**
