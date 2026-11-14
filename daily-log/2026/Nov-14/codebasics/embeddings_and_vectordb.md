# Qdrant --- AI Architect's Notes

## Vector Database, Python Client, Local Development & Production Architecture

> **Core idea:** Qdrant is a vector database. `QdrantClient` is the
> Python SDK used by an application to communicate with Qdrant. Qdrant
> stores vectors and associated payloads, then retrieves relevant
> records using similarity search and filters.

------------------------------------------------------------------------

## 1. The 30-second mental model

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  **Embedding model**                 Converts text, images, or other
                                      supported inputs into numerical
                                      vectors

  **Qdrant**                          Stores vectors and payloads;
                                      indexes and searches vectors

  **QdrantClient**                    Python interface for sending
                                      operations to Qdrant

  **Retriever / RAG application**     Turns a user query into a vector,
                                      retrieves relevant records, and
                                      prepares context

------------------------------------------------------------------------

## 2. What is `QdrantClient`?

``` python
from qdrant_client import QdrantClient
```

`QdrantClient` is the Python client library (SDK) for interacting with a
Qdrant instance.

It can connect to: - Qdrant running locally in embedded/local mode. - A
Qdrant server running in Docker, on a VM, or in Kubernetes. - Qdrant
Cloud.

It is not itself the vector database server in the normal remote-server
architecture. It is the client-side interface.

### Install

``` bash
pip install qdrant-client
```

### Connect to a local Qdrant server

``` python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
```

### Connect to Qdrant Cloud

``` python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://YOUR-CLUSTER-URL",
    api_key="YOUR-API-KEY"
)
```

Keep credentials in a secret manager or environment variables; do not
hard-code them in source code.

------------------------------------------------------------------------

## 4. How Qdrant fits into a RAG architecture

``` text
                 OFFLINE / INGESTION PIPELINE
                 ============================

  PDFs / Word / Web / Databases
               |
               v
       Parse and extract text
               |
               v
        Chunk the documents
               |
               v
        Embedding model
               |
         vectors + metadata
               |
               v
       Qdrant vector database
       (collections, points,
        vectors, payloads)


                 ONLINE / QUERY PIPELINE
                 =======================

             User question
                   |
                   v
          Python API / Backend
                   |
                   v
          Embedding model
                   |
             query vector
                   |
                   v
             QdrantClient
                   |
                   v
           Qdrant similarity
              search + filter
                   |
             relevant chunks
                   |
                   v
          Prompt construction
                   |
                   v
                  LLM
                   |
                   v
             Final answer
```

**Architectural distinction:** ingestion is usually an offline or
asynchronous pipeline; retrieval is part of the online request path.
They may share embedding infrastructure, but they have different
throughput and latency requirements.

------------------------------------------------------------------------

## 5. Core Qdrant data concepts

Qdrant organizes data into **collections** and **points**.

  -----------------------------------------------------------------------
  Concept                 Easy explanation        Relational database
                                                  analogy
  ----------------------- ----------------------- -----------------------
  Collection              Logical group of        Table (rough analogy)
                          records, configured for 
                          vector search           

  Point                   One stored record       Row

  Point ID                Unique identifier for a Primary key
                          point                   

  Vector                  Numerical               No direct equivalent
                          representation of       
                          content                 

  Payload                 JSON-like metadata      Columns / attributes
                          associated with a point 

  Distance metric         How vector similarity   No direct equivalent
                          or distance is measured 

  Vector index            Data structure that     Index (conceptual
                          accelerates vector      analogy)
                          search                  

  Filter                  Restricts search using  `WHERE` clause (rough
                          payload conditions      analogy)

  Shard                   Partition of collection Partition (rough
                          data                    analogy)

  Replica                 Copy of shard data for  Replicated data
                          availability/read       
                          scaling                 
  -----------------------------------------------------------------------

A point commonly contains: - An ID. - One or more named or unnamed
vectors, depending on collection configuration. - A payload containing
metadata and optionally the original text.

Example conceptual point:

``` json
{
  "id": 101,
  "vector": [0.12, 0.87, 0.34],
  "payload": {
    "text": "Home loan prepayment policy...",
    "document_id": "loan-policy-001",
    "category": "loans",
    "source": "home-loan-policy.pdf"
  }
}
```

The vector above is illustrative only; real embedding dimensions depend
on the embedding model.

------------------------------------------------------------------------

## 6. Important search and indexing concepts

### Similarity search

Qdrant compares a query vector with stored vectors and returns the
closest matches according to the collection's configured distance
metric.

Common distance metrics: - **Cosine:** compares vector direction;
commonly used for text embeddings. - **Dot product:** computes the inner
product; appropriate when supported by the model's embedding setup. -
**Euclidean (L2):** measures straight-line distance.

Use the metric recommended by the embedding model. Do not assume that
one metric is best for every model.

### HNSW

