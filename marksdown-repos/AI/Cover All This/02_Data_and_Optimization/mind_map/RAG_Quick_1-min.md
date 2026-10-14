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


> **Leadership question:** “Are we measuring retrieval quality separately from LLM quality?”
