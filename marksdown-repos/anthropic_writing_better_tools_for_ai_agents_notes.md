# 🧠 Writing Better Tools for AI Agents — Explained in Simple Language

**Based on Anthropic’s article: “Writing effective tools for agents — with agents”**  
**Reading time: ~10 minutes**

---

# 1. The Big Idea

Imagine you hire a very smart employee.

The employee can:

- understand English
- reason about problems
- make plans
- decide what to do next

But you give this employee **bad tools**.

For example:

```text
Employee: "Find customer information."

Tool:
get_all_customers()

Result:
10,00,000 customers
```

The employee now has to search through **10 lakh customers**.

The employee is smart.

The **tool is stupid**.

That is the central idea:

```text
             AI Agent
                |
                v
       +----------------+
       |     TOOLS      |
       +----------------+
          /     |     \
         v      v      v
      Search   DB     APIs
         |
         v
    Real World
```

### Key idea

**The quality of an AI agent depends heavily on the quality of its tools.**

Tools for AI agents should not simply be traditional APIs wrapped in an LLM interface.

---

# 2. What Exactly Is an AI Tool?

Suppose you ask:

> "Should I take an umbrella today?"

An AI agent could:

```text
User
 |
 v
"Should I take umbrella?"
 |
 v
AI Agent
 |
 +----> Already knows weather?
 |
 +----> Ask user location?
 |
 +----> Call weather tool?
 |
 +----> Search internet?
 |
 v
Answer
```

The agent decides **whether to use a tool and which tool to use**.

### Traditional programming

```text
Application
     |
     | getWeather("Chennai")
     v
Weather API
     |
     v
Weather Data
```

The programmer explicitly decided what happens.

### Agentic AI

```text
User
 |
 v
LLM
 |
 | "What should I do?"
 |
 +------> Weather Tool
 |
 +------> Search Tool
 |
 +------> Calendar Tool
 |
 +------> Ask User
 |
 v
Answer
```

The LLM makes the decision.

That's why tool design becomes extremely important.

---

# 3. The First Mistake: "More Tools = Better Agent"

A common engineering instinct is:

> "Let's expose everything!"

For example:

```text
                AI Agent
                   |
       +-----------+-----------+
       |           |           |
   list_users   get_user   delete_user
       |
   list_orders
       |
   get_order
       |
   list_products
       |
   search_products
       |
   create_order
       |
   update_order
       |
      ...
```

Sounds powerful.

But now the agent has to decide:

> "Which of these 50 tools should I use?"

This increases the agent's decision-making burden.

### Better approach

Start with a **small number of thoughtful, high-impact tools** rather than exposing every underlying API.

---

# 4. Think Like a Human

Imagine you are working in a bank.

You need to investigate:

> "Why was customer 9182 charged three times?"

Would you want these tools?

```text
get_customer()
list_transactions()
get_transaction()
search_logs()
get_logs()
get_payment()
get_payment_status()
get_account()
...
```

Or would you prefer:

```text
investigate_payment_issue(customer_id)
```

The second approach is closer to how a human thinks.

```text
              Agent
                |
                v
   investigate_payment_issue()
                |
       +--------+--------+
       |        |        |
       v        v        v
    Logs   Transactions Customer
       |        |        |
       +--------+--------+
                |
                v
       Relevant Context
```

### Important idea

> **The tool should represent a useful task, not necessarily a single API call.**

For example:

```text
BAD / LOW LEVEL

list_users()
list_events()
create_event()
```

Could become:

```text
BETTER

schedule_event()
```

Another example:

```text
BAD

read_logs()
```

Could become:

```text
BETTER

search_logs()
```

Because the second version can return **only the relevant information**.

---

# 5. Tool Design = Context Design

This is one of the most important concepts for an AI architect.

LLMs have a limited amount of context they can effectively process.

Imagine:

```text
LLM Context Window

+--------------------------------------+
| System instructions                  |
| User conversation                    |
| Previous tool calls                  |
| Tool descriptions                    |
| Tool responses                       |
| Other context                        |
|                                      |
|        LIMITED SPACE                 |
+--------------------------------------+
```

Now imagine your tool returns:

```text
10,000 customers
```

Most of that information is useless.

You're wasting the AI's context.

### Bad

```text
search_contacts()

returns:

1. John
2. Jane
3. Rahul
4. Priya
5. ...
...
10,000 contacts
```

### Better

```text
search_contacts("Rahul")

returns:

Rahul Sharma
Engineering Manager
IDFC FIRST Bank
```

