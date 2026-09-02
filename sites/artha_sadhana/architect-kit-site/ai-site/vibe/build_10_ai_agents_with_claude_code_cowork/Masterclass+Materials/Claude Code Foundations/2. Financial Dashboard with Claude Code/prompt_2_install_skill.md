# Prompt 2: Install the Frontend Design Skill

Skills are reusable instruction packages that teach Claude Code how to approach specific tasks better. Let's install one that dramatically improves UI/design output.

---

## Step 1: Install the frontend-design skill

Run this in your terminal (NOT inside Claude Code — exit first if needed):

```bash
npx skills add anthropics/claude-code --skill frontend-design
```

> **What this does:** Downloads the `frontend-design` skill from Anthropic's official repo and places it in your project's `.claude/skills/frontend-design/` folder. This skill teaches Claude to create distinctive, production-grade designs instead of generic "AI-looking" output.

---

## Step 2: Launch Claude Code and verify

```bash
claude
```

Inside Claude Code, type:

```
/skills
```

You should see `frontend-design` listed. This skill will now automatically activate whenever Claude builds anything visual.

---

## What changed?

Without the skill, Claude produces safe, generic designs — default fonts, muted colors, predictable layouts. The "AI slop" look.
With the skill, Claude commits to a design direction — bold typography, intentional color palettes, purposeful animations, professional spacing. The difference is dramatic. Let's see it in the next prompt.
