# 🧠 Transformers — Mind Map

> **Mental Model:** `Tokens → Embeddings → Attention → FFN → Repeated Blocks → Output`

## 1. What Is a Transformer?

A neural-network architecture designed to understand relationships between tokens.

```text
Input Text
   ↓
Tokenizer
   ↓
Token IDs
   ↓
Embeddings + Position
   ↓
Transformer Blocks
   ↓
Output / Next Token
```

> **Transformer = relationship engine between tokens.**

## 2. Self-Attention

Question:

> **"For this token, which other tokens are important?"**

```text
Input Tokens
     ↓
Attention scores
     ↓
Relevant tokens get higher weight
     ↓
Context-aware representation
```

## 3. Q, K, V

```text
Input X
 ├──→ Q = Query
 ├──→ K = Key
 └──→ V = Value
```

Easy mental model:

| Component | Question |
|---|---|
| Query | What am I looking for? |
| Key | What information do I contain? |
| Value | What information should I provide? |

Pipeline:

```text
Q
 ↓
Compare with K
 ↓
Similarity scores
 ↓
Scale
 ↓
Softmax
 ↓
Attention weights
 ↓
Weighted sum of V
 ↓
New representation
```

Core equation:

```text
Attention(Q,K,V)
= softmax(QKᵀ / √dₖ)V
```

## 4. Why Softmax?

```text
Raw scores
   ↓
Softmax
   ↓
Normalized attention weights
   ↓
Weights sum ≈ 1
```

## 5. Why Divide by √dₖ?

```text
Large dimensions
      ↓
Large dot products
      ↓
Very sharp softmax
      ↓
Poor training behavior
```

Scaling keeps scores in a useful range.

## 6. Multi-Head Attention

```text
Input
 ├──→ Head 1
 ├──→ Head 2
 ├──→ Head 3
 └──→ Head N
        ↓
    Concatenate
        ↓
    Linear Layer
        ↓
      Output
```

> Multiple heads learn different relationship patterns.

## 7. Transformer Block

```text
Input
  ↓
LayerNorm
  ↓
Self-Attention
  ↓
Residual
  ↓
LayerNorm
  ↓
FFN
  ↓
Residual
  ↓
Output
```

## 8. Attention vs FFN

```text
Attention
= "Which other tokens matter to me?"

FFN
= "Given what I now know,
   how should I transform this information?"
```

## 9. Position Matters

```text
"dog bites man"
      ≠
"man bites dog"
```

Therefore:

```text
Token Meaning + Position Information
              ↓
    Context-aware representation
```

Modern LLMs commonly use **RoPE** for positional information.

## 10. Encoder vs Decoder

```text
Original Transformer
       │
   ┌───┴────┐
   ↓        ↓
Encoder   Decoder
```

**Encoder:** builds contextual representations; common in BERT-style models.

**Decoder:** generates output tokens autoregressively; common in GPT-style LLMs.

## ⚡ 30-Second Recall

```text
TRANSFORMER
    ↓
SELF-ATTENTION
    ↓
Q + K + V
    ↓
Similarity
    ↓
Softmax
    ↓
Weighted V
    ↓
Context-aware representation
    ↓
FFN
    ↓
Repeated Blocks
```

### 🔥 7 Things to Remember

> **1. Transformer = relationship engine between tokens.**
>
> **2. Attention asks: "Which tokens matter?"**
>
> **3. Q = looking for, K = what I contain, V = what I provide.**
>
> **4. Multi-head = multiple relationship patterns.**
>
> **5. FFN transforms the token representation after attention.**
>
> **6. Position information is required because order matters.**
>
> **7. Decoder models generate the next token autoregressively.**

### 🎯 Architect Question
> **"What part of our LLM workload is driving performance and infrastructure cost — model size, context, attention, or serving pattern?"**
