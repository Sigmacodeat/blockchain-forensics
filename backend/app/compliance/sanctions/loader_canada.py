"""
Canada Sanctions Loader
Downloads and parses Canadian sanctions lists from Global Affairs Canada
"""
from typing import Dict, Any, List, Tuple
import httpx
import csv
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_canada() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Fetch Canada sanctions list from Global Affairs Canada
    
    Returns: (entities, aliases, version)
    """
    
    # Canada's Special Economic Measures Act (SEMA) and other sanctions
    CANADA_URLS = [
        # Main consolidated list
        "https://www.international.gc.ca/world-monde/assets/office_docs/international_relations-relations_internationales/sanctions/sema-lmes.csv",
        # Alternative: freezing assets list
        "https://www.international.gc.ca/world-monde/assets/office_docs/international_relations-relations_internationales/sanctions/freezing-gel.csv",
    ]
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    try:
        for url in CANADA_URLS:
            try:
                entities_batch, aliases_batch = _fetch_from_url(url)
                entities.extend(entities_batch)
                aliases.extend(aliases_batch)
            except Exception as e:
                logger.warning(f"Failed to fetch Canada sanctions from {url}: {e}")
                continue
        
        version = f"canada_{datetime.utcnow().strftime('%Y%m%d')}"
        logger.info(f"Fetched {len(entities)} Canada sanctioned entities")
        
        return entities, aliases, version
        
    except Exception as e:
        logger.error(f"Canada sanctions fetch failed: {e}")
        return [], [], "canada_v0"


def _fetch_from_url(url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch and parse CSV from a single URL"""
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    # Regex patterns for crypto addresses
    eth_re = re.compile(r'0x[a-fA-F0-9]{40}')
    btc_b58 = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
    btc_bech32 = re.compile(r'\bbc1[ac-hj-np-z02-9]{11,71}\b')
    ltc_b58 = re.compile(r'\b[L3][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
    
    async def _async_fetch():
        async with httpx.AsyncClient(follow_redirects=True, timeout=90.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    content = loop.run_until_complete(_async_fetch())
    
    # Parse CSV
    lines = content.splitlines()
    if not lines:
        return entities, aliases
    
    reader = csv.DictReader(lines)
    
    for row in reader:
        # Extract name (varies by CSV format)
        name = (
            row.get('Name') or 
            row.get('LastName') or 
            row.get('Entity') or 
            row.get('Given Name', '') + ' ' + row.get('Last Name', '')
        ).strip()
        
        if not name:
            continue
        
        entity_id = f"canada_{abs(hash(name)) % 1000000}"
        
        entity = {
            "id": entity_id,
            "canonical_name": name,
            "type": row.get('Type', 'Unknown'),
            "risk_level": "HIGH",
        }
        entities.append(entity)
        
        # Add name alias
        aliases.append({
            "id": f"{entity_id}_name",
            "entity_id": entity_id,
            "value": name,
            "kind": "name",
            "source_code": "canada",
            "confidence": 0.95
        })
        
        # Extract aliases/AKAs
        aka_fields = row.get('Aliases') or row.get('AKA') or row.get('Also Known As', '')
        if aka_fields:
            for aka in aka_fields.split(';'):
                aka = aka.strip()
                if aka:
                    aliases.append({
                        "id": f"{entity_id}_aka_{abs(hash(aka)) % 100000}",
                        "entity_id": entity_id,
                        "value": aka,
                        "kind": "aka",
                        "source_code": "canada",
                        "confidence": 0.9
                    })
        
        # Scan all fields for crypto addresses
        all_text = ' '.join(str(v) for v in row.values() if v)
        
        # Ethereum addresses
        for match in eth_re.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match.lower(),
                "kind": "address",
                "source_code": "canada",
                "confidence": 0.9
            })
        
        # Bitcoin addresses
        for match in btc_b58.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "canada",
                "confidence": 0.85
            })
        
        for match in btc_bech32.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "canada",
                "confidence": 0.85
            })
    
    return entities, aliases
