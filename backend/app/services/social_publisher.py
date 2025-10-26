import os
import logging
import asyncio
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SocialPublisher:
    def __init__(self) -> None:
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
        self.telegram_default_chat = os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "").strip()
        self.ayrshare_api_key = os.getenv("AYRSHARE_API_KEY", "").strip()

    def enabled_channels(self) -> Dict[str, bool]:
        chans = {
            "slack": bool(self.slack_webhook),
            "discord": bool(self.discord_webhook),
            "telegram": bool(self.telegram_token),
        }
        if self.ayrshare_api_key:
            # Expose aggregator-backed platforms
            chans.update({
                "linkedin": True,
                "twitter": True,
                "x": True,
            })
        return chans

    async def _post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        timeout: float = 20.0,
        headers: Optional[Dict[str, str]] = None,
        attempts: int = 3,
    ) -> bool:
        import aiohttp
        last_err: Optional[str] = None
        for i in range(max(1, attempts)):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as resp:
                        if resp.status in (200, 201, 202, 204):
                            return True
                        text = await resp.text()
                        last_err = f"HTTP {resp.status}: {text[:200]}"
                        # bei 4xx (außer 429) nicht erneut versuchen
                        if resp.status < 500 and resp.status != 429:
                            logger.error(f"POST {url} failed (no retry): {last_err}")
                            return False
            except Exception as e:
                last_err = str(e)
            # Backoff, falls weiterer Versuch
            if i < attempts - 1:
                await asyncio.sleep(0.5 * (2 ** i))
        logger.error(f"POST {url} failed after {attempts} attempts: {last_err}")
        return False

    async def send_slack(self, text: str, attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not self.slack_webhook:
            return {"status": "skipped", "channel": "slack", "reason": "not_configured"}
        ok = await self._post_json(self.slack_webhook, {"text": text, "attachments": attachments or []}, timeout=20.0)
        return {"status": "sent" if ok else "error", "channel": "slack"}

    async def send_discord(self, message: str, title: Optional[str] = None) -> Dict[str, Any]:
        if not self.discord_webhook:
            return {"status": "skipped", "channel": "discord", "reason": "not_configured"}
        embed = {
            "title": title or "",
            "description": message,
        }
        ok = await self._post_json(self.discord_webhook, {"embeds": [embed]}, timeout=20.0)
        return {"status": "sent" if ok else "error", "channel": "discord"}

    async def send_telegram(self, text: str, chat_id: Optional[str] = None, parse_mode: Optional[str] = None) -> Dict[str, Any]:
        token = self.telegram_token
        if not token:
            return {"status": "skipped", "channel": "telegram", "reason": "not_configured"}
        cid = chat_id or self.telegram_default_chat
        if not cid:
            return {"status": "skipped", "channel": "telegram", "reason": "missing_chat_id"}
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload: Dict[str, Any] = {"chat_id": cid, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        ok = await self._post_json(url, payload, timeout=20.0)
        return {"status": "sent" if ok else "error", "channel": "telegram"}

    async def post(self, message: str, channels: Optional[List[str]] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        targets = set((channels or [k for k, v in self.enabled_channels().items() if v]))
        results: Dict[str, Any] = {}
        if "slack" in targets:
            results["slack"] = await self.send_slack(message)
        if "discord" in targets:
            results["discord"] = await self.send_discord(message)
        if "telegram" in targets:
            chat_id = (extra or {}).get("telegram_chat_id") if extra else None
            results["telegram"] = await self.send_telegram(message, chat_id=chat_id)
        # Aggregated via Ayrshare (optional)
        aggregator_platforms: List[str] = []
        if "linkedin" in targets:
            aggregator_platforms.append("linkedin")
        if "twitter" in targets or "x" in targets:
            aggregator_platforms.append("twitter")
        if aggregator_platforms and self.ayrshare_api_key:
            link = (extra or {}).get("link") if extra else None
            results["ayrshare"] = await self.send_ayrshare(message, platforms=aggregator_platforms, link=link)
        return {"ok": True, "results": results}

    async def send_ayrshare(self, message: str, platforms: List[str], link: Optional[str] = None) -> Dict[str, Any]:
        if not self.ayrshare_api_key:
            return {"status": "skipped", "channel": "ayrshare", "reason": "not_configured"}
        payload: Dict[str, Any] = {
            "post": message,
            "platforms": platforms,
        }
        if link:
            payload["link"] = link
        headers = {
            "Authorization": f"Bearer {self.ayrshare_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BlockForensics-SocialBot/1.0",
        }
        ok = await self._post_json(
            "https://app.ayrshare.com/api/post",
            payload,
            headers=headers,
            timeout=25.0,
            attempts=3,
        )
        return {"status": "sent" if ok else "error", "channel": "ayrshare"}


social_publisher = SocialPublisher()
