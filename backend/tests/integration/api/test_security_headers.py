from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import SecurityHeadersMiddleware


def _build_app(enable_hsts: bool) -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return app


def test_security_headers_present_without_hsts():
    app = _build_app(enable_hsts=False)
    client = TestClient(app)

    r = client.get("/ping")
    assert r.status_code == 200

    # Core headers
    assert r.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"

    # CSP present and reasonably strict
    csp = r.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp

    # Permissions-Policy present
    pp = r.headers.get("Permissions-Policy")
    assert pp is not None
    assert "geolocation=()" in pp

    # HSTS not present when disabled
    assert "Strict-Transport-Security" not in r.headers


def test_hsts_enabled_over_https():
    app = _build_app(enable_hsts=True)
    client = TestClient(app, base_url="https://testserver")

    r = client.get("/ping")
    assert r.status_code == 200

    # HSTS present only when https scheme
    sts = r.headers.get("Strict-Transport-Security")
    assert sts is not None
    assert "max-age=" in sts
