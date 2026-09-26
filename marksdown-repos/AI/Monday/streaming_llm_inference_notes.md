# Streaming LLM Inference: Building a More Continuous, Interruptible AI

**Source:** https://columbus.aitinkerers.org/talks/rsvp_orGZOpQ-nT4

> Notes based on the talk transcript. The linked AI Tinkerers page is members-only, so these notes primarily summarize the transcript provided with the request.

---

## 1. The Big Idea

The speaker is building a **new LLM inference engine from scratch**.

He is **not creating a new AI model**. Instead, he takes an existing open-weight model and changes **how the model runs internally**.

The goal is to move from:

```text
Prompt → Think → Generate → Stop
```

toward:

```text
Think → Receive new information → Adjust thinking → Continue
```

In simple terms, he wants an LLM that behaves more like a **continuous thinking system** instead of a one-shot text generator.

---

## 2. The Problem with Today's LLMs

Imagine asking an LLM:

> "Read this huge file and summarize it."

The model starts generating an answer.

Halfway through, you realize it is going in the wrong direction and say:

> "Don't use Python. Use Linux commands."

With traditional inference, you normally have to **interrupt/cancel the current generation**, add the new instruction, and generate again.

The previous generation may effectively be discarded or require another inference pass.

The speaker wants something different:

```text
Generate
   ↓
New instruction arrives
   ↓
Integrate instruction
   ↓
Continue thinking
```

Instead of:

```text
Generate
   ↓
STOP
   ↓
Rebuild prompt
   ↓
Generate again
```

---

## 3. Why This Is Difficult

An LLM looks simple from the outside:

```text
Prompt
  ↓
Tokens
  ↓
Transformer
  ↓
Next token
  ↓
Next token
  ↓
Next token
```

Internally, however, the tokens pass through many transformer layers.

The speaker's inference engine gives him much more control over these internal representations.

Conceptually:

```text
Input
  ↓
Layer 1
  ↓
Layer 2
  ↓
Layer 3
  ↓
...
  ↓
Layer 48
  ↓
Output
```

Traditional inference engines largely behave like **black boxes**:

```text
Input → Inference Engine → Output
```

The speaker wants to expose and manipulate more of what happens inside:

```text
Input
 ↓
Internal model state
 ↓
Transformer layers
 ↓
Internal model state
 ↓
Output
```

---

## 4. Streaming Inference

This is the central idea of the talk.

Normal application-level streaming often means receiving small pieces of output:

```text
LLM
 ↓
Small batch
 ↓
Application
 ↓
Small batch
 ↓
Application
```

The speaker's approach is deeper.

He wants **streaming at the inference-engine level**.

That means the model can potentially receive new information while it is already generating.

Conceptually:

```text
                     New user input
                           ↓
                           ↓
Model thinking ────────────●──────────→ continues
                           ↑
                    adjust internal state
```

The model does not have to completely restart.

---

## 5. Interrupting at a Natural Point

One interesting technique discussed is using **entropy**.

### Low entropy

Low entropy means:

> "I have a very good idea what comes next."

Example:

```text
The capital of France is...
```

The next word is highly predictable:

```text
Paris
```

### High entropy

High entropy means:

> "There are many possible things I could say next."

For example:

```text
Here is the next feature:
```

Many different things could follow.

The speaker uses this property to identify a **good interruption point**.

Instead of stopping randomly in the middle of a word, the system can stop around a point where the model is naturally transitioning to another thought.

---

## 6. Why Clean Interruption Matters

Suppose a model is generating:

```text
The best approach is to use strea...
```

and the generation is suddenly cancelled.

The model may later see the incomplete text and become confused.

It may even produce something like:

> "I apologize for the garbled output..."

The speaker argues that clean interruption avoids this problem.

The model effectively gets:

```text
Previous reasoning
       +
New instruction
       ↓
Continue
```

rather than:

```text
Broken generation
       +
New instruction
       ↓
Try to recover
```

---

## 7. Ring Buffer and Internal State

The implementation uses a **ring buffer**.

A simplified view is:

```text
┌─────────┐
│ Layer 1 │
├─────────┤
│ Layer 2 │
├─────────┤
│ Layer 3 │
├─────────┤
│   ...   │
├─────────┤
│ Layer 48│
└─────────┘
```

Instead of treating the entire internal state as something disposable, the system allows the layers to retain their own state.

This becomes important for the memory mechanism.

---

## 8. A Different Kind of AI Memory

Traditional RAG generally works like this:

```text
Conversation
      ↓
Create embeddings
      ↓
Vector database
      ↓
Search relevant text
      ↓
Put text into prompt
      ↓
LLM
```

For example, the system might remember:

> "The user prefers Java."

Later, RAG retrieves that sentence and adds it to the prompt.

The speaker's system attempts something different.

It saves **internal model state**, which he calls **memory diffs**.

Conceptually:

```text
Conversation
     ↓
Model internal state
     ↓
State across many layers
     ↓
Calculate the difference
     ↓
Save to disk
```

Later:

```text
New conversation
      ↓
Memory search
      ↓
Find relevant memory
      ↓
Restore internal state
      ↓
Continue inference
```

The speaker reported that restoring this memory can be extremely fast.

---

## 9. RAG vs Internal-State Memory

| Traditional RAG | Internal-State Memory |
|---|---|
| Stores text | Stores model state |
| Uses embeddings | Searches memory representations |
| Retrieved text goes back into the prompt | Internal state can be restored |
| Model processes retrieved text again | Potentially less reprocessing |
| Mostly explicit information | Can preserve contextual state |