**HNSW (Hierarchical Navigable Small World)** is a graph-based
approximate nearest-neighbour indexing approach used to make vector
search fast at scale.

Architectural trade-off: - Faster retrieval and lower search cost. -
Index memory and build-time overhead. - Approximate search can trade a
little recall for speed.

Qdrant also has other search and storage optimizations; the best
configuration depends on dataset size, latency, recall, and hardware.

### Metadata filtering

Payload filters narrow the search to records matching conditions, for
example: - `category = "loans"` - `document_type = "policy"` -
`tenant_id = "bank-a"` - `effective_date` within a required range.

For multi-tenant systems, enforce tenant isolation in the backend and
apply appropriate filters on every query. Do not rely on a
client-supplied tenant ID without authorization checks.

------------------------------------------------------------------------

## 7. Local execution: two ways to run Qdrant

### Option A --- Embedded/local mode

The Python client can run Qdrant locally in embedded mode and persist
its data to a directory.

``` python
from qdrant_client import QdrantClient

client = QdrantClient(path="./qdrant_data")
```

What happens: 1. Your Python process opens local Qdrant storage. 2.
Qdrant operations run through the embedded/local implementation. 3. Data
is persisted under `./qdrant_data`. 4. A later process can reopen that
same path.

**Characteristics** - No separate Qdrant server process is needed. -
Useful for learning, experiments, tests, and small local workflows. -
The storage path is database data, not a portable CSV/JSON export. -
Local embedded mode has limitations compared with a distributed server
deployment; it is not the normal architecture for a horizontally scaled
production service. - Do not have multiple independent processes
concurrently open the same local storage path unless the documented mode
explicitly supports that usage.

### Option B --- Docker-based Qdrant server

This runs Qdrant as a separate service, closer to a production topology.

``` bash
docker run -p 6333:6333 \
  -p 6334:6334 \
  -v "$(pwd)/qdrant_storage:/qdrant/storage" \
  qdrant/qdrant
```

Connect from Python:

``` python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
```

What happens: 1. Docker starts the Qdrant server container. 2. The
server exposes its HTTP API on port `6333` and gRPC on port `6334` (when
enabled/configured). 3. The Python application connects over the
network. 4. The host directory `qdrant_storage` is mounted into the
container at `/qdrant/storage`. 5. Data survives container replacement
as long as the mounted storage is retained.

**Important:** port publishing makes services reachable from the host;
production deployments should restrict network exposure and configure
authentication/TLS as appropriate.

------------------------------------------------------------------------

## 8. What files does Qdrant create?

Qdrant is a database, not a file-export tool. It maintains its own
internal storage.

For example, with:

``` bash
-v /data/qdrant:/qdrant/storage
```

the host directory `/data/qdrant` holds Qdrant-managed data. Depending
on version and configuration, it may contain directories and files
for: - Collections and their segments. - Vector and payload data. -
Indexes. - WAL (write-ahead log) and other recovery-related data. -
Cluster metadata and related internal state.

An illustrative view:

``` text
/data/qdrant/
├── collections/
│   └── banking_documents/
│       └── ... Qdrant-managed segment and index data ...
├── raft/
└── ... other internal database files ...
```

**This is illustrative, not a guaranteed directory layout.** Exact names
and structure can vary by Qdrant version and configuration.

### Are embeddings saved as CSV or JSON files?

Not by default. Qdrant stores them in its managed database storage. You
can retrieve points through its API/SDK, or build an explicit export
pipeline if you need JSON, CSV, Parquet, or another interchange format.

### What is a snapshot?

A **snapshot** is a Qdrant-managed backup artifact for a collection or
supported scope. It can be used for backup, migration, and restoration.

A snapshot is different from: - A raw copy of the database directory. -
A CSV/JSON export. - The original PDF or Word documents.

Use Qdrant's documented snapshot and restore procedures for the deployed
version. Test restoration, not just snapshot creation.

------------------------------------------------------------------------

## 9. Production deployment architecture

In production, Qdrant is typically deployed as a dedicated service,
separate from the application that uses it.

``` text
                       USERS
                         |
                         v
                 API Gateway / ALB
                         |
                         v
                 Python Backend / RAG
                         |
                         v
                    QdrantClient
                         |
                    HTTP / gRPC
                         |
              +----------------------+
              |    QDRANT CLUSTER    |
              |                      |
              |  Node 1  Node 2  Node 3
              |    |       |       |
              +----|-------|-------|+
                   |       |       |
                   v       v       v
               Persistent storage / disks
```

This is a conceptual topology. Actual shard placement, replication, node
roles, and routing depend on the cluster configuration.

### Deployment choices

  -----------------------------------------------------------------------
  Deployment model        Description             Typical use
  ----------------------- ----------------------- -----------------------
  Docker                  Qdrant in a container   Development and simpler
                                                  deployments

  VM / EC2                Qdrant server on a      Dedicated self-managed
                          virtual machine         service

  Kubernetes              Qdrant deployed and     Containerized platform
                          operated in a cluster   environments

  Qdrant Cloud            Managed Qdrant service  Reduce database
                                                  operations burden
  -----------------------------------------------------------------------

