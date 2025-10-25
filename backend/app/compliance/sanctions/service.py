from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from typing import cast
import inspect

class SanctionsService:
    """Sanctions Aggregator (Stub-Daten), mit Reload-Hooks fuer Mehrquellen-Listen."""
    def __init__(self) -> None:
        self._sources = ["ofac", "un", "eu", "uk", "canada", "australia"]
        self._versions = {s: "v0" for s in self._sources}
        self._counts = {"entities": 0, "aliases": 0}
        # pro-Quelle letzter erfolgreicher Update-Zeitpunkt (ISO)
        self._last_updated: Dict[str, Optional[str]] = {s: None for s in self._sources}
        # In-memory Stores
        self._entities: List[Dict[str, Any]] = []
        self._aliases: List[Dict[str, Any]] = []
        # Schnell-Indexe
        self._address_index: Dict[str, Dict[str, Any]] = {}
        self._name_index: List[Tuple[str, Dict[str, Any]]] = []
        # Aggregierte Counts pro Quelle (für Diff + Health)
        self._source_entity_counts: Dict[str, int] = {s: 0 for s in self._sources}
        self._source_alias_counts: Dict[str, int] = {s: 0 for s in self._sources}
        self._previous_snapshot: Optional[Dict[str, Any]] = None
        self._last_diff_summary: Dict[str, Any] = {}

    def reload(self) -> Dict[str, Any]:
        """Laedt alle Quellen, normalisiert Aliase und aktualisiert Counts/Versions."""
        try:
            from .loader_ofac import fetch_ofac
            from .loader_un import fetch_un
            from .loader_eu import fetch_eu
            from .loader_uk import fetch_uk
            from .loader_canada import fetch_canada
            from .loader_australia import fetch_australia
            from .alias_normalizer import normalize_entities_aliases
        except Exception:
            # Loader sind optional – im Stub-Betrieb einfach leer lassen
            self._entities, self._aliases = [], []
            self._versions = {s: "v0" for s in self._sources}
            self._counts = {"entities": 0, "aliases": 0}
            self._last_updated = {s: None for s in self._sources}
            self._build_indexes()
            return {"success": True, "sources": self._sources, "versions": self._versions, "counts": self._counts}

        collected_entities: List[Dict[str, Any]] = []
        collected_aliases: List[Dict[str, Any]] = []
        # Optionale Prometheus-Metriken
        try:
            from app.metrics import (
                SANCTIONS_FETCH_TOTAL,
                SANCTIONS_FETCH_DURATION,
                SANCTIONS_ENTRIES_TOTAL,
                SANCTIONS_ENTRIES_PARSED,
                SANCTIONS_UPDATE_TIMESTAMP,
                SANCTIONS_UPDATE_ERRORS,
            )  # type: ignore
        except Exception:
            SANCTIONS_FETCH_TOTAL = SANCTIONS_FETCH_DURATION = SANCTIONS_ENTRIES_TOTAL = SANCTIONS_ENTRIES_PARSED = SANCTIONS_UPDATE_TIMESTAMP = SANCTIONS_UPDATE_ERRORS = None  # type: ignore

        import time as _time
        from datetime import datetime as _dt

        previous_snapshot = {
            "versions": dict(self._versions),
            "last_updated": dict(self._last_updated),
            "source_entity_counts": dict(self._source_entity_counts),
            "source_alias_counts": dict(self._source_alias_counts),
        }
        for code, fetch in (
            ("ofac", fetch_ofac),
            ("un", fetch_un),
            ("eu", fetch_eu),
            ("uk", fetch_uk),
            ("canada", fetch_canada),
            ("australia", fetch_australia)
        ):
            try:
                t0 = _time.time()
                if SANCTIONS_FETCH_TOTAL:
                    SANCTIONS_FETCH_TOTAL.labels(source=code).inc()
                ents, als, ver = fetch()
                self._versions[code] = ver
                collected_entities.extend(ents)
                collected_aliases.extend(als)
                self._last_updated[code] = _dt.utcnow().isoformat()
            except Exception:
                # Bei Fehlern Quelle ueberspringen, Version nicht aendern
                if SANCTIONS_UPDATE_ERRORS:
                    try:
                        SANCTIONS_UPDATE_ERRORS.labels(source=code, error_type="fetch_error").inc()
                    except Exception:
                        pass
                continue

        ents_norm, als_norm = normalize_entities_aliases(collected_entities, collected_aliases)
        self._entities, self._aliases = ents_norm, als_norm
        self._counts = {"entities": len(self._entities), "aliases": len(self._aliases)}
        # rebuild indexes for fast screening
        self._build_indexes()
        self._update_source_counts()
        self._previous_snapshot = previous_snapshot
        self._last_diff_summary = self._compute_diff_snapshot(previous_snapshot)
        return {
            "success": True,
            "sources": self._sources,
            "versions": self._versions,
            "counts": self._counts,
            "last_updated": self._last_updated,
        }

    def _build_indexes(self) -> None:
        """Build fast lookup indexes from current entities/aliases."""
        # Address index from aliases of kind 'address'
        addr_idx: Dict[str, Dict[str, Any]] = {}
        for a in self._aliases:
            kind = str(a.get("kind", "")).lower()
            if kind != "address":
                continue
            val = a.get("value_norm") or a.get("value")
            if not isinstance(val, str):
                continue
            key = val.strip().lower()
            if not key:
                continue
            if key not in addr_idx:
                addr_idx[key] = {
                    "entity_id": a.get("entity_id"),
                    "source": a.get("source"),
                }
        self._address_index = addr_idx

        # Name index (entities by canonical_name_norm + alias names/akas)
        name_idx: List[Tuple[str, Dict[str, Any]]] = []
        for e in self._entities:
            can = e.get("canonical_name_norm") or e.get("canonical_name")
            if isinstance(can, str) and can.strip():
                name_idx.append((can.strip().lower(), e))
        for a in self._aliases:
            kind = str(a.get("kind", "")).lower()
            if kind not in {"name", "aka"}:
                continue
            val = a.get("value_norm") or a.get("value")
            if isinstance(val, str) and val.strip():
                name_idx.append((val.strip().lower(), {"entity_id": a.get("entity_id"), "alias": a}))
        self._name_index = name_idx

    def _update_source_counts(self) -> None:
        entity_counts: Dict[str, int] = {s: 0 for s in self._sources}
        alias_counts: Dict[str, int] = {s: 0 for s in self._sources}
        entity_counts["unknown"] = 0
        alias_counts["unknown"] = 0

        for ent in self._entities:
            src = str(ent.get("source") or ent.get("list") or ent.get("origin") or "unknown").lower()
            entity_counts[src] = entity_counts.get(src, 0) + 1

        for ali in self._aliases:
            src = str(ali.get("source") or ali.get("list") or ali.get("origin") or "unknown").lower()
            alias_counts[src] = alias_counts.get(src, 0) + 1

        # Stelle sicher, dass alle bekannten Quellen befüllt sind
        for s in self._sources:
            entity_counts.setdefault(s, 0)
            alias_counts.setdefault(s, 0)

        self._source_entity_counts = entity_counts
        self._source_alias_counts = alias_counts

    def _compute_diff_snapshot(self, previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not previous:
            return {
                "sources": {
                    src: {
                        "version_changed": bool(self._versions.get(src)),
                        "previous_version": None,
                        "current_version": self._versions.get(src),
                        "entity_count_diff": self._source_entity_counts.get(src, 0),
                        "alias_count_diff": self._source_alias_counts.get(src, 0),
                        "previous_last_updated": None,
                        "current_last_updated": self._last_updated.get(src),
                    }
                    for src in self._sources
                },
                "total_entity_diff": self._counts.get("entities", 0),
                "total_alias_diff": self._counts.get("aliases", 0),
            }

        out: Dict[str, Any] = {"sources": {}, "total_entity_diff": 0, "total_alias_diff": 0}
        prev_versions = previous.get("versions", {})
        prev_last_updated = previous.get("last_updated", {})
        prev_entity_counts = previous.get("source_entity_counts", {})
        prev_alias_counts = previous.get("source_alias_counts", {})

        for src in sorted(set(list(prev_versions.keys()) + list(self._versions.keys()))):
            prev_ver = prev_versions.get(src)
            curr_ver = self._versions.get(src)
            prev_last = prev_last_updated.get(src)
            curr_last = self._last_updated.get(src)
            prev_ent = prev_entity_counts.get(src, 0)
            curr_ent = self._source_entity_counts.get(src, 0)
            prev_alias = prev_alias_counts.get(src, 0)
            curr_alias = self._source_alias_counts.get(src, 0)
            ent_diff = curr_ent - prev_ent
            alias_diff = curr_alias - prev_alias
            out["sources"][src] = {
                "version_changed": prev_ver != curr_ver,
                "previous_version": prev_ver,
                "current_version": curr_ver,
                "entity_count_diff": ent_diff,
                "alias_count_diff": alias_diff,
                "previous_last_updated": prev_last,
                "current_last_updated": curr_last,
            }
            out["total_entity_diff"] += ent_diff
            out["total_alias_diff"] += alias_diff
        return out

    def get_diff_summary(self) -> Dict[str, Any]:
        return dict(self._last_diff_summary)

    def health(self, max_age_seconds: int = 3600) -> Dict[str, Any]:
        summary: Dict[str, Any] = {"sources": [], "overall_status": "ok"}
        now = datetime.utcnow()

        for src in self._sources:
            last = self._last_updated.get(src)
            status = "never_updated"
            age_seconds: Optional[float] = None
            if last:
                try:
                    dt = datetime.fromisoformat(last)
                except Exception:
                    dt = None
                if dt:
                    age_seconds = max((now - dt).total_seconds(), 0.0)
                    if age_seconds <= max_age_seconds:
                        status = "ok"
                    else:
                        status = "stale"
                else:
                    status = "unknown"
            summary["sources"].append(
                {
                    "source": src,
                    "status": status,
                    "age_seconds": age_seconds,
                    "last_updated": last,
                    "version": self._versions.get(src),
                    "entity_count": self._source_entity_counts.get(src, 0),
                    "alias_count": self._source_alias_counts.get(src, 0),
                }
            )

        # Aggregierter Status: wenn irgendeine Quelle stale oder never_updated ist → warn
        if any(item["status"] in {"stale", "never_updated", "unknown"} for item in summary["sources"]):
            summary["overall_status"] = "warning"
        if all(item["status"] == "never_updated" for item in summary["sources"]):
            summary["overall_status"] = "critical"

        summary["totals"] = {
            "entities": self._counts.get("entities", 0),
            "aliases": self._counts.get("aliases", 0),
        }
        return summary

    def stats(self) -> Dict[str, Any]:
        """Liefert zusammengefasste Statistiken ohne Breaking Changes.

        Zusätzliche Felder:
        - last_updated: pro-Quelle ISO8601
        - totals: Detailzahlen (entities, aliases)
        """
        return {
            "sources": self._sources,
            "versions": self._versions,
            "counts": self._counts,
            "last_updated": self._last_updated,
            "totals": {"entities": len(self._entities), "aliases": len(self._aliases)},
            "source_entity_counts": dict(self._source_entity_counts),
            "source_alias_counts": dict(self._source_alias_counts),
            "diff": dict(self._last_diff_summary or {}),
        }

    def screen(
        self,
        address: Optional[str] = None,
        name: Optional[str] = None,
        ens: Optional[str] = None,
        lists: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        selected_lists = lists or self._sources
        # Build indexes if tests or callers patched in-memory data directly
        if not self._address_index or not self._name_index:
            try:
                self._build_indexes()
            except Exception:
                pass
        # Availability flag (tests may patch this)
        try:
            from app.compliance.sanctions import _SANCTIONS_AVAILABLE as _AVAIL  # type: ignore
        except Exception:
            _AVAIL = True
        if not _AVAIL:
            return {
                "matched": False,
                "entity_id": None,
                "canonical_name": None,
                "lists": selected_lists,
                "alias_hits": [],
                "explain": "Sanctions service not available",
            }

        if address:
            addr = address.lower()
            # First try repository (tests patch this function)
            try:
                from app.compliance.sanctions import query_labels_by_address  # type: ignore
            except Exception:
                query_labels_by_address = None  # type: ignore

            if query_labels_by_address is not None:  # type: ignore
                try:
                    labels = query_labels_by_address(addr)  # type: ignore[misc]
                except Exception:
                    labels = []
                # Optional list filter
                if lists:
                    allow = {s.lower() for s in selected_lists}
                    labels = [l for l in (labels or []) if str(l.get("source", "")).lower() in allow]
                if labels:
                    first = labels[0]
                    name_val = (first.get("metadata", {}) or {}).get("name") if isinstance(first.get("metadata"), dict) else None
                    src = str(first.get("source", "unknown")).lower()
                    return {
                        "matched": True,
                        "entity_id": first.get("id"),
                        "canonical_name": name_val,
                        "lists": [src] if src else selected_lists,
                        "alias_hits": [
                            {
                                "alias": addr,
                                "kind": "address",
                                "confidence": 1.0,
                                "source": src or "unknown",
                            }
                        ],
                        "explain": f"Address matched {len(labels)} sanctions entries",
                    }

            # Fallback 1: direct alias scan (address)
            try:
                for a in self._aliases:
                    if str(a.get("kind", "")).lower() != "address":
                        continue
                    val = a.get("value_norm") or a.get("value")
                    if isinstance(val, str) and val.strip().lower() == addr:
                        src = str(a.get("source", "unknown")).lower()
                        if (not lists) or (src in {s.lower() for s in selected_lists}):
                            return {
                                "matched": True,
                                "entity_id": a.get("entity_id"),
                                "canonical_name": None,
                                "lists": [src] if src else selected_lists,
                                "alias_hits": [
                                    {"alias": val, "kind": "address", "confidence": 1.0, "source": src}
                                ],
                                "explain": "Address matched sanctions aliases",
                            }
            except Exception:
                pass
            # Fallback 2: in-memory address index
            hit = self._address_index.get(addr)
            if hit and (not lists or str(hit.get("source", "")).lower() in {s.lower() for s in selected_lists}):
                return {
                    "matched": True,
                    "entity_id": hit.get("entity_id"),
                    "canonical_name": hit.get("name"),
                    "lists": [hit.get("source")] if hit.get("source") else selected_lists,
                    "alias_hits": [
                        {
                            "alias": addr,
                            "kind": "address",
                            "confidence": 1.0,
                            "source": hit.get("source", "unknown"),
                        }
                    ],
                    "explain": "Address matched sanctions index",
                }

        # ENS exact alias match (if provided)
        if ens:
            qens = str(ens).strip().lower()
            try:
                for a in self._aliases:
                    if str(a.get("kind", "")).lower() != "ens":
                        continue
                    val = a.get("value_norm") or a.get("value")
                    if isinstance(val, str) and val.strip().lower() == qens:
                        src = str(a.get("source", "unknown")).lower()
                        if (not lists) or (src in {s.lower() for s in selected_lists}):
                            return {
                                "matched": True,
                                "entity_id": a.get("entity_id"),
                                "canonical_name": None,
                                "lists": [src] if src else selected_lists,
                                "alias_hits": [
                                    {"alias": val, "kind": "ens", "confidence": 1.0, "source": src}
                                ],
                                "explain": "ENS matched sanctions aliases",
                            }
            except Exception:
                pass

        name_query = name or ens
        if name_query and self._name_index:
            try:
                from rapidfuzz import process, fuzz  # type: ignore
                candidates = [n for n, _ in self._name_index]
                match = process.extractOne(name_query, candidates, scorer=fuzz.WRatio)
                if match and match[1] >= 85:
                    idx = candidates.index(match[0])
                    entry = self._name_index[idx][1]
                    if (not lists) or (entry.get("source") in selected_lists):
                        return {
                            "matched": True,
                            "entity_id": entry.get("entity_id"),
                            "canonical_name": entry.get("name"),
                            "lists": [entry.get("source")] if entry.get("source") else selected_lists,
                            "alias_hits": [
                                {
                                    "alias": name_query,
                                    "kind": "name",
                                    "confidence": float(match[1]) / 100.0,
                                    "source": entry.get("source", "unknown"),
                                }
                            ],
                            "explain": "Name fuzzy-match sanctions index"
                        }
            except Exception:
                pass
        # No match / no input
        return {
            "matched": False,
            "entity_id": None,
            "canonical_name": None,
            "lists": selected_lists,
            "alias_hits": [],
            "explain": "No matches found",
        }

    def ingest_webhook(self, source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ingestiert ein Sanctions-Webhook-Payload, normalisiert Adressen und persistiert Labels.

        Erwartete Payload-Varianten (Beispiele):
        - {"addresses": ["0xabc...", ...], "chain": "ethereum", "label": "sanctioned", "category": "OFAC"}
        - {"items": [{"chain": "ethereum", "address": "0x...", "label": "sanctioned", "category": "OFAC"}, ...]}
        - {"entries": [...]}  # gleiches Format wie items
        """
        # Resolve bulk_upsert: prefer module-level (allows monkeypatch in tests), fallback to repo import
        bulk_fn = None
        try:
            from app.compliance.sanctions import service as _svc_mod  # type: ignore
            bulk_fn = getattr(_svc_mod, "bulk_upsert", None)
        except Exception:
            bulk_fn = None
        if bulk_fn is None:
            try:
                from app.repos.labels_repo import bulk_upsert as _bulk
                bulk_fn = _bulk
            except Exception:
                return {"inserted": 0, "existing": 0, "total": 0, "note": "labels_repo unavailable"}

        norm: List[Dict[str, str]] = []
        try:
            src = (source or "unknown").upper()
            # Variante 1: flache Liste addresses + gemeinsame Felder
            if isinstance(payload.get("addresses"), list):
                chain = str(payload.get("chain") or "ethereum").lower()
                label = str(payload.get("label") or "sanctioned").strip() or "sanctioned"
                category = str(payload.get("category") or src).strip() or src
                for addr in payload["addresses"]:
                    a = str(addr or "").lower()
                    if a:
                        norm.append({"chain": chain, "address": a, "label": label, "category": category})
            # Variante 2/3: items/entries mit detailierten Objekten
            for key in ("items", "entries"):
                if isinstance(payload.get(key), list):
                    for it in payload[key]:
                        chain = str((it or {}).get("chain") or payload.get("chain") or "ethereum").lower()
                        addr = str((it or {}).get("address") or "").lower()
                        label = str((it or {}).get("label") or payload.get("label") or "sanctioned").strip() or "sanctioned"
                        category = str((it or {}).get("category") or payload.get("category") or src).strip() or src
                        if addr:
                            norm.append({"chain": chain, "address": addr, "label": label, "category": category})
        except Exception:
            norm = []

        if not norm:
            return {"inserted": 0, "existing": 0, "total": 0}

        try:
            res = bulk_fn(norm)  # type: ignore[misc]
            if inspect.iscoroutine(res):
                import asyncio
                res = asyncio.get_event_loop().run_until_complete(res)
            inserted, existing = 0, 0
            if isinstance(res, (tuple, list)) and len(res) >= 2:
                inserted, existing = int(res[0]), int(res[1])
            elif isinstance(res, dict) and "inserted" in res and "existing" in res:
                inserted, existing = int(res.get("inserted", 0)), int(res.get("existing", 0))
            else:
                inserted, existing = len(norm), 0
        except Exception as e:
            return {"inserted": 0, "existing": 0, "total": len(norm), "error": str(e)}

        try:
            self._counts["entities"] += int(inserted)
        except Exception:
            pass
        return {"inserted": int(inserted), "existing": int(existing), "total": len(norm)}

sanctions_service = SanctionsService()
