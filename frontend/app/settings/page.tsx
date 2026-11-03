"use client";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api, Profile } from "@/lib/api";

export default function Settings() {
  const [p, setP] = useState<Profile | null>(null);
  const [tt, setTt] = useState<{ configured: boolean; connected: boolean; mock_mode: boolean } | null>(null);
  const [msg, setMsg] = useState("");
  useEffect(() => {
    api<Profile>("/api/me").then(setP).catch((e) => setMsg(e.message));
    api("/api/tiktok/status").then(setTt).catch(() => {});
    const code = new URLSearchParams(window.location.search).get("code");
    if (code) api(`/api/tiktok/callback?code=${encodeURIComponent(code)}`, { method: "POST" })
      .then(() => { setMsg("TikTok connected"); return api("/api/tiktok/status").then(setTt); })
      .catch((e) => setMsg(e.message));
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!p) return;
    const { name, timezone, country, audience_age, posts_per_day } = p;
    try {
      setP(await api<Profile>("/api/me", { method: "PATCH", body: JSON.stringify({ name, timezone, country, audience_age, posts_per_day: Number(posts_per_day) }) }));
      setMsg("Saved");
    } catch (err) { setMsg((err as Error).message); }
  }
  async function connect() {
    try { window.location.href = (await api<{ url: string }>("/api/tiktok/auth-url")).url; }
    catch (err) { setMsg((err as Error).message); }
  }

  return (
    <Shell>
      <h2>Settings</h2>
      {msg && <p>{msg}</p>}
      {p && (
        <form className="card" onSubmit={save}>
          <label>Name<input value={p.name} onChange={(e) => setP({ ...p, name: e.target.value })} /></label>
          <label>Timezone (IANA, e.g. America/New_York)<input value={p.timezone} onChange={(e) => setP({ ...p, timezone: e.target.value })} /></label>
          <label>Country<input value={p.country} onChange={(e) => setP({ ...p, country: e.target.value })} /></label>
          <label>Main follower age group
            <select value={p.audience_age} onChange={(e) => setP({ ...p, audience_age: e.target.value })}>
              {["13-17", "18-24", "25-34", "35+"].map((a) => <option key={a}>{a}</option>)}
            </select>
          </label>
          <label>Posts per day<input type="number" min={1} max={6} value={p.posts_per_day} onChange={(e) => setP({ ...p, posts_per_day: Number(e.target.value) })} /></label>
          <button type="submit">Save</button>
        </form>
      )}
      <div className="card">
        <h3>TikTok</h3>
        {tt?.mock_mode && <p>TikTok API credentials are not configured: posting and analytics run in <b>mock mode</b>.</p>}
        <p>Status: {tt?.connected ? "connected" : "not connected"}</p>
        {tt?.configured && !tt.connected && <button onClick={connect}>Connect TikTok</button>}
      </div>
    </Shell>
  );
}
