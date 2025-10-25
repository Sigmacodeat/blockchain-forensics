import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta

from backend.app.api.v1.crypto_payments import extend_payment_expiry, ExtendPaymentRequest


class DummyUser(dict):
    def get(self, k, d=None):
        return super().get(k, d)


@pytest.mark.asyncio
async def test_extend_payment_expiry_pending(monkeypatch):
    payment_id = 12345
    user_id = 999
    now = datetime.utcnow()

    # Mock DB row for pending payment owned by user
    payment_row = {
        "payment_id": payment_id,
        "user_id": user_id,
        "payment_status": "pending",
        "expires_at": now + timedelta(minutes=5),
    }

    calls = SimpleNamespace(updated=False, update_args=None)

    # Patch postgres_client.fetchrow and execute
    from backend.app.api.v1 import crypto_payments as module

    async def fake_fetchrow(query, pid, uid):
        assert pid == payment_id
        assert uid == user_id
        return payment_row

    async def fake_execute(query, new_expiry, pid, uid):
        assert pid == payment_id
        assert uid == user_id
        assert isinstance(new_expiry, datetime)
        calls.updated = True
        calls.update_args = (new_expiry, pid, uid)

    monkeypatch.setattr(module.postgres_client, "fetchrow", fake_fetchrow, raising=False)
    monkeypatch.setattr(module.postgres_client, "execute", fake_execute, raising=False)

    # Run endpoint
    body = ExtendPaymentRequest(minutes=10)
    current_user = DummyUser(id=user_id)
    result = await extend_payment_expiry(payment_id=payment_id, body=body, current_user=current_user)  # type: ignore[arg-type]

    assert result["payment_id"] == payment_id
    assert result["payment_status"] == "pending"
    assert "client_expiry" in result
    assert calls.updated is True


@pytest.mark.asyncio
async def test_extend_payment_expiry_non_pending(monkeypatch):
    payment_id = 555
    user_id = 42

    from backend.app.api.v1 import crypto_payments as module

    async def fake_fetchrow(query, pid, uid):
        return {
            "payment_id": payment_id,
            "user_id": user_id,
            "payment_status": "finished",
            "expires_at": datetime.utcnow(),
        }

    monkeypatch.setattr(module.postgres_client, "fetchrow", fake_fetchrow, raising=False)

    body = ExtendPaymentRequest(minutes=10)
    current_user = DummyUser(id=user_id)

    with pytest.raises(Exception):
        await extend_payment_expiry(payment_id=payment_id, body=body, current_user=current_user)  # type: ignore[arg-type]
