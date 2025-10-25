from __future__ import annotations
import os
import glob
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import ast


class Rule(BaseModel):
    id: str
    name: str
    version: str | int = "1"
    severity: str = "medium"
    enabled: bool = True
    variant: Optional[str] = None
    condition: str
    tags: List[str] = []


class _SafeEvaluator(ast.NodeVisitor):
    ALLOWED_NODES = (
        ast.Expression,
        ast.BoolOp,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.List,
        ast.Tuple,
        ast.Dict,
        ast.Subscript,
        ast.Index,  # py<3.9
        ast.And,
        ast.Or,
        ast.Not,
        ast.In,
        ast.NotIn,
        ast.Is,
        ast.IsNot,
        ast.Eq,
        ast.NotEq,
        ast.Gt,
        ast.GtE,
        ast.Lt,
        ast.LtE,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.USub,
    )

    def __init__(self, ctx: Dict[str, Any]):
        self.ctx = ctx

    def visit(self, node):  # type: ignore[override]
        if not isinstance(node, self.ALLOWED_NODES):
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")
        return super().visit(node)

    def eval(self, expr: str) -> Any:
        tree = ast.parse(expr, mode="eval")
        self.visit(tree)
        code = compile(tree, filename="<expr>", mode="eval")
        return eval(code, {"__builtins__": {}}, self.ctx)


class TypologyEngine:
    def __init__(self, rules_dir: Optional[str] = None) -> None:
        base = os.getcwd()
        self.rules_dir = rules_dir or os.path.join(base, "backend", "app", "policies", "typologies")
        self._rules: List[Rule] = []
        self._loaded = False

    def load_rules(self) -> int:
        self._rules = []
        # Lazy import to avoid hard dependency if YAML isn't installed in some test contexts
        try:
            import yaml  # type: ignore
        except Exception:
            self._loaded = True
            return 0
        pattern = os.path.join(self.rules_dir, "*.yaml")
        for path in glob.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if isinstance(data, dict) and data.get("rules"):
                    for r in data.get("rules", []):
                        try:
                            rule = Rule(**r)
                            if rule.enabled:
                                self._rules.append(rule)
                        except Exception:
                            continue
                elif isinstance(data, list):
                    for r in data:
                        try:
                            rule = Rule(**r)
                            if rule.enabled:
                                self._rules.append(rule)
                        except Exception:
                            continue
            except Exception:
                continue
        self._loaded = True
        return len(self._rules)

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_rules()

    def list_rules(self, variant: Optional[str] = None) -> List[Dict[str, Any]]:
        self.ensure_loaded()
        res: List[Dict[str, Any]] = []
        for r in self._rules:
            if variant and r.variant and r.variant != variant:
                continue
            res.append({
                "id": r.id,
                "name": r.name,
                "version": r.version,
                "severity": r.severity,
                "enabled": r.enabled,
                "variant": r.variant,
                "tags": r.tags,
            })
        return res

    def evaluate(self, event: Dict[str, Any], variant: Optional[str] = None) -> List[Dict[str, Any]]:
        self.ensure_loaded()
        ctx = {k: v for k, v in (event or {}).items()}
        # convenience aliases
        ctx.setdefault("metadata", event.get("metadata", {}))
        ctx.setdefault("labels", event.get("labels", []))
        matches: List[Dict[str, Any]] = []
        for r in self._rules:
            if variant and r.variant and r.variant != variant:
                continue
            try:
                ev = _SafeEvaluator(ctx)
                ok = bool(ev.eval(r.condition))
                if ok:
                    matches.append({
                        "id": r.id,
                        "name": r.name,
                        "severity": r.severity,
                        "version": r.version,
                        "tags": r.tags,
                    })
            except Exception:
                continue
        return matches


typology_engine = TypologyEngine()
