"""
Tests for Multi-List Sanctions Screening
"""
import os
from fastapi.testclient import TestClient

os.environ["TEST_MODE"] = "1"

from app.main import app

client = TestClient(app)


def test_sanctions_screen_multi_basic():
    """Test basic multi-address screening"""
    payload = {
        "addresses": ["0x1234567890123456789012345678901234567890", "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"],
        "sources": ["ofac", "un"]
    }
    response = client.post("/api/v1/sanctions/screen/multi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    for item in data:
        assert "address" in item
        assert "is_sanctioned" in item
        assert "matches" in item
        assert "screened_at" in item


def test_sanctions_screen_multi_empty_addresses():
    """Test with empty addresses list"""
    payload = {"addresses": [], "sources": ["ofac"]}
    response = client.post("/api/v1/sanctions/screen/multi", json=payload)
    # Backend returns empty list for empty input
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_sanctions_screen_multi_all_sources():
    """Test with all available sources"""
    payload = {
        "addresses": ["0x1111111111111111111111111111111111111111"],
        "sources": ["ofac", "un", "eu", "uk"]
    }
    response = client.post("/api/v1/sanctions/screen/multi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["address"].lower() == "0x1111111111111111111111111111111111111111"


def test_sanctions_screen_multi_invalid_source():
    """Test with invalid source"""
    payload = {
        "addresses": ["0x1234567890123456789012345678901234567890"],
        "sources": ["invalid_source"]
    }
    response = client.post("/api/v1/sanctions/screen/multi", json=payload)
    # Should either reject or ignore invalid source
    assert response.status_code in [200, 400, 422]


def test_sanctions_screen_multi_large_batch():
    """Test with larger batch of addresses"""
    addresses = [f"0x{'1234' * 10}{str(i).zfill(8)}" for i in range(50)]
    payload = {"addresses": addresses, "sources": ["ofac"]}
    response = client.post("/api/v1/sanctions/screen/multi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 50


def test_sanctions_screen_multi_response_structure():
    """Test response structure matches SanctionsScreeningResult"""
    payload = {
        "addresses": ["0xTest1234567890123456789012345678901234"],
        "sources": ["ofac"]
    }
    response = client.post("/api/v1/sanctions/screen/multi", json=payload)
    assert response.status_code == 200
    data = response.json()
    result = data[0]
    # Check all required fields
    assert "address" in result
    assert "is_sanctioned" in result
    assert isinstance(result["is_sanctioned"], bool)
    assert "matches" in result
    assert isinstance(result["matches"], list)
    assert "overall_risk" in result
    assert result["overall_risk"] in ["LOW", "MEDIUM", "HIGH"]
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)
    assert "screened_at" in result
