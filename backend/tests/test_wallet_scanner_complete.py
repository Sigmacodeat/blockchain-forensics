"""
Comprehensive tests for Wallet Scanner
"""
import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("TEST_MODE", "1")

from app.main import app
from app.auth.dependencies import get_current_user_strict

# Override auth
app.dependency_overrides[get_current_user_strict] = lambda: {
    "user_id": "test-user",
    "username": "tester",
    "plan": "pro",
}

client = TestClient(app)


@pytest.fixture(autouse=True)
def _bypass_plan(monkeypatch):
    async def _noop(user, plan):
        return None
    monkeypatch.setattr("app.api.v1.wallet_scanner.require_plan", _noop)
    yield


def test_scan_addresses_basic():
    """Test Zero-Trust address scan"""
    resp = client.post("/api/v1/wallet-scanner/scan/addresses", json={
        "addresses": [
            {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"},
        ],
        "check_history": False,
        "check_illicit": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["wallet_type"] == "addresses"
    assert len(data["addresses"]) >= 1


def test_scan_seed_phrase():
    """Test seed phrase scan (with mnemonic lib if available)"""
    resp = client.post("/api/v1/wallet-scanner/scan/seed-phrase", json={
        "seed_phrase": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
        "chains": ["ethereum"],
        "derivation_paths": ["m/44'/60'/0'/0/0"],
        "check_history": False,
        "check_illicit": False,
    })
    # Kann 200 oder 400 sein (je nach lib availability)
    assert resp.status_code in (200, 400)


def test_scan_private_key():
    """Test private key scan"""
    resp = client.post("/api/v1/wallet-scanner/scan/private-key", json={
        "private_key": "0x" + "1" * 64,
        "chain": "ethereum",
        "check_history": False,
        "check_illicit": False,
    })
    # Kann 200 oder 400 sein (je nach lib)
    assert resp.status_code in (200, 400)


def test_report_csv():
    """Test CSV report generation"""
    resp = client.get("/api/v1/wallet-scanner/report/test-scan-123/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


def test_report_pdf():
    """Test PDF (HTML) report generation"""
    resp = client.get("/api/v1/wallet-scanner/report/test-scan-123/pdf")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_report_evidence():
    """Test evidence JSON with signature"""
    resp = client.get("/api/v1/wallet-scanner/report/test-scan-123/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert "evidence_metadata" in data
    assert "sha256_hash" in data["evidence_metadata"]


def test_security_rate_limit():
    """Test rate limiting"""
    from app.services.wallet_scanner_security import wallet_scanner_security
    
    user = "test-rate-limit"
    # Erste 10 Requests OK
    for i in range(10):
        assert wallet_scanner_security.check_rate_limit(user, max_requests=10, window_seconds=60) is True
    
    # 11. Request blockiert
    assert wallet_scanner_security.check_rate_limit(user, max_requests=10, window_seconds=60) is False


def test_security_secret_detection():
    """Test secret detection in inputs"""
    from app.services.wallet_scanner_security import detect_secrets
    
    assert detect_secrets("0x" + "a" * 64) is True  # Private key
    assert detect_secrets("Hello World") is False
    assert detect_secrets("xprv" + "a" * 107) is True  # BIP32 key


def test_advanced_mixer_detection():
    """Test mixer activity detection"""
    from app.services.wallet_scanner_advanced import wallet_scanner_advanced
    import asyncio
    
    result = asyncio.run(wallet_scanner_advanced.detect_mixer_activity(
        address="0x123",
        chain="ethereum",
        transactions=[
            {"to_address": "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc", "timestamp": 1000},
            {"from_address": "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936", "timestamp": 2000},
        ]
    ))
    
    assert result["has_mixer_activity"] is True
    assert "tornado_cash" in result["mixer_protocols"]


def test_advanced_bridge_reconstruction():
    """Test bridge path reconstruction"""
    from app.services.wallet_scanner_advanced import wallet_scanner_advanced
    import asyncio
    
    result = asyncio.run(wallet_scanner_advanced.reconstruct_bridge_path(
        address="0x123",
        chain="ethereum",
        transactions=[
            {"to_address": "0xa0c68c638235ee32657e8f720a23cec1bfc77c77", "value": 1.5},
        ]
    ))
    
    assert len(result) >= 1
    assert result[0]["bridge_protocol"] == "polygon_pos_bridge"
