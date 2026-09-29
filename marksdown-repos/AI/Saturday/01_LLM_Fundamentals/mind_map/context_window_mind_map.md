# 🧠 Context Window — Mind Map

> **Mental Model:** `Context Window = LLM's temporary working area`

```text
Context Window
 ├── System Prompt
 ├── Conversation
 ├── RAG Documents
 ├── Tool Results
 ├── User Request
 └── Generated Tokens*
```

## 1. Context ≠ Model Memory

```text
Training   → Model Weights → Learned knowledge
Inference  → Context Window → Temporary working information
```

Prompting information does **not** permanently teach the model.

## 2. Why Context Matters

```text
Context ↑
 ├── Input processing ↑
 ├── KV Cache ↑
 ├── GPU memory pressure ↑
 ├── Latency ↑
 └── Cost ↑
```

> `Input tokens + Output tokens <= Context capacity`

## 3. RAG

```text
Question
   ↓
Retrieval
   ↓
Relevant chunks
   ↓
LLM Context
   ↓
Answer
```

> Don't dump the whole database. **Retrieve what is useful.**

## 4. Context Engineering

> **"What is the minimum useful context required to solve this task?"**

```text
Retrieve → Rank → Compress → Useful Context → LLM
```

## 5. Context Management

```text
Large Context
 ├── Summarization
 ├── Sliding Window
 ├── Retrieval
 ├── External Memory
 └── Relevance Filtering
          ↓
    Compact Context
```

## 6. Agentic Systems

Many tool calls can rapidly grow context.

Use:
- Tool-result filtering
- Summarization
- State management
- External memory
- Context pruning

## ⚡ 30-Second Recall

> **Context Window = temporary working memory.**
>
> **Good AI architecture = right information, not maximum information.**

### 🎯 Architect Question
> **"What information does the model actually need right now?"**
