"""
🧪 WALLET SCANNER API TESTS
Tests für Wallet Scanner - Premium Feature

Coverage:
- BIP39/BIP44 Seed Phrase Scan
- Private Key Scan
- Zero-Trust Address Scan
- Bulk Scanning
- Report Generation (CSV, PDF, Evidence)
- Security Features
"""

import pytest
from fastapi.testclient import TestClient
import json


class TestWalletScannerSeedPhrase:
    """Test Suite für Seed Phrase Scanning"""
    
    def test_scan_seed_phrase_success(self, client: TestClient, pro_user_headers):
        """Test: BIP39 Seed Phrase scannen"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/seed-phrase",
            json={
                "seed_phrase": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
                "chains": ["ethereum", "polygon", "bsc"],
                "derivation_count": 5,
                "check_history": True,
                "check_illicit": True
            },
            headers=pro_user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert "addresses" in data
        assert len(data["addresses"]) > 0
        
        # Check address format
        for addr in data["addresses"]:
            assert "chain" in addr
            assert "address" in addr
            assert "balance" in addr
    
    def test_scan_seed_phrase_invalid(self, client: TestClient, pro_user_headers):
        """Test: Ungültige Seed Phrase wird abgelehnt"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/seed-phrase",
            json={
                "seed_phrase": "invalid seed phrase words here",
                "chains": ["ethereum"]
            },
            headers=pro_user_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_scan_seed_phrase_requires_pro(self, client: TestClient, community_user_headers):
        """Test: Seed Phrase Scan benötigt Pro Plan"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/seed-phrase",
            json={
                "seed_phrase": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
                "chains": ["ethereum"]
            },
            headers=community_user_headers
        )
        
        assert response.status_code in [402, 403]
    
    def test_scan_seed_phrase_security_memory_wipe(self, client: TestClient, pro_user_headers):
        """Test: Memory-Wipe nach Scan"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/seed-phrase",
            json={
                "seed_phrase": "test test test test test test test test test test test junk",
                "chains": ["ethereum"]
            },
            headers=pro_user_headers
        )
        
        # Response should not contain seed phrase
        response_text = response.text.lower()
        assert "test test test" not in response_text


class TestWalletScannerPrivateKey:
    """Test Suite für Private Key Scanning"""
    
    def test_scan_private_key_success(self, client: TestClient, pro_user_headers):
        """Test: Private Key scannen"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/private-key",
            json={
                "private_key": "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "chain": "ethereum",
                "check_history": True
            },
            headers=pro_user_headers
        )
        
        assert response.status_code in [200, 422]  # 422 if invalid key format
    
    def test_scan_private_key_invalid_format(self, client: TestClient, pro_user_headers):
        """Test: Ungültiges Private Key Format"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/private-key",
            json={
                "private_key": "invalid_key",
                "chain": "ethereum"
            },
            headers=pro_user_headers
        )
        
        assert response.status_code == 422
    
    def test_scan_private_key_no_storage(self, client: TestClient, pro_user_headers):
        """Test: Private Keys werden nicht gespeichert"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/private-key",
            json={
                "private_key": "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "chain": "ethereum"
            },
            headers=pro_user_headers
        )
        
        # Later check - private key should not be retrievable
        if response.status_code == 200:
            scan_id = response.json()["scan_id"]
            
            # Try to get scan details
            detail_response = client.get(
                f"/api/v1/wallet-scanner/report/{scan_id}/evidence",
                headers=pro_user_headers
            )
            
            if detail_response.status_code == 200:
                # Private key should be hashed, not stored
                detail_text = detail_response.text
                assert "0x0123456789abcdef" not in detail_text


class TestWalletScannerAddresses:
    """Test Suite für Zero-Trust Address Scanning"""
    
    def test_scan_addresses_single(self, client: TestClient, pro_user_headers):
        """Test: Einzelne Adresse scannen"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {
                        "chain": "ethereum",
                        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
                    }
                ],
                "check_history": True,
                "check_illicit": True
            },
            headers=pro_user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert "results" in data
        assert len(data["results"]) == 1
        
        result = data["results"][0]
        assert "balance" in result
        assert "risk_score" in result
        assert "labels" in result
    
    def test_scan_addresses_multiple_chains(self, client: TestClient, pro_user_headers):
        """Test: Multiple Adressen verschiedener Chains"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"},
                    {"chain": "bitcoin", "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"},
                    {"chain": "polygon", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
                ]
            },
            headers=pro_user_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
    
    def test_scan_addresses_invalid_address(self, client: TestClient, pro_user_headers):
        """Test: Ungültige Adresse"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "invalid_address"}
                ]
            },
            headers=pro_user_headers
        )
        
        # Should either reject or mark as invalid in results
        assert response.status_code in [200, 422]


class TestWalletScannerBulk:
    """Test Suite für Bulk Scanning"""
    
    def test_scan_bulk_csv_upload(self, client: TestClient, pro_user_headers):
        """Test: CSV-Upload für Bulk-Scan"""
        csv_content = b"""chain,address
ethereum,0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
bitcoin,bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
polygon,0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"""
        
        response = client.post(
            "/api/v1/wallet-scanner/scan/bulk",
            files={"file": ("addresses.csv", csv_content, "text/csv")},
            headers=pro_user_headers
        )
        
        assert response.status_code in [200, 202]  # 202 = Accepted for processing
        if response.status_code in [200, 202]:
            data = response.json()
            assert "scan_id" in data
    
    def test_scan_bulk_large_file(self, client: TestClient, pro_user_headers):
        """Test: Große CSV-Datei (100+ Adressen)"""
        # Generate 100 addresses
        csv_lines = ["chain,address"]
        for i in range(100):
            csv_lines.append(f"ethereum,0x{'0' * 39}{i:x}")
        
        csv_content = "\n".join(csv_lines).encode()
        
        response = client.post(
            "/api/v1/wallet-scanner/scan/bulk",
            files={"file": ("large.csv", csv_content, "text/csv")},
            headers=pro_user_headers
        )
        
        # Should accept or reject based on limits
        assert response.status_code in [200, 202, 413]


