# /market-pulse — Daily Competitive Intelligence for Optimus

Scrapes 8 competitor websites + web searches for news. Tags Action Needed vs FYI. Posts to Notion.

## Step 1: Load Context

Read in order:
1. `soul.md` — priority lens
2. `brand/config/brand-config.md` — report format
3. `work/03-market-pulse/watchlist.md` — companies and scrape targets
4. `vault/business/competitors/{company}.md` for each company — prior state

## Step 2: Chrome Scraping (High/Medium companies)

For each company on the watchlist, in priority order:

```
mcp__claude-in-chrome__tabs_create_mcp → navigate to pricing page → read_page
navigate to product/features page → read_page
navigate to careers page → read_page
navigate to blog page → read_page
tabs_close_mcp
```

Extract per page:
- **Pricing**: fee structure, brokerage, AMC, subscription tiers, any changes
- **Product**: new features, asset classes added, integrations, partnerships
- **Careers**: new job titles, departments hiring (signals investment areas)
- **Blog**: latest 3 posts and themes

Compare against prior state in vault/business/competitors/{company}.md.
Flag delta as: `NEW_FEATURE`, `PRICE_CHANGE`, `HIRING_SIGNAL`, `PRODUCT_LAUNCH`, `LEADERSHIP_CHANGE`.

## Step 3: Web Search (all companies)

For each company:
```
WebSearch: "{company} news funding product launch 2026"
WebSearch: "{company} CEO leadership India fintech 2026"
```

Also run sector searches:
```
WebSearch: "India wealth management fintech news August 2026"
WebSearch: "SEBI mutual fund demat regulation 2026"
```

## Step 4: Classify Findings

**Action Needed** — flag for Ankur to review:
- Price change in MF / demat / G-Sec / insurance / LAMF domain
- New product feature in any domain Optimus competes in
- Competitor funding round or acquisition
- Leadership change at High priority competitor
- SEBI/regulatory announcement affecting the sector

**FYI** — log, no action:
- Blog posts and thought leadership
- General hiring (no specific Optimus-relevant department)
- Market growth stats, roundups

**Named executives found** → create `vault/people/{name}.md` if not exists.

## Step 5: Generate Report

```
# Market Pulse — YYYY-MM-DD

## Action Needed (N)
[Company] — [finding] — [why it matters for Optimus] — SOURCE: [URL]

## FYI (N)
[Company]: [finding] — SOURCE: [URL]

## Sector Trends
[2-3 macro signals from sector searches]

## Competitor Snapshots
[one-line status per company]
```

## Step 6: Update Vault

For each company: update `vault/business/competitors/{company}.md`
- Summary section only (latest intel, not full history)
- Append to `Last Updated` field

Update `vault/business/market/trends.md` — sector trends section.

## Step 7: Post to Notion

Create page in Market Scans DB (`collection://183138d4-efd4-4465-891a-8a1fddd65c23`):
- Name: "Scan YYYY-MM-DD"
- Date, Companies Scanned, Action Items, FYI Count
- Summary: one-line

Content: callout blocks — red for Action Needed, gray for FYI, blue for Sector Trends.

## Step 8: Save Local

`vault/projects/market-pulse/news-archive/YYYY-MM-DD.md`
Screenshots → `vault/projects/market-pulse/screenshots/YYYY-MM-DD-{company}.png`

## Step 9: Update Log

`vault/log.md`: `## [YYYY-MM-DD HH:MM] /market-pulse | N action items, N FYI, N companies scanned`
