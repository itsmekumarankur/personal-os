---
tags: [ai, llms, rag, retrieval, langchain]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/llm-engineering-bootcamp/day7, architect-kit/rag-notes, daily-learnings/2026-06-29]
---

# RAG — Retrieval-Augmented Generation

Answers the question: when should you give the model external knowledge instead of baking it into weights?

## Core Idea

Instead of retraining the model when your data changes, you retrieve relevant chunks at query time and inject them into the context window. The model reasons over what you give it, not what it learned during training.

## When RAG Wins

- Data changes frequently — compliance rules, policy docs, rates, live inventory
- You need source citations — audit trails, regulated environments (BFSI is the canonical case)
- You want to avoid retraining cost every time the data shifts
- The knowledge base is large and varied — vector search is cheaper than parametric storage

## When Fine-Tuning Wins

- Narrow, stable task with a fixed label set (e.g., classify loan applications into 3 categories)
- You need consistent tone/format across high-volume outputs
- Latency matters more than freshness — inference on a tuned model is faster than retrieve + generate

## Production Architecture

```
Query → Embed → Vector Search → Top-K chunks → Inject into prompt → LLM → Answer
```

Key choices at each step:
- **Embedding model**: OpenAI ada-002, HuggingFace BAAI/bge, or domain-specific
- **Vector store**: Pinecone, Chroma, Weaviate, pgvector (for Postgres-native)
- **Chunk size**: 256–512 tokens is typical. Smaller chunks = more precise retrieval, less context. Larger = more coherent but noisier.
- **Top-K**: Usually 3–5. More isn't always better — context bloat degrades reasoning.

## BFSI Application (from idfc-coder / Optimus context)

For KYC and demat workflows: compliance documents change too often to bake into model weights. RAG is the default. You get:
- Always-current policy retrieval
- Citable source for regulators
- No retraining cost when SEBI/RBI updates guidelines

## Tooling Used

- LangChain (day7 notebook): `VectorstoreIndexCreator`, `RetrievalQA`
- Chroma as local vector store in labs
- HuggingFace datasets for test corpora

## Related

- [[learning/ai-llms/fine-tuning-lora-peft]] — The alternative to RAG when task is stable
- [[learning/ai-llms/llm-engineering-bootcamp]] — Day 7 of the bootcamp
- [[learning/system-design/databases]] — Vector databases are storage systems
