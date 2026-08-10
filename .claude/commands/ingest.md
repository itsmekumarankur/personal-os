# /ingest — Process Raw Sources Into the Wiki

Takes files from `inbox/`, reads them, and weaves them into the vault. Knowledge compounds.

## Modes

- `/ingest` — Interactive (default). One file at a time. Discuss takeaways, ask what to emphasize, show wiki updates as they happen.
- `/ingest --batch` — Process all unprocessed files in one pass, no discussion. Use for bulk dumps.
- `/ingest <path>` — Force-ingest a specific file or folder (skips manifest check).

## Step 1: Read State

1. Read `vault/index.md` — the catalog. Know what pages already exist before deciding to create or update.
2. Read `vault/log.md` — last 20 entries to understand recent activity.
3. Read `inbox/_ingested.md` (the manifest). If it doesn't exist, create it:
   ```
   # Inbox Ingest Manifest
   Append-only. Format: file | sha256-short | date | pages_touched
   | File | Hash | Ingested | Pages Touched |
   |------|------|----------|---------------|
   ```

## Step 2: Find Unprocessed Files

List `inbox/`. Skip dotfiles (`.gitkeep`, `.DS_Store`) and `_ingested.md`. For each:

1. Compute sha256 short hash: `shasum -a 256 "{path}" | cut -c1-8`
2. Check if `{filename}|{hash}` is in `_ingested.md`
3. Match found → skip
4. Filename matches but hash differs → re-ingest (file updated)
5. Neither matches → new file, ingest

If list is empty: "Nothing new in inbox/." Exit.

## Step 3: Process Each File

### A. Read the Source

- `.pdf` → Read tool (Claude reads PDFs natively)
- `.docx` → Read or Bash (`docx2txt`)
- `.md`, `.txt`, `.html` → Read directly
- `.png`, `.jpg` → View with vision
- `.mp3`, `.m4a` → Transcribe with whisper, then ingest transcript

### B. Summarize and Discuss (interactive mode only)

Tell the user (in soul.md voice):
- 2-3 sentence summary of what the source contains
- Key concepts encountered (domains: AI, system design, leadership, etc.)
- Key people mentioned (authors, teachers, thinkers)
- Any contradictions with existing wiki content

Ask: "Want me to file this with default emphasis, or focus on anything specific?" Wait. If "default", proceed.

In `--batch` mode, skip this step.

### C. Update the Wiki

A single source typically touches 5-15 pages. For every entity:

**Concepts encountered:**
→ Create or update `vault/learning/{domain}/{concept}.md`
→ One page per concept. Real prose, not stub. Add `[[wiki links]]` to related concepts.
→ Note which domain: AI/LLMs, system-design, leadership, etc.

**People mentioned (authors, teachers, thinkers):**
→ Create or update `vault/people/{name}.md`
→ Include: who they are, what they're known for, what this source says about them

**Courses referenced:**
→ Update `vault/courses/tracker.md` with progress or new course found

**Project-relevant content:**
→ Update `vault/projects/{name}/status.md` if the source relates to an active project

**Spiritual content:**
→ Create or update `vault/spirituality/insights/{topic}.md`

Every page MUST have:
- YAML frontmatter: `tags`, `date_created`, `date_updated`, `sources`
- At least one `[[wiki link]]` to another page
- Real prose body, not stubs

### D. Flag Contradictions

If new info contradicts existing content, add a `## Contradictions` section:
```markdown
## Contradictions
- 2026-08-08: source `article.md` says X; this page previously said Y (from `source.pdf`, 2026-07-01). Newer source wins — flagged for review.
```
Tell the user about contradictions.

### E. Archive the Source

Move from `inbox/` to `vault/sources/`:
- `.pdf`, `.docx` → `vault/sources/documents/`
- `.md`, `.txt`, `.html` → `vault/sources/notes/`
- Web clips / articles → `vault/sources/articles/`
- Audio transcripts → `vault/sources/notes/`

Use `mv`, not `cp`. After moving: immutable. Do NOT modify again.

### F. Update Manifest

Append to `inbox/_ingested.md`:
```
| {filename} | {hash} | {YYYY-MM-DD} | {N pages touched} |
```

### G. Update Index and Log

- `vault/index.md`: add new pages to the right section
- `vault/log.md`: append `## [YYYY-MM-DD HH:MM] /ingest | {source filename} | {N pages}: {list}`

## Step 4: Report

After all files processed:
- N files ingested
- M wiki pages created, K updated
- Contradictions flagged (if any)
- Suggested next steps

## Special Cases

**URL pasted in chat:** Fetch with WebFetch → save to `inbox/web-{date}-{slug}.md` → ingest
**Text pasted in chat:** Save to `inbox/chat-{date}.md` → ingest
**Source is huge (>50KB, interactive mode):** Skim and summarize first, ask which sections to deep-read
**Source is in a subfolder of architect-kit/:** Can ingest directly — pass the path to `/ingest <path>`

## What /ingest Does NOT Do

- Modify `vault/sources/` after archiving (immutability rule)
- Run automations (`/study-brief`, `/design-lab`, etc.)
- Deduplicate the wiki — that's `/lint`