A simple way to think about the difference:

**RAG:**

> "Here is something you previously told me."

**Internal-state memory:**

> "Here is some of the internal context/state associated with that previous experience."

This is closer to the concept of **episodic memory**.

---

## 10. How Can a 4K Context Handle Huge Documents?

The prototype uses a relatively small active context.

Yet the speaker demonstrated the idea of processing very large documents, such as *War and Peace*.

The trick is **streaming**.

Instead of:

```text
Entire book → LLM context
```

the system can do:

```text
Book
 ↓
Small chunk
 ↓
Process
 ↓
Memory
 ↓
Next chunk
 ↓
Process
 ↓
Memory
 ↓
Next chunk
```

This is similar to **stream processing** in distributed systems.

The model does not need the entire document in active context at once.

---

## 11. Quiescence: Don't Spend Equal Compute Everywhere

Another interesting idea is called **quiescence**.

The basic idea:

> Not every token needs the same amount of computation.

Consider:

```text
I want to calculate A and B and C.
```

The word `and` may not significantly change the meaning.

But a word such as `NOT` can completely change the meaning.

So potentially:

```text
Important token
    ↓
More transformer layers

Less important token
    ↓
Fewer transformer layers
```

The speaker uses this as a configurable mechanism to reduce computation.

This is an example of **adaptive computation**.

Instead of:

```text
Every token → exactly the same work
```

the system tries to do:

```text
Important token → more work
Less important token → less work
```

---

## 12. The Model Itself Was Not Fine-Tuned

An important point:

The speaker used a **vanilla open-weight Gemma model**.

The main experimentation was performed in the **inference engine**, not by modifying the model's trained weights.

So conceptually:

```text
                 Same model
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
 Traditional engine     New inference engine
          ↓                   ↓
     Normal LLM        Streaming + memory
```

This is important because it suggests that **the inference/runtime layer itself can significantly affect how an AI system behaves**.

---

## 13. Why This Could Matter for AI Agents

Today's AI agents often work roughly like:

```text
User
 ↓
LLM
 ↓
Tool
 ↓
LLM
 ↓
Tool
 ↓
LLM
 ↓
Answer
```

Each step can involve another inference cycle.

A continuously streaming inference engine could potentially support:

```text
             ┌──────────────┐
             │     LLM      │
             │ continuously │
             │   thinking   │
             └──────┬───────┘
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
        User      Tools     Memory
        input     results   retrieval
          │         │         │
          └─────────┴─────────┘
                    ↓
              Continue thinking
```

The agent could potentially incorporate new information without fully restarting its reasoning process.

---

## 14. Robotics Is an Interesting Use Case

Someone at the talk mentioned robotics.

This makes sense because robots operate in a continuously changing environment.

Imagine:

```text
Robot plan:
Move forward 2 meters
       ↓
Turn left
       ↓
Pick up object
```

Suddenly the camera detects an obstacle.

A traditional approach may require interrupting the current reasoning and starting a new cycle.

A streaming approach could potentially do:

```text
Plan
 ↓
Observe environment
 ↓
New information arrives
 ↓
Adjust plan
 ↓
Continue
```

The world does not wait for an LLM to finish generating a paragraph.

---

## 15. The Bigger Idea: LLM as a Continuous Process

Most LLM applications think about AI like this:

```text
INPUT
  ↓
PROCESS
  ↓
OUTPUT
```

The speaker is exploring something closer to:

```text
             ┌─────────────────────┐
             │                     │
             ↓                     │
INPUT → THINK → OBSERVE → ADJUST ──┘
              ↑
            MEMORY
```

Instead of an LLM being primarily a **stateless text generator**, it starts looking more like a **continuously running cognitive process**.

---

## 16. What Is Still Unproven?

The talk demonstrates an interesting engineering prototype, but several claims still need rigorous benchmarking.

### Demonstrated / discussed

- Streaming interruption
- Internal-state memory
- Ring-buffer architecture
- Memory diffs
- Adaptive layer processing
- Running an open-weight model
- Fast memory restoration
- Processing large information streams in small chunks

### Still requiring validation

- Does accuracy improve?
- Does hallucination actually decrease at scale?
- Does it consistently outperform existing inference engines?
- How does it work with other model families?
- How much GPU/CPU efficiency is gained?
- How well does memory work over months of interaction?
- How does it perform on standard benchmarks?

The speaker specifically discussed the need to benchmark the **same model running on different inference engines**.

That would be a useful apples-to-apples comparison.

---

# 17. The Simplest Mental Model

Think of a traditional LLM as a person writing an answer on paper.

You say:

> "Stop."

They throw away the paper and start again.

The proposed system is more like:

> "Pause."

Then you say:

> "Actually, don't use Python."

The system responds:

> "Got it."

And continues from there.

The more ambitious part is that instead of remembering only the **words**, the system attempts to preserve some of the **internal state associated with the interaction**.

---

# 18. Three Key Takeaways

### 1. Streaming

**Interrupt the model while it is thinking and let it continue with new information.**

### 2. Internal Memory

**Store richer model state instead of only storing text memories.**

### 3. Adaptive Computation

**Spend more computation on important information and less on information that changes little.**

---

# Final Takeaway

The project is an attempt to turn an LLM from:

```text
Prompt → Answer
```

into:

```text
Think → Observe → Remember → Adjust → Continue
```

The important innovation is **not primarily a new model**.

It is the **inference engine underneath the model**.

That opens an interesting direction for future AI systems—especially **AI agents, robotics, long-running assistants, real-time systems, and systems that need persistent memory and continuous interaction**.
