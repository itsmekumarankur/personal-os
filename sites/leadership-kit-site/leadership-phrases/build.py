#!/usr/bin/env python3
"""
Build script for the Leadership Lexicon project.

Reads every .md file in entries/, parses its YAML front-matter
(scenario, category, tags, date_added) plus its markdown body,
and generates a single static index.html.

Usage:
    python3 build.py

Re-run this any time you add, edit, or remove a .md file in entries/.
"""

import glob
import html
import json
import re
from datetime import date
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
ENTRIES_DIR = ROOT / "entries"
OUTPUT_FILE = ROOT / "index.html"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_entry(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        raise ValueError(f"{path.name}: missing YAML front-matter (---...---)")

    meta = yaml.safe_load(match.group(1)) or {}
    body_md = match.group(2).strip()
    body_html = markdown.markdown(body_md, extensions=["extra"])

    return {
        "id": path.stem,
        "scenario": meta.get("scenario", path.stem),
        "category": meta.get("category", "Uncategorized"),
        "tags": meta.get("tags", []) or [],
        "date_added": str(meta.get("date_added", "")),
        "body_html": body_html,
        "search_blob": " ".join(
            [
                meta.get("scenario", ""),
                meta.get("category", ""),
                " ".join(meta.get("tags", []) or []),
                re.sub("<[^<]+?>", " ", body_html),
            ]
        ).lower(),
    }


def load_entries() -> list[dict]:
    paths = sorted(glob.glob(str(ENTRIES_DIR / "*.md")))
    if not paths:
        raise SystemExit(
            f"No .md files found in {ENTRIES_DIR}. Add at least one entry first."
        )
    entries = [parse_entry(Path(p)) for p in paths]
    entries.sort(key=lambda e: e["date_added"], reverse=True)
    return entries


def render_card(e: dict, index: int) -> str:
    tag_chips = "".join(
        f'<span class="chip">{html.escape(t)}</span>' for t in e["tags"]
    )
    num = f"{index:02d}"
    return f"""
    <article class="card" data-search="{html.escape(e['search_blob'])}" data-category="{html.escape(e['category'])}">
      <div class="card-frame">
        <div class="card-head">
          <span class="card-num">{num}</span>
          <span class="card-category">{html.escape(e['category'])}</span>
        </div>
        <h3 class="card-scenario">{html.escape(e['scenario'])}</h3>
        <div class="card-body">{e['body_html']}</div>
        <div class="card-foot">
          <div class="chips">{tag_chips}</div>
          <time>{html.escape(e['date_added'])}</time>
        </div>
      </div>
    </article>"""


def render_category_filters(categories: list[str]) -> str:
    buttons = ['<button class="filter-btn active" data-filter="all">All</button>']
    for c in categories:
        buttons.append(
            f'<button class="filter-btn" data-filter="{html.escape(c)}">{html.escape(c)}</button>'
        )
    return "\n".join(buttons)


def build():
    entries = load_entries()
    categories = sorted({e["category"] for e in entries})

    cards_html = "\n".join(render_card(e, i + 1) for i, e in enumerate(entries))
    filters_html = render_category_filters(categories)

    template = TEMPLATE.replace("{{CARDS}}", cards_html)
    template = template.replace("{{FILTERS}}", filters_html)
    template = template.replace("{{COUNT}}", str(len(entries)))
    template = template.replace("{{CATEGORY_COUNT}}", str(len(categories)))
    template = template.replace("{{BUILD_DATE}}", date.today().isoformat())

    OUTPUT_FILE.write_text(template, encoding="utf-8")
    print(f"Built {OUTPUT_FILE} — {len(entries)} entries across {len(categories)} categories.")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Leadership Lexicon</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg: #0E1420;
    --bg-raised: #141B29;
    --line: #24344A;
    --line-soft: #1A2434;
    --ink: #E7E4DA;
    --ink-dim: #93A0B4;
    --brass: #D9A15D;
    --brass-dim: #9C7748;
    --blue: #4E85B8;
  }
  *{ box-sizing: border-box; }
  html{ scroll-behavior: smooth; }
  body{
    margin:0;
    background:
      linear-gradient(var(--line-soft) 1px, transparent 1px) 0 0/48px 48px,
      linear-gradient(90deg, var(--line-soft) 1px, transparent 1px) 0 0/48px 48px,
      var(--bg);
    color: var(--ink);
    font-family: 'Inter', sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  .wrap{ max-width: 1080px; margin: 0 auto; padding: 0 28px 100px; }

  header.top{
    padding: 64px 0 36px;
    border-bottom: 1px solid var(--line);
    margin-bottom: 40px;
  }
  .eyebrow{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--blue);
    display:flex;
    align-items:center;
    gap: 10px;
  }
  .eyebrow::before{
    content:"";
    width: 18px; height: 1px;
    background: var(--blue);
    display:inline-block;
  }
  h1{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: clamp(34px, 5vw, 52px);
    margin: 18px 0 10px;
    letter-spacing: -0.01em;
  }
  h1 span{ color: var(--brass); }
  .sub{
    color: var(--ink-dim);
    font-size: 15.5px;
    max-width: 560px;
    line-height: 1.55;
  }
  .meta-row{
    display:flex; gap: 28px; margin-top: 26px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: var(--ink-dim);
  }
  .meta-row b{ color: var(--ink); font-weight: 500; }

  .controls{
    display:flex; flex-wrap: wrap; align-items:center;
    gap: 12px; margin-bottom: 34px;
  }
  #search{
    flex: 1 1 240px;
    background: var(--bg-raised);
    border: 1px solid var(--line);
    color: var(--ink);
    padding: 11px 14px;
    border-radius: 3px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    outline: none;
  }
  #search:focus{ border-color: var(--blue); }
  #search::placeholder{ color: var(--ink-dim); }

  .filters{ display:flex; flex-wrap: wrap; gap: 8px; }
  .filter-btn{
    background: transparent;
    border: 1px solid var(--line);
    color: var(--ink-dim);
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    padding: 8px 12px;
    border-radius: 3px;
    cursor: pointer;
    transition: all .15s ease;
  }
  .filter-btn:hover{ border-color: var(--blue); color: var(--ink); }
  .filter-btn.active{
    background: var(--brass);
    border-color: var(--brass);
    color: #1a1408;
    font-weight: 500;
  }

  .grid{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
  }

  .card{ position: relative; }
  .card-frame{
    background: var(--bg-raised);
    border: 1px solid var(--line);
    border-radius: 4px;
    padding: 22px 22px 18px;
    height: 100%;
    display: flex;
    flex-direction: column;
    position: relative;
    transition: border-color .15s ease, transform .15s ease;
  }
  .card-frame::before, .card-frame::after{
    content:"";
    position: absolute;
    width: 9px; height: 9px;
    border-top: 1px solid var(--brass-dim);
    border-left: 1px solid var(--brass-dim);
    top: -1px; left: -1px;
    opacity: .8;
  }
  .card-frame::after{
    top: auto; left: auto;
    bottom: -1px; right: -1px;
    border-top: none; border-left: none;
    border-bottom: 1px solid var(--brass-dim);
    border-right: 1px solid var(--brass-dim);
  }
  .card:hover .card-frame{
    border-color: var(--blue);
    transform: translateY(-2px);
  }

  .card-head{
    display:flex; justify-content: space-between; align-items: center;
    margin-bottom: 14px;
  }
  .card-num{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--brass-dim);
    letter-spacing: 0.08em;
  }
  .card-category{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--blue);
    border: 1px solid var(--line);
    padding: 3px 8px;
    border-radius: 20px;
  }
  .card-scenario{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 17px;
    font-weight: 600;
    line-height: 1.35;
    margin: 0 0 14px;
    color: var(--ink);
  }
  .card-body{ flex: 1; font-size: 14px; line-height: 1.6; color: var(--ink); }
  .card-body blockquote{
    margin: 0 0 12px;
    padding: 10px 14px;
    border-left: 2px solid var(--brass);
    background: rgba(217,161,93,0.06);
    font-style: italic;
    color: var(--ink);
    border-radius: 0 3px 3px 0;
  }
  .card-body blockquote p{ margin: 0; }
  .card-body p:not(blockquote p){
    color: var(--ink-dim);
    font-size: 13px;
    margin-top: 12px;
  }
  .card-body strong{ color: var(--brass); font-weight: 600; }

  .card-foot{
    display:flex; justify-content: space-between; align-items: center;
    margin-top: 16px; padding-top: 14px;
    border-top: 1px dashed var(--line);
  }
  .chips{ display:flex; flex-wrap: wrap; gap: 6px; }
  .chip{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: var(--ink-dim);
    background: var(--line-soft);
    padding: 3px 8px;
    border-radius: 3px;
  }
  time{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: var(--ink-dim);
    white-space: nowrap;
  }

  .empty-state{
    display:none;
    text-align:center;
    padding: 60px 20px;
    color: var(--ink-dim);
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    border: 1px dashed var(--line);
    border-radius: 4px;
  }

  footer{
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid var(--line);
    color: var(--ink-dim);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
  }

  @media (max-width: 600px){
    .wrap{ padding: 0 18px 60px; }
    header.top{ padding: 44px 0 28px; }
  }
