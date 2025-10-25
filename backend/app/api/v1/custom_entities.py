"""
Custom Entities API
===================

TRM Labs-Style Custom Entity Management API.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.services.custom_entities import (
    custom_entities_service,
    EntityType,
)
from app.auth.dependencies import get_current_user_optional, require_plan

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateEntityRequest(BaseModel):
    """Request für Entity-Erstellung"""
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: EntityType
    addresses: List[Dict[str, str]] = Field(..., min_length=1, max_length=1000)
    labels: Optional[List[str]] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateEntityRequest(BaseModel):
    """Request für Entity-Update"""
    name: Optional[str] = None
    labels: Optional[List[str]] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AddAddressesRequest(BaseModel):
    """Request für Adressen hinzufügen"""
    addresses: List[Dict[str, str]] = Field(..., min_length=1, max_length=10000)


class RemoveAddressesRequest(BaseModel):
    """Request für Adressen entfernen"""
    addresses: List[Dict[str, str]] = Field(..., min_length=1)


class LinkTRMEntityRequest(BaseModel):
    """Request für TRM Entity Link"""
    trm_entity_name: str = Field(..., min_length=1)


@router.post(
    "/entities",
    summary="Create Custom Entity",
    description="""
    Erstelle eine neue Custom Entity mit mehreren Adressen.
    
    Unterstützt bis zu 1M Adressen pro Entity (TRM Labs-Level).
    """,
    dependencies=[Depends(require_plan("pro"))],
)
async def create_entity(
    request: CreateEntityRequest,
    current_user = Depends(get_current_user_optional),
):
    """Erstelle neue Custom Entity"""
    try:
        entity = await custom_entities_service.create_entity(
            name=request.name,
            entity_type=request.entity_type,
            addresses=request.addresses,
            labels=request.labels,
            description=request.description,
            metadata=request.metadata,
        )
        
        return {
            "success": True,
            "entity": entity.to_dict(),
            "message": f"Created entity with {len(entity.addresses)} addresses",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/entities/{entity_id}",
    summary="Get Custom Entity",
    description="Hole Entity Details by ID",
    dependencies=[Depends(require_plan("pro"))],
)
async def get_entity(
    entity_id: str,
    current_user = Depends(get_current_user_optional),
):
    """Hole Entity by ID"""
    try:
        entity = await custom_entities_service.get_entity(entity_id)
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "entity": entity.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/entities/{entity_id}",
    summary="Update Custom Entity",
    description="Update Entity Metadata",
    dependencies=[Depends(require_plan("pro"))],
)
async def update_entity(
    entity_id: str,
    request: UpdateEntityRequest,
    current_user = Depends(get_current_user_optional),
):
    """Update Entity"""
    try:
        entity = await custom_entities_service.update_entity(
            entity_id=entity_id,
            name=request.name,
            labels=request.labels,
            description=request.description,
            metadata=request.metadata,
        )
        
        return {
            "success": True,
            "entity": entity.to_dict(),
            "message": "Entity updated",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/entities/{entity_id}/addresses",
    summary="Add Addresses to Entity",
    description="Füge Adressen zu Entity hinzu (bis zu 1M total)",
    dependencies=[Depends(require_plan("pro"))],
)
async def add_addresses(
    entity_id: str,
    request: AddAddressesRequest,
    current_user = Depends(get_current_user_optional),
):
    """Füge Adressen hinzu"""
    try:
        entity = await custom_entities_service.add_addresses(
            entity_id=entity_id,
            addresses=request.addresses,
        )
        
        return {
            "success": True,
            "entity": entity.to_dict(),
            "message": f"Added {len(request.addresses)} addresses",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add addresses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/entities/{entity_id}/addresses",
    summary="Remove Addresses from Entity",
    description="Entferne Adressen von Entity",
    dependencies=[Depends(require_plan("pro"))],
)
async def remove_addresses(
    entity_id: str,
    request: RemoveAddressesRequest,
    current_user = Depends(get_current_user_optional),
):
    """Entferne Adressen"""
    try:
        entity = await custom_entities_service.remove_addresses(
            entity_id=entity_id,
            addresses_to_remove=request.addresses,
        )
        
        return {
            "success": True,
            "entity": entity.to_dict(),
            "message": "Addresses removed",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to remove addresses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/entities/{entity_id}/link-trm",
    summary="Link TRM Named Entity",
    description="Verknüpfe TRM Named Entity mit Custom Entity",
    dependencies=[Depends(require_plan("plus"))],
)
async def link_trm_entity(
    entity_id: str,
    request: LinkTRMEntityRequest,
    current_user = Depends(get_current_user_optional),
):
    """Linke TRM Entity"""
    try:
        entity = await custom_entities_service.link_trm_entity(
            entity_id=entity_id,
            trm_entity_name=request.trm_entity_name,
        )
        
        return {
            "success": True,
            "entity": entity.to_dict(),
            "message": f"Linked TRM entity: {request.trm_entity_name}",
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to link TRM entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/entities/{entity_id}/insights",
    summary="Get Aggregate Insights",
    description="""
    Hole aggregierte Insights für alle Adressen in Entity.
    
    Aggregiert über:
    - Alle Chains
    - Bis zu 100M Transaktionen
    - Alle Counterparties
    - Risk Exposure
    """,
    dependencies=[Depends(require_plan("pro"))],
)
async def get_aggregate_insights(
    entity_id: str,
    include_counterparties: bool = Query(default=True),
    current_user = Depends(get_current_user_optional),
):
    """Hole Aggregate Insights"""
    try:
        insights = await custom_entities_service.get_aggregate_insights(
            entity_id=entity_id,
            include_counterparties=include_counterparties,
        )
        
        return {
            "success": True,
            "insights": insights.to_dict(),
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/entities",
    summary="List Custom Entities",
    description="Liste alle Custom Entities",
    dependencies=[Depends(require_plan("pro"))],
)
async def list_entities(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user_optional),
):
    """Liste Entities"""
    try:
        entities = await custom_entities_service.list_entities(
            limit=limit,
            offset=offset,
        )
        
        return {
            "success": True,
            "total": len(entities),
            "entities": [e.to_dict() for e in entities],
        }
        
    except Exception as e:
        logger.error(f"Failed to list entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/entities/{entity_id}",
    summary="Delete Custom Entity",
    description="Lösche Entity",
    dependencies=[Depends(require_plan("pro"))],
)
async def delete_entity(
    entity_id: str,
    current_user = Depends(get_current_user_optional),
):
    """Lösche Entity"""
    try:
        success = await custom_entities_service.delete_entity(entity_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "message": "Entity deleted",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
