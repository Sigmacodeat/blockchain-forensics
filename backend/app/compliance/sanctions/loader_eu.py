""" 
EU Sanctions Loader
Downloads and parses EU sanctions lists
"""
from typing import Dict, Any, List, Tuple
import httpx
import csv
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_eu() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Fetch EU sanctions list from European Union external action service
    
    Returns: (entities, aliases, version)
    """
    
    # EU Sanctions list (CSV format from data.europa.eu)
    EU_URLS = [
        # Consolidated financial sanctions list
        "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=",
        # Alternative: EEAS sanctions map data export
        "https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions/distributions",
    ]
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    try:
        # Try fetching from primary source
        entities, aliases = _fetch_from_web()
        
        version = f"eu_{datetime.utcnow().strftime('%Y%m%d')}"
        logger.info(f"Fetched {len(entities)} EU sanctioned entities")
        
        return entities, aliases, version
        
    except Exception as e:
        logger.error(f"EU sanctions fetch failed: {e}")
        return [], [], "eu_v0"


def _fetch_from_web() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch and parse EU sanctions from web source"""
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    # Regex patterns for crypto addresses
    eth_re = re.compile(r'0x[a-fA-F0-9]{40}')
    btc_b58 = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
    btc_bech32 = re.compile(r'\bbc1[ac-hj-np-z02-9]{11,71}\b')
    
    # EU publishes CSV with ; delimiter
    url = "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content"
    
    async def _async_fetch():
        async with httpx.AsyncClient(follow_redirects=True, timeout=90.0) as client:
            # EU requires User-Agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Blockchain-Forensics Sanctions Indexer)"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        content = loop.run_until_complete(_async_fetch())
    except Exception as e:
        logger.warning(f"EU primary source failed: {e}")
        return entities, aliases
    
    # Parse CSV (EU uses semicolon delimiter)
    lines = content.splitlines()
    if not lines:
        return entities, aliases
    
    # Try both comma and semicolon delimiters
    for delimiter in [';', ',']:
        try:
            reader = csv.DictReader(lines, delimiter=delimiter)
            rows = list(reader)
            if len(rows) > 0:
                break
        except:
            continue
    else:
        return entities, aliases
    
    for row in rows:
        # Extract name from various possible column names
        name = (
            row.get('Name') or
            row.get('NameAlias_WholeName') or 
            row.get('FirstName', '') + ' ' + row.get('LastName', '')
        ).strip()
        
        if not name:
            continue
        
        entity_id = f"eu_{abs(hash(name)) % 1000000}"
        
        entity = {
            "id": entity_id,
            "canonical_name": name,
            "type": row.get('SubjectType', 'Unknown'),
            "risk_level": "HIGH",
        }
        entities.append(entity)
        
        # Add name alias
        aliases.append({
            "id": f"{entity_id}_name",
            "entity_id": entity_id,
            "value": name,
            "kind": "name",
            "source_code": "eu",
            "confidence": 0.95
        })
        
        # Extract aliases from various columns
        for aka_col in ['NameAlias_WholeName', 'Alias', 'Aliases']:
            aka_val = row.get(aka_col, '')
            if aka_val and aka_val != name:
                aliases.append({
                    "id": f"{entity_id}_aka_{abs(hash(aka_val)) % 100000}",
                    "entity_id": entity_id,
                    "value": aka_val.strip(),
                    "kind": "aka",
                    "source_code": "eu",
                    "confidence": 0.9
                })
        
        # Scan all fields for crypto addresses
        all_text = ' '.join(str(v) for v in row.values() if v)
        
        # Ethereum
        for match in eth_re.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match.lower(),
                "kind": "address",
                "source_code": "eu",
                "confidence": 0.85
            })
        
        # Bitcoin
        for match in btc_b58.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "eu",
                "confidence": 0.8
            })
        
        for match in btc_bech32.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "eu",
                "confidence": 0.8
            })
    
    return entities, aliases
