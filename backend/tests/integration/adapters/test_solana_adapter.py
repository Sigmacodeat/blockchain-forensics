import pytest
from app.adapters.solana_adapter import create_solana_adapter

pytestmark = pytest.mark.asyncio


async def test_solana_token_transfer_parsed_instructions(monkeypatch):
    # no RPC needed; call to_canonical directly
    adapter = create_solana_adapter("")
    raw_tx = {
        "transaction": {
            "signatures": ["sig123"],
            "message": {
                "accountKeys": [
                    "FromTokenAccount11111111111111111111111111111",
                    "ToTokenAccount22222222222222222222222222222",
                ],
                "instructions": [
                    {
                        "parsed": {
                            "type": "transferChecked",
                            "info": {
                                "mint": "TokenMintXYZ",
                                "source": "FromTokenAccount11111111111111111111111111111",
                                "destination": "ToTokenAccount22222222222222222222222222222",
                                "tokenAmount": {"uiAmount": 12.34, "decimals": 6},
                            },
                        }
                    }
                ],
            },
        },
        "meta": {
            "innerInstructions": [],
            "preBalances": [1000000000],
            "postBalances": [999000000],
        },
        "slot": 123,
        "blockTime": 1700000000,
    }

    evt = await adapter.to_canonical(raw_tx)
    assert evt.event_type == "token_transfer"
    assert evt.metadata.get("token_mint") == "TokenMintXYZ"
    assert evt.metadata.get("from_owner").startswith("FromTokenAccount")
    assert evt.metadata.get("to_owner").startswith("ToTokenAccount")
    assert isinstance(evt.metadata.get("token_amount_ui"), (int, float))


async def test_solana_bridge_detection_account_keys(monkeypatch):
    adapter = create_solana_adapter("")
    # configure bridge programs via env-like settings if accessible; here we set attribute directly
    from app.config import settings
    settings.BRIDGE_PROGRAMS_SOL = ["BridgeProgExample1111111111111111111111111111"]

    raw_tx = {
        "transaction": {
            "signatures": ["sig456"],
            "message": {
                "accountKeys": [
                    "SomeKey",
                    "BridgeProgExample1111111111111111111111111111",
                ],
                "instructions": [],
            },
        },
        "meta": {"innerInstructions": [], "preBalances": [0], "postBalances": [0]},
        "slot": 456,
        "blockTime": 1700000100,
    }

    evt = await adapter.to_canonical(raw_tx)
    assert evt.event_type == "bridge"
    assert evt.metadata.get("bridge_program").lower() == settings.BRIDGE_PROGRAMS_SOL[0].lower()
