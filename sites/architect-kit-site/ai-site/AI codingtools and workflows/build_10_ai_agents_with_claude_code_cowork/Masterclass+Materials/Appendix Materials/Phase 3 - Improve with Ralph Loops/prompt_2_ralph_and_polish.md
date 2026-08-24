# Prompt 2: Run Ralph Loop — Review, Improve, and Verify

> Ralph will review the app, improve it, then use the frontend-design skill to verify the quality. It repeats this 2-3 times until the app looks like it was designed by a professional team.

Copy and paste the following into Claude Code:

```
Context: I have a working calorie tracker app with Gemini AI (text + image food recognition), a local database, and a connected frontend. I just installed the Ralph Loop plugin and the frontend-design skill. I want to make this app look and feel like it was built by a professional team at a real company.

Instruction: Run the Ralph Loop to review and improve the app. After each round of improvements, use the frontend-design skill to verify the quality — is the UI clean, usable, well-arranged, and visually polished? Repeat this cycle 2-3 times until the app meets a high design standard. Then do a final documentation pass. Don't ask me any questions — just run the loop.

Input:
The quality bar I want:
- Looks like a real product — not a tutorial project or a hackathon demo
- Clean layout, consistent spacing, professional color palette, good typography
- Intuitive to use — a first-time user knows exactly what to do
- Everything is well-arranged — nothing feels randomly placed
- Works well on both desktop and mobile
- Has the small details that matter — loading states, empty states, smooth interactions, proper error messages

Features to add if not already there:
- Daily calorie goal with a visual progress bar (green/yellow/red)
- Macro breakdown (protein, carbs, fat) with a visual
- Meal categories (Breakfast, Lunch, Dinner, Snack) with grouped entries
- A header with the app name and today's date
- Card-style food entries

Output:
- A polished, professional-quality calorie tracker app
- Updated CLAUDE.md reflecting the final state (under 200 lines) with a "Next Steps" section (deploy to Vercel, food history charts, user preferences, barcode scanning)
- A final dated entry in docs/ summarizing what Ralph found, what was improved, and how the design skill verified the quality
- A PLAN.md with three sections: "What We Built", "What We Improved", "Future Roadmap"
```
