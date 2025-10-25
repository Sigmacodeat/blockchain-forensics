"""
Function Signature Matching & Resolution
=========================================
Identifiziert Contract Functions via:
- 4byte.directory API
- Local signature database
- Common ERC standard functions
- Heuristic matching

Erweitert die Basic ABI-Decoding aus evm_log_decoder.py
"""

import hashlib
import httpx
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
from functools import lru_cache
import json


@dataclass
class FunctionSignature:
    """Repräsentiert eine Function Signature"""
    selector: str  # 4-byte function selector (0x12345678)
    signature: str  # Full signature (transfer(address,uint256))
    name: str  # Function name (transfer)
    params: List[str]  # Parameter types
    source: str  # Where signature was found (4byte, local, erc20, etc.)
    confidence: float  # 0.0 - 1.0


@dataclass
class ContractInterface:
    """Erkannte Contract Interface"""
    standards: List[str]  # ERC20, ERC721, etc.
    functions: List[FunctionSignature]
    events: List[str]
    is_proxy: bool
    implementation_hint: Optional[str]


# Bekannte ERC Standard Signatures
ERC_STANDARDS = {
    "ERC20": {
        "0x70a08231": "balanceOf(address)",
        "0xa9059cbb": "transfer(address,uint256)",
        "0x23b872dd": "transferFrom(address,address,uint256)",
        "0x095ea7b3": "approve(address,uint256)",
        "0xdd62ed3e": "allowance(address,address)",
        "0x18160ddd": "totalSupply()",
    },
    "ERC721": {
        "0x70a08231": "balanceOf(address)",
        "0x6352211e": "ownerOf(uint256)",
        "0x42842e0e": "safeTransferFrom(address,address,uint256)",
        "0xb88d4fde": "safeTransferFrom(address,address,uint256,bytes)",
        "0x23b872dd": "transferFrom(address,address,uint256)",
        "0x081812fc": "approve(address,uint256)",
        "0xa22cb465": "setApprovalForAll(address,bool)",
        "0xe985e9c5": "isApprovedForAll(address,address)",
    },
    "ERC1155": {
        "0x00fdd58e": "balanceOf(address,uint256)",
        "0x4e1273f4": "balanceOfBatch(address[],uint256[])",
        "0xf242432a": "safeTransferFrom(address,address,uint256,uint256,bytes)",
        "0x2eb2c2d6": "safeBatchTransferFrom(address,address,uint256[],uint256[],bytes)",
        "0xa22cb465": "setApprovalForAll(address,bool)",
        "0xe985e9c5": "isApprovedForAll(address,address)",
    },
    "Ownable": {
        "0x8da5cb5b": "owner()",
        "0xf2fde38b": "transferOwnership(address)",
        "0x715018a6": "renounceOwnership()",
    },
    "Pausable": {
        "0x5c975abb": "paused()",
        "0x8456cb59": "pause()",
        "0x3f4ba83a": "unpause()",
    },
    "Proxy": {
        "0x5c60da1b": "implementation()",
        "0x3659cfe6": "upgradeTo(address)",
        "0x4f1ef286": "upgradeToAndCall(address,bytes)",
    },
}


# Dangerous/Suspicious Function Signatures
DANGEROUS_FUNCTIONS = {
    "0x9f678cca": "burn(uint256)",  # Can destroy tokens
    "0x42966c68": "mint(uint256)",  # Can create new tokens
    "0x40c10f19": "mint(address,uint256)",
    "0xa9059cbb": "transfer(address,uint256)",  # Owner unrestricted transfer
    "0x3ccfd60b": "withdraw()",  # Can drain funds
    "0x51cff8d9": "withdrawAll()",
}


