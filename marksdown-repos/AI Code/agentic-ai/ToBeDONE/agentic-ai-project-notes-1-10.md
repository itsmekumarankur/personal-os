# Agentic AI Project Guide: Projects 1 to 10

## Part A: Projects 1 to 5

*Projects 1 to 5 in plain words. For each one: the one-line idea, the new words, why we learn it, what we gain, and what to watch out for. Tap a project to open it.*

---
## The big picture — How the five projects stack up

Claude is a very smart brain, but a brain alone can only talk. Each project adds one new power around that brain. Every step stands on the one below it.

```
 5  PARALLEL   many helpers work at the same time
 4  ROUTING    a receptionist sends you to the right helper
 3  CHAINING   step 1 -> step 2 -> step 3
 2  RAG        the brain reads YOUR documents
 1  TOOLS      the brain can DO things, not only talk
 0  BASE       FastAPI + Docker + AWS (inside all five)
```

### Two words to remember: workflow and agent

Anthropic's guide on building agents uses these two words. They are the most useful idea in the whole course.

```
 WORKFLOW  (projects 3, 4, 5)
 You draw the road in code. The model works at each stop.

   start --> step A --> step B --> step C --> end
```

```
 AGENT  (projects 1, 2)
 The model chooses the next step. Your code is the safety fence.

   start --> think --> need a tool? --no--> answer
               ^             |
               |            yes
               +--- use the tool, read the result
```

**Why this matters for an architect.** A workflow is predictable: same steps, easy to test, easy to cost. An agent is flexible: it can handle surprises, but you give up some control. Pick the least freedom that solves the problem. Anthropic's guide gives the same advice: start simple and add a pattern only when it clearly helps.

### What stays the same in all five

Every project is a small web service (FastAPI) in a Docker container, deployed on AWS with Terraform. We learned that once in Project 1. After that, only the "brain part" changes. That is the point of a template.

---
## How to understand the code — You do not need to deploy to learn

Do you have to deploy a project to understand it? **No.** Deploying (Docker, ECS, Terraform) teaches infrastructure. The agent ideas live in about 100 to 200 lines of Python per project. Deploy when you want to practise the infra side, and do it once, because the Terraform is almost the same in all five.

Reading alone works, but reading and then poking the code works much better. Use this path for every project:

```
 1. README + ASCII picture   get the idea in one sentence
        |
 2. Core file only          skip main.py, Dockerfile, infra/ for now
        |
 3. The tests               each test = one behaviour in plain words
        |
 4. Run tests, break code   change something, see which test fails
        |
 5. One real run            python cli.py ... with your API key
        |
 6. README exercises        small changes that prove you understood
```

### Which file is the core file?

| Project | Read this first | Then |
|---|---|---|
| 1 Tools | the agent loop in `agent.py` | the tool list and schemas |
| 2 RAG | `rag.py` (chunk, embed, search) | the search tool in `agent.py` |
| 3 Chaining | `chain.py` | the gate in `run_pipeline` |
| 4 Routing | `router.py` | the unknown-route fallback |
| 5 Parallel | `parallel.py` | `review.py`, then `vote.py` |

### Why this order

- **Tests are documentation.** A test like "if the draft fails the gate, the polish step is skipped" or "all five reviewers run at the same moment" tells you what the code is for. The tests run with a fake model, so no API key is needed.
- **Breaking code teaches faster than reading it.** Change the gate condition in Project 3, make the router return an unknown route in Project 4, or set `MAX_WORKERS=1` in Project 5. Then see which test fails and why.
- **One real run shows what tests cannot.** Use the command line, not Docker. It costs a few cents and shows the real prompts and answers. Add a `print` before and after each model call to watch the flow.
- **Keep this page open beside the code.** Match each box in the ASCII picture to a function.

### Be honest about what is tested

The tests use a fake model. I have not run these projects against the live API, Docker or AWS. Your first real run may show small issues, so treat them as part of learning and tell me what you see.

**If you are short on time:** do steps 2, 3 and 5. Deploy only one project end to end (Project 2 is a good pick), so you know the whole path from code to a running service.

---
## Project 1: Tools — Teach the brain to use tools

> *Claude only asks. Your code does the work.*

### The story

Imagine a very smart kid locked in a room with no calculator and no window. They can talk about anything, but they cannot check today's weather and they can slip on a big sum. Now slide a calculator and a phone under the door. The kid decides when to use them. That is a tool.

### The picture

```
 You: "What is 23 x 47? And Chennai weather?"
   |
   v
 +--------+  "run calculator 23*47"  +-----------+
 | CLAUDE | -----------------------> | YOUR CODE |
 | (brain)| <----------------------- | runs it   |
 |        |  result: 1081            +-----------+
 |        |
 |        |  "run get_weather"       +-----------+
 |        | -----------------------> | YOUR CODE |
 |        | <----------------------- | calls a   |
 +--------+  result: 31 C (example)  | weather   |
   |                                 | service   |
   v                                 +-----------+
 "23 x 47 = 1081. Chennai is 31 C."
```

```
 THE LOOP
   ask Claude --> wants a tool? --no--> final answer
        ^              |
        |             yes
        |              v
        +---- run it, send the result back

   Safety stop: give up after 5 rounds (max_turns)
```

