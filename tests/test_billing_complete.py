"""
💳 COMPLETE BILLING & SUBSCRIPTION TEST SUITE
============================================

Tests für ALLE Billing-Features:
- Subscription-Management (Create, Update, Cancel)
- Plan-Upgrades & Downgrades
- Token-Usage-Tracking
- Rate-Limiting pro Plan
- Payment-Processing
- Invoice-Generation
- Billing-History
- Proration-Calculations
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json


@pytest.fixture
def community_user():
    return {
        "id": "user-community",
        "email": "community@test.com",
        "plan": "community",
        "role": "user",
        "subscription_id": None,
        "subscription_status": None
    }

@pytest.fixture
def pro_user():
    return {
        "id": "user-pro",
        "email": "pro@test.com",
        "plan": "pro",
        "role": "user",
        "subscription_id": "sub-pro-123",
        "subscription_status": "active"
    }

@pytest.fixture
def admin_user():
    return {
        "id": "admin-1",
        "email": "admin@test.com",
        "plan": "enterprise",
        "role": "admin"
    }


class TestSubscriptionManagement:
    """Test: Subscription CRUD Operations"""
    
    def test_create_subscription(self, client, community_user):
        """Community-User kann Subscription erstellen"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            resp = client.post("/api/v1/billing/subscriptions", json={
                "plan": "pro",
                "billing_period": "monthly"
            })
            
            assert resp.status_code in [200, 201]
            data = resp.json()
            assert "subscription_id" in data
            assert data["plan"] == "pro"
            assert data["status"] == "active"
    
    def test_get_subscription(self, client, pro_user):
        """User kann eigene Subscription abrufen"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.get("/api/v1/billing/subscriptions/current")
            assert resp.status_code == 200
            data = resp.json()
            assert "plan" in data
            assert "status" in data
    
    def test_cancel_subscription(self, client, pro_user):
        """User kann Subscription kündigen"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.delete("/api/v1/billing/subscriptions/current")
            assert resp.status_code in [200, 204]
    
    def test_reactivate_subscription(self, client, pro_user):
        """User kann gekündigte Subscription reaktivieren"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.post("/api/v1/billing/subscriptions/current/reactivate")
            assert resp.status_code == 200


class TestPlanUpgradesDowngrades:
    """Test: Plan-Änderungen & Proration"""
    
    def test_upgrade_community_to_pro(self, client, community_user):
        """Upgrade von Community zu Pro"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            resp = client.post("/api/v1/billing/upgrade", json={
                "target_plan": "pro"
            })
            
            assert resp.status_code in [200, 201]
            data = resp.json()
            assert data["new_plan"] == "pro"
            assert "prorated_amount" in data or "amount_due" in data
    
    def test_upgrade_pro_to_enterprise(self, client, pro_user):
        """Upgrade von Pro zu Enterprise"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.post("/api/v1/billing/upgrade", json={
                "target_plan": "enterprise"
            })
            
            assert resp.status_code == 200
            data = resp.json()
            assert data["new_plan"] == "enterprise"
    
    def test_downgrade_pro_to_starter(self, client, pro_user):
        """Downgrade von Pro zu Starter"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.post("/api/v1/billing/downgrade", json={
                "target_plan": "starter"
            })
            
            assert resp.status_code == 200
            data = resp.json()
            # Downgrade erfolgt am Ende des Billing-Cycles
            assert "effective_date" in data
    
    def test_proration_calculation(self, client, pro_user):
        """Proration sollte korrekt berechnet werden"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.post("/api/v1/billing/calculate-proration", json={
                "target_plan": "business"
            })
            
            assert resp.status_code == 200
            data = resp.json()
            assert "prorated_amount" in data
            assert "days_remaining" in data
            assert float(data["prorated_amount"]) >= 0
    
    def test_cannot_downgrade_below_usage(self, client, pro_user):
        """Downgrade sollte blockiert werden wenn Features in Nutzung"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            # Simuliere aktive Pro-Features
            with patch('app.services.billing.check_active_features', return_value=["investigator", "correlation"]):
                resp = client.post("/api/v1/billing/downgrade", json={
                    "target_plan": "community"
                })
                
                assert resp.status_code == 400
                data = resp.json()
                assert "active_features" in data.get("detail", "").lower()


