"use client";
import { useState, useEffect, useRef } from "react";
import { getLLMConfig, setLLMConfig } from "../lib/api";
import { LLMConfig } from "../lib/types";

export default function LLMSwitcher() {
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getLLMConfig().then(setConfig).catch(() => {});
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function select(provider: string, model: string) {
    await setLLMConfig(provider, model).catch(() => {});
    setConfig((c) => (c ? { ...c, provider, model } : c));
    setOpen(false);
  }

  if (!config) return null;
  const current = config.available_models.find(
    (m) => m.provider === config.provider && m.model === config.model
  );

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="glass-pill text-xs text-secondary hover:text-white flex items-center gap-1.5"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
        {current?.label ?? config.model}
      </button>
      {open && (
        <div className="absolute right-0 top-8 rounded-lg w-52 z-50 py-1 shadow-2xl border border-white/10" style={{background: "#1a1a2e"}}>
          {config.available_models.map((m) => (
            <button
              key={`${m.provider}/${m.model}`}
              onClick={() => select(m.provider, m.model)}
              className={`w-full text-left px-3 py-2 text-xs hover:bg-white/10 transition-colors ${
                m.provider === config.provider && m.model === config.model
                  ? "text-accent font-medium"
                  : "text-white/80"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