```
 HOW IT REACHES THE INTERNET
 laptop            AWS
 +--------+  push  +-----+  pull  +-----------+
 | Docker | -----> | ECR | -----> |    ECS    |
 | image  |        +-----+        |  Fargate  |
 +--------+                       | container |
                 +-----------+    +-----------+
                 |  Secrets  | ------^
                 |  Manager  |  (hands over the API key)
                 +-----------+
```

### New words

- **Tool**: A normal function in your code that Claude is allowed to ask for.
- **Tool schema**: The label on the tool: its name, what it does, and what inputs it needs. Claude chooses a tool by reading this label.
- **tool_use / tool_result**: Claude's request ("please run this") and your answer ("here is what happened").
- **Agent loop**: Ask Claude, run the tool, send the result back, repeat until Claude gives a final answer.
- **max_turns**: A limit on how many rounds the loop may run. It stops endless loops.
- **Docker image / container**: A lunchbox that holds your app and everything it needs. The image is the packed box. The container is the box opened and running.
- **ECR**: A garage in AWS where images are stored.
- **ECS Fargate**: AWS runs your container for you. You do not look after any computer.
- **Secrets Manager**: A locked box for passwords and API keys.
- **Terraform**: You write the setup you want (servers, network, permissions) as a recipe file. Terraform builds it, and can remove it again.

### Why we learn this

A model that can only talk cannot change anything in the real world. Tools turn talking into doing: look things up, calculate, call a company system. Almost every useful AI product is "model plus tools". Everything in Projects 2 to 9 is built on the idea "the model asks, our code acts".

We also learn the full road to production once, so later projects only change the brain part.

### What we gain

- The skill to connect Claude to any function or web service.
- The agent loop pattern, which we reuse again and again.
- A first real deployment: container, AWS, secrets, Terraform.
- A template: later projects copy this folder and change the brain.

### Watch out (architect notes)

- **Claude's request is untrusted input.** Your code decides what really runs. The calculator accepts only digits and math signs. Never run text from a model as free code.
- **Stop runaway loops.** Keep a maximum number of rounds. Each round is a paid call.
- **Tool errors are information.** Send the error back as text so Claude can try something else.
- **Descriptions matter.** A vague tool description means Claude picks the wrong tool.
- **Secrets.** Never put keys in code. In Secrets Manager, store the key as a plain string. The Project 1 doc stored it as JSON without telling ECS which field to read, so the container would get the whole JSON text. Also give the container only the permission it needs. Project 1 used a broad one and Project 2 made it narrow.
- **Open door.** In Project 1 the container has a public address that anyone can call. That is fine for learning. A real service needs a load balancer and a login (Project 2 adds the first, not the second).

### Do not use it when

The steps never change. A fixed sequence in plain code is simpler and cheaper than letting a model decide.

---
## Project 2: RAG — Let the brain read your books first

> *Look up the right page, then answer.*

### The story

Claude learned from the internet. It has never read your company's leave policy. Think of an open-book exam: before answering, you find the right page in your notes, read it, and then write the answer. RAG means "Retrieval Augmented Generation": retrieve first, then generate.

### The picture

```
 ONCE, when the app starts
 docs/ files --> cut into chunks --> turn into numbers --> INDEX
                 (800 letters,       (embedding,           (kept in
                  100 shared)         by Voyage)            memory)

 EVERY question
 "How many leave days carry over?"
        |
        v
 turn the question into numbers
        |
        v
 find the 3 closest chunks in the INDEX
        |
        v
 Claude reads only those chunks --> answer + source file name
```

```
 A "MEANING MAP"  (close together = similar meaning)

   * leave days        * sick leave
        * carry forward

                                  * error 500
                              * server crashed
```

```
 THE FRONT DOOR (new in this project)
 you --> LOAD BALANCER --> container
         fixed address, checks /health.
         The only way in. The container hides behind it.
```

### New words

- **Chunk**: A small piece of a document. We cut long files into pieces so we can find the right piece.
- **Overlap**: Neighbouring chunks share a few letters, so a sentence is not cut in half and lost.
- **Embedding**: A list of numbers that stands for the meaning of a text. Like GPS coordinates, but for meaning.
- **Index**: The shelf where all chunks and their numbers are kept.
- **Similarity**: How close two lists of numbers are. Close means similar meaning. We use the dot product to measure it.
- **Retrieval**: Finding the best chunks for a question.
- **Grounding**: Answering only from what was found. If it was not found, say so.
- **Voyage AI**: A company that makes embeddings. Anthropic does not make its own embedding model and points to Voyage. So this project needs a second API key.
- **Load balancer**: A front door with a fixed address. It checks that the app is alive and sends traffic only to healthy containers.

### Why we learn this

A model does not know your private or fresh information. We could retrain it, but that is slow and expensive. We could paste every document into every question, but that is costly and hits size limits. RAG finds only the few pieces that matter, so it is cheaper, always up to date, and it can show its source.

### What we gain

- Answers from your own data, with the file name to check.
- New knowledge by changing files, with no retraining.
- Fewer made-up answers, because the agent is told to say "I could not find it".
- The idea of embeddings, which is used far beyond chatbots (search, matching, recommendations).