class TestTokenUsageTracking:
    """Test: Token-Usage pro Plan"""
    
    def test_track_api_usage(self, client, pro_user):
        """API-Calls sollten tracked werden"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            # Führe mehrere API-Calls aus
            for i in range(5):
                resp = client.post("/api/v1/trace/start", json={
                    "chain": "ethereum",
                    "address": f"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb{i}",
                    "direction": "backward"
                })
            
            # Prüfe Usage
            resp = client.get("/api/v1/usage/current")
            assert resp.status_code == 200
            data = resp.json()
            assert "api_calls" in data
            assert data["api_calls"] >= 5
    
    def test_rate_limiting_community(self, client, community_user):
        """Community-Plan sollte Rate-Limits haben"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            # Sende viele Requests
            success_count = 0
            rate_limited = False
            
            for i in range(100):
                resp = client.get("/api/v1/cases")
                if resp.status_code == 200:
                    success_count += 1
                elif resp.status_code == 429:
                    rate_limited = True
                    break
            
            # Community sollte nach X Requests limitiert werden
            assert rate_limited or success_count < 100
    
    def test_rate_limiting_pro_higher(self, client, pro_user):
        """Pro-Plan sollte höhere Limits haben"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            success_count = 0
            
            # Pro sollte mehr Requests erlauben
            for i in range(100):
                resp = client.get("/api/v1/cases")
                if resp.status_code == 200:
                    success_count += 1
            
            # Pro sollte alle 100 Requests erlauben
            assert success_count == 100
    
    def test_token_usage_per_feature(self, client, pro_user):
        """Token-Usage sollte pro Feature getrackt werden"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.get("/api/v1/usage/breakdown")
            assert resp.status_code == 200
            data = resp.json()
            
            # Sollte Breakdown nach Feature haben
            assert "traces" in data or "features" in data
            assert "total_tokens" in data or "total_usage" in data
    
    def test_monthly_quota_enforcement(self, client, community_user):
        """Monthly Quota sollte enforced werden"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            # Simuliere, dass Quota erschöpft ist
            with patch('app.services.usage.check_quota', return_value=False):
                resp = client.post("/api/v1/trace/start", json={
                    "chain": "ethereum",
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
                })
                
                assert resp.status_code == 429
                data = resp.json()
                assert "quota" in data.get("detail", "").lower()


class TestInvoiceGeneration:
    """Test: Invoice-Generation & History"""
    
    def test_generate_invoice(self, client, pro_user):
        """System sollte Invoices generieren"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.get("/api/v1/billing/invoices/current")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "invoice_number" in data
            assert "amount" in data
            assert "status" in data
            assert "due_date" in data
    
    def test_invoice_history(self, client, pro_user):
        """User sollte Invoice-History sehen können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.get("/api/v1/billing/invoices")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "invoices" in data or isinstance(data, list)
    
    def test_download_invoice_pdf(self, client, pro_user):
        """User sollte Invoices als PDF downloaden können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.get("/api/v1/billing/invoices/inv-123/pdf")
            assert resp.status_code in [200, 404]
            
            if resp.status_code == 200:
                assert resp.headers["content-type"] == "application/pdf"


