import pytest
from unittest.mock import AsyncMock, patch

from app.services.partner_service import partner_service


@pytest.mark.asyncio
async def test_record_commission_on_payment_records_entry():
    mock_partner = {
        "id": "partner-123",
        "commission_rate": 25.0,
    }
    inserted_row = {
        "id": "c-1",
        "partner_id": "partner-123",
        "commission_usd": 12.5,
        "status": "pending",
    }

    with patch.object(partner_service, "_resolve_partner_for_user", AsyncMock(return_value=mock_partner)), \
         patch("app.services.partner_service.postgres_client.fetchrow", AsyncMock(return_value=inserted_row)) as fetchrow:
        result = await partner_service.record_commission_on_payment(
            user_id="user-1",
            plan_name="pro",
            amount_usd=50.0,
            payment_id=101,
            order_id="order-abc",
        )

    fetchrow.assert_awaited()
    assert result == inserted_row


@pytest.mark.asyncio
async def test_assign_referral_updates_user_and_creates_referral():
    partner = {"id": "partner-456"}

    with patch.object(partner_service, "get_partner_by_referral_code", AsyncMock(return_value=partner)), \
         patch("app.services.partner_service.postgres_client.fetchrow", AsyncMock(return_value={"referred_by_partner_id": None})), \
         patch("app.services.partner_service.postgres_client.execute", AsyncMock()) as execute:
        assigned = await partner_service.assign_referral(
            referred_user_id="user-42",
            referral_code="p-demo",
            tracking_id="trk-1",
            source="landing-page",
        )

    assert assigned is True
    assert execute.await_count == 2


def test_partner_account_endpoint_returns_data(client):
    from app.auth.dependencies import get_current_user

    partner_user = {
        "user_id": "partner-user",
        "email": "partner@example.com",
        "role": "partner",
    }

    account_payload = {
        "account": {
            "id": "partner-1",
            "user_id": "partner-user",
            "referral_code": "p-test",
            "commission_rate": 20,
            "recurring_rate": 20,
            "cookie_duration_days": 30,
            "min_payout_usd": 50,
            "is_active": True,
            "created_at": "2025-10-23T00:00:00Z",
        },
        "stats": {"pending": 10.5, "approved": 25.0}
    }

    with patch("app.auth.dependencies.get_current_user", return_value=partner_user), \
         patch("app.services.partner_service.partner_service.ensure_partner_account", AsyncMock(return_value=account_payload["account"])), \
         patch("app.services.partner_service.postgres_client.fetch", AsyncMock(return_value=[])):
        response = client.get("/api/v1/partner/account")

    assert response.status_code == 200
    data = response.json()
    assert data["account"]["referral_code"] == "p-test"


def test_partner_payout_request(client):
    partner_user = {
        "user_id": "partner-user",
        "email": "partner@example.com",
        "role": "partner",
    }

    account_data = {
        "id": "partner-1",
        "user_id": "partner-user",
        "referral_code": "p-test",
        "commission_rate": 20,
        "recurring_rate": 20,
        "cookie_duration_days": 30,
        "min_payout_usd": 50,
        "is_active": True,
        "created_at": "2025-10-23T00:00:00Z",
    }

    with patch("app.auth.dependencies.get_current_user", return_value=partner_user), \
         patch("app.services.partner_service.partner_service.ensure_partner_account", AsyncMock(return_value=account_data)), \
         patch("app.services.partner_service.postgres_client.fetch", AsyncMock(return_value=[{"status": "pending", "sum": 100}])), \
         patch("app.services.partner_service.postgres_client.fetchrow", AsyncMock(return_value={"id": "payout-1"})):
        response = client.post("/api/v1/partner/payouts/request", json={"amount_usd": 75})

    assert response.status_code == 200
    data = response.json()
    assert data["payout"]["id"] == "payout-1"
