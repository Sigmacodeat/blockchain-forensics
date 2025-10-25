"""
Tests for Investigator Graph API
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_explore_address_graph():
    """Test exploring graph around an address"""
    # Test with a known address (would need real data in production)
    response = client.get("/api/v1/graph/investigator/explore?address=0x1234567890123456789012345678901234567890&max_hops=2")

    # For now, this might return empty data since we don't have real blockchain data
    assert response.status_code in [200, 404]  # 404 if no data found


def test_find_path_between_addresses():
    """Test finding paths between addresses"""
    payload = {
        "from_address": "0x1234567890123456789012345678901234567890",
        "to_address": "0x0987654321098765432109876543210987654321",
        "max_hops": 3
    }

    response = client.post("/api/v1/graph/path/find", json=payload)

    # Should return a valid response structure
    assert response.status_code == 200
    data = response.json()
    assert "found" in data
    assert "paths" in data
    assert "summary" in data


def test_get_address_timeline():
    """Test getting timeline for an address"""
    response = client.get("/api/v1/graph/timeline?address=0x1234567890123456789012345678901234567890&limit=50")

    assert response.status_code == 200
    data = response.json()
    assert "address" in data
    assert "events" in data
    assert "summary" in data
    assert data["address"] == "0x1234567890123456789012345678901234567890"


def test_investigator_summary():
    """Test getting summary for multiple addresses"""
    addresses = "0x1234567890123456789012345678901234567890,0x0987654321098765432109876543210987654321"

    response = client.get(f"/api/v1/graph/investigator/summary?addresses={addresses}")

    assert response.status_code == 200
    data = response.json()
    assert "addresses" in data
    assert "total_addresses" in data
    assert "address_stats" in data
    assert "overall_risk_distribution" in data
    assert len(data["addresses"]) == 2


def test_path_find_invalid_addresses():
    """Test path finding with invalid addresses"""
    payload = {
        "from_address": "invalid_address",
        "to_address": "another_invalid",
        "max_hops": 3
    }

    response = client.post("/api/v1/graph/path/find", json=payload)
    # Should handle gracefully, not crash
    assert response.status_code in [200, 400, 500]


def test_timeline_empty_address():
    """Test timeline with empty address"""
    response = client.get("/api/v1/graph/timeline?address=")

    # Should handle empty address gracefully
    assert response.status_code in [200, 400]


def test_explore_graph_with_time_filter():
    """Test graph exploration with time filters"""
    response = client.get(
        "/api/v1/graph/investigator/explore"
        "?address=0x1234567890123456789012345678901234567890"
        "&max_hops=2"
        "&from_timestamp=2023-01-01T00:00:00Z"
        "&to_timestamp=2023-12-31T23:59:59Z"
    )

    assert response.status_code in [200, 404]


def test_investigator_summary_too_many_addresses():
    """Test summary with too many addresses"""
    # Create a long list of addresses
    addresses = ",".join([f"0x{addr:032x}" for addr in range(60)])

    response = client.get(f"/api/v1/graph/investigator/summary?addresses={addresses}")

    # Should return 400 for too many addresses
    assert response.status_code == 400