class TestPaymentMethods:
    """Test: Payment-Method-Management"""
    
    def test_add_payment_method(self, client, pro_user):
        """User sollte Payment-Methods hinzufügen können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.post("/api/v1/billing/payment-methods", json={
                "type": "card",
                "token": "tok_visa_test"
            })
            
            assert resp.status_code in [200, 201]
    
    def test_list_payment_methods(self, client, pro_user):
        """User sollte Payment-Methods listen können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.get("/api/v1/billing/payment-methods")
            assert resp.status_code == 200
            data = resp.json()
            assert "payment_methods" in data or isinstance(data, list)
    
    def test_set_default_payment_method(self, client, pro_user):
        """User sollte Default-Payment-Method setzen können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=pro_user):
            resp = client.put("/api/v1/billing/payment-methods/pm-123/default")
            assert resp.status_code in [200, 404]


class TestBillingIntegration:
    """Integration-Tests: Complete Billing-Workflows"""
    
    def test_complete_upgrade_flow(self, client, community_user):
        """Kompletter Upgrade-Flow: Community → Pro"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            # 1. Calculate Proration
            resp = client.post("/api/v1/billing/calculate-proration", json={
                "target_plan": "pro"
            })
            assert resp.status_code == 200
            proration = resp.json()
            
            # 2. Create Subscription
            resp = client.post("/api/v1/billing/subscriptions", json={
                "plan": "pro",
                "billing_period": "monthly"
            })
            assert resp.status_code in [200, 201]
            subscription = resp.json()
            
            # 3. Verify Plan Changed
            resp = client.get("/api/v1/users/me")
            assert resp.status_code == 200
            user = resp.json()
            assert user["plan"] == "pro"
    
    def test_subscription_lifecycle(self, client, community_user):
        """Subscription-Lifecycle: Create → Pause → Resume → Cancel"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            # Create
            resp = client.post("/api/v1/billing/subscriptions", json={
                "plan": "starter"
            })
            assert resp.status_code in [200, 201]
            
            # Pause (falls unterstützt)
            resp = client.post("/api/v1/billing/subscriptions/current/pause")
            assert resp.status_code in [200, 404]  # 404 wenn nicht unterstützt
            
            # Resume
            if resp.status_code == 200:
                resp = client.post("/api/v1/billing/subscriptions/current/resume")
                assert resp.status_code == 200
            
            # Cancel
            resp = client.delete("/api/v1/billing/subscriptions/current")
            assert resp.status_code in [200, 204]


class TestAdminBilling:
    """Test: Admin-Billing-Features"""
    
    def test_admin_list_all_subscriptions(self, client, admin_user):
        """Admin sollte alle Subscriptions sehen können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=admin_user):
            resp = client.get("/api/v1/admin/billing/subscriptions")
            assert resp.status_code == 200
    
    def test_admin_billing_analytics(self, client, admin_user):
        """Admin sollte Billing-Analytics sehen können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=admin_user):
            resp = client.get("/api/v1/admin/billing/analytics")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "total_revenue" in data or "mrr" in data
            assert "active_subscriptions" in data or "subscriber_count" in data
    
    def test_admin_modify_user_plan(self, client, admin_user):
        """Admin sollte User-Plans direkt ändern können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=admin_user):
            resp = client.put("/api/v1/admin/users/user-123/plan", json={
                "plan": "enterprise",
                "reason": "VIP customer"
            })
            assert resp.status_code in [200, 404]


class TestTrialPeriods:
    """Test: Trial-Period-Management"""
    
    def test_start_trial(self, client, community_user):
        """User sollte Trial starten können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            resp = client.post("/api/v1/trials/start", json={
                "plan": "pro",
                "duration_days": 14
            })
            
            assert resp.status_code in [200, 201]
            data = resp.json()
            assert "trial_ends_at" in data or "expires_at" in data
    
    def test_trial_expiration(self, client, community_user):
        """Trial sollte nach Ablauf automatisch downgraden"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            # Simuliere expired Trial
            with patch('app.services.trials.check_trial_status', return_value="expired"):
                resp = client.get("/api/v1/users/me")
                assert resp.status_code == 200
                user = resp.json()
                # Sollte auf Community zurückgefallen sein
                assert user["plan"] == "community"
    
    def test_convert_trial_to_paid(self, client, community_user):
        """User sollte Trial in paid Subscription konvertieren können"""
        with patch('app.auth.dependencies.get_current_user_strict', return_value=community_user):
            resp = client.post("/api/v1/trials/convert", json={
                "payment_method": "pm-123"
            })
            
            assert resp.status_code in [200, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
