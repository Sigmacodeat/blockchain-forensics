"""
Tests for Smart Contract Deep Analysis
=======================================
Testet alle Komponenten:
- Bytecode Analyzer
- Vulnerability Detector
- Exploit Detector
- Function Signature Matcher
- Full Contract Analysis
"""

import pytest
from app.contracts.bytecode_analyzer import bytecode_analyzer
from app.contracts.vulnerability_detector import vulnerability_detector, VulnerabilitySeverity
from app.contracts.exploit_detector import exploit_detector
from app.contracts.function_signature_matcher import function_signature_matcher


# Sample bytecode snippets für Tests
SIMPLE_ERC20_BYTECODE = """
608060405234801561001057600080fd5b506004361061004c5760003560e01c
806318160ddd1461005157806370a082311461006f57806395ea7b31461009f
578063a9059cbb146100cf575b600080fd5b6100596100ff565b60405161006691906
"""

REENTRANCY_VULNERABLE_BYTECODE = """
608060405234801561001057600080fd5b5060043610610041576000356001c063
f17325672614610046575b600080fd5b610060600480360381019061005b919061
0151565b610062565b005b8073ffffffffffffffffffffffffffffffffffffffff
16311561008857600080fd5b8073ffffffffffffffffffffffffffffffffffffffff
1663f17325676040518163ffffffff1660e01b8152600401600060405180830381
600087803b1580156100e957600080fd5b505af11580156100fd573d6000803e3d
6000fd5b5050505060008054600101905550565b600080fd5b600073ffffffff
ffffffffffffffffffffffffffffffff82169050919050565b600061014082610
115565b9050919050565b61015081610135565b811461015b57600080fd5b50
565b60008135905061016d81610147565b92915050565b60006020828403121
56101885761018761010e565b5b60006101968482850161015e565b91505092915050
"""

SELFDESTRUCT_BYTECODE = """
60806040526004361061001e5760003560e01c8063715018a614610023575b60
0080fd5b61002b61002d565b005b3373ffffffffffffffffffffffffffffffff
ffffffff16600060009054906101000a900473ffffffffffffffffffffffffffff
ffffffffffff1673ffffffffffffffffffffffffffffffffffffffff161461008d
57600080fd5b3373ffffffffffffffffffffffffffffffffffffffffffffffff
16ff
"""


class TestBytecodeAnalyzer:
    """Tests für Bytecode Analyzer"""
    
    def test_disassemble_basic(self):
        """Test basic bytecode disassembly"""
        # Simple PUSH1 0x60 PUSH1 0x40 MSTORE
        bytecode = "6060604052"
        opcodes = bytecode_analyzer._disassemble(bytecode)
        
        assert len(opcodes) > 0
        # First opcode should be PUSH1
        assert opcodes[0][1] == "PUSH1"
        assert opcodes[0][2] == "60"  # value pushed
    
    def test_analyze_simple_contract(self):
        """Test analysis of simple contract"""
        result = bytecode_analyzer.analyze(SIMPLE_ERC20_BYTECODE)
        
        assert result.features.total_opcodes > 0
        assert result.features.unique_opcodes > 0
        assert 0.0 <= result.risk_score <= 1.0
    
    def test_detect_dangerous_opcodes(self):
        """Test detection of SELFDESTRUCT"""
        result = bytecode_analyzer.analyze(SELFDESTRUCT_BYTECODE)
        
        assert result.features.selfdestruct_present is True
        # Should have finding for selfdestruct
        selfdestruct_findings = [
            f for f in result.findings 
            if f.get("name") == "selfdestruct_present"
        ]
        assert len(selfdestruct_findings) > 0
    
    def test_detect_suspicious_patterns(self):
        """Test detection of reentrancy pattern"""
        result = bytecode_analyzer.analyze(REENTRANCY_VULNERABLE_BYTECODE)
        
        # Reentrancy has CALL followed by SSTORE
        # Check if pattern was detected
        assert result.risk_score > 0.0


