# AI Architect Interview Notes: Production LLM Systems


> **Scope:** Inference engineering, cost engineering, RAG, agent state, security, and observability.  

---

## 1. Inference Engineering:

### 1.1 Understand the inference lifecycle

LLM inference has two broad phases:

- **Prefill:** Processes the input prompt and builds the initial key-value (KV) cache. 
- **Decode:** Generates output tokens sequentially. 

This distinction matters because a request can be slow to start, slow to stream, or both.

| Metric | Meaning | Typical causes of degradation |
|---|---|---|
| **Time to First Token (TTFT)** | Time from request submission to the first generated token | Queueing, long prompts |
| **Inter-Token Latency (ITL)** | Time between successive generated tokens | Decode bottlenecks, memory bandwidth|
| **End-to-end latency** | Time until the complete answer is available | |
| **Throughput** | measure requests/sec and tokens/sec  | poor batching,  compute limits |

**Interview insight:** If TTFT is high but ITL is healthy, investigate queueing, prompt length, retrieval and prefill before optimizing decode. If TTFT is low but completion is slow, investigate output length, decode throughput and memory bandwidth.

Measure **p50, p95 and p99**, not only averages. 

### 1.2 Throughput, concurrency and queueing

A service may handle many short requests per second while struggling with fewer requests that have long prompts and long outputs.

If a service receives 20 requests/second and average time in the system is 2 seconds, approximately 40 requests are in flight on average. This is not a safe concurrency limit; memory, GPU capacity and workload distribution still determine the practical limit.

**Failure pattern:** Excess traffic grows the queue, increases TTFT, causes client timeouts, triggers retries.

**Architectural response:** Use bounded queues, backpressure, load shedding 

### 1.3 Continuous batching
Continuous batching = Keep the GPU busy by continuously replacing finished requests with new ones.

Imagine a bus carrying 10 passengers. When some passengers get off, new passengers can board immediately instead of waiting for everyone to get off.

- Benefit: Better GPU usage and faster processing of multiple AI requests.
- Challenge: Must ensure some users don't wait too long.

Remember: The goal is to serve more users efficiently without making anyone wait too long.

### 1.4 KV cache and PagedAttention

KV Cache = AI’s short-term memory of the conversation.

Imagine you are reading a book. Every time you read a new sentence, you don't reread the entire book to understand it. You remember what you have already read.

- Without KV Cache: AI repeatedly recalculates information from previous words. This wastes time.
- With KV Cache: AI saves useful information from previous words and reuses it to generate the next word faster.

Why is it useful?

- ⚡ Faster responses.
- 🔄 Less repeated computation.
- 🧠 But it consumes GPU memory, especially for long conversations and many users.

### 1.5 Speculative decoding

Speculative decoding = Guess first, verify later.
Imagine a fast junior employee drafts 5 words in advance. A senior employee quickly checks whether those words are correct.
- Draft model: Quickly guesses the next few words.
- Target model: Checks those guesses.
- Benefit: If most guesses are correct, the AI generates answers faster.
When does it help? When the guesses are usually correct and checking them is efficient.
- Speculative decoding: One AI model guesses; another verifies.

### 1.6 Quantization: BF16, FP8 and INT4

Quantization lowers the numerical precision used for weights, activations or cache values to reduce memory use and potentially improve speed.

| Format | Approximate raw storage/value | 
|---|---:|
| BF16 | 2 bytes |
| FP8 | 1 byte | 
| INT4 | 0.5 byte | 

These are raw representation sizes, not full deployment footprints. Metadata, scales, unquantized layers, runtime buffers and KV cache add overhead.

For a hypothetical 70-billion-parameter model, raw weight storage is roughly 140 GB in BF16, 70 GB in FP8, or 35 GB at 4 bits per parameter, using decimal units. Actual memory needs are higher.

**Decision principle:** Choose the lowest-cost configuration that meets quality, latency and reliability SLOs.


---

## 2. Cost Engineering and Token Economics

### 1. Measure cost per task
Don't measure only the cost of one AI call. Measure the total cost to complete one user's task, including retries and multiple AI calls.
### 2. Exact cache vs Semantic cache
- Exact cache: Same question → reuse the saved answer.
- Semantic cache: Similar question → try to reuse an answer, but verify it's correct.
### 3. Model routing
Use a small, cheaper model for simple tasks and a powerful, expensive model for complex tasks.
### 4. Rate limits, Circuit breakers and Fallbacks
- Rate limit: Restrict how many requests users can make.
- Circuit breaker: Stop calling a service that is repeatedly failing.
- Fallback: If the main AI fails, switch to an alternative.

---

## 3. Production RAG Architecture

### 3.1 RAG is a pipeline, not a vector database

RAG = Search for relevant information + Give it to AI + Generate an answer.

Example: AI searches your company documents, finds the relevant information, and answers your question using it.

Basic steps:

1. Store documents and prepare them for search.
2. Search for relevant information when a question comes.
3. Give that information to AI.
4. AI generates an answer based on it.

Remember: A vector database is only one part of RAG. RAG can still give wrong answers if the search finds the wrong information.

### 3.2 Chunking strategies

Chunking = Breaking large documents into smaller pieces so AI can search them easily.

