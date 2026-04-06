"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "./lib/auth";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import TickerStrip from "./components/TickerStrip";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [sidebarKey, setSidebarKey] = useState(0);
  const [ready, setReady] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) return null;

  function handleNewChat() {
    setSessionId(undefined);
  }

  function handleSessionCreated(id: string) {
    setSessionId(id);
    setSidebarKey((k) => k + 1);
  }

  return (
    <main className="flex flex-col h-screen" style={{ background: "#0a0a0f" }}>
      <Header />
      <TickerStrip />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          key={sidebarKey}
          currentSessionId={sessionId}
          onSessionSelect={setSessionId}
          onNewChat={handleNewChat}
        />
        <div className="flex-1 overflow-hidden">
          <ChatInterface sessionId={sessionId} onSessionCreated={handleSessionCreated} />
        </div>
      </div>
    </main>
  );
}
