"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import PostPanel from "@/components/PostPanel";
import { api, fmt, Video } from "@/lib/api";

export default function Videos() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [form, setForm] = useState({ title: "", caption: "", hashtags: "" });
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0);
  const [error, setError] = useState("");
  const load = useCallback(() => api<Video[]>("/api/videos").then(setVideos).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); }, [load]);

  const upload = (id: number, f: File) => {
    const body = new FormData();
    body.append("file", f);
    return api(`/api/videos/${id}/file`, { method: "POST", body });
  };

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const v = await api<Video>("/api/videos", { method: "POST", body: JSON.stringify(form) });
      if (file) {
        try { await upload(v.id, file); }
        catch (err) { setError("Draft saved, but the upload failed: " + (err as Error).message); }
      }
      setForm({ title: "", caption: "", hashtags: "" });
      setFile(null);
      setFileKey((k) => k + 1);
      load();
    } catch (err) { setError((err as Error).message); }
  }
  async function attach(id: number, f: File | undefined) {
    if (!f) return;
    setError("");
    try { await upload(id, f); load(); }
    catch (err) { setError((err as Error).message); }
  }
  const [panel, setPanel] = useState<{ id: number; mode: "publish" | "schedule" } | null>(null);
  const refreshStatus = async (id: number) => {
    setError("");
    try { await api(`/api/videos/${id}/publish-status`); load(); }
    catch (err) { setError((err as Error).message); }
  };

  return (
    <Shell>
      <h2>Videos</h2>
      {error && <p className="error">{error}</p>}
      <form className="card" onSubmit={add}>
        <h3>New draft</h3>
        <input placeholder="Title" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <label>Video file (mp4, mov or webm)
          <input key={fileKey} type="file" accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </label>
        <textarea placeholder="Caption" value={form.caption} onChange={(e) => setForm({ ...form, caption: e.target.value })} />
        <input placeholder="#hashtags" value={form.hashtags} onChange={(e) => setForm({ ...form, hashtags: e.target.value })} />
        <button type="submit">Save draft</button>
      </form>
      {videos.map((v) => (
        <div key={v.id}>
        <div className="card row">
          <div>
            <Link href={`/videos/${v.id}`}>{v.title}</Link> <span className="badge">{v.status}</span>{" "}
            <span className="badge">{v.has_file ? "file attached" : "no file"}</span>
            {v.scheduled_at && v.status === "scheduled" && <div>Scheduled: {fmt(v.scheduled_at)}</div>}
            {v.publish_status && v.status !== "failed" && <div>TikTok status: {v.publish_status}{" "}
              {v.publish_status !== "PUBLISH_COMPLETE" && <button className="secondary" onClick={() => refreshStatus(v.id)}>Refresh</button>}
            </div>}
            {v.fail_reason && <div className="error">{v.fail_reason}</div>}
          </div>
          {v.status !== "posted" && (
            <div>
              <label>{v.has_file ? "Replace video" : "Attach video"}
                <input type="file" accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm"
                  onChange={(e) => attach(v.id, e.target.files?.[0])} />
              </label>{" "}
              <button className="secondary" onClick={() => setPanel({ id: v.id, mode: "schedule" })}>Schedule at best time</button>{" "}
              <button onClick={() => setPanel({ id: v.id, mode: "publish" })}>Post to TikTok now</button>
            </div>
          )}
        </div>
        {panel?.id === v.id && (
          <PostPanel video={v} mode={panel.mode} onCancel={() => setPanel(null)}
            onDone={() => { setPanel(null); load(); }} />
        )}
        </div>
      ))}
    </Shell>
  );
}
