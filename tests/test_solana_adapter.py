import os
import sys
import pathlib
import pytest
from datetime import datetime

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.adapters.solana_adapter import SolanaAdapter  # noqa: E402


@pytest.mark.asyncio
async def test_to_canonical_parsed_transfer():
    adapter = SolanaAdapter(rpc_url="mock://solana")
    raw_tx = {
        "transaction": {
            "signatures": ["sig123"],
            "message": {
                "accountKeys": ["fromKey", "toKey"],
                "instructions": [
                    {"parsed": {"type": "transfer", "info": {
                        "mint": "mintX", "source": "fromKey", "destination": "toKey",
                        "tokenAmount": {"uiAmount": 42.0, "decimals": 6}
                    }}}
                ],
            },
        },
        "meta": {"preBalances": [1000000000], "postBalances": [900000000]},
        "blockTime": int(datetime.utcnow().timestamp()),
        "slot": 123,
    }
    evt = await adapter.to_canonical(raw_tx)
    assert evt.chain == "solana"
    assert evt.event_type == "token_transfer"
    assert evt.from_address == "fromKey"
    assert evt.to_address == "toKey"
    assert evt.metadata.get("token_mint") == "mintX"


@pytest.mark.asyncio
async def test_to_canonical_balance_delta_fallback():
    adapter = SolanaAdapter(rpc_url="mock://solana")
    raw_tx = {
        "transaction": {
            "signatures": ["sig456"],
            "message": {
                "accountKeys": ["A", "B"],
                "instructions": [],
            },
        },
        "meta": {
            "preBalances": [2000000000],
            "postBalances": [1500000000],
            "preTokenBalances": [
                {"owner": "A", "mint": "mintY", "uiTokenAmount": {"amount": "1000", "decimals": 3}}
            ],
            "postTokenBalances": [
                {"owner": "B", "mint": "mintY", "uiTokenAmount": {"amount": "2000", "decimals": 3}}
            ],
        },
        "blockTime": int(datetime.utcnow().timestamp()),
        "slot": 124,
    }
    evt = await adapter.to_canonical(raw_tx)
    assert evt.event_type == "token_transfer"
    assert evt.metadata.get("token_mint") == "mintY"
    # Check that numeric conversion worked
    assert isinstance(evt.metadata.get("token_delta_ui"), float)
