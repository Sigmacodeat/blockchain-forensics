import json
from typing import Any, Dict, List


def test_get_registry_protocols(client):
    resp = client.get("/api/v1/defi/registry/protocols")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # expect at least core protocols we seeded
    slugs = {p.get("slug") for p in data if isinstance(p, dict)}
    assert {"uniswap-v3", "curve", "aave"}.issubset(slugs)


def test_get_registry_labels_preview_default_limit(client, monkeypatch, tmp_path):
    # Ensure we can preview even without external sources
    # If external sources are configured elsewhere, this still should work
    if "DEFI_PROTOCOL_CONTRACT_SOURCES" in client.app.state.__dict__:
        pass
    resp = client.get("/api/v1/defi/registry/labels/preview")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "total" in data and "items" in data
    assert isinstance(data["items"], list)
    # items are label dicts when sources exist, may be empty otherwise


def test_get_registry_labels_preview_with_limit(client, monkeypatch, tmp_path):
    # Create a temporary external contracts file to populate preview
    items: List[Dict[str, Any]] = [
        {"slug": "uniswap-v3", "chain": "ethereum", "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "label": "Uniswap V3 USDC/WETH 0.05%"},
        {"slug": "aave", "chain": "ethereum", "address": "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9", "label": "Aave V2 LendingPool"},
        {"slug": "curve", "chain": "ethereum", "address": "0xa5407eae9ba41422680e2e00537571bcc53efbfd", "label": "Curve 3pool"},
    ]
    f = tmp_path / "defi.json"
    f.write_text(json.dumps(items), encoding="utf-8")

    import os
    os.environ["DEFI_PROTOCOL_CONTRACT_SOURCES"] = json.dumps([str(f)])

    resp = client.get("/api/v1/defi/registry/labels/preview?limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert data["total"] >= 2
    assert all(isinstance(x, dict) for x in data["items"])