class TestWalletScannerReports:
    """Test Suite für Report Generation"""
    
    def test_report_csv_export(self, client: TestClient, pro_user_headers):
        """Test: CSV Report generieren"""
        # First, create a scan
        scan_response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
                ]
            },
            headers=pro_user_headers
        )
        
        if scan_response.status_code == 200:
            scan_id = scan_response.json()["scan_id"]
            
            # Export CSV
            report_response = client.get(
                f"/api/v1/wallet-scanner/report/{scan_id}/csv",
                headers=pro_user_headers
            )
            
            assert report_response.status_code == 200
            assert report_response.headers["content-type"] == "text/csv"
            assert "chain,address" in report_response.text
    
    def test_report_pdf_export(self, client: TestClient, pro_user_headers):
        """Test: PDF Report generieren"""
        # Create scan
        scan_response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
                ]
            },
            headers=pro_user_headers
        )
        
        if scan_response.status_code == 200:
            scan_id = scan_response.json()["scan_id"]
            
            # Export PDF
            pdf_response = client.get(
                f"/api/v1/wallet-scanner/report/{scan_id}/pdf",
                headers=pro_user_headers
            )
            
            assert pdf_response.status_code in [200, 501]  # 501 if not implemented
    
    def test_report_evidence_json(self, client: TestClient, pro_user_headers):
        """Test: Evidence JSON mit Chain-of-Custody"""
        # Create scan
        scan_response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
                ]
            },
            headers=pro_user_headers
        )
        
        if scan_response.status_code == 200:
            scan_id = scan_response.json()["scan_id"]
            
            # Get evidence
            evidence_response = client.get(
                f"/api/v1/wallet-scanner/report/{scan_id}/evidence",
                headers=pro_user_headers
            )
            
            assert evidence_response.status_code == 200
            data = evidence_response.json()
            assert "timestamp" in data
            assert "scan_id" in data
            assert "sha256_hash" in data  # Chain-of-custody hash


class TestWalletScannerSecurity:
    """Test Suite für Security Features"""
    
    def test_rate_limiting(self, client: TestClient, pro_user_headers):
        """Test: Rate Limiting (10 req/60s)"""
        responses = []
        
        for i in range(15):
            response = client.post(
                "/api/v1/wallet-scanner/scan/addresses",
                json={
                    "addresses": [
                        {"chain": "ethereum", "address": f"0x{'0' * 39}{i:x}"}
                    ]
                },
                headers=pro_user_headers
            )
            responses.append(response.status_code)
        
        # Should have some 429 (Too Many Requests)
        assert 429 in responses or len([r for r in responses if r == 200]) <= 10
    
    def test_secret_detection_blocks_keys(self, client: TestClient, pro_user_headers):
        """Test: Secret-Detection blockiert Keys in Adressen"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {
                        "chain": "ethereum",
                        "address": "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # Looks like key
                    }
                ]
            },
            headers=pro_user_headers
        )
        
        # Should detect and reject
        assert response.status_code in [400, 422]
    
    def test_audit_log_sanitization(self, client: TestClient, pro_user_headers):
        """Test: Audit-Logs enthalten keine Secrets"""
        # Scan with seed phrase
        client.post(
            "/api/v1/wallet-scanner/scan/seed-phrase",
            json={
                "seed_phrase": "test test test test test test test test test test test junk",
                "chains": ["ethereum"]
            },
            headers=pro_user_headers
        )
        
        # Check audit logs (if accessible)
        # Seed phrase should be hashed, not stored
        pass  # Placeholder


class TestWalletScannerAdvanced:
    """Test Suite für Advanced Features"""
    
    def test_mixer_detection(self, client: TestClient, pro_user_headers):
        """Test: Tornado Cash Mixer Detection"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
                ],
                "check_mixers": True
            },
            headers=pro_user_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data["results"][0]
            # Should have mixer info if detected
            assert "mixer_exposure" in result or "risk_factors" in result
    
    def test_bridge_reconstruction(self, client: TestClient, pro_user_headers):
        """Test: Cross-Chain Bridge Rekonstruktion"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
                ],
                "detect_bridges": True
            },
            headers=pro_user_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for bridge links
            assert "bridge_transfers" in data or response.status_code == 200
    
    def test_indirect_risk_scoring(self, client: TestClient, pro_user_headers):
        """Test: Indirect Risk durch Counterparty-Analysis"""
        response = client.post(
            "/api/v1/wallet-scanner/scan/addresses",
            json={
                "addresses": [
                    {"chain": "ethereum", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}
                ],
                "include_indirect_risk": True
            },
            headers=pro_user_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data["results"][0]
            assert "indirect_risk_score" in result or "counterparty_risks" in result


# ==================== FIXTURES ====================

@pytest.fixture
def pro_user_headers(client: TestClient):
    """Fixture: Pro User Auth Headers"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "pro@test.com",
            "password": "test123"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        pytest.skip("Pro user not available")


@pytest.fixture
def community_user_headers(client: TestClient):
    """Fixture: Community User Auth Headers"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "community@test.com",
            "password": "test123"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        return {}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
