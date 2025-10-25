"""
Security Tests: SQL Injection Prevention
==========================================
Testet ob die Anwendung gegen SQL Injection geschützt ist.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestSQLInjectionPrevention:
    """Tests für SQL Injection Prevention"""

    def test_sql_injection_in_address_param(self):
        """Test: SQL Injection in Address-Parameter"""
        malicious_payloads = [
            "0x123' OR '1'='1",
            "0x123'; DROP TABLE users; --",
            "0x123' UNION SELECT * FROM users --",
            "' OR 1=1 --",
            "1' AND 1=(SELECT COUNT(*) FROM users) --",
        ]

        for payload in malicious_payloads:
            response = client.get(
                "/api/v1/enrich/sanctions-check",
                params={"address": payload}
            )
            # Sollte entweder 400 (Validation Error) oder 200 (safe handling) sein
            # Aber NIE 500 (Server Error durch SQL Injection)
            assert response.status_code in [200, 400, 422], \
                f"SQL Injection Payload caused unexpected status: {payload}"
            
            # Prüfe, dass keine SQL-Error-Messages in Response
            response_text = response.text.lower()
            assert "sql" not in response_text
            assert "syntax error" not in response_text
            assert "database" not in response_text

    def test_sql_injection_in_trace_request(self):
        """Test: SQL Injection in Trace-Request"""
        malicious_payload = {
            "source_address": "0x123' OR '1'='1 --",
            "direction": "forward",
            "max_depth": 3,
            "taint_model": "proportional"
        }

        response = client.post("/api/v1/trace/start", json=malicious_payload)
        
        # Sollte Validation Error sein
        assert response.status_code in [400, 422]
        
        # Keine SQL-Fehler
        assert "sql" not in response.text.lower()

    def test_sql_injection_in_user_query(self):
        """Test: SQL Injection in User-Suche (wenn implementiert)"""
        malicious_queries = [
            "admin' --",
            "' OR '1'='1",
            "'; DROP TABLE users; --"
        ]

        for query in malicious_queries:
            # Falls User-Suche existiert
            response = client.get(
                "/api/v1/users/search",
                params={"q": query}
            )
            
            # Sollte safe sein
            assert response.status_code in [200, 400, 401, 403, 404, 422]
            assert response.status_code != 500

    def test_parameterized_queries_in_audit_log(self):
        """Test: Parameterized Queries in Audit Logs"""
        # Simuliere Audit-Log mit potentiell gefährlichen Daten
        malicious_action = "'; DROP TABLE audit_logs; --"
        
        # Wenn Audit-Log-Abfrage existiert
        # (Dieser Test prüft indirekt, ob parameterized queries verwendet werden)
        response = client.get(
            "/api/v1/audit/logs",
            params={"action": malicious_action}
        )
        
        # Sollte entweder authorized reject oder safe handling sein
        assert response.status_code in [200, 400, 401, 403, 422]
        assert response.status_code != 500

    def test_no_sql_error_leakage(self):
        """Test: Keine SQL-Fehler in Responses"""
        # Teste mit verschiedenen malformed inputs
        test_cases = [
            ("/api/v1/trace/unknown-id-with-'-quote", "get"),
            ("/api/v1/enrich/labels", "post", {"address": "'; SELECT * FROM users --"}),
        ]

        for test_case in test_cases:
            if len(test_case) == 2:
                endpoint, method = test_case
                if method == "get":
                    response = client.get(endpoint)
            else:
                endpoint, method, data = test_case
                response = client.post(endpoint, json=data)

            # Prüfe, dass keine internen DB-Fehler geleakt werden
            if response.status_code >= 400:
                response_body = response.json() if response.headers.get('content-type') == 'application/json' else {}
                
                # Keine technischen Details in Error Messages
                error_text = str(response_body).lower()
                assert "sqlalchemy" not in error_text
                assert "postgres" not in error_text
                assert "table" not in error_text
                assert "column" not in error_text


class TestORMSecurityBestPractices:
    """Tests für ORM Security Best Practices"""

    def test_no_raw_sql_execution(self):
        """Test: Keine Raw SQL Execution (wird durch Code-Review geprüft)"""
        # Dieser Test ist dokumentierend - echte Prüfung erfolgt durch Bandit/Semgrep
        # Hier nur als Reminder für Security Audit
        pass

    def test_input_validation_on_all_endpoints(self):
        """Test: Input Validation auf allen Endpoints"""
        # Teste verschiedene Endpoints mit invalid input
        invalid_inputs = [
            {"endpoint": "/api/v1/trace/start", "data": {"source_address": "not-an-address"}},
            {"endpoint": "/api/v1/enrich/labels", "data": {"address": "invalid"}},
        ]

        for test in invalid_inputs:
            response = client.post(test["endpoint"], json=test["data"])
            # Sollte Validation Error sein
            assert response.status_code in [400, 422], \
                f"Endpoint {test['endpoint']} akzeptiert invalid input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