class FunctionSignatureMatcher:
    """
    Function Signature Resolution Engine
    Nutzt 4byte.directory + lokale DB
    """
    
    def __init__(self):
        self.local_db: Dict[str, List[str]] = self._load_local_db()
        self.cache: Dict[str, FunctionSignature] = {}
        self.fourbyte_api_url = "https://www.4byte.directory/api/v1/signatures/"
    
    def _load_local_db(self) -> Dict[str, List[str]]:
        """Lädt lokale Signature-Datenbank"""
        db = {}
        
        # Merge all ERC standards
        for standard, sigs in ERC_STANDARDS.items():
            for selector, signature in sigs.items():
                if selector not in db:
                    db[selector] = []
                db[selector].append(signature)
        
        return db
    
    @lru_cache(maxsize=1000)
    def resolve_selector(self, selector: str) -> Optional[FunctionSignature]:
        """
        Löst einen 4-byte selector zu seiner Signature auf
        
        Args:
            selector: 0x12345678 format
        
        Returns:
            FunctionSignature oder None
        """
        selector = selector.lower()
        if not selector.startswith('0x'):
            selector = '0x' + selector
        
        # 1. Cache check
        if selector in self.cache:
            return self.cache[selector]
        
        # 2. Local DB check
        if selector in self.local_db:
            signatures = self.local_db[selector]
            result = self._parse_signature(signatures[0], selector, "local")
            self.cache[selector] = result
            return result
        
        # 3. Try 4byte.directory (synchronous for simplicity)
        try:
            result = self._query_fourbyte_sync(selector)
            if result:
                self.cache[selector] = result
                return result
        except Exception:
            pass
        
        return None
    
    async def resolve_selector_async(self, selector: str) -> Optional[FunctionSignature]:
        """Async version für batch processing"""
        selector = selector.lower()
        if not selector.startswith('0x'):
            selector = '0x' + selector
        
        # Cache & local check
        if selector in self.cache:
            return self.cache[selector]
        
        if selector in self.local_db:
            signatures = self.local_db[selector]
            result = self._parse_signature(signatures[0], selector, "local")
            self.cache[selector] = result
            return result
        
        # API query
        try:
            result = await self._query_fourbyte_async(selector)
            if result:
                self.cache[selector] = result
                return result
        except Exception:
            pass
        
        return None
    
    def _query_fourbyte_sync(self, selector: str) -> Optional[FunctionSignature]:
        """Synchronous 4byte.directory query"""
        try:
            # Remove 0x prefix for API
            hex_sig = selector.replace('0x', '')
            url = f"{self.fourbyte_api_url}?hex_signature={hex_sig}"
            
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    # Take first result
                    sig_text = data['results'][0]['text_signature']
                    return self._parse_signature(sig_text, selector, "4byte")
        except Exception:
            pass
        
        return None
    
    async def _query_fourbyte_async(self, selector: str) -> Optional[FunctionSignature]:
        """Async 4byte.directory query"""
        try:
            hex_sig = selector.replace('0x', '')
            url = f"{self.fourbyte_api_url}?hex_signature={hex_sig}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        sig_text = data['results'][0]['text_signature']
                        return self._parse_signature(sig_text, selector, "4byte")
        except Exception:
            pass
        
        return None
    
    def _parse_signature(
        self, 
        signature: str, 
        selector: str, 
        source: str
    ) -> FunctionSignature:
        """Parst function signature string zu strukturiertem Format"""
        # Beispiel: "transfer(address,uint256)"
        
        if '(' not in signature:
            # Invalid format
            return FunctionSignature(
                selector=selector,
                signature=signature,
                name=signature,
                params=[],
                source=source,
                confidence=0.5,
            )
        
        name = signature.split('(')[0]
        params_str = signature.split('(')[1].rstrip(')')
        params = [p.strip() for p in params_str.split(',')] if params_str else []
        
        # Higher confidence for local/ERC standards
        confidence = 0.95 if source in ['local', 'erc20', 'erc721'] else 0.8
        
        return FunctionSignature(
            selector=selector,
            signature=signature,
            name=name,
            params=params,
            source=source,
            confidence=confidence,
        )
    
    def detect_interface(self, bytecode: str, selectors: List[str]) -> ContractInterface:
        """
        Erkennt Contract Standards basierend auf vorhandenen Function Selectors
        
        Args:
            bytecode: Contract bytecode
            selectors: Liste von gefundenen 4-byte selectors
        
        Returns:
            ContractInterface mit erkannten Standards
        """
        detected_standards = []
        functions = []
        is_proxy = False
        
        # Resolve all selectors
        for selector in selectors:
            func = self.resolve_selector(selector)
            if func:
                functions.append(func)
        
        # Check for ERC standards
        for standard, required_sigs in ERC_STANDARDS.items():
            matches = sum(1 for sel in selectors if sel in required_sigs)
            total = len(required_sigs)
            
            # If >50% of standard functions present, mark as detected
            if matches >= total * 0.5:
                detected_standards.append(standard)
                
                # Special handling
                if standard == "Proxy":
                    is_proxy = True
        
        # Detect events (simplified - would need log analysis)
        events = []
        if "ERC20" in detected_standards:
            events.extend(["Transfer", "Approval"])
        if "ERC721" in detected_standards:
            events.extend(["Transfer", "Approval", "ApprovalForAll"])
        
        return ContractInterface(
            standards=detected_standards,
            functions=functions,
            events=events,
            is_proxy=is_proxy,
            implementation_hint=None,
        )
    
    def extract_selectors_from_bytecode(self, bytecode: str) -> List[str]:
        """
        Extrahiert Function Selectors aus Bytecode
        
        Selectors sind die ersten 4 Bytes von keccak256(signature)
        Im Bytecode zu finden als PUSH4 instructions
        """
        selectors = set()
        bytecode = bytecode.lower().replace('0x', '')
        
        # Find PUSH4 (0x63) followed by 4 bytes
        i = 0
        while i < len(bytecode) - 8:
            opcode = bytecode[i:i+2]
            
            if opcode == '63':  # PUSH4
                # Next 4 bytes are potentially a function selector
                selector = '0x' + bytecode[i+2:i+10]
                selectors.add(selector)
                i += 10
            else:
                i += 2
        
        return list(selectors)
    
    def is_dangerous_function(self, selector: str) -> Tuple[bool, str]:
        """
        Prüft ob Function als gefährlich eingestuft ist
        
        Returns:
            (is_dangerous, reason)
        """
        selector = selector.lower()
        if selector in DANGEROUS_FUNCTIONS:
            sig = DANGEROUS_FUNCTIONS[selector]
            return True, f"Dangerous function: {sig}"
        
        # Resolve and check by name
        func = self.resolve_selector(selector)
        if func:
            dangerous_names = ['selfdestruct', 'suicide', 'kill', 'destroy']
            if any(name in func.name.lower() for name in dangerous_names):
                return True, f"Potentially dangerous function: {func.signature}"
        
        return False, ""


# Singleton
function_signature_matcher = FunctionSignatureMatcher()
