# 🧪 Demystifying Evals for AI Agents — Explained Simply

**Based on Anthropic Engineering's “Demystifying evals for AI agents”**  
**Reading time: ~6 minutes**

---

# 1. What is an "Eval"?

Think of an **eval** as an exam for an AI agent.

For a normal application:

```text
Input
  ↓
Program
  ↓
Output
  ↓
PASS / FAIL
```

For an AI agent:

```text
User Task
    ↓
+----------------+
|   AI Agent     |
|                |
| Think          |
| Call tools     |
| Try something  |
| Adapt          |
+----------------+
    ↓
Final Result
    ↓
GRADER
    ↓
PASS / FAIL
```

An eval answers:

> **"Can my AI agent actually do what I expect it to do?"**

---

# 2. Why Are Agent Evals Difficult?

A traditional LLM might work like:

```text
Question
   ↓
LLM
   ↓
Answer
```

Easy to test.

But an agent works more like:

```text
                    USER
                      |
                      v
                  AI AGENT
                      |
                "What should I do?"
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Search       Database     API
          |           |           |
          +-----------+-----------+
                      |
                  New result
                      |
                      v
                 AI AGENT
                      |
                 Another tool
                      |
                      v
                 Final result
```

There are many opportunities for something to go wrong.

```text
Task
 ↓
Wrong tool
 ↓
Wrong result
 ↓
Wrong decision
 ↓
Another wrong tool
 ↓
Wrong final answer
```

**One mistake can create another mistake.**

---

# 3. The 7 Important Words

## 1. Task

The problem given to the agent.

```text
"Refund this customer's payment."
```

## 2. Trial

One attempt at solving the task.

Because AI is non-deterministic, you may run the same task multiple times.

```text
Task
 |
 +--> Trial 1 → PASS
 |
 +--> Trial 2 → FAIL
 |
 +--> Trial 3 → PASS
```

## 3. Grader

The thing that decides whether the agent succeeded.

## 4. Transcript

The complete history of what happened.

```text
User
 ↓
Agent action
 ↓
Tool call
 ↓
Tool response
 ↓
Agent action
 ↓
Tool call
 ↓
Final answer
```

## 5. Outcome

What actually happened in the environment.

For example:

```text
Agent says:

"Your flight is booked."

             BUT

Database says:

reservation = NOT CREATED
```

The **outcome is NOT booked**.

## 6. Evaluation Harness

The infrastructure that runs everything:

```text
Tasks
 ↓
Run Agent
 ↓
Record transcript
 ↓
Run graders
 ↓
Calculate scores
```

## 7. Evaluation Suite

A collection of many tasks.

```text
Customer Support Eval
       |
       +-- Refund
       +-- Cancellation
       +-- Escalation
       +-- Identity verification
       +-- Payment issue
```

---

# 4. Why Do We Need Evals?

Imagine your team changes the prompt.

Before:

```text
Success = 85%
```

After:

```text
Success = ?
```

Without evals:

```text
Deploy
  ↓
Wait for users
  ↓
User complains
  ↓
Investigate
  ↓
Fix
  ↓
Hope nothing else broke
```

This is **reactive development**.

With evals:

```text
Code Change
    ↓
Run 500 tasks
    ↓
Compare results
    ↓
Regression?
    |
 +--+--+
 |     |
YES    NO
 |     |
Fix   Deploy
```

### Key idea

**Evals let you see behavioral changes before they become production problems.**

---

# 5. Three Types of Graders

There are three major ways to judge an agent.

```text
                 GRADERS
                    |
       +------------+------------+
       |            |            |
       v            v            v
     CODE          LLM          HUMAN
```

## A. Code-based grader

Example:

```text
Did the API return HTTP 200?

YES → PASS
NO  → FAIL
```

Or:

```text
Did unit tests pass?

YES → PASS
NO  → FAIL
```

### Advantages

- Fast
- Cheap
- Objective
- Repeatable

### Problem

It struggles with subjective questions.

For example:

> "Was the customer treated politely?"

Hard to judge with simple code.

---

# 6. LLM-Based Grader

Now ask another AI to judge the response.

```text
Agent
  |
  v
Answer
  |
  v
+----------------+
|  Judge LLM     |
+----------------+
  |
  v
Score
```

Example:

> Did the support agent show empathy?

The LLM judge can evaluate that.

### Advantages

- Flexible
- Handles natural language
- Can judge nuanced answers
- Scales better than humans

### Problem

The judge itself can make mistakes.

Therefore:

```text
LLM Judge
    ↓
Compare against
human experts
    ↓
Calibrate
```

---

# 7. Human Grader

Sometimes humans need to judge the result.

