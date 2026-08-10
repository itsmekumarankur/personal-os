# /lint — Vault Health Check

Audit the vault for quality issues. Run periodically or whenever the vault feels messy.

## What Lint Checks

### 1. Orphan Pages
Pages that have no `[[wiki links]]` pointing to them from anywhere else.
These are dead ends in the knowledge graph — nothing connects to them.
Fix: add links from related pages, or delete if genuinely useless.

### 2. Stub Pages
Pages with fewer than 50 characters of real body content.
These are placeholders that never got filled in.
Fix: either fill them in or delete them.

### 3. Missing Frontmatter
Pages missing YAML frontmatter (no `tags`, `date_created`, `date_updated`).
Fix: add frontmatter.

### 4. Stale Pages
Pages with `date_updated` more than 90 days ago that are in active domains (learning/, courses/, projects/).
These might be outdated.
Fix: either update them or mark them as archived.

### 5. Broken Wiki Links
`[[link]]` references that point to pages that don't exist yet.
These are desirable in moderation (future pages to create), but flag them if there are many.

### 6. Index Gaps
Pages that exist in `vault/` but aren't listed in `vault/index.md`.
Fix: add them to the index.

### 7. Log Gaps
Sessions where activity happened (recent journal entries) but no `/ingest` or `/learn` was logged.
Might mean learning happened that wasn't captured in the vault.

### 8. Course Tracker Accuracy
Courses in `vault/courses/tracker.md` with no recent log activity. Still active?

### 9. soul.md Quality
- Is it filled in? (No TODO/TBD/placeholder)
- Is it under 2.5KB?
- Does it have real writing samples?

## Output Format

For each issue found:
```
[TYPE] vault/path/to/page.md
  Issue: [description]
  Fix: [what to do]
```

End with a summary: "X issues found. Y are quick fixes, Z need your input."

## Auto-Fix vs. Manual

The agent auto-fixes:
- Missing frontmatter (generates from page content)
- Index gaps (adds page to index)

The agent asks before:
- Deleting stub pages (might be intentional placeholders)
- Updating stale pages (needs to know if still relevant)

## After Lint

Append to `vault/log.md`: `## [YYYY-MM-DD HH:MM] /lint | [N] issues found, [M] auto-fixed`
