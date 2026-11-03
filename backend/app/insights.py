"""Performance analysis and Gemini-powered suggestions."""
import httpx

from .config import settings


def engagement_rate(m: dict) -> float:
    views = m.get("views") or 0
    if not views:
        return 0.0
    return round((m.get("likes", 0) + m.get("comments", 0) + m.get("shares", 0)) / views * 100, 2)


def rule_based_suggestions(m: dict) -> list[str]:
    tips: list[str] = []
    er = engagement_rate(m)
    if (m.get("views") or 0) < 1000:
        tips.append("Low reach: use a stronger hook in the first 2 seconds and 3-5 niche + trending hashtags.")
    if er < 4:
        tips.append("Engagement is under 4%: end with a question or call-to-action to drive comments and shares.")
    elif er > 10:
        tips.append("Engagement is excellent: make a follow-up or series based on this video.")
    if m.get("completion_rate", 1) < 0.4:
        tips.append("Viewers drop off early: tighten the pacing and cut the intro.")
    if (m.get("shares", 0) or 0) < (m.get("views") or 1) * 0.005:
        tips.append("Few shares: add relatable or useful moments people want to send to friends.")
    return tips or ["Solid performance. Keep posting at your best times and test small variations."]


def gemini_suggestions(video_title: str, caption: str, platform: str, m: dict) -> tuple[list[str], str]:
    """Returns (suggestions, source). Falls back to rules if Gemini is unavailable."""
    if not settings.gemini_api_key:
        return rule_based_suggestions(m), "rules"
    prompt = (
        f"You are a short-form video growth coach. A {platform} video titled '{video_title}' "
        f"with caption '{caption}' has these metrics: {m}. Engagement rate: {engagement_rate(m)}%. "
        "Give 3-5 concise, actionable suggestions to improve future performance. "
        "Return one suggestion per line, no numbering or markdown."
    )
    try:
        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
            headers={"x-goog-api-key": settings.gemini_api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        lines = [ln.strip("-*• \t") for ln in text.splitlines() if ln.strip()]
        if lines:
            return lines[:5], "gemini"
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        pass
    return rule_based_suggestions(m), "rules"
