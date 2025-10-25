"""
Blockchain Data Ingestion Service
Fetches real blockchain data and stores in TimescaleDB
"""

import logging
import asyncio

from app.adapters.web3_client import web3_client
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class BlockchainIngester:
    """
    Ingests blockchain data into TimescaleDB
    
    **Usage:**
    ```python
    ingester = BlockchainIngester()
    await ingester.ingest_address_transactions('0x123...')
    ```
    """
    
    def __init__(self):
        self.w3_client = web3_client
        self.db_client = postgres_client
    
    async def ingest_transaction(self, tx_hash: str) -> bool:
        """
        Ingest single transaction
        
        Args:
            tx_hash: Transaction hash
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch from blockchain
            tx = await self.w3_client.get_transaction(tx_hash)
            
            if not tx:
                logger.warning(f"Transaction {tx_hash} not found")
                return False
            
            # Store in TimescaleDB
            async with self.db_client.get_session() as session:
                from sqlalchemy import text
                
                query = text("""
                    INSERT INTO transactions (
                        tx_hash, block_number, timestamp,
                        from_address, to_address, value,
                        gas_used, gas_price, chain, status
                    ) VALUES (
                        :tx_hash, :block_number, :timestamp,
                        :from_address, :to_address, :value,
                        :gas_used, :gas_price, :chain, :status
                    )
                    ON CONFLICT (tx_hash) DO UPDATE SET
                        block_number = EXCLUDED.block_number
                """)
                
                await session.execute(query, {
                    'tx_hash': tx['tx_hash'],
                    'block_number': tx['block_number'],
                    'timestamp': tx['timestamp'],
                    'from_address': tx['from_address'].lower(),
                    'to_address': tx['to_address'].lower() if tx['to_address'] else None,
                    'value': tx['value'],
                    'gas_used': tx['gas_used'],
                    'gas_price': tx['gas_price'],
                    'chain': 'ethereum',
                    'status': tx['status']
                })
            
            logger.info(f"✅ Ingested transaction {tx_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting transaction {tx_hash}: {e}", exc_info=True)
            return False
    
    async def ingest_address_transactions(
        self,
        address: str,
        start_block: int = 0,
        limit: int = 100
    ) -> int:
        """
        Ingest all transactions for an address
        
        **Warning:** This can be slow for addresses with many transactions!
        Use Etherscan API or indexing service for production.
        
        Args:
            address: Ethereum address
            start_block: Start block
            limit: Max transactions to fetch
        
        Returns:
            Number of transactions ingested
        """
        try:
            logger.info(f"Ingesting transactions for {address}...")
            
            # Fetch from blockchain
            transactions = await self.w3_client.get_address_transactions(
                address=address,
                start_block=start_block,
                limit=limit
            )
            
            if not transactions:
                logger.warning(f"No transactions found for {address}")
                return 0
            
            # Store in database
            ingested = 0
            for tx in transactions:
                success = await self.ingest_transaction(tx['tx_hash'])
                if success:
                    ingested += 1
            
            logger.info(f"✅ Ingested {ingested}/{len(transactions)} transactions for {address}")
            return ingested
            
        except Exception as e:
            logger.error(f"Error ingesting address transactions: {e}", exc_info=True)
            return 0
    
    async def ingest_block(self, block_number: int) -> int:
        """
        Ingest all transactions from a block
        
        Args:
            block_number: Block number
        
        Returns:
            Number of transactions ingested
        """
        try:
            if not self.w3_client.is_connected:
                logger.warning("Web3 not connected")
                return 0
            
            logger.info(f"Ingesting block {block_number}...")
            
            # Fetch block
            block = self.w3_client.w3.eth.get_block(block_number, full_transactions=True)
            
            # Ingest each transaction
            ingested = 0
            for tx in block['transactions']:
                success = await self.ingest_transaction(tx['hash'].hex())
                if success:
                    ingested += 1
                    
                # Rate limiting
                await asyncio.sleep(0.1)
            
            logger.info(f"✅ Ingested {ingested} transactions from block {block_number}")
            return ingested
            
        except Exception as e:
            logger.error(f"Error ingesting block {block_number}: {e}", exc_info=True)
            return 0


# Singleton instance
blockchain_ingester = BlockchainIngester()
