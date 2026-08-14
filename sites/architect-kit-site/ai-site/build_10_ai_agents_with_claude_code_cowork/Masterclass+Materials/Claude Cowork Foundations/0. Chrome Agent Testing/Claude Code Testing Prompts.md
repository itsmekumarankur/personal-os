Copy and paste the following into Claude's browser:

```
Context:
You are a team of AI agents building Apple investment dashboard. Output a single, polished HTML file.

Agents

Research Agent

Go to Yahoo Finance (AAPL)
Extract: price, % change, market cap, P/E, recent trend
Open only 3 recent news articles and summarize each in 2–3 bullets
No extra tabs


Analyst Agent
Identify key drivers of stock movement
Clearly separate signal vs noise
Provide 3–5 insights + 1–2 risks
Final stance: Bullish / Bearish / Neutral
Include reasoning + confidence level


Developer Agent
Generate a single self-contained HTML dashboard with:
	Apple stats (header)
	Price chart (e.g., Chart.js)
	News summaries (card layout)
	Insights (signal vs noise)
	Final recommendation (visually highlighted)

The page should be modern, clean UI (dark mode preferred), Everything runs locally (no setup). Add the Apple logo and create beautiful animations. Output only the HTML file

```




Copy and paste the following into Claude Code:

```
Context: I run a personal finance coaching service called "WealthPath." I want a website page I can open in my browser that helps clients understand their financial situation and gives them a simple plan.

Instruction: Create a single file called "wealthpath.html" with everything a client would need — a clean modern dashboard, an interactive financial intake flow (step-by-step, not a long form), a visual summary of their finances, personalized recommendations, and a way to book a consultation.

Implement it without using any frameworks or external libraries.

Input:

- Business name: WealthPath
- Tagline: "Clarity and control over your financial future"
- Intake questions: 
	Monthly income? (input number)
	Monthly expenses? (input number)
	Savings? (input number)
	Goal? (Save more, Get out of debt, Invest, Buy a home)
- Logic:
	Calculate savings rate
	Show financial health (Poor / Average / Strong)
	Give 2–3 personalized recommendations based on answers
- Dashboard:
	Show income vs expenses visually (simple bar or progress style)
	Show savings rate %
- Booking section:
	Name, email, preferred time, notes

Output: A single HTML file I can open in any browser — it should feel like a real fintech product, the intake should be smooth (one question at a time), calculations should update dynamically, and the UI should look polished enough to impress a client. Use the frontend-design skill and install it if you don't have it.

```