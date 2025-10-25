"""Fantom (Opera) Blockchain Adapter - EVM-compatible"""
from __future__ import annotations
import logging
from typing import Optional
from app.adapters.ethereum_adapter import EthereumAdapter
from app.services.multi_chain import ChainInfo

logger = logging.getLogger(__name__)


class FantomAdapter(EthereumAdapter):
    """Fantom Opera blockchain adapter - EVM-compatible with DAG consensus"""
    
    def __init__(self, chain_info: Optional[ChainInfo] = None, rpc_url: Optional[str] = None):
        if chain_info is None:
            chain_info = ChainInfo(
                chain_id="fantom",
                name="Fantom Opera",
                symbol="FTM",
                chain_type="evm",
                rpc_urls=[rpc_url] if rpc_url else ["https://rpc.ftm.tools"],
                block_explorer_url="https://ftmscan.com",
                native_currency={"name": "Fantom", "symbol": "FTM", "decimals": 18},
                features=["defi", "fast_finality", "dag"]
            )
        self.chain_info = chain_info
        super().__init__(rpc_url=chain_info.rpc_urls[0] if chain_info.rpc_urls else rpc_url)
    
    async def initialize(self):
        logger.info(f"Initializing Fantom adapter for {self.chain_info.name}")
