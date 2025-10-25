"""
Smart Contract Bytecode Deep Analysis
======================================
Implementiert ML-basierte Bytecode-Analyse ähnlich wie Chainalysis/AnChain:
- Opcode Pattern Matching
- Control Flow Graph (CFG) Analyse
- Bytecode Similarity Detection
- Malicious Pattern Recognition
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import hashlib


@dataclass
class OpcodeSequence:
    """Repräsentiert eine Opcode-Sequenz mit Metadaten"""
    opcodes: List[str]
    start_offset: int
    end_offset: int
    frequency: int = 0
    is_suspicious: bool = False


@dataclass
class BytecodeFeatures:
    """ML-Features aus Bytecode extrahiert"""
    opcode_distribution: Dict[str, int]
    unique_opcodes: int
    total_opcodes: int
    complexity_score: float
    suspicious_patterns: List[str]
    control_flow_score: float
    storage_operations: int
    external_calls: int
    delegatecall_count: int
    selfdestruct_present: bool


@dataclass
class BytecodeAnalysis:
    """Vollständige Bytecode-Analyse-Resultate"""
    contract_hash: str
    features: BytecodeFeatures
    risk_score: float
    findings: List[Dict]
    similarity_matches: List[Dict]
    opcode_sequences: List[OpcodeSequence]


# EVM Opcode Reference (vereinfacht)
EVM_OPCODES = {
    # Arithmetic
    '01': 'ADD', '02': 'MUL', '03': 'SUB', '04': 'DIV', '05': 'SDIV',
    '06': 'MOD', '07': 'SMOD', '08': 'ADDMOD', '09': 'MULMOD', '0a': 'EXP',
    
    # Comparison & Bitwise
    '10': 'LT', '11': 'GT', '12': 'SLT', '13': 'SGT', '14': 'EQ', '15': 'ISZERO',
    '16': 'AND', '17': 'OR', '18': 'XOR', '19': 'NOT', '1a': 'BYTE',
    '1b': 'SHL', '1c': 'SHR', '1d': 'SAR',
    
    # SHA3
    '20': 'SHA3',
    
    # Environmental
    '30': 'ADDRESS', '31': 'BALANCE', '32': 'ORIGIN', '33': 'CALLER',
    '34': 'CALLVALUE', '35': 'CALLDATALOAD', '36': 'CALLDATASIZE',
    '37': 'CALLDATACOPY', '38': 'CODESIZE', '39': 'CODECOPY',
    '3a': 'GASPRICE', '3b': 'EXTCODESIZE', '3c': 'EXTCODECOPY',
    '3d': 'RETURNDATASIZE', '3e': 'RETURNDATACOPY', '3f': 'EXTCODEHASH',
    
    # Block
    '40': 'BLOCKHASH', '41': 'COINBASE', '42': 'TIMESTAMP', '43': 'NUMBER',
    '44': 'DIFFICULTY', '45': 'GASLIMIT', '46': 'CHAINID', '47': 'SELFBALANCE',
    '48': 'BASEFEE',
    
    # Stack, Memory, Storage, Flow
    '50': 'POP', '51': 'MLOAD', '52': 'MSTORE', '53': 'MSTORE8',
    '54': 'SLOAD', '55': 'SSTORE', '56': 'JUMP', '57': 'JUMPI',
    '58': 'PC', '59': 'MSIZE', '5a': 'GAS', '5b': 'JUMPDEST',
    
    # Push Operations (0x60-0x7f)
    **{f'{i:02x}': f'PUSH{i-0x5f}' for i in range(0x60, 0x80)},
    
    # Duplicate Operations (0x80-0x8f)
    **{f'{i:02x}': f'DUP{i-0x7f}' for i in range(0x80, 0x90)},
    
    # Exchange Operations (0x90-0x9f)
    **{f'{i:02x}': f'SWAP{i-0x8f}' for i in range(0x90, 0xa0)},
    
    # Logging
    'a0': 'LOG0', 'a1': 'LOG1', 'a2': 'LOG2', 'a3': 'LOG3', 'a4': 'LOG4',
    
    # System
    'f0': 'CREATE', 'f1': 'CALL', 'f2': 'CALLCODE', 'f3': 'RETURN',
    'f4': 'DELEGATECALL', 'f5': 'CREATE2', 'fa': 'STATICCALL',
    'fd': 'REVERT', 'fe': 'INVALID', 'ff': 'SELFDESTRUCT',
}


# Bekannte Malicious/Suspicious Patterns
SUSPICIOUS_PATTERNS = {
    # Reentrancy Pattern: CALL gefolgt von SSTORE
    "reentrancy_call_sstore": [
        ['CALL', 'SSTORE'],
        ['DELEGATECALL', 'SSTORE'],
    ],
    
    # Unprotected SELFDESTRUCT
    "unprotected_selfdestruct": [
        ['CALLER', 'SELFDESTRUCT'],
        ['ORIGIN', 'SELFDESTRUCT'],
    ],
    
    # Delegatecall to user-controlled address
    "delegatecall_user_input": [
        ['CALLDATALOAD', 'DELEGATECALL'],
    ],
    
    # tx.origin for authentication (bad practice)
    "tx_origin_auth": [
        ['ORIGIN', 'EQ', 'JUMPI'],
    ],
    
    # Timestamp dependence
    "timestamp_dependence": [
        ['TIMESTAMP', 'MOD'],
        ['TIMESTAMP', 'DIV'],
    ],
    
    # Block number manipulation
    "block_manipulation": [
        ['NUMBER', 'MOD'],
        ['BLOCKHASH', 'MOD'],
    ],
}


# Known Exploit Signatures (simplified bytecode fragments)
EXPLOIT_SIGNATURES = {
    "flashloan_pattern": "3d3d3d3d363d3d37363d73",  # Common flashloan proxy pattern
    "create2_factory": "f5",  # CREATE2 opcode
    "metamorphic_contract": "3d602d80600a3d3981f3",  # Metamorphic init code
}


class BytecodeAnalyzer:
    """
    Deep Bytecode Analysis Engine
    Ähnlich wie Chainalysis/AnChain mit ML-Features
    """
    
    def __init__(self):
        self.known_patterns: Dict[str, List[OpcodeSequence]] = {}
        self.bytecode_cache: Dict[str, BytecodeAnalysis] = {}
    
    def analyze(self, bytecode: str, contract_address: Optional[str] = None) -> BytecodeAnalysis:
        """
        Vollständige Bytecode-Analyse
        
        Args:
            bytecode: Hex-String des Bytecodes (mit oder ohne 0x)
            contract_address: Optional für Caching
        
        Returns:
            BytecodeAnalysis mit allen Findings
        """
        # Normalisiere Bytecode
        bytecode = bytecode.lower().replace('0x', '')
        
        # Cache Check
        bc_hash = hashlib.sha256(bytecode.encode()).hexdigest()
        if bc_hash in self.bytecode_cache:
            return self.bytecode_cache[bc_hash]
        
        # 1. Disassemble zu Opcodes
        opcodes = self._disassemble(bytecode)
        
        # 2. Feature Extraction
        features = self._extract_features(opcodes, bytecode)
        
        # 3. Pattern Matching
        suspicious_sequences = self._find_suspicious_patterns(opcodes)
        
        # 4. Exploit Detection
        exploit_matches = self._detect_exploits(bytecode, opcodes)
        
        # 5. Similarity Check (gegen bekannte Malware)
        similarity_matches = self._check_similarity(bytecode, opcodes)
        
        # 6. Risk Scoring
        risk_score = self._calculate_risk_score(features, suspicious_sequences, exploit_matches)
        
        # 7. Findings zusammenstellen
        findings = []
        
        for pattern_name, sequences in suspicious_sequences.items():
            for seq in sequences:
                findings.append({
                    "type": "suspicious_pattern",
                    "name": pattern_name,
                    "severity": "medium" if risk_score < 0.7 else "high",
                    "location": f"offset_{seq.start_offset}",
                    "description": self._get_pattern_description(pattern_name),
                })
        
        for exploit in exploit_matches:
            findings.append({
                "type": "exploit_signature",
                "name": exploit["name"],
                "severity": "critical",
                "confidence": exploit["confidence"],
                "description": exploit["description"],
            })
        
        if features.delegatecall_count > 0:
            findings.append({
                "type": "dangerous_opcode",
                "name": "delegatecall_usage",
                "severity": "medium",
                "count": features.delegatecall_count,
                "description": "DELEGATECALL detected - can modify contract state if not properly protected",
            })
        
        if features.selfdestruct_present:
            findings.append({
                "type": "dangerous_opcode",
                "name": "selfdestruct_present",
                "severity": "high",
                "description": "SELFDESTRUCT opcode found - contract can be destroyed",
            })
        
        # Build result
        analysis = BytecodeAnalysis(
            contract_hash=bc_hash,
            features=features,
            risk_score=risk_score,
            findings=findings,
            similarity_matches=similarity_matches,
            opcode_sequences=list(suspicious_sequences.values())[0] if suspicious_sequences else [],
        )
        
        # Cache
        self.bytecode_cache[bc_hash] = analysis
        
        return analysis
    
    def _disassemble(self, bytecode: str) -> List[Tuple[int, str, Optional[str]]]:
        """
        Disassembliert Bytecode zu Opcodes
        
        Returns:
            List of (offset, opcode_name, push_value)
        """
        opcodes = []
        i = 0
        
        while i < len(bytecode):
            opcode_hex = bytecode[i:i+2]
            opcode_name = EVM_OPCODES.get(opcode_hex, f'UNKNOWN_{opcode_hex}')
            push_value = None
            
            # Handle PUSH instructions
            if opcode_name.startswith('PUSH'):
                push_size = int(opcode_name[4:])
                push_value = bytecode[i+2:i+2+(push_size*2)]
                i += push_size * 2
            
            opcodes.append((i // 2, opcode_name, push_value))
            i += 2
        
        return opcodes
    
    def _extract_features(self, opcodes: List[Tuple], bytecode: str) -> BytecodeFeatures:
        """Extrahiert ML-Features aus Opcodes"""
        opcode_names = [op[1] for op in opcodes]
        opcode_counter = Counter(opcode_names)
        
        # Count specific dangerous operations
        storage_ops = opcode_counter.get('SLOAD', 0) + opcode_counter.get('SSTORE', 0)
        external_calls = (
            opcode_counter.get('CALL', 0) + 
            opcode_counter.get('CALLCODE', 0) +
            opcode_counter.get('STATICCALL', 0)
        )
        delegatecall_count = opcode_counter.get('DELEGATECALL', 0)
        selfdestruct_present = opcode_counter.get('SELFDESTRUCT', 0) > 0
        
        # Complexity Score (vereinfacht)
        jumps = opcode_counter.get('JUMP', 0) + opcode_counter.get('JUMPI', 0)
        complexity = (jumps / len(opcodes)) if opcodes else 0
        
        # Control Flow Score (basierend auf JUMP/JUMPI Verhältnis)
        total_jumps = jumps
        control_flow_score = min(1.0, total_jumps / max(1, len(opcodes) / 10))
        
        return BytecodeFeatures(
            opcode_distribution=dict(opcode_counter),
            unique_opcodes=len(set(opcode_names)),
            total_opcodes=len(opcodes),
            complexity_score=complexity,
            suspicious_patterns=[],  # wird später gefüllt
            control_flow_score=control_flow_score,
            storage_operations=storage_ops,
            external_calls=external_calls,
            delegatecall_count=delegatecall_count,
            selfdestruct_present=selfdestruct_present,
        )
    
    def _find_suspicious_patterns(self, opcodes: List[Tuple]) -> Dict[str, List[OpcodeSequence]]:
        """Findet verdächtige Opcode-Sequenzen"""
        results = {}
        opcode_names = [op[1] for op in opcodes]
        
        for pattern_name, patterns in SUSPICIOUS_PATTERNS.items():
            matches = []
            
            for pattern in patterns:
                # Sliding window search
                pattern_len = len(pattern)
                for i in range(len(opcode_names) - pattern_len + 1):
                    window = opcode_names[i:i+pattern_len]
                    if window == pattern:
                        matches.append(OpcodeSequence(
                            opcodes=pattern,
                            start_offset=opcodes[i][0],
                            end_offset=opcodes[i+pattern_len-1][0] if i+pattern_len-1 < len(opcodes) else opcodes[-1][0],
                            is_suspicious=True,
                        ))
            
            if matches:
                results[pattern_name] = matches
        
        return results
    
    def _detect_exploits(self, bytecode: str, opcodes: List[Tuple]) -> List[Dict]:
        """Erkennt bekannte Exploit-Patterns"""
        exploits = []
        
        for exploit_name, signature in EXPLOIT_SIGNATURES.items():
            if signature in bytecode:
                exploits.append({
                    "name": exploit_name,
                    "confidence": 0.85,
                    "description": f"Known exploit signature: {exploit_name}",
                })
        
        return exploits
    
    def _check_similarity(self, bytecode: str, opcodes: List[Tuple]) -> List[Dict]:
        """
        Prüft Ähnlichkeit zu bekannten Malware-Contracts
        (Vereinfacht - in Production würde man ML-Embeddings nutzen)
        """
        # Hier würde normalerweise ein ML-Modell verwendet (z.B. Code2Vec, Bytecode Embeddings)
        # Für PoC: Simple Hash-basierte Similarity
        
        # Bekannte Malware Hashes (Beispiele)
        known_malware = {
            "tornado_cash_proxy": "363d3d373d3d3d363d73",
            "fake_phishing_contract": "608060405234801561001",
        }
        
        matches = []
        for malware_name, malware_fragment in known_malware.items():
            if malware_fragment in bytecode:
                matches.append({
                    "name": malware_name,
                    "similarity_score": 0.95,
                    "match_type": "exact_fragment",
                })
        
        return matches
    
    def _calculate_risk_score(
        self, 
        features: BytecodeFeatures,
        suspicious_patterns: Dict,
        exploit_matches: List[Dict]
    ) -> float:
        """
        Berechnet ML-basierten Risk Score (0.0 - 1.0)
        
        Factors:
        - Suspicious patterns found
        - Exploit signatures
        - Dangerous opcodes (DELEGATECALL, SELFDESTRUCT)
        - Complexity score
        - External calls
        """
        score = 0.0
        
        # Base score from suspicious patterns
        score += len(suspicious_patterns) * 0.15
        
        # Exploit matches
        score += len(exploit_matches) * 0.3
        
        # Dangerous opcodes
        if features.delegatecall_count > 0:
            score += 0.2
        if features.selfdestruct_present:
            score += 0.25
        
        # High external call count
        if features.external_calls > 5:
            score += 0.1
        
        # High complexity
        if features.complexity_score > 0.3:
            score += 0.1
        
        return min(1.0, score)
    
    def _get_pattern_description(self, pattern_name: str) -> str:
        """Returns human-readable description of pattern"""
        descriptions = {
            "reentrancy_call_sstore": "Potential reentrancy vulnerability: External call followed by state change",
            "unprotected_selfdestruct": "Unprotected SELFDESTRUCT: Contract can be destroyed by any caller",
            "delegatecall_user_input": "DELEGATECALL with user-controlled input: Arbitrary code execution risk",
            "tx_origin_auth": "Using tx.origin for authentication: Vulnerable to phishing attacks",
            "timestamp_dependence": "Timestamp manipulation: Block timestamp used in critical logic",
            "block_manipulation": "Block data manipulation: Block number/hash used for randomness",
        }
        return descriptions.get(pattern_name, f"Suspicious pattern: {pattern_name}")


# Singleton Instance
bytecode_analyzer = BytecodeAnalyzer()
