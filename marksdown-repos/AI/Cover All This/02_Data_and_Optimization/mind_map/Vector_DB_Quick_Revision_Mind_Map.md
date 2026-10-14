# Vector Databases — Quick Revision Mind Map

> **Core rule:** A Vector DB helps find semantically similar content. It is one retrieval component—not the whole RAG system.

```text
                    VECTOR DATABASE
                           |
                    Semantic retrieval
                           |
            +--------------+--------------+
            |              |              |
        1. EMBEDDING    2. SEARCH       3. METADATA
            |              |              |
        Text becomes     Query vector    Document ID
        numeric vector   compared with   Chunk ID
            |            stored vectors  Source / date
        Similar meaning       |           Department
        -> nearby vectors    Top-K        Permissions
                             candidates       |
            |                   |        Filter results
            +-------------------+-------------+
                                |
                       Relevant document chunks
                                |
                         Used by RAG / LLM

         +----------------------+----------------------+
         |                      |                      |
     4. INDEXES              5. METRICS             6. DESIGN
         |                      |                      |
     ANN search              Recall@K               Embedding model
     e.g. HNSW               Precision@K            Distance metric
     Faster than             Latency                Index choice
     exhaustive search       Recall/quality tradeoff Storage + cost
     May be approximate      Filter effectiveness    Update strategy
```

## How it works

1. Split documents into chunks.
2. Convert each chunk into an embedding vector.
3. Store vectors alongside useful metadata.
4. Convert the user's query into a vector using a compatible embedding model.
5. Search for nearby vectors; apply relevant metadata and permission filters.
6. Return top-ranked chunks to the RAG pipeline.

## Similarity concepts

- **Cosine similarity:** compares vector direction/angle.
- **Dot product:** measures alignment and magnitude relationship.
- **Euclidean distance:** measures straight-line distance.
- Use a metric compatible with the embedding model and its training assumptions.

## Vector DB vs relational DB

| Relational database | Vector database |
|---|---|
| Exact filters and structured records | Semantic similarity search |
| SQL, joins, transactions | Vector queries and ANN indexes |
| Business/customer data | Embeddings and retrieval metadata |

They often work **together**: SQL stores business records; the Vector DB retrieves semantically relevant content.

## Architect checklist

- Is semantic search actually required?
- Are embeddings generated with the right model?
- Are exact terms better handled with hybrid keyword + vector search?
- Are permissions enforced—not merely stored as metadata?
- Is recall acceptable at the required latency and cost?
- How are changed or deleted source documents reflected in the index?

> **Leadership question:** “How will we ensure the AI retrieves the right information—not just information that looks similar?”
