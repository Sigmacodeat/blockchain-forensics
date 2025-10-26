import os
import re
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from urllib.request import urlopen, Request  # nosec B310 (URLs controlled via env)
from urllib.error import URLError, HTTPError
from xml.etree import ElementTree as ET

from app.services.translation_service import translation_service

logger = logging.getLogger(__name__)

DEFAULT_SOURCES = {
    "chainalysis": "https://blog.chainalysis.com/feed/",
    "coindesk_policy": "https://www.coindesk.com/policy/rss/",
    "theblock_policy": "https://www.theblock.co/rss?category=policy-and-regulation",
    "elliptic": "https://www.elliptic.co/blog/rss.xml",
    "trm_labs": "https://www.trmlabs.com/blog/rss.xml",
}

DATA_DIR = Path(os.getcwd()) / "data" / "news_feeds"
DATA_DIR.mkdir(parents=True, exist_ok=True)
NEWS_FILE = DATA_DIR / "news.json"

KEYWORD_TAGS: List[Tuple[str, str]] = [
    (r"(?i)forensic|on[- ]chain analytics|blockchain analysis|cluster", "forensics"),
    (r"(?i)aml|anti[- ]money[- ]laundering|compliance|kyc|kyb", "aml"),
    (r"(?i)kyt|transaction monitoring|screening", "kyt"),
    (r"(?i)sanction|ofac|uk hmt|eu sanction|un sanction", "sanctions"),
    (r"(?i)mixer|tornado cash|coinjoin|privacy pool|railgun", "mixers"),
    (r"(?i)bridge|cross[- ]chain|wormhole|layerzero|stargate", "bridges"),
    (r"(?i)hack|exploit|breach|ransomware|phishing|scam", "incidents"),
    (r"(?i)vasp|travel rule", "travel_rule"),
]

TARGET_LANGS = [
    x.strip() for x in os.getenv("NEWS_TARGET_LANGS", "en,de,fr,es,it,pt,ar,zh,ja,ru").split(",") if x.strip()
]
DEFAULT_LANG = os.getenv("DEFAULT_LANGUAGE", "en")


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _parse_http_xml(url: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=20) as resp:  # nosec B310
            data = resp.read()
        root = ET.fromstring(data)
        # RSS 2.0: channel/item
        for node in root.findall(".//item"):
            title = (node.findtext("title") or "").strip()
            link = (node.findtext("link") or "").strip()
            desc = (node.findtext("description") or "").strip()
            pub = node.findtext("pubDate") or node.findtext("date") or ""
            try:
                published_at = datetime.strptime(pub[:25], "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                published_at = datetime.utcnow().replace(tzinfo=timezone.utc)
            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "summary": re.sub(r"<[^>]+>", " ", desc).strip(),
                    "published_at": published_at.isoformat(),
                })
        # Atom: entry
        if not items:
            for node in root.findall(".//{*}entry"):
                title = (node.findtext("{*}title") or "").strip()
                link_el = node.find("{*}link")
                link = link_el.get("href") if link_el is not None else ""
                summary = (node.findtext("{*}summary") or node.findtext("{*}content") or "").strip()
                pub = node.findtext("{*}updated") or node.findtext("{*}published") or ""
                try:
                    published_at = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except Exception:
                    published_at = datetime.utcnow().replace(tzinfo=timezone.utc)
                if title and link:
                    items.append({
                        "title": title,
                        "url": link,
                        "summary": re.sub(r"<[^>]+>", " ", summary).strip(),
                        "published_at": published_at.isoformat(),
                    })
    except (HTTPError, URLError, ET.ParseError) as e:
        logger.warning(f"News RSS fetch/parse failed for {url}: {e}")
    except Exception as e:
        logger.warning(f"News RSS unexpected error for {url}: {e}")
    return items


def _classify_tags(title: str, summary: str) -> List[str]:
    txt = f"{title}\n{summary}"
    tags: List[str] = []
    for pattern, tag in KEYWORD_TAGS:
        try:
            if re.search(pattern, txt):
                tags.append(tag)
        except Exception:
            continue
    # unique preserve order
    seen = set()
    result: List[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def _normalize_url(url: str) -> str:
    # Drop utm params for dedupe
    try:
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
        p = urlparse(url)
        q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith("utm_")]
        p2 = p._replace(query=urlencode(q))
        return urlunparse(p2)
    except Exception:
        return url


def _load_sources() -> Dict[str, Any]:
    raw = os.getenv("NEWS_FEEDS_URLS_JSON", "")
    if raw.strip():
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            logger.warning("NEWS_FEEDS_URLS_JSON invalid, using defaults")
    return DEFAULT_SOURCES


