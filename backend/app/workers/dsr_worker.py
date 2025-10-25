from __future__ import annotations
import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timezone
import os
import uuid
from pathlib import Path

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

ISO_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"

# Optional Prometheus metrics (non-fatal if unavailable)
try:
    from prometheus_client import Counter, Summary

    DSR_EXPORTS_PROCESSED = Counter(
        "dsr_exports_processed_total",
        "Number of DSR export tickets processed",
    )
    DSR_DELETES_PROCESSED = Counter(
        "dsr_deletes_processed_total",
        "Number of DSR delete tickets processed",
    )
    DSR_PROCESS_ERRORS = Counter(
        "dsr_process_errors_total",
        "Number of DSR processing errors",
        ["action"],
    )
    DSR_STATUS_TOTAL = Counter(
        "dsr_status_total",
        "DSR ticket status updates",
        ["action", "status"],
    )
    DSR_SCAN_SECONDS = Summary(
        "dsr_scan_seconds",
        "Time spent in a DSR worker scan iteration",
        ["action"],
    )
except Exception:  # pragma: no cover
    DSR_EXPORTS_PROCESSED = None
    DSR_DELETES_PROCESSED = None
    DSR_PROCESS_ERRORS = None
    DSR_SCAN_SECONDS = None
    DSR_STATUS_TOTAL = None


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