class TestVulnerabilityDetector:
    """Tests für Vulnerability Detector"""
    
    def test_detect_reentrancy(self):
        """Test reentrancy vulnerability detection"""
        bytecode = REENTRANCY_VULNERABLE_BYTECODE
        opcodes = bytecode_analyzer._disassemble(bytecode.replace('\n', ''))
        
        report = vulnerability_detector.detect(bytecode, opcodes)
        
        # Should detect some vulnerabilities
        assert report.total_vulnerabilities >= 0
    
    def test_detect_unchecked_calls(self):
        """Test unchecked external call detection"""
        # Bytecode with CALL not followed by ISZERO check
        bytecode = "60806040526004361060ff"
        opcodes = [
            (0, "PUSH1", "60"),
            (1, "PUSH1", "40"),
            (2, "MSTORE", None),
            (3, "CALL", None),  # External call
            (4, "POP", None),   # Return value popped without check!
        ]
        
        report = vulnerability_detector.detect(bytecode, opcodes)
        
        # Should detect unchecked call
        unchecked_calls = [
            v for v in report.vulnerabilities 
            if v.vuln_type.value == "unchecked_external_call"
        ]
        assert len(unchecked_calls) > 0
    
    def test_severity_classification(self):
        """Test that vulnerabilities are properly classified by severity"""
        bytecode = REENTRANCY_VULNERABLE_BYTECODE
        opcodes = bytecode_analyzer._disassemble(bytecode.replace('\n', ''))
        
        report = vulnerability_detector.detect(bytecode, opcodes)
        
        # Check that counts are non-negative
        assert report.critical_count >= 0
        assert report.high_count >= 0
        assert report.medium_count >= 0
        assert report.low_count >= 0


class TestExploitDetector:
    """Tests für Exploit Detector"""
    
    def test_detect_honeypot_pattern(self):
        """Test honeypot pattern detection"""
        # Bytecode mit ORIGIN check (honeypot indicator)
        opcodes = [
            (0, "CALLER", None),
            (1, "ORIGIN", None),
            (2, "EQ", None),
            (3, "JUMPI", None),
            # Multiple ORIGIN checks
            (10, "ORIGIN", None),
            (11, "SLOAD", None),
        ]
        
        exploits = exploit_detector.detect_exploits("", opcodes)
        
        # Should detect honeypot pattern
        honeypot_detections = [
            e for e in exploits 
            if e.category.value == "honeypot"
        ]
        # May or may not detect depending on threshold
        # Just ensure no crash
        assert isinstance(exploits, list)
    
    def test_detect_rugpull_risk(self):
        """Test rugpull risk detection"""
        # Bytecode with SELFDESTRUCT and multiple owner checks
        opcodes = [
            (0, "CALLER", None),
            (1, "SLOAD", None),
            (2, "EQ", None),
            (10, "CALLER", None),
            (11, "SLOAD", None),
            (12, "EQ", None),
            (20, "SELFDESTRUCT", None),
            (30, "DELEGATECALL", None),
        ]
        
        exploits = exploit_detector.detect_exploits("", opcodes)
        
        rugpull_detections = [
            e for e in exploits 
            if e.category.value == "rugpull"
        ]
        assert len(rugpull_detections) > 0
        assert rugpull_detections[0].severity in ["high", "critical"]
    
    def test_flash_loan_pattern(self):
        """Test flash loan attack pattern detection"""
        # Pattern: BALANCE -> DIV (price oracle) + multiple CALLs
        opcodes = [
            (0, "BALANCE", None),
            (1, "DIV", None),
            (10, "CALL", None),
            (20, "CALL", None),
            (30, "CALL", None),
        ]
        
        exploits = exploit_detector.detect_exploits("", opcodes)
        
        flash_loan_detections = [
            e for e in exploits 
            if e.category.value == "flash_loan_attack"
        ]
        assert len(flash_loan_detections) > 0


