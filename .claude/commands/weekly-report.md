# /weekly-report — Friday Learning Synthesis

A Friday command. Synthesize the week's learning: what was absorbed, what concepts connected, what compounded, what's next.

## When This Runs

Fridays (or end of any learning week). Can be scheduled via `/cron-setup`.

## Step 1: Read State

1. `soul.md` — voice
2. `vault/me/goals.md` — current priorities
3. `vault/log.md` — all entries from this week (filter by date)
4. `vault/me/journal/` — journal entries from this week
5. `vault/courses/tracker.md` — course progress this week

## Step 2: Gather the Week's Activity

From log.md and journal entries, collect:
- Which courses/modules were studied
- Which concepts were ingested
- Which design lab sessions happened
- What reflections were written
- Total approximate study time (if trackable from log timestamps)

## Step 3: Build the Weekly Report

Output format (in soul.md voice — real, not corporate):

---

**Week of [Date Range] — Learning Report**

**What Got Studied**
[List courses/topics covered, one line each. Concrete, not vague.]

**What Actually Clicked**
[The 2-3 ideas that genuinely landed this week. Not everything studied — the ones that shifted something.]

**Concept Connections**
[Did anything from this week connect to something from a previous week in an interesting way? The vault makes this visible.]

**What's Still Open**
[Questions that came up but weren't resolved. Threads to pull next week.]

**Vault Growth**
[N new wiki pages, M updated. Domains growing: AI/LLMs, System Design, etc.]

**Course Progress**
[Where each active course stands now.]

**Next Week's Focus**
[Based on goals, open questions, and what would compound: one primary focus area.]

---

## Step 4: Save Report

Save to `outputs/learning-reports/YYYY-MM-DD-weekly.md`.

Append to `vault/log.md`: `## [YYYY-MM-DD HH:MM] /weekly-report | week [N] summary`

## Step 5: Update Vault

- If connections emerged between concepts, add `[[wiki links]]` between those pages
- Update `vault/courses/tracker.md` with week's progress
- If priorities shifted, update `vault/me/goals.md`

## Step 6: Close

Ask: "Anything to adjust about next week's plan?"
Wait. Incorporate if needed. Update `vault/me/goals.md` if priorities shift.

End with something real (soul.md voice). Not a motivational quote. Just: "Good week. See you Monday."
