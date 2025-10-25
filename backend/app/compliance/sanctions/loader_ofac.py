"""
OFAC Sanctions Loader
Downloads and parses OFAC SDN lists (SDN, ALT, ADD) and extracts crypto addresses.
"""
from typing import Dict, Any, List, Tuple, Optional
import httpx
import csv
from io import StringIO
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


def fetch_ofac() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Fetch OFAC SDN, ALT (aka), and ADD (addresses) lists.

    Returns: (entities, aliases, version)
    """
    entities: List[Dict[str, Any]] = []
    aliases: List[Dict[str, Any]] = []

    try:
        ent = _fetch_sdn_entities()
        als1 = _fetch_alt_names()
        als2 = _fetch_addresses_aliases()

        entities.extend(ent)
        aliases.extend(als1)
        aliases.extend(als2)

        version = f"ofac_{datetime.utcnow().strftime('%Y%m%d')}"
        logger.info(f"Fetched OFAC: entities={len(ent)}, aliases={len(als1)+len(als2)}")
        return entities, aliases, version
    except Exception as e:
        logger.error(f"OFAC fetch failed: {e}")
        return [], [], "ofac_v0"


def _http_get_text(url: str, timeout: float = 90.0) -> Optional[str]:
    async def _async_fetch() -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_async_fetch())


def _fetch_sdn_entities() -> List[Dict[str, Any]]:
    """Parse SDN entities from sdn.csv"""
    url = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    text = _http_get_text(url, timeout=120.0)
    if not text:
        return []
    reader = csv.DictReader(StringIO(text))
    entities: List[Dict[str, Any]] = []
    for row in reader:
        try:
            name = (row.get("SDN_Name") or "").strip()
            if not name:
                continue
            ent_num = (row.get("ent_num") or "").strip()
            entity_id = f"ofac_{ent_num or abs(hash(name)) % 1000000}"
            entity = {
                "id": entity_id,
                "canonical_name": name,
                "type": (row.get("SDN_Type") or "Unknown").strip(),
                "risk_level": "CRITICAL",
            }
            entities.append(entity)
        except Exception:
            continue
    return entities


def _fetch_alt_names() -> List[Dict[str, Any]]:
    """Parse alternate names from alt.csv to name/aka aliases"""
    url = "https://www.treasury.gov/ofac/downloads/alt.csv"
    text = _http_get_text(url, timeout=90.0)
    if not text:
        return []
    reader = csv.DictReader(StringIO(text))
    aliases: List[Dict[str, Any]] = []
    for row in reader:
        try:
            ent_num = (row.get("ent_num") or "").strip()
            alt_name = (row.get("alt_name") or "").strip()
            if not alt_name:
                continue
            entity_id = f"ofac_{ent_num or abs(hash(alt_name)) % 1000000}"
            aliases.append({
                "id": f"{entity_id}_aka_{abs(hash(alt_name)) % 100000}",
                "entity_id": entity_id,
                "value": alt_name,
                "kind": "aka",
                "source_code": "ofac",
                "confidence": 0.9,
            })
        except Exception:
            continue
    return aliases


def _fetch_addresses_aliases() -> List[Dict[str, Any]]:
    """Parse addresses from add.csv and extract crypto addresses as aliases"""
    url = "https://www.treasury.gov/ofac/downloads/add.csv"
    text = _http_get_text(url, timeout=90.0)
    if not text:
        return []
    reader = csv.DictReader(StringIO(text))
    aliases: List[Dict[str, Any]] = []

    # Simple regexes
    eth_re = re.compile(r"0x[a-fA-F0-9]{40}")
    btc_b58 = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
    btc_bech32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b")

    for row in reader:
        try:
            ent_num = (row.get("ent_num") or "").strip()
            entity_id = f"ofac_{ent_num or 'unknown'}"
            address_text = (row.get("address") or "").strip()
            city_state = (row.get("city_state_province_postalcode") or "").strip()
            add_remarks = (row.get("add_remarks") or "").strip()
            blob = " ".join([address_text, city_state, add_remarks])

            # Ethereum
            for m in eth_re.findall(blob):
                aliases.append({
                    "id": f"{entity_id}_eth_{m[-8:]}",
                    "entity_id": entity_id,
                    "value": m.lower(),
                    "kind": "address",
                    "source_code": "ofac",
                    "confidence": 0.9,
                })
            # Bitcoin base58
            for m in btc_b58.findall(blob):
                aliases.append({
                    "id": f"{entity_id}_btc_{m[-8:]}",
                    "entity_id": entity_id,
                    "value": m,
                    "kind": "address",
                    "source_code": "ofac",
                    "confidence": 0.85,
                })
            # Bitcoin bech32
            for m in btc_bech32.findall(blob):
                aliases.append({
                    "id": f"{entity_id}_btc_{m[-8:]}",
                    "entity_id": entity_id,
                    "value": m,
                    "kind": "address",
                    "source_code": "ofac",
                    "confidence": 0.85,
                })
        except Exception:
            continue

    return aliases
