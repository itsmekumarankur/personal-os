# RAG — A 5-Minute AI Architect Guide

> **Goal:** Understand Retrieval-Augmented Generation (RAG), why it is used, how the complete pipeline works, and the architectural decisions that determine retrieval quality, latency, cost, and reliability.

---

## 1. What Is RAG?

**RAG = Retrieval-Augmented Generation.**

The basic idea:

> **Retrieve relevant external information first, then give that information to the LLM to generate an answer.**

Instead of:

```text
User
 |
 v
LLM
 |
 v
Answer
```

we use:

```text
User
 |
 v
Retriever
 |
 v
Relevant Knowledge
 |
 v
LLM
 |
 v
Answer
```

This allows an LLM application to use information that may not be contained in the model's training data.

---

# 2. Why Do We Need RAG?

Suppose your company has:

```text
Internal policies
Product documents
Technical documentation
Customer manuals
Regulatory documents
```

The base LLM does not automatically know your private documents.

RAG connects the model to external knowledge.

```text
             Company Knowledge
                    |
                    v
               RAG System
                    |
                    v
                   LLM
                    |
                    v
                 Answer
```

---

# 3. RAG Has Two Major Pipelines

This is one of the most important concepts.

```text
                RAG
                 |
        +--------+--------+
        |                 |
        v                 v
   Ingestion           Retrieval
   Pipeline             Pipeline
```

### Ingestion

Prepare knowledge.

### Retrieval

Find relevant knowledge at query time.

---

# 4. RAG Ingestion Pipeline

```text
Documents
    |
    v
Load / Parse
    |
    v
Clean
    |
    v
Chunk
    |
    v
Embedding Model
    |
    v
Vector Database
```

Example:

```text
100-page PDF
      |
      v
  500 chunks
      |
      v
  500 embeddings
      |
      v
  Vector DB
```

Metadata should also be stored.

```text
Chunk
 +
document_id
 +
page
 +
section
 +
timestamp
 +
access permissions
```

---

# 5. RAG Retrieval Pipeline

Now the user asks:

> "What is the process for redeeming this mutual fund?"

The application does:

```text
User Question
      |
      v
Query Processing
      |
      v
Query Embedding
      |
      v
Vector Search
      |
      v
Top-K Chunks
      |
      v
Optional Reranking
      |
      v
Context Builder
      |
      v
LLM
      |
      v
Answer
```

---

# 6. The Complete RAG Architecture

```text
                    DOCUMENTS
                        |
                        v
                  +-----------+
                  |  Parser   |
                  +-----------+
                        |
                        v
                  +-----------+
                  | Chunking  |
                  +-----------+
                        |
                        v
                  +-----------+
                  | Embedding |
                  +-----------+
                        |
                        v
                +----------------+
                |  Vector DB     |
                |                |
                | vectors        |
                | metadata       |
                +----------------+
                        ^
                        |
                      Query
                        |
                        v
                 Query Embedding
                        |
                        v
                +----------------+
                |   Retrieval    |
                +----------------+
                        |
                        v
                     Top-K
                        |
                        v
                  +-----------+
                  | Reranker  |
                  +-----------+
                        |
                        v
                 Prompt Builder
                        |
                        v
                      LLM
                        |
                        v
                     Answer
```

---

# 7. Retrieval Quality Is Critical

A powerful LLM cannot generate a correct answer if retrieval gives it the wrong information.

Think:

```text
Bad Retrieval
     |
     v
Wrong Context
     |
     v
LLM
     |
     v
Potentially Wrong Answer
```

Therefore:

> **RAG quality is often retrieval quality + generation quality, not just LLM quality.**

---

# 8. Top-K Retrieval

Suppose vector search returns:

```text
Chunk A  score 0.91
Chunk B  score 0.88
Chunk C  score 0.85
Chunk D  score 0.62
Chunk E  score 0.54
```

If:

```text
K = 3
```

we retrieve:

```text
A
B
C
```

But blindly choosing K is not enough.

Too few:

```text
Missing useful context
```

Too many:

```text
More noise
+
More tokens
+
More latency
+
More cost
```

---

# 9. Reranking

Initial vector retrieval may return several candidates.

A **reranker** can examine the query and candidate passages more deeply.

```text
Query
  |
  v
Vector Search
  |
  v
50 candidates
  |
  v
Reranker
  |
  v
Top 5
  |
  v
LLM
```

This creates a common two-stage retrieval architecture:

```text
Stage 1:
Fast retrieval
        |
        v
Candidate set

Stage 2:
More accurate reranking
        |
        v
Final context
```

This is a classic latency-vs-quality trade-off.

---

# 10. Hybrid RAG

Sometimes both keyword and semantic retrieval are useful.

```text
                  Query
                    |
          +---------+---------+
          |                   |
          v                   v
    Keyword Search      Vector Search
          |                   |
          +---------+---------+
                    |
                    v
               Fusion / Rank
                    |
                    v
                 Reranker
                    |
                    v
                 Context
                    |
                    v
                   LLM
```

This can help when documents contain:

- product IDs
- policy numbers
- names
- codes
- exact technical terms

---

# 11. RAG and Hallucination

RAG can reduce hallucination risk by providing relevant evidence, but it does **not automatically eliminate hallucinations**.

```text
RAG
 |
 +--> Better evidence
 |
 X--> Guaranteed truth
```

The LLM can still:

- misunderstand retrieved text
- combine unrelated passages
- make unsupported claims
- ignore context

Therefore production RAG should include evaluation for:

