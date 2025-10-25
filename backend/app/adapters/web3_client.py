"""
Web3 Client for Ethereum RPC Interactions
Fetches real blockchain data
"""

import logging
from typing import Optional, Dict, List
from web3 import Web3
from web3.exceptions import Web3Exception
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class Web3Client:
    """Web3 client for Ethereum blockchain interaction"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_RPC_URL))
        self.is_connected = self.w3.is_connected()
        
        if self.is_connected:
            logger.info(f"✅ Web3 connected to Ethereum (Chain ID: {self.w3.eth.chain_id})")
        else:
            logger.warning("⚠️  Web3 not connected - using mock data")
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction details
        
        Args:
            tx_hash: Transaction hash
        
        Returns:
            Transaction dict or None
        """
        if not self.is_connected:
            return None
        
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            block = self.w3.eth.get_block(tx['blockNumber'])
            
            return {
                'tx_hash': tx_hash,
                'block_number': tx['blockNumber'],
                'timestamp': datetime.fromtimestamp(block['timestamp']),
                'from_address': tx['from'],
                'to_address': tx.get('to'),
                'value': str(tx['value']),
                'gas_used': receipt['gasUsed'],
                'gas_price': str(tx['gasPrice']),
                'status': receipt['status'],
                'input_data': tx.get('input', '0x')
            }
        except Web3Exception as e:
            logger.error(f"Error fetching transaction {tx_hash}: {e}")
            return None
    
    async def get_address_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get transactions for an address
        
        **Note:** This is a simplified version.
        For production, use Etherscan API or indexing service.
        
        Args:
            address: Ethereum address
            start_block: Start block number
            end_block: End block number (default: latest)
            limit: Max results
        
        Returns:
            List of transactions
        """
        if not self.is_connected:
            logger.warning("Web3 not connected - returning empty list")
            return []
        
        if end_block is None:
            end_block = self.w3.eth.block_number
        
        transactions = []
        
        # This is inefficient! In production:
        # - Use Etherscan API
        # - Use The Graph
        # - Use own indexer
        logger.warning(
            f"Scanning blocks {start_block}-{end_block} for {address}. "
            "This is slow! Use indexing service in production."
        )
        
        try:
            for block_num in range(start_block, min(end_block + 1, start_block + 1000)):
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block['transactions']:
                    if (tx['from'].lower() == address.lower() or 
                        (tx.get('to') and tx['to'].lower() == address.lower())):
                        
                        transactions.append({
                            'tx_hash': tx['hash'].hex(),
                            'block_number': block_num,
                            'timestamp': datetime.fromtimestamp(block['timestamp']),
                            'from_address': tx['from'],
                            'to_address': tx.get('to'),
                            'value': str(tx['value']),
                            'gas_price': str(tx['gasPrice']),
                        })
                        
                        if len(transactions) >= limit:
                            return transactions
            
            return transactions
            
        except Web3Exception as e:
            logger.error(f"Error scanning blocks: {e}")
            return []
    
    async def get_balance(self, address: str) -> int:
        """
        Get ETH balance for address
        
        Args:
            address: Ethereum address
        
        Returns:
            Balance in Wei
        """
        if not self.is_connected:
            return 0
        
        try:
            balance = self.w3.eth.get_balance(address)
            return balance
        except Web3Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0
    
    async def get_code(self, address: str) -> str:
        """
        Get contract code (if address is contract)
        
        Args:
            address: Ethereum address
        
        Returns:
            Contract bytecode or '0x' if EOA
        """
        if not self.is_connected:
            return '0x'
        
        try:
            code = self.w3.eth.get_code(address)
            return code.hex()
        except Web3Exception as e:
            logger.error(f"Error fetching code: {e}")
            return '0x'
    
    def is_contract(self, address: str) -> bool:
        """
        Check if address is a smart contract
        
        Args:
            address: Ethereum address
        
        Returns:
            True if contract, False if EOA
        """
        if not self.is_connected:
            return False
        
        try:
            code = self.w3.eth.get_code(address)
            return len(code) > 0
        except Web3Exception:
            return False


# Singleton instance
web3_client = Web3Client()
