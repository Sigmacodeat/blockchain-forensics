"""
Chain-of-Thought Investigator (Planner → Tracer → Verifier)
===========================================================

Leichtgewichtige Multi-Agent Pipeline, die vorhandene Tools nutzt
(`app/ai_agents/tools.py`) und ohne harte LLM-Abhängigkeit lauffähig ist.

Ziel:
- Plan generieren (Was ist zu tun?)
- Tracing ausführen (Tool-gestützt)
- Verifizieren und Score/Confidence aggregieren
- Artefakte für Cases zurückgeben
"""
from __future__ import annotations
import time
from typing import List, Dict, Any, Optional

from app.ai_agents.tools import trace_address_tool, risk_score_tool, bridge_lookup_tool


class PlannerAgent:
    """Heuristische Planung basierend auf Seed-Inputs"""
    def plan(self, seed_addresses: List[str], max_depth: int = 4) -> List[Dict[str, Any]]:
        steps: List[Dict[str, Any]] = []
        for addr in seed_addresses:
            steps.append({
                "type": "trace",
                "address": addr,
                "max_depth": max_depth,
                "enable_native": True,
                "enable_token": True,
                "enable_bridge": True,
                "enable_utxo": True,
            })
            steps.append({
                "type": "risk_score",
                "address": addr,
            })
        return steps


class TracerAgent:
    """Führt Trace/Risk/Bridge-Schritte mit vorhandenen Tools aus"""
    async def execute(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        outputs: List[Dict[str, Any]] = []
        for step in steps:
            stype = step.get("type")
            if stype == "trace":
                payload = {
                    "address": step["address"],
                    "max_depth": step.get("max_depth", 4),
                    "direction": "forward",
                    "enable_native": step.get("enable_native", True),
                    "enable_token": step.get("enable_token", True),
                    "enable_bridge": step.get("enable_bridge", True),
                    "enable_utxo": step.get("enable_utxo", True),
                    "max_nodes": 1000,
                }
                out = await trace_address_tool.ainvoke(payload)
                outputs.append({"step": step, "result": out})
            elif stype == "risk_score":
                out = await risk_score_tool.ainvoke({"address": step["address"]})
                outputs.append({"step": step, "result": out})
            elif stype == "bridge_lookup":
                out = await bridge_lookup_tool.ainvoke({
                    "chain": step.get("chain"),
                    "address": step.get("address"),
                    "method_selector": step.get("method_selector"),
                })
                outputs.append({"step": step, "result": out})
        return outputs


class VerifierAgent:
    """Aggregiert Ergebnisse zu Confidence & Findings"""
    def verify(self, execution: List[Dict[str, Any]]) -> Dict[str, Any]:
        risk_scores: List[float] = []
        high_risk_addresses: List[str] = []
        traces: List[Dict[str, Any]] = []
        for item in execution:
            step = item.get("step", {})
            res = item.get("result", {})
            if step.get("type") == "risk_score":
                score = float(res.get("risk_score", 0.0))
                risk_scores.append(score)
                if score >= 0.7 and step.get("address"):
                    high_risk_addresses.append(step["address"])
            if step.get("type") == "trace":
                traces.append(res)
        avg_risk = sum(risk_scores)/len(risk_scores) if risk_scores else 0.0
        confidence = min(1.0, 0.5 + 0.5 * avg_risk)
        return {
            "avg_risk": avg_risk,
            "confidence": confidence,
            "high_risk": list(sorted(set(high_risk_addresses))),
            "trace_count": len(traces),
        }


class CoTInvestigator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.tracer = TracerAgent()
        self.verifier = VerifierAgent()

    async def run(self,
                  seed_addresses: List[str],
                  max_depth: int = 4,
                  case_id: Optional[str] = None) -> Dict[str, Any]:
        t0 = time.time()
        plan = self.planner.plan(seed_addresses, max_depth=max_depth)
        execution = await self.tracer.execute(plan)
        verdict = self.verifier.verify(execution)
        return {
            "plan": plan,
            "execution": execution,
            "verdict": verdict,
            "case_id": case_id,
            "took": time.time() - t0,
        }


# Singleton helper
_cot: Optional[CoTInvestigator] = None

def get_cot() -> CoTInvestigator:
    global _cot
    if _cot is None:
        _cot = CoTInvestigator()
    return _cot