### Watch out (architect notes)

- **Garbage in, garbage out.** Old or wrong documents give old or wrong answers.
- **Chunk size is a trade-off.** Too small and the meaning is lost. Too big and different topics get mixed.
- **Who may see which document?** Search can show a document to the wrong person. Before real use, filter by permission.
- **Documents can carry tricks**, like "ignore your rules". Treat documents as data, not as orders.
- **Test the search and the answer separately.** If the right chunk is not found, even the best model cannot help. Anthropic's RAG cookbook measures retrieval apart from the final answer for this reason.
- **The index lives in memory** and is rebuilt on every start. That is fine for a few hundred documents. Bigger collections need a vector database.
- **Extra key, extra cost.** Every start calls Voyage to embed all chunks.
- **Changing a document means redeploying** in this version.

### Do not use it when

The documents are tiny and fit in the prompt. Or the answer needs calculation, not reading. Then use a tool (Project 1).

---
## Project 3: Prompt chaining — Break one hard job into small easy steps

> *Draft, then critique, then polish.*

### The story

Writing a school essay. First you write a rough draft. Then a friend marks the weak parts. Then you rewrite. If you try to do all three in one go, the essay is usually worse. A model is the same: one small job per step gives better results.

### The picture

```
 request
    |
    v
 [1 DRAFT]  writes a first version
    |
    v
 [2 CRITIC] lists problems + says "pass" or "revise"
    |
    v
 GATE  (a plain Python if-statement, no AI)
    |
    +-- pass ---------------------------> return the draft   (2 calls)
    |
    +-- revise
          |
          v
       [3 POLISH]  sees request + draft + problems
          |
          v
       final text                                             (3 calls)
```

### New words

- **Prompt chaining**: Several model calls in a fixed order. Each one gets what the earlier ones produced.
- **Context**: Everything a step is told. Polish needs the request, the draft and the critique, so we pass all three.
- **Gate**: A check written in normal code between two steps. It decides whether to go on.
- **XML tags**: Labels like `<draft>...</draft>` that let our code find each part of a reply.
- **Fallback parsing**: If the tags are missing, use the raw text instead of crashing.
- **Temperature**: How adventurous the model is. Low means careful and repeatable. High means more creative. The draft is warm (0.7). The critic is cool (0.2).
- **Fake model (in tests)**: A pretend Claude that gives fixed answers. Tests run free, fast, and need no API key.

### Why we learn this

One big prompt that asks for many things does each of them a bit worse. Small steps are easier for the model, and easier for us: when the result is bad, we open the draft and the critique and see exactly where it went wrong. We can also improve one step without touching the others. This is a workflow, so the path is the same every time, which makes it testable.

### What we gain

- Better quality on writing and analysis tasks.
- See-through debugging: every step's output can be inspected.
- Control over cost: the gate skips the last step when it is not needed.
- The habit of testing AI code with a fake model.

### Watch out (architect notes)

- **Three calls cost about three times as much and take about three times as long.** We raised the load balancer timeout to 120 seconds for this reason.
- **Mistakes travel.** A bad draft makes a bad polish. Put gates between steps where you can.
- **Prove the chain helps.** Compare it with one good prompt on real examples. If there is no gain, do not chain.
- **The critic can be too kind or too harsh.** Try it on samples you know.
- **Pass what the next step needs.** A step that cannot see the draft cannot improve it.
- **Keep output formats strict** and always have a fallback.
- **Our tests check the code, not the writing quality.** Judging quality needs real samples and a human eye.

### Do not use it when

The task is simple, or speed matters more than polish.

---
## Project 4: Routing — Send each request to the right expert

> *Sort first, then answer.*

### The story

A school office has a reception desk. "I lost my bag" goes to lost property. "My computer will not log in" goes to IT. "Something serious happened" goes to the principal. The receptionist does not solve anything. They only send you to the right place. A router does the same for requests.

### The picture

```
 ticket
   |
   v
 ROUTER  (small, cheap model)
         writes its reasoning, then picks one team
   |
   +--> billing   --> billing expert prompt   --+
   +--> technical --> technical expert prompt   |
   +--> account   --> account expert prompt     +--> reply
   +--> product   --> product expert prompt   --+
   |
   +--> human, or "not sure"
          --> "A person will follow up"  (no more AI calls)
```

```
 TWO MODELS, ONE JOB EACH
   sorting  = easy  --> small model (fast, cheap)
   writing  = harder --> bigger model (better answers)
```

### New words

- **Router**: The first model call. It only chooses a route. It does not answer.
- **Route**: One path, for example "billing". Each route has its own expert prompt.
- **Specialized prompt**: Instructions for one topic only: who you are, how to start, what to include, what never to invent.
- **Reasoning before choice**: The router first writes why, then chooses. This makes the choice more careful and gives us a note to read later.
- **Escalation**: Handing the case to a human.
- **Fallback**: What happens when the router is unsure or says something unknown: go to a human, never guess.
- **Untrusted input**: Anything a customer writes. It is data, not orders. A ticket that says "ignore your rules" must not change the rules.

### Why we learn this

