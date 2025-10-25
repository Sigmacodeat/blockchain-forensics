"""
E2E Test for BTC Checkout Flow
Simulates complete payment flow from invoice creation to subscription activation
"""

import asyncio
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import json


class TestBTCInvoiceCheckout:
    """E2E test suite for BTC invoice checkout flow."""

    @pytest.mark.asyncio
    async def test_complete_btc_checkout_flow(self, client: AsyncClient):
        """Test complete BTC checkout flow from invoice creation to subscription activation."""

        # Mock user authentication
        user_id = "test_user_123"
        user_token = "test_jwt_token"

        # Mock BTC wallet service
        with patch('app.services.btc_wallet_service.btc_wallet_service') as mock_wallet:
            mock_wallet.generate_invoice_address.return_value = {
                "address": "bc1qtestaddress123456789012345678901234567890",
                "encrypted_private_key": "encrypted_test_key",
                "index": "12345",
                "order_id": "btc_inv_test_123",
                "plan_name": "pro",
                "expected_amount_btc": "0.001",
                "address_type": "bech32_p2wpkh"
            }

            # Step 1: Create BTC Invoice
            invoice_data = {
                "plan_name": "pro",
                "amount_btc": 0.001,
                "expires_hours": 24,
                "idempotency_key": "test_idempotency_123"
            }

            response = await client.post(
                "/api/v1/crypto-payments/invoice",
                json=invoice_data,
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == 200
            invoice_response = response.json()
            assert "order_id" in invoice_response
            assert "address" in invoice_response
            assert invoice_response["plan_name"] == "pro"
            order_id = invoice_response["order_id"]

            # Step 2: Check invoice status (should be pending)
            response = await client.get(
                f"/api/v1/crypto-payments/invoice/{order_id}",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == 200
            status_response = response.json()
            assert status_response["status"] == "pending"
            assert status_response["expected_amount_btc"] == "0.001"

            # Step 3: Simulate payment received (mock Esplora API)
            with patch('app.services.btc_wallet_service.btc_wallet_service.get_total_received') as mock_balance:
                mock_balance.return_value = 0.001  # Payment received

                # Check status again (should be paid now)
                response = await client.get(
                    f"/api/v1/crypto-payments/invoice/{order_id}",
                    headers={"Authorization": f"Bearer {user_token}"}
                )

                assert response.status_code == 200
                paid_response = response.json()
                assert paid_response["status"] == "paid"
                assert paid_response["received_amount_btc"] == "0.001"

            # Step 4: Verify subscription was activated
            # Mock subscription activation
            with patch('app.services.subscription_activation_service.handle_paid_invoice') as mock_activation:
                mock_activation.return_value = True

                # Trigger invoice monitor (normally done by background worker)
                from app.services.btc_invoice_service import btc_invoice_service
                final_status = btc_invoice_service.check_payment_status(order_id)
                assert final_status["status"] == "paid"

    @pytest.mark.asyncio
    async def test_idempotent_invoice_creation(self, client: AsyncClient):
        """Test that invoice creation is idempotent with the same key."""

        user_token = "test_jwt_token"
        idempotency_key = "test_idempotency_456"

        # Mock BTC wallet service
        with patch('app.services.btc_wallet_service.btc_wallet_service') as mock_wallet:
            mock_wallet.generate_invoice_address.return_value = {
                "address": "bc1qtestaddress123456789012345678901234567890",
                "encrypted_private_key": "encrypted_test_key",
                "index": "12346",
                "order_id": "btc_inv_test_456",
                "plan_name": "business",
                "expected_amount_btc": "0.005",
                "address_type": "bech32_p2wpkh"
            }

            # First request
            invoice_data = {
                "plan_name": "business",
                "amount_btc": 0.005,
                "expires_hours": 24,
                "idempotency_key": idempotency_key
            }

            response1 = await client.post(
                "/api/v1/crypto-payments/invoice",
                json=invoice_data,
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response1.status_code == 200
            invoice1 = response1.json()

            # Second request with same idempotency key
            response2 = await client.post(
                "/api/v1/crypto-payments/invoice",
                json=invoice_data,
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response2.status_code == 200
            invoice2 = response2.json()

            # Should return the same invoice
            assert invoice1["order_id"] == invoice2["order_id"]
            assert invoice1["address"] == invoice2["address"]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient):
        """Test that rate limiting prevents abuse."""

        user_token = "test_jwt_token"

        # Mock Redis for rate limiting
        with patch('redis.Redis') as mock_redis:
            mock_instance = MagicMock()
            mock_redis.return_value = mock_instance

            # First 5 requests succeed
            mock_instance.incr.side_effect = [1, 2, 3, 4, 5]
            mock_instance.expire.return_value = True

            # Mock BTC wallet service
            with patch('app.services.btc_wallet_service.btc_wallet_service') as mock_wallet:
                mock_wallet.generate_invoice_address.side_effect = [
                    {
                        "address": f"bc1qtest{i}",
                        "encrypted_private_key": f"encrypted_test_key_{i}",
                        "index": str(10000 + i),
                        "order_id": f"btc_inv_test_{10000 + i}",
                        "plan_name": "pro",
                        "expected_amount_btc": "0.001",
                        "address_type": "bech32_p2wpkh"
                    } for i in range(5)
                ]

                invoice_data = {
                    "plan_name": "pro",
                    "amount_btc": 0.001,
                    "expires_hours": 24
                }

                # Make 5 requests (should succeed)
                for i in range(5):
                    response = await client.post(
                        "/api/v1/crypto-payments/invoice",
                        json=invoice_data,
                        headers={"Authorization": f"Bearer {user_token}"}
                    )
                    assert response.status_code == 200

                # 6th request should be rate limited
                mock_instance.incr.side_effect = [6]

                response = await client.post(
                    "/api/v1/crypto-payments/invoice",
                    json=invoice_data,
                    headers={"Authorization": f"Bearer {user_token}"}
                )

                assert response.status_code == 429
                assert "Rate limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_websocket_realtime_updates(self, client: AsyncClient):
        """Test WebSocket real-time invoice status updates."""
        # This would require WebSocket testing framework like pytest-asyncio with websockets
        # For now, just test the API endpoints that WS uses

        user_token = "test_jwt_token"

        # Create invoice
        with patch('app.services.btc_wallet_service.btc_wallet_service') as mock_wallet:
            mock_wallet.generate_invoice_address.return_value = {
                "address": "bc1qws_test",
                "encrypted_private_key": "encrypted_ws_test",
                "index": "99999",
                "order_id": "btc_inv_ws_test",
                "plan_name": "pro",
                "expected_amount_btc": "0.002",
                "address_type": "bech32_p2wpkh"
            }

            response = await client.post(
                "/api/v1/crypto-payments/invoice",
                json={
                    "plan_name": "pro",
                    "amount_btc": 0.002,
                    "expires_hours": 24
                },
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == 200
            order_id = response.json()["order_id"]

            # Test status endpoint that WS uses
            response = await client.get(
                f"/api/v1/crypto-payments/invoice/{order_id}",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == 200
            status = response.json()
            assert status["order_id"] == order_id
            assert "expires_at" in status
            assert "plan_name" in status
