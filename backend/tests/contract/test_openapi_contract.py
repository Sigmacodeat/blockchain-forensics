import os
import yaml
import pytest

OPENAPI_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "openapi.yaml")


def load_openapi():
    with open(OPENAPI_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_openapi_file_exists():
    assert os.path.exists(OPENAPI_PATH), f"OpenAPI file not found at {OPENAPI_PATH}"


def test_core_paths_present():
    spec = load_openapi()
    assert "paths" in spec and isinstance(spec["paths"], dict)

    # Minimal contract: core domains present (adjust as API evolves)
    required_path_prefixes = [
        "/api/v1/trace",
        "/api/v1/risk",
        "/api/v1/alerts",
        "/api/v1/cases",
    ]

    paths = list(spec["paths"].keys())
    for prefix in required_path_prefixes:
        assert any(p.startswith(prefix) for p in paths), f"Missing any path starting with {prefix}"


@pytest.mark.parametrize("path,methods", [
    ("/api/v1/trace/start", ["post"]),
    ("/api/v1/risk/score", ["get"]),
])
def test_specific_endpoints_declared(path, methods):
    spec = load_openapi()
    paths = spec.get("paths", {})
    assert path in paths, f"Expected path {path} not declared in OpenAPI"
    declared = set(paths[path].keys())
    for m in methods:
        assert m in declared, f"Method {m} not declared for {path}"
