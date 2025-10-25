"""Moonbeam Blockchain Adapter - Polkadot EVM Parachain"""
from __future__ import annotations
import logging
from typing import Optional
from app.adapters.ethereum_adapter import EthereumAdapter
from app.services.multi_chain import ChainInfo

logger = logging.getLogger(__name__)


class MoonbeamAdapter(EthereumAdapter):
    """Moonbeam blockchain adapter - Polkadot EVM-compatible parachain"""
    
    def __init__(self, chain_info: Optional[ChainInfo] = None, rpc_url: Optional[str] = None):
        if chain_info is None:
            chain_info = ChainInfo(
                chain_id="moonbeam",
                name="Moonbeam",
                symbol="GLMR",
                chain_type="evm",
                rpc_urls=[rpc_url] if rpc_url else ["https://rpc.api.moonbeam.network"],
                block_explorer_url="https://moonscan.io",
                native_currency={"name": "Glimmer", "symbol": "GLMR", "decimals": 18},
                features=["polkadot_parachain", "cross_chain", "evm"]
            )
        self.chain_info = chain_info
        super().__init__(rpc_url=chain_info.rpc_urls[0] if chain_info.rpc_urls else rpc_url)
    
    async def initialize(self):
        logger.info(f"Initializing Moonbeam adapter for {self.chain_info.name}")
