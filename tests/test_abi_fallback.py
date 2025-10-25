import os
import sys
import pathlib
import pytest
import asyncio

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.enrichment.abi_signatures import resolve_selector_name  # noqa: E402
from app.adapters.ethereum_adapter import EthereumAdapter  # noqa: E402


def test_resolve_selector_name_basic():
    assert resolve_selector_name("0xa9059cbbdeadbeef") == "transfer(address,uint256)"
    assert resolve_selector_name("0x095ea7b3cafebabe") == "approve(address,uint256)"
    assert resolve_selector_name("0x00000000") is None
    assert resolve_selector_name(None) is None


@pytest.mark.asyncio
async def test_adapter_method_selector_fallback():
    adapter = EthereumAdapter(rpc_url=None)
    # Disable web3 to avoid external RPC calls; use adapter's offline paths
    adapter.w3 = None  # type: ignore

    raw_tx = {
        "hash": b"\x12\x34\x56",  # minimal bytes acceptable to _hash_str
        "from": "0x1111111111111111111111111111111111111111",
        "to": "0x2222222222222222222222222222222222222222",
        # selector for transfer + a few bytes (not decodable for full ABI)
        "input": "0xa9059cbb0000000000000000000000003333333333333333333333333333333333333333",
        "value": 0,
        "gasPrice": 1,
        "transactionIndex": 0,
        "chainId": 1,
        "nonce": 0,
    }
    block_data = {"number": 1, "timestamp": int(1700000000)}

    event = await adapter.transform_transaction(raw_tx, block_data)
    assert event.method_name == "transfer(address,uint256)"
    assert event.event_type in {"contract_call", "token_transfer", "dex_swap", "bridge", "unknown", "transfer"}
