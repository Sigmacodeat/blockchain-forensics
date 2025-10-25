"""
OFAC Sanctions List Auto-Updater

Lädt täglich die OFAC SDN (Specially Designated Nationals) Liste
und aktualisiert die lokale Datenbank.

Features:
- Daily auto-update via scheduler
- CSV parsing von OFAC data
- Blockchain address extraction
- Database persistence
- Change detection und Notifications
"""
import asyncio
import logging
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from io import StringIO

from app.db.postgres_client import postgres_client
from app.config import settings

logger = logging.getLogger(__name__)


class OFACUpdater:
    """OFAC Sanctions List Updater"""
    
    # OFAC SDN List URLs (official U.S. Treasury)
    SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    SDN_ADVANCED_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn_advanced.csv"
    CRYPTO_ADDRESSES_URL = "https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml"
    
    # Alternative: Chainalysis free API (if available)
    CHAINALYSIS_FREE_URL = "https://public.chainalysis.com/api/v1/sanctions"
    
    def __init__(self):
        self.last_update: Optional[datetime] = None
        self.total_addresses: int = 0
    
    async def auto_update_loop(self, interval_hours: int = 24):
        """
        Main loop für automatische Updates
        
        Args:
            interval_hours: Update interval in hours
        """
        logger.info(f"Starting OFAC auto-updater (interval: {interval_hours}h)")
        
        while True:
            try:
                # Perform update
                await self.update_sanctions_list()
                
                # Wait for next update
                logger.info(f"Next update in {interval_hours} hours")
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error in auto-update loop: {e}")
                # Wait 1 hour on error before retry
                await asyncio.sleep(3600)
    
    async def update_sanctions_list(self) -> Dict[str, Any]:
        """
        Updates OFAC sanctions list
        
        Returns:
            Update statistics
        """
        logger.info("Starting OFAC sanctions list update...")
        start_time = datetime.utcnow()
        
        stats = {
            "started_at": start_time.isoformat(),
            "addresses_added": 0,
            "addresses_updated": 0,
            "addresses_removed": 0,
            "errors": []
        }
        
        try:
            # 1. Fetch SDN list
            sdn_data = await self._fetch_sdn_list()
            
            if not sdn_data:
                logger.warning("No SDN data fetched")
                return stats
            
            # 2. Extract crypto addresses
            crypto_addresses = await self._extract_crypto_addresses(sdn_data)
            logger.info(f"Extracted {len(crypto_addresses)} crypto addresses from SDN list")
            
            # 3. Try Chainalysis free API for additional addresses
            try:
                chainalysis_addresses = await self._fetch_chainalysis_sanctions()
                crypto_addresses.extend(chainalysis_addresses)
                logger.info(f"Added {len(chainalysis_addresses)} addresses from Chainalysis")
            except Exception as e:
                logger.warning(f"Chainalysis fetch failed (non-critical): {e}")
            
            # Remove duplicates
            unique_addresses = {addr["address"].lower(): addr for addr in crypto_addresses}
            crypto_addresses = list(unique_addresses.values())
            
            # 4. Update database
            stats = await self._update_database(crypto_addresses)
            
            # 5. Update metadata
            self.last_update = datetime.utcnow()
            self.total_addresses = len(crypto_addresses)
            
            stats["completed_at"] = datetime.utcnow().isoformat()
            stats["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            stats["total_addresses"] = self.total_addresses
            
            logger.info(f"OFAC update completed: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error updating OFAC list: {e}", exc_info=True)
            stats["errors"].append(str(e))
            return stats
    
    async def _fetch_sdn_list(self) -> List[Dict[str, Any]]:
        """Fetches SDN list from Treasury"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.SDN_CSV_URL, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch SDN list: HTTP {response.status}")
                        return []
                    
                    content = await response.text()
                    
                    # Parse CSV
                    reader = csv.DictReader(StringIO(content))
                    sdn_data = [row for row in reader]
                    
                    logger.info(f"Fetched {len(sdn_data)} SDN entries")
                    return sdn_data
                    
        except Exception as e:
            logger.error(f"Error fetching SDN list: {e}")
            return []
    
    async def _extract_crypto_addresses(self, sdn_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts cryptocurrency addresses from SDN data
        
        Args:
            sdn_data: Raw SDN data
            
        Returns:
            List of crypto addresses with metadata
        """
        addresses = []
        
        # Common patterns for crypto addresses in SDN remarks
        # Ethereum: 0x followed by 40 hex chars
        # Bitcoin: various formats (not implemented yet)
        
        import re
        eth_pattern = re.compile(r'\b0x[a-fA-F0-9]{40}\b')
        
        for entry in sdn_data:
            # Check remarks field for addresses
            remarks = entry.get('remarks', '') or entry.get('Remarks', '')
            
            # Extract Ethereum addresses
            eth_matches = eth_pattern.findall(remarks)
            
            for addr in eth_matches:
                addresses.append({
                    "address": addr.lower(),
                    "chain": "ethereum",
                    "entity_name": entry.get('name', '') or entry.get('NAME', ''),
                    "entity_type": entry.get('type', '') or entry.get('TYPE', ''),
                    "programs": entry.get('programs', '') or entry.get('PROGRAMS', ''),
                    "remarks": remarks[:500],  # Limit length
                    "source": "OFAC_SDN",
                    "list_date": datetime.utcnow().isoformat()
                })
        
        return addresses
    
    async def _fetch_chainalysis_sanctions(self) -> List[Dict[str, Any]]:
        """
        Fetches sanctions from Chainalysis free API (if available)
        
        Returns:
            List of sanctioned addresses
        """
        addresses = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Note: This is a placeholder - actual Chainalysis API may require auth
                # For free/public sanctions, check their documentation
                async with session.get(self.CHAINALYSIS_FREE_URL, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse Chainalysis format (example structure)
                        for entry in data.get('identifications', []):
                            addresses.append({
                                "address": entry['address'].lower(),
                                "chain": entry.get('network', 'ethereum'),
                                "entity_name": entry.get('name', 'Unknown'),
                                "entity_type": entry.get('category', 'sanctions'),
                                "programs": "Chainalysis",
                                "remarks": entry.get('description', ''),
                                "source": "Chainalysis",
                                "list_date": datetime.utcnow().isoformat()
                            })
                        
                        logger.info(f"Fetched {len(addresses)} from Chainalysis")
                    
        except Exception as e:
            logger.warning(f"Chainalysis fetch failed: {e}")
            # Non-critical - return empty list
        
        return addresses
    
    async def _update_database(self, addresses: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Updates database with new sanctions data
        
        Args:
            addresses: List of sanctioned addresses
            
        Returns:
            Statistics (added, updated, removed)
        """
        stats = {
            "addresses_added": 0,
            "addresses_updated": 0,
            "addresses_removed": 0
        }
        
        try:
            # Create table if not exists
            await postgres_client.execute("""
                CREATE TABLE IF NOT EXISTS ofac_sanctions (
                    id SERIAL PRIMARY KEY,
                    address VARCHAR(255) NOT NULL,
                    chain VARCHAR(50) NOT NULL,
                    entity_name TEXT,
                    entity_type VARCHAR(100),
                    programs TEXT,
                    remarks TEXT,
                    source VARCHAR(100),
                    list_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(address, chain)
                )
            """)
            
            # Create index
            await postgres_client.execute("""
                CREATE INDEX IF NOT EXISTS idx_ofac_address ON ofac_sanctions(address)
            """)
            
            # Get existing addresses
            existing = await postgres_client.fetch("""
                SELECT address, chain FROM ofac_sanctions
            """)
            
            existing_set = {(row['address'].lower(), row['chain']) for row in existing}
            new_set = {(addr['address'].lower(), addr['chain']) for addr in addresses}
            
            # Determine changes
            to_add = new_set - existing_set
            to_update = new_set & existing_set
            to_remove = existing_set - new_set
            
            # Add new addresses
            for addr_data in addresses:
                key = (addr_data['address'].lower(), addr_data['chain'])
                
                if key in to_add:
                    await postgres_client.execute("""
                        INSERT INTO ofac_sanctions 
                        (address, chain, entity_name, entity_type, programs, remarks, source, list_date)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, 
                        addr_data['address'],
                        addr_data['chain'],
                        addr_data['entity_name'],
                        addr_data['entity_type'],
                        addr_data['programs'],
                        addr_data['remarks'],
                        addr_data['source'],
                        addr_data['list_date']
                    )
                    stats["addresses_added"] += 1
                
                elif key in to_update:
                    await postgres_client.execute("""
                        UPDATE ofac_sanctions 
                        SET entity_name = $3,
                            entity_type = $4,
                            programs = $5,
                            remarks = $6,
                            source = $7,
                            list_date = $8,
                            updated_at = NOW()
                        WHERE address = $1 AND chain = $2
                    """,
                        addr_data['address'],
                        addr_data['chain'],
                        addr_data['entity_name'],
                        addr_data['entity_type'],
                        addr_data['programs'],
                        addr_data['remarks'],
                        addr_data['source'],
                        addr_data['list_date']
                    )
                    stats["addresses_updated"] += 1
            
            # Remove delisted addresses (mark as inactive instead of delete for audit)
            for address, chain in to_remove:
                await postgres_client.execute("""
                    UPDATE ofac_sanctions 
                    SET updated_at = NOW(),
                        remarks = CONCAT(remarks, ' [DELISTED]')
                    WHERE address = $1 AND chain = $2
                """, address, chain)
                stats["addresses_removed"] += 1
            
            logger.info(f"Database update: {stats}")
            
        except Exception as e:
            logger.error(f"Database update error: {e}")
            raise
        
        return stats
    
    async def check_address(self, address: str, chain: str = "ethereum") -> Optional[Dict[str, Any]]:
        """
        Checks if an address is sanctioned
        
        Args:
            address: Address to check
            chain: Blockchain name
            
        Returns:
            Sanctions data if found, None otherwise
        """
        try:
            result = await postgres_client.fetch_one("""
                SELECT * FROM ofac_sanctions
                WHERE address = $1 AND chain = $2
                LIMIT 1
            """, address.lower(), chain)
            
            if result:
                return dict(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking address: {e}")
            return None


# Singleton instance
ofac_updater = OFACUpdater()


async def start_ofac_updater_background():
    """Start OFAC updater as background task"""
    # Run initial update
    await ofac_updater.update_sanctions_list()
    
    # Start auto-update loop
    interval = getattr(settings, "OFAC_UPDATE_INTERVAL_HOURS", 24)
    asyncio.create_task(ofac_updater.auto_update_loop(interval_hours=interval))
    
    logger.info("OFAC updater background task started")