### Production concerns checklist

  -----------------------------------------------------------------------
  Concern                             Architect's design question
  ----------------------------------- -----------------------------------
  Persistence                         Is Qdrant data on durable storage?

  Availability                        What happens when a node or disk
                                      fails?

  Replication                         Are shards replicated to meet
                                      availability requirements?

  Sharding                            How is data distributed as it
                                      grows?

  Scaling                             What are the scale-up and scale-out
                                      triggers?

  Backup / DR                         Are snapshots scheduled and
                                      restores tested?

  Security                            Are TLS, API keys, network
                                      controls, and secrets management
                                      configured?

  Tenant isolation                    Are tenant filters and
                                      authorization enforced server-side?

  Observability                       Are latency, throughput, errors,
                                      resource usage, and collection
                                      health monitored?

  Capacity                            Are RAM, disk, CPU, vector
                                      dimensions, and index overhead
                                      sized from workload tests?

  Upgrades                            Is there a tested upgrade and
                                      rollback procedure?
  -----------------------------------------------------------------------

Do not assume that running three nodes automatically provides high
availability. Correct replication, placement, quorum/consensus behavior,
failure-domain design, and operational configuration matter.

------------------------------------------------------------------------

## 10. Local vs production comparison

  ------------------------------------------------------------------------
  Dimension         Local embedded    Local Docker       Production
                    mode              server             service
  ----------------- ----------------- ------------------ -----------------
  Runtime           Inside Python     Separate container Dedicated service
                    process                              / cluster

  Connection        Local client API  HTTP / gRPC        HTTP / gRPC over
                                                         secured network

  Storage           Local path        Mounted host       Durable disks /
                                      volume             persistent
                                                         volumes

  Multi-node        No typical        Possible but not   Supported cluster
                    cluster topology  the usual          topology
                                      single-container   
                                      setup              

  Availability      Process / machine Container / host   Designed with
                    dependent         dependent          replication and
                                                         failure handling

  Scaling           Limited           Primarily          Vertical and
                                      single-server      horizontal
                                                         options

  Best fit          Learning, tests,  Integration and    Production
                    prototypes        production-like    workloads
                                      development        
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 11. A minimal end-to-end Python example

This example uses local embedded mode and a small illustrative vector.
In a real RAG application, generate vectors using an embedding model and
configure the collection's vector size to match that model.

``` python
from qdrant_client import QdrantClient, models

# 1. Open local Qdrant storage
client = QdrantClient(path="./qdrant_data")

# 2. Create a collection
client.create_collection(
    collection_name="banking_documents",
    vectors_config=models.VectorParams(
        size=3,
        distance=models.Distance.COSINE
    )
)

# 3. Insert a point
client.upsert(
    collection_name="banking_documents",
    points=[
        models.PointStruct(
            id=1,
            vector=[0.1, 0.2, 0.3],
            payload={
                "text": "Home loan prepayment policy",
                "category": "loans"
            }
        )
    ]
)

# 4. Search for similar vectors
results = client.query_points(
    collection_name="banking_documents",
    query=[0.1, 0.2, 0.25],
    limit=3
)

# 5. Inspect returned points
for point in results.points:
    print(point.id, point.score, point.payload)

# 6. Close local storage
client.close()
```

The output is a search response containing matching point IDs,
similarity scores, and payloads. It is not a generated document file.

**Note:** API signatures can evolve across client versions. Check the
documentation for the installed `qdrant-client` version when adapting
code.

------------------------------------------------------------------------

## 12. Qdrant vs a traditional database

  -----------------------------------------------------------------------
  Traditional relational DB           Qdrant
  (e.g. PostgreSQL)                   
  ----------------------------------- -----------------------------------
  Optimized for structured data and   Optimized for vector similarity
  transactions                        retrieval

  SQL predicates and joins            Vector queries and payload filters

  Exact key/value and relational      Nearest-neighbour search
  lookup                              

  B-tree and other relational indexes Vector indexes such as HNSW

  Strong fit for transactional system Strong fit for semantic retrieval
  of record                           
  -----------------------------------------------------------------------

**Architectural guidance:** Qdrant does not automatically replace
PostgreSQL, Oracle, or another transactional database. A common design
keeps authoritative business data in the relational database and uses
Qdrant as a retrieval index. Store a stable business/document ID in
Qdrant payload so the application can fetch the authoritative record
when needed.

------------------------------------------------------------------------

```

### One-line architect's takeaway

**The embedding model converts meaning into vectors; Qdrant persists and
retrieves those vectors; the RAG application supplies relevant context
to the LLM; and `QdrantClient` is the SDK connecting the application to
the vector database.**
