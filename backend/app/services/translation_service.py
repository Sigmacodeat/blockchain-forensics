import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self) -> None:
        self.provider = (os.getenv("TRANSLATION_PROVIDER") or "none").strip().lower()
        self.deepl_key = os.getenv("DEEPL_API_KEY")
        self.deepl_api_base = os.getenv("DEEPL_API_BASE", "api.deepl.com").strip()
        self.google_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
        try:
            self.timeout = float(os.getenv("TRANSLATION_TIMEOUT_SECONDS", "15"))
        except Exception:
            self.timeout = 15.0

    async def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        text = text or ""
        if not text:
            return text
        if not target_lang:
            return text
        if source_lang and target_lang.lower() == source_lang.lower():
            return text
        # Provider selection with graceful fallback to passthrough
        try:
            if self.provider == "deepl" and self.deepl_key:
                out = await self._translate_deepl(text, target_lang, source_lang)
                if out and out != text:
                    return out
                if self.google_key:
                    out2 = await self._translate_google(text, target_lang, source_lang)
                    return out2 or text
                return text
            if self.provider == "google" and self.google_key:
                out = await self._translate_google(text, target_lang, source_lang)
                if out and out != text:
                    return out
                if self.deepl_key:
                    out2 = await self._translate_deepl(text, target_lang, source_lang)
                    return out2 or text
                return text
        except Exception as e:
            logger.warning(f"Translation fallback to passthrough due to error: {e}")
        return text

    async def _translate_deepl(self, text: str, target_lang: str, source_lang: Optional[str]) -> Optional[str]:
        try:
            import httpx  # type: ignore
        except Exception:
            return None
        if not self.deepl_key:
            return None
        api_host = self.deepl_api_base or "api.deepl.com"
        url = f"https://{api_host}/v2/translate"
        params = {
            "auth_key": self.deepl_key,
            "text": text,
            "target_lang": target_lang.upper(),
        }
        if source_lang:
            params["source_lang"] = source_lang.upper()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(url, data=params)
                if r.status_code == 200:
                    data = r.json()
                    tr = (data.get("translations") or [{}])[0].get("text")
                    if isinstance(tr, str):
                        return tr
        except Exception as e:
            logger.warning(f"DeepL translate failed: {e}")
        return None

    async def _translate_google(self, text: str, target_lang: str, source_lang: Optional[str]) -> Optional[str]:
        try:
            import httpx  # type: ignore
        except Exception:
            return None
        if not self.google_key:
            return None
        # Google Cloud Translate v2 REST
        url = f"https://translation.googleapis.com/language/translate/v2?key={self.google_key}"
        payload = {
            "q": text,
            "target": target_lang.lower(),
        }
        if source_lang:
            payload["source"] = source_lang.lower()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    tr = (((data.get("data") or {}).get("translations") or [{}])[0]).get("translatedText")
                    if isinstance(tr, str):
                        return tr
        except Exception as e:
            logger.warning(f"Google translate failed: {e}")
        return None

translation_service = TranslationService()
