"""NEAR Protocol Blockchain Adapter"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
from app.adapters.base import IChainAdapter
from app.services.multi_chain import ChainInfo, BaseChainAdapter

logger = logging.getLogger(__name__)


class NearAdapter(BaseChainAdapter):
    """
    NEAR Protocol blockchain adapter - Sharded PoS L1
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        chain_info = ChainInfo(
            chain_id="near",
            name="NEAR Protocol",
            symbol="NEAR",
            chain_type="cosmos",  # Using cosmos as placeholder for sharded chains
            rpc_urls=[rpc_url] if rpc_url else ["https://rpc.mainnet.near.org"],
            block_explorer_url="https://nearblocks.io",
            native_currency={"name": "NEAR", "symbol": "NEAR", "decimals": 24},
            features=["sharding", "proof_of_stake", "human_readable_addresses"]
        )
        super().__init__(chain_info)
    
    async def initialize(self):
        logger.info(f"Initializing NEAR adapter for {self.chain_info.name}")
    
    async def get_block_height(self) -> int:
        """Get latest block height"""
        response = await self.make_request("block", {"finality": "final"})
        return int(response.get("result", {}).get("header", {}).get("height", 0))
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by hash"""
        # NEAR uses account_id for transaction queries
        logger.warning(f"NEAR transaction {tx_hash} - requires account_id for query")
        return None
    
    async def get_address_balance(self, address: str) -> float:
        """Get account balance"""
        response = await self.make_request("query", {
            "request_type": "view_account",
            "finality": "final",
            "account_id": address
        })
        amount_yocto = int(response.get("result", {}).get("amount", 0))
        return amount_yocto / 1e24  # yoctoNEAR to NEAR
    
    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions for account"""
        logger.warning(f"NEAR transaction history for {address} - requires indexer")
        return []
    
    async def get_block_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """Get transactions in a block"""
        response = await self.make_request("block", {"block_id": block_number})
        block = response.get("result", {})
        
        txs = []
        for chunk in block.get("chunks", []):
            # Simplified - full implementation requires chunk queries
            txs.append({
                "block_number": block_number,
                "chunk_hash": chunk.get("chunk_hash"),
                "chain": self.chain_info.chain_id
            })
        return txs
