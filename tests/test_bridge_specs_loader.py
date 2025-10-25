import os
import sys
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import importlib


def test_event_specs_env_loader(monkeypatch):
    # Prepare a fake spec for a dummy topic0
    topic0 = "0xabc123"
    specs = {
        topic0: {
            "name": "SendToChain",
            "sender_index": 1,
            "receiver_index": 2,
            "amount_word_index": 0,
            "token_is_contract": True,
        }
    }
    monkeypatch.setenv("BRIDGE_EVENT_SPECS_JSON", json.dumps(specs))
    # Force reload module to apply env
    mod = importlib.import_module("app.services.evm_log_decoder")
    importlib.reload(mod)

    # Build a dummy log according to spec
    from_addr = "0x" + ("00"*12) + "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"[-40:]
    to_addr = "0x" + ("00"*12) + "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"[-40:]
    amount_hex = ("0"*64)
    log = {"topics": [topic0, from_addr, to_addr], "data": "0x" + amount_hex}

    dec = mod.decode_bridge_log("ethereum", "0xBridge", log)
    assert dec["event_name"] == "SendToChain"
    assert dec["sender"].endswith("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    assert dec["receiver"].endswith("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    assert isinstance(dec["confidence"], float) and dec["confidence"] >= 0.85