One giant prompt that covers billing, bugs, accounts and product questions becomes a mess, and every change risks breaking another topic. With routing, each expert prompt is small, clear and can be improved alone. It also saves money: a small model sorts, and the bigger model works only once. And the human route gives a safe exit for cases the AI should not handle.

### What we gain

- Better answers for each type of request.
- Lower cost and faster sorting.
- Easy growth: a new team is one new entry in the list.
- A safety exit to a human.
- Useful numbers: how many tickets per route tells you what customers really need.

### Watch out (architect notes)

- **A wrong route gives a wrong answer.** Test with a list of sample tickets and check where each one goes.
- **Never guess when unsure.** An unknown choice goes to a human. Our code does this.
- **Watch the escalation rate.** Too many escalations means the routes do not fit real traffic. Almost none may mean the router is overconfident.
- **Write clear route descriptions.** Overlapping descriptions confuse the router.
- **Names must match exactly.** The code looks up the route by name, so a typo breaks it.
- **Routing adds one call to every request.** Keep that call small and fast.
- **Tickets hold personal data.** Be careful what you write in logs.

### Do not use it when

There is only one kind of request. Then routing is just extra cost.

---
## Project 5: Parallelization — Many helpers, same time

> *Do independent work together, not one by one.*

### The story

A group project with five friends. One checks spelling, one checks facts, one checks the pictures, and so on, all at the same moment. Then one friend gathers the results. That is much faster than one friend doing five checks in a row. In our project the "friends" are five reviewers of a software design: security, reliability, performance, cost and maintainability.

### The picture

```
 design document
   |
   +--> [security]        --+
   +--> [reliability]       |
   +--> [performance]       +--> Python: worst verdict wins
   +--> [cost]              |             |
   +--> [maintainability] --+             v
                                   1 call: write the summary

   All five run at the same time.
```

```
 one after another:  |--A--|--B--|--C--|--D--|--E--|   5 units of time

 at the same time:   |--A--|
                     |--B--|
                     |--C--|                            1 unit of time
                     |--D--|
                     |--E--|
```

```
 VOTING: the same question, asked 5 times at once

   yes   yes   no   yes   no    -->   YES wins (3 of 5)
                                      agreement: 60 percent
```

### New words

- **Parallel**: Running things at the same time. The opposite is sequential: one after another.
- **Thread**: One worker inside your program. Many threads can wait for the model at once.
- **Thread pool, max_workers**: A team of threads with a limit on how many work at once.
- **Sectioning**: Split a job into independent parts. Each part gets its own helper. This is our review panel.
- **Voting**: Run the same job several times and take the majority. Good for yes/no questions where one answer could be a fluke.
- **Aggregation**: Combining the results into one.
- **Failure isolation**: If one helper fails, the others still count. The answer says which area was not covered (`complete: false`).
- **Rate limit**: The most calls per minute that the model service allows. Parallel calls reach it faster.
- **Deterministic**: Same input, same output, always. We decide the final verdict in plain code (worst reviewer wins), not with AI, so it never changes by mood.

### Why we learn this

Model calls are slow because they wait for the network and the model. When the jobs do not depend on each other, waiting for all of them together takes only as long as the slowest one. Also, a reviewer with one narrow focus checks more deeply than one prompt that is asked to check five things. And voting gives extra confidence on risky yes/no decisions.

### What we gain

- Speed: the time is about the slowest helper, not the sum.
- Depth: each reviewer has one focus.
- Confidence: voting shows how much the answers agree.
- Resilience: one failure does not lose everything.
- A clean split: AI gives opinions, plain code makes the decision.

### Watch out (architect notes)

- **Parallel saves time, not money.** Five calls cost five calls.
- **Rate limits.** Many calls hit at once. If you see rate-limit errors, lower `MAX_WORKERS`.
- **Only parallelize independent work.** If B needs A's result, that is a chain (Project 3).
- **Never hide a failure.** If one reviewer failed, the summary must not claim that area was checked.
- **Voting needs independent tries.** If the model holds the same wrong belief, five votes only repeat it.
- **Keep results in input order** so each result belongs to the right helper.
- **The summary step can invent things.** Tell it to use only what the reviewers wrote.
- **More threads need more memory.** We gave this service a bigger container (512 CPU units, 1 GB).
- **Prove it really runs in parallel.** Our test uses a barrier that opens only when all five are running together.

### Do not use it when

The steps depend on each other, or you cannot afford the extra calls.

---
## Compare all five — One table, and how to choose

| Project | Who decides the steps | Model calls per request | Best for | Main risk |
|---|---|---|---|---|
| 1 Tools | The model | 1 to 5 (loop) | Needing outside facts or actions | Runaway loops, unsafe tools |
| 2 RAG | The model decides when to search | 1 to 5, plus one embedding call per search | Questions about your own documents | Stale or leaked documents |
| 3 Chaining | Your code | 2 or 3, in a row | Quality of one piece of writing | About 3x cost and time, errors pass along |
| 4 Routing | Your code | 2 (one small, one big), or 1 for a human | Mixed kinds of requests | Wrong route |
| 5 Parallel | Your code | N at once, plus 1 | Independent checks, extra confidence | N times the cost, rate limits |

### Which one do I need?

