# Speeding Up Agentic Workflows with WebSockets

## A 6-minute easy explanation from an AI + Software Architect perspective

OpenAI's article is about a very important problem in modern AI systems:

> **The model became extremely fast, but the systems around the model were still slow.**

OpenAI explains how it made agentic workflows around the Responses API faster by using caching, removing unnecessary network hops, improving the safety path, and—most importantly—using **persistent WebSocket connections**.

---

# 1. What Is an Agentic Workflow?

A normal chatbot might look like:

```text
User
 │
 ▼
LLM
 │
 ▼
Answer
```

An AI coding agent behaves differently:

```text
User
 │
 ▼
Agent
 │
 ├──► Search code
 ├──► Read files
 ├──► Understand code
 ├──► Edit files
 ├──► Run tests
 ├──► See failure
 ├──► Fix code
 ├──► Run tests again
 └──► Return result
```

An agent is essentially a **loop**:

```text
             ┌───────────────┐
             │      LLM      │
             └───────┬───────┘
                     │
                 Choose action
                     │
                     ▼
                  Tool call
                     │
                     ▼
                Tool executes
                     │
                     ▼
                Result returned
                     │
                     ▼
             Back to the LLM
                     │
                     └──────────►
```

This loop can happen dozens of times during one user request.

---

# 2. The Surprising Problem: The Model Wasn't the Slowest Part

Historically:

```text
LLM inference
████████████████████
       VERY SLOW
```

So API overhead was relatively small.

But as inference became dramatically faster:

```text
NEW WORLD

API overhead     ███████
LLM inference    ███
```

Suddenly:

> **The API and surrounding infrastructure became part of the bottleneck.**

This is a classic systems-engineering problem.

---

# 3. Think About a Race Car

Imagine you build a very fast race car.

Before:

```text
Car speed       █████████████████
Pit stop        ██
```

You upgrade the engine:

```text
Car speed       █████████████████████████████
Pit stop        ██
```

The car is faster, but the pit stop now represents a much larger percentage of total race time.

The same thing happened with AI inference:

```text
FASTER MODEL
     │
     ▼
Less inference time
     │
     ▼
API overhead becomes visible
     │
     ▼
Agent still feels slow
```

So OpenAI had to optimize **the system around the model**, not just the model itself.

---

# 4. What Was Happening with HTTP?

Suppose an agent wants to perform several tool calls.

A simplified architecture might look like:

```text
Agent
 │
 ▼
HTTP Request #1
 │
 ▼
OpenAI API
 │
 ▼
Model
 │
 ▼
Response
 │
 ▼
Tool
 │
 ▼
HTTP Request #2
 │
 ▼
OpenAI API
 │
 ▼
Model
 │
 ▼
Response
 │
 ▼
Tool
 │
 ▼
HTTP Request #3
 │
 ▼
...
```

Every request introduces overhead.

For an agent making many calls:

```text
Request 1 → overhead
Request 2 → overhead
Request 3 → overhead
Request 4 → overhead
...
Request 30 → overhead
```

Small overhead × many calls = **large latency**.

---

# 5. The Big Idea: Keep the Connection Open

This is where WebSockets enter the picture.

Traditional request/response communication repeatedly performs request lifecycles.

With WebSockets:

```text
Client
   │
   │  Persistent connection
   │══════════════════════════════╗
   │                              ║
   ▼                              ║
OpenAI API                        ║
   │                              ║
   ├── Message 1 ◄───────────────►║
   ├── Message 2 ◄───────────────►║
   ├── Message 3 ◄───────────────►║
   ├── Message 4 ◄───────────────►║
   └── Message 5 ◄───────────────►║
                                  ║
                         connection stays open
```

Instead of repeatedly establishing the interaction, the agent maintains a **persistent connection**.

This lets the system reuse state associated with that connection.

---

# 6. Why Persistent Connections Matter

Think about going to a restaurant.

### Old approach

Every time you want something:

```text
Enter restaurant
     ↓
Order
     ↓
Eat
     ↓
Leave
```

Then:

```text
Enter restaurant again
     ↓
Order
     ↓
Eat
     ↓
Leave
```

