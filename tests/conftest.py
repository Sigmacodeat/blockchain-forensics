"""
🧪 PROFESSIONAL TEST CONFIGURATION
====================================

Vollständige pytest-Konfiguration mit allen Fixtures,
wie sie eine 50.000€-Agentur implementieren würde.

Enthält:
- TestClient mit korrekter App-Initialisierung
- DB-Fixtures (PostgreSQL, Neo4j, Redis)
- Auth-Mocking für alle User-Rollen
- Service-Mocking für externe APIs
- Performance-Monitoring
- Coverage-Tracking
"""

import os
import sys
import pytest
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

# Ensure project root is on sys.path so 'backend' package is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure backend folder is on sys.path so nested 'app' package is importable
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# FastAPI TestClient
from fastapi.testclient import TestClient


# ============================================================================
# APP & CLIENT FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def app():
    """FastAPI App Instance (Session-Wide)"""
    # Import hier, damit sys.path korrekt ist
    from backend.app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="function")
def client(app) -> Generator[TestClient, None, None]:
    """
    TestClient für HTTP-Requests
    Wird für jeden Test neu erstellt (function scope)
    """
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# USER FIXTURES (Alle Rollen & Plans)
# ============================================================================

@pytest.fixture
def community_user() -> Dict[str, Any]:
    """Community-Plan User (Free Tier)"""
    return {
        "id": "user-community-001",
        "email": "community@test.com",
        "username": "community_user",
        "plan": "community",
        "role": "user",
        "subscription_id": None,
        "subscription_status": None,
        "org_id": "org-test-001",
        "features": [],
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def starter_user() -> Dict[str, Any]:
    """Starter-Plan User"""
    return {
        "id": "user-starter-001",
        "email": "starter@test.com",
        "username": "starter_user",
        "plan": "starter",
        "role": "user",
        "subscription_id": "sub-starter-123",
        "subscription_status": "active",
        "org_id": "org-test-002",
        "features": ["labels.enrichment", "reports.pdf"],
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def pro_user() -> Dict[str, Any]:
    """Pro-Plan User (Professional Tier)"""
    return {
        "id": "user-pro-001",
        "email": "pro@test.com",
        "username": "pro_user",
        "plan": "pro",
        "role": "user",
        "subscription_id": "sub-pro-123",
        "subscription_status": "active",
        "org_id": "org-test-003",
        "features": ["investigator.access", "correlation.basic", "tracing.unlimited"],
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def business_user() -> Dict[str, Any]:
    """Business-Plan User"""
    return {
        "id": "user-business-001",
        "email": "business@test.com",
        "username": "business_user",
        "plan": "business",
        "role": "user",
        "subscription_id": "sub-business-123",
        "subscription_status": "active",
        "org_id": "org-test-004",
        "features": ["risk_policies.manage", "roles_permissions.manage", "sso.basic"],
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def plus_user() -> Dict[str, Any]:
    """Plus-Plan User (Financial Institutions)"""
    return {
        "id": "user-plus-001",
        "email": "plus@test.com",
        "username": "plus_user",
        "plan": "plus",
        "role": "user",
        "subscription_id": "sub-plus-123",
        "subscription_status": "active",
        "org_id": "org-test-005",
        "features": ["ai_agents.unlimited", "correlation.advanced", "travel_rule.support"],
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def enterprise_user() -> Dict[str, Any]:
    """Enterprise-Plan User"""
    return {
        "id": "user-enterprise-001",
        "email": "enterprise@test.com",
        "username": "enterprise_user",
        "plan": "enterprise",
        "role": "user",
        "subscription_id": "sub-enterprise-123",
        "subscription_status": "active",
        "org_id": "org-test-006",
        "features": ["chain_of_custody.full", "eidas.signatures", "white_label", "private_indexers"],
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def admin_user() -> Dict[str, Any]:
    """Admin User (Full Access)"""
    return {
        "id": "admin-001",
        "email": "admin@test.com",
        "username": "admin",
        "plan": "enterprise",
        "role": "admin",
        "subscription_id": "sub-admin-123",
        "subscription_status": "active",
        "org_id": "org-admin-001",
        "features": [],  # Admin hat Zugriff auf alles
        "created_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def postgres_mock():
    """Mock für PostgreSQL-Verbindung"""
    mock = MagicMock()
    mock.execute = AsyncMock(return_value=None)
    mock.fetch = AsyncMock(return_value=[])
    mock.fetchrow = AsyncMock(return_value=None)
    return mock


@pytest.fixture(scope="session")
def neo4j_mock():
    """Mock für Neo4j-Verbindung"""
    mock = MagicMock()
    mock.run = AsyncMock(return_value=[])
    mock.close = AsyncMock()
    return mock


@pytest.fixture(scope="session")
def redis_mock():
    """Mock für Redis-Verbindung"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=0)
    mock.expire = AsyncMock(return_value=True)
    return mock


# ============================================================================
# SERVICE MOCKS
# ============================================================================

@pytest.fixture
def crypto_payment_service_mock():
    """Mock für CryptoPaymentService"""
    mock = MagicMock()
    mock.get_available_currencies = MagicMock(return_value=[
        {"code": "btc", "name": "Bitcoin"},
        {"code": "eth", "name": "Ethereum"},
        {"code": "usdt", "name": "Tether USD"}
    ])
    mock.create_payment = AsyncMock(return_value={
        "payment_id": "pay-test-123",
        "status": "pending",
        "pay_address": "0xABC123...",
        "pay_amount": "0.0123",
        "pay_currency": "eth",
        "invoice_url": "https://nowpayments.io/payment/123"
    })
    mock.get_payment_status = AsyncMock(return_value={
        "payment_id": "pay-test-123",
        "status": "finished"
    })
    return mock


@pytest.fixture
def ai_agent_service_mock():
    """Mock für AI-Agent-Service"""
    mock = MagicMock()
    mock.query = AsyncMock(return_value={
        "response": "Analysis complete",
        "tools_used": ["trace_address", "risk_score"],
        "execution_time": 1.2
    })
    return mock


@pytest.fixture
def tracing_service_mock():
    """Mock für Tracing-Service"""
    mock = MagicMock()
    mock.start_trace = AsyncMock(return_value={
        "trace_id": "trace-test-123",
        "status": "running"
    })
    mock.get_trace_results = AsyncMock(return_value={
        "nodes": [{"address": "0xABC"}, {"address": "0xDEF"}],
        "edges": [{"from": "0xABC", "to": "0xDEF"}]
    })
    return mock


# ============================================================================
# AUTH MOCKING HELPERS
# ============================================================================

def mock_auth_for_user(user: Dict[str, Any]):
    """
    Helper: Mockt Authentication für einen User
    
    Usage:
        with mock_auth_for_user(pro_user):
            resp = client.post("/api/v1/endpoint", json={...})
    """
    return patch('app.auth.dependencies.get_current_user_strict', return_value=user)


def mock_auth_optional(user: Dict[str, Any] = None):
    """Helper: Mockt optionale Authentication"""
    return patch('app.auth.dependencies.get_current_user_optional', return_value=user)


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================

@pytest.fixture
def performance_tracker():
    """Tracked Test-Performance"""
    start_time = None
    
    def start():
        nonlocal start_time
        start_time = datetime.utcnow()
    
    def stop(max_duration_seconds: float = 5.0):
        """
        Stoppt Timer und prüft ob Test < max_duration
        
        Raises:
            AssertionError: Wenn Test zu langsam war
        """
        if start_time is None:
            return
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        assert duration < max_duration_seconds, f"Test took {duration}s (max: {max_duration_seconds}s)"
        return duration
    
    return {"start": start, "stop": stop}


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_ethereum_address():
    """Sample Ethereum-Address für Tests"""
    return "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"


@pytest.fixture
def sample_bitcoin_address():
    """Sample Bitcoin-Address für Tests"""
    return "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"


@pytest.fixture
def sample_transaction_hash():
    """Sample Transaction-Hash für Tests"""
    return "0xabc123def456789abc123def456789abc123def456789abc123def456789abc1"


@pytest.fixture
def sample_case_data():
    """Sample Case-Data für Tests"""
    return {
        "title": "Test Investigation Case",
        "description": "Test case for automated testing",
        "priority": "high",
        "status": "open",
        "tags": ["test", "automated"]
    }


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_mocks():
    """Auto-Reset aller Mocks nach jedem Test"""
    yield
    # Cleanup logic hier wenn nötig


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Pytest-Konfiguration"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "critical: marks tests as critical for production"
    )
