# Prompt 1: Download the Data and Build the Dashboard (No Skill)

> **Instructor note:** This is the "before" version. No design skill active. Claude will fetch real stock data and build a functional but plain dashboard. The goal is a working UI that looks like a developer built it quickly — nothing polished.

Copy and paste the following into Claude Code:

```
Context: I want to build a stock portfolio dashboard as a single HTML file I can open in my browser.

Instruction: First, check if a file called stock_data.csv exists in the current folder. If it does not exist, run a Python script to download the latest stock prices using yfinance and save them to stock_data.csv. Then build a dashboard.html file from that data using plain HTML, CSS, and JavaScript. Do not use any design skill. Style it with basic CSS only — functional layout, default colors, nothing fancy.

Input:
- Stocks: AAPL, MSFT, GOOGL, AMZN, NVDA, JPM
- CSV columns: symbol, name, price, change, change_pct
- Install yfinance if needed: pip install yfinance

Output:
- stock_data.csv with real current prices
- dashboard.html showing:
  - Header with total portfolio value and overall daily change
  - A card for each stock with name, price, and daily change
  - Green tint for stocks that are up, red tint for stocks that are down
  - A bar chart comparing daily % change across all 6 stocks
  - Basic responsive layout
```

> **Instructor note:** Once done, open dashboard.html in a browser. It should show real prices but look plain and generic. Take a screenshot or keep the tab open — you will compare it side by side with the v2 version after Prompt 4.
