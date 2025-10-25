"""Cardano Blockchain Adapter - Extended UTXO Model"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
from app.services.multi_chain import ChainInfo, BaseChainAdapter

logger = logging.getLogger(__name__)


class CardanoAdapter(BaseChainAdapter):
    """
    Cardano blockchain adapter - Extended UTXO (eUTXO) model
    
    Note: Cardano uses Ouroboros PoS and eUTXO, different from Bitcoin/Ethereum
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        chain_info = ChainInfo(
            chain_id="cardano",
            name="Cardano",
            symbol="ADA",
            chain_type="utxo",
            rpc_urls=[rpc_url] if rpc_url else ["https://cardano-mainnet.blockfrost.io/api/v0"],
            block_explorer_url="https://cardanoscan.io",
            native_currency={"name": "Cardano", "symbol": "ADA", "decimals": 6},
            features=["proof_of_stake", "eutxo", "smart_contracts", "native_assets"]
        )
        super().__init__(chain_info)
        # Blockfrost requires API key in production
        self.api_key = None  # Would be set from env
    
    async def initialize(self):
        logger.info(f"Initializing Cardano adapter for {self.chain_info.name}")
    
    async def get_block_height(self) -> int:
        """Get latest block number"""
        # Blockfrost API: GET /blocks/latest
        response = await self.make_request("blocks/latest")
        return int(response.get("height", 0))
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by hash"""
        # Blockfrost API: GET /txs/{hash}
        response = await self.make_request(f"txs/{tx_hash}")
        if not response:
            return None
        
        return {
            "tx_hash": tx_hash,
            "block_height": response.get("block_height"),
            "block_hash": response.get("block"),
            "slot": response.get("slot"),
            "index": response.get("index"),
            "output_amount": sum(int(out.get("amount", [{}])[0].get("quantity", 0)) for out in response.get("outputs", [])),
            "fees": int(response.get("fees", 0)),
            "timestamp": None,  # Requires epoch conversion
            "chain": self.chain_info.chain_id,
            "chain_type": "utxo"
        }
    
    async def get_address_balance(self, address: str) -> float:
        """Get address balance in ADA"""
        # Blockfrost API: GET /addresses/{address}
        response = await self.make_request(f"addresses/{address}")
        total_lovelace = sum(int(amt.get("quantity", 0)) for amt in response.get("amount", []) if amt.get("unit") == "lovelace")
        return total_lovelace / 1_000_000  # Lovelace to ADA
    
    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions for address"""
        # Blockfrost API: GET /addresses/{address}/transactions
        logger.warning(f"Cardano transaction history for {address} - requires Blockfrost API key")
        return []
    
    async def get_block_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """Get transactions in a block"""
        # Blockfrost API: GET /blocks/{hash_or_number}/txs
        logger.warning(f"Cardano block {block_number} transactions - requires Blockfrost API key")
        return []
