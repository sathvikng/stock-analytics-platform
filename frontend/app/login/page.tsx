"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { setToken, setUser } from "../lib/auth";
import { login, signup } from "../lib/api";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = isLogin
        ? await login(email, password)
        : await signup(email, password, displayName || undefined);
      setToken(data.access_token);
      setUser(data.user);
      router.push("/");
    } catch (err) {
      setError(String(err).replace("Error: ", ""));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "#0a0a0f" }}>
      <div className="glass-panel rounded-2xl p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-white mb-1">MeshDefend</h1>
        <p className="text-secondary text-sm mb-6">Stock Analytics Platform</p>

        <div className="flex gap-1 mb-6 glass-panel rounded-lg p-1">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${
              isLogin ? "bg-accent text-white" : "text-secondary hover:text-white"
            }`}
          >
            Sign in
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${
              !isLogin ? "bg-accent text-white" : "text-secondary hover:text-white"
            }`}
          >
            Sign up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {!isLogin && (
            <input
              type="text"
              placeholder="Display name (optional)"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="glass-input w-full rounded-lg px-3 py-2 text-sm"
            />
          )}
          <input
            type="email"
            placeholder="Email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="glass-input w-full rounded-lg px-3 py-2 text-sm"
          />
          <input
            type="password"
            placeholder="Password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="glass-input w-full rounded-lg px-3 py-2 text-sm"
          />
          {error && (
            <p className="text-red-400 text-xs">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full rounded-lg py-2 text-sm font-medium mt-1"
          >
            {loading ? "…" : isLogin ? "Sign in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
