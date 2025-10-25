"""
UN Sanctions Loader
Downloads and parses United Nations Security Council sanctions lists
"""
from typing import Dict, Any, List, Tuple
import httpx
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_un() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Fetch UN Security Council sanctions lists (1267, 1988, etc.)
    
    Returns: (entities, aliases, version)
    """
    
    # UN Security Council Consolidated List (XML format)
    UN_URLS = [
        # ISIL (Da'esh) & Al-Qaida Sanctions List
        "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
        # Alternative JSON endpoint
        "https://scsanctions.un.org/resources/json/en/consolidated.json",
    ]
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    try:
        # Try XML first (more complete data)
        entities, aliases = _fetch_xml()
        
        if not entities:
            # Fallback to JSON
            entities, aliases = _fetch_json()
        
        version = f"un_{datetime.utcnow().strftime('%Y%m%d')}"
        logger.info(f"Fetched {len(entities)} UN sanctioned entities")
        
        return entities, aliases, version
        
    except Exception as e:
        logger.error(f"UN sanctions fetch failed: {e}")
        return [], [], "un_v0"


def _fetch_xml() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch and parse UN sanctions XML"""
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    
    # Regex patterns for crypto addresses
    eth_re = re.compile(r'0x[a-fA-F0-9]{40}')
    btc_b58 = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
    btc_bech32 = re.compile(r'\bbc1[ac-hj-np-z02-9]{11,71}\b')
    
    async def _async_fetch():
        async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        content = loop.run_until_complete(_async_fetch())
    except Exception as e:
        logger.warning(f"UN XML fetch failed: {e}")
        return entities, aliases
    
    try:
        root = ET.fromstring(content)
    except Exception as e:
        logger.error(f"UN XML parse failed: {e}")
        return entities, aliases
    
    # Parse individuals and entities
    for item in root.findall(".//INDIVIDUAL") + root.findall(".//ENTITY"):
        try:
            # Get name fields
            first_name = item.findtext(".//FIRST_NAME", "").strip()
            second_name = item.findtext(".//SECOND_NAME", "").strip()
            third_name = item.findtext(".//THIRD_NAME", "").strip()
            fourth_name = item.findtext(".//FOURTH_NAME", "").strip()
            
            name_parts = [first_name, second_name, third_name, fourth_name]
            name = " ".join(p for p in name_parts if p).strip()
            
            # For entities, use FIRST_NAME as main name
            if not name:
                name = item.findtext(".//NAME_ORIGINAL_SCRIPT", "").strip()
            
            if not name:
                continue
            
            dataid = item.get("DATAID", "")
            entity_id = f"un_{dataid}" if dataid else f"un_{abs(hash(name)) % 1000000}"
            
            entity_type = "Individual" if item.tag == "INDIVIDUAL" else "Entity"
            
            entity = {
                "id": entity_id,
                "canonical_name": name,
                "type": entity_type,
                "risk_level": "CRITICAL",  # UN sanctions are highest level
            }
            entities.append(entity)
            
            # Add primary name alias
            aliases.append({
                "id": f"{entity_id}_name",
                "entity_id": entity_id,
                "value": name,
                "kind": "name",
                "source_code": "un",
                "confidence": 0.98
            })
            
            # Extract all aliases
            for idx, alias_elem in enumerate(item.findall(".//INDIVIDUAL_ALIAS") + item.findall(".//ENTITY_ALIAS")):
                alias_name_parts = [
                    alias_elem.findtext(".//ALIAS_NAME", "").strip(),
                    alias_elem.findtext(".//QUALITY", "").strip()
                ]
                alias_name = " ".join(p for p in alias_name_parts if p).strip()
                
                if alias_name and alias_name != name:
                    aliases.append({
                        "id": f"{entity_id}_aka_{idx}",
                        "entity_id": entity_id,
                        "value": alias_name,
                        "kind": "aka",
                        "source_code": "un",
                        "confidence": 0.95
                    })
            
            # Scan all text fields for crypto addresses
            all_text_fields = [
                item.findtext(".//COMMENTS1", ""),
                item.findtext(".//LISTING_REASON", ""),
                item.findtext(".//NARRATIVE_SUMMARY", ""),
            ]
            all_text = " ".join(all_text_fields)
            
            # Extract Ethereum addresses
            for match in eth_re.findall(all_text):
                aliases.append({
                    "id": f"{entity_id}_addr_{match[-8:]}",
                    "entity_id": entity_id,
                    "value": match.lower(),
                    "kind": "address",
                    "source_code": "un",
                    "confidence": 0.9
                })
            
            # Extract Bitcoin addresses
            for match in btc_b58.findall(all_text):
                aliases.append({
                    "id": f"{entity_id}_btc_{match[-8:]}",
                    "entity_id": entity_id,
                    "value": match,
                    "kind": "address",
                    "source_code": "un",
                    "confidence": 0.85
                })
            
            for match in btc_bech32.findall(all_text):
                aliases.append({
                    "id": f"{entity_id}_btc_{match[-8:]}",
                    "entity_id": entity_id,
                    "value": match,
                    "kind": "address",
                    "source_code": "un",
                    "confidence": 0.85
                })
        
        except Exception as e:
            logger.warning(f"Failed to parse UN entry: {e}")
            continue
    
    return entities, aliases


def _fetch_json() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch and parse UN sanctions JSON (fallback)"""
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    url = "https://scsanctions.un.org/resources/json/en/consolidated.json"
    
    async def _async_fetch():
        async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        data = loop.run_until_complete(_async_fetch())
    except Exception as e:
        logger.warning(f"UN JSON fetch failed: {e}")
        return entities, aliases
    
    # Parse JSON structure (varies by endpoint)
    items = []
    if isinstance(data, dict):
        items = data.get("individuals", []) + data.get("entities", [])
    elif isinstance(data, list):
        items = data
    
    for item in items:
        name = item.get("name", "").strip()
        if not name:
            continue
        
        entity_id = f"un_{item.get('id', abs(hash(name)) % 1000000)}"
        
        entity = {
            "id": entity_id,
            "canonical_name": name,
            "type": item.get("type", "Unknown"),
            "risk_level": "CRITICAL",
        }
        entities.append(entity)
        
        aliases.append({
            "id": f"{entity_id}_name",
            "entity_id": entity_id,
            "value": name,
            "kind": "name",
            "source_code": "un",
            "confidence": 0.98
        })
    
    return entities, aliases
