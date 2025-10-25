import pytest

from app.analytics.smart_contract_analyzer import smart_contract_analyzer

@pytest.mark.asyncio
async def test_selector_extraction_and_vuln_detection():
    # Craft minimal bytecode with two PUSH4 selectors and vulnerable patterns
    # 0x63 <4 bytes> is PUSH4
    sel1 = bytes.fromhex('a9059cbb')  # transfer(address,uint256)
    sel2 = bytes.fromhex('095ea7b3')  # approve(address,uint256)
    # Compose: PUSH4 sel1; PUSH4 sel2; CALL; SSTORE; SELFDESTRUCT; DELEGATECALL; REVERT
    bytecode = bytes([0x63]) + sel1 + bytes([0x63]) + sel2 + bytes([
        0xF1,  # CALL
        0x55,  # SSTORE (reentrancy heuristic)
        0xFF,  # SELFDESTRUCT
        0xF4,  # DELEGATECALL (proxy)
        0xFD,  # REVERT (honeypot score)
    ])
    result = await smart_contract_analyzer.analyze_contract('0xdeadbeef', '0x' + bytecode.hex())

    # Function selectors
    assert result.function_count >= 2
    selectors = result.patterns.get('function_selectors', [])
    assert '0xa9059cbb' in selectors and '0x095ea7b3' in selectors

    # Vulnerabilities
    vuln_types = {v.type for v in result.vulnerabilities}
    assert 'reentrancy' in vuln_types
    assert 'unprotected_selfdestruct' in vuln_types

    # Patterns
    assert result.patterns.get('is_proxy') is True
    assert result.patterns.get('honeypot_score', 0) >= 0.5
    assert isinstance(result.patterns.get('similarity_key'), str) and len(result.patterns['similarity_key']) == 40
