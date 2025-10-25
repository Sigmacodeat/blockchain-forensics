import os
import pytest
from fastapi.testclient import TestClient
from app.auth.jwt import create_access_token
from app.auth.models import UserRole

os.environ["TEST_MODE"] = "1"

from app.main import app

client = TestClient(app)

@pytest.mark.parametrize("bytecode_hex", [
    # PUSH4 a9059cbb; PUSH4 095ea7b3; CALL; SSTORE; REVERT
    "0x63a9059cbb63095ea7b3f155fd"
])
def test_analyze_contract_bytecode_ok(bytecode_hex):
    payload = {
        "address": "0xDeaDbeEfDeaDbeEfDeaDbeEfDeaDbeEfDeaDbeEf",
        "bytecode": bytecode_hex,
    }
    token = create_access_token("u1", "u1@example.com", UserRole.VIEWER, plan="pro")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/v1/contracts/analyze/bytecode", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["address"].lower().startswith("0xdeadbeef")
    assert isinstance(data.get("bytecode_hash"), str)
    assert data.get("function_count", 0) >= 0
    patterns = data.get("patterns", {})
    assert patterns.get("is_proxy") in (True, False)
    sels = patterns.get("function_selectors", [])
    hist = (patterns.get("metrics") or {}).get("opcode_histogram", {})
    # Accept either explicit selectors or histogram indicating PUSH4 occurrences
    assert (any(s in sels for s in ("0xa9059cbb", "0x095ea7b3"))) or (hist.get("PUSH4", 0) >= 1)
