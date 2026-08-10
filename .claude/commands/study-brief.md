# /study-brief — Morning Learning Brief

A morning command. What did I do/learn yesterday, what's the plan for today, what should I review.

## When This Runs

On-demand every morning. Can be scheduled via `/cron-setup` (suggested: weekdays 7:30 AM).

## Step 1: Read State

1. `soul.md` — voice and priorities
2. `vault/me/goals.md` — current priorities (100-Day Shift, AI mastery, system design, etc.)
3. `vault/courses/tracker.md` — active courses and last-touched date
4. `vault/log.md` — last 5 entries
5. Most recent journal entry from `projects/leadership-kit/daily-journal/entries/2026/`
6. `vault/projects/leadership-kit/status.md` — 100-Day Shift progress

## Step 2: Build the Brief

Output format (in soul.md voice, tight):

---

**Morning Brief — [Day], [Date]**

**Yesterday**
What was studied/done. Pull from log + most recent journal. 2-3 sentences. Include sadhana if journal mentions it.

**Today's Focus**
Primary study/work priority for the day. One thing. Based on active goals and course tracker.

**100-Day Shift — Today's Micro-Habit**
The daily 10-minute diagramming practice. Suggest one specific problem from current work or learning to diagram today. (e.g., "Draw the MF order lifecycle as a sequence diagram" or "Diagram the Kafka consumer group rebalancing flow")

**Review Queue**
1-2 concepts from 7-14 days ago that deserve a second pass. Spaced repetition, manual form.

**Open Question**
One unresolved question from recent learning. Something to hold in mind during the day.

---

## Step 3: Vault Update

Append to `vault/log.md`: `## [YYYY-MM-DD HH:MM] /study-brief | generated`

## Output

Display in chat. Optionally save to `outputs/study-briefs/YYYY-MM-DD.md` if requested.
