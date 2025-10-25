"""
NewsCase Service
================

Leichter Service zum Erstellen/Verwalten von NewsCases (slug-basierte Watchlists)
und Live-Tracking von Adressen. Minimal-invasive Persistenz als JSON in data/news_cases/.

Features:
- Create/Get/List/Update/Delete NewsCases (slug, name, addresses)
- Periodischer Watcher pro Slug (pollt chain adapters, entdeckt neue TXs)
- KYT-Analyse (best-effort) für EVM-TXs
- WebSocket-Integration via subscribe()/publish()

Hinweis: Für MVP ohne DB-Migrationen ausgelegt. Später substituierbar durch SQL.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque
from datetime import datetime

from app.services.multi_chain import ChainAdapterFactory
from app.services.kyt_engine import kyt_engine, Transaction as KYTTransaction
try:
    from app.observability.metrics import NEWSCASE_EVENTS_TOTAL, NEWSCASE_SUBSCRIPTIONS, NEWSCASE_WATCHERS
except Exception:  # pragma: no cover
    NEWSCASE_EVENTS_TOTAL = None  # type: ignore
    NEWSCASE_SUBSCRIPTIONS = None  # type: ignore
    NEWSCASE_WATCHERS = None  # type: ignore

logger = logging.getLogger(__name__)
DATA_DIR = Path(os.getcwd()) / "data" / "news_cases"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class WatchedAddress:
    chain: str
    address: str


@dataclass
class NewsCase:
    slug: str
    name: str
    description: Optional[str] = None
    addresses: List[WatchedAddress] = field(default_factory=list)
    auto_trace: bool = False
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "addresses": [asdict(a) for a in self.addresses],
            "auto_trace": self.auto_trace,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "NewsCase":
        addrs = [WatchedAddress(**a) for a in d.get("addresses", [])]
        return NewsCase(
            slug=d["slug"],
            name=d.get("name", d["slug"]),
            description=d.get("description"),
            addresses=addrs,
            auto_trace=bool(d.get("auto_trace", False)),
            created_at=d.get("created_at") or datetime.utcnow().timestamp(),
            updated_at=d.get("updated_at") or datetime.utcnow().timestamp(),
        )


class NewsCaseService:
    def __init__(self) -> None:
        self._cases: Dict[str, NewsCase] = {}
        self._seen: Dict[str, Dict[Tuple[str, str], Set[str]]] = {}
        # seen[slug][(chain,address)] = { tx_hash, ... }
        self._queues: Dict[str, Set[asyncio.Queue]] = {}
        self._watch_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._factory = ChainAdapterFactory()
        # Event backlog per slug
        try:
            self._backlog_size = max(10, int(os.getenv("NEWSCASE_BACKLOG_SIZE", "200")))
        except Exception:
            self._backlog_size = 200
        self._backlog: Dict[str, deque] = {}

    # ------------------ Persistence ------------------
    def _case_file(self, slug: str) -> Path:
        return DATA_DIR / f"{slug}.json"

    async def _load_case(self, slug: str) -> Optional[NewsCase]:
        fp = self._case_file(slug)
        if not fp.exists():
            return None
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            case = NewsCase.from_dict(d)
            self._cases[slug] = case
            return case
        except Exception as e:
            logger.error("Failed to load news case %s: %s", slug, e)
            return None

    async def _save_case(self, case: NewsCase) -> None:
        fp = self._case_file(case.slug)
        try:
            fp.write_text(json.dumps(case.to_dict(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to save news case %s: %s", case.slug, e)

    # ------------------ CRUD ------------------
    @staticmethod
    def _validate_slug(slug: str) -> bool:
        import re
        return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}[a-z0-9]", slug))

    async def create(self, slug: str, name: str, addresses: List[Dict[str, str]], description: Optional[str] = None, auto_trace: bool = False) -> NewsCase:
        if not self._validate_slug(slug):
            raise ValueError("invalid slug; allowed: a-z0-9 and dash, 3-64 chars, no leading/trailing dash")
        if slug in self._cases or self._case_file(slug).exists():
            raise ValueError("slug already exists")
        addrs = [WatchedAddress(chain=a["chain"].lower(), address=a["address"]) for a in addresses]
        case = NewsCase(slug=slug, name=name or slug, description=description, addresses=addrs, auto_trace=bool(auto_trace))
        self._cases[slug] = case
        await self._save_case(case)
        return case

    async def get(self, slug: str) -> Optional[NewsCase]:
        case = self._cases.get(slug)
        if case is None:
            case = await self._load_case(slug)
        return case

    async def list(self) -> List[NewsCase]:
        # Lazy load from disk for safety
        for fp in DATA_DIR.glob("*.json"):
            slug = fp.stem
            if slug not in self._cases:
                await self._load_case(slug)
        return list(self._cases.values())

    async def update(self, slug: str, name: Optional[str] = None, description: Optional[str] = None, addresses: Optional[List[Dict[str, str]]] = None, auto_trace: Optional[bool] = None) -> NewsCase:
        case = await self.get(slug)
        if not case:
            raise ValueError("news case not found")
        if name is not None:
            case.name = name
        if description is not None:
            case.description = description
        if addresses is not None:
            case.addresses = [WatchedAddress(chain=a["chain"].lower(), address=a["address"]) for a in addresses]
            # Reset seen when address list changes
            self._seen.pop(slug, None)
        if auto_trace is not None:
            case.auto_trace = bool(auto_trace)
        case.updated_at = datetime.utcnow().timestamp()
        await self._save_case(case)
        # Kick watcher if running
        await self._ensure_watch(slug)
        return case

    async def delete(self, slug: str) -> None:
        case = await self.get(slug)
        if not case:
            return
        self._cases.pop(slug, None)
        self._seen.pop(slug, None)
        # stop watcher
        await self._stop_watch(slug)
        try:
            self._case_file(slug).unlink(missing_ok=True)
        except Exception:
            pass

    # ------------------ Subscribe/Broadcast ------------------
    def subscribe(self, slug: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.setdefault(slug, set()).add(q)
        try:
            if NEWSCASE_SUBSCRIPTIONS is not None:
                NEWSCASE_SUBSCRIPTIONS.inc()
        except Exception:
            pass
        return q

    async def _auto_trace(self, hint: Dict[str, Any]) -> None:
        """Best-effort Auto-Trace für gefundene Events.
        Nutzt vereinfachten Tracer-Flow; in TEST_MODE oder ohne Neo4j nur no-op.
        """
        try:
            from app.tracing.models import TraceRequest, TaintModel, TraceDirection
            from app.tracing.tracer import TransactionTracer
            try:
                from app.db.neo4j_client import neo4j_client
                tracer = TransactionTracer(db_client=neo4j_client)
            except Exception:
                return
            req = TraceRequest(
                source_address=str(hint.get("source_address") or ""),
                direction=TraceDirection.FORWARD,
                max_depth=int(hint.get("max_depth") or 3),
                max_nodes=200,
                taint_model=TaintModel.PROPORTIONAL,
                min_taint_threshold=0.1,
                start_timestamp=None,
                end_timestamp=None,
                enable_native=True,
                enable_token=True,
                enable_bridge=True,
                enable_utxo=True,
                native_decay=1.0,
                token_decay=1.0,
                bridge_decay=0.9,
                utxo_decay=1.0,
            )
            await tracer.trace(req)
        except Exception as e:
            logger.debug("_auto_trace failed: %s", e)

    def unsubscribe(self, slug: str, q: asyncio.Queue) -> None:
        try:
            qs = self._queues.get(slug)
            if qs:
                qs.discard(q)
                if not qs:
                    self._queues.pop(slug, None)
            try:
                if NEWSCASE_SUBSCRIPTIONS is not None:
                    NEWSCASE_SUBSCRIPTIONS.dec()
            except Exception:
                pass
        except Exception:
            pass

    async def _broadcast(self, slug: str, payload: Dict[str, Any]) -> None:
        # Append to backlog first
        try:
            bl = self._backlog.get(slug)
            if bl is None:
                bl = deque(maxlen=self._backlog_size)
                self._backlog[slug] = bl
            bl.append(payload)
        except Exception:
            pass
        for q in list(self._queues.get(slug, set())):
            try:
                await q.put(payload)
            except Exception as e:
                logger.debug("queue put failed for %s: %s", slug, e)
        # metrics
        try:
            if NEWSCASE_EVENTS_TOTAL is not None:
                NEWSCASE_EVENTS_TOTAL.labels(type=str(payload.get("type") or "unknown")).inc()
        except Exception:
            pass

    # ------------------ Snapshot & Status ------------------
    async def snapshot(self, slug: str) -> Dict[str, Any]:
        case = await self.get(slug)
        if not case:
            raise ValueError("news case not found")
        result: Dict[str, Any] = {
            "slug": case.slug,
            "name": case.name,
            "description": case.description,
            "auto_trace": case.auto_trace,
            "addresses": [],
            "generated_at": datetime.utcnow().timestamp(),
        }
        for a in case.addresses:
            try:
                adapter = self._factory.adapters.get(a.chain) or self._ensure_adapter(a.chain)
                balance = await adapter.get_address_balance(a.address)
            except Exception as e:
                logger.debug("balance error %s/%s: %s", a.chain, a.address, e)
                balance = None
            latest_tx = None
            try:
                adapter = self._factory.adapters.get(a.chain) or self._ensure_adapter(a.chain)
                txs = await adapter.get_address_transactions(a.address, limit=1)
                latest_tx = txs[0] if txs else None
            except Exception as e:
                logger.debug("tx error %s/%s: %s", a.chain, a.address, e)
            result["addresses"].append({
                "chain": a.chain,
                "address": a.address,
                "balance": balance,
                "latest_tx": latest_tx,
            })
        return result

    def _ensure_adapter(self, chain: str):
        # Build or return cached adapter
        try:
            adapter = self._factory.adapters.get(chain)
            if adapter is None:
                info = self._factory.chain_registry.get(chain)
                if not info:
                    raise ValueError(f"unsupported chain: {chain}")
                # Map chain type to adapter class (simplified: use EthereumAdapter for EVM)
                from app.services.multi_chain import ChainType, EthereumAdapter, BitcoinAdapter, SolanaAdapter
                if info.chain_type.name.lower() == ChainType.EVM.value:
                    adapter = EthereumAdapter(info)
                elif info.chain_type.name.lower() == ChainType.UTXO.value:
                    adapter = BitcoinAdapter(info)
                elif info.chain_type.name.lower() == ChainType.SVM.value:
                    adapter = SolanaAdapter(info)
                else:
                    adapter = EthereumAdapter(info)
                self._factory.adapters[chain] = adapter
            return adapter
        except Exception as e:
            logger.error("failed to ensure adapter for %s: %s", chain, e)
            raise

    # ------------------ Watchers ------------------
    async def _ensure_watch(self, slug: str) -> None:
        # Start watcher for slug if subscribers or if not running yet
        if slug in self._watch_tasks and not self._watch_tasks[slug].done():
            return
        task = asyncio.create_task(self._watch_loop(slug))
        self._watch_tasks[slug] = task
        try:
            if NEWSCASE_WATCHERS is not None:
                NEWSCASE_WATCHERS.set(len([t for t in self._watch_tasks.values() if not t.done()]))
        except Exception:
            pass

    async def _stop_watch(self, slug: str) -> None:
        t = self._watch_tasks.get(slug)
        if t and not t.done():
            t.cancel()
            try:
                await asyncio.sleep(0)
            except Exception:
                pass
            self._watch_tasks.pop(slug, None)
        try:
            if NEWSCASE_WATCHERS is not None:
                NEWSCASE_WATCHERS.set(len([t for t in self._watch_tasks.values() if not t.done()]))
        except Exception:
            pass

    async def _watch_loop(self, slug: str) -> None:
        interval = float(os.getenv("NEWSCASE_WATCH_INTERVAL", "10"))
        # Initialize seen map
        self._seen.setdefault(slug, {})
        while True:
            try:
                case = await self.get(slug)
                if not case:
                    return
                # If no subscribers, still run at lower frequency
                has_subscribers = bool(self._queues.get(slug))
                if not has_subscribers and os.getenv("NEWSCASE_PAUSE_WHEN_NO_CLIENT", "1") == "1":
                    await asyncio.sleep(interval)
                    continue

                # Per address scan
                for a in case.addresses:
                    key = (a.chain, a.address)
                    self._seen[slug].setdefault(key, set())
                    try:
                        adapter = self._factory.adapters.get(a.chain) or self._ensure_adapter(a.chain)
                        txs = await adapter.get_address_transactions(a.address, limit=5)
                    except Exception as e:
                        logger.debug("scan error %s/%s: %s", a.chain, a.address, e)
                        txs = []

                    for tx in txs:
                        tx_hash = tx.get("tx_hash") or tx.get("txid") or tx.get("tx_signature") or tx.get("hash")
                        if not tx_hash or tx_hash in self._seen[slug][key]:
                            continue
                        self._seen[slug][key].add(tx_hash)
                        # Normalize minimal TX view
                        # Build trace hint (source = watched address)
                        trace_hint = {
                            "source_address": a.address,
                            "chain": a.chain,
                            "direction": "forward",
                            "max_depth": 3,
                        }
                        event = {
                            "type": "news_case.tx",
                            "slug": slug,
                            "chain": a.chain,
                            "address": a.address,
                            "tx": tx,
                            "trace_hint": trace_hint,
                            "timestamp": datetime.utcnow().timestamp(),
                        }
                        await self._broadcast(slug, event)
                        # KYT analysis (best-effort) for EVM-like tx
                        try:
                            value_eth = float(tx.get("value") or 0)
                            from_addr = tx.get("from_address") or a.address
                            to_addr = tx.get("to_address") or ""
                            block_number = int(tx.get("block_number") or tx.get("block_height") or 0)
                            kyt_tx = KYTTransaction(
                                tx_hash=str(tx_hash),
                                chain=a.chain,
                                from_address=str(from_addr or ""),
                                to_address=str(to_addr or ""),
                                value_eth=value_eth,
                                value_usd=value_eth * 1800.0,  # grobe Schätzung; kann später mit price_service ersetzt werden
                                timestamp=datetime.utcnow(),
                                block_number=block_number,
                            )
                            kyt_res = await kyt_engine.analyze_transaction(kyt_tx)
                            await self._broadcast(slug, {
                                "type": "news_case.kyt",
                                "slug": slug,
                                "tx_hash": kyt_res.tx_hash,
                                "risk_level": kyt_res.risk_level.value,
                                "risk_score": kyt_res.risk_score,
                                "alerts": kyt_res.alerts,
                                "from_labels": kyt_res.from_labels,
                                "to_labels": kyt_res.to_labels,
                                "trace_hint": trace_hint,
                                "analysis_time_ms": kyt_res.analysis_time_ms,
                                "timestamp": datetime.utcnow().timestamp(),
                            })
                        except Exception as e:
                            logger.debug("kyt analyze skipped for %s: %s", tx_hash, e)

                        # Optional: Auto-Trace (env-gated)
                        try:
                            if case.auto_trace and os.getenv("ENABLE_NEWSCASE_AUTOTRACE", "0") == "1":
                                asyncio.create_task(self._auto_trace(trace_hint))
                        except Exception as _ae:
                            logger.debug("auto_trace skipped: %s", _ae)

                # Periodic snapshot broadcast (throttled)
                try:
                    snap = await self.snapshot(slug)
                    await self._broadcast(slug, {"type": "news_case.status", "slug": slug, "snapshot": snap})
                except Exception:
                    pass

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("watch loop error for %s: %s", slug, e)
                await asyncio.sleep(interval)

    # ------------------ Public subscribe helper ------------------
    async def connect(self, slug: str) -> asyncio.Queue:
        # Ensure case exists and start watcher
        case = await self.get(slug)
        if not case:
            case = await self._load_case(slug)
        if not case:
            raise ValueError("news case not found")
        await self._ensure_watch(slug)
        q = self.subscribe(slug)
        # Prime with snapshot
        try:
            snap = await self.snapshot(slug)
            await q.put({"type": "news_case.snapshot", "slug": slug, "snapshot": snap})
        except Exception as e:
            logger.debug("initial snapshot failed for %s: %s", slug, e)
        # Prime with recent backlog (deliver last N)
        try:
            bl = self._backlog.get(slug)
            if bl:
                # deliver up to 50 most recent events to avoid flooding
                for evt in list(bl)[-50:]:
                    try:
                        await q.put(evt)
                    except Exception:
                        break
        except Exception:
            pass
        return q


news_case_service = NewsCaseService()
