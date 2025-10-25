"""
OFAC Sanctions List Service
Automatically downloads and updates OFAC SDN list

Features:
- Daily automatic updates
- CSV parsing
- Database storage
- Address normalization
- Cache integration
"""

import logging
import csv
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set
from io import StringIO
import asyncio

import httpx
from app.db.postgres import postgres_client
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class OFACSanctionsService:
    """
    OFAC Sanctions List Manager
    
    Downloads, parses, and stores OFAC SDN (Specially Designated Nationals)
    list with focus on crypto addresses.
    """
    
    # OFAC SDN List URLs
    SDN_LIST_URL = "https://www.treasury.gov/ofac/downloads/sdnlist.txt"
    SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    SDN_ALT_URL = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV"
    
    # Additional crypto-specific sanctions lists
    CHAINALYSIS_SANCTIONS_URL = "https://public.chainalysis.com/sanctions/ofac_sanctions.csv"
    
    # Cache keys
    CACHE_KEY_PREFIX = "ofac:sanctions:"
    CACHE_KEY_ALL = f"{CACHE_KEY_PREFIX}all"
    CACHE_KEY_ETH = f"{CACHE_KEY_PREFIX}eth"
    CACHE_KEY_BTC = f"{CACHE_KEY_PREFIX}btc"
    CACHE_TTL = 86400  # 24 hours
    
    # Update interval
    UPDATE_INTERVAL_HOURS = 24
    
    def __init__(self):
        self.sanctioned_addresses: Set[str] = set()
        self.sanctioned_entities: Dict[str, Dict] = {}
        self.last_update: Optional[datetime] = None
        
        logger.info("OFAC Sanctions Service initialized")
    
    async def start_auto_update(self):
        """Start automatic daily updates"""
        logger.info("Starting OFAC auto-update loop")
        
        # Initial update
        await self.update_sanctions_list()
        
        # Background task
        while True:
            try:
                await asyncio.sleep(self.UPDATE_INTERVAL_HOURS * 3600)
                await self.update_sanctions_list()
            except Exception as e:
                logger.error(f"Auto-update error: {e}", exc_info=True)
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def update_sanctions_list(self) -> Dict[str, Any]:
        """
        Download and update OFAC sanctions list
        
        Returns:
            Update statistics
        """
        logger.info("Updating OFAC sanctions list...")
        start_time = datetime.utcnow()
        
        stats = {
            "started_at": start_time.isoformat(),
            "success": False,
            "addresses_added": 0,
            "entities_added": 0,
            "errors": []
        }
        
        try:
            # Download from multiple sources
            sanctions_data = await self._download_sanctions()
            
            if not sanctions_data:
                stats["errors"].append("Failed to download from all sources")
                return stats
            
            # Parse and normalize
            parsed = await self._parse_sanctions(sanctions_data)
            
            # Store in database
            stored_count = await self._store_sanctions(parsed)
            
            # Update cache
            await self._update_cache(parsed)
            
            # Update in-memory
            self.sanctioned_addresses = {
                addr.lower() for addr in parsed.get("addresses", [])
            }
            self.sanctioned_entities = parsed.get("entities", {})
            self.last_update = datetime.utcnow()
            
            stats["success"] = True
            stats["addresses_added"] = len(self.sanctioned_addresses)
            stats["entities_added"] = len(self.sanctioned_entities)
            stats["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"OFAC update complete: {stats['addresses_added']} addresses, "
                f"{stats['entities_added']} entities"
            )
            
        except Exception as e:
            logger.error(f"OFAC update failed: {e}", exc_info=True)
            stats["errors"].append(str(e))
        
        return stats
    
    async def _download_sanctions(self) -> Optional[str]:
        """Download sanctions list from OFAC"""
        
        urls = [
            self.SDN_CSV_URL,
            self.SDN_ALT_URL,
            # self.CHAINALYSIS_SANCTIONS_URL,  # Optional: Community-maintained list
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for url in urls:
                try:
                    logger.info(f"Downloading from: {url}")
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully downloaded ({len(response.text)} bytes)")
                        return response.text
                    else:
                        logger.warning(f"Failed: HTTP {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Download error from {url}: {e}")
                    continue
        
        return None
    
    async def _parse_sanctions(self, csv_data: str) -> Dict:
        """
        Parse CSV sanctions data
        
        OFAC SDN CSV Format:
        0: Entity Number
        1: SDN Name
        2: SDN Type (individual, entity, vessel, aircraft)
        3: Program
        4: Title
        5: Call Sign
        6: Vess type
        7: Tonnage
        8: GRT
        9: Vess flag
        10: Vess owner
        11: Remarks (contains addresses!)
        """
        
        parsed = {
            "addresses": [],
            "entities": {}
        }
        
        try:
            reader = csv.reader(StringIO(csv_data))
            
            for row in reader:
                if not row or len(row) < 2:
                    continue
                
                # Skip header
                if row[0].strip().lower() == "ent_num":
                    continue
                
                entity_num = row[0].strip()
                name = row[1].strip() if len(row) > 1 else ""
                sdn_type = row[2].strip() if len(row) > 2 else ""
                program = row[3].strip() if len(row) > 3 else ""
                remarks = row[11].strip() if len(row) > 11 else ""
                
                # Extract crypto addresses from remarks
                addresses = self._extract_crypto_addresses(remarks)
                
                if addresses:
                    entity_info = {
                        "entity_num": entity_num,
                        "name": name,
                        "type": sdn_type,
                        "program": program,
                        "addresses": addresses,
                        "added_date": datetime.utcnow().isoformat()
                    }
                    
                    for addr in addresses:
                        addr_lower = addr.lower()
                        parsed["addresses"].append(addr_lower)
                        parsed["entities"][addr_lower] = entity_info
            
            logger.info(f"Parsed {len(parsed['addresses'])} sanctioned addresses")
            
        except Exception as e:
            logger.error(f"Parsing error: {e}", exc_info=True)
        
        return parsed
    
    def _extract_crypto_addresses(self, text: str) -> List[str]:
        """
        Extract cryptocurrency addresses from text
        
        Supports:
        - Ethereum: 0x[40 hex chars]
        - Bitcoin: [26-35 alphanumeric starting with 1, 3, or bc1]
        """
        import re
        
        addresses = []
        
        # Ethereum addresses (0x followed by 40 hex chars)
        eth_pattern = r'0x[a-fA-F0-9]{40}'
        eth_matches = re.findall(eth_pattern, text)
        addresses.extend(eth_matches)
        
        # Bitcoin addresses (simplified - production needs better validation)
        btc_pattern = r'\b(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}\b'
        btc_matches = re.findall(btc_pattern, text)
        addresses.extend(btc_matches)
        
        return addresses
    
    async def _store_sanctions(self, parsed: Dict) -> int:
        """Store sanctions in database"""
        
        stored_count = 0
        
        try:
            async with postgres_client.acquire() as conn:
                # Create table if not exists
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ofac_sanctions (
                        address VARCHAR(100) PRIMARY KEY,
                        entity_num VARCHAR(50),
                        entity_name TEXT,
                        entity_type VARCHAR(50),
                        program VARCHAR(100),
                        added_date TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Create index
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ofac_address_lower 
                    ON ofac_sanctions (LOWER(address))
                """)
                
                # Insert/Update
                for addr, entity_info in parsed["entities"].items():
                    await conn.execute("""
                        INSERT INTO ofac_sanctions 
                        (address, entity_num, entity_name, entity_type, program, added_date)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (address) 
                        DO UPDATE SET last_updated = NOW()
                    """, 
                        addr,
                        entity_info["entity_num"],
                        entity_info["name"],
                        entity_info["type"],
                        entity_info["program"],
                        entity_info["added_date"]
                    )
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} sanctions in database")
            
        except Exception as e:
            logger.error(f"Database storage error: {e}", exc_info=True)
        
        return stored_count
    
    async def _update_cache(self, parsed: Dict):
        """Update Redis cache"""
        
        try:
            client = await redis_client.get_client()
            if not client:
                return
            
            # Store all addresses as set
            if parsed["addresses"]:
                await client.delete(self.CACHE_KEY_ALL)
                await client.sadd(self.CACHE_KEY_ALL, *parsed["addresses"])
                await client.expire(self.CACHE_KEY_ALL, self.CACHE_TTL)
            
            # Store entity details as hash
            for addr, entity in parsed["entities"].items():
                key = f"{self.CACHE_KEY_PREFIX}{addr}"
                await client.hset(key, mapping={
                    "name": entity["name"],
                    "type": entity["type"],
                    "program": entity["program"]
                })
                await client.expire(key, self.CACHE_TTL)
            
            logger.info("Cache updated successfully")
            
        except Exception as e:
            logger.warning(f"Cache update error: {e}")
    
    async def is_sanctioned(self, address: str) -> bool:
        """
        Check if address is on OFAC sanctions list
        
        Args:
            address: Crypto address to check
        
        Returns:
            True if sanctioned
        """
        addr_lower = address.lower()
        
        # Check cache first
        try:
            client = await redis_client.get_client()
            if client:
                is_member = await client.sismember(self.CACHE_KEY_ALL, addr_lower)
                if is_member:
                    return True
        except Exception as e:
            logger.warning(f"Cache check error: {e}")
        
        # Check in-memory
        if addr_lower in self.sanctioned_addresses:
            return True
        
        # Check database
        try:
            async with postgres_client.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT 1 FROM ofac_sanctions WHERE LOWER(address) = $1",
                    addr_lower
                )
                return row is not None
        except Exception as e:
            logger.error(f"Database check error: {e}")
            return False
    
    async def get_entity_info(self, address: str) -> Optional[Dict]:
        """Get entity information for sanctioned address"""
        
        addr_lower = address.lower()
        
        # Check cache
        try:
            client = await redis_client.get_client()
            if client:
                key = f"{self.CACHE_KEY_PREFIX}{addr_lower}"
                data = await client.hgetall(key)
                if data:
                    return data
        except Exception:
            pass
        
        # Check database
        try:
            async with postgres_client.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM ofac_sanctions WHERE LOWER(address) = $1",
                    addr_lower
                )
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Entity info error: {e}")
        
        return None
    
    async def get_statistics(self) -> Dict:
        """Get sanctions list statistics"""
        
        try:
            async with postgres_client.acquire() as conn:
                total = await conn.fetchval("SELECT COUNT(*) FROM ofac_sanctions")
                
                by_program = await conn.fetch("""
                    SELECT program, COUNT(*) as count 
                    FROM ofac_sanctions 
                    GROUP BY program 
                    ORDER BY count DESC
                """)
                
                return {
                    "total_addresses": total,
                    "last_update": self.last_update.isoformat() if self.last_update else None,
                    "by_program": [dict(row) for row in by_program],
                    "in_memory": len(self.sanctioned_addresses)
                }
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {
                "total_addresses": 0,
                "error": str(e)
            }


# Singleton instance
ofac_service = OFACSanctionsService()

__all__ = ['OFACSanctionsService', 'ofac_service']