```
 Need facts from outside or an action?       --> TOOLS     (1)
 Is the answer inside YOUR documents?        --> RAG       (2)
 Does one output need several passes?        --> CHAINING  (3)
 Are the requests of different kinds?        --> ROUTING   (4)
 Are the parts independent?                  --> PARALLEL  (5)
 None of these?                              --> one good prompt.
                                                 Start simple.
```

These patterns can be combined. A router can send a ticket to a RAG agent, and a chain step can itself run in parallel. We will do that in later projects.

---
## Rules that apply to every project — The architect's checklist

- **Secrets live in Secrets Manager**, as plain strings, with the smallest permission that works.
- **Every service has `/health`** so the load balancer can tell if it is alive.
- **Limit input size** so nobody can send a giant request and run up the bill.
- **Put limits on loops and time.** Maximum rounds, timeouts, a maximum number of workers.
- **Outside text is data, not orders.** User messages, documents, tickets and designs go inside tags and the model is told so.
- **Test the code with a fake model.** It is free and fast. It does not prove the AI answers are good. That needs real samples.
- **Everything is code.** Docker and Terraform make the setup repeatable. Run `terraform destroy` when you finish so AWS stops charging.
- **Model names are settings** (environment variables), so changing a model needs no code change.

### Not done yet (honest list)

- No login. Anyone with the web address can call projects 2 to 5.
- HTTP only, no HTTPS. HTTPS needs a domain name and a certificate.
- No per-user limits, no cost alarms, no monitoring dashboards.
- No quality evaluation with the real model yet. Our tests use a fake one.
- Nothing has been run against the live API or on AWS by me. You will do the first real run.

Project 10 (the capstone) covers monitoring, guardrails, human approval and automated deployment.

---

# Part B: Projects 6 to 10

*Same format as Part A: the one-line idea, a story, pictures, new words, why we learn it, what we gain, and what to watch out for.*

## Project 6: Orchestrator-workers — A boss plans, helpers do the parts

> *The plan is not written in advance. The lead writes it after reading the job.*

### The story

Imagine a school project: "Write a report on our town." A good team leader does not know the parts in advance. She reads the topic first, then decides: "You do history, you do food, you do maps." Helpers work at the same time. At the end she glues the pieces into one report.

That is the orchestrator-workers pattern. In Project 5 (parallel) *you* decided the parts in code. Here the *model* decides how many parts there are and what they are.

### The picture

```
 GOAL: "Plan a launch for our new savings account"
        |
        v
 +----------------+   makes a list of tasks
 |  ORCHESTRATOR  | ---------------------------+
 |  (the planner) |                            |
 +----------------+                            v
        ^                        +-------------+-------------+
        |                        |             |             |
        |                   +--------+    +--------+    +--------+
        |                   | WORKER |    | WORKER |    | WORKER |
        |                   | task 1 |    | task 2 |    | task 3 |
        |                   +--------+    +--------+    +--------+
        |                        |             |             |
        |                        +------+------+-------------+
        |                               |
        |                        all results come back
        |                               |
        +--- SYNTHESIZER <--------------+
             (glues the pieces, and lists "Gaps" it could not cover)
                    |
                    v
              ONE final answer
```

```
 THE PLAN IS UNTRUSTED (it is model output!)

 model's plan text --> parse it --> too many tasks? --> keep first 8 only
                          |
                          +--> cannot read it at all? --> fall back to ONE task
                                                          (the whole goal)
 Workers run at the same time, but never more than 5 at once.
```

### New words

- **Orchestrator**: The model that reads the goal and writes the list of tasks.
- **Worker**: A model call that does exactly one task from the list. It knows nothing about the other tasks.
- **Synthesizer**: The last step. It reads all worker results and writes the final answer. It must list "Gaps" (things nobody covered).
- **Fan-out / fan-in**: Fan-out means one job splits into many. Fan-in means many results join into one.
- **Thread pool (`MAX_WORKERS`)**: A fixed number of helper threads. Extra tasks wait in line, so we never start 100 calls at once.
- **Fallback**: A safe plan B. If the plan cannot be read, do the whole goal as one task.

### Why we learn this

Some jobs cannot be split by a human in advance. "Review this codebase" needs 3 parts for a small repo and 30 for a big one. Only something that reads the job can choose the parts. This is the pattern Anthropic uses in its research system: a lead agent plans and sub-agents search in parallel.

### What we gain

- A way to handle jobs whose shape is unknown until run time.
- Speed: workers run side by side, so 5 tasks take about as long as 1.
- Cleaner results: each worker has a small, focused job.
- A safe way to treat model output (a plan) as input to our own code.

### Watch out (architect notes)

- **The plan is untrusted input.** The model might return 500 tasks or nonsense. We parse it, cap it at 8 tasks, and fall back to one task.
- **Cost multiplies.** One goal becomes 1 plan call + N worker calls + 1 synthesis call. Cap N, and use a cheaper `WORKER_MODEL` for workers.
- **Workers cannot see each other.** If task 2 needs task 1's result, this is the wrong pattern. Use chaining (Project 3).
- **One bad worker must not sink the job.** Report what failed in "Gaps" instead of crashing.
- **Load balancer timeouts.** One request now runs several model calls, so the load balancer's idle timeout was raised to 120 seconds.

### Do not use it when

