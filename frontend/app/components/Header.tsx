"use client";
import { useRouter } from "next/navigation";
import { clearToken, getUser } from "../lib/auth";
import LLMSwitcher from "./LLMSwitcher";

export default function Header() {
  const router = useRouter();
  const user = getUser();

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="glass-panel border-b border-glass px-6 py-3 flex items-center gap-3 shrink-0">
      <h1 className="font-semibold text-lg tracking-tight text-white">MeshDefend</h1>
      <span className="text-secondary text-sm">Stock Analytics</span>
      <div className="ml-auto flex items-center gap-4">
        <LLMSwitcher />
        {user && (
          <span className="text-secondary text-xs hidden sm:block">{user.email}</span>
        )}
        <button
          onClick={logout}
          className="text-xs text-secondary hover:text-white transition-colors"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
