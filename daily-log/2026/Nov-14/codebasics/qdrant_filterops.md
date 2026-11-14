# Qdrant Filtering: Exact Match and Boolean Conditions

> **Architect's mental model:** Qdrant combines semantic vector search with metadata filtering. The vector query finds documents by meaning; metadata filters restrict which documents are eligible to be returned.

## 1. Why filtering is needed

Imagine a Qdrant collection containing 1,000 documents. Each point can contain:

- **Vector:** numerical representation (embedding) of the document's meaning.
- **Payload:** metadata and other stored fields, such as `text`, `category`, `role`, `department`, or `access`.

Example dataset:

| Document text | category | role |
|---|---|---|
| Computers are useful for learning | technology | public |
| AI is changing software development | technology | public |
| Stars are massive objects in space | science | public |
| Black holes have strong gravity | science | private |
| Python is a programming language | technology | private |

Think of the collection like a database table:
- `text` is the document content.
- `category` and `role` are metadata fields.
- `vector` is the embedding used for semantic similarity.

**Problem:** A user asks, “What are computers used for?” You may want results only from the `technology` category. A metadata filter expresses that restriction.

## 2. Exact-match filtering: complete example

```python
from qdrant_client import models

results = client.query_points(
    collection_name="my_collection",
    query=model.encode("computers and learning").tolist(),
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="category",
                match=models.MatchValue(value="technology")
            )
        ]
    ),
    limit=3
)

for r in results.points:
    print(f"Score: {r.score:.4f} | {r.payload['text'][:60]}")
```

> Depending on the imports in your notebook, you may have imported `Filter`, `FieldCondition`, and `MatchValue` directly. In that case, you can omit the `models.` prefix.

### Line-by-line explanation

| Code | Meaning |
|---|---|
| `client.query_points(...)` | Ask Qdrant to search a collection. |
| `collection_name="my_collection"` | Select the collection to search. |
| `model.encode("computers and learning")` | Convert the search sentence into an embedding vector. |
| `.tolist()` | Convert the embedding array into a regular Python list. |
| `query_filter=...` | Supply metadata conditions that restrict eligible points. |
| `Filter(...)` | Group one or more filter conditions. |
| `must=[...]` | Conditions in this list must be satisfied. |
| `FieldCondition(...)` | Define a condition on a payload field. |
| `key="category"` | Inspect the `category` payload field. |
| `match=MatchValue(value="technology")` | Require an exact value match for `technology`. |
| `limit=3` | Return at most three matching points. |

### Translate the code into plain English

“Search for documents related in meaning to **computers and learning**, but only consider documents whose `category` field is exactly **technology**. Return up to three results.”

### Reading the output

```python
for r in results.points:
    print(f"Score: {r.score:.4f} | {r.payload['text'][:60]}")
```

- `results.points`: the points returned by Qdrant.
- `r.score`: the vector-search score for that result. Its interpretation and direction depend on the configured distance metric.
- `r.payload['text']`: the stored text field in the point's payload.
- `[:60]`: display only the first 60 characters of the text.

The score is a relevance/similarity measure, **not a probability** that the result is correct.

## 3. Boolean filter operators: MUST, SHOULD, MUST_NOT

These operators express logical conditions.

| Qdrant operator | Familiar logic | Meaning |
|---|---|---|
| `must` | AND | Every condition in this list must match. |
| `should` | OR | At least one condition must match when `should` is used on its own. |
| `must_not` | NOT | A point matching a condition in this list is excluded. |

### 3.1 MUST = AND

```python
query_filter=models.Filter(
    must=[
        models.FieldCondition(
            key="category",
            match=models.MatchValue(value="science")
        ),
        models.FieldCondition(
            key="role",
            match=models.MatchValue(value="public")
        )
    ]
)
```

Plain English:

`category = science AND role = public`

Both conditions must be true.

### 3.2 SHOULD = OR