You already know the parts. Then use parallelization (Project 5), which is simpler and cheaper.

---

## Project 7: MCP — One standard plug for tools

> *Write the tool once, use it from any agent.*

### The story

Think about phone chargers. Years ago every phone had a different plug. Today most use USB-C, so one charger fits many phones. MCP (Model Context Protocol) is USB-C for AI tools. A tool server speaks MCP. Any agent that understands MCP can plug in and ask, "What can you do?"

In Project 1 the tools lived inside the agent's code. Here the tools live in a separate program (a server). The agent discovers them at start-up.

### The picture

```
 BEFORE (Project 1)                 AFTER (Project 7)

 +---------------------+            +---------+   MCP    +--------------+
 | AGENT               |            |  AGENT  | <------> |  MCP SERVER  |
 |  + calculator code  |            | (client)|  stdio   |  calculate_emi
 |  + weather code     |            +---------+          |  get_account_summary
 +---------------------+                                 |  list_transactions
 tools are glued in                                      |  resource: fees
                                                         +--------------+
                                                         any other agent can
                                                         plug in the same way
```

```
 WHAT HAPPENS AT START-UP

 agent starts the server as a child program (talks over stdin/stdout)
   |
   v
 agent asks:  "list your tools"
   |
   v
 server replies with names + descriptions + input shapes
   |
   v
 agent converts them to Claude's tool format  (to_anthropic_tool)
   |
   v
 agent keeps ONLY the tools on its allowlist  (ALLOWED_TOOLS)
```

### New words

- **MCP**: A standard way for an AI app to talk to tools and data.
- **MCP server**: The program that offers tools. We built one with FastMCP.
- **MCP client**: The part inside the agent that connects to the server.
- **Tool vs resource**: A tool *does* something (calculate). A resource is something to *read* (the fee policy page).
- **stdio transport**: The server runs as a child program and they talk through its input and output pipes. Simple and local.
- **Allowlist**: The list of tool names the agent is allowed to use. Anything else is ignored.
- **`isError`**: A flag on a tool result that says "this failed", so the model can react.

### Why we learn this

In a real company, ten teams build ten agents. Without a standard, each team rewrites the same "get account summary" glue. With MCP, the banking team writes one server and every agent uses it. The tool owner can improve it without touching any agent.

### What we gain

- Reusable tools: write once, plug into many agents.
- A clean split: the tool team owns the server, the agent team owns the brain.
- Discovery: the agent asks what exists instead of hard-coding it.
- The skill to read and build against an open standard, which is where the industry is moving.

### Watch out (architect notes)

- **A server can offer more than you want.** The allowlist makes the agent use only the tools you approved.
- **Do not leak secrets to the child program.** The server starts with a minimal environment, so it never sees the API key.
- **Tool results are untrusted text.** We cut them at 4000 characters so one huge result cannot flood the model.
- **Loop limits still apply.** The agent stops after 6 turns.
- **Version pinning.** `mcp==1.12.4` is pinned because newer major versions rename things.
- **stdio means local only.** A remote server over HTTP needs login and network care. That is a later topic.

### Do not use it when

You have one agent and two tiny tools. Plain functions (Project 1) are simpler.

---

## Project 8: Evaluator-optimizer — One writes, one checks, repeat

> *Good writers have editors. So do good agents.*

### The story

You write an essay. Your teacher marks it: "Too long. Missing the date." You fix it and hand it in again. This repeats until the teacher says "good". The teacher is the evaluator. You are the optimizer (the generator).

The second model is not magic. It just looks at the work with fresh eyes and a checklist.

### The picture

```
 task + rules
     |
     v
 +-----------+   draft    +------------+
 |  WRITER   | ---------> |  REVIEWER  |
 | (model)   |            |  (model)   |
 +-----------+ <--------- +------------+
     ^         feedback        |
     |                         +--> PASS --> done
     +---- try again <---------+
           (but not forever!)
```

```
 ONE ROUND, step by step

 draft --> CODE CHECK first (word limit)  --> too long? --> feedback, no model needed
                |
                v ok
          MODEL REVIEW --> PASS / NEEDS_IMPROVEMENT + feedback

 STOP when:   passed          the reviewer is happy
              max_rounds      we ran out of tries
              stalled         the new draft is the same as the last one
```

### New words

- **Generator**: The model call that writes or rewrites.
- **Evaluator**: The model call that judges against the rules.
- **Feedback loop**: Judge, fix, judge again.
- **Hard check**: A rule checked by plain code (like word count). It never gets tired or fooled.
- **`max_rounds`**: A hard limit on tries. The cookbook version has none, and we added one.
- **Stalled**: A stop reason. If the writer keeps giving the same text, more rounds only waste money.
- **`EVAL_MODEL`**: A setting that lets the reviewer be a different model from the writer.

### Why we learn this

One model call gives a decent first draft, not a reliable one. Many business texts must follow rules: length, tone, required facts. A check-and-fix loop turns "usually good" into "checked against the rules".

### What we gain

- Better quality without a human reading every draft.
- A pattern for any task with clear rules: emails, summaries, SQL, code.
- A visible record (`history`) of every round, so you can see why an answer changed.
- Habits for trusting model judgments carefully.

