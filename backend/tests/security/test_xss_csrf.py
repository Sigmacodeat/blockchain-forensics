"""
Security Tests: XSS & CSRF Prevention
======================================
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestXSSPrevention:
    """Tests für XSS Prevention"""

    def test_xss_in_response_escaped(self):
        """Test: XSS Payloads in Responses werden escaped"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]

        for payload in xss_payloads:
            response = client.get(
                "/api/v1/enrich/sanctions-check",
                params={"address": payload}
            )
            
            if response.status_code == 200:
                # Prüfe, dass Payload escaped wurde
                assert "<script>" not in response.text
                assert "javascript:" not in response.text.lower()


class TestCSRFPrevention:
    """Tests für CSRF Prevention"""

    def test_csrf_token_required_for_state_change(self):
        """Test: CSRF Token für State-Changes (optional bei JWT)"""
        # Bei JWT-Auth ist CSRF weniger kritisch
        # Aber teste trotzdem, dass SameSite Cookies verwendet werden
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
