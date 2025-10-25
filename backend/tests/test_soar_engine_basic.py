from app.services.soar_engine import SOAREngine
from app.services.case_management import case_management_service


def setup_function():
    # reset cases between tests
    case_management_service.cases.clear()


def test_playbooks_load_and_list():
    eng = SOAREngine()
    cnt = eng.load_playbooks()
    pbs = eng.list_playbooks()
    assert isinstance(cnt, int)
    assert cnt >= 3
    assert len(pbs) >= 3


def test_run_large_value_creates_case():
    eng = SOAREngine()
    eng.load_playbooks()
    evt = {
        "address": "0xabc",
        "value_usd": 20000,
        "metadata": {},
        "labels": [],
    }
    res = eng.run(evt)
    assert res["match_count"] >= 1
    # At least one action should be ok
    actions = [a for m in res.get("matches", []) for a in m.get("actions", [])]
    assert any(a.get("status") == "ok" for a in actions)
    # Case should exist
    assert len(case_management_service.cases) == 1


def test_run_sanctions_creates_case():
    eng = SOAREngine()
    eng.load_playbooks()
    evt = {
        "address": "0xdef",
        "metadata": {"counterparty_risk": 0.95},
        "labels": [],
    }
    res = eng.run(evt)
    assert res["match_count"] >= 1
    assert len(case_management_service.cases) == 1


def test_run_mev_creates_case():
    eng = SOAREngine()
    eng.load_playbooks()
    evt = {
        "address": "0xmev",
        "metadata": {"mev": {"sandwich_score": 0.75}},
        "labels": [],
    }
    res = eng.run(evt)
    assert res["match_count"] >= 1
    assert len(case_management_service.cases) == 1
