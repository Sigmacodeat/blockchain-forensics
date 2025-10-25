
from app.services.typology_engine import TypologyEngine, typology_engine


def test_typology_rules_loading():
    # Ensure default engine can load rules without exception
    cnt = typology_engine.load_rules()
    assert isinstance(cnt, int)
    # We expect at least the 3 sample rules to be present
    assert cnt >= 3


def test_evaluate_large_value_match():
    engine = TypologyEngine()
    engine.load_rules()
    evt = {"value_usd": 15000, "metadata": {}, "labels": []}
    matches = engine.evaluate(evt)
    ids = {m.get("id") for m in matches}
    assert "TYP-001" in ids  # Large Value Transfer


def test_evaluate_sanctions_counterparty_match():
    engine = TypologyEngine()
    engine.load_rules()
    evt = {"metadata": {"counterparty_risk": 0.95}, "labels": []}
    matches = engine.evaluate(evt)
    ids = {m.get("id") for m in matches}
    assert "TYP-002" in ids  # Sanctions Counterparty


def test_evaluate_dex_sandwich_match():
    engine = TypologyEngine()
    engine.load_rules()
    evt = {"metadata": {"mev": {"sandwich_score": 0.8}}, "labels": []}
    matches = engine.evaluate(evt)
    ids = {m.get("id") for m in matches}
    assert "TYP-003" in ids  # DEX Sandwich Pattern
