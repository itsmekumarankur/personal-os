# Prompt 0: Setup Your Environment

## Step 1: Get a Free Gemini API Key

1. Go to [https://aistudio.google.com/](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy the key — you'll need it in a moment

> No credit card needed. The free tier gives you 1,000 requests/day.

## Step 2: Make Sure Node.js is Installed

# Node.js is a runtime environment that lets you run JavaScript outside of a web browser, usually on a server.

Open your terminal and run:

```bash
node -v
```

You should see a version number (v18 or higher). If not, install Node.js from [nodejs.org](https://nodejs.org/).

## Step 3: Create an Empty Folder and Launch Claude Code

```bash
mkdir \\\~/Desktop/my\\\_calorie\\\_tracker
cd \\\~/Desktop/my\\\_calorie\\\_tracker
claude
```

## Step 4: Paste This Prompt into Claude Code

```
Context: I'm starting a new project in this empty folder. Nothing exists here yet.

Instruction: Create a .env file with a placeholder for my Gemini API key and a .gitignore file that ignores common things. Don't build anything else yet — just these two files.

Input: GEMINI\\\_API\\\_KEY=your-key-here as the placeholder in .env.

Output: A .env file with the placeholder key and a .gitignore file. Nothing else.
```

## Step 5: Add Your API Key

Open the `.env` file and replace the placeholder with your real key:

```
GEMINI\\\_API\\\_KEY=your-actual-key-here
```

