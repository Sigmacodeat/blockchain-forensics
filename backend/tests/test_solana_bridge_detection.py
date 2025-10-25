import pytest
from app.adapters.solana_adapter import SolanaAdapter

pytestmark = pytest.mark.asyncio


async def test_solana_bridge_detection_sets_event_type_bridge(monkeypatch):
    # Configure a known bridge program id
    from app import config as cfg
    monkeypatch.setattr(cfg.settings, "BRIDGE_PROGRAMS_SOL", ["Bridge1111111111111111111111111111111111111"])

    adapter = SolanaAdapter(rpc_url="")  # rpc_url empty -> we won't call RPC

    # Craft raw tx with programId matching configured bridge program
    raw_tx = {
        "transaction": {
            "signatures": ["sig123"],
            "message": {
                "accountKeys": [
                    "FeePayer11111111111111111111111111111111111",
                    "Bridge1111111111111111111111111111111111111",
                ],
                "instructions": [
                    {"programId": "Bridge1111111111111111111111111111111111111"}
                ],
            },
        },
        "meta": {},
        "slot": 100,
        "blockTime": 1700000000,
    }

    event = await adapter.to_canonical(raw_tx)
    assert event.event_type == "bridge"
    assert event.metadata.get("bridge_program")
