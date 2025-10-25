"""
UK Sanctions Loader
Downloads and parses UK HM Treasury (OFSI) sanctions lists
"""
from typing import Dict, Any, List, Tuple
import httpx
import csv
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_uk() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Fetch UK sanctions list from HM Treasury OFSI
    
    Returns: (entities, aliases, version)
    """
    
    # UK Office of Financial Sanctions Implementation (OFSI)
    UK_URLS = [
        # Primary API endpoint
        "https://sanctionslistservice.ofsi.hmtreasury.gov.uk/api/search/download?format=csv",
        # Alternative static file locations
        "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1151318/ConList.csv",
        "https://www.gov.uk/government/publications/financial-sanctions-consolidated-list-of-targets/consolidated-list-of-targets.csv",
    ]
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    try:
        # Try multiple URLs
        for url in UK_URLS:
            try:
                entities_batch, aliases_batch = _fetch_from_url(url)
                if entities_batch:
                    entities.extend(entities_batch)
                    aliases.extend(aliases_batch)
                    break
            except Exception as e:
                logger.warning(f"UK source {url} failed: {e}")
                continue
        
        version = f"uk_{datetime.utcnow().strftime('%Y%m%d')}"
        logger.info(f"Fetched {len(entities)} UK sanctioned entities")
        
        return entities, aliases, version
        
    except Exception as e:
        logger.error(f"UK sanctions fetch failed: {e}")
        return [], [], "uk_v0"


def _fetch_from_url(url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch and parse CSV from a single URL"""
    
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []
    
    # Regex patterns for crypto addresses
    eth_re = re.compile(r'0x[a-fA-F0-9]{40}')
    btc_b58 = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
    btc_bech32 = re.compile(r'\bbc1[ac-hj-np-z02-9]{11,71}\b')
    
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
        # UK uses various column formats
        name = (
            row.get('Name') or
            row.get('Name 1') or
            row.get('Full Name') or
            row.get('LastName', '') + ' ' + row.get('FirstName', '')
        ).strip()
        
        if not name:
            continue
        
        entity_id = f"uk_{abs(hash(name)) % 1000000}"
        
        entity = {
            "id": entity_id,
            "canonical_name": name,
            "type": row.get('Group Type', 'Unknown'),
            "risk_level": "HIGH",
        }
        entities.append(entity)
        
        # Add name alias
        aliases.append({
            "id": f"{entity_id}_name",
            "entity_id": entity_id,
            "value": name,
            "kind": "name",
            "source_code": "uk",
            "confidence": 0.95
        })
        
        # Extract aliases
        for aka_col in ['Alias', 'Name 2', 'Name 3', 'Name 4', 'Name 5', 'Name 6', 'Also Known As']:
            aka_val = row.get(aka_col, '')
            if aka_val and aka_val.strip() and aka_val != name:
                aliases.append({
                    "id": f"{entity_id}_aka_{abs(hash(aka_val)) % 100000}",
                    "entity_id": entity_id,
                    "value": aka_val.strip(),
                    "kind": "aka",
                    "source_code": "uk",
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
                "source_code": "uk",
                "confidence": 0.85
            })
        
        # Bitcoin
        for match in btc_b58.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "uk",
                "confidence": 0.8
            })
        
        for match in btc_bech32.findall(all_text):
            aliases.append({
                "id": f"{entity_id}_addr_{match[-8:]}",
                "entity_id": entity_id,
                "value": match,
                "kind": "address",
                "source_code": "uk",
                "confidence": 0.8
            })
    
    return entities, aliases
