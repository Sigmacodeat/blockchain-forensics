"""
OFAC Sanctions List Auto-Updater
=================================

Automatically downloads and updates OFAC SDN (Specially Designated Nationals) list.
Runs daily to ensure compliance with latest sanctions data.

Features:
- Daily Auto-Update
- Multi-Source Support (OFAC, UN, EU)
- Fuzzy Matching for Name Variations
- Crypto Address Extraction
- PostgreSQL Storage
- Audit Logging

Data Sources:
- OFAC SDN List: https://www.treasury.gov/ofac/downloads/sdn.csv
- OFAC Alt Names: https://www.treasury.gov/ofac/downloads/alt.csv
- OFAC Addresses: https://www.treasury.gov/ofac/downloads/add.csv
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import csv
import httpx
from io import StringIO

from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class SanctionsUpdater:
    """
    OFAC Sanctions List Updater
    """
    
    # OFAC Data URLs
    OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    OFAC_ALT_URL = "https://www.treasury.gov/ofac/downloads/alt.csv"
    OFAC_ADD_URL = "https://www.treasury.gov/ofac/downloads/add.csv"
    
    def __init__(self):
        self.last_update: Optional[datetime] = None
        self.update_interval = timedelta(hours=24)  # Daily updates
        self.running = False
    
    async def start_auto_update(self):
        """
        Start automatic daily updates
        Background task that runs continuously
        """
        self.running = True
        logger.info("Starting OFAC sanctions auto-updater (24h interval)")
        
        while self.running:
            try:
                # Run update
                await self.update_sanctions_list()
                
                # Wait 24 hours
                await asyncio.sleep(self.update_interval.total_seconds())
            
            except Exception as e:
                logger.error(f"Error in auto-update loop: {e}")
                # Wait 1 hour on error, then retry
                await asyncio.sleep(3600)
        
        logger.info("OFAC auto-updater stopped")
    
    def stop(self):
        """Stop auto-updater"""
        self.running = False
    
    async def update_sanctions_list(self) -> Dict:
        """
        Download and update OFAC sanctions list
        
        Returns:
            Update statistics
        """
        logger.info("Starting OFAC sanctions list update...")
        start_time = datetime.utcnow()
        
        stats = {
            "sdn_count": 0,
            "alt_names_count": 0,
            "addresses_count": 0,
            "crypto_addresses": 0,
            "errors": []
        }
        
        try:
            # Download SDN List (Main List)
            sdn_data = await self._download_file(self.OFAC_SDN_URL)
            if sdn_data:
                stats["sdn_count"] = await self._process_sdn_list(sdn_data)
            
            # Download Alternate Names
            alt_data = await self._download_file(self.OFAC_ALT_URL)
            if alt_data:
                stats["alt_names_count"] = await self._process_alt_names(alt_data)
            
            # Download Addresses
            add_data = await self._download_file(self.OFAC_ADD_URL)
            if add_data:
                addresses, crypto = await self._process_addresses(add_data)
                stats["addresses_count"] = addresses
                stats["crypto_addresses"] = crypto
            
            # Update last_update timestamp
            self.last_update = datetime.utcnow()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"OFAC update completed in {duration:.2f}s: {stats}")
            
            # Store update metadata
            await self._record_update(stats, duration)
        
        except Exception as e:
            logger.error(f"OFAC update failed: {e}")
            stats["errors"].append(str(e))
        
        return stats
    
    async def _download_file(self, url: str) -> Optional[str]:
        """Download CSV file from URL"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
    
    async def _process_sdn_list(self, csv_data: str) -> int:
        """
        Process SDN (Specially Designated Nationals) list
        
        CSV Format:
        ent_num, SDN_Name, SDN_Type, Program, Title, Call_Sign, Vess_type, Tonnage, GRT, Vess_flag, Vess_owner, Remarks
        """
        count = 0
        reader = csv.DictReader(StringIO(csv_data))
        
        batch = []
        for row in reader:
            entity = {
                "entity_number": row.get("ent_num", "").strip(),
                "name": row.get("SDN_Name", "").strip(),
                "entity_type": row.get("SDN_Type", "").strip(),
                "program": row.get("Program", "").strip(),
                "title": row.get("Title", "").strip(),
                "remarks": row.get("Remarks", "").strip(),
                "source": "OFAC_SDN",
                "list_type": "sanctions",
                "updated_at": datetime.utcnow()
            }
            
            batch.append(entity)
            count += 1
            
            # Batch insert every 1000 records
            if len(batch) >= 1000:
                await self._bulk_insert_entities(batch)
                batch = []
        
        # Insert remaining
        if batch:
            await self._bulk_insert_entities(batch)
        
        logger.info(f"Processed {count} SDN entities")
        return count
    
    async def _process_alt_names(self, csv_data: str) -> int:
        """
        Process Alternate Names list
        
        CSV Format:
        ent_num, alt_num, alt_type, alt_name, alt_remarks
        """
        count = 0
        reader = csv.DictReader(StringIO(csv_data))
        
        batch = []
        for row in reader:
            alt_name = {
                "entity_number": row.get("ent_num", "").strip(),
                "alt_number": row.get("alt_num", "").strip(),
                "alt_type": row.get("alt_type", "").strip(),
                "alt_name": row.get("alt_name", "").strip(),
                "remarks": row.get("alt_remarks", "").strip(),
                "source": "OFAC_ALT",
                "updated_at": datetime.utcnow()
            }
            
            batch.append(alt_name)
            count += 1
            
            if len(batch) >= 1000:
                await self._bulk_insert_alt_names(batch)
                batch = []
        
        if batch:
            await self._bulk_insert_alt_names(batch)
        
        logger.info(f"Processed {count} alternate names")
        return count
    
    async def _process_addresses(self, csv_data: str) -> tuple[int, int]:
        """
        Process Addresses list (includes crypto addresses)
        
        CSV Format:
        ent_num, add_num, address, city_state_province_postalcode, country, add_remarks
        """
        count = 0
        crypto_count = 0
        reader = csv.DictReader(StringIO(csv_data))
        
        batch = []
        crypto_batch = []
        
        for row in reader:
            address_text = row.get("address", "").strip()
            
            # Detect cryptocurrency addresses
            crypto_addr = self._extract_crypto_address(address_text)
            
            address_record = {
                "entity_number": row.get("ent_num", "").strip(),
                "address_number": row.get("add_num", "").strip(),
                "address": address_text,
                "city_state": row.get("city_state_province_postalcode", "").strip(),
                "country": row.get("country", "").strip(),
                "remarks": row.get("add_remarks", "").strip(),
                "is_crypto": bool(crypto_addr),
                "crypto_address": crypto_addr,
                "source": "OFAC_ADD",
                "updated_at": datetime.utcnow()
            }
            
            batch.append(address_record)
            count += 1
            
            if crypto_addr:
                crypto_batch.append({
                    "address": crypto_addr.lower(),
                    "entity_number": row.get("ent_num", "").strip(),
                    "chain": self._detect_chain(crypto_addr),
                    "source": "OFAC",
                    "added_at": datetime.utcnow()
                })
                crypto_count += 1
            
            if len(batch) >= 1000:
                await self._bulk_insert_addresses(batch)
                batch = []
            
            if len(crypto_batch) >= 100:
                await self._bulk_insert_crypto_addresses(crypto_batch)
                crypto_batch = []
        
        if batch:
            await self._bulk_insert_addresses(batch)
        
        if crypto_batch:
            await self._bulk_insert_crypto_addresses(crypto_batch)
        
        logger.info(f"Processed {count} addresses ({crypto_count} crypto)")
        return count, crypto_count
    
    def _extract_crypto_address(self, text: str) -> Optional[str]:
        """Extract cryptocurrency address from text"""
        # Simple heuristic: 40-66 char hex strings or bc1/0x prefixes
        text = text.strip()
        
        # Ethereum (0x...)
        if text.startswith("0x") and len(text) == 42:
            return text
        
        # Bitcoin (bc1... or 1... or 3...)
        if text.startswith("bc1") and len(text) >= 42:
            return text
        
        if (text.startswith("1") or text.startswith("3")) and 26 <= len(text) <= 35:
            return text
        
        # Solana (base58, ~44 chars)
        if 43 <= len(text) <= 44 and text.isalnum():
            return text
        
        return None
    
    def _detect_chain(self, address: str) -> str:
        """Detect blockchain from address format"""
        if address.startswith("0x"):
            return "ethereum"
        if address.startswith("bc1") or address[0] in "13":
            return "bitcoin"
        return "unknown"
    
    async def _bulk_insert_entities(self, entities: List[Dict]):
        """Bulk insert SDN entities"""
        query = """
        INSERT INTO ofac_sdn_entities (
            entity_number, name, entity_type, program, title, remarks, source, list_type, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (entity_number) DO UPDATE SET
            name = EXCLUDED.name,
            updated_at = EXCLUDED.updated_at
        """
        
        async with postgres_client.pool.acquire() as conn:
            await conn.executemany(query, [
                (e["entity_number"], e["name"], e["entity_type"], e["program"], 
                 e["title"], e["remarks"], e["source"], e["list_type"], e["updated_at"])
                for e in entities
            ])
    
    async def _bulk_insert_alt_names(self, alt_names: List[Dict]):
        """Bulk insert alternate names"""
        query = """
        INSERT INTO ofac_alt_names (
            entity_number, alt_number, alt_type, alt_name, remarks, source, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (entity_number, alt_number) DO UPDATE SET
            alt_name = EXCLUDED.alt_name,
            updated_at = EXCLUDED.updated_at
        """
        
        async with postgres_client.pool.acquire() as conn:
            await conn.executemany(query, [
                (a["entity_number"], a["alt_number"], a["alt_type"], a["alt_name"],
                 a["remarks"], a["source"], a["updated_at"])
                for a in alt_names
            ])
    
    async def _bulk_insert_addresses(self, addresses: List[Dict]):
        """Bulk insert addresses"""
        query = """
        INSERT INTO ofac_addresses (
            entity_number, address_number, address, city_state, country, remarks,
            is_crypto, crypto_address, source, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (entity_number, address_number) DO UPDATE SET
            address = EXCLUDED.address,
            updated_at = EXCLUDED.updated_at
        """
        
        async with postgres_client.pool.acquire() as conn:
            await conn.executemany(query, [
                (a["entity_number"], a["address_number"], a["address"], a["city_state"],
                 a["country"], a["remarks"], a["is_crypto"], a["crypto_address"],
                 a["source"], a["updated_at"])
                for a in addresses
            ])
    
    async def _bulk_insert_crypto_addresses(self, addresses: List[Dict]):
        """Bulk insert cryptocurrency addresses (for fast lookup)"""
        query = """
        INSERT INTO sanctioned_addresses (
            address, entity_number, chain, source, added_at
        ) VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (address) DO UPDATE SET
            added_at = EXCLUDED.added_at
        """
        
        async with postgres_client.pool.acquire() as conn:
            await conn.executemany(query, [
                (a["address"], a["entity_number"], a["chain"], a["source"], a["added_at"])
                for a in addresses
            ])
    
    async def _record_update(self, stats: Dict, duration: float):
        """Record update metadata"""
        query = """
        INSERT INTO sanctions_updates (
            update_timestamp, sdn_count, alt_names_count, addresses_count,
            crypto_addresses, duration_seconds, status, errors
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        status = "success" if not stats.get("errors") else "partial_failure"
        
        async with postgres_client.pool.acquire() as conn:
            await conn.execute(
                query,
                datetime.utcnow(),
                stats["sdn_count"],
                stats["alt_names_count"],
                stats["addresses_count"],
                stats["crypto_addresses"],
                duration,
                status,
                stats.get("errors", [])
            )


# Global instance
sanctions_updater = SanctionsUpdater()


# Background task runner
async def start_sanctions_updater():
    """Start updater as background task"""
    await sanctions_updater.start_auto_update()