```python
query_filter=models.Filter(
    should=[
        models.FieldCondition(
            key="category",
            match=models.MatchValue(value="science")
        ),
        models.FieldCondition(
            key="category",
            match=models.MatchValue(value="technology")
        )
    ]
)
```

Plain English:

`category = science OR category = technology`

Either condition can match when `should` is used alone.

**Important nuance:** When `should` is combined with `must` or `must_not`, it is generally optional unless you explicitly set `min_should`. Use `min_should` when you need to require a minimum number of `should` conditions to match. Check the syntax supported by the Qdrant client version in use.

### 3.3 MUST_NOT = NOT

```python
query_filter=models.Filter(
    must_not=[
        models.FieldCondition(
            key="role",
            match=models.MatchValue(value="private")
        )
    ]
)
```

Plain English:

Exclude documents where `role = private`.

This is equivalent to the idea of:

`role != private`

It excludes points matching the specified condition.

## 4. Understand the second example

```python
results = client.query_points(
    collection_name="my_collection",
    query=model.encode("astronomy and stars").tolist(),
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="science")
            ),
            FieldCondition(
                key="role",
                match=MatchValue(value="public")
            )
        ]
    ),
    limit=5
)

for r in results.points:
    print(f"Score: {r.score:.4f} | {r.payload['text'][:60]}")
```

Plain-English translation:

“Search for documents related to **astronomy and stars**. Only return documents for which both of these statements are true:

1. `category` is `science`.
2. `role` is `public`.

Return up to five results.”

Using the sample dataset:

| Document | category | role | Passes filter? |
|---|---|---|---|
| Computers are useful for learning | technology | public | No |
| AI is changing software development | technology | public | No |
| Stars are massive objects in space | science | public | **Yes** |
| Black holes have strong gravity | science | private | No |
| Python is a programming language | technology | private | No |

Only the “Stars are massive objects in space” point passes both conditions in this small example. Qdrant then uses vector similarity to rank the eligible points.

## 5. The complete search mental model

A useful conceptual view of a filtered vector query:

```text
                 USER QUERY
          "astronomy and stars"
                    |
                    v
           EMBEDDING MODEL
          Convert text to vector
                    |
                    v
             QDRANT QUERY
       Collection + vector + filter
                    |
                    v
          METADATA CONDITIONS
       category = science
          AND role = public
                    |
                    v
         ELIGIBLE POINTS / SEARCH
      Find relevant vectors subject
          to the filter conditions
                    |
                    v
          SIMILARITY RANKING
                    |
                    v
             TOP 5 RESULTS
```

This is a **conceptual model**, not a guarantee that Qdrant executes filtering and vector search as separate sequential stages. Qdrant integrates filtering into its search process.

## 6. Filtering in real-world applications

Imagine building a banking knowledge assistant. The collection contains:

| Document | department | access |
|---|---|---|
| Mutual Fund Policy | Wealth | Public |
| Loan Policy | Lending | Public |
| Internal Audit Report | Risk | Restricted |
| Payment API Documentation | Payments | Public |
| Employee Salary Details | HR | Restricted |

Possible requirements:

| Business requirement | Filter logic |
|---|---|
| Search only Wealth documents | `department = Wealth` |
| Search only public documents | `access = Public` |
| Exclude restricted documents | `must_not: access = Restricted` |
| Search Wealth AND Public | `must: Wealth + Public` |
| Search Wealth OR Lending | `should: Wealth + Lending` |

### Where this is useful

- **Multi-tenant applications:** restrict results to the current tenant.
- **Role-based document access:** restrict results according to the user's permissions.
- **Department-specific knowledge bases:** search only the relevant department's content.
- **Product-specific search:** restrict results to a product or product family.
- **Document-type filtering:** search policies, FAQs, manuals, or API documentation.
- **Date-based search:** restrict results to a date range.

### Security and architecture warning

Do not rely solely on a filter supplied by the frontend for authorization.

A safer design is:

