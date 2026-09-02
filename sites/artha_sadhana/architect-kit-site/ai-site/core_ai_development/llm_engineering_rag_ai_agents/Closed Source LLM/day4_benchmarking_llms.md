# 🚀 AI Landing Page Generator (OpenAI vs Claude vs Gemini) — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty notebook" to "three AI models each building you a full landing page — so you can judge them side by side." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

Think of this notebook as **eight stops on a road trip**:

```
🏁 START      📊 BENCHMARKS      🥊 BLIND TEST      🔑 3-KEY SETUP      💡 THE PROMPT      🌐 GPT BUILDS      💎 GEMINI BUILDS      🎨 CLAUDE BUILDS
Overview  →  Leaderboards   →  Chatbot Arena   →  3 AI providers  →  One shared brief →  index.html #1  →  index.html #2   →  index.html #3
```

By the end, you go from "which AI model is even best?" to having **three real, saved HTML landing pages** — one from OpenAI, one from Gemini, one from Claude — generated from the exact same brief, ready to compare head-to-head.

---

## Stop 1 — 🏁 Project Overview
**What's happening:** Screenshots preview the finished experience — the same startup idea, turned into three different landing pages by three different AI "front-end developers."

**Why it matters:** You see the comparison exercise up front, so every later stop makes sense as a piece of that puzzle.

---

## Stop 2 — 📊 LLM Benchmarks & Leaderboards
**What's happening:** A tour of how AI models get ranked against each other *before* you even write code — using public leaderboards (like Vellum's) that track speed, context window size, knowledge cut-off dates, and accuracy.

**Fun fact dropped in:** A model running at ~2,500 tokens/second is roughly writing 1,800 full words *per second* — fast enough to draft a short essay in the blink of an eye.

**Practice challenge:** Use Vellum to compare Gemini 2.5 Pro against DeepSeek-R1 across latency, context window, and accuracy.

**Why it matters:** Before picking a model to build with, it helps to know how models are formally evaluated — not just vibes.

---

## Stop 3 — 🥊 Blind Test Evaluation with Chatbot Arena
**What's happening:** Instead of trusting benchmark charts alone, you become the judge. Chatbot Arena lets you send the same prompt to two anonymous AI models and vote on which answer is better — no brand names shown, so no bias.

**Practice challenge:** Run a blind test with three prompt types:
- 🔧 **Technical** — "Explain how a blockchain works."
- 🎨 **Creative** — a heartfelt birthday poem.
- 😄 **Funny** — a joke about electric cars.

**Why it matters:** This builds real intuition for *how* these models differ in style and quality — intuition that's put to direct use two stops later.

---

## Stop 4 — 🔑 Setting Up 3 API Keys (OpenAI, Gemini, Claude)
**What's happening:** This is where the notebook levels up from "one AI provider" to **three simultaneously**:
- 🟢 **OpenAI** (already familiar from earlier lessons)
- 🔵 **Google Gemini** — via the `google-generativeai` library
- 🟣 **Anthropic Claude** — via the `anthropic` library

All three keys are loaded securely from a single `.env` file (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`) — the safe pattern this course keeps reinforcing. Each provider's client is initialized, and a couple of helper functions are defined to neatly display generated Markdown and HTML.

**Quick sanity check:** Each of the three clients is tested with the same simple prompts — a math riddle and a silly birthday poem — just to confirm all three connections actually work before the real task begins.

**Practice challenge:** Compare how OpenAI, Gemini, and Claude each handle a small coding task (a BMI calculator function).

**Why it matters:** This is the "assemble your panel of judges" stop — three different AI brains, all wired up and ready to tackle the same challenge.

---

## Stop 5 — 💡 Defining the Startup Idea & the Shared Prompt
**What's happening:** For a fair comparison, all three models need to receive **the exact same brief**. So the notebook defines:
- A fictional startup: **"ConnectGenius"** — an AI-powered CRM that predicts customer needs and automates follow-ups
- One carefully engineered prompt (`html_prompt`) that tells the AI to act as a front-end developer and generate a complete, single-file `index.html` — covering a header, hero section, features, a "How it Works" section, and more

**Why it matters:** This is the scientific-method moment — controlling every variable except the AI model itself, so any differences in the output are genuinely due to *which AI* built the page.

**Practice challenge:** Swap in your own fictional startup name and concept to personalize the experiment.

---

## Stop 6 — 🌐 Generate the Landing Page with OpenAI
**What's happening:** The shared prompt is sent to OpenAI's `gpt-4o` model. The flow:
1. Call the API with `html_prompt`
2. Extract the generated HTML text
3. Strip out any accidental Markdown code-fences (```html blocks) so it's pure HTML
4. Display the code inline
5. **Save it to disk** as `openai_landing_page.html`

**Why it matters:** This produces Contestant #1 — a real, working landing page file you can open directly in a browser.

**Practice challenge:** Swap `gpt-4o` for `gpt-4o-mini` and see how much the output changes.

---

## Stop 7 — 💎 Generate the Landing Page with Google Gemini
**What's happening:** The identical `html_prompt` goes to Gemini this time, using the slightly different `generate_content()` call style of the `google-generativeai` library. Same cleanup-and-save routine follows, producing `gemini_landing_page.html`.

**Why it matters:** Contestant #2 enters the ring — same brief, same rules, different AI "personality" behind the code.

**Practice challenge:** Compare Gemini's raw HTML structure against OpenAI's, and try generating a page for a completely different startup concept (like quantum computing).

---

## Stop 8 — 🎨 Generate the Landing Page with Anthropic Claude
**What's happening:** The same prompt makes its final stop at Claude Sonnet, using Anthropic's `messages.create()` API structure. The response text is extracted from `response.content[0].text`, cleaned up the same way, displayed, and saved as `claude_landing_page.html`.

**Why it matters:** Contestant #3 completes the lineup — now there are three saved, ready-to-open HTML files built from one identical brief.

**Practice challenge:** Open all three saved files side by side in a browser or text editor and judge them yourself: which felt cleanest? Which followed instructions most faithfully? (There's no single right answer — it's genuinely subjective and can vary run to run.)

---

## 🏆 What You Walk Away With
By the end of this notebook, you've run a real, controlled **three-way AI bake-off**:

✅ Learned how public benchmarks and blind-test arenas evaluate AI models
✅ Connected to three different AI providers in one notebook, securely
✅ Designed one carefully structured prompt used identically across all three
✅ Generated and saved three complete, working landing pages — one per model
✅ Practiced comparing AI-generated code side by side, forming your own opinion instead of relying on a leaderboard alone

**Next natural steps** (not in this notebook, but the logical Stop 9): wrapping this into a Gradio interface so anyone can type a startup idea and instantly get three landing pages to compare, or scoring the outputs automatically with a fourth "judge" AI call.

---

*Guide generated from `Landing_Page_Generator_with_OpenAI__Claude__and_Gemini.ipynb`*
