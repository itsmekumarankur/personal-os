# RAG — Quick Revision Mind Map

> **Core rule:** A better LLM cannot fix bad information. Measure retrieval quality separately from answer quality.

```text
                    RAG
       Retrieval-Augmented Generation
                    |
          Retrieve evidence first
                    |
           Give evidence to LLM
                    |
              Grounded answer
                    |
      +-------------+-------------+
      |                           |
  1. INGESTION                2. RETRIEVAL
      |                           |
  Documents                   User question
      |                           |
  Parse + clean               Query processing
      |                           |
  Chunk                       Query embedding
      |                           |
  Create embeddings           Vector / hybrid search
      |                           |
  Store vectors + metadata    Top-K candidates
      |                           |
  Update when source changes  Optional reranker
                                  |
                              Context builder
                                  |
                                  LLM
                                  |
                            Answer + citations

      +-------------+-------------+-------------+
      |             |             |             |
   3. QUALITY     4. CONTROL    5. METRICS    6. RISKS
      |             |             |             |
  Relevant chunks Permissions   Recall@K      Wrong retrieval
  Good chunking   ACL filters    Precision@K   Stale documents
  Right Top-K     Tenant scope   Groundedness  Too much context
  Reranking       Prompt safety  Correctness   Hallucinations
  Hybrid search   Citations      Latency/cost  Data leakage
```

## RAG in one example

Question: “What is the current process for redeeming a mutual fund?”

1. Find the latest authorized policy chunks.
2. Filter out documents the user cannot access.
3. Rank the most relevant evidence.
4. Send only useful context to the LLM.
5. Generate an answer with source references.
6. Evaluate whether the answer is supported by the sources.

## Key trade-offs

- **Top-K too low:** may miss required evidence.
- **Top-K too high:** adds noise, tokens, latency, and cost.
- **Vector search:** finds semantic similarity.
- **Keyword search:** helps with exact policy numbers, IDs, and codes.
- **Hybrid retrieval:** combines both.
- **Reranking:** improves the ordering of retrieved candidates, at extra cost/latency.
- **RAG reduces hallucination risk; it does not guarantee truth.**

## Architect checklist

- Are source documents current and correctly chunked?
- Are metadata and access permissions applied before context reaches the model?
- Do retrieval metrics and answer metrics have separate tests?
- Can the answer cite its source?
- What happens when evidence is missing or conflicting?

> **Leadership question:** “Are we measuring retrieval quality separately from LLM quality?”
