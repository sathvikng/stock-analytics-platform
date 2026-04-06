"use client";
import { useState, useRef, useEffect } from "react";
import { Message, StepData, ChatResponse, StreamEvent } from "../lib/types";
import { streamChat, getSessionMessages } from "../lib/api";
import DataTable from "./DataTable";
import ChartView from "./ChartView";
import StreamingMessage from "./StreamingMessage";

interface Props {
  sessionId?: string;
  onSessionCreated?: (id: string) => void;
}

export default function ChatInterface({ sessionId, onSessionCreated }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<StepData[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, steps]);

  useEffect(() => {
    if (!sessionId) { setMessages([]); return; }
    getSessionMessages(sessionId).then((msgs) => {
      setMessages(msgs.map((m) => ({
        id: m.id,
        role: m.role as "user" | "assistant",
        content: m.content,
        response: m.response_json ?? undefined,
      })));
    }).catch(() => {});
  }, [sessionId]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const query = input;
    setMessages((m) => [...m, { id: Date.now().toString(), role: "user", content: query }]);
    setInput("");
    setLoading(true);
    setSteps([]);

    let resultData: ChatResponse | undefined;
    try {
      for await (const event of streamChat(query, sessionId) as AsyncIterable<StreamEvent>) {
        if (event.event === "step") {
          const step = event.data as StepData;
          setSteps((prev) => {
            const idx = prev.findIndex((s) => s.step === step.step);
            if (idx >= 0) { const u = [...prev]; u[idx] = step; return u; }
            return [...prev, step];
          });
        } else if (event.event === "result") {
          resultData = event.data as ChatResponse;
          if (resultData.session_id && onSessionCreated) {
            onSessionCreated(resultData.session_id);
          }
        } else if (event.event === "error") {
          throw new Error((event.data as { message: string }).message);
        }
      }
      setMessages((m) => [...m, {
        id: Date.now().toString() + "_a",
        role: "assistant",
        content: resultData?.intent_summary ?? "Done",
        response: resultData,
      }]);
    } catch (e) {
      setMessages((m) => [...m, {
        id: Date.now().toString() + "_e",
        role: "assistant",
        content: `Error: ${String(e).replace("Error: ", "")}`,
      }]);
    } finally {
      setLoading(false);
      setSteps([]);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && !loading && (
          <p className="text-secondary text-center mt-20 text-sm">
            Ask anything about stock data — e.g. &quot;Show AAPL closing prices for the last 30 days&quot;
          </p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-3xl w-full rounded-xl px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-accent text-white ml-8"
                  : "glass-panel text-primary"
              }`}
            >
              <p>{msg.content}</p>
              {msg.response && (
                <div className="mt-3 space-y-3">
                  {(msg.response.type === "table" || msg.response.type === "both") && (
                    <DataTable data={msg.response.data} />
                  )}
                  {msg.response.chart &&
                    (msg.response.type === "chart" || msg.response.type === "both") && (
                      <ChartView data={msg.response.data} config={msg.response.chart} />
                    )}
                  {msg.response.sql_used && (
                    <details className="text-xs text-secondary">
                      <summary className="cursor-pointer hover:text-primary transition-colors">SQL used</summary>
                      <pre className="mt-1 rounded p-2 overflow-x-auto text-xs" style={{ background: "rgba(0,0,0,0.4)" }}>
                        {msg.response.sql_used}
                      </pre>
                    </details>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="glass-panel rounded-xl px-4 py-3 max-w-xs">
              <StreamingMessage steps={steps} isComplete={false} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-glass p-4 flex gap-2 shrink-0">
        <input
          className="glass-input flex-1 rounded-lg px-4 py-2 text-sm"
          placeholder="Ask about stocks…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          className="btn-primary rounded-lg px-4 py-2 text-sm font-medium"
        >
          Send
        </button>
      </div>
    </div>
  );
}
