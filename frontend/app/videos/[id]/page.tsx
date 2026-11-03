"use client";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api, fmt } from "@/lib/api";

interface Analytics {
  title: string; platform: string; posted_at: string; metrics: Record<string, number>;
  engagement_rate: number; suggestions: string[]; suggestions_source: string;
}

export default function VideoAnalytics() {
  const { id } = useParams<{ id: string }>();
  const [a, setA] = useState<Analytics | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Analytics>(`/api/videos/${id}/analytics?platform=tiktok`).then(setA).catch((e) => setError(e.message));
  }, [id]);

  return (
    <Shell>
      <h2>{a?.title ?? "Video"}</h2>
      {error && <p className="error">{error}</p>}
      {a && (
        <>
          <p>Platform: <span className="badge">{a.platform}</span> · Posted {fmt(a.posted_at)}</p>
          <div className="grid">
            {Object.entries(a.metrics).map(([k, v]) => (
              <div className="card stat" key={k}><b>{v.toLocaleString()}</b>{k.replace(/_/g, " ")}</div>
            ))}
            <div className="card stat"><b>{a.engagement_rate}%</b>engagement rate</div>
          </div>
          <div className="card">
            <h3>Suggestions <small>({a.suggestions_source === "gemini" ? "Gemini" : "rule-based"})</small></h3>
            <ul>{a.suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul>
          </div>
        </>
      )}
    </Shell>
  );
}
