# Prompt 2: Connect AI to the App

Enable plan mode and then run the following prompt: (Shift+Tab)

Copy and paste the following into Claude Code:

```
Context: My calorie tracker now has two working API routes — one for text-based food queries and one for image uploads — both powered by Gemini. The frontend still only uses hardcoded food data.

Instruction: Connect the Gemini API routes to the frontend so users have three ways to add food. Don't ask me any questions — just build it.

Input:
- Quick-add from the existing list of common foods (keep what we already have)
- A text box where users describe what they ate in plain English — AI looks up the nutrition
- An upload button where users can take or upload a photo of their meal — AI analyzes the image and identifies all the foods
- For photo uploads: show a preview of the image, and if Gemini finds multiple food items, show all of them so the user can confirm before adding to the log
- Everything should save to the database
- Show a loading spinner while waiting for AI responses
- Show a friendly error message if something goes wrong

Output: The app now has three ways to add food — quick-add, text search, and photo upload. All entries persist in the database. Loading states and error handling work. Updated CLAUDE.md and a new dated entry in docs/ with what changed and why.
```

