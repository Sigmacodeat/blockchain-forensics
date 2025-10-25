import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.evm_log_decoder import decode_bridge_log  # noqa: E402


def test_decode_bridge_log_erc20_transfer_basic():
    chain_id = "ethereum"
    contract = "0xToken"
    # ERC20 Transfer topic0
    topic0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    # topics: [topic0, from, to] as 32-byte hex padded
    from_addr = "0x" + ("00"*12) + "1111111111111111111111111111111111111111"[-40:]
    to_addr = "0x" + ("00"*12) + "2222222222222222222222222222222222222222"[-40:]
    amount_hex = hex(123456789)[2:].rjust(64, "0")
    log = {
        "topics": [topic0, from_addr, to_addr],
        "data": "0x" + amount_hex,
    }
    dec = decode_bridge_log(chain_id, contract, log)
    assert dec["event_name"] == "Transfer"
    assert dec["sender"].endswith("1111111111111111111111111111111111111111")
    assert dec["receiver"].endswith("2222222222222222222222222222222222222222")
    assert dec["amount"] == 123456789
    assert dec["token"] == contract
    assert dec["confidence"] >= 0.9
