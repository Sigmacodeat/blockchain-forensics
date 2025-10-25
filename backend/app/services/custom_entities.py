"""
Custom Entities Service
========================

TRM Labs-Style Custom Entity Management:
- Gruppiere bis zu 1M Adressen in Custom Entities
- Unterstütze 100M+ Transaktionen pro Entity
- Merge TRM-Named-Entities mit Custom Addresses
- Aggregate Insights (Counterparties, Transfers, Risk)
- Custom Labels & Metadata
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


# Expose multi_chain_engine at module scope for test patching
try:
    from app.services.multi_chain import multi_chain_engine as multi_chain_engine  # type: ignore
except Exception:
    multi_chain_engine = None  # type: ignore

class EntityType(str, Enum):
    """Entity Type Classification"""
    INDIVIDUAL = "individual"
    EXCHANGE = "exchange"
    MIXER = "mixer"
    BRIDGE = "bridge"
    DEFI_PROTOCOL = "defi_protocol"
    NFT_MARKETPLACE = "nft_marketplace"
    WALLET_SERVICE = "wallet_service"
    UNKNOWN = "unknown"
    CUSTOM = "custom"


@dataclass
class EntityAddress:
    """Einzelne Adresse in Entity"""
    chain_id: str
    address: str
    label: Optional[str] = None
    confidence: float = 1.0  # 0.0 - 1.0
    added_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "address": self.address,
            "label": self.label,
            "confidence": self.confidence,
            "added_at": self.added_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CustomEntity:
    """Custom Entity mit mehreren Adressen"""
    entity_id: str
    name: str
    entity_type: EntityType
    addresses: List[EntityAddress]
    labels: List[str] = field(default_factory=list)
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Aggregate Stats (cached)
    total_addresses: int = 0
    total_transactions: int = 0
    total_value_usd: float = 0.0
    unique_counterparties: int = 0
    risk_score: float = 0.0
    
    # TRM Named Entity Integration
    linked_trm_entities: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.total_addresses = len(self.addresses)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "addresses": [addr.to_dict() for addr in self.addresses],
            "labels": self.labels,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "stats": {
                "total_addresses": self.total_addresses,
                "total_transactions": self.total_transactions,
                "total_value_usd": self.total_value_usd,
                "unique_counterparties": self.unique_counterparties,
                "risk_score": self.risk_score,
            },
            "linked_trm_entities": self.linked_trm_entities,
        }


@dataclass
class EntityAggregateInsights:
    """Aggregierte Insights für Entity"""
    entity_id: str
    total_transactions: int
    total_value_usd: float
    unique_counterparties: Set[str]
    chain_breakdown: Dict[str, Dict[str, Any]]
    counterparty_details: List[Dict[str, Any]]
    risk_exposure: Dict[str, float]
    time_range: Dict[str, datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "total_transactions": self.total_transactions,
            "total_value_usd": self.total_value_usd,
            "unique_counterparties": len(self.unique_counterparties),
            "chain_breakdown": self.chain_breakdown,
            "top_counterparties": self.counterparty_details[:20],  # Top 20
            "risk_exposure": self.risk_exposure,
            "time_range": {
                "first_activity": self.time_range.get("first", datetime.utcnow()).isoformat(),
                "last_activity": self.time_range.get("last", datetime.utcnow()).isoformat(),
            },
        }


class CustomEntitiesService:
    """Custom Entities Management Service (TRM Labs-Style)"""
    
    # Limits (TRM Labs: 1M addresses, 100M transactions)
    MAX_ADDRESSES_PER_ENTITY = 1_000_000
    MAX_TRANSACTIONS_SUPPORTED = 100_000_000
    
    def __init__(self):
        # In-Memory Store (in Production: PostgreSQL + Redis)
        self._entities: Dict[str, CustomEntity] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialisiere Service"""
        if self._initialized:
            return
        
        logger.info("Initializing Custom Entities Service")
        self._initialized = True
    
    async def create_entity(
        self,
        name: str,
        entity_type: EntityType,
        addresses: List[Dict[str, str]],
        labels: Optional[List[str]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CustomEntity:
        """
        Erstelle neue Custom Entity.
        
        Args:
            name: Entity Name
            entity_type: Entity Typ
            addresses: Liste von {"chain_id": str, "address": str, "label": Optional[str]}
            labels: Optional Labels
            description: Optional Beschreibung
            metadata: Optional Metadata
            
        Returns:
            CustomEntity
        """
        await self.initialize()
        
        # Validiere
        if len(addresses) > self.MAX_ADDRESSES_PER_ENTITY:
            raise ValueError(f"Maximum {self.MAX_ADDRESSES_PER_ENTITY:,} addresses allowed")
        
        # Generiere Entity ID
        entity_id = self._generate_entity_id(name, addresses)
        
        # Erstelle EntityAddress Objekte
        entity_addresses = []
        for addr_data in addresses:
            entity_addresses.append(EntityAddress(
                chain_id=addr_data["chain_id"],
                address=addr_data["address"],
                label=addr_data.get("label"),
            ))
        
        # Erstelle Entity
        entity = CustomEntity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            addresses=entity_addresses,
            labels=labels or [],
            description=description,
            metadata=metadata or {},
        )
        
        # Speichere
        self._entities[entity_id] = entity
        
        # Berechne initiale Stats (async)
        asyncio.create_task(self._compute_entity_stats(entity_id))
        
        logger.info(f"Created custom entity: {entity_id} with {len(entity_addresses)} addresses")
        
        return entity
    
    async def get_entity(self, entity_id: str) -> Optional[CustomEntity]:
        """Hole Entity by ID"""
        await self.initialize()
        return self._entities.get(entity_id)
    
    async def update_entity(
        self,
        entity_id: str,
        name: Optional[str] = None,
        labels: Optional[List[str]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CustomEntity:
        """Update Entity Metadata"""
        await self.initialize()
        
        entity = self._entities.get(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        # Update Fields
        if name:
            entity.name = name
        if labels is not None:
            entity.labels = labels
        if description is not None:
            entity.description = description
        if metadata:
            entity.metadata.update(metadata)
        
        entity.updated_at = datetime.utcnow()
        
        return entity
    
    async def add_addresses(
        self,
        entity_id: str,
        addresses: List[Dict[str, str]],
    ) -> CustomEntity:
        """
        Füge Adressen zu Entity hinzu.
        
        Args:
            entity_id: Entity ID
            addresses: Liste von {"chain_id": str, "address": str, "label": Optional[str]}
        """
        await self.initialize()
        
        entity = self._entities.get(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        # Validiere Limit
        new_total = len(entity.addresses) + len(addresses)
        if new_total > self.MAX_ADDRESSES_PER_ENTITY:
            raise ValueError(
                f"Would exceed max {self.MAX_ADDRESSES_PER_ENTITY:,} addresses "
                f"(current: {len(entity.addresses)}, adding: {len(addresses)})"
            )
        
        # Füge hinzu
        for addr_data in addresses:
            entity.addresses.append(EntityAddress(
                chain_id=addr_data["chain_id"],
                address=addr_data["address"],
                label=addr_data.get("label"),
            ))
        
        entity.total_addresses = len(entity.addresses)
        entity.updated_at = datetime.utcnow()
        
        # Re-compute Stats
        asyncio.create_task(self._compute_entity_stats(entity_id))
        
        logger.info(f"Added {len(addresses)} addresses to entity {entity_id}")
        
        return entity
    
    async def remove_addresses(
        self,
        entity_id: str,
        addresses_to_remove: List[Dict[str, str]],
    ) -> CustomEntity:
        """
        Entferne Adressen von Entity.
        
        Args:
            entity_id: Entity ID
            addresses_to_remove: Liste von {"chain_id": str, "address": str}
        """
        await self.initialize()
        
        entity = self._entities.get(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        # Erstelle Set für schnelle Lookup
        remove_set = set()
        for addr in addresses_to_remove:
            key = f"{addr['chain_id']}:{addr['address'].lower()}"
            remove_set.add(key)
        
        # Filtere
        original_count = len(entity.addresses)
        entity.addresses = [
            addr for addr in entity.addresses
            if f"{addr.chain_id}:{addr.address.lower()}" not in remove_set
        ]
        
        removed_count = original_count - len(entity.addresses)
        entity.total_addresses = len(entity.addresses)
        entity.updated_at = datetime.utcnow()
        
        # Re-compute Stats
        if removed_count > 0:
            asyncio.create_task(self._compute_entity_stats(entity_id))
        
        logger.info(f"Removed {removed_count} addresses from entity {entity_id}")
        
        return entity
    
    async def link_trm_entity(
        self,
        entity_id: str,
        trm_entity_name: str,
    ) -> CustomEntity:
        """
        Linke TRM Named Entity zu Custom Entity.
        
        Ermöglicht Merge von TRM-Entities mit Custom Addresses.
        """
        await self.initialize()
        
        entity = self._entities.get(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        if trm_entity_name not in entity.linked_trm_entities:
            entity.linked_trm_entities.append(trm_entity_name)
            entity.updated_at = datetime.utcnow()
            
            logger.info(f"Linked TRM entity '{trm_entity_name}' to {entity_id}")
        
        return entity
    
    async def get_aggregate_insights(
        self,
        entity_id: str,
        include_counterparties: bool = True,
        max_concurrent: int = 10,
    ) -> EntityAggregateInsights:
        """
        Berechne aggregierte Insights für alle Adressen in Entity.
        
        Aggregiert über:
        - Alle Chains
        - Alle Adressen
        - Alle Transaktionen (bis zu 100M)
        
        Returns:
            EntityAggregateInsights
        """
        await self.initialize()
        
        entity = self._entities.get(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        # Parallel Daten sammeln für alle Adressen
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_address_data(addr: EntityAddress):
            async with semaphore:
                return await self._fetch_address_insights(addr)
        
        # Parallel fetchen
        tasks = [fetch_address_data(addr) for addr in entity.addresses]
        address_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregiere
        total_transactions = 0
        total_value_usd = 0.0
        unique_counterparties: Set[str] = set()
        chain_breakdown: Dict[str, Dict[str, Any]] = {}
        counterparty_map: Dict[str, int] = {}
        risk_exposure: Dict[str, float] = {}
        timestamps: List[datetime] = []
        
        for result in address_results:
            if isinstance(result, dict):
                total_transactions += result.get("tx_count", 0)
                total_value_usd += result.get("value_usd", 0.0)
                
                # Counterparties
                for cp in result.get("counterparties", []):
                    unique_counterparties.add(cp)
                    counterparty_map[cp] = counterparty_map.get(cp, 0) + 1
                
                # Chain Breakdown
                chain = result.get("chain_id", "unknown")
                if chain not in chain_breakdown:
                    chain_breakdown[chain] = {
                        "transactions": 0,
                        "value_usd": 0.0,
                        "addresses": 0,
                    }
                chain_breakdown[chain]["transactions"] += result.get("tx_count", 0)
                chain_breakdown[chain]["value_usd"] += result.get("value_usd", 0.0)
                chain_breakdown[chain]["addresses"] += 1
                
                # Timestamps
                if result.get("first_seen"):
                    timestamps.append(result["first_seen"])
                if result.get("last_activity"):
                    timestamps.append(result["last_activity"])
                
                # Risk Exposure
                for category, score in result.get("risk_exposure", {}).items():
                    risk_exposure[category] = max(risk_exposure.get(category, 0), score)
        
        # Top Counterparties
        counterparty_details = [
            {"address": addr, "interactions": count}
            for addr, count in sorted(counterparty_map.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Time Range
        time_range = {}
        if timestamps:
            time_range["first"] = min(timestamps)
            time_range["last"] = max(timestamps)
        
        return EntityAggregateInsights(
            entity_id=entity_id,
            total_transactions=total_transactions,
            total_value_usd=total_value_usd,
            unique_counterparties=unique_counterparties,
            chain_breakdown=chain_breakdown,
            counterparty_details=counterparty_details,
            risk_exposure=risk_exposure,
            time_range=time_range,
        )
    
    async def list_entities(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CustomEntity]:
        """Liste alle Entities"""
        await self.initialize()
        
        all_entities = list(self._entities.values())
        return all_entities[offset:offset + limit]
    
    async def delete_entity(self, entity_id: str) -> bool:
        """Lösche Entity"""
        await self.initialize()
        
        if entity_id in self._entities:
            del self._entities[entity_id]
            logger.info(f"Deleted entity {entity_id}")
            return True
        return False
    
    def _generate_entity_id(self, name: str, addresses: List[Dict[str, str]]) -> str:
        """Generiere eindeutige Entity ID"""
        data = f"{name}:{len(addresses)}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def _compute_entity_stats(self, entity_id: str):
        """Berechne und cache Entity Stats (async)"""
        try:
            entity = self._entities.get(entity_id)
            if not entity:
                return
            
            # Vereinfachte Stats (in Production: full aggregation)
            insights = await self.get_aggregate_insights(entity_id, include_counterparties=False)
            
            entity.total_transactions = insights.total_transactions
            entity.total_value_usd = insights.total_value_usd
            entity.unique_counterparties = len(insights.unique_counterparties)
            
            # Risk Score (max über alle Adressen)
            if insights.risk_exposure:
                entity.risk_score = max(insights.risk_exposure.values())
            
            logger.debug(f"Updated stats for entity {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to compute stats for entity {entity_id}: {e}")
    
    async def _fetch_address_insights(self, addr: EntityAddress) -> Dict[str, Any]:
        """Fetch Insights für einzelne Adresse"""
        try:
            engine = multi_chain_engine
            if not engine or not hasattr(engine, "get_address_transactions_paged"):
                return {
                    "chain_id": addr.chain_id,
                    "tx_count": 0,
                    "value_usd": 0.0,
                    "counterparties": [],
                }

            # Hole Transaktionen (limitiert für Performance)
            txs = await engine.get_address_transactions_paged(
                chain_id=addr.chain_id,
                address=addr.address,
                limit=100,
            )
            
            if not txs:
                return {
                    "chain_id": addr.chain_id,
                    "tx_count": 0,
                    "value_usd": 0.0,
                    "counterparties": [],
                }
            
            # Extrahiere Metriken
            counterparties = set()
            total_value = 0.0
            timestamps = []
            
            for tx in txs:
                if tx.get("from"):
                    counterparties.add(tx["from"].lower())
                if tx.get("to"):
                    counterparties.add(tx["to"].lower())
                
                if tx.get("value"):
                    try:
                        total_value += float(tx["value"])
                    except:
                        pass
                
                if tx.get("timestamp"):
                    try:
                        ts = datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00"))
                        timestamps.append(ts)
                    except:
                        pass
            
            return {
                "chain_id": addr.chain_id,
                "tx_count": len(txs),
                "value_usd": total_value,
                "counterparties": list(counterparties),
                "first_seen": min(timestamps) if timestamps else None,
                "last_activity": max(timestamps) if timestamps else None,
                "risk_exposure": {},  # Simplified
            }
            
        except Exception as e:
            logger.debug(f"Failed to fetch insights for {addr.chain_id}/{addr.address}: {e}")
            return {
                "chain_id": addr.chain_id,
                "tx_count": 0,
                "value_usd": 0.0,
                "counterparties": [],
            }


# Global Service Instance
custom_entities_service = CustomEntitiesService()
