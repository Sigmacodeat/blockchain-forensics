"""Sui Blockchain Adapter - Move VM"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
from app.adapters.base import IChainAdapter
from app.services.multi_chain import ChainInfo, BaseChainAdapter

logger = logging.getLogger(__name__)


class SuiAdapter(BaseChainAdapter):
    """
    Sui blockchain adapter - Move VM with object-centric model
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        chain_info = ChainInfo(
            chain_id="sui",
            name="Sui",
            symbol="SUI",
            chain_type="cosmos",  # Using cosmos as placeholder
            rpc_urls=[rpc_url] if rpc_url else ["https://fullnode.mainnet.sui.io"],
            block_explorer_url="https://suiexplorer.com",
            native_currency={"name": "Sui", "symbol": "SUI", "decimals": 9},
            features=["move_vm", "object_centric", "parallel_execution"]
        )
        super().__init__(chain_info)
    
    async def initialize(self):
        logger.info(f"Initializing Sui adapter for {self.chain_info.name}")
    
    async def get_block_height(self) -> int:
        """Get latest checkpoint sequence number"""
        response = await self.make_request("sui_getLatestCheckpointSequenceNumber")
        return int(response.get("result", 0))
    
    async def get_transaction(self, tx_digest: str) -> Optional[Dict[str, Any]]:
        """Get transaction by digest"""
        response = await self.make_request("sui_getTransactionBlock", {
            "digest": tx_digest,
            "options": {"showEffects": True, "showInput": True}
        })
        if not response.get("result"):
            return None
        
        tx = response["result"]
        return {
            "tx_digest": tx_digest,
            "checkpoint": tx.get("checkpoint"),
            "sender": tx.get("transaction", {}).get("data", {}).get("sender"),
            "gas_used": tx.get("effects", {}).get("gasUsed", {}).get("computationCost", 0),
            "status": tx.get("effects", {}).get("status", {}).get("status"),
            "chain": self.chain_info.chain_id,
            "chain_type": "move_vm"
        }
    
    async def get_address_balance(self, address: str) -> float:
        """Get address balance"""
        response = await self.make_request("suix_getBalance", [address])
        total_balance = int(response.get("result", {}).get("totalBalance", 0))
        return total_balance / 1e9  # MIST to SUI
    
    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions for address"""
        response = await self.make_request("suix_queryTransactionBlocks", {
            "filter": {"FromAddress": address},
            "options": {"showEffects": True},
            "limit": limit
        })
        
        txs = []
        for tx in response.get("result", {}).get("data", []):
            txs.append({
                "tx_digest": tx.get("digest"),
                "checkpoint": tx.get("checkpoint"),
                "chain": self.chain_info.chain_id
            })
        return txs
    
    async def get_block_transactions(self, checkpoint: int) -> List[Dict[str, Any]]:
        """Get transactions in a checkpoint"""
        logger.warning(f"Sui checkpoint {checkpoint} transactions - requires pagination")
        return []
