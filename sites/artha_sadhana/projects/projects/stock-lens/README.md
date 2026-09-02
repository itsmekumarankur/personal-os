# Portfolio Lab

A 2-page HTML portfolio tracker for your Indian equity holdings — no build step, no server.

## Files
- `dashboard.html` — portfolio overview: ticker tape, invested vs current value, P&L, sector allocation, holdings table
- `analysis.html` — deep dive on one stock: P/E, P/B, EPS, 52-week range, a price chart with SMA20/SMA50, computed RSI(14), and research links (Screener.in, MoneyControl, Trendlyne, Google News, Economic Times)
- `config.js` — **edit this** with your API key and real holdings
- `app.js` / `styles.css` — shared logic and styling, no need to touch these

## Setup (2 minutes)
1. Get a free API key: https://www.alphavantage.co/support/#api-key
2. Open `config.js`, paste your key into `API_KEY`
3. Replace the sample `HOLDINGS` array with your real positions. Symbol format:
   - NSE stock → `"NSE:SYMBOL"` e.g. `"NSE:RELIANCE"`
   - BSE stock → `"BSE:CODE"` e.g. `"BSE:500325"`
4. Open `dashboard.html` in a browser (double-click works, or host on GitHub Pages like your Architects Lab site)

## Good to know
- Free Alpha Vantage tier = **25 requests/day, 5/minute**. That's why prices load on a manual "Refresh live prices" click, not automatically, and why each holding is fetched with a small delay between calls.
- Nothing is written to disk or browser storage — all fetched data lives in memory for that browser tab/session only. Refreshing the page re-fetches from scratch.
- `OVERVIEW` (fundamentals: P/E, P/B, EPS) has inconsistent coverage for NSE/BSE tickers on Alpha Vantage's free tier — when it's empty, use the Screener.in link on the analysis page instead, which has full Indian fundamentals for free.
- If you outgrow the 25/day limit, worth checking Twelve Data or a Zerodha Kite Connect key (paid) — the `fetchQuote` / `fetchDaily` / `fetchOverview` functions in `app.js` are isolated so swapping providers only touches those three functions.

## Ideas to extend
- Add a "Watchlist" section in `config.js` for stocks you don't own yet, reusing `analysis.html`
- Add a CSV export button on the dashboard for tax/LTCG record-keeping
- Wire a cron-less "last refreshed" note using a static JSON you regenerate nightly via a GitHub Action, if you want data without burning live API calls every visit
