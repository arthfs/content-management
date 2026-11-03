"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api, fmt } from "@/lib/api";

interface Dash {
  counts: Record<string, number>; totals: Record<string, number>;
  top_videos: { video_id: number; title: string; platform: string; views: number; engagement_rate: number }[];
  upcoming: { id: number; title: string; scheduled_at: string }[];
  posted_today: number; daily_goal: number; platforms: Record<string, boolean>;
}
interface BestTimes { timezone: string; local_hours: number[]; slots: { utc: string; local: string }[] }

export default function Dashboard() {
  const [d, setD] = useState<Dash | null>(null);
  const [bt, setBt] = useState<BestTimes | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Dash>("/api/dashboard").then(setD).catch((e) => setError(e.message));
    api<BestTimes>("/api/schedule/best-times").then(setBt).catch(() => {});
  }, []);

  return (
    <Shell>
      <h2>Dashboard</h2>
      {error && <p className="error">{error}</p>}
      {d && (
        <>
          <div className="grid">
            {Object.entries(d.counts).map(([k, v]) => (
              <div className="card stat" key={k}><b>{v}</b>{k}</div>
            ))}
            <div className="card stat"><b>{d.posted_today}/{d.daily_goal}</b>posted today</div>
          </div>
          <div className="grid">
            {Object.entries(d.totals).map(([k, v]) => (
              <div className="card stat" key={k}><b>{v.toLocaleString()}</b>total {k}</div>
            ))}
          </div>
          <div className="card">
            <h3>Platforms</h3>
            {Object.entries(d.platforms).map(([k, on]) => (
              <span key={k} className="badge" style={{ marginRight: 8 }}>{k}: {on ? "active" : "coming soon"}</span>
            ))}
          </div>
          <div className="card">
            <h3>Top videos</h3>
            {d.top_videos.length === 0 && <p>No posted videos yet.</p>}
            {d.top_videos.map((v) => (
              <div className="row" key={v.video_id + v.platform}>
                <Link href={`/videos/${v.video_id}`}>{v.title}</Link>
                <span>{v.views.toLocaleString()} views · {v.engagement_rate}% eng.</span>
              </div>
            ))}
          </div>
          <div className="card">
            <h3>Upcoming</h3>
            {d.upcoming.length === 0 && <p>Nothing scheduled.</p>}
            {d.upcoming.map((v) => (
              <div className="row" key={v.id}><Link href={`/videos/${v.id}`}>{v.title}</Link><span>{fmt(v.scheduled_at)}</span></div>
            ))}
          </div>
        </>
      )}
      {bt && (
        <div className="card">
          <h3>Best times to post ({bt.timezone})</h3>
          <p>Daily sweet spots (local): {bt.local_hours.map((h) => `${h}:00`).join(", ")}</p>
          {bt.slots.slice(0, 4).map((s) => <div key={s.utc}>{fmt(s.utc)}</div>)}
        </div>
      )}
    </Shell>
  );
}