```text
Agent Result
     ↓
Human Expert
     ↓
PASS / FAIL / SCORE
```

Humans are particularly useful for:

- subjective quality
- expert judgment
- calibrating LLM judges
- spot checking

But:

```text
Human
 ↓
Slow
 ↓
Expensive
```

So the practical model is usually:

```text
            EVALUATION
                 |
      +----------+----------+
      |          |          |
     CODE       LLM       HUMAN
      |          |          |
    cheap      scalable   accurate
```

---

# 8. Capability Eval vs Regression Eval

This is **very important**.

## Capability Eval

Question:

> **"What can my agent do?"**

Suppose your agent currently succeeds only 30% of the time.

```text
Capability Eval

Success = 30%

     ↓

Improve agent

     ↓

Success = 50%

     ↓

Improve

     ↓

Success = 75%
```

You're trying to **climb the hill**.

---

## Regression Eval

Question:

> **"Can the agent still do everything it could previously do?"**

Suppose:

```text
Old capability:

Refund → PASS
Cancel → PASS
Escalate → PASS
Search → PASS
```

You change the agent.

Now:

```text
Refund → PASS
Cancel → FAIL  ← REGRESSION
Escalate → PASS
Search → PASS
```

The regression eval catches the problem.

### Easy memory trick

```text
CAPABILITY
"What can we learn to do?"

REGRESSION
"What must we NOT break?"
```

---

# 9. Don't Only Check the Final Answer

This is one of the biggest lessons.

Imagine:

```text
Agent says:

"Refund completed."
```

Looks correct.

But inspect the system:

```text
Payment database:

refund_status = PENDING
```

The agent **said the right thing but did the wrong thing**.

Therefore:

```text
             AGENT
               |
       +-------+-------+
       |               |
   Transcript        Outcome
       |               |
 "What did it do?"  "What happened?"
```

You should often check **both**.

---

# 10. Don't Force the Agent to Follow One Exact Path

Suppose you expect:

```text
Step 1 → Search customer
Step 2 → Get transaction
Step 3 → Refund
```

But the agent discovers a different valid path:

```text
Step 1 → Get transaction
Step 2 → Search customer
Step 3 → Refund
```

If the final result is correct, should it fail?

Usually, **no**.

Think:

```text
BAD EVAL

"Did you follow MY exact steps?"

BETTER EVAL

"Did you achieve the correct result?"
```

### Principle

Evaluate **outcomes and important constraints**, not arbitrary implementation paths.

---

# 11. Give Partial Credit

Imagine a customer support agent needs to process a refund.

Agent A:

```text
Identified customer
      ↓
Verified identity
      ↓
Found transaction
      ↓
Refunded
```

Agent B:

```text
Identified customer
      ↓
Verified identity
      ↓
Found transaction
      ↓
Failed to refund
```

Agent B is not completely useless.

So don't always use:

```text
PASS = 1
FAIL = 0
```

You might use:

```text
Identity verified       +25
Correct transaction     +25
Correct diagnosis       +25
Refund completed        +25

Total = 75/100
```

### Principle

**Use partial credit when a task contains multiple meaningful components.**

---

# 12. Non-Determinism: AI Doesn't Behave the Same Every Time

This is fundamental.

Ask an AI the same question 10 times:

```text
Trial 1 → PASS
Trial 2 → PASS
Trial 3 → FAIL
Trial 4 → PASS
Trial 5 → PASS
Trial 6 → FAIL
...
```

Therefore:

```text
One test
   ↓
Not enough
```

Instead:

```text
             TASK
               |
       +-------+-------+
       |       |       |
    Trial 1 Trial 2 Trial 3
       |       |       |
      PASS    FAIL    PASS
```

You can calculate the success rate.

---

# 13. Pass@K vs Pass^K — Easy Explanation

These two metrics sound complicated but are simple.

## pass@k

Question:

> **"If I try K times, did I succeed at least once?"**

Example:

```text
3 attempts

PASS
FAIL
FAIL
```

At least one success?

**Yes.**

So pass@3 = success.

Useful when:

> One good solution is enough.

---

## pass^k

Question:

> **"Did I succeed every single time?"**

Example:

```text
PASS
PASS
FAIL
```

No.

Therefore pass^3 fails.

Useful when:

> **Consistency is important.**

### Easy memory trick

```text
pass@k
   =
"Did I get at least ONE success?"

pass^k
   =
"Did I get success EVERY time?"
```

---

# 14. How to Start Evals: You Don't Need 1,000 Tests

Don't say:

> "We need 10,000 test cases before starting."

Start with:

```text
20–50 real tasks
```

Especially:

```text
Real user failures
        +
Manual tests
        +
Important workflows
```

