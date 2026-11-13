const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
// Login is optional: mirror the backend's AUTH_REQUIRED flag (default off = single local user).
export const AUTH_REQUIRED = process.env.NEXT_PUBLIC_AUTH_REQUIRED === "true";

export type Metrics = Record<string, number>;
export interface Post { id: number; platform: string; posted_at: string; metrics: Metrics }
export interface Video {
  id: number; title: string; caption: string; hashtags: string; video_url: string; has_file: boolean;
  status: "draft" | "scheduled" | "posted" | "failed"; scheduled_at: string | null;
  publish_status: string | null; fail_reason: string | null;
  created_at: string; posts: Post[];
}
export interface CreatorInfo {
  creator_nickname: string; creator_username: string; privacy_level_options: string[];
  comment_disabled: boolean; duet_disabled: boolean; stitch_disabled: boolean;
  max_video_post_duration_sec: number; mock?: boolean;
}
export interface PublishOptions {
  privacy_level: string; allow_comment: boolean; allow_duet: boolean; allow_stitch: boolean;
  commercial_content: boolean; brand_organic: boolean; brand_content: boolean; consent: boolean;
}
export interface Profile {
  id: number; email: string; name: string; timezone: string; country: string;
  audience_age: string; posts_per_day: number; tiktok_connected: boolean;
}

export const getToken = () => (typeof window === "undefined" ? null : localStorage.getItem("token"));
export const setToken = (t: string | null) =>
  t ? localStorage.setItem("token", t) : localStorage.removeItem("token");

export async function api<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(init.headers as Record<string, string>) };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  if (init.body && typeof init.body === "string") headers["Content-Type"] = "application/json";
  const res = await fetch(API + path, { ...init, headers });
  if (res.status === 401 && AUTH_REQUIRED && typeof window !== "undefined" && !path.startsWith("/api/auth")) {
    setToken(null);
    window.location.href = "/login";
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const d = body.detail;
    throw new Error(typeof d === "string" ? d : "Request failed (" + res.status + ")");
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export async function login(email: string, password: string) {
  const res = await api<{ access_token: string }>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }) as unknown as BodyInit,
  });
  setToken(res.access_token);
}

export async function register(email: string, password: string, name: string) {
  const res = await api<{ access_token: string }>("/api/auth/register", {
    method: "POST", body: JSON.stringify({ email, password, name }),
  });
  setToken(res.access_token);
}

export const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleString() : "—");
