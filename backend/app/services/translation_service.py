import os
import hashlib
import json
from typing import Optional, Dict
from time import time

# Optional dependency: we'll import functions locally in methods to avoid global NameError

from app.db.redis_client import redis_client


class TranslationService:
    """Minimaler Übersetzungsservice mit Caching und TEST_MODE-Fallback."""

    def __init__(self) -> None:
        self.provider = os.getenv("TRANSLATION_PROVIDER", "none").lower().strip()
        self.deepl_key = os.getenv("DEEPL_API_KEY", "").strip()
        self.google_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "").strip()
        self.test_mode = bool(os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"))
        # Konfiguration
        self.timeout = int(os.getenv("TRANSLATION_TIMEOUT_SECONDS", "15") or "15")
        self.retries = max(0, int(os.getenv("TRANSLATION_RETRIES", "2") or "2"))
        # DeepL: api.deepl.com (paid) oder api-free.deepl.com (free)
        self.deepl_base = (os.getenv("DEEPL_API_BASE", "api.deepl.com") or "api.deepl.com").strip()
        self._local_cache: Dict[str, str] = {}

    def _cache_key(self, text: str, source: Optional[str], target: str) -> str:
        raw = f"{source or ''}|{target}|{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Übersetzt Text best-effort. In TEST_MODE wird der Originaltext zurückgegeben."""
        if not text or not target_lang:
            return text
        if self.test_mode or self.provider == "none":
            return text

        key = self._cache_key(text, source_lang, target_lang)
        cached = await redis_client.cache_get(f"translation:{key}")
        if cached:
            return str(cached)
        if key in self._local_cache:
            return self._local_cache[key]

        translated = await self._do_translate(text, target_lang, source_lang)
        # Cache 24h
        try:
            await redis_client.cache_set(f"translation:{key}", translated, ttl=86400)
        except Exception:
            pass
        self._local_cache[key] = translated
        return translated

    async def _do_translate(self, text: str, target_lang: str, source_lang: Optional[str]) -> str:
        # Primary provider based on config
        if self.provider == "deepl" and self.deepl_key:
            primary = await self._translate_deepl(text, target_lang, source_lang)
            # Fallback to Google if available and no improvement
            if primary == text and self.google_key:
                secondary = await self._translate_google(text, target_lang, source_lang)
                return secondary
            return primary
        if self.provider == "google" and self.google_key:
            primary = await self._translate_google(text, target_lang, source_lang)
            # Fallback to DeepL if available and no improvement
            if primary == text and self.deepl_key:
                secondary = await self._translate_deepl(text, target_lang, source_lang)
                return secondary
            return primary
        # No provider configured -> passthrough
        return text

    async def _translate_deepl(self, text: str, target_lang: str, source_lang: Optional[str]) -> str:
        try:
            from urllib.parse import urlencode
            from urllib.request import Request, urlopen  # nosec B310

            endpoint = f"https://{self.deepl_base}/v2/translate"
            params = {
                "auth_key": self.deepl_key,
                "text": text,
                "target_lang": target_lang.upper(),
            }
            if source_lang:
                params["source_lang"] = source_lang.upper()
            data = urlencode(params).encode("utf-8")
            last_err = None
            for _ in range(self.retries + 1):
                try:
                    req = Request(endpoint, data=data, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Sigmacode-Translator/1.0"})
                    with urlopen(req, timeout=self.timeout) as resp:  # nosec B310
                        body = resp.read().decode("utf-8", errors="ignore")
                        obj = json.loads(body)
                        if isinstance(obj, dict) and obj.get("translations"):
                            t0 = obj["translations"][0]
                            return str(t0.get("text") or text)
                except Exception as e:
                    last_err = e
                    continue
        except Exception:
            pass
        return text

    async def _translate_google(self, text: str, target_lang: str, source_lang: Optional[str]) -> str:
        """Minimal Google Translate REST call (v2) using API key.
        Note: For production, use official client; here we keep a light optional dependency.
        """
        try:
            from urllib.parse import urlencode
            from urllib.request import urlopen, Request  # nosec B310
            params = {
                "q": text,
                "target": target_lang.lower(),
                "key": self.google_key,
            }
            if source_lang:
                params["source"] = source_lang.lower()
            url = "https://translation.googleapis.com/language/translate/v2"
            body = urlencode(params).encode("utf-8")
            last_err = None
            for _ in range(self.retries + 1):
                try:
                    req = Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Sigmacode-Translator/1.0"})
                    with urlopen(req, timeout=self.timeout) as resp:  # nosec B310
                        txt = resp.read().decode("utf-8", errors="ignore")
                    obj = json.loads(txt)
                    t = (
                        obj.get("data", {})
                          .get("translations", [{}])[0]
                          .get("translatedText")
                    )
                    return str(t or text)
                except Exception as e:
                    last_err = e
                    continue
            return text
        except Exception:
            return text


translation_service = TranslationService()