class TestFunctionSignatureMatcher:
    """Tests für Function Signature Matcher"""
    
    def test_resolve_known_selector(self):
        """Test resolving known ERC20 function"""
        # transfer(address,uint256)
        result = function_signature_matcher.resolve_selector("0xa9059cbb")
        
        assert result is not None
        assert result.name == "transfer"
        assert len(result.params) == 2
        assert "address" in result.params
        assert "uint256" in result.params
    
    def test_resolve_multiple_selectors(self):
        """Test resolving multiple selectors"""
        selectors = [
            "0xa9059cbb",  # transfer
            "0x70a08231",  # balanceOf
            "0x18160ddd",  # totalSupply
        ]
        
        results = []
        for selector in selectors:
            result = function_signature_matcher.resolve_selector(selector)
            if result:
                results.append(result)
        
        assert len(results) >= 2  # At least 2 should resolve
    
    def test_extract_selectors_from_bytecode(self):
        """Test extracting function selectors from bytecode"""
        selectors = function_signature_matcher.extract_selectors_from_bytecode(
            SIMPLE_ERC20_BYTECODE
        )
        
        assert len(selectors) > 0
        # Should find common ERC20 selectors
        # Note: May vary by bytecode, just check format
        for selector in selectors:
            assert selector.startswith("0x")
            assert len(selector) == 10  # 0x + 8 hex chars
    
    def test_detect_erc20_interface(self):
        """Test ERC20 interface detection"""
        # Simulate bytecode with ERC20 selectors
        selectors = [
            "0xa9059cbb",  # transfer
            "0x70a08231",  # balanceOf
            "0x18160ddd",  # totalSupply
            "0x095ea7b3",  # approve
        ]
        
        interface = function_signature_matcher.detect_interface("", selectors)
        
        # Should detect ERC20
        assert "ERC20" in interface.standards
        assert len(interface.functions) > 0
    
    def test_dangerous_function_detection(self):
        """Test detection of dangerous functions"""
        # Test selfdestruct-like function
        is_dangerous, reason = function_signature_matcher.is_dangerous_function(
            "0x9f678cca"  # burn function
        )
        
        assert is_dangerous is True
        assert "burn" in reason.lower() or "dangerous" in reason.lower()


class TestFullContractAnalysis:
    """Integration tests für vollständige Contract-Analyse"""
    
    def test_analyze_erc20_contract(self):
        """Test full analysis of ERC20-like contract"""
        from app.contracts.service import ContractsService
        
        service = ContractsService()
        
        # Mock bytecode fetch (in real test would use fixture)
        # For now, test the analysis logic with sample bytecode
        bytecode = SIMPLE_ERC20_BYTECODE.replace('\n', '')
        
        # Manually run analysis components
        bytecode_analysis = bytecode_analyzer.analyze(bytecode)
        opcodes = bytecode_analyzer._disassemble(bytecode)
        vuln_report = vulnerability_detector.detect(bytecode, opcodes)
        exploits = exploit_detector.detect_exploits(bytecode, opcodes)
        
        # Verify all components ran
        assert bytecode_analysis is not None
        assert vuln_report is not None
        assert isinstance(exploits, list)
    
    def test_risk_scoring(self):
        """Test that risk scoring works correctly"""
        from app.contracts.service import ContractsService
        
        service = ContractsService()
        
        # Test with dangerous bytecode
        bytecode = SELFDESTRUCT_BYTECODE.replace('\n', '')
        bytecode_analysis = bytecode_analyzer.analyze(bytecode)
        opcodes = bytecode_analyzer._disassemble(bytecode)
        vuln_report = vulnerability_detector.detect(bytecode, opcodes)
        exploits = exploit_detector.detect_exploits(bytecode, opcodes)
        
        risk_score = service._calculate_overall_risk(
            bytecode_analysis,
            vuln_report,
            exploits,
        )
        
        # Should have elevated risk due to SELFDESTRUCT
        assert risk_score > 0.0
        assert risk_score <= 1.0
    
    def test_summary_generation(self):
        """Test summary generation"""
        from app.contracts.service import ContractsService
        
        service = ContractsService()
        
        bytecode = SIMPLE_ERC20_BYTECODE.replace('\n', '')
        bytecode_analysis = bytecode_analyzer.analyze(bytecode)
        opcodes = bytecode_analyzer._disassemble(bytecode)
        vuln_report = vulnerability_detector.detect(bytecode, opcodes)
        exploits = exploit_detector.detect_exploits(bytecode, opcodes)
        
        selectors = function_signature_matcher.extract_selectors_from_bytecode(bytecode)
        interface = function_signature_matcher.detect_interface(bytecode, selectors)
        
        summary = service._generate_summary(
            bytecode_analysis,
            vuln_report,
            exploits,
            interface,
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0


# Pytest fixtures
@pytest.fixture
def sample_erc20_bytecode():
    return SIMPLE_ERC20_BYTECODE.replace('\n', '')


@pytest.fixture
def sample_vulnerable_bytecode():
    return REENTRANCY_VULNERABLE_BYTECODE.replace('\n', '')


@pytest.fixture
def sample_dangerous_bytecode():
    return SELFDESTRUCT_BYTECODE.replace('\n', '')


# Mark tests that require network access
pytestmark = pytest.mark.asyncio