Doing this 20 times would be ridiculous.

### WebSocket approach

You sit at the table:

```text
Enter once
   │
   ▼
Sit at table
   │
   ├── Order
   ├── Another order
   ├── Ask waiter
   ├── Another request
   └── Final request
```

You maintain the relationship.

That's the basic idea behind persistent connections.

---

# 7. Repeated Context Was Another Problem

Suppose an agent has already processed:

```text
System instructions
+
Conversation
+
Tools
+
Previous results
```

Then it makes another request.

Why rebuild everything?

Conceptually:

```text
Request 1
[AAAAAAAAAAAAAAAA][B]

Request 2
[AAAAAAAAAAAAAAAA][B][C]

Request 3
[AAAAAAAAAAAAAAAA][B][C][D]
```

The `A` section hasn't changed.

Yet processing it repeatedly creates unnecessary work.

OpenAI's approach keeps reusable response state in an **in-memory cache associated with the WebSocket connection**.

```text
             WebSocket Connection
                     │
                     ▼
          ┌─────────────────────┐
          │   MEMORY CACHE      │
          ├─────────────────────┤
          │ Previous response   │
          │ Conversation state  │
          │ Tool definitions    │
          │ Rendered tokens     │
          └─────────────────────┘
                     │
                     ▼
              Next agent step
```

---

# 8. `previous_response_id` Is Important

OpenAI keeps a familiar Responses API programming model.

Conceptually:

```text
Response 1
     │
     ▼
response_id = ABC123
     │
     ▼
Tool executes
     │
     ▼
Response 2
previous_response_id = ABC123
```

The server can retrieve previous state from the connection-scoped cache rather than rebuilding the complete history.

A strong API-design lesson:

> **Improve the underlying architecture without unnecessarily forcing developers to learn a completely new programming model.**

---

# 9. What Happens Inside an Agent Loop?

The improved architecture can be visualized as:

```text
                     USER
                      │
                      ▼
                 Agent Client
                      │
                      │ WebSocket
                      ▼
             ┌─────────────────┐
             │ Responses API   │
             └────────┬────────┘
                      │
              ┌───────┴────────┐
              │ Connection      │
              │ Scoped Cache    │
              └───────┬────────┘
                      │
                      ▼
                    Model
                      │
                Tool decision
                      │
                      ▼
                 Tool call
                      │
                      ▼
                Client executes
                      │
                      │ result
                      ▼
             Responses API
                      │
                      ▼
                Model continues
```

The important sequence is:

```text
CONNECT ONCE
     │
     ▼
REUSE STATE
     │
     ▼
CALL TOOL
     │
     ▼
SEND RESULT
     │
     ▼
CONTINUE MODEL
     │
     ▼
REPEAT
```

---

# 10. Pause the Model Instead of Restarting Everything

Imagine the model is generating:

```text
"I need to inspect file payment.go..."
```

The model decides to call a tool.

A less efficient approach might look like:

```text
Model
 │
 ▼
Stop
 │
 ▼
New API request
 │
 ▼
Rebuild context
 │
 ▼
Model starts again
```

A better architecture is:

```text
Model
 │
 ▼
Tool call
 │
 ▼
PAUSE
 │
 ▼
Client executes tool
 │
 ▼
Tool result
 │
 ▼
RESUME
 │
 ▼
Model continues
```

Think of a video game:

```text
Old:
Save game → Quit → Restart → Load → Continue

New:
Pause → Do something → Resume
```

---

# 11. WebSocket vs gRPC

OpenAI considered approaches including:

- WebSockets
- gRPC bidirectional streaming

WebSockets were selected because they provide persistent message transport while keeping the existing Responses API input/output shapes familiar to developers.

The architectural lesson:

> **Don't choose infrastructure technology only because it is technically fast. Consider compatibility, developer experience, migration cost, and operational complexity too.**

---

# 12. Removing Unnecessary Network Hops

WebSockets weren't the only optimization.

Imagine:

```text
Request
  │
  ▼
API
  │
  ▼
Service A
  │
  ▼
Service B
  │
  ▼
Inference
```

