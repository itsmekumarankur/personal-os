// ============================================================
// PORTFOLIO LAB — shared logic
// All fetched data lives in memory only (window.__cache) and is
// lost on refresh by design — re-click "Refresh" to re-fetch.
// ============================================================

const AV_BASE = "https://www.alphavantage.co/query";
window.__cache = window.__cache || { quotes: {}, overview: {}, daily: {} };

function fmtINR(n){
  if (n === null || n === undefined || isNaN(n)) return "—";
  return "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}
function fmtPct(n){
  if (n === null || n === undefined || isNaN(n)) return "—";
  const s = n >= 0 ? "+" : "";
  return s + n.toFixed(2) + "%";
}
function pillClass(n){
  if (n === null || n === undefined || isNaN(n)) return "flat";
  return n > 0 ? "up" : n < 0 ? "down" : "flat";
}

async function avFetch(params){
  if (!API_KEY || API_KEY === "YOUR_ALPHA_VANTAGE_KEY"){
    throw new Error("NO_API_KEY");
  }
  const qs = new URLSearchParams({ ...params, apikey: API_KEY });
  const res = await fetch(`${AV_BASE}?${qs.toString()}`);
  const data = await res.json();
  if (data.Note || data.Information){
    throw new Error("RATE_LIMIT");
  }
  return data;
}

async function fetchQuote(symbol){
  if (window.__cache.quotes[symbol]) return window.__cache.quotes[symbol];
  const data = await avFetch({ function: "GLOBAL_QUOTE", symbol });
  const q = data["Global Quote"] || {};
  const parsed = {
    price: parseFloat(q["05. price"]),
    change: parseFloat(q["09. change"]),
    changePct: parseFloat((q["10. change percent"] || "").replace("%","")),
    prevClose: parseFloat(q["08. previous close"]),
  };
  window.__cache.quotes[symbol] = parsed;
  return parsed;
}

async function fetchOverview(symbol){
  if (window.__cache.overview[symbol]) return window.__cache.overview[symbol];
  const data = await avFetch({ function: "OVERVIEW", symbol });
  window.__cache.overview[symbol] = data && Object.keys(data).length ? data : null;
  return window.__cache.overview[symbol];
}

async function fetchDaily(symbol){
  if (window.__cache.daily[symbol]) return window.__cache.daily[symbol];
  const data = await avFetch({ function: "TIME_SERIES_DAILY", symbol, outputsize: "compact" });
  const series = data["Time Series (Daily)"];
  if (!series) { window.__cache.daily[symbol] = null; return null; }
  const rows = Object.entries(series)
    .map(([date, v]) => ({ date, close: parseFloat(v["4. close"]) }))
    .sort((a,b) => a.date.localeCompare(b.date));
  window.__cache.daily[symbol] = rows;
  return rows;
}

// throttle sequential calls so we don't blow the 5/min free-tier limit
async function withThrottle(items, fn, delayMs = 800){
  const out = [];
  for (const item of items){
    try { out.push(await fn(item)); }
    catch(e){ out.push({ error: e.message }); }
    await new Promise(r => setTimeout(r, delayMs));
  }
  return out;
}

function researchLinks(symbol, name){
  const bare = symbol.split(":").pop();
  const q = encodeURIComponent(name || bare);
  return [
    { label: "Screener.in", url: `https://www.screener.in/company/${bare}/` },
    { label: "MoneyControl", url: `https://www.google.com/search?q=site:moneycontrol.com+${q}` },
    { label: "Trendlyne", url: `https://trendlyne.com/stock/search/?q=${q}` },
    { label: "Google News", url: `https://news.google.com/search?q=${q}%20stock&hl=en-IN` },
    { label: "Economic Times", url: `https://economictimes.indiatimes.com/searchresult.cms?query=${q}` },
  ];
}

function renderTicker(rows){
  const wrap = document.getElementById("ticker-track");
  if (!wrap) return;
  const build = () => rows.map(r => {
    const cls = r.changePct > 0 ? "up" : r.changePct < 0 ? "down" : "flat";
    const arrow = r.changePct > 0 ? "▲" : r.changePct < 0 ? "▼" : "•";
    return `<span class="ticker-item"><span class="sym">${r.symbol.split(":").pop()}</span>
      <span class="chg ${cls}">${arrow} ${isNaN(r.changePct) ? "—" : r.changePct.toFixed(2) + "%"}</span></span>`;
  }).join("");
  wrap.innerHTML = build() + build(); // duplicate for seamless loop
}