- Fixed-size: Break into equal-sized pieces.
- Semantic: Break according to meaning.
- Parent-child: Find a small piece, then retrieve its larger section for context.
- Hierarchical: Search from document → chapter → section → paragraph.

Remember: Good chunking helps AI find the right information.

### 3.3 Embeddings and embedding-model migrations

Embeddings = Converting text into numbers that represent its meaning.

Example: “How do I reset my password?” and “I forgot my password” have similar meanings, so their embeddings may be close together.

Embedding-model migration means switching to a new model that converts text into these numbers. Usually, you must regenerate the document embeddings so searches remain compatible.

### 3.3 Embeddings and embedding-model migrations

Embeddings represent text as vectors so semantically related text can be retrieved. Query and document vectors must be compatible.

---

## 4. Agentic Scalability and State Management

## 4. Agentic Scalability and State Management

### 4.1 Agent as a Workflow
An agent is a sequence of steps: understand request → call tools → validate results → respond.

**Use a simple, controlled workflow instead of unnecessary multiple agents.**

### 4.2 Checkpointing and Recovery
Save workflow progress so the agent can resume after a crash without repeating completed work unnecessarily.

### 4.3 Bound Agent Execution
Set limits on steps, retries, time, tokens and cost to prevent infinite loops and unexpected expenses.

### 4.4 Human Approval
Require human approval before sensitive actions, such as making payments or modifying important records.

### 4.5 Idempotent Tool Execution
Prevent duplicate actions when a request is retried. For example, a payment should not happen twice because the first response timed out.

### 4.6 Modular Workflows
Break complex workflows into smaller, independent steps that are easier to test, debug and maintain.

**Interview takeaway:** Build agents with controlled workflows, saved state, execution limits, proper authorization and safe retries.
---

## 5. Enterprise Security, Privacy and Data Isolation

### 5.1 Prompt Injection
- **Direct:** User tricks AI into ignoring instructions.
- **Indirect:** Malicious instructions are hidden in documents or web pages.

**Defense:** Treat external content as untrusted, restrict tools, and require approval for sensitive actions.

### 5.2 Secure Tool Calling
AI can suggest an action, but the application must verify **permissions and business rules** before executing it.

### 5.3 PII Protection
**Redaction:** Hide sensitive data, such as account numbers.

**Tokenization:** Replace sensitive data with controlled tokens.

Never send sensitive data to unapproved AI services or expose it in logs.

### 5.4 Secrets and Tenant Isolation
- **Secrets:** Store API keys securely; never expose them to AI.
- **Tenant isolation:** Ensure one customer's data is never accessible to another customer across databases, RAG, caches, tools and logs.

**Interview takeaway:** Never rely on AI alone for security. Enforce authorization, data protection and access controls in the application itself.

---

## 6. Observability and Day-2 Operations

### 6.1 Why normal monitoring is not enough

An AI request can succeed technically but still give a wrong or unsafe answer.

**Monitor both:**
- **System:** Speed, errors, memory and cost.
- **AI:** Answer correctness, safety, retrieval quality and tool usage.

Trace the complete journey: request → search → AI → tools → final answer.

**Remember:** Don't store sensitive user data unnecessarily in logs.

### 6.2 OpenTelemetry, Langfuse and Arize Phoenix

- **OpenTelemetry:** Tracks requests across different services.
- **Langfuse:** Helps track AI calls, prompts, tokens and cost.
- **Arize Phoenix:** Helps inspect AI behavior, search results and answer quality.

### 6.3 Production metrics

- **Performance:** Response time, errors and GPU usage.
- **Cost:** Cost per task, token usage and cache savings.
- **RAG quality:** Whether the right information was retrieved and answers are supported by sources.
- **Agent quality:** Whether the task completed and tools worked correctly.
- **Security:** Unauthorized access, data leaks and policy violations.

### 6.4 Offline evaluation vs Online monitoring

- **Offline evaluation:** Test AI using prepared questions before releasing changes.
- **Online monitoring:** Watch real users' requests to detect problems after release.

**Safe release process:**
1. Test the new version.
2. Check quality and security.
3. Release to a small group first (canary).
4. Monitor performance and answers.
5. Roll back if problems occur.

**Remember:** An AI release is successful only when quality, safety and reliability remain good.
---

## 8. Interview Questions Worth Practicing

Try to answer each question by explaining the diagnostic process, trade-offs and failure modes—not just naming a tool.

1. **TTFT is high but ITL is healthy. What do you investigate first?**  
   Separate queueing, retrieval/tool latency, prompt size and prefill before optimizing decode.

2. **Why can a model fit on a GPU but fail at production concurrency?**  
   KV cache, runtime buffers and temporary memory are additional to weights; context length and active sequences affect capacity.

3. **How do you recover an agent after a worker crash?**  
   Persist validated state transitions, resume from a checkpoint and make side effects idempotent or reconcilable.

4. **How do you know a new model or prompt is better?**  
    Use a versioned gold set, compare quality and safety by task, test retrieval/tool behavior, then shadow or canary with rollback criteria.

5. **LLM spans are fast, but end-to-end latency is high. What next?**  
    Inspect retrieval, queueing, tools, retries, serialization, networking and post-processing; verify trace boundaries.

---

