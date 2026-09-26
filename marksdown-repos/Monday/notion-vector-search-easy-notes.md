# Notion's Vector Search Journey --- 10× Scale, 1/10th Cost

**6-minute easy-read notes**

Based on Notion's engineering article: *Two years of vector search at
Notion*.

Source: https://www.notion.com/blog/two-years-of-vector-search-at-notion

------------------------------------------------------------------------

## 1. First: What problem was Notion solving?

Imagine you search:

> **"team meeting notes"**

A traditional keyword search looks for those exact words.

But the actual document might be called:

> **"Engineering standup summary"**

Humans understand they are related. A traditional search engine may not.

### Vector search solves this

Instead of storing only words, Notion converts text into **embeddings**.

Think of an embedding as a **GPS coordinate for meaning**.

``` text
"team meeting notes"
        ↓
   Embedding
        ↓
[0.21, -0.73, 0.45, ...]
        ↓
Meaning represented as a point
```

Similar meanings end up close together:

``` text
                    ● Team meeting
                  ● Standup notes
                ● Sprint discussion


                                      ● Pizza recipe
```

So Notion can search based on **meaning**, not just exact words.

This is important because Notion AI needs to answer natural-language
questions using information spread across Notion and connected sources.

------------------------------------------------------------------------

## 2. The starting architecture

When Notion AI Q&A launched in **November 2023**, Notion had two
indexing pipelines.

### A. Offline pipeline

Used for existing/bulk data.

``` text
Documents
    ↓
Apache Spark
    ↓
Chunk documents
    ↓
Generate embeddings
    ↓
Vector Database
```

### B. Online pipeline

Used for live changes.

``` text
User edits page
      ↓
     Kafka
      ↓
Kafka Consumer
      ↓
Generate embedding
      ↓
Vector Database
```

This gave them:

-   Bulk processing for large amounts of data
-   Near-real-time updates for active users
-   Sub-minute indexing latency

------------------------------------------------------------------------

## 3. Then came the first big problem: SCALE

Notion AI became extremely popular.

There was a waitlist containing **millions of workspaces**.

But the vector database started running out of capacity just **one month
after launch**.

They had a fundamental problem:

``` text
More users
   ↓
More documents
   ↓
More embeddings
   ↓
More vectors
   ↓
Vector DB capacity problem
```

### What did they do?

Instead of continuously reshuffling existing data, they introduced
**generations**.

Think of it like opening new warehouses.

``` text
Generation 1
Workspace A
Workspace B
Workspace C

Generation 2
Workspace D
Workspace E
Workspace F

Generation 3
Workspace G
Workspace H
```

New workspaces went to the newest generation.

This avoided expensive re-sharding operations.

------------------------------------------------------------------------

## 4. They dramatically increased onboarding speed

Initially:

> Only a few hundred workspaces could be onboarded per day.

That wasn't enough.

They optimized:

-   Airflow scheduling
-   Spark jobs
-   Pipeline parallelism
-   Data processing throughput

The results were significant:

  Metric                        Improvement
  --------------------------- -------------
  Daily onboarding capacity        **600×**
  Active workspaces                 **15×**
  Vector DB capacity                 **8×**

By April 2024, they had cleared the Q&A waitlist.

### Important architecture lesson

**Scaling isn't always about buying bigger machines.**

Often it is about improving:

``` text
Scheduling
    +
Parallelism
    +
Batching
    +
Data partitioning
    +
Pipeline efficiency
```

------------------------------------------------------------------------

## 5. Then they attacked COST

Scaling solved the capacity problem.

But now they had another problem:

> **The system was expensive.**

Their original vector database used dedicated hardware where **storage
and compute were coupled**.

That means they were paying for infrastructure even when it wasn't fully
utilized.

### May 2024: Serverless architecture

They moved to a serverless architecture where:

``` text
Storage
   ↓
separated from
   ↓
Compute
```

And they paid more based on **actual usage rather than simply keeping
infrastructure running**.

### Result

