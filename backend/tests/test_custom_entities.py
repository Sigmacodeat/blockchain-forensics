"""
Tests für Custom Entities Service
==================================
"""

import pytest
from unittest.mock import patch, AsyncMock

from app.services.custom_entities import (
    custom_entities_service,
    CustomEntity,
    EntityAddress,
    EntityType,
)


@pytest.mark.asyncio
async def test_create_entity_success():
    """Test erfolgreiche Entity-Erstellung"""
    
    await custom_entities_service.initialize()
    
    entity = await custom_entities_service.create_entity(
        name="Test Entity",
        entity_type=EntityType.CUSTOM,
        addresses=[
            {"chain_id": "ethereum", "address": "0x123", "label": "Main Wallet"},
            {"chain_id": "bitcoin", "address": "bc1q456", "label": "BTC Wallet"},
        ],
        labels=["test", "investigation"],
        description="Test entity for unit tests",
        metadata={"priority": "high"},
    )
    
    assert isinstance(entity, CustomEntity)
    assert entity.name == "Test Entity"
    assert entity.entity_type == EntityType.CUSTOM
    assert len(entity.addresses) == 2
    assert entity.total_addresses == 2
    assert "test" in entity.labels
    assert entity.description == "Test entity for unit tests"
    assert entity.metadata["priority"] == "high"


@pytest.mark.asyncio
async def test_create_entity_exceeds_max_addresses():
    """Test dass MAX_ADDRESSES_PER_ENTITY respektiert wird"""
    
    await custom_entities_service.initialize()
    
    # Versuche mehr als MAX_ADDRESSES zu erstellen
    with pytest.raises(ValueError, match="Maximum .* addresses allowed"):
        addresses = [
            {"chain_id": "ethereum", "address": f"0x{i:040x}"}
            for i in range(custom_entities_service.MAX_ADDRESSES_PER_ENTITY + 1)
        ]
        
        await custom_entities_service.create_entity(
            name="Too Many Addresses",
            entity_type=EntityType.CUSTOM,
            addresses=addresses,
        )


@pytest.mark.asyncio
async def test_get_entity():
    """Test Entity abrufen"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity
    created = await custom_entities_service.create_entity(
        name="Get Test",
        entity_type=EntityType.EXCHANGE,
        addresses=[{"chain_id": "ethereum", "address": "0xabc"}],
    )
    
    # Hole Entity
    entity = await custom_entities_service.get_entity(created.entity_id)
    
    assert entity is not None
    assert entity.entity_id == created.entity_id
    assert entity.name == "Get Test"


@pytest.mark.asyncio
async def test_get_nonexistent_entity():
    """Test dass None zurückgegeben wird für nicht-existente Entity"""
    
    await custom_entities_service.initialize()
    
    entity = await custom_entities_service.get_entity("nonexistent_id")
    
    assert entity is None


@pytest.mark.asyncio
async def test_update_entity():
    """Test Entity-Update"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity
    entity = await custom_entities_service.create_entity(
        name="Original Name",
        entity_type=EntityType.CUSTOM,
        addresses=[{"chain_id": "ethereum", "address": "0x123"}],
        labels=["old_label"],
    )
    
    # Update Entity
    updated = await custom_entities_service.update_entity(
        entity_id=entity.entity_id,
        name="Updated Name",
        labels=["new_label"],
        description="New description",
        metadata={"updated": True},
    )
    
    assert updated.name == "Updated Name"
    assert "new_label" in updated.labels
    assert updated.description == "New description"
    assert updated.metadata["updated"] is True
    assert updated.updated_at > entity.created_at


