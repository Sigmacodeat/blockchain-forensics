"""Aptos Blockchain Adapter - Move VM"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
from app.services.multi_chain import ChainInfo, BaseChainAdapter

logger = logging.getLogger(__name__)


class AptosAdapter(BaseChainAdapter):
    """
    Aptos blockchain adapter - Move VM with BFT consensus
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        chain_info = ChainInfo(
            chain_id="aptos",
            name="Aptos",
            symbol="APT",
            chain_type="cosmos",  # Using cosmos as placeholder
            rpc_urls=[rpc_url] if rpc_url else ["https://fullnode.mainnet.aptoslabs.com/v1"],
            block_explorer_url="https://explorer.aptoslabs.com",
            native_currency={"name": "Aptos", "symbol": "APT", "decimals": 8},
            features=["move_vm", "parallel_execution", "block_stm"]
        )
        super().__init__(chain_info)
    
    async def initialize(self):
        logger.info(f"Initializing Aptos adapter for {self.chain_info.name}")
    
    async def get_block_height(self) -> int:
        """Get latest ledger version"""
        response = await self.make_request("")  # GET /
        return int(response.get("ledger_version", 0))
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by hash"""
        response = await self.make_request(f"transactions/by_hash/{tx_hash}")
        if not response:
            return None
        
        return {
            "tx_hash": tx_hash,
            "version": response.get("version"),
            "sender": response.get("sender"),
            "sequence_number": response.get("sequence_number"),
            "gas_used": response.get("gas_used"),
            "success": response.get("success"),
            "timestamp": response.get("timestamp"),
            "chain": self.chain_info.chain_id,
            "chain_type": "move_vm"
        }
    
    async def get_address_balance(self, address: str) -> float:
        """Get account balance"""
        response = await self.make_request(f"accounts/{address}/resource/0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>")
        coin_data = response.get("data", {}).get("coin", {})
        value = int(coin_data.get("value", 0))
        return value / 1e8  # Octas to APT
    
    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions for account"""
        response = await self.make_request(f"accounts/{address}/transactions", {"limit": limit})
        
        txs = []
        for tx in response if isinstance(response, list) else []:
            txs.append({
                "tx_hash": tx.get("hash"),
                "version": tx.get("version"),
                "sender": tx.get("sender"),
                "chain": self.chain_info.chain_id
            })
        return txs
    
    async def get_block_transactions(self, block_height: int) -> List[Dict[str, Any]]:
        """Get transactions by block height"""
        response = await self.make_request(f"blocks/by_height/{block_height}", {"with_transactions": True})
        
        txs = []
        for tx in response.get("transactions", []):
            txs.append({
                "tx_hash": tx.get("hash"),
                "version": tx.get("version"),
                "chain": self.chain_info.chain_id
            })
        return txs
