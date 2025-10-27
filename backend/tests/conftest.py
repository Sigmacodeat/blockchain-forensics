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


@pytest.fixture
def auth_headers(client):
    """Fixture: Auth Headers for authenticated requests"""
    # Login as test user
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "test123"
        }
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        return {}


@pytest.fixture
def test_user(client):
    """Fixture: Create and return a test user"""
    from app.db.session import get_db_session
    from app.models.user import UserORM
    from app.core.security import get_password_hash

    db = get_db_session()
    try:
        # Check if test user already exists
        user = db.query(UserORM).filter(UserORM.email == "test@example.com").first()
        if not user:
            # Create test user
            user = UserORM(
                email="test@example.com",
                username="testuser",
                hashed_password=get_password_hash("test123"),
                role="user",
                plan="community",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()
