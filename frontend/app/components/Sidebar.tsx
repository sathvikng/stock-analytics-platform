"use client";
import { useState, useEffect } from "react";
import { getSessions } from "../lib/api";
import { Session } from "../lib/types";

interface Props {
  currentSessionId?: string;
  onSessionSelect: (id: string) => void;
  onNewChat: () => void;
}

export default function Sidebar({ currentSessionId, onSessionSelect, onNewChat }: Props) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    getSessions().then(setSessions).catch(() => {});
  }, []);

  if (collapsed) {
    return (
      <div className="glass-panel border-r border-glass flex flex-col items-center py-4 shrink-0" style={{ width: "40px" }}>
        <button
          onClick={() => setCollapsed(false)}
          className="text-secondary hover:text-white text-lg leading-none"
          title="Expand sidebar"
        >
          ›
        </button>
      </div>
    );
  }

  return (
    <aside
      className="glass-panel border-r border-glass flex flex-col shrink-0"
      style={{ width: "280px" }}
    >
      <div className="px-4 py-3 flex items-center justify-between border-b border-glass">
        <span className="text-sm font-medium text-white">History</span>
        <div className="flex items-center gap-3">
          <button
            onClick={onNewChat}
            className="text-xs text-accent hover:text-white transition-colors"
          >
            + New
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="text-secondary hover:text-white text-lg leading-none"
            title="Collapse sidebar"
          >
            ‹
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto py-1">
        {sessions.length === 0 && (
          <p className="text-xs text-secondary text-center mt-8 px-4">No conversations yet</p>
        )}
        {sessions.map((s) => (
          <button
            key={s.id}
            onClick={() => onSessionSelect(s.id)}
            className={`w-full text-left px-4 py-2.5 hover:bg-white/5 transition-colors border-l-2 ${
              s.id === currentSessionId
                ? "bg-white/8 border-accent"
                : "border-transparent"
            }`}
          >
            <div className="text-sm text-white truncate">{s.title}</div>
            <div className="text-xs text-secondary mt-0.5">
              {new Date(s.updated_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
              {" · "}
              {s.message_count} msg{s.message_count !== 1 ? "s" : ""}
            </div>
          </button>
        ))}
      </div>
    </aside>
  );
}
