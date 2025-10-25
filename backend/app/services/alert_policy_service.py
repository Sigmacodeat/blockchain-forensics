"""
Alert Policy Service
====================

Lightweight in-memory/JSON-based policy store for alert rules with versioning
and simulation support. Designed as a drop-in until DB models are added.
"""
from __future__ import annotations

import os
import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from app.observability.metrics import RULE_EVAL_TOTAL, RULE_EVAL_LATENCY
except Exception:
    RULE_EVAL_TOTAL = None  # type: ignore
    RULE_EVAL_LATENCY = None  # type: ignore

_POLICY_DIR = Path(os.getenv("ALERT_POLICY_DIR", ".policies"))
_POLICY_DIR.mkdir(exist_ok=True)


@dataclass
class PolicyVersion:
    version: int
    created_at: str
    created_by: str
    status: str  # draft|active|archived
    rules: Dict[str, Any]
    notes: Optional[str] = None


@dataclass
class Policy:
    id: str
    name: str
    latest_version: int
    versions: List[PolicyVersion]


class AlertPolicyService:
    """Simple policy store with JSON persistence per policy.

    File layout: .policies/{policy_id}.json
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: Dict[str, Policy] = {}
        self._load_all()

    def _policy_path(self, policy_id: str) -> Path:
        return _POLICY_DIR / f"{policy_id}.json"

    def _load_all(self) -> None:
        for p in _POLICY_DIR.glob("*.json"):
            try:
                data = json.loads(p.read_text())
                versions = [PolicyVersion(**v) for v in data.get("versions", [])]
                policy = Policy(
                    id=data["id"],
                    name=data.get("name", data["id"]),
                    latest_version=data.get("latest_version", len(versions)),
                    versions=versions,
                )
                self._cache[policy.id] = policy
            except Exception:
                continue

    def _persist(self, policy: Policy) -> None:
        with self._lock:
            data = asdict(policy)
            self._policy_path(policy.id).write_text(json.dumps(data, indent=2))
            self._cache[policy.id] = policy

    # CRUD
    def list_policies(self) -> List[Dict[str, Any]]:
        return [self._serialize_summary(p) for p in self._cache.values()]

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        p = self._cache.get(policy_id)
        return self._serialize(p) if p else None

    def create_policy(self, policy_id: str, name: str, rules: Dict[str, Any], created_by: str = "system", notes: Optional[str] = None) -> Dict[str, Any]:
        if policy_id in self._cache:
            raise ValueError("policy_id already exists")
        v = PolicyVersion(
            version=1,
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by,
            status="draft",
            rules=rules,
            notes=notes,
        )
        policy = Policy(id=policy_id, name=name, latest_version=1, versions=[v])
        self._persist(policy)
        return self._serialize(policy)

    def update_policy(self, policy_id: str, rules: Dict[str, Any], created_by: str = "system", notes: Optional[str] = None, status: str = "draft") -> Dict[str, Any]:
        p = self._cache.get(policy_id)
        if not p:
            raise ValueError("policy not found")
        new_version = p.latest_version + 1
        v = PolicyVersion(
            version=new_version,
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by,
            status=status,
            rules=rules,
            notes=notes,
        )
        p.versions.append(v)
        p.latest_version = new_version
        self._persist(p)
        return self._serialize(p)

    def set_status(self, policy_id: str, version: int, status: str) -> Dict[str, Any]:
        p = self._cache.get(policy_id)
        if not p:
            raise ValueError("policy not found")
        for v in p.versions:
            if v.version == version:
                v.status = status
                self._persist(p)
                return self._serialize(p)
        raise ValueError("version not found")

    def get_active_rules(self) -> Dict[str, Any]:
        # Combine all policies' latest active versions (simple merge by top-level keys)
        active: Dict[str, Any] = {}
        for p in self._cache.values():
            # pick highest version with status=active, else skip
            active_versions = [v for v in p.versions if v.status == "active"]
            if not active_versions:
                continue
            v = sorted(active_versions, key=lambda x: x.version)[-1]
            # merge rules (shallow)
            for k, val in v.rules.items():
                active[k] = val
        return active

    # Simulation
    def simulate(self, policy_rules: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulation: apply rule conditions against events and compute hits.
        Backward-compatible and extended with additional operators and optional weighted scoring.
        Expected structure (example):
        {
          "rules": [
            {"name": "high_risk_address", "when": {"risk_score_gte": 80}, "severity": "high"},
            {"name": "sanctioned", "when": {"sanctioned": true}, "severity": "critical"}
          ],
          "weighted_rules": [
            {"name": "mixer_usage_weight", "weight": 0.4, "when": {"mixer_usage": true}},
            {"name": "bridge_weight", "weight": 0.3, "when": {"cross_chain_bridge": true}},
            {"name": "cluster_weight", "weight": 0.3, "when": {"cluster_size_gte": 10}}
          ],
          "score_threshold": 0.7
        }
        """
        rules = policy_rules.get("rules", [])
        weighted_rules = policy_rules.get("weighted_rules", [])
        score_threshold = float(policy_rules.get("score_threshold", 0.0))

        total = len(events)
        hits = 0
        by_rule: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        scores: List[float] = []

        def _match_conditions(ev: Dict[str, Any], when: Dict[str, Any]) -> bool:
            ok = True
            for cond, val in (when or {}).items():
                if cond == "risk_score_gte":
                    ok = ok and float(ev.get("risk_score", 0)) >= float(val)
                elif cond == "sanctioned":
                    ok = ok and bool(ev.get("sanctioned", False)) is bool(val)
                elif cond == "label_in":
                    labels = ev.get("labels", []) or []
                    ok = ok and any(l in labels for l in (val or []))
                elif cond == "cluster_size_gte":
                    ok = ok and int(ev.get("cluster_size", 1)) >= int(val)
                elif cond == "cross_chain_bridge":
                    ok = ok and bool(ev.get("bridge_activity", False)) is bool(val)
                elif cond == "mixer_usage":
                    ok = ok and bool(ev.get("mixer_usage", False)) is bool(val)
                elif cond == "anomaly_score_gte":
                    ok = ok and float(ev.get("anomaly_score", 0.0)) >= float(val)
                elif cond == "whale_movement":
                    ok = ok and bool(ev.get("whale_movement", False)) is bool(val)
                elif cond == "suspicious_pattern_in":
                    pats = ev.get("suspicious_patterns", []) or []
                    ok = ok and any(p in pats for p in (val or []))
                elif cond == "in_list":
                    # expects { in_list: { field: "labels", values: [..] } }
                    try:
                        field = val.get("field")
                        values = val.get("values", [])
                        seq = ev.get(field, []) or []
                        if not isinstance(seq, list):
                            seq = [seq]
                        ok = ok and any(x in values for x in seq)
                    except Exception:
                        ok = False
                elif cond == "not_in_list":
                    try:
                        field = val.get("field")
                        values = val.get("values", [])
                        seq = ev.get(field, []) or []
                        if not isinstance(seq, list):
                            seq = [seq]
                        ok = ok and all(x not in values for x in seq)
                    except Exception:
                        ok = False
                else:
                    ok = ok and ev.get(cond) == val
                if not ok:
                    break
            return ok

        # Boolean rules -> hits
        import time as _t
        for ev in events:
            for rule in rules:
                name = rule.get("name", "unnamed")
                when: Dict[str, Any] = rule.get("when", {})
                _start = _t.perf_counter()
                matched = _match_conditions(ev, when)
                _dur = _t.perf_counter() - _start
                # metrics
                try:
                    if RULE_EVAL_TOTAL:
                        RULE_EVAL_TOTAL.labels(rule=name, outcome=("hit" if matched else "miss")).inc()
                    if RULE_EVAL_LATENCY:
                        RULE_EVAL_LATENCY.labels(rule=name).observe(_dur)
                except Exception:
                    pass
                if matched:
                    hits += 1
                    by_rule[name] = by_rule.get(name, 0) + 1
                    sev = rule.get("severity", "medium")
                    by_severity[sev] = by_severity.get(sev, 0) + 1
                    break  # one rule hit per event

        # Weighted rules -> risk score (0..1)
        if weighted_rules:
            for ev in events:
                score = 0.0
                for wr in weighted_rules:
                    w = float(wr.get("weight", 0.0))
                    when = wr.get("when", {})
                    if w > 0 and _match_conditions(ev, when):
                        score += w
                # clamp to 1.0
                score = min(score, 1.0)
                scores.append(score)
                # if a threshold is provided, we can also count as hit
                if score_threshold > 0 and score >= score_threshold:
                    hits += 1
                    by_rule["weighted_threshold"] = by_rule.get("weighted_threshold", 0) + 1
                    by_severity["high"] = by_severity.get("high", 0) + 1

        return {
            "total_events": total,
            "hits": hits,
            "hit_rate": (hits / total) if total else 0.0,
            "by_rule": by_rule,
            "by_severity": by_severity,
            "scores": scores if scores else None,
            "score_threshold": score_threshold if weighted_rules else None,
        }

    # Serialization helpers
    def _serialize_summary(self, p: Policy) -> Dict[str, Any]:
        return {
            "id": p.id,
            "name": p.name,
            "latest_version": p.latest_version,
            "versions": [
                {"version": v.version, "status": v.status, "created_at": v.created_at}
                for v in p.versions
            ]
        }

    def _serialize(self, p: Optional[Policy]) -> Optional[Dict[str, Any]]:
        if not p:
            return None
        return {
            "id": p.id,
            "name": p.name,
            "latest_version": p.latest_version,
            "versions": [asdict(v) for v in p.versions]
        }


# Global instance
alert_policy_service = AlertPolicyService()
