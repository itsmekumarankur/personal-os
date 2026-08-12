# Market Pulse — Spec

## What It Does

Daily competitive intelligence scan of Optimus wealth platform rivals.
Scrapes pricing/product/careers/blog pages via Chrome. Web searches for news and funding.
Tags findings as Action Needed or FYI. Posts branded report to Notion.

## Watchlist

See `work/03-market-pulse/watchlist.md`. 8 companies, prioritized.

## Inputs

| Source | What | How |
|--------|------|-----|
| Chrome MCP | Pricing, product, careers, blog pages | `mcp__claude-in-chrome__navigate` + `read_page` |
| WebSearch | News, funding, leadership changes | `WebSearch` per company |
| Notion MCP | Internal docs, prior scans | `notion-search` |
| soul.md | Priority filter | Read at start |
| brand/config/brand-config.md | Report format | Read at start |
| vault/business/competitors/ | Existing intel | Read each company page |

## Chrome Scraping Protocol

For each High/Medium priority company:
1. Navigate to pricing page → read text → extract: fee structure, changes, new tiers
2. Navigate to product/features page → extract: new features, asset classes, integrations
3. Navigate to careers page → extract: new roles, departments hiring, headcount signals
4. Navigate to blog/news page → extract: last 3 posts, themes

Compare against prior scan in `vault/business/competitors/{company}.md`.
Flag delta as: NEW FEATURE, PRICE CHANGE, HIRING SIGNAL, PRODUCT LAUNCH.

## Classification Logic

**Action Needed** (flag for Ankur to review):
- Price change in any domain Optimus competes in
- New product feature in MF/demat/G-Sec/insurance/LAMF
- Leadership change at a competitor
- Funding round or acquisition

**FYI** (log, no immediate action):
- Blog posts, thought leadership
- Careers page updates (general hiring)
- Minor UI/UX changes

## Output Files

- `vault/projects/market-pulse/news-archive/YYYY-MM-DD.md` — daily report
- `vault/business/competitors/{company}.md` — updated with latest summary only
- `vault/business/market/trends.md` — sector trends, updated weekly
- Screenshots → `vault/projects/market-pulse/screenshots/YYYY-MM-DD-{company}.png`

## Notion Resources

- Market Scans database: `collection://183138d4-efd4-4465-891a-8a1fddd65c23`
- Market Scans page: https://app.notion.com/p/818f6a78f1024899a473a52649cf6e1c
- Personal OS page: https://app.notion.com/p/3b82145568cd814c9c1eeb5ea21e2f3e

## Sprint Board Contract

- Sprint Board DB: `collection://9a4012bf-a097-4da2-b1d3-05e2f35a8188`
- Mark "Market Pulse" Done when built.