The agent gets the **signal**, not the noise.

### Remember

> **Context is a scarce resource.**

---

# 6. Tool Response Should Be "High Signal"

Think about a tool returning this:

```json
{
  "uuid": "7f83a91b-...",
  "mime_type": "image/jpeg",
  "pixel_width": 256,
  "internal_code": "X8292",
  "name": "Rahul"
}
```

The LLM doesn't necessarily need all of that.

Instead:

```json
{
  "name": "Rahul",
  "file_type": "image",
  "image_url": "..."
}
```

The principle is:

```text
        Tool Response
              |
       +------+------+
       |             |
   Useful         Noise
   Context
       |             |
       v             X
      LLM
```

### Rule

**Prioritize contextual relevance over flexibility.**

Avoid unnecessary low-level identifiers and metadata when they don't help the agent reason.

---

# 7. Human Names Are Better Than Cryptic IDs

Consider:

```text
7f82ab9c-83ad-4f...
```

versus:

```text
Rahul Sharma
```

Humans understand the second one more easily.

LLMs also tend to work better with meaningful names and identifiers.

So:

```text
BAD

user_id = "8e7d91ab..."

GOOD

user = "Rahul Sharma"
```

However, sometimes the agent **does need the technical ID** for another tool.

For example:

```text
search_user("Rahul")
       |
       v
Rahul Sharma
ID = 12345
       |
       v
send_message(user_id=12345)
```

### Design principle

Return the human-readable information by default, while preserving technical identifiers when they are required for downstream actions.

---

# 8. Concise vs Detailed Responses

Imagine Slack search returns:

```text
Message:
"Let's discuss the production issue..."

Channel ID:
C0238392

User ID:
U827362

Thread ID:
17283922

Timestamp:
172839...
```

Maybe the agent only needs:

```text
"Let's discuss the production issue..."
```

So you can design:

```text
response_format =
       |
       +---- concise
       |
       +---- detailed
```

### Concise

```text
Just the information needed
to understand the result.
```

### Detailed

```text
Information + IDs + metadata
needed for subsequent actions.
```

This can dramatically reduce token consumption.

### Simple rule

> **Give the agent only as much information as it needs for the current task.**

---

# 9. Token Efficiency Matters

Many engineers think:

> "Token cost is mainly about the prompt."

For agents, tool responses can become a major part of the context.

Consider:

```text
Agent
 |
 +--> Tool call 1
 |       |
 |       +--> 10,000 tokens
 |
 +--> Tool call 2
 |       |
 |       +--> 8,000 tokens
 |
 +--> Tool call 3
 |       |
 |       +--> 12,000 tokens
 |
 v
Final answer
```

The agent's context becomes huge.

Instead:

```text
Agent
 |
 +--> Search → 500 tokens
 |
 +--> Filter → 300 tokens
 |
 +--> Get details → 700 tokens
 |
 v
Final answer
```

Much better.

### Useful techniques

- Pagination
- Filtering
- Date/range selection
- Truncation
- Sensible defaults
- Search instead of full retrieval

---

# 10. Pagination Is Still Important

Suppose you have:

```text
search_transactions()
```

and a customer has:

```text
2 million transactions
```

Don't return:

```text
2,000,000 records
```

Instead:

```text
search_transactions(
    customer_id=9182,
    date_range="last_30_days",
    limit=50
)
```

Result:

```text
50 relevant transactions
+
"More results available"
```

The agent can then decide whether it needs more.

```text
             Search
               |
               v
        +--------------+
        | First 50     |
        +--------------+
               |
         Enough data?
          /       \
        YES       NO
         |         |
         v         v
       Done     Next page
```

### Principle

**Don't force the agent to consume data it didn't ask for.**

---

# 11. Errors Should Teach the Agent

This is a surprisingly important point.

Imagine the agent sends:

```text
customer_id = "Rahul"
```

but the API expects:

```text
customer_id = integer
```

### Bad error

```text
400 Bad Request
```

The agent has little idea what to do.

### Better error

```text
Invalid customer_id.

Expected:
Numeric customer ID.

Example:
customer_id = 9182
```

Now the agent can correct itself.

Think of an error as:

```text
ERROR
  |
  v
"You're wrong."
```

versus:

```text
ERROR
  |
  v
"You're wrong because X.
Try Y."
```

The second is much more useful for agents.

### Rule

> **Errors should be actionable, not merely descriptive.**

---

# 12. Tool Names Matter More Than You Think

Imagine the agent has these tools:

