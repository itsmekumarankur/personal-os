# /learn — Deep-Process a Course Module or Article

Takes a specific piece of learning content and does a full deep-process into the vault. Deeper than `/ingest` — this is for content you want to really absorb, not just archive.

## When to Use

- Just finished a Udemy module or section
- Read an important article or paper
- Watched a talk or listened to a podcast
- Went through a technical doc or RFC
- Worked through a chapter of a book

## Step 1: Get the Source

If the user doesn't specify: "What did you just study? Drop it in inbox/ or paste the key points."

Wait for input. Accept:
- File path (`projects/architect-kit/AI/deploy_ai/day1-instant-gratification-notes.html`)
- Dropped file in `inbox/`
- Direct text paste in chat
- URL (fetch with WebFetch)

## Step 2: Read and Understand

Read the source fully. Then:

1. **Identify the domain** — AI/LLMs, system design, leadership, etc.
2. **Extract key concepts** — What are the 3-7 most important ideas here?
3. **Identify people mentioned** — Authors, researchers, teachers, figures cited
4. **Find connections** — What does this connect to in the existing vault? Read `vault/index.md` first to check.
5. **Note what's new vs. what reinforces** — New concept or extension of something already known?

## Step 3: Interactive Deep-Process

Tell the user in soul.md voice:
- What this source covers (2-3 sentences)
- The 3-5 key concepts you extracted
- How it connects to existing vault pages

Then ask: "What do you want to make sure sticks? Anything to emphasize or drill into?"

Wait. Incorporate their response.

## Step 4: Build Wiki Pages

For each key concept:

1. **Create or update** `vault/learning/{domain}/{concept}.md`
   - Explain the concept in plain language
   - Note the key insight or "aha" from this source
   - Add examples if the source had them
   - Add `[[wiki links]]` to related concepts
   - YAML frontmatter with `tags`, `date_created`, `date_updated`, `sources`

2. **Update the domain index** (`vault/learning/{domain}/index.md`)
   - Add the new concept page to the index
   - Add a one-line summary

3. **Update course tracker** if this was a course module
   - Update `vault/courses/tracker.md` with progress
   - Note what section was completed

4. **Create people pages** for any notable author or teacher encountered

## Step 5: Synthesis Question

After building the pages, ask one synthesis question to push understanding:

"Based on what you just learned about [concept], how would you explain [related scenario] differently now?"

Wait for the answer. File a brief note in `vault/me/journal/{today}.md` if the answer is insightful.

## Step 6: Vault Update

- Archive source to `vault/sources/` (if not already there)
- Append to `vault/log.md`
- Update `vault/index.md` for new pages

## Output to User

In soul.md voice:
- Summary of what was added to the vault
- Key concepts now in the wiki (with links)
- One question to mull over or revisit tomorrow