Every hop adds latency.

If possible:

```text
Request
  │
  ▼
API
  │
  ▼
Inference
```

Fewer hops mean less latency and fewer possible failure points.

General principle:

> **Every network hop has a cost. Remove unnecessary hops from the critical path.**

---

# 13. Caching Rendered Tokens

Tokenization and rendering can also consume CPU time.

Without caching:

```text
Conversation
     │
     ▼
Tokenize
     │
     ▼
Process
```

Repeatedly:

```text
Conversation
     │
     ▼
Tokenize AGAIN
     │
     ▼
Process AGAIN
```

With caching:

```text
First time
    │
    ▼
Tokenize
    │
    ▼
+----------------+
| TOKEN CACHE    |
+----------------+
        │
        ▼
Reuse
```

Again:

> **Don't repeatedly perform work whose inputs haven't changed.**

---

# 14. Move Non-Critical Work Off the Critical Path

Suppose the system needs:

```text
Model response
Billing
Logging
Metrics
Analytics
```

Not everything needs to block the user response.

Instead:

```text
                Request
                   │
                   ▼
              Model result
                   │
            ┌──────┴──────┐
            ▼             ▼
       User response   Billing
                          │
                          ▼
                       Async
```

This is a classic systems-engineering principle:

> **Move non-critical work off the critical path.**

---

# 15. The Result: Faster Agent Workflows

OpenAI reports that alpha users saw **up to 40% improvement** in agentic workflows.

For GPT-5.3-Codex-Spark, OpenAI reported reaching a target of around **1,000 tokens/second**, with bursts up to around **4,000 tokens/second** in production traffic.

The article also reports improvements observed by several partner products. These are reported measurements, not universal guarantees for every workload.

The important point is:

```text
Faster model
     +
Faster networking
     +
Better caching
     +
Fewer hops
     +
Async work
     ↓
Faster agent
```

---

# 16. The Most Important Architecture Lesson

> **When your model gets faster, your surrounding infrastructure can become the bottleneck.**

Think about the complete agent pipeline:

```text
                AGENT WORKFLOW
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
     Client          API          Model
       │             │             │
       ▼             ▼             ▼
     Tools        Routing       Inference
       │             │             │
       └─────────────┼─────────────┘
                     ▼
                  Response
```

Improving only the model isn't enough.

You need to optimize the complete path.

---

# 17. The "Bottleneck Moves" Principle

Imagine:

```text
VERSION 1

Model       ████████████████████
API         ███
Network     ██
```

Model is the bottleneck.

You make the model 10× faster:

```text
VERSION 2

Model       ██
API         ███
Network     ██
```

Now:

```text
API = bottleneck
```

You optimize the API.

Then perhaps:

```text
VERSION 3

Model       ██
API         █
Network     ██
```

Now the network or tool execution may become the bottleneck.

Therefore:

> **Optimization is iterative. When you remove one bottleneck, another becomes visible.**

---

# 18. Complete Architecture

```text
                         USER
                          │
                          ▼
                    AGENT CLIENT
                          │
                    Persistent
                    WebSocket
                          │
                          ▼
                 ┌────────────────┐
                 │ Responses API  │
                 └───────┬────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
           Routing     Cache     Validation
              │          │          │
              └──────────┼──────────┘
                         ▼
                    MODEL/GPU
                         │
                         ▼
                     Tool Call
                         │
                         ▼
                  Client Tool
                         │
                         ▼
                   Tool Result
                         │
                         ▼
                  WebSocket
                         │
                         ▼
                    MODEL
                         │
                         ▼
                  Final Response
```

The entire loop stays optimized.

---

# 19. WebSocket vs HTTP

| Area | Repeated HTTP requests | Persistent WebSocket |
|---|---|---|
| Connection | Repeated request lifecycle | Persistent connection |
| Context | Can be repeatedly processed | Connection-scoped state can be reused |
| Network overhead | Higher | Lower |
| Agent loops | More request overhead | Better suited to repeated interactions |
| State | Reconstructed more often | Cached in memory |
| Tool calls | More request overhead | Messages over existing connection |
| Developer API | Familiar | Familiar Responses API shapes |
| Best fit | Independent requests | Long-running interactive agent loops |