class DSRWorker:
    def __init__(self, interval_seconds: int = 300):
        self._interval = max(30, int(interval_seconds))
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Storage configuration
        self._export_dir = os.getenv("DSR_EXPORT_DIR", "/tmp/dsr-exports")
        self._s3_bucket = os.getenv("DSR_S3_BUCKET")
        self._s3_prefix = os.getenv("DSR_S3_PREFIX", "exports/")
        self._aws_region = os.getenv("AWS_REGION")
        self._presign_expires = int(os.getenv("DSR_S3_PRESIGN_EXPIRES", "604800"))
        self._max_attempts_default = int(os.getenv("DSR_MAX_ATTEMPTS", "5"))
        self._done_ttl_default = int(os.getenv("DSR_DONE_TTL", "604800"))
        # boto3 is optional
        self._boto3 = None
        if self._s3_bucket:
            try:
                import boto3  # type: ignore

                self._boto3 = boto3
            except Exception:
                logger.warning("boto3 nicht verfügbar – Export fällt auf Lokalspeicher zurück")

    # -------------------- JSON helpers --------------------
    @staticmethod
    def _loads(val: Any) -> Dict[str, Any]:
        try:
            if val is None:
                return {}
            if isinstance(val, bytes):
                val = val.decode("utf-8", errors="ignore")
            if isinstance(val, str) and val.strip():
                return json.loads(val)
        except Exception:
            pass
        return {}

    @staticmethod
    def _dumps(obj: Dict[str, Any]) -> str:
        return json.dumps(obj, separators=(",", ":"))

    # -------------------- Locking helpers --------------------
    @staticmethod
    async def _acquire_lock(client, key: str, ttl_sec: int = 300) -> bool:
        """Try to acquire per-ticket lock to avoid double processing."""
        lock_key = f"{key}:lock"
        try:
            # set if not exists with ttl
            # For aioredis 2.x: set(name, value, ex=None, px=None, nx=False, xx=False)
            ok = await client.set(lock_key, "1", ex=ttl_sec, nx=True)
            return bool(ok)
        except Exception:
            return False

    @staticmethod
    async def _release_lock(client, key: str):
        try:
            await client.delete(f"{key}:lock")
        except Exception:
            pass

    # -------------------- Generic processor --------------------
    async def _process_tickets(
        self,
        client,
        pattern: str,
        mutate_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        action: str,
    ) -> int:
        processed = 0
        timer_ctx = None
        try:
            if DSR_SCAN_SECONDS is not None:
                timer_ctx = DSR_SCAN_SECONDS.labels(action=action).time()
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
                for k in keys or []:
                    # Acquire lock to prevent concurrent workers racing
                    got_lock = await self._acquire_lock(client, k)
                    if not got_lock:
                        continue
                    try:
                        raw = await client.get(k)
                        payload = self._loads(raw)

                        # Idempotency: skip if already done
                        if payload.get("status") == "done":
                            continue

                        # Mark started_at if first time
                        payload.setdefault("started_at", _utcnow_iso())
                        payload.setdefault("attempts", 0)
                        payload["attempts"] = int(payload.get("attempts", 0))
                        payload.setdefault("request_id", payload.get("id") or "")
                        payload.setdefault("type", action)

                        # Basic validation
                        missing = []
                        if not payload.get("user_id"):
                            missing.append("user_id")
                        if not payload.get("request_id"):
                            missing.append("request_id")
                        if missing:
                            raise ValueError(f"missing fields: {','.join(missing)}")

                        # Apply mutation (domain-specific work)
                        new_payload = mutate_fn(payload)
                        new_payload.setdefault("ticket", k)
                        new_payload.setdefault("action", action)

                        await client.set(k, self._dumps(new_payload))
                        # Set TTL for completed tickets (default 7d)
                        try:
                            await client.expire(k, int(payload.get("ttl_done", self._done_ttl_default)))
                        except Exception:
                            pass
                        processed += 1
                        # Metrics
                        if action == "export" and DSR_EXPORTS_PROCESSED is not None:
                            DSR_EXPORTS_PROCESSED.inc()
                        elif action == "delete" and DSR_DELETES_PROCESSED is not None:
                            DSR_DELETES_PROCESSED.inc()
                        if DSR_STATUS_TOTAL is not None:
                            DSR_STATUS_TOTAL.labels(action=action, status=new_payload.get("status", "")).inc()
                    except Exception as e:
                        logger.warning(f"DSR {action} ticket processing failed for {k}: {e}")
                        # Update failure info and attempts, with optional max attempts
                        try:
                            payload["attempts"] = int(payload.get("attempts", 0)) + 1
                            payload["last_error"] = str(e)
                            payload["failed_at"] = _utcnow_iso()
                            max_attempts = int(payload.get("max_attempts", self._max_attempts_default))
                            if payload["attempts"] >= max_attempts:
                                payload["status"] = "failed"
                            await client.set(k, self._dumps(payload))
                        except Exception:
                            pass
                        if DSR_PROCESS_ERRORS is not None:
                            DSR_PROCESS_ERRORS.labels(action=action).inc()
                        if DSR_STATUS_TOTAL is not None:
                            DSR_STATUS_TOTAL.labels(action=action, status=payload.get("status", "failed")).inc()
                    finally:
                        await self._release_lock(client, k)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"DSR {action} scan failed: {e}")
            if DSR_PROCESS_ERRORS is not None:
                DSR_PROCESS_ERRORS.labels(action=action).inc()
        finally:
            if timer_ctx is not None:
                try:
                    timer_ctx.__exit__(None, None, None)
                except Exception:
                    pass
        return processed

    # -------------------- Specific processors --------------------
    async def _assemble_user_export(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """Assembles a comprehensive export payload for the user.
        Aggregates data from Postgres (users, cases, alerts), Neo4j (graph), Redis (sessions).
        """
        user_id = p.get("user_id")
        export_data = {
            "user_id": user_id,
            "generated_at": _utcnow_iso(),
            "entities": {
                "profile": {},
                "cases": [],
                "alerts": [],
                "analytics": {},
                "graph_nodes": [],
                "sessions": [],
            },
            "meta": {"request_id": p.get("request_id")},
        }
        
        try:
            # Postgres: User profile, cases, alerts
            from app.db.session import get_db
            async for db in get_db():
                try:
                    # User profile (sanitized)
                    from sqlalchemy import text
                    result = await db.execute(
                        text("SELECT id, email, created_at, updated_at FROM users WHERE id = :user_id"),
                        {"user_id": user_id}
                    )
                    user_row = result.fetchone()
                    if user_row:
                        export_data["entities"]["profile"] = {
                            "id": str(user_row[0]),
                            "email": user_row[1],
                            "created_at": user_row[2].isoformat() if user_row[2] else None,
                            "updated_at": user_row[3].isoformat() if user_row[3] else None,
                        }
                    
                    # Cases (if table exists)
                    try:
                        cases_result = await db.execute(
                            text("SELECT id, title, created_at, status FROM cases WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 100"),
                            {"user_id": user_id}
                        )
                        for row in cases_result:
                            export_data["entities"]["cases"].append({
                                "id": str(row[0]),
                                "title": row[1],
                                "created_at": row[2].isoformat() if row[2] else None,
                                "status": row[3],
                            })
                    except Exception:
                        pass  # Table may not exist
                    
                    # Alerts (if table exists)
                    try:
                        alerts_result = await db.execute(
                            text("SELECT id, rule_type, severity, created_at FROM alerts WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 100"),
                            {"user_id": user_id}
                        )
                        for row in alerts_result:
                            export_data["entities"]["alerts"].append({
                                "id": str(row[0]),
                                "rule_type": row[1],
                                "severity": row[2],
                                "created_at": row[3].isoformat() if row[3] else None,
                            })
                    except Exception:
                        pass
                except Exception as e:
                    logger.warning(f"Postgres aggregation error: {e}")
                break
            
            # Neo4j: User-created graph nodes/relationships (if applicable)
            try:
                from app.db.neo4j_client import neo4j_client
                query = """
                    MATCH (n) WHERE n.user_id = $user_id OR n.created_by = $user_id
                    RETURN n.address as address, labels(n) as labels, n.created_at as created_at
                    LIMIT 50
                """
                records = await neo4j_client.execute_read(query, {"user_id": str(user_id)})
                for rec in records:
                    export_data["entities"]["graph_nodes"].append({
                        "address": rec.get("address"),
                        "labels": rec.get("labels"),
                        "created_at": rec.get("created_at"),
                    })
            except Exception as e:
                logger.warning(f"Neo4j aggregation error: {e}")
            
            # Redis: Active sessions (keys like session:{user_id}:*)
            try:
                from app.db.redis_client import redis_client
                await redis_client._ensure_connected()
                client = getattr(redis_client, "client", None)
                if client:
                    pattern = f"session:{user_id}:*"
                    cursor = 0
                    sessions_found = 0
                    while sessions_found < 20:  # limit to 20
                        cursor, keys = await client.scan(cursor=cursor, match=pattern, count=10)
                        for k in keys or []:
                            try:
                                val = await client.get(k)
                                if val:
                                    export_data["entities"]["sessions"].append({
                                        "key": k.decode() if isinstance(k, bytes) else k,
                                        "data": val.decode()[:200] if isinstance(val, bytes) else str(val)[:200],
                                    })
                                    sessions_found += 1
                            except Exception:
                                pass
                        if cursor == 0:
                            break
            except Exception as e:
                logger.warning(f"Redis aggregation error: {e}")
        except Exception as e:
            logger.error(f"Data export aggregation failed: {e}")
        
        return export_data

    def _store_export(self, data: Dict[str, Any], user_id: str, request_id: str) -> str:
        """Stores export JSON to S3 (if configured) or local disk and returns a URL/path.
        Returns an s3:// URL if uploaded, else file:// path.
        """
        content = self._dumps(data)
        filename = f"{user_id}_{request_id}_{uuid.uuid4().hex}.json"
        # Try S3 first when available
        if self._boto3 and self._s3_bucket:
            try:
                key = f"{self._s3_prefix.rstrip('/')}/{filename}"
                if self._aws_region:
                    s3 = self._boto3.client("s3", region_name=self._aws_region)
                else:
                    s3 = self._boto3.client("s3")
                s3.put_object(Bucket=self._s3_bucket, Key=key, Body=content.encode("utf-8"), ContentType="application/json")
                try:
                    url = s3.generate_presigned_url(
                        ClientMethod="get_object",
                        Params={"Bucket": self._s3_bucket, "Key": key},
                        ExpiresIn=self._presign_expires,
                    )
                    return url
                except Exception:
                    return f"s3://{self._s3_bucket}/{key}"
            except Exception as e:
                logger.warning(f"S3 Upload fehlgeschlagen, nutze Lokalspeicher: {e}")
        # Fallback: local file
        try:
            Path(self._export_dir).mkdir(parents=True, exist_ok=True)
            file_path = Path(self._export_dir) / filename
            file_path.write_text(content, encoding="utf-8")
            return f"file://{file_path}"
        except Exception as e:
            logger.error(f"Lokaler Export fehlgeschlagen: {e}")
            raise

    async def _process_exports(self, client) -> int:
        async def mutate_export(p: Dict[str, Any]) -> Dict[str, Any]:
            # Assemble data and store
            data = await self._assemble_user_export(p)
            try:
                export_url = self._store_export(data, str(p.get("user_id")), str(p.get("request_id")))
                p["export_url"] = export_url
                p["status"] = "done"
            except Exception as e:
                p["status"] = "failed"
                p["last_error"] = str(e)
            p["completed_at"] = _utcnow_iso()
            return p

        return await self._process_tickets(client, "dsr:export:*", mutate_export, "export")

    async def _process_deletes(self, client) -> int:
        async def mutate_delete(p: Dict[str, Any]) -> Dict[str, Any]:
            """Implement deletion policies per datastore (GDPR Right to Erasure).
            Anonymizes or deletes personal data from Postgres, Neo4j, Redis.
            """
            user_id = p.get("user_id")
            errors = []
            
            try:
                # Postgres: Anonymize user record and delete related data
                from app.db.session import get_db
                async for db in get_db():
                    try:
                        from sqlalchemy import text
                        # Anonymize user profile (keep record for referential integrity)
                        await db.execute(
                            text("""
                                UPDATE users 
                                SET email = CONCAT('deleted_', id, '@anonymized.local'),
                                    name = 'Deleted User',
                                    password_hash = '',
                                    updated_at = NOW()
                                WHERE id = :user_id
                            """),
                            {"user_id": user_id}
                        )
                        
                        # Delete user-owned cases (if table exists)
                        try:
                            await db.execute(
                                text("DELETE FROM cases WHERE user_id = :user_id"),
                                {"user_id": user_id}
                            )
                        except Exception:
                            pass
                        
                        # Delete user alerts
                        try:
                            await db.execute(
                                text("DELETE FROM alerts WHERE user_id = :user_id"),
                                {"user_id": user_id}
                            )
                        except Exception:
                            pass
                        
                        await db.commit()
                    except Exception as e:
                        errors.append(f"Postgres: {e}")
                        await db.rollback()
                    break
                
                # Neo4j: Delete user-created nodes/relationships
                try:
                    from app.db.neo4j_client import neo4j_client
                    query = """
                        MATCH (n) WHERE n.user_id = $user_id OR n.created_by = $user_id
                        DETACH DELETE n
                    """
                    await neo4j_client.execute_write(query, {"user_id": str(user_id)})
                except Exception as e:
                    errors.append(f"Neo4j: {e}")
                
                # Redis: Delete sessions and cached data
                try:
                    from app.db.redis_client import redis_client
                    await redis_client._ensure_connected()
                    redis_cli = getattr(redis_client, "client", None)
                    if redis_cli:
                        # Delete session keys
                        pattern = f"session:{user_id}:*"
                        cursor = 0
                        while True:
                            cursor, keys = await redis_cli.scan(cursor=cursor, match=pattern, count=100)
                            if keys:
                                await redis_cli.delete(*keys)
                            if cursor == 0:
                                break
                        # Delete user cache
                        await redis_cli.delete(f"user:{user_id}")
                        await redis_cli.delete(f"user:{user_id}:*")
                except Exception as e:
                    errors.append(f"Redis: {e}")
                
                # Mark as done if no critical errors
                if errors:
                    p["status"] = "partial" if len(errors) < 3 else "failed"
                    p["last_error"] = "; ".join(errors)
                else:
                    p["status"] = "done"
            except Exception as e:
                p["status"] = "failed"
                p["last_error"] = str(e)
            
            p["completed_at"] = _utcnow_iso()
            return p

        return await self._process_tickets(client, "dsr:delete:*", mutate_delete, "delete")

    # -------------------- Run loop --------------------
    async def run(self):
        self._running = True
        logger.info("DSR worker started")
        try:
            while self._running:
                try:
                    await redis_client._ensure_connected()  # type: ignore[attr-defined]
                    client = getattr(redis_client, "client", None)
                    if client is not None:
                        exp = await self._process_exports(client)
                        dele = await self._process_deletes(client)
                        if exp or dele:
                            logger.info(f"DSR worker processed: exports={exp}, deletes={dele}")
                    else:
                        logger.warning("DSR worker: redis unavailable")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"DSR worker iteration failed: {e}")
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            logger.info("DSR worker cancelled")
            raise
        finally:
            logger.info("DSR worker stopped")

    async def run_once(self) -> Dict[str, int]:
        """Runs a single scan iteration for exports and deletes."""
        stats = {"exports": 0, "deletes": 0}
        try:
            await redis_client._ensure_connected()  # type: ignore[attr-defined]
            client = getattr(redis_client, "client", None)
            if client is not None:
                stats["exports"] = await self._process_exports(client)
                stats["deletes"] = await self._process_deletes(client)
            else:
                logger.warning("DSR run_once: redis unavailable")
        except Exception as e:
            logger.error(f"DSR run_once failed: {e}")
        return stats

    def start(self) -> asyncio.Task:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())
        return self._task

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()


def start_dsr_worker(interval_seconds: int = 300) -> DSRWorker:
    w = DSRWorker(interval_seconds=interval_seconds)
    w.start()
    return w


def stop_dsr_worker(worker: Optional[DSRWorker]):
    try:
        if worker:
            worker.stop()
    except Exception:
        pass
