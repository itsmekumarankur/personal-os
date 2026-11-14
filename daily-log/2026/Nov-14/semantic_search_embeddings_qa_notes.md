# Semantic Search and Embeddings --- Q&A Notes

## Q1. What is the purpose of this example?

**Crux:** Convert text into numerical vectors called **embeddings**,
then find the document that is most relevant to a query based on
meaning.

This is the basic idea behind **semantic search**.

### How does it work?

1.  **Load an embedding model:** Load `all-MiniLM-L6-v2`.
2.  **Create document embeddings:** Convert each document into a
    numerical vector.
3.  **Create a query embedding:** Convert the query
    `"What animals make good pets?"` into a vector.
4.  **Calculate similarity:** Compare the query vector with each
    document vector.
5.  **Find the best match:** The document with the highest similarity
    score is the most semantically relevant.

### What is the real-world application?

This is a fundamental concept behind: - Semantic search -
Retrieval-Augmented Generation (RAG) - Document similarity -
Recommendation systems

**One-line takeaway:** We are enabling machines to find relevant
information based on meaning rather than exact keyword matching.

------------------------------------------------------------------------

## Q2. What does `tensor([[0.4816]])` mean?

It means the calculated similarity score is **0.4816**.

Breakdown:

-   `tensor` --- A PyTorch data structure used to store numerical
    values.
-   `[[0.4816]]` --- The score represented as a two-dimensional tensor
    (one row and one column).
-   `0.4816` --- The similarity value between the query embedding and
    the document embedding.

**Important:** A score of `0.4816` is not a 48.16% probability or
confidence level. It is a similarity score. In general, a higher score
indicates greater semantic similarity when comparing results produced by
the same similarity method and model.

------------------------------------------------------------------------

## Q3. What is a Sequence Transformer?

**Meaning:** A Transformer is a neural-network architecture that
processes a sequence of tokens and uses attention to learn relationships
between them.

Example:

> "The bank approved my loan."

The meaning of a word such as `bank` depends on its surrounding context.
A Transformer uses the context of the sequence to build contextual
representations.

### How does it work?

1.  Takes a sequence of tokens (pieces of text).
2.  Uses **self-attention** to model relationships between tokens.
3.  Produces contextual representations of the tokens.

**Remember:** Transformer is an underlying architecture used by models
such as BERT and GPT. Different Transformer models are designed for
different tasks.

------------------------------------------------------------------------

## Q4. What is the Sentence Transformers library?

**Meaning:** Sentence Transformers is a Python library that makes it
easy to generate useful embeddings for sentences and paragraphs.

Example:

``` python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode("What animals make good pets?")
```

The `encode()` method converts the input sentence into a numerical
vector that represents its semantic meaning.

### Why do we use it?

-   Semantic search
-   Sentence and document similarity
-   RAG applications
-   Clustering
-   Recommendation systems

**Think of it as:** A ready-to-use Python library for generating
sentence embeddings.

------------------------------------------------------------------------

## Q5. What does `EMBEDDING_MODEL = "all-MiniLM-L6-v2"` mean?

It identifies the specific pretrained model that will be loaded to
generate embeddings.

### Decode the model name

  Part       Meaning
  ---------- --------------------------------------------
  `all`      A general-purpose sentence-embedding model
  `MiniLM`   A smaller, lightweight Transformer model
  `L6`       The model has 6 Transformer layers
  `v2`       Version 2

### Why use this model?

-   Lightweight and relatively fast.
-   Produces **384-dimensional embeddings**.
-   Useful for semantic search and similarity tasks.
-   Requires fewer computational resources than many larger models.

------------------------------------------------------------------------

## Q6. How do the Transformer, Sentence Transformers library, and embedding model fit together?

Think of them as three different layers:

1.  **Transformer architecture** --- The underlying neural-network
    architecture.
2.  **Sentence Transformers library** --- The Python library used to
    generate sentence embeddings.
3.  **`all-MiniLM-L6-v2`** --- The specific pretrained model loaded
    through the library.
4.  **384-dimensional vector** --- The numerical embedding produced for
    each input sentence.

### Memory map

``` text
Transformer Architecture
        |
        v
Sentence Transformers Library
        |
        v
all-MiniLM-L6-v2 Model
        |
        v
384-dimensional Embedding
```

**Key distinction:**

-   Transformer = Architecture
-   Sentence Transformers = Python library
-   `all-MiniLM-L6-v2` = Pretrained model

Together, they convert text into embeddings that can be compared for
semantic similarity.

------------------------------------------------------------------------


## **Q7.  Sequence Transformer Vs Sentence Transformer?**

| Sequence Transformer                                                  | Sentence Transformer                                                            |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Processes a sequence of tokens and models relationships between them. | Uses a Transformer-based model designed to produce sentence or text embeddings. |
| Produces contextual representations of tokens or sequences.           | Produces a fixed-size vector for a sentence or text passage.                    |
| Examples: BERT and GPT.                                               | Example: `all-MiniLM-L6-v2`.                                                    |
| Used in language understanding and language generation tasks.         | Commonly used for semantic search, similarity, and RAG retrieval.               |
  -----------------------------------------------------------------------

### In simple words

-   **Sequence Transformer:** Understands relationships and context
    across tokens.
-   **Sentence Transformer:** Converts a sentence or passage into a
    numerical vector representing its meaning.

**Remember:** Sentence Transformers are built using Transformer-based
models, with an approach designed to create useful sentence embeddings.

------------------------------------------------------------------------

## Final recap

> **Semantic search = Embed the documents + Embed the query + Compare
> the vectors + Retrieve the closest match.**

The central idea is to search by **meaning**, not just by matching exact
words.
