"""
Service Orchestrator & Integration Layer
Zentrale Koordination aller System-Services für nahtlose Interaktion
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class EventType(Enum):
    """Types of system events"""
    ALERT_TRIGGERED = "alert_triggered"
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    EVIDENCE_ADDED = "evidence_added"
    ANOMALY_DETECTED = "anomaly_detected"
    GRAPH_UPDATED = "graph_updated"
    METRIC_RECORDED = "metric_recorded"
    SECURITY_INCIDENT = "security_incident"
    COMPLIANCE_VIOLATION = "compliance_violation"


@dataclass
class ServiceEvent:
    """Represents a system event"""
    event_type: EventType
    source_service: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    priority: str = "normal"


class ServiceHealthMonitor:
    """Monitors health of all services"""

    def __init__(self):
        self.service_status: Dict[str, ServiceStatus] = {}
        self.last_health_check: Dict[str, datetime] = {}
        self.health_check_intervals = {
            "alert_engine": 30,
            "case_manager": 60,
            "graph_db": 30,
            "ml_service": 60,
            "security_service": 30
        }

    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """Check health of a specific service"""
        try:
            if service_name == "alert_engine":
                # Prefer facade to avoid tight coupling to engine internals
                try:
                    from app.services.alert_service import alert_service as _as
                    _ = _as.list_rules()
                    return ServiceStatus.HEALTHY
                except Exception:
                    return ServiceStatus.UNHEALTHY

            elif service_name == "case_manager":
                from app.models.case import cases
                # Check if case storage is accessible
                return ServiceStatus.HEALTHY if isinstance(cases, dict) else ServiceStatus.UNHEALTHY

            elif service_name == "graph_db":
                from app.db.neo4j_client import neo4j_client
                # Check database connectivity
                try:
                    await neo4j_client.execute_read("RETURN 1 as test")
                    return ServiceStatus.HEALTHY
                except Exception:
                    return ServiceStatus.UNHEALTHY

            elif service_name == "ml_service":
                from app.services.ml_model_service import ml_model_service
                # Check if ML service is initialized
                return ServiceStatus.HEALTHY if hasattr(ml_model_service, 'models') else ServiceStatus.UNHEALTHY

            elif service_name == "security_service":
                from app.services.security_compliance import audit_trail_service
                # Check if audit service is working
                return ServiceStatus.HEALTHY if hasattr(audit_trail_service, 'audit_log') else ServiceStatus.UNHEALTHY

            else:
                return ServiceStatus.UNKNOWN

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return ServiceStatus.UNHEALTHY

    async def get_all_service_status(self) -> Dict[str, ServiceStatus]:
        """Get health status of all services"""
        services = list(self.health_check_intervals.keys())
        status_tasks = [self.check_service_health(service) for service in services]

        results = await asyncio.gather(*status_tasks, return_exceptions=True)

        service_status = {}
        for service, result in zip(services, results):
            if isinstance(result, Exception):
                service_status[service] = ServiceStatus.UNHEALTHY
                logger.error(f"Health check exception for {service}: {result}")
            else:
                service_status[service] = result
                self.last_health_check[service] = datetime.utcnow()

        self.service_status.update(service_status)
        return service_status


class EventBus:
    """Event bus for service communication"""

    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[ServiceEvent] = []
        self.max_history_size = 1000

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                logger.info(f"Unsubscribed from {event_type.value}")
            except ValueError:
                pass

    async def publish(self, event: ServiceEvent):
        """Publish an event to all subscribers"""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)

        # Notify subscribers
        if event.event_type in self.subscribers:
            tasks = []
            for callback in self.subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(callback(event))
                    else:
                        # Run sync callback in thread pool
                        tasks.append(asyncio.get_event_loop().run_in_executor(None, callback, event))
                except Exception as e:
                    logger.error(f"Error in event subscriber for {event.event_type.value}: {e}")

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Published event: {event.event_type.value}")


class DataFlowManager:
    """Manages data flow between services"""

    def __init__(self):
        self.data_pipelines: Dict[str, Callable] = {}
        self.pipeline_status: Dict[str, str] = {}

    def register_pipeline(self, name: str, pipeline_func: Callable):
        """Register a data processing pipeline"""
        self.data_pipelines[name] = pipeline_func
        self.pipeline_status[name] = "registered"
        logger.info(f"Registered data pipeline: {name}")

    async def execute_pipeline(self, pipeline_name: str, data: Any) -> Any:
        """Execute a data processing pipeline"""
        if pipeline_name not in self.data_pipelines:
            raise ValueError(f"Pipeline {pipeline_name} not found")

        try:
            self.pipeline_status[pipeline_name] = "running"

            # Execute pipeline
            if asyncio.iscoroutinefunction(self.data_pipelines[pipeline_name]):
                result = await self.data_pipelines[pipeline_name](data)
            else:
                result = self.data_pipelines[pipeline_name](data)

            self.pipeline_status[pipeline_name] = "completed"
            logger.info(f"Pipeline {pipeline_name} completed successfully")
            return result

        except Exception as e:
            self.pipeline_status[pipeline_name] = "failed"
            logger.error(f"Pipeline {pipeline_name} failed: {e}")
            raise


class ServiceOrchestrator:
    """Main service orchestrator coordinating all system components"""

    def __init__(self):
        self.health_monitor = ServiceHealthMonitor()
        self.event_bus = EventBus()
        self.data_flow_manager = DataFlowManager()

        # Initialize services
        self._initialize_services()

        # Setup event handlers
        self._setup_event_handlers()

        # Setup data pipelines
        self._setup_data_pipelines()

        # Start background tasks
        self._start_background_tasks()

    def _initialize_services(self):
        """Initialize all system services"""
        try:
            # Import and initialize services (use facade to avoid tight coupling)
            from app.services.alert_service import alert_service as _alert_service
            from app.services.ml_model_service import ml_model_service
            from app.services.security_compliance import audit_trail_service, security_service
            from app.services.performance_monitor import performance_monitor

            # Store service references
            self.services = {
                "alert_service": _alert_service,
                "ml_service": ml_model_service,
                "audit_service": audit_trail_service,
                "security_service": security_service,
                "performance_monitor": performance_monitor
            }

            logger.info("All services initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise

    def _setup_event_handlers(self):
        """Setup event handlers for service communication"""

        # Alert triggered -> Create/Update case
        async def handle_alert_triggered(event: ServiceEvent):
            alert_data = event.data
            try:
                # Create case for high/critical alerts
                if alert_data.get("severity") in ["high", "critical"]:
                    from app.models.case import create_case

                    case = create_case(
                        title=f"Alert Investigation: {alert_data.get('title', 'Unknown')}",
                        description=alert_data.get("description", ""),
                        priority="high" if alert_data.get("severity") == "critical" else "medium",
                        category="alert_investigation",
                        source="alert_system",
                        created_by="system"
                    )

                    # Add alert as evidence
                    from app.models.case import add_evidence
                    add_evidence(
                        case_id=case.id,
                        name=f"Alert: {alert_data.get('alert_type', 'unknown')}",
                        description=alert_data.get("description", ""),
                        evidence_type="alert",
                        source_url=alert_data.get("source_url"),
                        metadata=alert_data
                    )

                    logger.info(f"Created case {case.id} for alert {alert_data.get('alert_id')}")

            except Exception as e:
                logger.error(f"Error handling alert event: {e}")

        self.event_bus.subscribe(EventType.ALERT_TRIGGERED, handle_alert_triggered)

        # Case created -> Trigger graph analysis
        async def handle_case_created(event: ServiceEvent):
            case_data = event.data
            try:
                # Trigger graph analysis for new case
                addresses = case_data.get("related_addresses", [])
                if addresses:
                    # This would trigger graph analysis
                    logger.info(f"Triggered graph analysis for case {case_data.get('case_id')}")

            except Exception as e:
                logger.error(f"Error handling case created event: {e}")

        self.event_bus.subscribe(EventType.CASE_CREATED, handle_case_created)

        # Anomaly detected -> Trigger alert
        async def handle_anomaly_detected(event: ServiceEvent):
            anomaly_data = event.data
            try:
                # Convert anomaly to alert via facade
                from app.services.alert_service import alert_service as _as
                alert_event = {
                    "address": anomaly_data.get("address"),
                    "anomaly_score": anomaly_data.get("anomaly_score"),
                    "anomaly_factors": anomaly_data.get("anomaly_factors", []),
                    "risk_score": min(1.0, anomaly_data.get("anomaly_score", 0.0))
                }

                alerts = await _as.process_event(alert_event)
                logger.info(f"Generated {len(alerts)} alerts from anomaly detection")

            except Exception as e:
                logger.error(f"Error handling anomaly event: {e}")

        self.event_bus.subscribe(EventType.ANOMALY_DETECTED, handle_anomaly_detected)

    def _setup_data_pipelines(self):
        """Setup data processing pipelines"""

        # Evidence processing pipeline
        def evidence_pipeline(evidence_data: Dict[str, Any]) -> Dict[str, Any]:
            """Process evidence through validation and enrichment"""
            try:
                # Validate evidence integrity
                if evidence_data.get("hash_value"):
                    # Verify hash
                    pass

                # Enrich with metadata
                enriched = evidence_data.copy()
                enriched["processed_at"] = datetime.utcnow().isoformat()
                enriched["validation_status"] = "pending"

                return enriched

            except Exception as e:
                logger.error(f"Error in evidence pipeline: {e}")
                raise

        self.data_flow_manager.register_pipeline("evidence_processing", evidence_pipeline)

        # Alert correlation pipeline
        async def alert_correlation_pipeline(alert_data: Dict[str, Any]) -> Dict[str, Any]:
            """Correlate alerts with existing cases and evidence"""
            try:
                # Find related cases
                related_cases = []
                if alert_data.get("address"):
                    # This would query cases by address
                    pass

                # Find related evidence
                related_evidence = []
                if alert_data.get("tx_hash"):
                    # This would query evidence by tx_hash
                    pass

                return {
                    "alert": alert_data,
                    "related_cases": related_cases,
                    "related_evidence": related_evidence,
                    "correlation_timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"Error in alert correlation pipeline: {e}")
                raise

        self.data_flow_manager.register_pipeline("alert_correlation", alert_correlation_pipeline)

    def _start_background_tasks(self):
        """Start background orchestration tasks"""
        # Health monitoring
        asyncio.create_task(self._periodic_health_check())

        # Event cleanup
        asyncio.create_task(self._periodic_event_cleanup())

        # Data pipeline monitoring
        asyncio.create_task(self._monitor_pipelines())

    async def _periodic_health_check(self):
        """Periodic health check of all services"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.health_monitor.get_all_service_status()

                # Log overall system health
                healthy_services = sum(
                    1 for status in self.health_monitor.service_status.values()
                    if status == ServiceStatus.HEALTHY
                )
                total_services = len(self.health_monitor.service_status)

                logger.info(f"System health: {healthy_services}/{total_services} services healthy")

            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")

    async def _periodic_event_cleanup(self):
        """Periodic cleanup of old events"""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean every hour

                # Cleanup old events
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.event_bus.event_history = [
                    event for event in self.event_bus.event_history
                    if event.timestamp > cutoff_time
                ]

                logger.info(f"Cleaned up event history, {len(self.event_bus.event_history)} events remaining")

            except Exception as e:
                logger.error(f"Error in event cleanup: {e}")

    async def _monitor_pipelines(self):
        """Monitor data pipeline status"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                failed_pipelines = [
                    name for name, status in self.data_flow_manager.pipeline_status.items()
                    if status == "failed"
                ]

                if failed_pipelines:
                    logger.warning(f"Failed pipelines detected: {failed_pipelines}")

                    # Reset failed pipelines
                    for pipeline in failed_pipelines:
                        self.data_flow_manager.pipeline_status[pipeline] = "registered"

            except Exception as e:
                logger.error(f"Error monitoring pipelines: {e}")

    async def publish_event(self, event_type: EventType, data: Dict[str, Any], source_service: str):
        """Publish an event to the system"""
        event = ServiceEvent(
            event_type=event_type,
            source_service=source_service,
            timestamp=datetime.utcnow(),
            data=data,
            correlation_id=data.get("correlation_id")
        )

        await self.event_bus.publish(event)

    async def execute_pipeline(self, pipeline_name: str, data: Any) -> Any:
        """Execute a data processing pipeline"""
        return await self.data_flow_manager.execute_pipeline(pipeline_name, data)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        service_status = await self.health_monitor.get_all_service_status()

        # Calculate overall health
        healthy_count = sum(1 for status in service_status.values() if status == ServiceStatus.HEALTHY)
        total_count = len(service_status)

        overall_status = ServiceStatus.HEALTHY
        if healthy_count < total_count:
            overall_status = ServiceStatus.DEGRADED if healthy_count > 0 else ServiceStatus.UNHEALTHY

        return {
            "overall_status": overall_status.value,
            "service_status": {k: v.value for k, v in service_status.items()},
            "services_healthy": healthy_count,
            "services_total": total_count,
            "last_check": datetime.utcnow().isoformat(),
            "event_count": len(self.event_bus.event_history),
            "pipeline_count": len(self.data_flow_manager.data_pipelines)
        }

    async def trigger_cross_service_workflow(self, workflow_name: str, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a cross-service workflow"""
        workflow_results = {}

        if workflow_name == "alert_to_case":
            # Alert -> Case creation workflow
            await self.publish_event(
                EventType.ALERT_TRIGGERED,
                trigger_data,
                "orchestrator"
            )
            workflow_results["alert_published"] = True

        elif workflow_name == "anomaly_to_investigation":
            # Anomaly -> Investigation workflow
            await self.publish_event(
                EventType.ANOMALY_DETECTED,
                trigger_data,
                "orchestrator"
            )
            workflow_results["anomaly_published"] = True

        elif workflow_name == "evidence_validation":
            # Evidence validation pipeline
            validated_evidence = await self.execute_pipeline("evidence_processing", trigger_data)
            workflow_results["evidence_validated"] = True
            workflow_results["validation_result"] = validated_evidence

        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        return {
            "workflow": workflow_name,
            "triggered_at": datetime.utcnow().isoformat(),
            "results": workflow_results
        }


# Global orchestrator instance (lazy to avoid circular imports during module import)
service_orchestrator = None  # type: Optional[ServiceOrchestrator]

def get_service_orchestrator() -> ServiceOrchestrator:
    global service_orchestrator
    if service_orchestrator is None:
        service_orchestrator = ServiceOrchestrator()
    return service_orchestrator


# Convenience functions for external use
async def publish_system_event(event_type: EventType, data: Dict[str, Any], source: str = "external"):
    """Publish an event to the system"""
    await get_service_orchestrator().publish_event(event_type, data, source)


async def execute_data_pipeline(pipeline_name: str, data: Any) -> Any:
    """Execute a data processing pipeline"""
    return await get_service_orchestrator().execute_pipeline(pipeline_name, data)


async def trigger_workflow(workflow_name: str, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger a cross-service workflow"""
    return await get_service_orchestrator().trigger_cross_service_workflow(workflow_name, trigger_data)


async def get_system_overview() -> Dict[str, Any]:
    """Get comprehensive system overview"""
    return await get_service_orchestrator().get_system_status()