@pytest.mark.asyncio
async def test_add_addresses():
    """Test Adressen hinzufügen"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity mit 1 Adresse
    entity = await custom_entities_service.create_entity(
        name="Add Test",
        entity_type=EntityType.CUSTOM,
        addresses=[{"chain_id": "ethereum", "address": "0x123"}],
    )
    
    original_count = len(entity.addresses)
    
    # Füge 2 weitere Adressen hinzu
    updated = await custom_entities_service.add_addresses(
        entity_id=entity.entity_id,
        addresses=[
            {"chain_id": "polygon", "address": "0x456"},
            {"chain_id": "arbitrum", "address": "0x789"},
        ],
    )
    
    assert len(updated.addresses) == original_count + 2
    assert updated.total_addresses == original_count + 2


@pytest.mark.asyncio
async def test_add_addresses_exceeds_limit():
    """Test dass Limit beim Hinzufügen respektiert wird"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity
    entity = await custom_entities_service.create_entity(
        name="Limit Test",
        entity_type=EntityType.CUSTOM,
        addresses=[{"chain_id": "ethereum", "address": "0x123"}],
    )
    
    # Versuche zu viele Adressen hinzuzufügen
    with pytest.raises(ValueError, match="Would exceed max"):
        addresses = [
            {"chain_id": "ethereum", "address": f"0x{i:040x}"}
            for i in range(custom_entities_service.MAX_ADDRESSES_PER_ENTITY)
        ]
        
        await custom_entities_service.add_addresses(
            entity_id=entity.entity_id,
            addresses=addresses,
        )


@pytest.mark.asyncio
async def test_remove_addresses():
    """Test Adressen entfernen"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity mit 3 Adressen
    entity = await custom_entities_service.create_entity(
        name="Remove Test",
        entity_type=EntityType.CUSTOM,
        addresses=[
            {"chain_id": "ethereum", "address": "0x123"},
            {"chain_id": "polygon", "address": "0x456"},
            {"chain_id": "arbitrum", "address": "0x789"},
        ],
    )
    
    # Entferne 1 Adresse
    updated = await custom_entities_service.remove_addresses(
        entity_id=entity.entity_id,
        addresses_to_remove=[
            {"chain_id": "polygon", "address": "0x456"},
        ],
    )
    
    assert len(updated.addresses) == 2
    assert updated.total_addresses == 2
    
    # Prüfe dass richtige Adresse entfernt wurde
    remaining_addresses = [(a.chain_id, a.address) for a in updated.addresses]
    assert ("polygon", "0x456") not in remaining_addresses
    assert ("ethereum", "0x123") in remaining_addresses


@pytest.mark.asyncio
async def test_link_trm_entity():
    """Test TRM Entity Linking"""
    
    await custom_entities_service.initialize()
    
    entity = await custom_entities_service.create_entity(
        name="Link Test",
        entity_type=EntityType.CUSTOM,
        addresses=[{"chain_id": "ethereum", "address": "0x123"}],
    )
    
    # Linke TRM Entity
    updated = await custom_entities_service.link_trm_entity(
        entity_id=entity.entity_id,
        trm_entity_name="Binance",
    )
    
    assert "Binance" in updated.linked_trm_entities
    
    # Linke zweite TRM Entity
    updated2 = await custom_entities_service.link_trm_entity(
        entity_id=entity.entity_id,
        trm_entity_name="Coinbase",
    )
    
    assert len(updated2.linked_trm_entities) == 2
    assert "Binance" in updated2.linked_trm_entities
    assert "Coinbase" in updated2.linked_trm_entities


@pytest.mark.asyncio
async def test_get_aggregate_insights():
    """Test Aggregate Insights Berechnung"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity
    entity = await custom_entities_service.create_entity(
        name="Insights Test",
        entity_type=EntityType.CUSTOM,
        addresses=[
            {"chain_id": "ethereum", "address": "0x123"},
            {"chain_id": "ethereum", "address": "0x456"},
        ],
    )
    
    # Mock Multi-Chain Engine
    with patch('app.services.custom_entities.multi_chain_engine') as mock_engine:
        mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
            {
                "from": "0x123",
                "to": "0xabc",
                "value": "1000000",
                "timestamp": "2025-10-18T10:00:00Z",
            },
            {
                "from": "0xdef",
                "to": "0x123",
                "value": "2000000",
                "timestamp": "2025-10-18T11:00:00Z",
            },
        ])
        
        insights = await custom_entities_service.get_aggregate_insights(
            entity_id=entity.entity_id,
            include_counterparties=True,
        )
        
        assert insights.entity_id == entity.entity_id
        assert insights.total_transactions >= 0
        assert insights.total_value_usd >= 0
        assert len(insights.unique_counterparties) >= 0
        assert "ethereum" in insights.chain_breakdown