**\~50% cost reduction from peak usage**, saving several million dollars
annually.

But they still weren't satisfied.

------------------------------------------------------------------------

## 6. They changed the Vector Search engine

Notion evaluated alternative search engines and eventually moved its
multi-billion-object workload to **turbopuffer**.

The migration wasn't simply:

> Old DB → New DB

They used it as an opportunity to redesign the architecture.

### Four major changes

#### 1. Full re-indexing

They rebuilt their corpus with higher write throughput.

#### 2. Better embedding model

They upgraded the embedding model.

#### 3. Simpler architecture

Instead of worrying about complex sharding and generation routing:

``` text
Namespace
    ↓
Independent Index
```

#### 4. Gradual migration

They migrated one generation at a time.

``` text
Generation 1
    ↓
Validate
    ↓
Generation 2
    ↓
Validate
    ↓
Generation 3
    ↓
Validate
```

This reduced migration risk.

### Results

-   **60% reduction** in search-engine spend
-   **35% reduction** in AWS EMR compute cost
-   p50 query latency improved from **70--100 ms → 50--70 ms**

------------------------------------------------------------------------

## 7. The clever optimization: Don't re-embed unchanged data

This is one of the most interesting parts of the article.

Suppose a Notion page has:

``` text
100 chunks
```

A user changes **one sentence**.

The old system effectively did:

``` text
Page changed
    ↓
Re-chunk entire page
    ↓
Re-embed all 100 chunks
    ↓
Upload all 100 chunks
```

That's wasteful.

------------------------------------------------------------------------

## 8. Page State Project

Notion introduced a mechanism to understand **exactly what changed**.

They maintained two hashes for every chunk:

``` text
Chunk
 ├── Text Hash
 └── Metadata Hash
```

They used **xxHash64** because it offered a useful balance of speed,
collision characteristics, and storage footprint.

The previous state was stored in **DynamoDB**.

### Case 1: Text changed

``` text
Previous:

Chunk 1 → same
Chunk 2 → same
Chunk 3 → CHANGED
Chunk 4 → same

              ↓

Only Chunk 3
gets re-embedded
```

Instead of processing the whole page.

### Case 2: Only metadata changed

Imagine the content doesn't change, but permissions change.

``` text
Before:
User A can read

After:
Everyone can read
```

The text embedding doesn't need to change.

``` text
Text hash      → SAME
Metadata hash  → CHANGED

          ↓

Don't generate embedding
          ↓
Only update metadata
```

### Result

They achieved approximately **70% reduction in data volume**, reducing
both embedding API costs and vector database write costs.

------------------------------------------------------------------------

## 9. Next problem: Embedding APIs themselves

Notion's pipeline originally depended on an external embedding API.

``` text
Spark
  ↓
Preprocessing
  ↓
Embedding API
  ↓
Vector DB
```

There were several problems.

### Problem 1 --- Double compute

They were paying for:

``` text
Spark compute
      +
Embedding API
```

### Problem 2 --- External dependency

If the embedding provider had problems:

``` text
Embedding API down
       ↓
Indexing slows/stops
       ↓
Search index becomes stale
```

### Problem 3 --- Complicated pipeline

They had created additional pipelines to smooth traffic and avoid API
rate limits.

------------------------------------------------------------------------

## 10. Enter Ray + Anyscale

In July 2025, Notion started migrating the near-real-time embedding
pipeline from **Spark to Ray**, running on **Anyscale**.

The idea was simple:

> Put preprocessing and model inference closer together.

Instead of:

``` text
CPU processing
     ↓
External API
     ↓
GPU/embedding infrastructure
```

They could do:

``` text
CPU
 ↓
Chunking
 ↓
Change detection
 ↓
GPU
 ↓
Embedding generation
 ↓
Vector DB
```

Ray can pipeline CPU-heavy and GPU-heavy work.

------------------------------------------------------------------------

## 11. Why Ray?

Notion highlighted several benefits.

### 1. Model flexibility

They can run open-source embedding models themselves.

