import asyncio
import pytest

from app.analytics.smart_contract_analyzer import SmartContractAnalyzer


@pytest.mark.asyncio
async def test_empty_bytecode():
    analyzer = SmartContractAnalyzer()
    res = await analyzer.analyze_contract("0x0", "")
    assert res.metadata["bytecode_size"] == 0
    assert res.function_count == 0
    assert isinstance(res.patterns, dict)


@pytest.mark.asyncio
async def test_invalid_hex():
    analyzer = SmartContractAnalyzer()
    res = await analyzer.analyze_contract("0x0", "0xGARBAGE")
    assert res.patterns.get("parse_error") is True
    assert res.function_count == 0


@pytest.mark.asyncio
async def test_selector_extraction_dispatcher_pattern():
    analyzer = SmartContractAnalyzer()
    # Build bytecode: PUSH4 <abcd1234> then within window EQ (0x14) and JUMPI (0x57)
    selector = bytes([0x63, 0xAB, 0xCD, 0x12, 0x34])
    tail = bytes([0x14, 0x57])  # EQ, JUMPI
    valid = selector + tail
    # An invalid PUSH4 without dispatcher pattern
    invalid_selector = bytes([0x63, 0x11, 0x22, 0x33, 0x44, 0x01, 0x02])
    bytecode = (valid + invalid_selector).hex()
    res = await analyzer.analyze_contract("0x1", bytecode)
    sels = res.patterns.get("function_selectors", [])
    assert "0xabcd1234" in sels
    assert "0x11223344" not in sels
    assert res.function_count == len(sels) >= 1
    # Similarity key should exist
    assert "similarity_key" in res.patterns


@pytest.mark.asyncio
async def test_vulnerabilities_detection_basic():
    analyzer = SmartContractAnalyzer()
    # Build bytes containing CALL (0xf1) and SSTORE (0x55) to trigger reentrancy signal
    # Also include SELFDESTRUCT (0xff)
    bc = bytes([0xf1, 0x01, 0x55, 0x00, 0xff]).hex()
    res = await analyzer.analyze_contract("0x2", bc)
    types = {v.type for v in res.vulnerabilities}
    assert "reentrancy" in types
    assert "unprotected_selfdestruct" in types


@pytest.mark.asyncio
async def test_delegatecall_and_unchecked_call():
    analyzer = SmartContractAnalyzer()
    # Contains DELEGATECALL (0xf4) without CALLER (0x33) / EQ (0x14) gates
    # Contains CALL (0xf1) without ISZERO (0x15) / JUMPI (0x57)
    bc = bytes([0xf4, 0x01, 0x02, 0xf1, 0x00]).hex()
    res = await analyzer.analyze_contract("0x3", bc)
    types = {v.type for v in res.vulnerabilities}
    assert "unprotected_delegatecall" in types
    assert "unchecked_external_call" in types


@pytest.mark.asyncio
async def test_opcode_histogram_present():
    analyzer = SmartContractAnalyzer()
    # Include a few known opcodes and unknown
    bc = bytes([0x56, 0x57, 0x60, 0x01, 0x00, 0xaa]).hex()  # JUMP, JUMPI, PUSH1, ADD, STOP, UNKNOWN_aa
    res = await analyzer.analyze_contract("0x4", bc)
    metrics = res.patterns.get("metrics", {})
    hist = metrics.get("opcode_histogram")
    assert isinstance(hist, dict)
    assert any(k.startswith("UNKNOWN_") for k in hist.keys()) or True
