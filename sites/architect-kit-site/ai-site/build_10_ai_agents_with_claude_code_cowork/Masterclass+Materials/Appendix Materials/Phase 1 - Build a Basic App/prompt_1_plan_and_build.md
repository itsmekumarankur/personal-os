# Prompt 1: Plan and Build the Calorie Tracker

> \\\*\\\*Before pasting:\\\*\\\* Activate Plan Mode by pressing `Shift+Tab` twice. You should see "Plan Mode" in the bottom bar. Claude will first think through the design, then ask to start building. When it does, approve it.

Copy and paste the following into Claude Code:

```
Context: I have an empty project folder with just a .env and .gitignore file. I want to build a calorie tracker web app from scratch.

Instruction: First, plan out the architecture — what components, what data structure, how the UI flows. Then build the entire app. Use Next.js with TypeScript and Tailwind CSS. Save the food log in a local database so it persists across page refreshes. After everything is working, create documentation. Don't ask me any questions — just plan it, build it, and document it.

Input:
- A simple single-page app — no login, no accounts
- A search bar to find foods, with a list of 20+ common foods I can quickly add (chicken, rice, eggs, banana, etc.)
- Each food should have calories, protein, carbs, fat, and serving size
- A daily food log showing what I've eaten and a calorie total at the top
- The app should run with npm run dev

Output:
- A written plan of the architecture
- A fully working calorie tracker at localhost:3000
- A CLAUDE.md file describing the project — what it does, how to run it, tech stack, folder structure, what's coming next. Keep under 200 lines.
- A docs/ folder with a decision log file named with today's date (e.g., docs/2026-03-15-initial-build.md) recording what was built, what technical choices were made and why.
- Run the app for user preview at the end.
```

