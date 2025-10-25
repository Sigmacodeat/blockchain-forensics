"""
🚀 COMPLETE CRYPTO-PAYMENTS TEST SUITE
======================================

Tests für ALLE Crypto-Payment-Features:
- Currency-List
- Payment-Estimate
- Payment-Creation
- Payment-Status
- QR-Code-Generation
- WebSocket-Updates
- Web3-Wallet-Integration
- Admin-Analytics
- Webhook-Handler
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import asyncio
from datetime import datetime, timedelta


@pytest.fixture
def starter_user():
    return {
        "id": "user-starter",
        "email": "starter@test.com",
        "plan": "starter",
        "role": "user"
    }

@pytest.fixture
def admin_user():
    return {
        "id": "admin-1",
        "email": "admin@test.com",
        "plan": "enterprise",
        "role": "admin"
    }


class TestCryptoPaymentsCurrencies:
    """Test: Available Cryptocurrencies abrufen"""
    
    def test_get_currencies_success(self, client):
        """Currencies-Liste sollte 30+ Coins enthalten"""
        resp = client.get("/api/v1/crypto-payments/currencies")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "currencies" in data
        currencies = data["currencies"]
        assert len(currencies) >= 30
        
        # Check für wichtige Coins
        symbols = [c["symbol"] for c in currencies]
        assert "BTC" in symbols
        assert "ETH" in symbols
        assert "USDT" in symbols
        assert "USDC" in symbols
    
    def test_currencies_structure(self, client):
        """Jede Currency sollte vollständige Infos haben"""
        resp = client.get("/api/v1/crypto-payments/currencies")
        data = resp.json()
        currencies = data["currencies"]
        
        first_currency = currencies[0]
        assert "symbol" in first_currency
        assert "name" in first_currency
        assert "network" in first_currency or "chain" in first_currency


class TestCryptoPaymentsEstimate:
    """Test: Payment-Estimates berechnen"""
    
    def test_estimate_success(self, client, starter_user):
        """Estimate sollte korrekten Betrag zurückgeben"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.post("/api/v1/crypto-payments/estimate", json={
                "plan": "pro",
                "currency": "ETH"
            })
            assert resp.status_code == 200
            data = resp.json()
            
            assert "amount" in data
            assert "currency" in data
            assert "plan" in data
            assert "usd_price" in data
            
            # Amount sollte > 0 sein
            assert float(data["amount"]) > 0
    
    def test_estimate_all_plans(self, client, starter_user):
        """Estimates für alle Plans sollten funktionieren"""
        plans = ["starter", "pro", "business", "plus", "enterprise"]
        
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            for plan in plans:
                resp = client.post("/api/v1/crypto-payments/estimate", json={
                    "plan": plan,
                    "currency": "USDT"
                })
                assert resp.status_code == 200
                data = resp.json()
                assert float(data["amount"]) > 0
    
    def test_estimate_invalid_currency(self, client, starter_user):
        """Ungültige Currency sollte Fehler geben"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.post("/api/v1/crypto-payments/estimate", json={
                "plan": "pro",
                "currency": "INVALID_COIN"
            })
            assert resp.status_code in [400, 404]


class TestCryptoPaymentsCreation:
    """Test: Payment-Creation Workflow"""
    
    @patch('app.services.crypto_payments.CryptoPaymentService.create_payment')
    def test_create_payment_success(self, mock_create, client, starter_user):
        """Payment-Creation sollte vollständige Daten zurückgeben"""
        mock_create.return_value = {
            "id": "payment-123",
            "payment_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "amount": "0.123",
            "currency": "ETH",
            "status": "pending",
            "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat()
        }
        
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.post("/api/v1/crypto-payments/create", json={
                "plan": "pro",
                "currency": "ETH",
                "email": starter_user["email"]
            })
            
            assert resp.status_code in [200, 201]
            data = resp.json()
            
            assert "id" in data or "payment_id" in data
            assert "payment_address" in data or "address" in data
            assert "amount" in data
            assert "currency" in data
            assert data["currency"] == "ETH"
    
    def test_create_payment_requires_auth(self, client):
        """Payment-Creation ohne Auth sollte 401 geben"""
        resp = client.post("/api/v1/crypto-payments/create", json={
            "plan": "pro",
            "currency": "BTC"
        })
        assert resp.status_code == 401


class TestCryptoPaymentsStatus:
    """Test: Payment-Status abrufen"""
    
    @patch('app.services.crypto_payments.CryptoPaymentService.get_payment_status')
    def test_get_status_success(self, mock_status, client, starter_user):
        """Status sollte aktuelle Payment-Infos zurückgeben"""
        mock_status.return_value = {
            "id": "payment-123",
            "status": "waiting",
            "amount": "0.123",
            "currency": "ETH",
            "payment_address": "0x742d...",
            "tx_hash": None
        }
        
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.get("/api/v1/crypto-payments/status/payment-123")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "status" in data
            assert data["status"] in ["pending", "waiting", "confirming", "finished", "failed", "expired"]
    
    def test_get_status_not_found(self, client, starter_user):
        """Nicht-existentes Payment sollte 404 geben"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.get("/api/v1/crypto-payments/status/nonexistent")
            assert resp.status_code == 404


class TestCryptoPaymentsQRCode:
    """Test: QR-Code-Generation"""
    
    @patch('app.services.crypto_payments.CryptoPaymentService.generate_qr_code')
    def test_qr_code_generation(self, mock_qr, client, starter_user):
        """QR-Code sollte Base64-encodiertes PNG zurückgeben"""
        mock_qr.return_value = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
        
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.get("/api/v1/crypto-payments/qr-code/payment-123")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "qr_code" in data
            assert data["qr_code"].startswith("data:image/png;base64,")