</style>
</head>
<body>
<div class="wrap">

  <header class="top">
    <div class="eyebrow">Field Notes / Daily Use</div>
    <h1>Leadership <span>Lexicon</span></h1>
    <p class="sub">A running library of phrases and lines for the moments that actually happen day to day — hard feedback, tense rooms, managing up. Not theory. What to actually say.</p>
    <div class="meta-row">
      <span><b>{{COUNT}}</b> entries</span>
      <span><b>{{CATEGORY_COUNT}}</b> categories</span>
      <span>last built <b>{{BUILD_DATE}}</b></span>
    </div>
  </header>

  <div class="controls">
    <input id="search" type="text" placeholder="Search phrases, scenarios, tags…">
    <div class="filters">
      {{FILTERS}}
    </div>
  </div>

  <div class="grid" id="grid">
    {{CARDS}}
  </div>

  <div class="empty-state" id="empty-state">No entries match that search — try a different word or filter.</div>

  <footer>
    Built from markdown in <code>entries/</code>. Add a .md file, re-run <code>python3 build.py</code>.
  </footer>

</div>

<script>
  const searchInput = document.getElementById('search');
  const filterBtns = document.querySelectorAll('.filter-btn');
  const cards = Array.from(document.querySelectorAll('.card'));
  const emptyState = document.getElementById('empty-state');
  let activeFilter = 'all';

  function applyFilters(){
    const q = searchInput.value.trim().toLowerCase();
    let visibleCount = 0;
    cards.forEach(card => {
      const matchesCategory = activeFilter === 'all' || card.dataset.category === activeFilter;
      const matchesSearch = !q || card.dataset.search.includes(q);
      const show = matchesCategory && matchesSearch;
      card.style.display = show ? '' : 'none';
      if (show) visibleCount++;
    });
    emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
  }

  searchInput.addEventListener('input', applyFilters);
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.dataset.filter;
      applyFilters();
    });
  });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