``` text
New embedding model
        ↓
Experiment
        ↓
Deploy
```

They don't have to wait for an external provider.

### 2. Unified compute

Preprocessing + inference can happen on the same compute layer.

### 3. Better GPU utilization

CPU preprocessing can happen while GPUs perform embedding inference.

``` text
CPU → Chunking
       ↓
GPU → Embedding
       ↓
CPU → Next batch
```

### 4. Lower latency

Self-hosting embeddings removes an external API hop.

### 5. Developer productivity

Anyscale provides managed infrastructure so engineers don't have to
build all the underlying ML infrastructure themselves.

Notion anticipates **90%+ reduction in embedding infrastructure costs**,
although this was still rolling out when the article was published.

------------------------------------------------------------------------

## 12. What about query-time embeddings?

There are actually **two embedding problems**.

### Index-time

When a document is added:

``` text
Document
   ↓
Embedding
   ↓
Vector DB
```

### Query-time

When a user searches:

``` text
User question
      ↓
Embedding
      ↓
Vector DB search
      ↓
Relevant documents
```

Query-time embedding is especially latency-sensitive because the user is
waiting.

Notion uses **Ray Serve** to host embedding models persistently on GPUs.

It provides capabilities such as:

-   Dynamic batching
-   Replication
-   Autoscaling
-   GPU model hosting

------------------------------------------------------------------------

## 13. The complete evolution

``` text
2023
│
├── Launch Vector Search
│
├── Spark + Kafka
│
├── Dedicated Vector DB
│
└── Rapid scale
       ↓
2024
│
├── Generation-based scaling
│
├── Serverless Vector DB
│
├── New vector search engine
│
└── Major cost reduction
       ↓
2025
│
├── Detect only changed chunks
│
├── Reduce unnecessary embeddings
│
├── Move embeddings to Ray
│
└── Self-host embedding models
       ↓
2026
│
└── More scalable + cheaper + lower latency
```

------------------------------------------------------------------------

## 14. The biggest architecture lessons

### Lesson 1 --- Scale first, optimize second

Initially, Notion needed to survive massive growth.

They didn't try to build the perfect architecture from day one.

``` text
First:
Make it work at scale

Then:
Make it cheaper

Then:
Make it simpler
```

### Lesson 2 --- Don't recompute what hasn't changed

Bad:

``` text
Small change
   ↓
Reprocess everything
```

Better:

``` text
Small change
   ↓
Detect changed component
   ↓
Process only that component
```

This principle applies far beyond vector databases.

### Lesson 3 --- Separate storage and compute

Coupled architecture:

``` text
Storage + Compute
       ↓
Always pay for both
```

Decoupled architecture:

``` text
Storage ←→ Compute
```

Now compute can scale independently.

### Lesson 4 --- External APIs are convenient but create dependency

Using an embedding API gives you:

**Pros** - Easy to start - No GPU management - Fast development

**Cons** - API cost - Rate limits - Reliability dependency - Network
latency - Less model control

At sufficient scale, self-hosting can become attractive.

------------------------------------------------------------------------

## 15. The most important takeaway for an AI Architect

The article isn't really about **vector databases**.

It is about this:

> **AI infrastructure must continuously evolve as usage grows.**

A system that is perfect for:

``` text
10K documents
```

may be terrible for:

``` text
10 BILLION vectors
```

The architecture must evolve across multiple dimensions:

``` text
                 AI SEARCH
                    │
      ┌─────────────┼─────────────┐
      ↓             ↓             ↓
   SCALE          COST         LATENCY
      │             │             │
 Sharding       Serverless    Ray Serve
 Batching       Better DB     GPU serving
 Pipelines      Change detect Self-hosting
```

And Notion's journey shows an important engineering principle:

> **The biggest optimization is often eliminating unnecessary work---not
> simply making the existing work faster.**

That is the core idea worth remembering from this article.

------------------------------------------------------------------------

## Source

Notion Engineering --- *Two years of vector search at Notion*\
https://www.notion.com/blog/two-years-of-vector-search-at-notion