For example:

```text
Initial Eval Suite

20 tasks
  ↓
Run
  ↓
Find failures
  ↓
Add new tasks
  ↓
30 tasks
  ↓
Run
  ↓
50 tasks
  ↓
100 tasks
```

### Principle

> **Start early. Grow the eval suite from real failures.**

---

# 15. Your Eval Tasks Must Be Unambiguous

Bad task:

```text
"Create a script."
```

Create it where?

```text
/script.py?
/src/script.py?
/tmp/script.py?
```

If your grader expects:

```text
/src/script.py
```

but the task didn't say that, the agent may fail unfairly.

### Good task

```text
Create the script at:

/src/script.py

Then run the provided tests.
```

The rule is:

```text
Ambiguous task
      ↓
Bad measurement
      ↓
Bad engineering decision
```

### Important lesson

A 0% score can sometimes mean the **task or grader is broken**, not that the model is incapable.

---

# 16. Test Both "Should" and "Should NOT"

Suppose you're testing a web-search agent.

You test:

```text
"What's today's weather?"
        ↓
Should search
```

Great.

But what about:

```text
"Who founded Apple?"
        ↓
Should NOT necessarily search
```

If you only test the first type, your AI may learn:

```text
SEARCH EVERYTHING!
```

Therefore:

```text
             Search Eval
                  |
        +---------+---------+
        |                   |
   SHOULD SEARCH       SHOULD NOT SEARCH
        |                   |
     Weather             Simple facts
     Current news        Existing knowledge
```

### Principle

**A good eval tests both positive and negative behavior.**

---

# 17. Keep Every Trial Clean

Imagine Trial #2 can see files created by Trial #1.

```text
Trial 1
  ↓
Creates file
  ↓
Trial 2
  ↓
Sees file
  ↓
Gets unfair advantage
```

Your evaluation becomes unreliable.

Instead:

```text
Trial 1 → Clean Environment
Trial 2 → Clean Environment
Trial 3 → Clean Environment
Trial 4 → Clean Environment
```

Each test should ideally start from a known state.

### Principle

**Isolate trials and control the environment.**

---

# 18. The Complete Eval Pipeline

Put everything together:

```text
                    USER TASKS
                        |
                        v
              +-------------------+
              |  EVAL HARNESS     |
              +-------------------+
                        |
                        v
                   AI AGENT
                        |
             +----------+----------+
             |          |          |
             v          v          v
           Tool       Tool       Tool
             |          |          |
             +----------+----------+
                        |
                        v
                  Final Outcome
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
       Code Grader   LLM Grader   Human Review
          |             |             |
          +-------------+-------------+
                        |
                        v
                     SCORE
                        |
                        v
                 Analyze Transcript
                        |
                        v
                  Improve Agent
                        |
                        +---------> Repeat
```

That's **eval-driven agent development**.

---

# 19. The Most Important Mental Model

Think of your AI agent like a junior engineer.

You don't say:

> "I ran it once and it worked."

Instead, you ask:

```text
Can it do the task?
       ↓
Can it do it repeatedly?
       ↓
Does it handle edge cases?
       ↓
Does it make unnecessary tool calls?
       ↓
Does it modify the correct state?
       ↓
Did my latest change break something?
```

That's exactly what good evals answer.

---

# 🧠 10 Rules to Remember

```text
1. Eval = exam for an AI agent

2. Test real tasks, not toy examples

3. Check outcomes, not just answers

4. Use code graders where possible

5. Use LLM graders for subjective quality

6. Use humans to calibrate and validate

7. Test both SHOULD and SHOULD NOT behavior

8. Run multiple trials because AI is non-deterministic

9. Keep regression tests so improvements don't break old capabilities

10. Read the transcripts — never blindly trust the score
```

---

# 🚀 For an AI Architect: The Big Picture

Traditional software:

```text
CODE
 ↓
UNIT TEST
 ↓
PASS / FAIL
```

Agentic AI:

```text
             AGENT
               |
       +-------+-------+
       |       |       |
    Reason   Tools   Environment
       |       |       |
       +-------+-------+
               |
               v
          Final Outcome
               |
      +--------+--------+
      |        |        |
     Code     LLM     Human
   Grader    Grader   Review
      |        |        |
      +--------+--------+
               |
               v
             SCORE
               |
               v
        Improve Agent
               |
               +-------> Repeat
```

### The key shift

> **You are not just testing whether an LLM gives the right answer. You are testing whether an autonomous system can reliably achieve the desired outcome.**

And that is the real meaning of **evals for AI agents**.

---

## Source

Anthropic Engineering — **Demystifying evals for AI agents**

https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
