"""
Service Orchestrator API
Endpoints für Service-Koordination und System-Integration
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime

from app.services.service_orchestrator import (
    service_orchestrator, EventType, ServiceStatus,
    publish_system_event, execute_data_pipeline, trigger_workflow, get_system_overview
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get overall system status and service health
    """
    try:
        status = await service_orchestrator.get_system_status()
        return status

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/overview")
async def get_system_overview_endpoint() -> Dict[str, Any]:
    """
    Get comprehensive system overview
    """
    try:
        overview = await get_system_overview()
        return overview

    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/publish")
async def publish_event(
    event_type: str = Body(...),
    data: Dict[str, Any] = Body(...),
    source: str = Body("external")
) -> Dict[str, Any]:
    """
    Publish an event to the system

    **Request Body:**
    ```json
    {
      "event_type": "alert_triggered",
      "data": {"alert_id": "alert_123", "severity": "high"},
      "source": "alert_engine"
    }
    ```
    """
    try:
        # Convert string to enum
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

        await publish_system_event(event_type_enum, data, source)

        return {
            "status": "published",
            "event_type": event_type,
            "source": source,
            "published_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipelines/execute")
async def execute_pipeline(
    pipeline_name: str = Body(...),
    data: Any = Body(...)
) -> Dict[str, Any]:
    """
    Execute a data processing pipeline

    **Request Body:**
    ```json
    {
      "pipeline_name": "evidence_processing",
      "data": {"evidence_id": "evidence_123", "hash": "sha256_hash"}
    }
    ```
    """
    try:
        result = await execute_data_pipeline(pipeline_name, data)

        return {
            "status": "executed",
            "pipeline": pipeline_name,
            "result": result,
            "executed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error executing pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/trigger")
async def trigger_workflow_endpoint(
    workflow_name: str = Body(...),
    trigger_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Trigger a cross-service workflow

    **Request Body:**
    ```json
    {
      "workflow_name": "alert_to_case",
      "trigger_data": {"alert_id": "alert_123", "severity": "critical"}
    }
    ```
    """
    try:
        result = await trigger_workflow(workflow_name, trigger_data)

        return result

    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/history")
async def get_event_history(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    source_service: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    """
    Get event history with optional filtering

    **Query Parameters:**
    - limit: Maximum events to return (1-1000)
    - event_type: Filter by event type
    - source_service: Filter by source service
    """
    try:
        events = service_orchestrator.event_bus.event_history[-limit:]

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]

        if source_service:
            events = [e for e in events if e.source_service == source_service]

        return [
            {
                "event_type": event.event_type.value,
                "source_service": event.source_service,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "correlation_id": event.correlation_id,
                "priority": event.priority
            }
            for event in events
        ]

    except Exception as e:
        logger.error(f"Error getting event history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/health")
async def get_services_health() -> Dict[str, str]:
    """
    Get health status of all services
    """
    try:
        status = await service_orchestrator.health_monitor.get_all_service_status()
        return {service: status.value for service, status in status.items()}

    except Exception as e:
        logger.error(f"Error getting services health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipelines")
async def get_pipelines() -> Dict[str, str]:
    """
    Get available data processing pipelines
    """
    try:
        return service_orchestrator.data_flow_manager.pipeline_status

    except Exception as e:
        logger.error(f"Error getting pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integration/test")
async def test_integration() -> Dict[str, Any]:
    """
    Test integration between all services
    """
    try:
        # Test event publishing
        test_event = {
            "test_id": "integration_test",
            "timestamp": datetime.utcnow().isoformat(),
            "test_data": "integration_test_payload"
        }

        await publish_system_event(EventType.ALERT_TRIGGERED, test_event, "integration_test")

        # Test pipeline execution
        test_data = {"test": "pipeline_data"}
        pipeline_result = await execute_data_pipeline("evidence_processing", test_data)

        # Get system status
        system_status = await get_system_overview()

        return {
            "status": "integration_test_completed",
            "event_published": True,
            "pipeline_executed": True,
            "system_status": system_status,
            "test_timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in integration test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integration/workflows")
async def get_available_workflows() -> List[Dict[str, Any]]:
    """
    Get available cross-service workflows
    """
    try:
        workflows = [
            {
                "name": "alert_to_case",
                "description": "Create investigation case when high/critical alert is triggered",
                "trigger_service": "alert_engine",
                "target_services": ["case_manager", "audit_service"]
            },
            {
                "name": "anomaly_to_investigation",
                "description": "Create investigation when ML anomaly is detected",
                "trigger_service": "ml_service",
                "target_services": ["alert_engine", "case_manager"]
            },
            {
                "name": "evidence_validation",
                "description": "Validate and enrich evidence through processing pipeline",
                "trigger_service": "case_manager",
                "target_services": ["security_service", "audit_service"]
            }
        ]

        return workflows

    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))
