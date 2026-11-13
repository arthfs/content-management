"use client";
import { useEffect, useState } from "react";
import { api, CreatorInfo, PublishOptions, Video } from "@/lib/api";

const PRIVACY_LABELS: Record<string, string> = {
  PUBLIC_TO_EVERYONE: "Everyone",
  MUTUAL_FOLLOW_FRIENDS: "Friends",
  FOLLOWER_OF_CREATOR: "Followers",
  SELF_ONLY: "Only me",
};

const EMPTY: PublishOptions = {
  privacy_level: "", allow_comment: false, allow_duet: false, allow_stitch: false,
  commercial_content: false, brand_organic: false, brand_content: false, consent: false,
};

// "Post to TikTok" panel following TikTok's content sharing guidelines:
// fresh creator info, no pre-selected privacy/interactions, disclosure, and explicit consent.
export default function PostPanel({ video, mode, onDone, onCancel }: {
  video: Video; mode: "publish" | "schedule"; onDone: () => void; onCancel: () => void;
}) {
  const [creator, setCreator] = useState<CreatorInfo | null>(null);
  const [opts, setOpts] = useState<PublishOptions>(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<CreatorInfo>("/api/tiktok/creator-info").then(setCreator).catch((e) => setError(e.message));
  }, []);

  const set = (patch: Partial<PublishOptions>) => setOpts((o) => ({ ...o, ...patch }));
  const branded = opts.commercial_content && opts.brand_content;
  const label = branded ? "Paid partnership" : opts.commercial_content && opts.brand_organic ? "Promotional content" : "";
  const disclosureMissing = opts.commercial_content && !opts.brand_organic && !opts.brand_content;
  const ready = !!creator && !!opts.privacy_level && opts.consent && !disclosureMissing && !busy;

  async function submit() {
    setBusy(true);
    setError("");
    try {
      const body = mode === "publish" ? opts : { options: opts };
      const r = await api<Video>(`/api/videos/${video.id}/${mode}`, { method: "POST", body: JSON.stringify(body) });
      if (r.status === "failed") setError(r.fail_reason || "TikTok rejected the post");
      else onDone();
    } catch (e) { setError((e as Error).message); }
    setBusy(false);
  }

  return (
    <div className="card">
      <h4>{mode === "publish" ? "Post to TikTok" : "Schedule on TikTok"}</h4>
      {error && <p className="error">{error}</p>}
      {!creator ? <p>Loading TikTok account…</p> : (
        <>
          <p>Posting to: <b>{creator.creator_nickname}</b>{creator.mock && " (mock mode: nothing is sent to TikTok)"}</p>
          <p><b>{video.title}</b><br />{video.caption} {video.hashtags}</p>
          <label>Who can view this video
            <select value={opts.privacy_level} onChange={(e) => set({ privacy_level: e.target.value })}>
              <option value="" disabled>Select…</option>
              {creator.privacy_level_options.map((p) => (
                <option key={p} value={p} disabled={p === "SELF_ONLY" && branded}
                  title={p === "SELF_ONLY" && branded ? "Branded content visibility cannot be set to private." : ""}>
                  {PRIVACY_LABELS[p] ?? p}
                </option>
              ))}
            </select>
          </label>
          <div>
            <label><input type="checkbox" checked={opts.allow_comment} disabled={creator.comment_disabled}
              onChange={(e) => set({ allow_comment: e.target.checked })} /> Allow comments</label>{" "}
            <label><input type="checkbox" checked={opts.allow_duet} disabled={creator.duet_disabled}
              onChange={(e) => set({ allow_duet: e.target.checked })} /> Allow Duet</label>{" "}
            <label><input type="checkbox" checked={opts.allow_stitch} disabled={creator.stitch_disabled}
              onChange={(e) => set({ allow_stitch: e.target.checked })} /> Allow Stitch</label>
          </div>
          <label><input type="checkbox" checked={opts.commercial_content}
            onChange={(e) => set({ commercial_content: e.target.checked, brand_organic: false, brand_content: false })} />
            {" "}This video promotes myself, a brand, product or service</label>
          {opts.commercial_content && (
            <div>
              <label><input type="checkbox" checked={opts.brand_organic}
                onChange={(e) => set({ brand_organic: e.target.checked })} /> Your brand</label>{" "}
              <label><input type="checkbox" checked={opts.brand_content}
                onChange={(e) => set({
                  brand_content: e.target.checked,
                  privacy_level: e.target.checked && opts.privacy_level === "SELF_ONLY" ? "" : opts.privacy_level,
                })} /> Branded content</label>
              {disclosureMissing && <p className="error">You need to indicate if your content promotes yourself, a third party, or both.</p>}
              {label && <p>Your video will be labeled as &ldquo;{label}&rdquo;.</p>}
            </div>
          )}
          <label><input type="checkbox" checked={opts.consent} onChange={(e) => set({ consent: e.target.checked })} />{" "}
            By posting, you agree to TikTok&apos;s{" "}
            {branded && <><a href="https://www.tiktok.com/legal/page/global/bc-policy/en" target="_blank" rel="noreferrer">Branded Content Policy</a> and </>}
            <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en" target="_blank" rel="noreferrer">Music Usage Confirmation</a>.
          </label>
          <p><small>After posting, it may take a few minutes for the video to finish processing and show on your profile.</small></p>
        </>
      )}
      <button disabled={!ready} onClick={submit}>{mode === "publish" ? "Post" : "Schedule"}</button>{" "}
      <button className="secondary" onClick={onCancel}>Cancel</button>
    </div>
  );
}