```text
Retrieval quality
+
Groundedness / faithfulness
+
Answer correctness
```

---

# 12. Citations and Grounded Answers

A strong RAG system can preserve source information.

```text
Retrieved Chunk
      |
      +--> document_id
      +--> page
      +--> section
      |
      v
     LLM
      |
      v
Answer + Citation
```

Example:

```text
Answer:
"The redemption process requires..."

Source:
Policy Document, Page 14
```

This makes the system easier to audit.

---

# 13. Access Control Is Critical

Suppose a user should not access:

```text
HR documents
Executive documents
Restricted financial data
```

The vector database should not simply return every semantically relevant document.

You need authorization-aware retrieval.

```text
User
 |
 v
Identity / Permissions
 |
 v
Retriever
 |
 +---- Metadata filter
 |
 v
Only authorized chunks
 |
 v
LLM
```

This is particularly important for enterprise RAG.

---

# 14. RAG vs Fine-Tuning

This is a common architecture question.

### RAG

```text
Knowledge at inference time
```

Best suited for:

- private documents
- frequently changing information
- citations
- current policies
- enterprise knowledge

### Fine-tuning

```text
Behavior learned into model parameters
```

Best suited for:

- style
- format
- task behavior
- specialized response patterns

Mental model:

```text
Need new knowledge?
       |
       v
      RAG

Need different behavior?
       |
       v
   Fine-tuning
```

They can be combined.

---

# 15. RAG Latency

A RAG request has multiple stages:

```text
User
 |
 |-- Query processing
 |
 |-- Embedding
 |
 |-- Vector search
 |
 |-- Reranking
 |
 |-- Prompt construction
 |
 |-- LLM inference
 |
 v
Answer
```

Therefore:

```text
Total latency =
retrieval latency
+
reranking latency
+
LLM latency
+
network / application overhead
```

This matters when setting P95/P99 SLOs.

---

# 16. RAG Cost

Cost can come from:

```text
Embedding
+
Vector DB
+
Reranker
+
LLM input tokens
+
LLM output tokens
+
Infrastructure
```

A common mistake is retrieving too much context.

```text
More chunks
    |
    v
More input tokens
    |
    v
Higher cost
```

Therefore:

> **Retrieval should optimize for relevance, not maximum context.**

---

# 17. RAG Evaluation

Do not evaluate only the final answer.

Evaluate each stage.

```text
             RAG Evaluation
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
   Retrieval     Context      Generation
    Quality      Quality       Quality
        |           |           |
      Recall      Relevance   Correctness
      Precision   Groundedness Faithfulness
```

Useful questions:

### Retrieval

```text
Did we retrieve the correct chunk?
```

### Context

```text
Did we provide enough useful evidence?
```

### Generation

```text
Did the answer correctly use that evidence?
```

---

# 18. Production RAG Architecture

```text
                         USER
                           |
                           v
                    +-------------+
                    | API Gateway |
                    +-------------+
                           |
                           v
                    +-------------+
                    | RAG Service |
                    +-------------+
                           |
              +------------+------------+
              |                         |
              v                         v
        Query Processing          Access Control
              |                         |
              +------------+------------+
                           |
                           v
                     Retriever
                           |
                +----------+----------+
                |                     |
                v                     v
           Vector Search        Keyword Search
                |                     |
                +----------+----------+
                           |
                           v
                       Reranker
                           |
                           v
                    Context Builder
                           |
                           v
                         LLM
                           |
                           v
                       Answer
                           |
                           v
                     Citations
```

---

# 19. Architect's Key Questions

When designing RAG, ask:

### Data

```text
Where does knowledge come from?
How frequently does it change?
```

### Chunking

```text
What is the chunk size?
Should chunks overlap?
Are sections preserved?
```

### Embeddings

```text
Which embedding model?
What dimensions?
What language coverage?
```

### Retrieval

```text
Vector, keyword, or hybrid?
What top-K?
What filters?
```

### Reranking

```text
Do we need a reranker?
What is the latency budget?
```

### Security

```text
Can retrieval enforce user permissions?
```

### Quality

```text
How do we measure retrieval recall?
How do we measure answer groundedness?
```

### Operations

```text
How are documents re-indexed?
How do we handle stale embeddings?
How do we monitor latency and cost?
```

---

# 20. The AI Architect's RAG Mental Model

Think in two pipelines:

```text
              RAG
               |
       +-------+-------+
       |               |
       v               v
 INGESTION          QUERY TIME
       |               |
 Documents           Question
       |               |
 Chunking          Embedding
       |               |
 Embedding         Retrieval
       |               |
 Vector DB         Reranking
                       |
                       v
                 Context Builder
                       |
                       v
                      LLM
                       |
                       v
                    Answer
```

---

## Final Mental Model

```text
               USER QUESTION
                      |
                      v
                +-----------+
                | RETRIEVE  |
                +-----------+
                      |
                      v
              Relevant Evidence
                      |
                      v
                +-----------+
                | AUGMENT   |
                +-----------+
                      |
                      v
                Context + Query
                      |
                      v
                +-----------+
                | GENERATE  |
                +-----------+
                      |
                      v
                    ANSWER
```

> **RAG is not simply "put documents into a vector database." It is an end-to-end retrieval architecture: ingestion, chunking, embeddings, retrieval, ranking, context construction, generation, security, and evaluation.**

For an AI Architect, the most important skill is understanding how each stage affects **retrieval quality, hallucination risk, latency, token cost, security, and scalability**.