### Watch out (architect notes)

- **Always set a stop.** Without `max_rounds`, a picky reviewer and a stubborn writer can loop and spend money forever.
- **Use code for rules that code can check.** Word count in Python is exact. A model counting words is not.
- **An unreadable verdict is never a PASS.** If the reviewer's reply cannot be parsed, we treat it as "not passed".
- **A model grading itself is biased.** Use a different `EVAL_MODEL` when you can.
- **Cost.** Each round is up to 2 model calls, so 5 rounds is up to 10. We report `llm_calls` so you can see it.
- **The load balancer timeout** was raised to 300 seconds, because rounds run one after another.

### Do not use it when

There are no clear rules for "good". The reviewer will just guess, and you pay twice for a guess.

---

## Project 9: Memory — Agents that remember

> *A new chat should not start from zero.*

### The story

A good shopkeeper remembers you: "You like the blue notebook, and your birthday is in June." A shop with a new keeper every day forgets you every day. Models are like that new keeper: each conversation starts empty unless we give them notes.

We solve it with a notebook. The agent writes important facts to files and reads them next time.

### The picture

```
 SHORT-TERM (this chat)            LONG-TERM (files, kept forever)
 +----------------------+          +---------------------------+
 | the messages so far  |          | /memories/<user>/         |
 | (session history)    |          |    profile.md             |
 +----------------------+          |    preferences.md ...     |
 gone when the chat ends           +---------------------------+
                                   still there tomorrow
```

```
 THREE AGENTS, THREE JOBS

 user message
     |
     v
 +--------+  reads memory  +----------+
 |  LEAD  | <------------- | PLANNER  |   read-only: may look, may not write
 | answers|                +----------+
 +--------+
     |  answer goes back to the user right away
     |
     +--(in the background, after the answer)--> +-----------+
                                                 | ARCHIVIST |  the ONLY one
                                                 | writes    |  allowed to
                                                 | notes     |  write memory
                                                 +-----------+
```

```
 MEMORY COMMANDS (like a tiny file system, from the official SDK idea)
 view   create   str_replace   insert   delete   rename
 all inside /memories, one folder per user
```

### New words

- **Short-term memory**: The messages of the current chat.
- **Long-term memory**: Facts saved in files that survive restarts.
- **Memory tool**: A set of six commands the model uses to read and edit its notes.
- **Archivist**: The only agent allowed to write memory. It decides what is worth saving.
- **Snapshot injection**: Our code (not the model) pastes the saved notes into the lead's prompt inside `<memory>` tags.
- **Memory poisoning**: A trick where bad text gets saved as a "fact" and later steers the agent.
- **EFS**: An AWS shared disk. Containers can be replaced but the files stay.

### Why we learn this

Without memory, every conversation repeats "who are you, what do you like". With memory, the agent gets better the longer it works with someone. This is also how long tasks survive: notes carry over when the context window fills up.

### What we gain

- Personal, continuous agents.
- The idea of separating *who may read* from *who may write*.
- Safe file handling: path checks, size limits, per-user folders.
- A deployment with a real disk (EFS) so data survives restarts.

### Watch out (architect notes)

- **Memory is an attack surface.** Whatever gets saved comes back into prompts later. Only the archivist writes, tag-closing text is neutralised, and sensitive text is refused.
- **Path safety.** The model must never escape its folder (`../../other-user`). Every path is checked.
- **Limits.** Maximum file size and file count stop a runaway agent from filling the disk.
- **One user, one lock.** Two requests for the same user must not corrupt the same file at once.
- **Privacy.** Decide what must never be stored (cards, passwords). Give users a way to see and delete their memory (`GET` and `DELETE /memory/{user_id}`).
- **Honest limits.** There is no login here, and files on one disk mean a single instance.

### Do not use it when

Chats are one-off and carry nothing useful forward. Memory adds risk and cost for no gain.

---

## Project 10: Capstone — The production platform

> *The agent is 10% of the system. The other 90% is what keeps it safe.*

### The story

A race car is exciting, but to drive it on a real road you need brakes, seat belts, lights, a number plate and a service record. Projects 1 to 9 built the engine. Project 10 adds everything that lets other people use it safely: login, limits, guards, a human who approves big actions, logs, alarms, and an automatic way to ship new versions.

### The picture

```
 request --> LOGIN (API key + role) --> RATE LIMIT --> INPUT GUARD
                                                          |
             redact cards/keys, block attack text <-------+
                                                          |
                                                          v
                                                   +-------------+
                                                   |    AGENT    |
                                                   +-------------+
                                                     |         |
                                          READ tools |         | WRITE tools
                                     (summary, history,        (freeze_card,
                                      EMI calculator)           raise_refund)
                                                     |         |
                                                     |         v
                                                     |   +-------------+
                                                     |   |  APPROVAL   |  waits for a
                                                     |   |  (paused)   |  human approver
                                                     |   +-------------+
                                                     v         |
                                                OUTPUT GUARD <-+
                                      (no card numbers, no other person's account)
                                                     |
                                                     v
                                                   answer
```

```
 WHO CAN DO WHAT
 customer   chat about their own accounts
 approver   say yes/no to freeze_card and raise_refund
 ops        read the audit log, see metrics
```

