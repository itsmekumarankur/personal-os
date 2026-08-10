# /design-lab — System Design Practice

Structured system design practice. Get a problem, work it out loud, get structured feedback. Maps to how interviews and real design reviews actually work.

## Modes

- `/design-lab` — Get a random problem at current skill level
- `/design-lab <topic>` — Get a problem in a specific area (e.g., `/design-lab kafka`, `/design-lab database`)
- `/design-lab review <description>` — Review a design the user already wrote
- `/design-lab debrief` — Debrief after a practice session: what went well, what to study next

## Step 1: Read State

1. Read `vault/learning/system-design/index.md` — what topics have been studied
2. Read the Practice Log in that file — recent sessions, skill areas
3. Read `vault/me/goals.md` — current learning priorities

## Step 2: Problem Selection

### If random:
Choose a problem that:
- Matches topics already studied (build on existing knowledge)
- Stretches into adjacent territory (don't repeat the same problem twice)
- Scales in complexity: warm-up → intermediate → hard based on practice history

**Problem categories to rotate through:**
- Data-intensive systems (message queues, event streaming, pipelines)
- Storage systems (databases, caches, file storage)
- Compute systems (job schedulers, distributed compute)
- Communication systems (APIs, CDNs, load balancers)
- Platform systems (auth, tracing, monitoring)
- Product systems (social feed, notifications, search)

### If topic-specific:
Find a problem that exercises that topic meaningfully.

## Step 3: Present the Problem

Format:
```
System Design: [Problem Name]

Context:
[2-3 sentences of real context — not just "design Twitter". Give scope, users, constraints.]

Requirements:
Functional:
- [3-5 functional requirements]
Non-functional:
- [Scale: X requests/sec, Y users]
- [Latency: P99 < Z ms]
- [Availability: N nines]
- [Other constraints]

Out of scope:
- [Be explicit about what NOT to design]

You have 35 minutes. Think out loud. I'll prompt you if you get stuck.
```

Wait. Let the user start talking or typing.

## Step 4: Facilitate the Session

Don't solve it for them. Be a good rubber duck:
- If they skip requirements: "What does the scale look like? How many concurrent users?"
- If they jump to implementation: "What are the core data entities first?"
- If they miss a constraint: Ask about it as a question, not a correction
- If they're stuck: Give a hint, not the answer ("Have you thought about how you'd handle...")
- If they handwave something: "Walk me through how that actually works"

Prompts to have ready:
- "What happens when [failure scenario]?"
- "How does [component] scale as load grows 10x?"
- "Where are the bottlenecks?"
- "What are the tradeoffs with this approach?"

## Step 5: Debrief

After they finish (or after ~35 minutes):

**Strengths:**
- What they did well (be specific, not generic)

**Gaps:**
- What was missed or underspecified (concrete)
- What tradeoffs weren't considered

**What to Study Next:**
- 1-2 specific concepts to go deeper on from this session
- Link to existing vault pages or suggest new ones to create

**Score (optional, if asked):** Rate the design on: Requirements Gathering, High-Level Design, Deep Dive, Tradeoffs. 1-5 scale with specific reasoning.

## Step 6: Vault Update

After session:
1. Add entry to Practice Log in `vault/learning/system-design/index.md`:
   ```
   | [Date] | [Problem] | [Approach] | [Key Insight] |
   ```
2. Create or update concept pages for anything encountered during debrief
3. Append to `vault/log.md`
4. Save full debrief to `outputs/design-reviews/YYYY-MM-DD-{problem}.md`
