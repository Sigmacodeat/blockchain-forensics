"""Base Chain Adapter Interface"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from app.schemas import CanonicalEvent


class IChainAdapter(ABC):
    """
    Interface for blockchain adapters.
    Each chain implements this to transform raw data → Canonical Events.
    """
    
    @property
    @abstractmethod
    def chain_name(self) -> str:
        """Chain identifier (eth, btc, sol, etc.)"""
        pass
    
    @abstractmethod
    async def get_block(self, block_number: int) -> dict:
        """Fetch raw block data"""
        pass
    
    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> dict:
        """Fetch raw transaction data"""
        pass
    
    @abstractmethod
    async def transform_transaction(self, raw_tx: dict, block_data: dict) -> CanonicalEvent:
        """Transform raw transaction → Canonical Event"""
        pass
    
    @abstractmethod
    def stream_blocks(
        self,
        start_block: int,
        end_block: Optional[int] = None
    ) -> AsyncGenerator[CanonicalEvent, None]:
        """Stream transactions from blocks as Canonical Events"""
        pass
    
    @abstractmethod
    async def get_latest_block_number(self) -> int:
        """Get latest block number"""
        pass
    
    @abstractmethod
    async def is_contract(self, address: str) -> bool:
        """Check if address is a contract"""
        pass
