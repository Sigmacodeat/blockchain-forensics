from __future__ import annotations
from typing import Any, Dict, Mapping


class RuleEngine:
    """JSON-DSL Rule Evaluator (MVP) supporting any/all/not and comparisons."""

    def _get(self, data: Mapping[str, Any], path: str) -> Any:
        cur: Any = data
        for part in path.split('.'):
            if isinstance(cur, Mapping) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    def _cmp(self, left: Any, op_map: Mapping[str, Any]) -> bool:
        for op, rhs in op_map.items():
            if op == ">":
                if not (left is not None and left > rhs):
                    return False
            elif op == ">=":
                if not (left is not None and left >= rhs):
                    return False
            elif op == "<":
                if not (left is not None and left < rhs):
                    return False
            elif op == "<=":
                if not (left is not None and left <= rhs):
                    return False
            elif op == "==":
                if not (left == rhs):
                    return False
            else:
                return False
        return True

    def _eval_node(self, node: Any, data: Mapping[str, Any]) -> bool:
        if isinstance(node, Mapping):
            if "all" in node:
                items = node["all"] or []
                return all(self._eval_node(x, data) for x in items)
            if "any" in node:
                items = node["any"] or []
                return any(self._eval_node(x, data) for x in items)
            if "not" in node:
                return not self._eval_node(node["not"], data)
            # field comparison: {"field.path": {">=": 1}}
            if len(node) == 1:
                field, cmp_map = next(iter(node.items()))
                val = self._get(data, field)
                if isinstance(cmp_map, Mapping):
                    return self._cmp(val, cmp_map)
                # literal equality
                return val == cmp_map
        return bool(node)

    def evaluate(self, expression: Dict[str, Any], data: Mapping[str, Any]) -> bool:
        return self._eval_node(expression, data)


rule_engine = RuleEngine()
