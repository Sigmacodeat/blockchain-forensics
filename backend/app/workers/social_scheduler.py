import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.news_service import query_news
from app.services.social_content import generate_news_post, build_shortlink
from app.services.social_publisher import social_publisher

logger = logging.getLogger(__name__)


class SocialSchedulerWorker:
    def __init__(self, interval_minutes: int = 120, channels: Optional[List[str]] = None) -> None:
        self.running: bool = False
        self.worker_name: str = "social_scheduler"
        self.interval_minutes = max(5, int(interval_minutes))
        default_channels = os.getenv("SOCIAL_DEFAULT_CHANNELS", "").strip()
        self.channels = channels or ([x.strip() for x in default_channels.split(",") if x.strip()] or ["telegram"]) 
        # State
        data_dir = Path(os.getcwd()) / "data" / "social_scheduler"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = data_dir / "state.json"
        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        try:
            if self.state_path.exists():
                return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"{self.worker_name}: failed to load state: {e}")
        return {"posted_ids": [], "last_ts": None}

    def _save_state(self) -> None:
        try:
            self.state_path.write_text(json.dumps(self.state, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"{self.worker_name}: failed to save state: {e}")

    async def _post_item(self, item: Dict[str, Any]) -> bool:
        try:
            lang = os.getenv("DEFAULT_LANGUAGE", "en")
            post = generate_news_post(item, lang)
            link = build_shortlink(item.get("url") or item.get("url_norm") or "", platform="social", campaign="news")
            msg = f"{post['message']}\n\n{link['public_url']}"
            extra = {
                "telegram_chat_id": os.getenv("TELEGRAM_DEFAULT_CHAT_ID") or os.getenv("SOCIAL_TELEGRAM_CHAT_ID") or None,
                "link": link["public_url"],
            }
            res = await social_publisher.post(msg, channels=self.channels, extra=extra)
            ok = bool(res.get("ok", True))  # post() returns {ok: True}
            return ok
        except Exception as e:
            logger.error(f"{self.worker_name}: post failed: {e}")
            return False

    async def run_once(self) -> int:
        """Fetch latest news and post items not yet posted. Returns number of posts."""
        out_count = 0
        try:
            # Fetch last 50 items, optionally filter by time if we stored last_ts
            res = await query_news(limit=50)
            items = res.get("items", []) if isinstance(res, dict) else []
            posted_ids: List[str] = list(self.state.get("posted_ids") or [])
            for it in items:
                iid = str(it.get("id"))
                if not iid or iid in posted_ids:
                    continue
                ok = await self._post_item(it)
                if ok:
                    posted_ids.append(iid)
                    out_count += 1
            # Trim state
            self.state["posted_ids"] = posted_ids[-500:]
            self.state["last_ts"] = datetime.now(timezone.utc).isoformat()
            self._save_state()
        except Exception as e:
            logger.error(f"{self.worker_name}: run_once error: {e}")
        return out_count

    async def run_loop(self) -> None:
        if self.running:
            return
        self.running = True
        logger.info(f"✅ {self.worker_name} started (interval={self.interval_minutes} min, channels={self.channels})")
        try:
            while self.running:
                await self.run_once()
                await asyncio.sleep(self.interval_minutes * 60)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"{self.worker_name}: loop error: {e}")
        finally:
            self.running = False
            logger.info(f"🛑 {self.worker_name} stopped")

    def stop(self) -> None:
        self.running = False


social_scheduler_worker = SocialSchedulerWorker(
    interval_minutes=int(os.getenv("SOCIAL_SCHEDULER_INTERVAL_MINUTES", "120") or 120)
)


async def start_social_scheduler_worker() -> None:
    await social_scheduler_worker.run_loop()


def stop_social_scheduler_worker() -> None:
    social_scheduler_worker.stop()
