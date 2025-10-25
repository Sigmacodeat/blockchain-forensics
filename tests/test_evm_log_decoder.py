import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.evm_log_decoder import get_event_name, decode_event, register_topics  # noqa: E402


def test_get_event_name_known_transfer():
    topic0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    assert get_event_name(topic0) == "Transfer"


def test_decode_event_with_topics():
    log = {"topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]}
    dec = decode_event(log)
    assert dec["event_name"] == "Transfer"
    assert dec["topic0"].startswith("0xddf")


def test_register_topics_and_env_map(monkeypatch):
    custom_map = {"0xaaaa": "CustomEvent"}
    register_topics(custom_map)
    assert get_event_name("0xAAAA") == "CustomEvent"

    # Env-driven mapping takes effect on import; simulate by reloading module
    monkeypatch.setenv("BRIDGE_TOPIC_MAP_JSON", '{"0xbbbb":"EnvEvent"}')
    import importlib
    mod = importlib.import_module("app.services.evm_log_decoder")
    importlib.reload(mod)
    assert mod.get_event_name("0xBBBB") == "EnvEvent"