def _read_existing() -> List[Dict[str, Any]]:
    if NEWS_FILE.exists():
        try:
            return json.loads(NEWS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _write_all(items: List[Dict[str, Any]]) -> None:
    try:
        NEWS_FILE.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to write news store: {e}")


def get_news_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Return single news item by id (hash of normalized URL), or None."""
    try:
        items = _read_existing()
        for it in items:
            if str(it.get("id")) == str(item_id):
                return it
    except Exception:
        return None
    return None


async def run_once() -> Dict[str, Any]:
    """Fetch all sources once, dedupe, classify, persist."""
    sources = _load_sources()
    fetched: List[Dict[str, Any]] = []
    for name, urls in sources.items():
        url_list = urls if isinstance(urls, list) else [urls]
        for u in url_list:
            items = _parse_http_xml(u)
            for it in items:
                url_norm = _normalize_url(it.get("url", ""))
                it["id"] = _hash(url_norm)
                it["source"] = name
                it["url_norm"] = url_norm
                it["tags"] = _classify_tags(it.get("title", ""), it.get("summary", ""))
                it["lang"] = DEFAULT_LANG
                fetched.append(it)
    # Merge with existing
    existing = {row.get("id"): row for row in _read_existing()}
    for row in fetched:
        existing[row["id"]] = {**existing.get(row["id"], {}), **row}
    # Sort by published_at desc
    merged = list(existing.values())
    def _key(x):
        try:
            return datetime.fromisoformat(str(x.get("published_at", "")).replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()
    merged.sort(key=_key, reverse=True)
    _write_all(merged)
    return {"count": len(merged), "added": len(fetched)}


async def query_news(
    lang: str = DEFAULT_LANG,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    since_iso: Optional[str] = None,
) -> Dict[str, Any]:
    items = _read_existing()
    # Filters
    if source:
        items = [x for x in items if str(x.get("source")) == source]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    if since_iso:
        try:
            t = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
            items = [x for x in items if datetime.fromisoformat(str(x.get("published_at", "")).replace("Z", "+00:00")) >= t]
        except Exception:
            pass
    if q:
        qq = q.lower()
        def _match(x):
            return qq in str(x.get("title", "")).lower() or qq in str(x.get("summary", "")).lower()
        items = [x for x in items if _match(x)]

    items = items[: max(1, min(200, int(limit)))]

    # On-demand translation of title & summary
    out: List[Dict[str, Any]] = []
    for it in items:
        row = dict(it)
        if lang and lang != DEFAULT_LANG:
            row["title_translated"] = await translation_service.translate(row.get("title", ""), lang, source_lang=DEFAULT_LANG)
            row["summary_translated"] = await translation_service.translate(row.get("summary", ""), lang, source_lang=DEFAULT_LANG)
            row["lang"] = lang
        out.append(row)
    return {"items": out, "count": len(out)}


def generate_news_sitemap(base_url: str, max_items: int = 50) -> str:
    """Generate a minimal sitemap XML for latest news items."""
    items = _read_existing()[:max_items]
    # Build XML
    def _xml_escape(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    urls = []
    for it in items:
        loc = f"{base_url.rstrip('/')}/{DEFAULT_LANG}/news?u={_xml_escape(it.get('id',''))}"
        lastmod = it.get("published_at") or datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{_xml_escape(lastmod)}</lastmod></url>")
    body = "\n".join(urls)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        f"{body}\n"
        "</urlset>\n"
    )


def generate_google_news_sitemap(base_url: str, lang: str, max_items: int = 50) -> str:
    """Generate Google News compatible sitemap for items within last 48h.
    Uses news:news namespace with publication info.
    """
    try:
        from datetime import timedelta
    except Exception:
        timedelta = None  # type: ignore

    items = _read_existing()
    # Filter last 48h as per Google News guidelines
    filtered: List[Dict[str, Any]] = []
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    for it in items:
        try:
            t = datetime.fromisoformat(str(it.get("published_at", "")).replace("Z", "+00:00"))
        except Exception:
            t = now
        if timedelta is None or (now - t).total_seconds() <= 48 * 3600:
            filtered.append(it)
    # limit
    filtered = filtered[: max(1, min(1000, int(max_items)))]

    publication_name = os.getenv("NEWS_PUBLICATION_NAME", os.getenv("APP_NAME", "SIGMACODE News"))

    def _xml_escape(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    urls: List[str] = []
    for it in filtered:
        loc = f"{base_url.rstrip('/')}/{lang}/news?u={_xml_escape(it.get('id',''))}"
        title = _xml_escape(it.get("title") or "")
        # RFC3339/ISO8601
        lastmod = it.get("published_at") or now.isoformat()
        urls.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            "    <news:news>\n"
            "      <news:publication>\n"
            f"        <news:name>{_xml_escape(publication_name)}</news:name>\n"
            f"        <news:language>{_xml_escape(lang or 'en')}</news:language>\n"
            "      </news:publication>\n"
            f"      <news:publication_date>{_xml_escape(lastmod)}</news:publication_date>\n"
            f"      <news:title>{title}</news:title>\n"
            "    </news:news>\n"
            "  </url>"
        )
    body = "\n".join(urls)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:news=\"http://www.google.com/schemas/sitemap-news/0.9\">\n"
        f"{body}\n"
        "</urlset>\n"
    )
