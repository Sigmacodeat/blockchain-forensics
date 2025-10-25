import os
import json
from pathlib import Path
import pytest

from app.ingest.label_feeds_aggregator import normalize_and_dedupe, fetch_sources, aggregate_label_feeds


def test_normalize_and_dedupe_merges_sources():
    rows = [
        {"chain": "ethereum", "address": "0xabc", "label": "scam", "category": "illicit", "source": "rekt"},
        {"chain": "ethereum", "address": "0xabc", "label": "scam", "category": "illicit", "source": "slowmist"},
    ]
    items, stats = normalize_and_dedupe(rows)
    assert len(items) == 1
    assert stats["unique"] == 1
    # sources dict contains key (chain,address,label) → 2 sources
    assert isinstance(stats.get("sources"), dict)
    assert list(stats["sources"].values())[0] == 2
    assert stats["input"] == 2


@pytest.mark.asyncio
async def test_fetch_sources_from_local_files(tmp_path: Path, monkeypatch):
    # Prepare local feed files under repo data/label_feeds
    repo_root = Path(os.getcwd())
    data_dir = repo_root / "data" / "label_feeds"
    data_dir.mkdir(parents=True, exist_ok=True)
    rekt_path = data_dir / "rekt.json"
    content = [
        {"chain": "Ethereum", "address": "0xAbC", "label": "scam", "category": "illicit"}
    ]
    original = None
    if rekt_path.exists():
        original = rekt_path.read_text(encoding="utf-8")
    try:
        rekt_path.write_text(json.dumps(content), encoding="utf-8")
        res = await fetch_sources(["rekt"])  # only read rekt
        assert isinstance(res, list)
        assert len(res) >= 1
        item = res[0]
        # normalized
        assert item["chain"] == "ethereum"
        assert item["address"] == "0xabc"
        assert item["label"] == "scam"
        assert item["category"] == "generic" or item["category"] == "illicit"
        assert item["source"] == "rekt"
    finally:
        if original is not None:
            rekt_path.write_text(original, encoding="utf-8")
        else:
            try:
                rekt_path.unlink()
            except Exception:
                pass


@pytest.mark.asyncio
async def test_aggregate_label_feeds_best_effort(monkeypatch):
    # No remote, no local; should not fail and return zeroes
    res = await aggregate_label_feeds(["nonexistent_feed"])
    assert "inserted" in res
    assert isinstance(res["inserted"], int)
    assert res["unique"] == 0
    assert res["input"] == 0
