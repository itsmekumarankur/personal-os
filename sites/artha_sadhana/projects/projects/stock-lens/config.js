// ============================================================
// CONFIG — this is the only file you should need to edit
// ============================================================

// 1. Get a free API key: https://www.alphavantage.co/support/#api-key
//    Free tier = 25 requests/day, 5/minute. That's why prices only
//    refresh when you click "Refresh live prices" — not on every load.
const API_KEY = "YOUR_ALPHA_VANTAGE_KEY";

// 2. List your holdings here. Symbol format Alpha Vantage expects
//    for Indian exchanges:
//      NSE stock  -> "NSE:SYMBOL"   e.g. "NSE:RELIANCE"
//      BSE stock  -> "BSE:CODE"     e.g. "BSE:500325"
//    (Sample data below — replace with your actual portfolio.)
const HOLDINGS = [
  { symbol: "NSE:RELIANCE",  name: "Reliance Industries",       sector: "Energy",  qty: 25, buyPrice: 2450.00, buyDate: "2023-04-12" },
  { symbol: "NSE:TCS",       name: "Tata Consultancy Services", sector: "IT",      qty: 10, buyPrice: 3550.00, buyDate: "2023-06-02" },
  { symbol: "NSE:HDFCBANK",  name: "HDFC Bank",                 sector: "Banking", qty: 30, buyPrice: 1580.00, buyDate: "2023-08-15" },
  { symbol: "NSE:INFY",      name: "Infosys",                   sector: "IT",      qty: 20, buyPrice: 1420.00, buyDate: "2024-01-10" },
  { symbol: "NSE:ICICIBANK", name: "ICICI Bank",                sector: "Banking", qty: 22, buyPrice: 980.00,  buyDate: "2024-02-20" },
];
