"""
Multi-Sanctions Sources
Downloads and parses sanctions lists from multiple jurisdictions
"""
import csv
import re
import json
import logging
from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path
import os
import httpx
from app.metrics import SANCTIONS_ENTRIES_TOTAL, SANCTIONS_ADDRESSES_TOTAL, SANCTIONS_UPDATE_TIMESTAMP

logger = logging.getLogger(__name__)


class SanctionsSource:
    """Base class for sanctions data sources"""

    def __init__(self, name: str, url: str, format_type: str = "csv", env_key: Optional[str] = None):
        self.name = name
        # Allow overriding URL via ENV, e.g., OFAC_URL, UN_URL, UK_URL, EU_URL
        if env_key:
            self.url = os.getenv(env_key, url)
        else:
            self.url = url
        self.format_type = format_type

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and parse data"""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.url, timeout=90)
                response.raise_for_status()

                if self.format_type == "csv":
                    return await self._parse_csv(response.text)
                elif self.format_type == "json":
                    return await self._parse_json(response.text)
                elif self.format_type == "xml":
                    return await self._parse_xml(response.text)
                else:
                    return []

        except Exception as e:
            logger.error(f"Failed to fetch {self.name}: {e}")
            return []

    async def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse CSV content"""
        # Base implementation - override in subclasses
        return []

    async def _parse_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON content"""
        return json.loads(content)

    async def _parse_xml(self, content: str) -> List[Dict[str, Any]]:
        """Parse XML content (base: no-op)"""
        return []


class OFACSource(SanctionsSource):
    """OFAC Specially Designated Nationals (SDN) List"""

    def __init__(self):
        # New OFAC publication service (redirect target)
        super().__init__("OFAC", "https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/sdn.csv", "csv", env_key="OFAC_URL")

    async def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse OFAC SDN CSV and extract crypto addresses from multiple fields."""
        lines = content.splitlines()
        reader = csv.DictReader(lines)

        # Regex patterns (simplified) for common chains
        eth_re = re.compile(r"0x[a-fA-F0-9]{40}")
        # Base58 for BTC/LTC/BCH (very rough; accept 26-42 length starting with 13Lbc or bc1 bech32 handled below)
        btc_b58 = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        ltc_b58 = re.compile(r"\b[L3][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        bch_b58 = re.compile(r"\b[qp][a-z0-9]{41}\b", re.IGNORECASE)  # cashaddr (no prefix)
        # Bech32 BTC: bc1...
        btc_bech32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b")
        # TRX base58check T...
        trx_b58 = re.compile(r"\bT[a-km-zA-HJ-NP-Z1-9]{25,34}\b")

        def detect(text: str) -> List[Dict[str, str]]:
            hits: List[Dict[str, str]] = []
            if not text:
                return hits
            # ETH
            for m in eth_re.findall(text):
                hits.append({"chain": "ethereum", "address": m.lower()})
            # BTC
            for m in btc_b58.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in btc_bech32.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            # LTC
            for m in ltc_b58.findall(text):
                hits.append({"chain": "litecoin", "address": m})
            # BCH (cashaddr without prefix)
            for m in bch_b58.findall(text):
                hits.append({"chain": "bitcoin-cash", "address": m})
            # TRX
            for m in trx_b58.findall(text):
                hits.append({"chain": "tron", "address": m})
            return hits

        out: List[Dict[str, Any]] = []
        for row in reader:
            name = row.get('Name', '')
            s_type = row.get('Type', '')
            fields_to_scan = []
            # Common OFAC CSV columns (varies over time); scan broadly
            for key in (
                'Digital Currency Address', 'Remarks', 'Remarks2', 'Program', 'aka', 'A.K.A.s',
                'Address', 'Additional Sanctions Information', 'Comments', 'ID #', 'Alt. Names', 'Call Sign'
            ):
                val = row.get(key)
                if isinstance(val, str) and val:
                    fields_to_scan.append(val)

            blob = " | ".join(fields_to_scan)
            for hit in detect(blob):
                out.append({
                    'chain': hit['chain'],
                    'address': hit['address'],
                    'label': 'sanctioned',
                    'category': 'sanctions',
                    'source': 'OFAC',
                    'confidence': 0.95,
                    'name': name,
                    'sanction_type': s_type
                })

            # Also check the dedicated column if present
            addr_col = (row.get('Digital Currency Address') or '').strip()
            if addr_col:
                for hit in detect(addr_col):
                    out.append({
                        'chain': hit['chain'],
                        'address': hit['address'],
                        'label': 'sanctioned',
                        'category': 'sanctions',
                        'source': 'OFAC',
                        'confidence': 0.98,
                        'name': name,
                        'sanction_type': s_type
                    })

        return out


class UNSource(SanctionsSource):
    """United Nations Sanctions List"""

    def __init__(self):
        # Legacy URL now redirects to Azure blob; using legacy endpoint is fine with follow_redirects
        super().__init__("UN", "https://scsanctions.un.org/resources/xml/en/consolidated.xml", "xml", env_key="UN_URL")

    async def _parse_xml(self, content: str) -> List[Dict[str, Any]]:
        """Parse UN XML (basic): scan text for crypto addresses using regex, similar to OFAC."""
        import xml.etree.ElementTree as ET
        # Reuse simplified regexes
        eth_re = re.compile(r"0x[a-fA-F0-9]{40}")
        btc_b58 = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        ltc_b58 = re.compile(r"\b[L3][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        bch_b58 = re.compile(r"\b[qp][a-z0-9]{41}\b", re.IGNORECASE)
        btc_bech32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b")
        trx_b58 = re.compile(r"\bT[a-km-zA-HJ-NP-Z1-9]{25,34}\b")

        def detect(text: str) -> List[Dict[str, str]]:
            hits: List[Dict[str, str]] = []
            if not text:
                return hits
            for m in eth_re.findall(text):
                hits.append({"chain": "ethereum", "address": m.lower()})
            for m in btc_b58.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in btc_bech32.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in ltc_b58.findall(text):
                hits.append({"chain": "litecoin", "address": m})
            for m in bch_b58.findall(text):
                hits.append({"chain": "bitcoin-cash", "address": m})
            for m in trx_b58.findall(text):
                hits.append({"chain": "tron", "address": m})
            return hits

        out: List[Dict[str, Any]] = []
        try:
            root = ET.fromstring(content)
        except Exception:
            return out
        # Collect all text nodes
        texts: List[str] = []
        for elem in root.iter():
            if elem.text and isinstance(elem.text, str):
                texts.append(elem.text)
            if elem.tail and isinstance(elem.tail, str):
                texts.append(elem.tail)
        blob = " | ".join(texts)
        for hit in detect(blob):
            out.append({
                'chain': hit['chain'],
                'address': hit['address'],
                'label': 'sanctioned',
                'category': 'sanctions',
                'source': 'UN',
                'confidence': 0.8,
            })
        return out


class EUSource(SanctionsSource):
    """European Union Sanctions List"""

    def __init__(self):
        super().__init__("EU", "https://data.europa.eu/data/datasets/sanctionsmap", "csv", env_key="EU_URL")

    async def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse EU sanctions CSV by scanning all text fields for crypto addresses (regex-based).
        The EU dataset format varies. We avoid strong schema assumptions and scan all string fields.
        """
        lines = content.splitlines()
        if not lines:
            return []
        reader = csv.DictReader(lines)

        # Reuse simplified regexes from OFAC/UK
        eth_re = re.compile(r"0x[a-fA-F0-9]{40}")
        btc_b58 = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        ltc_b58 = re.compile(r"\b[L3][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        bch_b58 = re.compile(r"\b[qp][a-z0-9]{41}\b", re.IGNORECASE)
        btc_bech32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b")
        trx_b58 = re.compile(r"\bT[a-km-zA-HJ-NP-Z1-9]{25,34}\b")

        def detect(text: str) -> List[Dict[str, str]]:
            hits: List[Dict[str, str]] = []
            if not text:
                return hits
            for m in eth_re.findall(text):
                hits.append({"chain": "ethereum", "address": m.lower()})
            for m in btc_b58.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in btc_bech32.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in ltc_b58.findall(text):
                hits.append({"chain": "litecoin", "address": m})
            for m in bch_b58.findall(text):
                hits.append({"chain": "bitcoin-cash", "address": m})
            for m in trx_b58.findall(text):
                hits.append({"chain": "tron", "address": m})
            return hits

        out: List[Dict[str, Any]] = []
        for row in reader:
            # combine all string fields
            fields: List[str] = []
            for k, v in row.items():
                if isinstance(v, str) and v:
                    fields.append(v)
            blob = " | ".join(fields)
            for hit in detect(blob):
                out.append({
                    'chain': hit['chain'],
                    'address': hit['address'],
                    'label': 'sanctioned',
                    'category': 'sanctions',
                    'source': 'EU',
                    'confidence': 0.75,
                })
        return out


class UKSource(SanctionsSource):
    """United Kingdom Sanctions List"""

    def __init__(self):
        # Prefer OFSI download API; allow ENV override
        super().__init__("UK", "https://sanctionslistservice.ofsi.hmtreasury.gov.uk/api/search/download?format=csv", "csv", env_key="UK_URL")

    async def fetch(self) -> List[Dict[str, Any]]:
        """Try multiple candidate URLs for UK consolidated list."""
        candidates = [
            # Official OFSI API CSV download
            "https://sanctionslistservice.ofsi.hmtreasury.gov.uk/api/search/download?format=csv",
            # Legacy attachments (filenames may change)
            "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1151318/ConList.csv",
            "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1147618/ConList.csv",
        ]
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for url in [self.url, *candidates]:
                try:
                    resp = await client.get(url, timeout=90)
                    resp.raise_for_status()
                    if self.format_type == "csv":
                        return await self._parse_csv(resp.text)
                except Exception as e:
                    logger.warning(f"UK source candidate failed {url}: {e}")
                    continue
        return []

    async def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse UK sanctions CSV by scanning all text fields for crypto addresses (regex-based)."""
        lines = content.splitlines()
        if not lines:
            return []
        reader = csv.DictReader(lines)

        # Reuse simplified regexes from OFAC
        eth_re = re.compile(r"0x[a-fA-F0-9]{40}")
        btc_b58 = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        ltc_b58 = re.compile(r"\b[L3][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        bch_b58 = re.compile(r"\b[qp][a-z0-9]{41}\b", re.IGNORECASE)
        btc_bech32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b")
        trx_b58 = re.compile(r"\bT[a-km-zA-HJ-NP-Z1-9]{25,34}\b")

        def detect(text: str) -> List[Dict[str, str]]:
            hits: List[Dict[str, str]] = []
            if not text:
                return hits
            for m in eth_re.findall(text):
                hits.append({"chain": "ethereum", "address": m.lower()})
            for m in btc_b58.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in btc_bech32.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in ltc_b58.findall(text):
                hits.append({"chain": "litecoin", "address": m})
            for m in bch_b58.findall(text):
                hits.append({"chain": "bitcoin-cash", "address": m})
            for m in trx_b58.findall(text):
                hits.append({"chain": "tron", "address": m})
            return hits

        out: List[Dict[str, Any]] = []
        for row in reader:
            # combine all string fields
            fields: List[str] = []
            for k, v in row.items():
                if isinstance(v, str) and v:
                    fields.append(v)
            blob = " | ".join(fields)
            for hit in detect(blob):
                out.append({
                    'chain': hit['chain'],
                    'address': hit['address'],
                    'label': 'sanctioned',
                    'category': 'sanctions',
                    'source': 'UK',
                    'confidence': 0.8,
                })
        return out


class CanadaSource(SanctionsSource):
    """Canada Sanctions List (SEMA)"""

    def __init__(self):
        super().__init__("Canada", "https://www.international.gc.ca/world-monde/assets/office_docs/international_relations-relations_internationales/sanctions/sema-lmes.csv", "csv", env_key="CANADA_URL")

    async def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse Canada sanctions CSV."""
        lines = content.splitlines()
        if not lines:
            return []
        reader = csv.DictReader(lines)

        eth_re = re.compile(r"0x[a-fA-F0-9]{40}")
        btc_b58 = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        btc_bech32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b")

        def detect(text: str) -> List[Dict[str, str]]:
            hits: List[Dict[str, str]] = []
            if not text:
                return hits
            for m in eth_re.findall(text):
                hits.append({"chain": "ethereum", "address": m.lower()})
            for m in btc_b58.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in btc_bech32.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            return hits

        out: List[Dict[str, Any]] = []
        for row in reader:
            fields: List[str] = []
            for k, v in row.items():
                if isinstance(v, str) and v:
                    fields.append(v)
            blob = " | ".join(fields)
            for hit in detect(blob):
                out.append({
                    'chain': hit['chain'],
                    'address': hit['address'],
                    'label': 'sanctioned',
                    'category': 'sanctions',
                    'source': 'Canada',
                    'confidence': 0.85,
                })
        return out


class AustraliaSource(SanctionsSource):
    """Australia Sanctions List (DFAT)"""

    def __init__(self):
        super().__init__("Australia", "https://www.dfat.gov.au/sites/default/files/regulation8_consolidated.csv", "csv", env_key="AUSTRALIA_URL")

    async def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse Australia sanctions CSV."""
        lines = content.splitlines()
        if not lines:
            return []
        reader = csv.DictReader(lines)

        eth_re = re.compile(r"0x[a-fA-F0-9]{40}")
        btc_b58 = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        btc_bech32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b")
        trx_b58 = re.compile(r"\bT[a-km-zA-HJ-NP-Z1-9]{25,34}\b")

        def detect(text: str) -> List[Dict[str, str]]:
            hits: List[Dict[str, str]] = []
            if not text:
                return hits
            for m in eth_re.findall(text):
                hits.append({"chain": "ethereum", "address": m.lower()})
            for m in btc_b58.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in btc_bech32.findall(text):
                hits.append({"chain": "bitcoin", "address": m})
            for m in trx_b58.findall(text):
                hits.append({"chain": "tron", "address": m})
            return hits

        out: List[Dict[str, Any]] = []
        for row in reader:
            fields: List[str] = []
            for k, v in row.items():
                if isinstance(v, str) and v:
                    fields.append(v)
            blob = " | ".join(fields)
            for hit in detect(blob):
                out.append({
                    'chain': hit['chain'],
                    'address': hit['address'],
                    'label': 'sanctioned',
                    'category': 'sanctions',
                    'source': 'Australia',
                    'confidence': 0.85,
                })
        return out


class SanctionsIndexer:
    """Indexes sanctions data from multiple sources"""

    def __init__(self):
        self.sources = [
            OFACSource(),
            UNSource(),
            EUSource(),
            UKSource(),
            CanadaSource(),
            AustraliaSource()
        ]

    async def fetch_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all sanctions data"""
        results = {}

        for source in self.sources:
            logger.info(f"Fetching {source.name} sanctions...")
            data = await source.fetch()
            results[source.name] = data
            logger.info(f"Found {len(data)} entries from {source.name}")
            
            # Update metrics
            if SANCTIONS_ENTRIES_TOTAL:
                SANCTIONS_ENTRIES_TOTAL.labels(source=source.name.lower()).inc(len(data))
            if SANCTIONS_ADDRESSES_TOTAL:
                addresses = len(set(item.get('address', '') for item in data if item.get('address')))
                SANCTIONS_ADDRESSES_TOTAL.labels(source=source.name.lower()).inc(addresses)
            if SANCTIONS_UPDATE_TIMESTAMP:
                import time
                SANCTIONS_UPDATE_TIMESTAMP.labels(source=source.name.lower()).set(time.time())

        return results

    def dedupe(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates based on chain+address"""
        seen = set()
        unique = []

        for item in data:
            key = f"{item['chain']}:{item['address']}"
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

    async def get_normalized_data(self) -> List[Dict[str, Any]]:
        """Get all sanctions data normalized and deduped"""
        all_data = await self.fetch_all()

        merged = []
        for source_data in all_data.values():
            merged.extend(source_data)

        # Normalize and dedupe
        normalized = []
        for item in merged:
            normalized_item = {
                'chain': (item.get('chain') or '').lower(),
                'address': (item.get('address') or '').lower(),
                'label': item.get('label', 'sanctioned'),
                'category': item.get('category', 'sanctions'),
                'source': item.get('source', 'unknown'),
                'confidence': float(item.get('confidence', 0.8)),
                'metadata': {
                    'name': item.get('name', ''),
                    'sanction_type': item.get('sanction_type', ''),
                    'source_url': item.get('source_url', '')
                }
            }
            normalized.append(normalized_item)

        return self.dedupe(normalized)


# Global instance
sanctions_indexer = SanctionsIndexer()
