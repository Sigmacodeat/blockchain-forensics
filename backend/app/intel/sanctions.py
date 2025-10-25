"""
Sanctions Indexer - Multi-Source Sanctions Intelligence
======================================================

Fetches, parses, and merges sanctions data from multiple sources:
- OFAC (US Treasury)
- EU Sanctions
- UK Sanctions (HMT)
- UN Sanctions

Features:
- Incremental updates with ETags/Last-Modified
- Normalization and deduplication
- DB integration via labels_repo.bulk_upsert
- Sanctions-specific metrics
- Configurable refresh intervals
"""

from __future__ import annotations
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Import labels repo for DB integration
try:
    from app.repos.labels_repo import bulk_upsert
    DB_INTEGRATION = True
except ImportError:
    DB_INTEGRATION = False
    logger.warning("Labels repo not available, running without DB integration")

try:
    from app.metrics import (
        SANCTIONS_FETCH_TOTAL,
        SANCTIONS_FETCH_DURATION,
        SANCTIONS_ENTRIES_PARSED,
        SANCTIONS_ENTRIES_STORED,
        SANCTIONS_UPDATE_ERRORS,
    )
except Exception:
    # Fallback metrics if not available
    class MockCounter:
        def inc(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self

    class MockHistogram:
        def observe(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self

    SANCTIONS_FETCH_TOTAL = MockCounter()
    SANCTIONS_FETCH_DURATION = MockHistogram()
    SANCTIONS_ENTRIES_PARSED = MockCounter()
    SANCTIONS_ENTRIES_STORED = MockCounter()
    SANCTIONS_UPDATE_ERRORS = MockCounter()


class SanctionsSource:
    """Represents a sanctions data source"""

    def __init__(
        self,
        name: str,
        url: str,
        format_type: str,  # "xml", "json", "csv"
        parser_func: callable,
        refresh_interval: timedelta = timedelta(days=1),
        headers: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.url = url
        self.format_type = format_type
        self.parser_func = parser_func
        self.refresh_interval = refresh_interval
        self.headers = headers or {}
        self.last_fetch: Optional[datetime] = None
        self.etag: Optional[str] = None
        self.last_modified: Optional[str] = None

    async def should_fetch(self) -> bool:
        """Check if source should be fetched based on refresh interval"""
        if not self.last_fetch:
            return True
        return datetime.utcnow() - self.last_fetch > self.refresh_interval

    async def fetch_data(self) -> Optional[str]:
        """Fetch data from source with ETag/Last-Modified support"""
        try:
            headers = dict(self.headers)

            # Add conditional headers for incremental updates
            if self.etag:
                headers["If-None-Match"] = self.etag
            if self.last_modified:
                headers["If-Modified-Since"] = self.last_modified

            start_time = datetime.utcnow()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.url,
                    headers=headers,
                    timeout=60.0,
                    follow_redirects=True
                )

                # Handle conditional responses
                if response.status_code == 304:  # Not Modified
                    logger.debug(f"Source {self.name} not modified, skipping")
                    return None

                response.raise_for_status()

                # Update metadata for next fetch
                self.etag = response.headers.get("ETag")
                self.last_modified = response.headers.get("Last-Modified")
                self.last_fetch = datetime.utcnow()

                duration = (datetime.utcnow() - start_time).total_seconds()

                # Update metrics
                try:
                    SANCTIONS_FETCH_TOTAL.labels(source=self.name).inc()
                    SANCTIONS_FETCH_DURATION.labels(source=self.name).observe(duration)
                except Exception:
                    pass

                return response.text

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 304:
                logger.debug(f"Source {self.name} not modified")
                return None
            logger.error(f"HTTP error fetching {self.name}: {e}")
            try:
                SANCTIONS_UPDATE_ERRORS.labels(source=self.name, error_type="http").inc()
            except Exception:
                pass
            return None
        except Exception as e:
            logger.error(f"Error fetching {self.name}: {e}")
            try:
                SANCTIONS_UPDATE_ERRORS.labels(source=self.name, error_type="network").inc()
            except Exception:
                pass
            return None


class SanctionsIndexer:
    """Main sanctions indexer service"""

    def __init__(self):
        self.sources: List[SanctionsSource] = []
        self._initialize_sources()

    def _initialize_sources(self):
        """Initialize all sanctions sources"""

        # OFAC Specially Designated Nationals (SDN) List
        self.sources.append(SanctionsSource(
            name="ofac_sdn",
            url="https://www.treasury.gov/ofac/downloads/sdn.xml",
            format_type="xml",
            parser_func=self._parse_ofac_xml,
            refresh_interval=timedelta(hours=6),
            headers={"User-Agent": "Blockchain-Forensics-Sanctions-Indexer/1.0"}
        ))

        # EU Sanctions List (XML format)
        self.sources.append(SanctionsSource(
            name="eu_sanctions",
            url="https://data.europa.eu/api/hub/search/sanctions",
            format_type="json",  # EU provides JSON API
            parser_func=self._parse_eu_json,
            refresh_interval=timedelta(days=1),
        ))

        # UK HMT Sanctions (CSV format)
        self.sources.append(SanctionsSource(
            name="uk_hmt",
            url="https://www.gov.uk/government/publications/financial-sanctions-consolidated-list-of-targets/consolidated-list-of-targets.csv",
            format_type="csv",
            parser_func=self._parse_uk_csv,
            refresh_interval=timedelta(hours=12),
        ))

        # UN Sanctions (XML format)
        self.sources.append(SanctionsSource(
            name="un_sanctions",
            url="https://scsanctions.un.org/resources/xml/en/consolidated.xml",
            format_type="xml",
            parser_func=self._parse_un_xml,
            refresh_interval=timedelta(days=1),
        ))

    def _parse_ofac_xml(self, xml_content: str) -> List[Dict[str, str]]:
        """Parse OFAC SDN XML format"""
        entries = []

        try:
            root = ET.fromstring(xml_content)

            for entry in root.findall(".//sdnEntry"):
                # Extract addresses (focus on crypto-relevant entries)
                addresses = entry.findall(".//address")

                for addr in addresses:
                    # Look for crypto-related address types or content
                    address_type = addr.findtext("addressType")
                    address_content = addr.findtext("address")

                    if self._is_crypto_relevant(address_type, address_content):
                        entries.append({
                            'chain': 'ethereum',  # Default, could be enhanced
                            'address': self._extract_address_from_text(address_content),
                            'label': 'sanctioned',
                            'category': 'sanctions',
                            'source': 'ofac',
                            'confidence': 1.0,
                            'metadata': {
                                'sanction_type': 'SDN',
                                'name': entry.findtext("firstName", "") + " " + entry.findtext("lastName", ""),
                                'program': entry.findtext("program", ""),
                                'list_type': 'SDN'
                            }
                        })

        except Exception as e:
            logger.error(f"Error parsing OFAC XML: {e}")

        return entries

    def _parse_eu_json(self, json_content: str) -> List[Dict[str, str]]:
        """Parse EU Sanctions JSON format"""
        entries = []

        try:
            data = json.loads(json_content)

            # EU API structure - adjust based on actual format
            for item in data.get("results", []):
                if item.get("type") == "sanction":
                    # Extract addresses if available
                    addresses = item.get("addresses", [])

                    for addr in addresses:
                        if self._is_crypto_relevant(None, addr.get("address", "")):
                            entries.append({
                                'chain': 'ethereum',
                                'address': self._extract_address_from_text(addr.get("address", "")),
                                'label': 'sanctioned',
                                'category': 'sanctions',
                                'source': 'eu',
                                'confidence': 1.0,
                                'metadata': {
                                    'sanction_type': item.get("sanctionType", ""),
                                    'name': item.get("name", ""),
                                    'regulation': item.get("regulation", "")
                                }
                            })

        except Exception as e:
            logger.error(f"Error parsing EU JSON: {e}")

        return entries

    def _parse_uk_csv(self, csv_content: str) -> List[Dict[str, str]]:
        """Parse UK HMT CSV format"""
        entries = []

        try:
            lines = csv_content.strip().split('\n')
            # Skip header
            for line in lines[1:]:
                if not line.strip():
                    continue

                # CSV format: Name,DOB,Nationality,Address,Other Info
                parts = [p.strip() for p in line.split(',')]

                if len(parts) >= 4:
                    name = parts[0]
                    address = parts[3]

                    if self._is_crypto_relevant(None, address):
                        crypto_addr = self._extract_address_from_text(address)

                        if crypto_addr:
                            entries.append({
                                'chain': 'ethereum',
                                'address': crypto_addr,
                                'label': 'sanctioned',
                                'category': 'sanctions',
                                'source': 'uk_hmt',
                                'confidence': 0.9,
                                'metadata': {
                                    'name': name,
                                    'nationality': parts[2] if len(parts) > 2 else "",
                                    'list_type': 'HMT'
                                }
                            })

        except Exception as e:
            logger.error(f"Error parsing UK CSV: {e}")

        return entries

    def _parse_un_xml(self, xml_content: str) -> List[Dict[str, str]]:
        """Parse UN Sanctions XML format"""
        entries = []

        try:
            root = ET.fromstring(xml_content)

            for individual in root.findall(".//INDIVIDUAL"):
                # Extract data
                name = individual.findtext("FIRST_NAME", "") + " " + individual.findtext("SECOND_NAME", "")
                designation = individual.findtext("DESIGNATION")

                # Look for crypto addresses in comments or other fields
                comments = individual.findtext("COMMENTS1", "")

                if self._is_crypto_relevant(None, comments):
                    crypto_addr = self._extract_address_from_text(comments)

                    if crypto_addr:
                        entries.append({
                            'chain': 'ethereum',
                            'address': crypto_addr,
                            'label': 'sanctioned',
                            'category': 'sanctions',
                            'source': 'un',
                            'confidence': 0.8,
                            'metadata': {
                                'name': name,
                                'designation': designation or "",
                                'committee': individual.findtext("UN_LIST_TYPE", ""),
                                'reference_number': individual.findtext("REFERENCE_NUMBER", "")
                            }
                        })

        except Exception as e:
            logger.error(f"Error parsing UN XML: {e}")

        return entries

    def _is_crypto_relevant(self, address_type: Optional[str], content: str) -> bool:
        """Check if content appears to contain crypto-related information"""
        if not content:
            return False

        content_lower = content.lower()

        # Look for crypto-related keywords
        crypto_keywords = [
            'bitcoin', 'ethereum', 'wallet', 'address', '0x', 'bc1', 'crypto',
            'blockchain', 'virtual currency', 'digital asset'
        ]

        return any(keyword in content_lower for keyword in crypto_keywords)

    def _extract_address_from_text(self, text: str) -> Optional[str]:
        """Extract crypto address from text using regex patterns"""
        if not text:
            return None

        # Ethereum address pattern
        eth_pattern = r'0x[0-9a-fA-F]{40}'
        eth_match = re.search(eth_pattern, text)
        if eth_match:
            return eth_match.group(0).lower()

        # Bitcoin address patterns
        btc_patterns = [
            r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Legacy
            r'bc1[ac-hj-np-z02-9]{11,71}'        # SegWit
        ]

        for pattern in btc_patterns:
            btc_match = re.search(pattern, text)
            if btc_match:
                return btc_match.group(0).lower()

        # Solana address pattern (simplified)
        sol_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
        sol_match = re.search(sol_pattern, text)
        if sol_match:
            return sol_match.group(0)

        return None

    def normalize_entries(self, entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Normalize and deduplicate sanctions entries"""
        seen = set()
        normalized = []

        for entry in entries:
            key = f"{entry['chain']}:{entry['address']}:{entry['label']}"
            if key not in seen:
                seen.add(key)
                normalized_entry = {
                    'chain': entry.get('chain', 'ethereum').lower(),
                    'address': entry.get('address', '').lower(),
                    'label': entry.get('label', 'sanctioned'),
                    'category': entry.get('category', 'sanctions'),
                    'source': entry.get('source', 'unknown'),
                    'confidence': float(entry.get('confidence', 1.0)),
                    'metadata': entry.get('metadata', {})
                }
                normalized.append(normalized_entry)

        return normalized

    async def fetch_all_sources(self) -> List[Dict[str, str]]:
        """Fetch data from all sources that need updating"""
        tasks = []

        for source in self.sources:
            if await source.should_fetch():
                tasks.append(source.fetch_data())

        if not tasks:
            logger.info("No sources need updating")
            return []

        logger.info(f"Fetching {len(tasks)} sanctions sources")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_entries = []
        for i, result in enumerate(results):
            source = self.sources[i]

            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {source.name}: {result}")
                try:
                    SANCTIONS_UPDATE_ERRORS.labels(source=source.name, error_type="fetch").inc()
                except Exception:
                    pass
                continue

            if result is None:  # Not modified
                continue

            # Parse source data
            try:
                entries = source.parser_func(result)
                logger.info(f"Parsed {len(entries)} entries from {source.name}")

                try:
                    SANCTIONS_ENTRIES_PARSED.labels(source=source.name).inc(len(entries))
                except Exception:
                    pass

                all_entries.extend(entries)

            except Exception as e:
                logger.error(f"Failed to parse {source.name}: {e}")
                try:
                    SANCTIONS_UPDATE_ERRORS.labels(source=source.name, error_type="parse").inc()
                except Exception:
                    pass

        return self.normalize_entries(all_entries)

    async def run_update(self) -> Dict[str, Any]:
        """Run full sanctions update cycle"""
        start_time = datetime.utcnow()

        try:
            logger.info("Starting sanctions update cycle")
            entries = await self.fetch_all_sources()

            logger.info(f"Fetched {len(entries)} sanctions entries")

            # Store in database if available
            if DB_INTEGRATION and entries:
                try:
                    inserted, existing = await bulk_upsert(entries)
                    logger.info(f"DB: {inserted} inserted, {existing} existing")

                    try:
                        SANCTIONS_ENTRIES_STORED.inc(inserted)
                    except Exception:
                        pass

                    return {
                        "status": "success",
                        "total_entries": len(entries),
                        "sources": list(set(e.get("source", "unknown") for e in entries)),
                        "chains": list(set(e.get("chain", "ethereum") for e in entries)),
                        "db_inserted": inserted,
                        "db_existing": existing,
                        "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                    }

                except Exception as e:
                    logger.error(f"DB storage failed: {e}")
                    try:
                        SANCTIONS_UPDATE_ERRORS.labels(source="db", error_type="storage").inc()
                    except Exception:
                        pass

                    return {
                        "status": "error",
                        "error": str(e),
                        "total_entries": len(entries),
                        "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                    }
            else:
                return {
                    "status": "success",
                    "total_entries": len(entries),
                    "sources": list(set(e.get("source", "unknown") for e in entries)),
                    "chains": list(set(e.get("chain", "ethereum") for e in entries)),
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                }

        except Exception as e:
            logger.error(f"Sanctions update cycle failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
            }


# Global indexer instance
sanctions_indexer = SanctionsIndexer()


async def run_sanctions_update() -> Dict[str, Any]:
    """Convenience function to run sanctions update"""
    return await sanctions_indexer.run_update()