---

# 20. The 12-Year-Old Explanation

Imagine you're talking to a very smart robot.

You say:

> "Fix my bicycle."

The robot says:

> "I need a screwdriver."

You give it a screwdriver.

Then:

> "I need a wrench."

You give it a wrench.

Then:

> "I need to test the wheel."

You help it.

### Bad communication system

```text
Robot
  │
  ▼
Call office
  │
  ▼
Explain entire bicycle problem
  │
  ▼
Ask for screwdriver
  │
  ▼
Come back
```

Then repeat everything for the wrench.

### Better communication system

```text
You ═══════════════════════════ Robot
         phone stays open

Robot: "Give me screwdriver."
You:   "Here."

Robot: "Now wrench."
You:   "Here."

Robot: "Let's test."
You:   "Okay."
```

The robot doesn't have to repeatedly explain the entire problem.

That's essentially why the persistent WebSocket connection helps an AI agent.

---

# 21. The Deep AI Architect Takeaway

The article isn't really about WebSockets.

WebSockets are the **mechanism**.

The deeper idea is:

```text
              AGENTIC AI
                  │
                  ▼
        Repeated model/tool loop
                  │
                  ▼
          Lots of repeated work
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      Network   Context    Validation
      overhead  rebuilding  overhead
        │         │         │
        └─────────┼─────────┘
                  ▼
             High latency
                  │
                  ▼
             Optimize loop
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
    Persistent  Caching   Async work
    connection
        │         │         │
        └─────────┼─────────┘
                  ▼
             Faster agent
```

The fundamental principle is:

> **Optimize the loop, not just the model.**

---

# 22. Five Architecture Principles to Remember

## 1. Persistent connections

If two systems communicate repeatedly:

```text
Connect → communicate → disconnect
```

may be inefficient.

Consider:

```text
Connect
   │
   ├── message
   ├── message
   ├── message
   └── message
```

when the workload justifies it.

---

## 2. Cache reusable state

Ask:

> "What am I recomputing on every request?"

Then cache it.

```text
Repeated work
      │
      ▼
Can it be reused?
      │
     YES
      │
      ▼
CACHE
```

---

## 3. Remove network hops

Every hop:

```text
Service A
   ↓
Service B
   ↓
Service C
   ↓
Service D
```

adds latency and another possible failure point.

If appropriate:

```text
Service A ─────────► Service D
```

---

## 4. Keep the critical path small

Ask:

> "Does this work have to happen before the user gets the response?"

If not:

```text
                    Request
                       │
                       ▼
                  User response
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          Critical           Background
            work                work
```

---

## 5. Optimize the entire agent loop

Don't measure only:

```text
LLM tokens/sec
```

Measure:

```text
User request
     │
     ▼
API latency
     +
Model latency
     +
Tool latency
     +
Context building
     +
Network latency
     +
Validation
     +
Final response
     │
     ▼
TOTAL USER LATENCY
```

That's the number that matters.

---

# Final Crux

If I had to summarize the entire article in one sentence:

> **As AI models become extremely fast, the bottleneck moves to everything around the model—so persistent WebSocket connections, caching, fewer network hops, and asynchronous work can make the entire agent loop faster.**

The mental model to remember is:

```text
                  FAST MODEL
                     │
                     ▼
          ┌─────────────────────┐
          │  Agentic Workflow   │
          └──────────┬──────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    WebSocket      Cache      Async Work
        │            │            │
        └────────────┼────────────┘
                     ▼
              Less overhead
                     │
                     ▼
              Faster Agent
                     │
                     ▼
             Better UX
```

## The Key Architectural Question

Don't ask only:

> **"How fast is my LLM?"**

Ask:

> **"How fast can my entire agent complete one useful piece of work?"**

That is the real lesson from OpenAI's WebSocket architecture.

---

## Source

OpenAI — *Speeding up agentic workflows with WebSockets*

https://openai.com/index/speeding-up-agentic-workflows-with-websockets/
