# Leadership Lexicon

A simple project: you write leadership phrases as markdown files, and a build
script turns them into one styled `index.html` page you can open in any
browser (or host on GitHub Pages next to Architects Lab).

## How to add a new phrase

1. Copy any file in `entries/` as a starting point, e.g.:

   ```
   entries/004-my-new-scenario.md
   ```

2. Fill in the front-matter and body:

   ```markdown
   ---
   scenario: One line describing the situation
   category: Feedback
   tags: [tag1, tag2]
   date_added: 2026-08-04
   ---

   > "The actual line you'd say."

   **Why it works:** one or two lines on why this phrasing works.
   ```

   - `scenario` — short, specific, written the way you'd search for it later
     ("pushing back on a leader's decision"), not a generic label.
   - `category` — used for the filter buttons at the top of the page. Reuse
     an existing category where it fits (Feedback, Managing Up, Conflict,
     etc.) so the filters stay useful instead of multiplying.
   - `tags` — free-form, used only for search.
   - Body — one or more `>` blockquote lines for the phrase(s) themselves,
     plus an optional `**Why it works:**` note.

3. Rebuild:

   ```
   python3 build.py
   ```

   This regenerates `index.html` from every `.md` file in `entries/`.

4. Open `index.html` in a browser. Use the search box or category filters
   to find a phrase before a meeting.

## Notes

- No server needed — `index.html` is fully static and self-contained.
- Newest entries (by `date_added`) show first.
- If you want this on the web, push the folder to a GitHub repo and enable
  GitHub Pages, same as Architects Lab.
# leadership-phrases
