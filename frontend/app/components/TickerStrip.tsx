"use client";
import { useEffect, useState, useCallback } from "react";
import { LiveQuote } from "../lib/types";
import { fetchLiveQuotes } from "../lib/api";

const SYMBOLS = [
  // US equities
  "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "NFLX",
  // Commodities
  "GLD", "SLV",
  // US indexes
  "SPY", "QQQ", "DIA",
  // Indian indexes
  "NIFTY50", "SENSEX",
  // Indian equities
  "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
];
const REFRESH_MS = 30_000;

function currencyPrefix(symbol: string) {
  if (symbol.endsWith(".NS") || symbol === "NIFTY50" || symbol === "SENSEX") return "₹";
  if (symbol === "NIFTY50" || symbol === "SENSEX") return "";
  return "$";
}

function Ticker({ q }: { q: LiveQuote }) {
  const up = q.change >= 0;
  const prefix = currencyPrefix(q.symbol);
  const displaySym = q.symbol.replace(".NS", "");
  return (
    <span className="inline-flex items-center gap-1.5 px-3 shrink-0">
      <span className="font-semibold text-white">{displaySym}</span>
      <span className="text-gray-200">{prefix}{q.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</span>
      <span className={up ? "text-emerald-400" : "text-red-400"}>
        {up ? "▲" : "▼"} {Math.abs(q.pct_change).toFixed(2)}%
      </span>
    </span>
  );
}

export default function TickerStrip() {
  const [quotes, setQuotes] = useState<LiveQuote[]>([]);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchLiveQuotes(SYMBOLS);
      setQuotes(data);
      setError(false);
    } catch { setError(true); }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  if (error) return null;
  if (!quotes.length) return <div className="h-8 bg-gray-950 animate-pulse" />;

  return (
    <div className="bg-gray-950 border-b border-gray-800 overflow-hidden h-8 flex items-center">
      <div className="flex animate-[ticker_40s_linear_infinite] whitespace-nowrap text-xs">
        {[...quotes, ...quotes].map((q, i) => <Ticker key={i} q={q} />)}
      </div>
    </div>
  );
}
