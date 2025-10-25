"""
Tests for Risk Streaming SSE Endpoint
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)


def test_risk_stream_valid_ethereum_address():
    """Test SSE stream with valid Ethereum address"""
    # Valid Ethereum address
    with client.stream(
        "GET",
        "/api/v1/risk/stream",
        params={"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        # Collect events
        events = []
        event_type = None
        for line in response.iter_lines():
            line_str = line.strip()
            if line_str.startswith("event:"):
                event_type = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("data:"):
                data = json.loads(line_str.split(":", 1)[1].strip())
                events.append({"type": event_type, "data": data})
        
        # Check event sequence
        assert len(events) >= 2  # At least ready + result or error
        assert events[0]["type"] == "risk.ready"
        assert events[0]["data"]["ok"] is True
        
        # Should eventually get a result
        result_events = [e for e in events if e["type"] == "risk.result"]
        if result_events:
            result = result_events[0]["data"]
            assert "chain" in result
            assert "address" in result
            assert "score" in result
            assert isinstance(result["score"], (int, float))


def test_risk_stream_invalid_ethereum_address():
    """Test SSE stream with invalid Ethereum address"""
    with client.stream(
        "GET",
        "/api/v1/risk/stream",
        params={"chain": "ethereum", "address": "not_an_address"},
    ) as response:
        assert response.status_code == 200
        
        # Collect events
        events = []
        event_type = None
        for line in response.iter_lines():
            line_str = line.strip()
            if line_str.startswith("event:"):
                event_type = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("data:"):
                data = json.loads(line_str.split(":", 1)[1].strip())
                events.append({"type": event_type, "data": data})
        
        # Should get ready + error
        assert len(events) >= 2
        assert events[0]["type"] == "risk.ready"
        
        error_events = [e for e in events if e["type"] == "risk.error"]
        assert len(error_events) > 0
        assert error_events[0]["data"]["detail"] == "invalid_address"


def test_risk_stream_missing_params():
    """Test SSE stream with missing parameters"""
    response = client.get("/api/v1/risk/stream")
    assert response.status_code == 422  # Validation error


def test_risk_stream_rate_limiting():
    """Test rate limiting on risk stream endpoint"""
    # Make many requests quickly to trigger rate limit
    valid_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    
    rate_limited_count = 0
    for _ in range(65):  # Exceed default 60/min limit
        resp = client.get(
            "/api/v1/risk/stream",
            params={"chain": "ethereum", "address": valid_address},
        )
        if resp.status_code == 429:
            rate_limited_count += 1
            # Check Retry-After header
            assert "retry-after" in resp.headers
            break
    
    # At least one should be rate limited
    assert rate_limited_count > 0


def test_risk_stream_bitcoin_chain():
    """Test SSE stream with Bitcoin chain (no validation yet)"""
    with client.stream(
        "GET",
        "/api/v1/risk/stream",
        params={"chain": "bitcoin", "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"},
    ) as response:
        assert response.status_code == 200
        # Bitcoin validation not yet implemented, so should proceed
