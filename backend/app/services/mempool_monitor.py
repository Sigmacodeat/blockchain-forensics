"""
Mempool Monitor Service
- Streams mempool-like events (best-effort / simulated if RPC doesn't support pending pool)
- Broadcasts via WebSocket: app.api.v1.websockets.mempool.broadcast_mempool_tx/alert
"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class MempoolMonitor:
    """Lightweight mempool monitor with best-effort simulation.

    In production, integrate chain-specific pending pools (geth/parity filters, TronGrid events, Solana subscriptions).
    For now, we simulate by sampling newest blocks and emitting lightweight events to the WS for UX validation.
    """

    def __init__(self, chains: Optional[List[str]] = None, interval_seconds: float = 2.0) -> None:
        self._chains = chains or ["ethereum", "polygon", "tron"]
        self._interval = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Mempool monitor started for chains={self._chains} interval={self._interval}s")

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            try:
                self._task.cancel()
            except Exception:
                pass
        logger.info("Mempool monitor stopped")

    async def _run(self) -> None:
        # Lazy imports to avoid hard deps in tests
        from app.api.v1.websockets.mempool import broadcast_mempool_tx, broadcast_mempool_alert  # type: ignore
        from app.services.multi_chain import ChainAdapterFactory  # type: ignore

        factory = ChainAdapterFactory()

        # If SIMULATE mode is enabled, emit synthetic demo events
        simulate_only = os.getenv("MEMPOOL_SIMULATE_ONLY", "1") == "1"
        min_value_usd = float(os.getenv("MEMPOOL_ALERT_MIN_VALUE_USD", "10000"))

        # Simple price map (best-effort)
        price_usd = {
            "ethereum": 2000.0,
            "polygon": 1.0,
            "tron": 0.1,
        }

        while self._running:
            try:
                for chain in list(self._chains):
                    adapter = factory.get_adapter(chain)
                    if not adapter:
                        continue
                    # Simulate one 'pending' tx per chain per interval
                    try:
                        # Get a recent block for timestamp context (no mempool here)
                        # Fallback event data
                        tx_hash = f"{chain}_pending_{int(asyncio.get_event_loop().time()*1000)}"
                        frm = "0xdeadbeef" if chain != "tron" else "TXYZDEADBEEF111111111111111111111"
                        to = "0xfeedface" if chain != "tron" else "TPQWERTY1234567890ABCDEFGHJKLMNPQ"
                        value_native = 0.25 if chain == "ethereum" else (1000 if chain == "tron" else 500)
                        event: Dict[str, Any] = {
                            "chain": chain,
                            "tx_hash": tx_hash,
                            "from": frm,
                            "to": to,
                            "value": value_native,
                            "heuristics": {
                                "type": "simulated",
                                "notes": "Replace with real mempool integration on capable nodes",
                            },
                        }
                        # Typology & SOAR (best-effort, ENV-gated)
                        try:
                            if os.getenv("ENABLE_MEMPOOL_TYPOS", "1") == "1":
                                from app.services.typology_engine import typology_engine as _typo
                                # Build minimal event for typologies (align keys with DSL)
                                _evt = {
                                    "address": to,
                                    "value_usd": value_native * price_usd.get(chain, 1.0),
                                    "labels": [],
                                    "metadata": {
                                        "from_address": frm,
                                        "to_address": to,
                                        "chain": chain,
                                        "tx_hash": tx_hash,
                                    },
                                }
                                _matches = _typo.evaluate(_evt)
                                if _matches:
                                    event["typology_matches"] = _matches
                                    # Optional SOAR
                                    if os.getenv("ENABLE_MEMPOOL_SOAR", "1") == "1":
                                        try:
                                            from app.services.soar_engine import soar_engine as _soar
                                            _soar.run(_evt)
                                        except Exception:
                                            pass
                        except Exception as _te:
                            logger.debug(f"Mempool typology/soar error: {_te}")

                        await broadcast_mempool_tx(event)

                        # Alert heuristic: large value
                        usd = value_native * price_usd.get(chain, 1.0)
                        if usd >= min_value_usd:
                            alert_payload: Dict[str, Any] = {
                                "rule": "large_pending_value",
                                "severity": "medium" if usd < min_value_usd*5 else "high",
                                "tx": event,
                                "usd_value": usd,
                            }
                            if event.get("typology_matches"):
                                alert_payload["typology_matches"] = event["typology_matches"]
                            await broadcast_mempool_alert(alert_payload)
                    except Exception as e:
                        logger.debug(f"Mempool iter error on {chain}: {e}")

                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Mempool monitor loop error: {e}")
                await asyncio.sleep(self._interval)


# Global instance helpers
_mempool_monitor: Optional[MempoolMonitor] = None


def start_mempool_monitor(chains: Optional[List[str]] = None, interval_seconds: float = 2.0) -> MempoolMonitor:
    global _mempool_monitor
    if _mempool_monitor is None:
        _mempool_monitor = MempoolMonitor(chains=chains, interval_seconds=interval_seconds)
    asyncio.create_task(_mempool_monitor.start())
    return _mempool_monitor


def stop_mempool_monitor() -> None:
    global _mempool_monitor
    if _mempool_monitor is not None:
        _mempool_monitor.stop()
        _mempool_monitor = None
