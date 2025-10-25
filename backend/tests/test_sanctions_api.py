import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import importlib.util
from pathlib import Path
from types import ModuleType


def _load_sanctions_router():
    backend_dir = Path(__file__).resolve().parents[1]
    sanc_path = backend_dir / "app" / "api" / "v1" / "sanctions.py"
    # Prepare minimal package hierarchy and inject sanctions_service
    for pkg in ["app", "app.api", "app.api.v1", "app.compliance", "app.compliance.sanctions"]:
        if pkg not in sys.modules:
            sys.modules[pkg] = ModuleType(pkg)
    # Load sanctions service to expose sanctions_service in package
    service_path = backend_dir / "app" / "compliance" / "sanctions" / "service.py"
    spec_service = importlib.util.spec_from_file_location("app.compliance.sanctions.service", service_path)
    service_mod = importlib.util.module_from_spec(spec_service)
    assert spec_service and spec_service.loader
    spec_service.loader.exec_module(service_mod)  # type: ignore
    # Expose sanctions_service at app.compliance.sanctions
    pkg_mod = sys.modules["app.compliance.sanctions"]
    setattr(pkg_mod, "sanctions_service", getattr(service_mod, "sanctions_service"))
    spec = importlib.util.spec_from_file_location("app.api.v1.sanctions", sanc_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    sys.modules["app.api.v1.sanctions"] = mod
    return mod.router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(_load_sanctions_router(), prefix="/api/v1/sanctions")
    return TestClient(app)


def test_stats_contains_optional_fields(client):
    r = client.get("/api/v1/sanctions/stats")
    assert r.status_code == 200
    data = r.json()
    assert "sources" in data and isinstance(data["sources"], list)
    assert "versions" in data and isinstance(data["versions"], dict)
    assert "counts" in data and isinstance(data["counts"], dict)
    # Optional fields now present
    assert "last_updated" in data and isinstance(data["last_updated"], dict)
    assert "totals" in data and isinstance(data["totals"], dict)


def test_webhook_ingest_with_bulk_upsert_stub(client, monkeypatch):
    # Stub bulk_upsert to simulate persistence
    inserted_existing = (2, 1)

    def _bulk_upsert(entries):  # type: ignore
        # Should receive normalized list of dicts
        assert isinstance(entries, list)
        return inserted_existing

    # Patch repo function
    import builtins
    backend_dir = Path(__file__).resolve().parents[1]
    service_path = backend_dir / "app" / "compliance" / "sanctions" / "service.py"
    # Ensure module loaded to pick up stub at runtime
    spec = importlib.util.spec_from_file_location("app.compliance.sanctions.service", service_path)
    service_mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(service_mod)  # type: ignore
    sys.modules["app.compliance.sanctions.service"] = service_mod

    # Patch labels_repo.bulk_upsert symbol resolution inside service at call time
    module_name = "app.repos.labels_repo"
    labels_repo_mod = ModuleType(module_name)
    setattr(labels_repo_mod, "bulk_upsert", _bulk_upsert)
    sys.modules[module_name] = labels_repo_mod

    payload = {
        "chain": "ethereum",
        "label": "sanctioned",
        "category": "OFAC",
        "addresses": ["0xabc", "0xdef", ""]
    }
    r = client.post(
        "/api/v1/sanctions/webhook/ofac",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["inserted"] == inserted_existing[0]
    assert data["existing"] == inserted_existing[1]
    assert data["total"] == 2  # two non-empty addresses
