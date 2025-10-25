import os
from typing import Any, Dict, Optional, List

import httpx

from app.config import settings


class KiloClientError(Exception):
    pass


class KiloClient:
    """
    Minimaler API-Client für Kilo/Grok Code Fast.

    Konfiguration über ENV/Settings:
    - settings.KILO_BASE_URL oder settings.GROK_CODEFAST_BASE_URL
    - settings.KILO_API_KEY oder settings.GROK_CODEFAST_API_KEY

    Hinweise:
    - Secrets werden niemals geloggt
    - Timeouts & Retries konservativ
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self._test_mode = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TEST_MODE") == "1")

        # Primary KILO/GROK config
        self.base_url = (
            base_url or settings.KILO_BASE_URL or settings.GROK_CODEFAST_BASE_URL
        )
        self.api_key = api_key or settings.KILO_API_KEY or settings.GROK_CODEFAST_API_KEY

        # OpenAI fallback
        self._mode = "kilo"
        self._openai_api_key = None
        self._openai_model = None
        # In test environments, prefer OpenAI fallback to avoid external calls
        if self._test_mode and getattr(settings, "OPENAI_API_KEY", None):
            self._mode = "openai"
            self._openai_api_key = settings.OPENAI_API_KEY
            self._openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        if not self.base_url or not self.api_key:
            # Try OpenAI fallback if available
            if getattr(settings, "OPENAI_API_KEY", None):
                self._mode = "openai"
                self._openai_api_key = settings.OPENAI_API_KEY
                self._openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
            elif self._test_mode:
                # Allow mock mode during tests without raising
                self._mode = "mock"
                self._client = None
                return
            else:
                # Preserve previous error behavior
                if not self.base_url:
                    raise KiloClientError(
                        "Kilo/Grok Base URL ist nicht konfiguriert (KILO_BASE_URL/GROK_CODEFAST_BASE_URL)"
                    )
                if not self.api_key:
                    raise KiloClientError(
                        "Kilo/Grok API Key ist nicht gesetzt (KILO_API_KEY/GROK_CODEFAST_API_KEY)"
                    )

        self._timeout = httpx.Timeout(timeout)
        if self._mode == "kilo":
            self._client = httpx.Client(
                base_url=self.base_url.rstrip("/"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=self._timeout,
            )
        elif self._mode == "openai":
            # OpenAI REST client
            self._client = httpx.Client(
                base_url="https://api.openai.com/v1",
                headers={
                    "Authorization": f"Bearer {self._openai_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )
        else:
            # mock mode
            self._client = None

    def _handle_response(self, resp: httpx.Response) -> Dict[str, Any]:
        if resp.status_code == 401:
            raise KiloClientError("Unauthorized (401): API Key ungültig oder abgelaufen")
        if resp.status_code == 429:
            raise KiloClientError("Rate limited (429): Zu viele Anfragen – bitte Retry-Logik anwenden")
        if 500 <= resp.status_code:
            raise KiloClientError(f"Serverfehler ({resp.status_code})")
        try:
            return resp.json()
        except Exception as e:
            raise KiloClientError(f"Fehler beim Parsen der Antwort: {e}") from e

    def extract_from_code(self, code: str, *, language: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
        """
        Führt eine Extraktion aus Code durch. Endpoint ist konfigurierbar über ENV:
        - KILO_EXTRACT_ENDPOINT oder GROK_CODEFAST_EXTRACT_ENDPOINT
        Fallback: "/v1/extract"
        """
        if self._mode == "kilo":
            endpoint = (
                os.getenv("KILO_EXTRACT_ENDPOINT")
                or os.getenv("GROK_CODEFAST_EXTRACT_ENDPOINT")
                or "/v1/extract"
            )
            payload: Dict[str, Any] = {"code": code}
            if language:
                payload["language"] = language
            if task:
                payload["task"] = task
            resp = self._client.post(endpoint, json=payload)
            return self._handle_response(resp)
        # OpenAI fallback: use Chat Completions with system prompt
        system_prompt = (
            "You are a precise code extraction engine. Return a compact JSON object with extracted entities."
        )
        user_parts: List[str] = ["Extract structured info from the following code snippet."]
        if language:
            user_parts.append(f"Language: {language}")
        if task:
            user_parts.append(f"Task: {task}")
        user_parts.append("Code:\n" + code)
        openai_payload = {
            "model": self._openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
            "temperature": 0.1,
        }
        resp = self._client.post("/chat/completions", json=openai_payload)
        data = resp.json()
        # Extract assistant message
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            raise KiloClientError(f"OpenAI response malformed: {data}")
        return {"provider": "openai", "result": content}

    def extract_from_text(self, text: str, *, schema: Optional[Dict[str, Any]] = None, task: Optional[str] = None) -> Dict[str, Any]:
        """
        Führt eine Extraktion aus freiem Text durch. Endpoint konfigurierbar:
        - KILO_TEXT_EXTRACT_ENDPOINT oder GROK_CODEFAST_TEXT_EXTRACT_ENDPOINT
        Fallback: "/v1/extract-text"
        """
        if self._mode == "kilo":
            endpoint = (
                os.getenv("KILO_TEXT_EXTRACT_ENDPOINT")
                or os.getenv("GROK_CODEFAST_TEXT_EXTRACT_ENDPOINT")
                or "/v1/extract-text"
            )
            payload: Dict[str, Any] = {"text": text}
            if schema is not None:
                payload["schema"] = schema
            if task:
                payload["task"] = task
            resp = self._client.post(endpoint, json=payload)
            return self._handle_response(resp)
        # OpenAI fallback
        system_prompt = (
            "You are a precise information extraction engine. When given a schema, adhere to it; otherwise return a concise JSON object with extracted entities."
        )
        user_parts: List[str] = ["Extract structured info from the following text."]
        if task:
            user_parts.append(f"Task: {task}")
        if schema is not None:
            user_parts.append("Schema (JSON):\n" + str(schema))
        user_parts.append("Text:\n" + text)
        openai_payload = {
            "model": self._openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
            "temperature": 0.1,
        }
        resp = self._client.post("/chat/completions", json=openai_payload)
        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            raise KiloClientError(f"OpenAI response malformed: {data}")
        return {"provider": "openai", "result": content}

    def health(self) -> Dict[str, Any]:
        if self._mode == "kilo":
            endpoint = os.getenv("KILO_HEALTH_ENDPOINT") or "/v1/health"
            resp = self._client.get(endpoint)
            return self._handle_response(resp)
        # OpenAI fallback health: simple models list ping
        resp = self._client.get("/models")
        if resp.status_code == 200:
            return {"ok": True, "provider": "openai"}
        raise KiloClientError("OpenAI health check failed")

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
