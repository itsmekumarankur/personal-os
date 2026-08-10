# /setup — First-Run Onboarding

Guide through setting up the Personal OS. One step at a time. Wait for input before proceeding.

## Step 1: Verify Connections

Silently check what's connected. Don't error if something isn't. The OS works without MCP tools.

Test if connected:
- Gmail MCP: list 1 recent email subject
- Google Calendar: check today's events
- Notion: list databases

Report: "I can see your [Gmail/Calendar/Notion]. [Anything not connected] isn't set up — we'll work without it."

## Step 2: Build Your Identity (soul.md)

Tell the user exactly:

```
Let's build your soul.md — the file that defines how I talk, what I prioritize, and how I sound.

Two ways to give me material:
1. Drop files into inbox/ — notes, a bio, writing samples, anything that helps me know how you think. PDF, DOCX, MD, TXT all work.
2. Paste directly into chat.

When you're ready, type 'go'. If you want to skip the inbox and just talk, type 'chat'.
```

**WAIT for 'go' or 'chat'.** Do not continue.

### A. Read inbox (if 'go')

List `inbox/`. Skip dotfiles. For each file:
- Read it (PDF, DOCX, plain text, HTML all work)
- Track filenames in a "what I read" list

If inbox is empty: "Inbox is empty. Drop files now and type 'go' again, or paste your info. I can also check your existing notes in architect-kit/ if you want."

### B. Learn about existing work

After reading any inbox material, also check:
- `vault/me/role.md` and `vault/me/goals.md` (already pre-seeded — verify still accurate)
- `projects/architect-kit/` folder overview (to understand current study areas)
- `projects/antarmukh/` folder (to understand spiritual dimension)

### C. Questions to ask

Ask ONLY what you don't already know. Don't repeat what the vault already has. Always ask:

1. "What's your current professional role or situation? One sentence."
2. "What does a typical week look like for you — how much time on learning vs. work vs. other?"
3. "What kind of personality should I have? Give me a character: 'sharp and direct', 'warm but rigorous', 'like a senior engineer who's read philosophy', whatever fits."
4. "Paste 3-5 things you've actually written — messages, notes, posts, comments. I need your real writing voice."
5. "What are the top 3 things you want from this OS day to day?" (if not clear from what they shared)

Aim for 4-5 questions total. Skip what you already know from inbox or existing vault.

### D. Quality check before writing

Required before writing soul.md:
- At least one of: bio / role / self-description
- A character/personality answer (not one word)
- At least one concrete goal
- Writing samples: 3+ snippets or one long piece

If anything is missing, ask for it directly. Don't write a generic soul.md. It will produce a generic agent.

## Step 3: Write soul.md

OVERWRITE the template. Fill every section with real content from what you collected.

Generate the Agent Personality section:
- Core identity (one sentence that captures who this agent is)
- How you talk (4-5 specific rules, not generic)
- Addressing style (first name? direct? formal?)
- 5 example responses — calibration examples. Model what good responses look like. Write them in the agent's actual voice.
- Anti-patterns (things this voice would never do)

soul.md MUST be fully filled. No `TODO`, no placeholders. Under 2.5KB.

After writing: read it back to the user. Ask "Does this sound right? Anything to fix?" Wait. Fix if needed.

## Step 4: Seed the Vault from Existing Notes

Run a targeted ingest on existing work that hasn't been processed yet:

1. Check `vault/index.md` to see what's already there.
2. Ask: "Want me to ingest your architect-kit/ notes and antarmukh/ project into the vault now? It'll create wiki pages for every major concept and cross-link them."
3. If yes: run `/ingest --batch` against the relevant folders.

This is optional but high-value. The more that gets ingested, the more the vault compounds.

## Step 5: Set Up Obsidian

"Open Obsidian. Open folder as vault. Navigate to the `vault/` folder inside personal-os_byMe/. You'll see your pages and the graph. Each `[[wiki link]]` becomes an edge in the graph."

## Step 6: Done

Summary:
- Connections: [list what's connected]
- soul.md: filled with [personality description]
- Vault: [N pages], seeded from [sources used]
- Obsidian: ready to open

Then:

```
Your Personal OS is ready.

Start with:
  /study-brief      — Morning learning brief
  /learn            — Process a course or article
  /reflect          — Evening journal and consolidation
  /weekly-report    — Friday synthesis

Other tools:
  /course-tracker   — View all course progress
  /design-lab       — System design practice
  /career-radar     — Track your skills and growth
  /ingest           — Drop anything in inbox/ to process it
  /lint             — Check vault health

Welcome aboard.
```
