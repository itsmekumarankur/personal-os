# Prompt 1: Add AI-Powered Food Recognition

Enable plan mode and then run the following prompt: (Shift+Tab)

Copy and paste the following into Claude Code:

```
Context: I have a working calorie tracker app with hardcoded food data and a local database. Now I want to make it smarter using the Gemini API (model: gemini-2.5-flash-lite). The API key is already in my .env file as GEMINI\\\_API\\\_KEY.

Instruction: Build the backend API routes for two ways to look up nutrition data using AI. Don't change the frontend yet — just get the API working so we can connect it in the next step.

Input:
- Text-based lookup: I type a description of what I ate (like "grilled chicken with rice and salad") and get back the calories and macros
- Image-based lookup: I upload a photo of my meal and Gemini analyzes the image to identify the foods and estimate calories

Output: Two working API routes — one for text queries, one for image uploads — both returning structured nutrition data from Gemini. Frontend untouched. Updated CLAUDE.md and a new dated entry in docs/ recording what was added, what decisions were made, and why.
```

