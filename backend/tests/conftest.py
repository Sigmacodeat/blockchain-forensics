import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure minimal env for tests
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ENABLE_AI_AGENTS", "true")
os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

# Ensure backend directory is on sys.path so sitecustomize.py is auto-discovered
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Explicitly import sitecustomize to patch bcrypt/passlib behavior under tests
try:
    import sitecustomize  # noqa: F401
except Exception:
    pass

# Force anyio to use asyncio backend only (avoid trio requirement)
@pytest.fixture
def anyio_backend():
    return "asyncio"


# Provide a shared FastAPI TestClient for endpoint tests expecting `client`
@pytest.fixture
def client():
    # Import app lazily to avoid heavy imports during unit-test collection
    from app.main import app as _app
    return TestClient(_app)