```text
search()
search2()
search_data()
find()
lookup()
query()
```

What should it use?

Confusing.

Instead:

```text
asana_search_projects()
asana_search_users()

jira_search_issues()
jira_search_projects()

slack_search_messages()
slack_search_users()
```

Now the boundaries are obvious.

This is called **namespacing**.

```text
             Tools
               |
       +-------+-------+
       |               |
     Slack            Jira
       |               |
       +-- search      +-- search
       +-- users       +-- issues
       +-- messages    +-- projects
```

### Rule

> **Tool names should communicate purpose and scope immediately.**

---

# 13. Tool Description Is Basically a Mini Prompt

When you create a tool, you might write:

```text
search_logs
```

That's not enough.

The agent needs to understand:

```text
What does this tool do?

When should I use it?

What input does it expect?

What does it return?

What should I NOT use it for?
```

Think of the tool description as:

```text
             TOOL
              |
      +-------+-------+
      |       |       |
    Name   Description Schema
              |
              v
           AI Agent
```

### Good mental model

> **Write the tool description as if you are explaining the tool to a new engineer joining your team.**

---

# 14. Bad Parameter vs Good Parameter

Suppose you create:

```text
get_customer(user)
```

What does `user` mean?

Could it be:

```text
name?
ID?
email?
username?
```

Ambiguous.

Better:

```text
get_customer(customer_id)
```

Or:

```text
search_customer_by_email(email)
```

### Rule

> **Parameter names should make their meaning obvious.**

Avoid vague parameters such as:

```text
user
data
value
input
item
```

when a more specific name is possible.

---

# 15. Don't Build Tools in Isolation

Anthropic recommends an iterative process.

Think of it like this:

```text
      Build Tool
          |
          v
      Test Tool
          |
          v
   Give it to Agent
          |
          v
     Run Evaluation
          |
          v
    Observe Problems
          |
          v
     Improve Tool
          |
          +----------+
                     |
                     v
               Run Again
```

Not:

```text
Build → Deploy → Hope
```

But:

```text
Build
 ↓
Measure
 ↓
Learn
 ↓
Improve
 ↓
Measure again
```

This is **evaluation-driven tool engineering**.

---

# 16. Create Realistic Evaluation Tasks

Don't test with overly simple questions.

### Weak test

```text
"Find customer 9182."
```

### Strong test

```text
"Customer 9182 says they were charged
three times for one purchase.

Find the relevant logs,
determine what happened,
and check whether other customers
were affected."
```

Why is the second better?

Because a real agent may need:

```text
Customer
   ↓
Transactions
   ↓
Payment logs
   ↓
Search similar incidents
   ↓
Correlate evidence
   ↓
Answer
```

### Rule

> **Evaluate tools using realistic, multi-step workflows rather than toy questions.**

---

# 17. Measure More Than "Did It Work?"

Suppose the agent successfully solved 90% of tasks.

You might think:

> "Excellent!"

But look deeper.

Track:

```text
                    Agent Evaluation
                           |
       +---------+---------+---------+---------+
       |         |         |         |         |
    Accuracy   Tokens   Tool Calls Errors   Runtime
```

For example:

| Metric | Result |
|---|---:|
| Task success | 90% |
| Average tool calls | 17 |
| Average tokens | 35K |
| Tool errors | 8% |
| Runtime | 42 sec |

Maybe the agent is successful—but incredibly inefficient.

### Important metrics

- Task success / accuracy
- Token consumption
- Number of tool calls
- Tool errors
- Runtime / latency
- Cost

---

# 18. Read the Tool-Calling Transcript

This is like debugging a production system.

Don't only look at:

```text
FINAL ANSWER
```

Look at:

```text
User request
     ↓
LLM decision
     ↓
Tool call
     ↓
Tool response
     ↓
LLM decision
     ↓
Tool call
     ↓
Tool response
     ↓
Final answer
```

You might discover:

```text
Tool #1 → unnecessary
Tool #2 → wrong parameter
Tool #3 → correct
Tool #4 → duplicate
Tool #5 → correct
```

That tells you where your tool design is weak.

### Debugging mindset

Treat an agent transcript almost like an application trace:

```text
Request
  ↓
Decision
  ↓
Action
  ↓
Result
  ↓
Decision
  ↓
Action
```

---

# 19. Let the AI Help Improve Its Own Tools

This is one of the most interesting ideas.

You can take evaluation transcripts:

```text
100 Agent Runs
      |
      v
+----------------------+
| Tool calls           |
| Tool responses       |
| Errors               |
| Final answers        |
+----------------------+
          |
          v
       Claude
          |
          v
"Why did agents fail?"
          |
          v
Suggested improvements
```

Then use an AI coding agent to improve:

- Tool implementation
- Tool descriptions
- Schemas
- Response formats
- Error messages
- Filtering
- Search behavior

The cycle becomes:

```text
Agent runs
    ↓
Collect traces
    ↓
Find failure patterns
    ↓
AI suggests changes
    ↓
Engineer reviews
    ↓
Update tools
    ↓
Run evaluation again
```

---

# 20. One Important Warning: Don't Overfit

Suppose you have 100 evaluation questions.

You optimize your tools until:

```text
Training evaluation = 99%
```

Fantastic!

But then you test 100 **new questions**:

```text
New evaluation = 78%
```

You overfit.

So maintain:

```text
              Evaluation Data
                    |
             +------+------+
             |             |
          Training       Held-out
           tests           tests
             |               |
        Improve tools     Don't touch
             |               |
             +-------+-------+
                     |
                     v
              Real performance
```

### Rule

> **Always keep a held-out evaluation set.**

This tells you whether your improvements actually generalize.

---

# 21. The Complete Mental Model

If you are building an **AI Agent Platform**, remember this architecture:

```text
                         USER
                           |
                           v
                    +-------------+
                    |  AI AGENT   |
                    |    LLM      |
                    +-------------+
                           |
                    "What should I do?"
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
       Search Tool     Customer Tool   Payment Tool
            |              |              |
            v              v              v
         Search           DB/API         DB/API
            |              |              |
            +--------------+--------------+
                           |
                           v
                    Relevant Context
                           |
                           v
                    +-------------+
                    |  AI AGENT   |
                    +-------------+
                           |
                           v
                      Final Answer
```

The critical engineering question isn't:

> **"How many APIs can I expose?"**

It is:

> **"What tools allow the agent to solve real tasks efficiently?"**

---

# 22. The 7 Rules to Remember

## ① Fewer, smarter tools

```text
10 mediocre tools
       ↓
Not necessarily better

5 well-designed tools
       ↓
Often more useful
```

## ② Design around tasks

```text
API thinking:
"One endpoint = one tool"

Agent thinking:
"One useful task = one tool"
```

## ③ Return signal, not noise

```text
1000 irrelevant records ❌

10 relevant records     ✅
```

## ④ Save context

```text
Less useless context
        ↓
More useful reasoning
```

## ⑤ Name things clearly

```text
search()              ❌

jira_search_issues()  ✅
```

## ⑥ Make errors actionable

```text
"400 Bad Request" ❌

"customer_id must be numeric.
Example: 9182"     ✅
```

## ⑦ Measure and improve

```text
Build
 ↓
Evaluate
 ↓
Inspect
 ↓
Improve
 ↓
Evaluate again
```

---

# 23. The Big Takeaway for an AI Architect

Traditional software engineering often looks like:

```text
Requirements
     ↓
API
     ↓
Implementation
     ↓
Unit Tests
     ↓
Production
```

Agentic AI requires an additional mindset:

```text
                 REAL TASK
                    |
                    v
               DESIGN TOOL
                    |
                    v
               TEST WITH LLM
                    |
                    v
             OBSERVE BEHAVIOR
                    |
                    v
              MEASURE METRICS
                    |
                    v
             IMPROVE TOOL
                    |
                    v
             TEST AGAIN
                    |
                    +-------> repeat
```

The important shift is:

> **You are no longer only designing APIs for software. You are designing an environment in which an AI agent can successfully reason and act.**

Effective agent tools are:

- Clearly defined
- Context-efficient
- Composable
- Task-oriented
- Easy for the agent to understand
- Designed around real-world workflows
- Continuously evaluated

---

# 🧠 One-Line Memory Trick

Remember:

```text
              GREAT AGENT TOOLS
                     |
       +-------------+-------------+
       |             |             |
    FEW TOOLS     GOOD CONTEXT   CLEAR SPECS
       |             |             |
       v             v             v
    Less choice   Less noise    Less confusion
       \             |             /
        \            |            /
         +-----------+-----------+
                     |
                     v
              BETTER AGENT
```

### In simple words

> **Don't give the AI 100 tools and expect it to become smarter. Give it the right tools, give it the right information, make the tools easy to understand, and continuously test how well it uses them.**

---

## Source

Anthropic Engineering — **Writing effective tools for agents — with agents**

https://www.anthropic.com/engineering/writing-tools-for-agents