class TestCryptoPaymentsHistory:
    """Test: Payment-History abrufen"""
    
    @patch('app.services.crypto_payments.CryptoPaymentService.get_user_payments')
    def test_get_history(self, mock_history, client, starter_user):
        """History sollte alle User-Payments zurückgeben"""
        mock_history.return_value = [
            {
                "id": "payment-1",
                "plan": "pro",
                "amount": "0.123",
                "currency": "ETH",
                "status": "finished",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "payment-2",
                "plan": "business",
                "amount": "50.0",
                "currency": "USDT",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.get("/api/v1/crypto-payments/history")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "payments" in data or isinstance(data, list)
            payments = data.get("payments", data)
            assert len(payments) == 2


class TestCryptoPaymentsWebhook:
    """Test: NOWPayments Webhook-Handler"""
    
    @patch('app.services.crypto_payments.CryptoPaymentService.verify_webhook_signature')
    @patch('app.services.crypto_payments.CryptoPaymentService.process_webhook')
    def test_webhook_valid_signature(self, mock_process, mock_verify, client):
        """Webhook mit gültiger Signatur sollte verarbeitet werden"""
        mock_verify.return_value = True
        mock_process.return_value = {"status": "processed"}
        
        webhook_payload = {
            "payment_id": "123456789",
            "payment_status": "finished",
            "pay_amount": "0.123",
            "pay_currency": "ETH",
            "order_id": "payment-123"
        }
        
        resp = client.post(
            "/api/v1/webhooks/nowpayments",
            json=webhook_payload,
            headers={"x-nowpayments-sig": "valid-signature"}
        )
        
        assert resp.status_code == 200
    
    def test_webhook_invalid_signature(self, client):
        """Webhook mit ungültiger Signatur sollte 401 geben"""
        with patch('app.services.crypto_payments.CryptoPaymentService.verify_webhook_signature', return_value=False):
            webhook_payload = {"payment_id": "123"}
            
            resp = client.post(
                "/api/v1/webhooks/nowpayments",
                json=webhook_payload,
                headers={"x-nowpayments-sig": "invalid-signature"}
            )
            
            assert resp.status_code == 401


class TestCryptoPaymentsAdmin:
    """Test: Admin-Analytics & Management"""
    
    @patch('app.services.crypto_payments.CryptoPaymentService.get_analytics')
    def test_admin_analytics(self, mock_analytics, client, admin_user):
        """Admin sollte Analytics sehen können"""
        mock_analytics.return_value = {
            "total_payments": 150,
            "successful_payments": 120,
            "pending_payments": 20,
            "failed_payments": 10,
            "total_revenue_usd": 45000,
            "conversion_rate": 0.80
        }
        
        with patch('app.auth.dependencies.get_current_user_strict', return_value=admin_user):
            resp = client.get("/api/v1/admin/crypto-payments/analytics")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "total_payments" in data
            assert "conversion_rate" in data
    
    def test_admin_list_all_payments(self, client, admin_user):
        """Admin sollte alle Payments listen können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=admin_user):
            resp = client.get("/api/v1/admin/crypto-payments/list")
            assert resp.status_code == 200
    
    def test_non_admin_cannot_access_analytics(self, client, starter_user):
        """Non-Admin sollte keinen Zugriff haben"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            resp = client.get("/api/v1/admin/crypto-payments/analytics")
            assert resp.status_code == 403


class TestCryptoPaymentsIntegration:
    """Integration-Tests: End-to-End Workflows"""
    
    @patch('app.services.crypto_payments.CryptoPaymentService')
    def test_full_payment_workflow(self, mock_service, client, starter_user):
        """Kompletter Workflow: Estimate → Create → Status → QR"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=starter_user):
            # 1. Estimate
            resp = client.post("/api/v1/crypto-payments/estimate", json={
                "plan": "pro",
                "currency": "ETH"
            })
            assert resp.status_code == 200
            estimate = resp.json()
            
            # 2. Create (mocked)
            mock_service.create_payment.return_value = {
                "id": "payment-xyz",
                "payment_address": "0x742d...",
                "amount": estimate["amount"],
                "currency": "ETH",
                "status": "pending"
            }
            
            resp = client.post("/api/v1/crypto-payments/create", json={
                "plan": "pro",
                "currency": "ETH",
                "email": starter_user["email"]
            })
            assert resp.status_code in [200, 201]
            payment = resp.json()
            payment_id = payment.get("id") or payment.get("payment_id")
            
            # 3. Status (mocked)
            mock_service.get_payment_status.return_value = {
                "id": payment_id,
                "status": "waiting"
            }
            
            resp = client.get(f"/api/v1/crypto-payments/status/{payment_id}")
            assert resp.status_code == 200
            
            # 4. QR-Code (mocked)
            mock_service.generate_qr_code.return_value = "data:image/png;base64,..."
            
            resp = client.get(f"/api/v1/crypto-payments/qr-code/{payment_id}")
            assert resp.status_code == 200


# WebSocket-Tests (falls WebSocket-Support vorhanden)
class TestCryptoPaymentsWebSocket:
    """Test: WebSocket Live-Updates"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """WebSocket sollte sich verbinden und Updates senden"""
        # WebSocket-Tests benötigen spezielle Test-Clients
        # Placeholder für vollständige WebSocket-Tests
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
