# /reflect — Evening Journaling and Knowledge Consolidation

An evening command. Structured reflection on the day's learning, experiences, and practices. Consolidates insights into the vault.

## How the Journal Works

The daily journal lives at `projects/leadership-kit/daily-journal/entries/2026/{month}/{date}.md`. It uses a specific template with frontmatter for tracking sadhana, mood, energy, focus, and self-rating.

The `/reflect` command is the AI companion to that journal. It doesn't replace it — it deepens it.

## When This Runs

On-demand, any evening. Can be scheduled via `/cron-setup`.

## Step 1: Check What Happened Today

Read:
- Today's journal entry from `projects/leadership-kit/daily-journal/entries/2026/{month}/YYYY-MM-DD.md` if it exists
- `vault/log.md` for today's activity
- `vault/courses/tracker.md` to see what was being studied

## Step 2: Open the Conversation

Ask naturally (in soul.md voice):

"How was today? What happened with sadhana, learning, and work?"

Wait. Let them talk. This isn't a form-fill.

## Step 3: Listen and Probe

After they respond, ask 1-2 follow-up questions:
- On sadhana: "How did practice feel today?" (only if not mentioned)
- On learning: "What actually clicked — not just what you covered, but what shifted?"
- On leadership/meetings: "Any meeting moments worth reflecting on for the 100-Day Shift?"
- On friction: "What pulled you off track today, and why?"
- On the observation issue noted in journal (recurrent): "Did the rush show up today? What did you notice?"

Read what they shared and pick the right 1-2. Don't interrogate.

## Step 4: Extract and File

From the conversation:

**Vault updates:**
- New concept learned → `vault/learning/{domain}/{concept}.md`
- Spiritual insight → `vault/spirituality/insights/{topic}.md`
- 100-Day Shift observation → add to `vault/projects/leadership-kit/status.md` notes
- Priority shift → update `vault/me/goals.md`
- Course progress → update `vault/courses/tracker.md`

**Journal synthesis:**
If the conversation surfaced something worth keeping — an insight, a pattern, a realization — save it to `vault/me/journal/{YYYY-MM-DD}.md`:

```markdown
---
tags: [journal, reflection]
date: YYYY-MM-DD
---

# Reflection — {Day}, {Date}

## What Happened
[Brief summary of sadhana, learning, work]

## What Actually Clicked
[The real insight — not just what was covered]

## Pattern Noticed
[Recurring themes, things to watch]

## Tomorrow's Anchor
[One thing to hold onto going into tomorrow]
```

Don't show the whole thing back unless asked. Just: "Saved."

## Step 5: Vault Update

- Update `vault/index.md` if new pages created
- Append to `vault/log.md`: `## [YYYY-MM-DD HH:MM] /reflect | journal entry + [N] vault updates`

## Step 6: Close

End with something brief and real (soul.md voice). Not motivational. Not robotic.

Something anchored in what they actually shared. If sadhana happened: acknowledge it. If a hard day: acknowledge that. One sentence.