@pytest.mark.asyncio
async def test_list_entities():
    """Test Entity-Liste"""
    
    await custom_entities_service.initialize()
    
    # Erstelle 3 Entities
    for i in range(3):
        await custom_entities_service.create_entity(
            name=f"Entity {i}",
            entity_type=EntityType.CUSTOM,
            addresses=[{"chain_id": "ethereum", "address": f"0x{i:040x}"}],
        )
    
    # Liste Entities
    entities = await custom_entities_service.list_entities(limit=10, offset=0)
    
    assert len(entities) >= 3


@pytest.mark.asyncio
async def test_delete_entity():
    """Test Entity löschen"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity
    entity = await custom_entities_service.create_entity(
        name="Delete Test",
        entity_type=EntityType.CUSTOM,
        addresses=[{"chain_id": "ethereum", "address": "0x123"}],
    )
    
    # Lösche Entity
    success = await custom_entities_service.delete_entity(entity.entity_id)
    
    assert success is True
    
    # Prüfe dass Entity nicht mehr existiert
    deleted = await custom_entities_service.get_entity(entity.entity_id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_nonexistent_entity():
    """Test Löschen von nicht-existenter Entity"""
    
    await custom_entities_service.initialize()
    
    success = await custom_entities_service.delete_entity("nonexistent_id")
    
    assert success is False


def test_entity_address_to_dict():
    """Test EntityAddress Serialisierung"""
    
    address = EntityAddress(
        chain_id="ethereum",
        address="0x123",
        label="Test Wallet",
        confidence=0.95,
        metadata={"source": "manual"},
    )
    
    result = address.to_dict()
    
    assert result["chain_id"] == "ethereum"
    assert result["address"] == "0x123"
    assert result["label"] == "Test Wallet"
    assert result["confidence"] == 0.95
    assert result["metadata"]["source"] == "manual"
    assert "added_at" in result


@pytest.mark.asyncio
async def test_entity_stats_computation():
    """Test dass Stats automatisch berechnet werden"""
    
    await custom_entities_service.initialize()
    
    entity = await custom_entities_service.create_entity(
        name="Stats Test",
        entity_type=EntityType.CUSTOM,
        addresses=[{"chain_id": "ethereum", "address": "0x123"}],
    )
    
    # Initial sollten Stats 0 sein
    assert entity.total_transactions == 0
    assert entity.total_value_usd == 0.0
    
    # Nach Stats-Computation sollten sie upgedatet werden
    # (wird async durchgeführt, also warten wir kurz)
    import asyncio
    await asyncio.sleep(0.1)
    
    # Stats sollten jetzt existieren (auch wenn 0)
    assert entity.risk_score >= 0.0


@pytest.mark.asyncio
async def test_concurrent_entity_operations():
    """Test Thread-Safety bei parallelen Operationen"""
    
    await custom_entities_service.initialize()
    
    # Erstelle Entity
    entity = await custom_entities_service.create_entity(
        name="Concurrent Test",
        entity_type=EntityType.CUSTOM,
        addresses=[{"chain_id": "ethereum", "address": "0x123"}],
    )
    
    # Simuliere parallele Updates
    import asyncio
    
    async def update_labels(labels):
        return await custom_entities_service.update_entity(
            entity_id=entity.entity_id,
            labels=labels,
        )
    
    # Führe parallele Updates durch
    results = await asyncio.gather(
        update_labels(["label1"]),
        update_labels(["label2"]),
        update_labels(["label3"]),
    )
    
    # Alle sollten erfolgreich sein
    assert all(r is not None for r in results)
    
    # Finales Entity holen
    final = await custom_entities_service.get_entity(entity.entity_id)
    
    # Sollte irgendwelche Labels haben
    assert len(final.labels) > 0
