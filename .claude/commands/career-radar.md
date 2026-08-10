# /career-radar — Track Skills, Growth, and Opportunities

A periodic command (run weekly or monthly) to audit where you are, where you're going, and what the market looks like.

## Modes

- `/career-radar` — Full career audit
- `/career-radar skills` — Just the skill inventory update
- `/career-radar opportunities` — Research current market signals

## Full Audit (/career-radar)

### Step 1: Read State

1. `vault/me/role.md` — who I am right now
2. `vault/me/goals.md` — what I'm moving toward
3. `vault/learning/career/index.md` — skill inventory
4. `vault/courses/tracker.md` — what's been studied
5. `vault/log.md` — what's been learned in the last 30 days

### Step 2: Skill Inventory

Compare what's in `vault/learning/career/index.md` with what's been ingested and studied.

Update the skill inventory table:

| Skill | Estimated Level | Evidence | Building? |
|-------|----------------|---------|-----------|
| LLM Engineering | — | [vault pages, courses] | Yes |
| System Design | — | [vault pages, lab sessions] | Yes |
| AI Guardrails | — | [course notes] | Yes |
| Engineering Leadership | — | — | Yes |
| ... | | | |

Levels: Awareness → Beginner → Intermediate → Advanced → Expert

### Step 3: Gap Analysis

Based on goals and current state:
- What skills are most underdeveloped relative to goals?
- What's the next skill to push?
- What courses or projects would move the needle?

### Step 4: Market Signals (if web search is available)

Search for:
- Current demand for skills in the inventory
- Trends in AI engineering, system design, engineering management roles
- What senior/staff engineers and AI leads are expected to know in 2026

Summarize: 3-5 signals. What's in demand, what's declining, what's emerging.

### Step 5: Recommendations

3 concrete recommendations:
1. **Study next** — Most impactful skill to invest in
2. **Build next** — A project that demonstrates a key skill
3. **Position** — How to think about your positioning over the next 6-12 months

### Step 6: Vault Update

- Update `vault/learning/career/index.md` with the new skill inventory
- Update `vault/me/goals.md` if the analysis shifts priorities
- Save full audit to `outputs/learning-reports/YYYY-MM-DD-career-radar.md`
- Append to `vault/log.md`
