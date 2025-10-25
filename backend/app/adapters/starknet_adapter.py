"""Starknet Blockchain Adapter - Cairo VM ZK-Rollup"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
from app.adapters.base import IChainAdapter
from app.services.multi_chain import ChainInfo, BaseChainAdapter

logger = logging.getLogger(__name__)


class StarknetAdapter(BaseChainAdapter):
    """
    Starknet blockchain adapter - Cairo VM ZK-Rollup on Ethereum
    
    Note: Starknet uses Cairo VM (not EVM), different address format and RPC methods
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        chain_info = ChainInfo(
            chain_id="starknet",
            name="Starknet",
            symbol="ETH",
            chain_type="layer2",
            rpc_urls=[rpc_url] if rpc_url else ["https://starknet-mainnet.public.blastapi.io"],
            block_explorer_url="https://starkscan.co",
            native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
            features=["zk_rollup", "cairo_vm", "validity_proofs"]
        )
        super().__init__(chain_info)
    
    async def initialize(self):
        logger.info(f"Initializing Starknet adapter for {self.chain_info.name}")
    
    async def get_block_height(self) -> int:
        """Get latest block number"""
        response = await self.make_request("starknet_blockNumber")
        return int(response.get("result", 0))
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by hash"""
        response = await self.make_request("starknet_getTransactionByHash", [tx_hash])
        if not response.get("result"):
            return None
        
        tx_data = response["result"]
        return {
            "tx_hash": tx_hash,
            "block_number": tx_data.get("block_number"),
            "from_address": tx_data.get("sender_address"),
            "to_address": tx_data.get("contract_address"),
            "status": tx_data.get("status"),
            "timestamp": None,  # Requires separate block fetch
            "chain": self.chain_info.chain_id,
            "chain_type": "cairo_vm"
        }
    
    async def get_address_balance(self, address: str) -> float:
        """
        Get address balance
        Note: Starknet uses different balance query (contract calls)
        """
        # Simplified - real implementation would call ETH balance contract
        logger.warning(f"Balance query for Starknet address {address} - placeholder implementation")
        return 0.0
    
    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions for address"""
        # Simplified - Starknet requires different API or indexer
        logger.warning(f"Transaction history for Starknet address {address} - requires indexer")
        return []
    
    async def get_block_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """Get transactions in a block"""
        response = await self.make_request("starknet_getBlockWithTxs", [{"block_number": block_number}])
        if not response.get("result"):
            return []
        
        block = response["result"]
        txs = []
        for tx in block.get("transactions", []):
            txs.append({
                "tx_hash": tx.get("transaction_hash"),
                "block_number": block_number,
                "from_address": tx.get("sender_address"),
                "to_address": tx.get("contract_address"),
                "chain": self.chain_info.chain_id,
                "chain_type": "cairo_vm"
            })
        return txs
