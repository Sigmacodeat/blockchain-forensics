import os
from typing import Dict, Any, Optional, Tuple

from app.services.link_tracker import link_tracker


def _shorten(text: str, max_len: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max(0, max_len - 1)].rstrip() + "…"


def _public_short_base() -> str:
    base = os.getenv("SHORTLINK_PUBLIC_BASE", "").strip()
    if base:
        return base.rstrip("/") + "/"
    backend = os.getenv("BACKEND_URL", "").strip()
    if backend:
        return backend.rstrip("/") + "/api/v1/links/s/"
    # Fallback to relative API path
    return "/api/v1/links/s/"


def build_shortlink(target_url: str, platform: str, campaign: str = "news", content_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Build a tracked short link for a target URL and platform using LinkTracker.
    Returns dict with keys: tracking_id, slug, public_url.
    """
    try:
        res = link_tracker.create_tracking_link(
            target_url=target_url,
            source_platform=platform,
            source_username=None,
            campaign=campaign,
            custom_slug=None,
        )
        slug = res.get("short_url", "").split("/")[-1] or (res.get("tracking_id") or "")[-8:]
        public_url = target_url  # Use original URL for reliability until shortlink storage is wired
        return {
            "tracking_id": res.get("tracking_id"),
            "slug": slug,
            "public_url": public_url,
        }
    except Exception:
        return {"tracking_id": None, "slug": None, "public_url": target_url}


def generate_news_post(item: Dict[str, Any], lang: Optional[str] = None, max_len: int = 260) -> Dict[str, Any]:
    """
    Create a concise social post for a news item.
    Returns: { message, hashtags }
    """
    title = (item.get("title_translated") or item.get("title") or "").strip()
    summary = (item.get("summary_translated") or item.get("summary") or "").strip()
    tags = item.get("tags") or []
    # Build hashtags (max 3)
    hash_tags = [f"#{t.replace(' ', '')}" for t in (tags[:3])]
    headline = _shorten(title, 120) if title else "News"
    body = _shorten(summary, max(40, max_len - len(headline) - 10)) if summary else ""
    parts = [f"🧠 {headline}"]
    if body:
        parts.append(body)
    if hash_tags:
        parts.append(" ".join(hash_tags))
    message = "\n\n".join(parts)
    return {"message": message, "hashtags": hash_tags}
