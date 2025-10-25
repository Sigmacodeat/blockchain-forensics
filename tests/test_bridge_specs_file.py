import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.evm_log_decoder import EVENT_SPECS, _load_file_event_specs  # noqa: E402


def test_bridge_specs_file_loading():
    # Check that file-based specs are loaded
    specs = _load_file_event_specs()
    assert isinstance(specs, dict)
    assert len(specs) > 0

    # Check a known spec
    transfer_spec = specs.get("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")
    assert transfer_spec is not None
    assert transfer_spec["name"] == "Transfer"
    assert transfer_spec["sender_index"] == 1
    assert transfer_spec["receiver_index"] == 2
    assert transfer_spec["amount_word_index"] == 0

    # Verify EVENT_SPECS includes file specs
    assert "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef" in EVENT_SPECS
