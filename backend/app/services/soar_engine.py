from __future__ import annotations
import os
import glob
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

from app.services.typology_engine import _SafeEvaluator  # reuse safe expression evaluator
from app.services.case_management import (
    case_management_service,
    CaseType,
    CasePriority,
)

logger = logging.getLogger(__name__)


@dataclass
class Action:
    type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Playbook:
    id: str
    name: str
    enabled: bool = True
    condition: str = ""
    actions: List[Action] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class SOAREngine:
    def __init__(self, dir_path: Optional[str] = None) -> None:
        base = os.getcwd()
        self.dir_path = dir_path or os.path.join(base, "backend", "app", "soar", "playbooks")
        self._playbooks: List[Playbook] = []
        self._loaded = False

    def load_playbooks(self) -> int:
        # Lazy import yaml
        try:
            import yaml  # type: ignore
        except Exception:
            self._loaded = True
            return 0
        self._playbooks = []
        os.makedirs(self.dir_path, exist_ok=True)
        for path in glob.glob(os.path.join(self.dir_path, "*.yaml")):
            try:
                data = yaml.safe_load(open(path, "r", encoding="utf-8")) or {}
                rules = data.get("playbooks", []) if isinstance(data, dict) else []
                for pb in rules:
                    try:
                        actions = [Action(type=a.get("type"), params={k: v for k, v in a.items() if k != "type"}) for a in pb.get("actions", [])]
                        self._playbooks.append(
                            Playbook(
                                id=str(pb.get("id")),
                                name=str(pb.get("name")),
                                enabled=bool(pb.get("enabled", True)),
                                condition=str(pb.get("condition", "")),
                                actions=actions,
                                tags=list(pb.get("tags", [])),
                            )
                        )
                    except Exception:
                        continue
            except Exception:
                continue
        self._loaded = True
        return len(self._playbooks)

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_playbooks()

    def list_playbooks(self) -> List[Dict[str, Any]]:
        self.ensure_loaded()
        return [
            {
                "id": pb.id,
                "name": pb.name,
                "enabled": pb.enabled,
                "tags": pb.tags,
            }
            for pb in self._playbooks
        ]

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Get a single playbook by id."""
        self.ensure_loaded()
        for pb in self._playbooks:
            if str(pb.id) == str(playbook_id):
                return pb
        return None

    def set_enabled(self, playbook_id: str, enabled: bool) -> bool:
        """Enable or disable a playbook in-memory (non-persistent)."""
        self.ensure_loaded()
        for pb in self._playbooks:
            if str(pb.id) == str(playbook_id):
                pb.enabled = bool(enabled)
                return True
        return False

    def _fmt(self, s: Any, ctx: Dict[str, Any]) -> str:
        if not isinstance(s, str):
            return str(s)
        # simple format: replace {key} with ctx.get(key, "") (no nested)
        out = s
        for k, v in ctx.items():
            try:
                out = out.replace("{" + str(k) + "}", str(v))
            except Exception:
                continue
        return out

    def _exec_action(self, action: Action, event: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        t = action.type
        p = action.params or {}
        res: Dict[str, Any] = {"type": t, "status": "skipped"}
        try:
            if t == "create_case":
                case_type = CaseType[p.get("case_type", "TRANSACTION_REVIEW").upper()]
                title = self._fmt(p.get("title", "Auto Case"), ctx)
                desc = self._fmt(p.get("description", ""), ctx)
                priority = CasePriority[p.get("priority", "MEDIUM").upper()]
                customer_id = self._fmt(p.get("customer_id", ""), ctx)
                customer_name = self._fmt(p.get("customer_name", ""), ctx)
                customer_tier = self._fmt(p.get("customer_tier", "unknown"), ctx)
                created_by = self._fmt(p.get("created_by", "system"), ctx)
                created_by_name = self._fmt(p.get("created_by_name", "SOAR"), ctx)
                related_transactions = list(p.get("related_transactions", []))
                related_addresses = list(p.get("related_addresses", []))
                tags = list(p.get("tags", []))
                case = case_management_service.create_case(
                    case_type=case_type,
                    title=title,
                    description=desc,
                    customer_id=customer_id,
                    customer_name=customer_name,
                    customer_tier=customer_tier,
                    created_by=created_by,
                    created_by_name=created_by_name,
                    priority=priority,
                    related_transactions=related_transactions,
                    related_addresses=related_addresses,
                    tags=tags,
                )
                res.update({"status": "ok", "case_id": case.case_id})
            elif t == "add_comment":
                case_id = self._fmt(p.get("case_id", ""), ctx)
                comment = self._fmt(p.get("comment", ""), ctx)
                if case_id and comment:
                    case_management_service.add_comment(
                        case_id=case_id,
                        user_id=self._fmt(p.get("user_id", "system"), ctx),
                        user_name=self._fmt(p.get("user_name", "SOAR"), ctx),
                        comment=comment,
                        is_internal=bool(p.get("is_internal", True)),
                    )
                    res.update({"status": "ok"})
            elif t == "update_priority":
                case_id = self._fmt(p.get("case_id", ""), ctx)
                new_prio = CasePriority[p.get("priority", "HIGH").upper()]
                if case_id:
                    case_management_service.update_priority(
                        case_id=case_id,
                        new_priority=new_prio,
                        user_id=self._fmt(p.get("user_id", "system"), ctx),
                        user_name=self._fmt(p.get("user_name", "SOAR"), ctx),
                    )
                    res.update({"status": "ok"})
            else:
                res.update({"status": "unknown_action"})
        except Exception as e:
            res.update({"status": "error", "error": str(e)})
        return res

    def run(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_loaded()
        ctx = {k: v for k, v in (event or {}).items()}
        ctx.setdefault("metadata", event.get("metadata", {}))
        ctx.setdefault("labels", event.get("labels", []))
        matched: List[Dict[str, Any]] = []
        for pb in self._playbooks:
            if not pb.enabled:
                continue
            try:
                ev = _SafeEvaluator(ctx)
                if pb.condition and bool(ev.eval(pb.condition)):
                    actions_res: List[Dict[str, Any]] = []
                    for a in pb.actions:
                        actions_res.append(self._exec_action(a, event, ctx))
                    matched.append({
                        "playbook_id": pb.id,
                        "name": pb.name,
                        "actions": actions_res,
                    })
            except Exception as e:
                logger.debug(f"Playbook error {pb.id}: {e}")
                continue
        return {"matches": matched, "match_count": len(matched)}

    def evaluate_only(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate playbooks without executing actions; returns only matched playbooks."""
        self.ensure_loaded()
        ctx = {k: v for k, v in (event or {}).items()}
        ctx.setdefault("metadata", event.get("metadata", {}))
        ctx.setdefault("labels", event.get("labels", []))
        matched: List[Dict[str, Any]] = []
        for pb in self._playbooks:
            if not pb.enabled:
                continue
            try:
                ev = _SafeEvaluator(ctx)
                if pb.condition and bool(ev.eval(pb.condition)):
                    matched.append({
                        "playbook_id": pb.id,
                        "name": pb.name,
                        "tags": pb.tags,
                    })
            except Exception as e:
                logger.debug(f"Playbook eval error {pb.id}: {e}")
                continue
        return {"matches": matched, "match_count": len(matched)}


soar_engine = SOAREngine()
