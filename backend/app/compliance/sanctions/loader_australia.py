"""
Australia Sanctions Loader
Downloads and parses Australian sanctions lists from DFAT
"""
from typing import Dict, Any, List, Tuple
import httpx
import csv
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_australia() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Fetch Australia sanctions list from Department of Foreign Affairs and Trade (DFAT)
    
    Returns: (entities, aliases, version)
    """
    
    # Australia's Consolidated List
    AUSTRALIA_URLS = [
        # Main consolidated sanctions list
        "https://www.dfat.gov.au/sites/default/files/regulation8_consolidated.csv",
        # Alternative URLs if primary fails
        "https://www.dfat.gov.au/international-relations/security/sanctions/sanctions-regimes/Documents/regulation8_consolidated.csv",
    ]
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    try:
        for url in AUSTRALIA_URLS:
            try:
                entities_batch, aliases_batch = _fetch_from_url(url)
                entities.extend(entities_batch)
                aliases.extend(aliases_batch)
                break  # Success, no need to try alternatives
            except Exception as e:
                logger.warning(f"Failed to fetch Australia sanctions from {url}: {e}")
                continue
        
        version = f"australia_{datetime.utcnow().strftime('%Y%m%d')}"
        logger.info(f"Fetched {len(entities)} Australia sanctioned entities")
        
        return entities, aliases, version
        
    except Exception as e:
        logger.error(f"Australia sanctions fetch failed: {e}")
        return [], [], "australia_v0"


def _fetch_from_url(url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch and parse CSV from a single URL"""
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    # Regex patterns for crypto addresses
    eth_re = re.compile(r'0x[a-fA-F0-9]{40}')
    btc_b58 = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
    btc_bech32 = re.compile(r'\bbc1[ac-hj-np-z02-9]{11,71}\b')
    trx_b58 = re.compile(r'\bT[a-km-zA-HJ-NP-Z1-9]{25,34}\b')
    
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
        # Extract name - Australia uses different column names
        name = (
            row.get('Name') or 
            row.get('name_of_individual') or
            row.get('name_of_entity') or
            row.get('LastName', '') + ' ' + row.get('FirstName', '')
        ).strip()
        
        if not name:
            continue
        
        entity_id = f"australia_{abs(hash(name)) % 1000000}"
        
        # Determine entity type
        entity_type = row.get('Type') or row.get('type') or 'Unknown'
        
        entity = {
            "id": entity_id,
            "canonical_name": name,
            "type": entity_type,
            "risk_level": "HIGH",
        }
        entities.append(entity)
        
        # Add name alias
        aliases.append({
            "id": f"{entity_id}_name",
            "entity_id": entity_id,
            "value": name,
            "kind": "name",
            "source_code": "australia",
            "confidence": 0.95
        })
        
        # Extract aliases/AKAs
        aka_fields = (
            row.get('Aliases') or 
            row.get('alias') or 
            row.get('other_names') or 
            row.get('Also Known As', '')
        )
        if aka_fields:
            for aka in aka_fields.split(';'):
                aka = aka.strip()
                if aka and aka != name:
                    aliases.append({
                        "id": f"{entity_id}_aka_{abs(hash(aka)) % 100000}",
                        "entity_id": entity_id,
                        "value": aka,
                        "kind": "aka",
                        "source_code": "australia",
                        "confidence": 0.9
                    })
        
        # Scan all fields for crypto addresses
        all_text = ' '.join(str(v) for v in row.values() if v)
        
        # Ethereum addresses
        for match in eth_re.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_eth_{match[-8:]}",
                "entity_id": entity_id,
                "value": match.lower(),
                "kind": "address",
                "source_code": "australia",
                "confidence": 0.9
            })
        
        # Bitcoin addresses
        for match in btc_b58.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_btc_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "australia",
                "confidence": 0.85
            })
        
        for match in btc_bech32.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_btc_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "australia",
                "confidence": 0.85
            })
        
        # Tron addresses
        for match in trx_b58.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_trx_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "australia",
                "confidence": 0.8
            })
    
    return entities, aliases
