"""
Event Signature Matching & Resolution
======================================
Identifiziert Contract Events via:
- 4byte.directory Events API
- Local event database
- Common ERC standard events
"""

import hashlib
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class EventSignature:
    """Repräsentiert eine Event Signature"""
    topic0: str  # 32-byte event signature hash (0x123...)
    signature: str  # Full signature (Transfer(address,address,uint256))
    name: str  # Event name (Transfer)
    params: List[str]  # Parameter types
    source: str  # Where signature was found (4byte, local, erc20, etc.)
    confidence: float  # 0.0 - 1.0


# Bekannte ERC Standard Events
ERC_EVENT_SIGNATURES = {
    "ERC20": {
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer(address,address,uint256)",
        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval(address,address,uint256)",
    },
    "ERC721": {
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer(address,address,uint256)",
        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval(address,address,uint256)",
        "0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31": "ApprovalForAll(address,address,bool)",
    },
    "ERC1155": {
        "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62": "TransferSingle(address,address,address,uint256,uint256)",
        "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb": "TransferBatch(address,address,address,uint256[],uint256[])",
        "0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31": "ApprovalForAll(address,address,bool)",
        "0x6bb7ff708619ba0610cba295a58592e0451dee2622938c8755667688daf3529b": "URI(string,uint256)",
    },
    "Ownable": {
        "0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0": "OwnershipTransferred(address,address)",
    },
    "Pausable": {
        "0x62e78cea01bee320cd4e420270b5ea74000d11b0c9f74754ebdbfc544b05a258": "Paused(address)",
        "0x5db9ee0a495bf2e6ff9c91a7834c1ba4fdd244a5e8aa4e537bd38aeae4b073aa": "Unpaused(address)",
    },
}


class EventSignatureMatcher:
    """
    Event Signature Resolution Engine
    Nutzt 4byte.directory + lokale DB
    """
    
    def __init__(self):
        self.local_db: Dict[str, List[str]] = self._load_local_db()
        self.cache: Dict[str, EventSignature] = {}
        self.fourbyte_events_api_url = "https://www.4byte.directory/api/v1/event-signatures/"
    
    def _load_local_db(self) -> Dict[str, List[str]]:
        """Lädt lokale Event-Signature-Datenbank"""
        db = {}
        
        # Merge all ERC standards
        for standard, sigs in ERC_EVENT_SIGNATURES.items():
            for topic0, signature in sigs.items():
                if topic0 not in db:
                    db[topic0] = []
                db[topic0].append(signature)
        
        return db
    
    @lru_cache(maxsize=1000)
    def resolve_event(self, topic0: str) -> Optional[EventSignature]:
        """
        Löst einen topic0 hash zu seiner Event-Signature auf
        
        Args:
            topic0: 32-byte event signature hash (0x123...)
        
        Returns:
            EventSignature oder None
        """
        topic0 = topic0.lower()
        if not topic0.startswith('0x'):
            topic0 = '0x' + topic0
        
        # 1. Cache check
        if topic0 in self.cache:
            return self.cache[topic0]
        
        # 2. Local DB check
        if topic0 in self.local_db:
            signatures = self.local_db[topic0]
            result = self._parse_signature(signatures[0], topic0, "local")
            self.cache[topic0] = result
            return result
        
        # 3. Try 4byte.directory events (synchronous for simplicity)
        try:
            result = self._query_fourbyte_events_sync(topic0)
            if result:
                self.cache[topic0] = result
                return result
        except Exception:
            pass
        
        return None
    
    async def resolve_event_async(self, topic0: str) -> Optional[EventSignature]:
        """Async version für batch processing"""
        topic0 = topic0.lower()
        if not topic0.startswith('0x'):
            topic0 = '0x' + topic0
        
        # Cache & local check
        if topic0 in self.cache:
            return self.cache[topic0]
        
        if topic0 in self.local_db:
            signatures = self.local_db[topic0]
            result = self._parse_signature(signatures[0], topic0, "local")
            self.cache[topic0] = result
            return result
        
        # API query
        try:
            result = await self._query_fourbyte_events_async(topic0)
            if result:
                self.cache[topic0] = result
                return result
        except Exception:
            pass
        
        return None
    
    def _query_fourbyte_events_sync(self, topic0: str) -> Optional[EventSignature]:
        """Synchronous 4byte.directory events query"""
        try:
            # Remove 0x prefix for API
            hex_sig = topic0.replace('0x', '')
            url = f"{self.fourbyte_events_api_url}?hex_signature={hex_sig}"
            
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    # Take first result
                    sig_text = data['results'][0]['text_signature']
                    return self._parse_signature(sig_text, topic0, "4byte")
        except Exception:
            pass
        
        return None
    
    async def _query_fourbyte_events_async(self, topic0: str) -> Optional[EventSignature]:
        """Async 4byte.directory events query"""
        try:
            hex_sig = topic0.replace('0x', '')
            url = f"{self.fourbyte_events_api_url}?hex_signature={hex_sig}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        sig_text = data['results'][0]['text_signature']
                        return self._parse_signature(sig_text, topic0, "4byte")
        except Exception:
            pass
        
        return None
    
    def _parse_signature(
        self, 
        signature: str, 
        topic0: str, 
        source: str
    ) -> EventSignature:
        """Parst event signature string zu strukturiertem Format"""
        # Beispiel: "Transfer(address,address,uint256)"
        
        if '(' not in signature:
            # Invalid format
            return EventSignature(
                topic0=topic0,
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
        
        return EventSignature(
            topic0=topic0,
            signature=signature,
            name=name,
            params=params,
            source=source,
            confidence=confidence,
        )
    
    def extract_events_from_logs(self, logs: List[Dict]) -> List[str]:
        """
        Extrahiert unique Event-Topics aus Transaction Logs
        
        Args:
            logs: Liste von Log-Objekten mit 'topics' field
        
        Returns:
            Liste von topic0 hashes
        """
        topics = set()
        for log in logs:
            if log.get('topics') and len(log['topics']) > 0:
                topic0 = log['topics'][0]
                if topic0:
                    topics.add(topic0.lower())
        
        return list(topics)


# Singleton
event_signature_matcher = EventSignatureMatcher()
