"""
Custom Ledgers Service
=======================

TRM Labs Mai 2025 Feature: Custom Ledgers
- Subpoena Returns visualisieren
- Bulk Transfer Data (CSV Upload)  
- Large Dataset Handling (Millionen von Transfers)
- Interactive Ledger Node im Graph
"""

import logging
import csv
import io
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class LedgerType(str, Enum):
    """Ledger Type"""
    SUBPOENA_RETURN = "subpoena_return"
    EXCHANGE_EXPORT = "exchange_export"
    BULK_TRANSFER = "bulk_transfer"
    INVESTIGATION_DATA = "investigation_data"
    CUSTOM = "custom"


class TransferDirection(str, Enum):
    """Transfer Direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


@dataclass
class LedgerTransfer:
    """Einzelner Transfer im Ledger"""
    transfer_id: str
    timestamp: datetime
    from_address: str
    to_address: str
    amount: float
    currency: str
    chain_id: str
    direction: TransferDirection
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "timestamp": self.timestamp.isoformat(),
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "currency": self.currency,
            "chain_id": self.chain_id,
            "direction": self.direction.value,
            "metadata": self.metadata,
            "notes": self.notes,
        }


@dataclass
class CustomLedger:
    """Custom Ledger mit vielen Transfers"""
    ledger_id: str
    name: str
    ledger_type: LedgerType
    description: Optional[str]
    transfers: List[LedgerTransfer]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Stats
    total_transfers: int = 0
    total_inbound: float = 0.0
    total_outbound: float = 0.0
    unique_addresses: int = 0
    chains_involved: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.total_transfers = len(self.transfers)
        self._compute_stats()
    
    def _compute_stats(self):
        """Berechne Stats"""
        if not self.transfers:
            return
        
        # Compute totals
        for transfer in self.transfers:
            if transfer.direction == TransferDirection.INBOUND:
                self.total_inbound += transfer.amount
            elif transfer.direction == TransferDirection.OUTBOUND:
                self.total_outbound += transfer.amount
        
        # Unique addresses
        addresses = set()
        chains = set()
        for transfer in self.transfers:
            addresses.add(transfer.from_address)
            addresses.add(transfer.to_address)
            chains.add(transfer.chain_id)
        
        self.unique_addresses = len(addresses)
        self.chains_involved = list(chains)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "name": self.name,
            "ledger_type": self.ledger_type.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "stats": {
                "total_transfers": self.total_transfers,
                "total_inbound": self.total_inbound,
                "total_outbound": self.total_outbound,
                "unique_addresses": self.unique_addresses,
                "chains_involved": self.chains_involved,
            },
            "transfers_preview": [t.to_dict() for t in self.transfers[:10]],  # Erste 10
        }


class CustomLedgersService:
    """Custom Ledgers Management Service"""
    
    # Limits (TRM Labs: Millionen von Transfers)
    MAX_TRANSFERS_PER_LEDGER = 10_000_000  # 10M
    MAX_CSV_FILE_SIZE_MB = 500  # 500MB
    
    def __init__(self):
        # In-Memory Store (in Production: PostgreSQL + TimescaleDB)
        self._ledgers: Dict[str, CustomLedger] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialisiere Service"""
        if self._initialized:
            return
        
        logger.info("Initializing Custom Ledgers Service")
        self._initialized = True
    
    async def create_ledger(
        self,
        name: str,
        ledger_type: LedgerType,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CustomLedger:
        """
        Erstelle neuen Custom Ledger.
        """
        await self.initialize()
        
        ledger_id = self._generate_ledger_id(name)
        
        ledger = CustomLedger(
            ledger_id=ledger_id,
            name=name,
            ledger_type=ledger_type,
            description=description,
            transfers=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        
        self._ledgers[ledger_id] = ledger
        
        logger.info(f"Created custom ledger: {ledger_id}")
        
        return ledger
    
    async def upload_csv(
        self,
        ledger_id: str,
        csv_content: str,
        mapping: Optional[Dict[str, str]] = None,
    ) -> CustomLedger:
        """
        Upload CSV mit Bulk Transfer Data.
        
        Args:
            ledger_id: Ledger ID
            csv_content: CSV content als String
            mapping: Column mapping {csv_column: ledger_field}
                Default: {
                    "timestamp": "timestamp",
                    "from": "from_address",
                    "to": "to_address",
                    "amount": "amount",
                    "currency": "currency",
                    "chain": "chain_id",
                }
        """
        await self.initialize()
        
        ledger = self._ledgers.get(ledger_id)
        if not ledger:
            raise ValueError(f"Ledger {ledger_id} not found")
        
        # Default Mapping
        if mapping is None:
            mapping = {
                "timestamp": "timestamp",
                "from": "from_address",
                "to": "to_address",
                "amount": "amount",
                "currency": "currency",
                "chain": "chain_id",
                "direction": "direction",
            }
        
        # Parse CSV
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        transfers = []
        for i, row in enumerate(reader):
            try:
                # Map columns
                timestamp_str = row.get(mapping.get("timestamp", "timestamp"), "")
                from_addr = row.get(mapping.get("from", "from"), "")
                to_addr = row.get(mapping.get("to", "to"), "")
                amount_str = row.get(mapping.get("amount", "amount"), "0")
                currency = row.get(mapping.get("currency", "currency"), "USD")
                chain_id = row.get(mapping.get("chain", "chain"), "ethereum")
                direction_str = row.get(mapping.get("direction", "direction"), "outbound")
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()
                
                # Parse amount
                try:
                    amount = float(amount_str.replace(",", ""))
                except:
                    amount = 0.0
                
                # Parse direction
                try:
                    direction = TransferDirection(direction_str.lower())
                except:
                    direction = TransferDirection.OUTBOUND
                
                # Create transfer
                transfer = LedgerTransfer(
                    transfer_id=f"{ledger_id}_{i}",
                    timestamp=timestamp,
                    from_address=from_addr,
                    to_address=to_addr,
                    amount=amount,
                    currency=currency,
                    chain_id=chain_id,
                    direction=direction,
                    metadata={"csv_row": i + 1},
                )
                
                transfers.append(transfer)
                
                # Check limit
                if len(transfers) >= self.MAX_TRANSFERS_PER_LEDGER:
                    logger.warning(f"Reached max transfers limit: {self.MAX_TRANSFERS_PER_LEDGER}")
                    break
                
            except Exception as e:
                logger.warning(f"Failed to parse CSV row {i}: {e}")
                continue
        
        # Add transfers to ledger
        ledger.transfers.extend(transfers)
        ledger.total_transfers = len(ledger.transfers)
        ledger._compute_stats()
        ledger.updated_at = datetime.utcnow()
        
        logger.info(f"Uploaded {len(transfers)} transfers to ledger {ledger_id}")
        
        return ledger
    
    async def add_transfer(
        self,
        ledger_id: str,
        transfer: Dict[str, Any],
    ) -> CustomLedger:
        """Füge einzelnen Transfer hinzu"""
        await self.initialize()
        
        ledger = self._ledgers.get(ledger_id)
        if not ledger:
            raise ValueError(f"Ledger {ledger_id} not found")
        
        # Create LedgerTransfer
        ledger_transfer = LedgerTransfer(
            transfer_id=transfer.get("transfer_id", f"{ledger_id}_{len(ledger.transfers)}"),
            timestamp=datetime.fromisoformat(transfer["timestamp"]) if isinstance(transfer.get("timestamp"), str) else transfer.get("timestamp", datetime.utcnow()),
            from_address=transfer["from_address"],
            to_address=transfer["to_address"],
            amount=float(transfer["amount"]),
            currency=transfer.get("currency", "USD"),
            chain_id=transfer.get("chain_id", "ethereum"),
            direction=TransferDirection(transfer.get("direction", "outbound")),
            metadata=transfer.get("metadata", {}),
            notes=transfer.get("notes"),
        )
        
        ledger.transfers.append(ledger_transfer)
        ledger.total_transfers = len(ledger.transfers)
        ledger._compute_stats()
        ledger.updated_at = datetime.utcnow()
        
        return ledger
    
    async def get_ledger(self, ledger_id: str) -> Optional[CustomLedger]:
        """Hole Ledger"""
        await self.initialize()
        return self._ledgers.get(ledger_id)
    
    async def list_ledgers(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CustomLedger]:
        """Liste Ledgers"""
        await self.initialize()
        
        all_ledgers = list(self._ledgers.values())
        return all_ledgers[offset:offset + limit]
    
    async def get_transfers(
        self,
        ledger_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[LedgerTransfer]:
        """
        Hole Transfers aus Ledger mit Filtering.
        
        Filters:
            - min_amount: float
            - max_amount: float
            - chain_id: str
            - direction: TransferDirection
            - from_date: datetime
            - to_date: datetime
        """
        await self.initialize()
        
        ledger = self._ledgers.get(ledger_id)
        if not ledger:
            raise ValueError(f"Ledger {ledger_id} not found")
        
        transfers = ledger.transfers
        
        # Apply filters
        if filters:
            if "min_amount" in filters:
                transfers = [t for t in transfers if t.amount >= filters["min_amount"]]
            
            if "max_amount" in filters:
                transfers = [t for t in transfers if t.amount <= filters["max_amount"]]
            
            if "chain_id" in filters:
                transfers = [t for t in transfers if t.chain_id == filters["chain_id"]]
            
            if "direction" in filters:
                transfers = [t for t in transfers if t.direction == filters["direction"]]
            
            if "from_date" in filters:
                from_date = filters["from_date"]
                if isinstance(from_date, str):
                    from_date = datetime.fromisoformat(from_date)
                transfers = [t for t in transfers if t.timestamp >= from_date]
            
            if "to_date" in filters:
                to_date = filters["to_date"]
                if isinstance(to_date, str):
                    to_date = datetime.fromisoformat(to_date)
                transfers = [t for t in transfers if t.timestamp <= to_date]
        
        # Pagination
        return transfers[offset:offset + limit]
    
    async def analyze_ledger(
        self,
        ledger_id: str,
    ) -> Dict[str, Any]:
        """
        Analysiere Ledger und generiere Insights.
        
        Returns:
            - Top Counterparties
            - Transaction Volume by Chain
            - Transfer Patterns
            - Risk Indicators
        """
        await self.initialize()
        
        ledger = self._ledgers.get(ledger_id)
        if not ledger:
            raise ValueError(f"Ledger {ledger_id} not found")
        
        # Top Counterparties
        counterparty_volumes: Dict[str, float] = {}
        for transfer in ledger.transfers:
            addr = transfer.to_address if transfer.direction == TransferDirection.OUTBOUND else transfer.from_address
            counterparty_volumes[addr] = counterparty_volumes.get(addr, 0.0) + transfer.amount
        
        top_counterparties = sorted(
            counterparty_volumes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        # Volume by Chain
        chain_volumes: Dict[str, float] = {}
        for transfer in ledger.transfers:
            chain_volumes[transfer.chain_id] = chain_volumes.get(transfer.chain_id, 0.0) + transfer.amount
        
        # Transfer Patterns (hourly)
        hourly_pattern: Dict[int, int] = {}
        for transfer in ledger.transfers:
            hour = transfer.timestamp.hour
            hourly_pattern[hour] = hourly_pattern.get(hour, 0) + 1
        
        return {
            "ledger_id": ledger_id,
            "summary": {
                "total_transfers": ledger.total_transfers,
                "total_inbound": ledger.total_inbound,
                "total_outbound": ledger.total_outbound,
                "net_flow": ledger.total_inbound - ledger.total_outbound,
                "unique_addresses": ledger.unique_addresses,
            },
            "top_counterparties": [
                {"address": addr, "volume": vol}
                for addr, vol in top_counterparties
            ],
            "chain_breakdown": [
                {"chain_id": chain, "volume": vol}
                for chain, vol in sorted(chain_volumes.items(), key=lambda x: x[1], reverse=True)
            ],
            "hourly_pattern": hourly_pattern,
        }
    
    async def delete_ledger(self, ledger_id: str) -> bool:
        """Lösche Ledger"""
        await self.initialize()
        
        if ledger_id in self._ledgers:
            del self._ledgers[ledger_id]
            logger.info(f"Deleted ledger {ledger_id}")
            return True
        return False
    
    def _generate_ledger_id(self, name: str) -> str:
        """Generiere eindeutige Ledger ID"""
        data = f"{name}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Global Service Instance
custom_ledgers_service = CustomLedgersService()
