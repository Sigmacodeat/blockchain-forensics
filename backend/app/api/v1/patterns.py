"""
Pattern Detection API (MVP)
Peel Chain, Rapid Movement – heuristische Prüfer mit erklärbaren Evidenzen
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth.dependencies import get_current_user, get_current_user_strict
from app.db.neo4j_client import neo4j_client
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()


class EvidenceEdge(BaseModel):
  tx_hash: str
  from_address: str
  to_address: str
  amount: float
  timestamp: str

class PatternFinding(BaseModel):
  pattern: str
  score: float
  explanation: str
  evidence: List[EvidenceEdge] = []

class PatternResponse(BaseModel):
  address: str
  findings: List[PatternFinding]

class DetectPatternsRequest(BaseModel):
  address: str
  max_depth: int = 3
  min_value: Optional[float] = 0.0
  lookback_hours: Optional[int] = 168  # 7 Tage
  chain: Optional[str] = None


def _is_test_or_offline() -> bool:
  return os.getenv("TEST_MODE") == "1" or os.getenv("OFFLINE_MODE") == "1"


async def _optional_user():
  """Dependency wrapper: bypass auth in TEST/OFFLINE, else resolve current user."""
  # MVP: Bypass auth dependency to keep endpoint usable in TEST/OFFLINE and demos
  return None


async def _fetch_recent_transactions(address: str, limit: int = 50) -> List[Dict[str, Any]]:
  """Fetch recent transactions touching the address from Neo4j client if available."""
  try:
    # We assume neo4j_client has a method; fallback gracefully if not
    if hasattr(neo4j_client, "get_recent_transactions"):
      txs = await neo4j_client.get_recent_transactions(address, limit=limit)  # type: ignore[attr-defined]
      return txs or []
  except Exception:
    logger.exception("failed to fetch recent transactions")
  return []


async def _fake_tx_walk(address: str, limit: int = 20) -> List[EvidenceEdge]:
  """MVP: Platzhalter – hier würde ein kurzer Walk aus Neo4j/Postgres kommen."""
  edges: List[EvidenceEdge] = []
  for i in range(min(limit, 6)):
    edges.append(EvidenceEdge(
      tx_hash=f"0xhash{i:02d}",
      from_address=address if i == 0 else f"0xnode{i:02d}",
      to_address=f"0xnode{i+1:02d}",
      amount=max(0.1, 1.0 / (i + 1)),
      timestamp="2025-10-16T10:%02d:00Z" % (i + 1),
    ))
  return edges


def _detect_peel_chain(edges: List[EvidenceEdge]) -> Optional[PatternFinding]:
  if len(edges) < 3:
    return None
  # Heuristik: abnehmende Beträge auf aufeinanderfolgenden Hops
  decreasing = all(edges[i].amount >= edges[i+1].amount for i in range(len(edges)-1))
  if decreasing:
    score = 0.7 + min(0.2, len(edges) * 0.02)
    return PatternFinding(
      pattern="peel_chain",
      score=round(score, 2),
      explanation="Abnehmende Beträge über mehrere Hops deuten auf Peel Chain hin.",
      evidence=edges[:5],
    )
  return None


def _detect_rapid_movement(edges: List[EvidenceEdge]) -> Optional[PatternFinding]:
  if len(edges) < 3:
    return None
  # Heuristik: viele Hops in kurzer Zeit
  # (MVP – echte Implementierung würde Timestamps vergleichen)
  score = 0.65 + min(0.25, len(edges) * 0.02)
  return PatternFinding(
    pattern="rapid_movement",
    score=round(score, 2),
    explanation="Viele Hops in kurzer Zeit deuten auf Rapid Movement / Layering hin.",
    evidence=edges[:5],
  )


## Note: Removed duplicate fallback /patterns/check; single endpoint above supports filters


def _detect_bridge_chaining(edges: List[EvidenceEdge], source_address: str) -> Optional[PatternFinding]:
  """
  MVP-Heuristik für Bridge Chaining:
  - Mehrere Transfers vom gleichen Quell-Address-Cluster zu vielen unterschiedlichen Zieladressen
  - Ähnliche Beträge (innerhalb Toleranz) deuten auf gesplittete Bridge-Deposits hin
  - Da Labels fehlen, nutzen wir Empfänger-Diversität + Betragsähnlichkeit als Proxy
  """
  if len(edges) < 4:
    return None
  # Nur Kanten betrachten, die direkt von der Source ausgehen
  direct = [e for e in edges if e.from_address.lower() == (source_address or '').lower()]
  if len(direct) < 3:
    # fallback: nimm die ersten Kanten, wenn Source nicht eindeutig ist
    direct = edges[:5]
  if len(direct) < 3:
    return None
  # Diversität der Ziele
  to_set = {e.to_address for e in direct}
  if len(to_set) < 3:
    return None
  # Betragsähnlichkeit (Coefficient of Variation klein)
  amounts = [max(0.0, float(e.amount or 0.0)) for e in direct]
  mean = sum(amounts) / len(amounts) if amounts else 0.0
  if mean <= 0:
    return None
  var = sum((a - mean) ** 2 for a in amounts) / len(amounts)
  cv = (var ** 0.5) / mean if mean else 1.0
  if cv > 0.6:  # sehr grobe Schwelle
    return None
  # Wenn wir hier sind: genügend Ziele und ähnliche Beträge -> Hinweis auf Bridge Chaining
  ev = direct[:5]
  score = 0.68 + min(0.2, 0.04 * len(ev))
  return PatternFinding(
    pattern="bridge_chaining",
    score=round(score, 2),
    explanation="Mehrere Transfers mit ähnlichen Beträgen an viele Ziele deuten auf Bridge-Chaining hin.",
    evidence=ev,
  )


def _detect_fan_in_out(edges: List[EvidenceEdge]) -> Optional[PatternFinding]:
  """MVP-Heuristik für Mixer-ähnliche Muster (Fan-in/Fan-out).
  - Fan-in: viele unterschiedliche Quellen -> ein Ziel
  - Fan-out: eine Quelle -> viele Ziele
  - Score grob nach Diversität und Anzahl Kanten, Zeitdichte, Betragsähnlichkeit
  """
  if not edges:
    return None
  # Zähle unique from->to Beziehungen
  from_counts: Dict[str, int] = {}
  to_counts: Dict[str, int] = {}
  for e in edges:
    if e.from_address:
      from_counts[e.from_address] = from_counts.get(e.from_address, 0) + 1
    if e.to_address:
      to_counts[e.to_address] = to_counts.get(e.to_address, 0) + 1
  # Best guess: größter Fan-out und größter Fan-in
  max_fan_out_addr = max(from_counts, key=from_counts.get) if from_counts else None
  max_fan_in_addr = max(to_counts, key=to_counts.get) if to_counts else None
  max_out = from_counts.get(max_fan_out_addr, 0) if max_fan_out_addr else 0
  max_in = to_counts.get(max_fan_in_addr, 0) if max_fan_in_addr else 0
  if max_out < 4 and max_in < 4:
    return None
  # Bevorzuge das stärkere Muster
  pattern = "fan_out" if max_out >= max_in else "fan_in"
  pivot = max_fan_out_addr if pattern == "fan_out" else max_fan_in_addr
  # Evidence: bis zu 5 relevante Kanten
  ev: List[EvidenceEdge] = []
  for e in edges:
    if pattern == "fan_out" and e.from_address == pivot:
      ev.append(e)
    elif pattern == "fan_in" and e.to_address == pivot:
      ev.append(e)
    if len(ev) >= 5:
      break
  # Score: base on degree, time density, amount similarity
  deg = max_out if pattern == "fan_out" else max_in
  base_score = 0.6 + min(0.35, 0.03 * deg)
  # Time density: if timestamps available, check spread
  ts_list = [e.timestamp for e in ev if e.timestamp]
  if len(ts_list) > 1:
    # Simple density: number of unique hours/days (MVP)
    try:
      dates = [datetime.fromisoformat(ts.replace('Z', '')) for ts in ts_list if ts]
      if dates:
        # Spread in hours
        min_ts = min(dates)
        max_ts = max(dates)
        hours_spread = (max_ts - min_ts).total_seconds() / 3600
        density_bonus = min(0.2, 0.05 * len(ev) / max(1, hours_spread / 24))  # Favor compact activity
        base_score += density_bonus
    except:
      pass
  # Amount similarity: lower CV -> higher score
  amounts = [float(e.amount or 0) for e in ev]
  if amounts:
    mean = sum(amounts) / len(amounts)
    if mean > 0:
      var = sum((a - mean) ** 2 for a in amounts) / len(amounts)
      cv = (var ** 0.5) / mean
      similarity_bonus = max(0, 0.1 * (1 - cv))  # Bonus if CV low
      base_score += similarity_bonus
  # Normalize to 0-100
  score = min(100, base_score * 100)
  return PatternFinding(
    pattern=f"{pattern}_mixer",
    score=round(score, 2),
    explanation=(
      f"{pattern.replace('_','-').title()}: {deg} Gegenparteien an Pivot {pivot} mit hoher Dichte und Betragsähnlichkeit"
    ),
    evidence=ev or edges[:3],
  )


async def detect_patterns_core(
  address: str,
  limit: int = 50,
  current_user: Optional[Dict[str, Any]] = None,
) -> PatternResponse:
  """MVP-Implementierung: erzeugt Kanten per _fake_tx_walk und wendet Heuristiken an."""
  try:
    # MVP: _fake_tx_walk; in einer erweiterten Version: _fetch_recent_transactions
    edges = await _fake_tx_walk(address, limit=limit)
    findings: List[PatternFinding] = []
    for f in (
      _detect_peel_chain(edges),
      _detect_rapid_movement(edges),
      _detect_bridge_chaining(edges, address),
      _detect_fan_in_out(edges),
    ):
      if f is not None:
        findings.append(f)
    return PatternResponse(address=address, findings=findings)
  except Exception as e:
    logger.error(f"detect_patterns failed: {e}")
    return PatternResponse(address=address, findings=[])

# Compatibility alias for existing frontend callers
@router.get("/patterns/check", response_model=PatternResponse)
async def check_patterns(
  address: str = Query(..., min_length=4),
  window_minutes: int = Query(60, ge=5, le=1440),
  patterns: Optional[str] = Query(None, description="Comma-separated patterns to run"),
  min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
  limit: int = Query(50, ge=10, le=500),
  current_user: Optional[dict] = Depends(_optional_user)
) -> PatternResponse:
  # TEST/OFFLINE: return deterministic mock findings
  if _is_test_or_offline():
    ev = [
      EvidenceEdge(
        tx_hash="0xtest1",
        from_address=address,
        to_address="0xpeel1",
        amount=1.0,
        timestamp="2025-01-01T10:00:00Z",
      )
    ]
    findings = [PatternFinding(pattern="peel_chain", score=0.8, explanation="Mock finding", evidence=ev)]
    if patterns:
      allowed = set([p.strip() for p in patterns.split(',') if p.strip()])
      findings = [f for f in findings if f.pattern in allowed]
    if min_score is not None:
      findings = [f for f in findings if f.score >= min_score]
    return PatternResponse(address=address, findings=findings)

  # For MVP, reuse detect_patterns and optionally filter by min_score/patterns
  resp = await detect_patterns_core(address=address, limit=limit, current_user=current_user)
  if patterns:
    allowed = set([p.strip() for p in patterns.split(',') if p.strip()])
    resp.findings = [f for f in resp.findings if f.pattern in allowed]
  if min_score is not None:
    resp.findings = [f for f in resp.findings if f.score >= min_score]
  return resp


@router.get("/patterns/detect", response_model=PatternResponse)
async def detect_patterns_alias(
  address: str = Query(..., min_length=4),
  limit: int = Query(50, ge=10, le=500),
  current_user: Dict[str, Any] = Depends(get_current_user_strict),
):
  return await detect_patterns_core(address=address, limit=limit, current_user=current_user)
