"""Aurora Blockchain Adapter - NEAR EVM"""
from __future__ import annotations
import logging
from typing import Optional
from app.adapters.ethereum_adapter import EthereumAdapter
from app.services.multi_chain import ChainInfo

logger = logging.getLogger(__name__)


class AuroraAdapter(EthereumAdapter):
    """Aurora blockchain adapter - NEAR Protocol EVM"""
    
    def __init__(self, chain_info: Optional[ChainInfo] = None, rpc_url: Optional[str] = None):
        if chain_info is None:
            chain_info = ChainInfo(
                chain_id="aurora",
                name="Aurora",
                symbol="ETH",
                chain_type="evm",
                rpc_urls=[rpc_url] if rpc_url else ["https://mainnet.aurora.dev"],
                block_explorer_url="https://aurorascan.dev",
                native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
                features=["near_protocol", "low_fees", "rainbow_bridge"]
            )
        self.chain_info = chain_info
        super().__init__(rpc_url=chain_info.rpc_urls[0] if chain_info.rpc_urls else rpc_url)
    
    async def initialize(self):
        logger.info(f"Initializing Aurora adapter for {self.chain_info.name}")
