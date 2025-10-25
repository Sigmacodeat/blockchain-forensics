from app.compliance.rule_engine import rule_engine


def test_rule_engine_simple_comparisons():
    expr = {"risk_score": {">=": 0.8}}
    assert rule_engine.evaluate(expr, {"risk_score": 0.85}) is True
    assert rule_engine.evaluate(expr, {"risk_score": 0.5}) is False


def test_rule_engine_nested_any_all_not():
    expr = {
        "all": [
            {"any": [
                {"tx.value_usd": {">=": 10000}},
                {"risk_score": {">=": 0.9}},
            ]},
            {"not": {"counterparty.vasp_trust": {"<": 0.4}}}
        ]
    }
    data_ok = {"tx": {"value_usd": 20000}, "counterparty": {"vasp_trust": 0.5}}
    data_fail = {"tx": {"value_usd": 5000}, "risk_score": 0.2, "counterparty": {"vasp_trust": 0.9}}
    assert rule_engine.evaluate(expr, data_ok) is True
    assert rule_engine.evaluate(expr, data_fail) is False


def test_rule_engine_literal_equality():
    expr = {"ofac_match": True}
    assert rule_engine.evaluate(expr, {"ofac_match": True}) is True
    assert rule_engine.evaluate(expr, {"ofac_match": False}) is False