```
 SHIPPING A NEW VERSION (GitHub Actions)

 push code --> lint + 67 tests --> build image --> push to ECR (unique tag)
                                                        |
                                    a human clicks "approve" for production
                                                        |
                                                        v
                         ECS rolling update --> health check fails? --> AUTO ROLLBACK
                                                        |
                                                        v ok
                                                   smoke test
```

```
 WATCHING IT
 JSON logs (no message text) --> CloudWatch --> metric filters --> ALARMS --> SNS email
 /metrics (Prometheus)        --> request counts, latency, tool calls, blocked requests
```

### New words

- **Guardrail**: A rule in code that blocks or cleans something dangerous, whatever the model says.
- **Redaction**: Replacing sensitive text (like a card number) with a placeholder before it goes further.
- **Prompt injection**: Text that tries to give the model new orders ("ignore your rules").
- **Authorization vs authentication**: Authentication is "who are you?" (API key). Authorization is "what may you do?" (role and ownership).
- **Human-in-the-loop**: The agent pauses and a person approves risky actions.
- **Audit log**: A permanent record of who did what and when.
- **Observability**: Logs, metrics and traces that let you see inside a running system.
- **Evals**: Tests that use the real model to check answer quality.
- **CI/CD**: Automatic test (CI) and automatic delivery (CD).
- **OIDC**: A way for GitHub to get short-lived AWS access without storing AWS passwords.
- **Circuit breaker (rollback)**: If the new version is unhealthy, ECS goes back to the old one by itself.

### Why we learn this

Companies do not fail because the agent cannot answer. They fail because it leaked data, did a wrong refund, ran up a huge bill, or broke at night and nobody knew. For a bank, controls are the product. This is the part an AI architect gets judged on.

### What we gain

- A reference design for safe, observable, deployable agents.
- The rule *authorization lives in code, never in the prompt*. The model never supplies an account id, and every id is checked against the logged-in user.
- A habit: write actions need approval and are checked again at execution time.
- A full path from commit to production, with a rollback.
- A map to move from ECS to EKS (Kubernetes manifests are included).

### Watch out (architect notes)

- **Do not trust the model for security.** Prompts can be bypassed. Put limits and checks in code.
- **Approvals must be atomic.** Moving from pending to decided must happen once, or two approvers could both trigger a refund.
- **Cost controls.** Rate limit, daily token budget, turn limit, model timeout.
- **Logs must not become a leak.** Log request ids and counts, never message text.
- **Metric labels.** Use route templates (`/v1/approvals/{id}`) and not real ids, or metrics explode in size.
- **When the model is down.** Return a fixed, safe fallback message instead of an error page.
- **Honest limits.** SQLite means one instance. A real multi-instance system needs Postgres and Redis. Evals and the cloud steps were not run against live services by me.

### Do not use it when

It is a weekend prototype for yourself. Take the pieces you need (login, limits, logs) and skip the rest.

---

## Compare all ten — One table

| # | Project | Who decides the steps? | Main new idea | Biggest risk |
|---|---|---|---|---|
| 1 | Tools | The model, step by step | Model asks, code acts | Running untrusted requests |
| 2 | RAG | The model + a search tool | Look up your documents first | Wrong or missing chunks |
| 3 | Chaining | You (fixed order) | Small steps with a gate | Errors passing down the chain |
| 4 | Routing | The model picks a lane | Send work to the right expert | Wrong route |
| 5 | Parallel | You (fixed split) | Many helpers at once | Cost and cap |
| 6 | Orchestrator-workers | The model plans the split | Plan at run time | Untrusted plan, cost |
| 7 | MCP | The model, with discovered tools | A standard plug for tools | Too many tools exposed |
| 8 | Evaluator-optimizer | A loop with a judge | Check and fix until good | Endless loop |
| 9 | Memory | Three agents with roles | Remember across chats | Memory poisoning |
| 10 | Capstone | All of the above, behind controls | Make it safe to run | Gaps between the controls |

### How to choose

```
 Is the job always the same steps?  --yes--> CHAINING (3) or plain code
        | no
 Does it need outside data or actions? --> TOOLS (1), RAG (2), MCP (7)
        | no / also
 Are the parts known in advance?  --yes--> PARALLEL (5)
        | no
 Parts depend on the job?         --yes--> ORCHESTRATOR-WORKERS (6)
 Different kinds of request?      --yes--> ROUTING (4)
 Output must meet rules?          --yes--> EVALUATOR-OPTIMIZER (8)
 Must remember the user?          --yes--> MEMORY (9)
 Real users, real money?          --yes--> CAPSTONE controls (10)
```

### Rules that also apply to Projects 6 to 10

- **Treat every model output as untrusted** (plans, tool arguments, verdicts, memory text).
- **Put code in charge of rules** that code can check (word counts, ownership, limits).
- **Every loop needs a stop** (max tasks, max turns, max rounds, stalled).
- **Test with a fake model first.** Run evals with the real model separately.
- **Keep secrets out of children and logs.** The MCP child gets no API key, and logs have no message text.

---
Based on Anthropic's "Building Effective Agents" guide and the `patterns/agents` examples in the claude-cookbooks repository. Pictures are simplified on purpose.
