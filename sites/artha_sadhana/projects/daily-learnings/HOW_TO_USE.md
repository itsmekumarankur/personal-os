# How to Use This — Daily Workflow

## One-time setup (5 minutes)

1. Create a new GitHub repo named `daily-learnings`.
2. Upload everything in this folder to that repo (drag-and-drop on github.com works fine, or `git push`).
3. Go to repo **Settings → Pages → Source → main branch → / (root)**. Save.
4. Your site goes live at `https://YOUR_USERNAME.github.io/daily-learnings/` within a minute or two.
5. Edit `_config.yml` and replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

## Every day you learn something new

1. Go to the `_posts` folder on github.com (or your local clone).
2. Click **Add file → Create new file**.
3. Name it exactly like this: `YYYY-MM-DD-short-title.md`
   Example: `2026-07-01-mcp-servers-explained.md`
4. Paste this template and fill it in:

```
---
title: "Your Article Title"
date: 2026-07-01
tags: [ai, leadership]
read_time: "3 min read"
---

Your article content here. Write naturally — this renders as markdown.

![optional image](../../assets/images/your-image.png)
```

5. If you have an image: upload it to `assets/images/` first, reference it by filename.
6. If you have an audio recap: upload the mp3 to `assets/audio/`, add `audio: filename.mp3` to the frontmatter (see sample post 2 for the exact placement).
7. Commit the file directly to `main`. GitHub Pages rebuilds automatically — your new article is live in under 2 minutes.

## That's the whole loop
Find something worth remembering → write 200-400 words → commit → it's published. No build tools, no local setup required if you're editing straight from github.com on your phone or laptop.

## Optional: posting from your phone
GitHub's mobile site lets you create files directly — bookmark `github.com/YOUR_USERNAME/daily-learnings/new/main/_posts` for a one-tap "new post" shortcut.
