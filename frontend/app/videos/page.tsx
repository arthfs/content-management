"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api, fmt, Video } from "@/lib/api";

export default function Videos() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [form, setForm] = useState({ title: "", caption: "", hashtags: "", video_url: "" });
  const [error, setError] = useState("");
  const load = useCallback(() => api<Video[]>("/api/videos").then(setVideos).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/api/videos", { method: "POST", body: JSON.stringify(form) });
      setForm({ title: "", caption: "", hashtags: "", video_url: "" });
      load();
    } catch (err) { setError((err as Error).message); }
  }
  const act = async (id: number, path: string) => {
    setError("");
    try { await api(`/api/videos/${id}/${path}`, { method: "POST", body: JSON.stringify({}) }); load(); }
    catch (err) { setError((err as Error).message); }
  };

  return (
    <Shell>
      <h2>Videos</h2>
      {error && <p className="error">{error}</p>}
      <form className="card" onSubmit={add}>
        <h3>New draft</h3>
        <input placeholder="Title" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <input placeholder="Public video URL (https://…)" value={form.video_url} onChange={(e) => setForm({ ...form, video_url: e.target.value })} />
        <textarea placeholder="Caption" value={form.caption} onChange={(e) => setForm({ ...form, caption: e.target.value })} />
        <input placeholder="#hashtags" value={form.hashtags} onChange={(e) => setForm({ ...form, hashtags: e.target.value })} />
        <button type="submit">Save draft</button>
      </form>
      {videos.map((v) => (
        <div className="card row" key={v.id}>
          <div>
            <Link href={`/videos/${v.id}`}>{v.title}</Link> <span className="badge">{v.status}</span>
            {v.scheduled_at && v.status === "scheduled" && <div>Scheduled: {fmt(v.scheduled_at)}</div>}
          </div>
          {v.status !== "posted" && (
            <div>
              <button className="secondary" onClick={() => act(v.id, "schedule")}>Schedule at best time</button>{" "}
              <button onClick={() => act(v.id, "publish")}>Post to TikTok now</button>
            </div>
          )}
        </div>
      ))}
    </Shell>
  );
}