1. Authenticate the user in the backend.
2. Resolve the user's tenant, role, and permissions from trusted server-side data.
3. Construct the Qdrant filter on the backend.
4. Execute the search using that filter.
5. Return only authorized results.

Metadata filtering is a search capability; it does not replace application-level authorization.

## 7. Semantic search vs exact-match filtering

These are two different operations that work together.

| Semantic vector search | Exact-match metadata filtering |
|---|---|
| Finds content by meaning | Checks a specific payload value |
| Uses embeddings/vectors | Uses metadata fields and conditions |
| Finds semantically relevant documents | Restricts which documents are eligible |
| Example: “computers and learning” | Example: `category = technology` |

Example semantic query:

```python
query = model.encode("computers and learning").tolist()
```

This represents the meaning of the search sentence as a vector.

Example metadata condition:

```python
FieldCondition(
    key="category",
    match=MatchValue(value="technology")
)
```

This checks whether the payload field `category` has the exact value `technology`.

**Remember:** Vector search answers “Which documents are relevant?” Metadata filtering answers “Which documents satisfy my conditions?”

## 8. More Qdrant filter types to learn

Exact matching is only one kind of filtering. Other useful Qdrant payload conditions include:

| Filter type | Simple purpose |
|---|---|
| `MatchValue` | Match one exact value. |
| `MatchAny` | Match any value from a supplied list. |
| `MatchExcept` | Match values except those in a supplied list. |
| `Range` | Match numeric values within a range. |
| `DatetimeRange` | Match dates/times within a range. |
| `IsEmpty` | Check whether a payload field is missing or empty. |
| `IsNull` | Check whether a payload field is explicitly null. |
| `Nested` | Filter objects inside nested payload structures. |

Exact class names and supported payload types can vary by client/server version. Consult the Qdrant documentation for the version deployed.

## 9. Quick knowledge check

Try answering these questions:

1. You want `category = science` AND `role = public`. Which operator should you use?
   - Answer: `must`

2. You want documents from either `science` OR `technology`. Which operator can you use on its own?
   - Answer: `should`

3. You want to exclude documents where `role = private`. Which operator should you use?
   - Answer: `must_not`

4. Which part converts the user's sentence into a vector?
   - Answer: `model.encode(...)`

5. Which part specifies the metadata condition?
   - Answer: `query_filter=Filter(...)`

6. What does `limit=5` mean?
   - Answer: Return at most five points.

7. Does a vector similarity score mean the result is guaranteed to be correct?
   - Answer: No. It is a similarity/relevance score, not a correctness probability.

## 10. Architect's memory map

```text
QDRANT FILTERED VECTOR SEARCH
|
+-- 1. COLLECTION
|      Stored points, vectors and payload
|
+-- 2. QUERY
|      User's text
|      |
|      +-- model.encode(text)
|             |
|             +-- Embedding vector
|
+-- 3. FILTER
|      Payload conditions
|      |
|      +-- must      = AND
|      +-- should    = OR
|      +-- must_not  = NOT
|
+-- 4. SEARCH AND RANK
|      Relevant eligible vectors
|
+-- 5. LIMIT
       Maximum number of returned points
```

### The one-line takeaway

**Qdrant filtered vector search = semantic similarity search + metadata conditions + result limit.**

### Suggested next learning sequence

1. `MatchAny` and `MatchExcept` — match multiple or excluded values.
2. `Range` — filter by numeric ranges, such as price or age.
3. `DatetimeRange` — filter by date/time.
4. `IsEmpty` and `IsNull` — handle missing or null payload fields.
5. `Nested` filters — filter structured JSON payloads.
6. Payload indexes — understand how to make filtering efficient at scale.
7. Filter design for multi-tenant RAG — combine retrieval with secure backend authorization.

---

## Reference

- Qdrant documentation: https://qdrant.tech/documentation/
- Qdrant filtering concepts: https://qdrant.tech/documentation/concepts/filtering/
- Qdrant Python client: https://github.com/qdrant/qdrant-client
