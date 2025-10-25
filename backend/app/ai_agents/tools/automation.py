"""
Automation Tools for AI Agent.
Schedule monitoring, create alert rules, and automate workflows.
"""

import logging
from typing import List, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# Input Schemas
class ScheduleMonitoringInput(BaseModel):
    """Input for schedule_monitoring tool"""
    address: str = Field(..., description="Address to monitor")
    interval: str = Field(..., description="Check interval: 15m, 1h, 6h, 24h")
    conditions: Dict[str, Any] = Field(..., description="Trigger conditions")
    actions: List[str] = Field(..., description="Actions to take: alert, email, webhook")


class CreateAlertRuleInput(BaseModel):
    """Input for create_alert_rule tool"""
    name: str = Field(..., description="Rule name")
    condition_type: str = Field(..., description="Condition: risk_threshold, sanctions_hit, large_transfer, etc.")
    condition_params: Dict[str, Any] = Field(..., description="Condition parameters")
    actions: List[str] = Field(..., description="Actions: email, webhook, sms, slack")
    enabled: bool = Field(default=True, description="Enable rule immediately")


class AutomateWorkflowInput(BaseModel):
    """Input for automate_workflow tool"""
    workflow_name: str = Field(..., description="Workflow name")
    trigger: Dict[str, Any] = Field(..., description="Trigger configuration")
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps")


# Tools Implementation
@tool("schedule_monitoring", args_schema=ScheduleMonitoringInput)
async def schedule_monitoring_tool(
    address: str,
    interval: str,
    conditions: Dict[str, Any],
    actions: List[str]
) -> Dict[str, Any]:
    """
    Schedule automated monitoring of an address.
    
    Intervals:
    - 15m: Check every 15 minutes
    - 1h: Check every hour
    - 6h: Check every 6 hours
    - 24h: Check once per day
    
    Conditions:
    - risk_score_above: Trigger if risk score > threshold
    - new_transaction: Trigger on any new transaction
    - balance_change: Trigger on balance change
    - sanctions_hit: Trigger if sanctioned
    
    Actions:
    - alert: Create platform alert
    - email: Send email notification
    - webhook: Call webhook URL
    - sms: Send SMS (enterprise)
    
    Examples:
    - "Monitor this address every hour for high risk"
    - "Alert me if this address receives funds"
    """
    try:
        from app.services.automation_service import automation_service
        
        monitor = await automation_service.schedule_monitor(
            address=address,
            interval=interval,
            conditions=conditions,
            actions=actions
        )
        
        return {
            "success": True,
            "monitor_id": monitor.get("id"),
            "address": address,
            "interval": interval,
            "conditions": conditions,
            "actions": actions,
            "next_check": monitor.get("next_check"),
            "status": "active"
        }
        
    except ImportError:
        # Fallback with mock monitor
        import uuid
        from datetime import datetime, timedelta
        
        mock_monitor = {
            "id": str(uuid.uuid4()),
            "next_check": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        return {
            "success": True,
            "monitor_id": mock_monitor["id"],
            "address": address,
            "interval": interval,
            "conditions": conditions,
            "actions": actions,
            "next_check": mock_monitor["next_check"],
            "status": "active",
            "message": "Using mock data - automation_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling monitoring: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to schedule monitoring"
        }


@tool("create_alert_rule", args_schema=CreateAlertRuleInput)
async def create_alert_rule_tool(
    name: str,
    condition_type: str,
    condition_params: Dict[str, Any],
    actions: List[str],
    enabled: bool = True
) -> Dict[str, Any]:
    """
    Create a custom alert rule.
    
    Condition types:
    - risk_threshold: Alert if risk score exceeds value
    - sanctions_hit: Alert on sanctions list match
    - large_transfer: Alert on transfers > amount
    - mixer_usage: Alert on mixer interaction
    - defi_exposure: Alert on DeFi position changes
    - nft_transfer: Alert on NFT transfers
    
    Examples:
    - "Create alert rule for high risk addresses"
    - "Alert me when large transfers occur"
    """
    try:
        from app.services.automation_service import automation_service
        
        rule = await automation_service.create_alert_rule(
            name=name,
            condition_type=condition_type,
            condition_params=condition_params,
            actions=actions,
            enabled=enabled
        )
        
        return {
            "success": True,
            "rule_id": rule.get("id"),
            "name": name,
            "condition_type": condition_type,
            "actions": actions,
            "enabled": enabled,
            "created_at": rule.get("created_at"),
            "triggers_count": 0
        }
        
    except ImportError:
        # Fallback with mock rule
        import uuid
        from datetime import datetime
        
        mock_rule = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "rule_id": mock_rule["id"],
            "name": name,
            "condition_type": condition_type,
            "actions": actions,
            "enabled": enabled,
            "created_at": mock_rule["created_at"],
            "triggers_count": 0,
            "message": "Using mock data - automation_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create alert rule"
        }


@tool("automate_workflow", args_schema=AutomateWorkflowInput)
async def automate_workflow_tool(
    workflow_name: str,
    trigger: Dict[str, Any],
    steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create an automated workflow with multiple steps.
    
    Workflow examples:
    1. High-Risk Detection Workflow:
       - Trigger: Risk score > 0.7
       - Steps: Trace funds → Create case → Send alert → Generate report
    
    2. Sanctions Screening Workflow:
       - Trigger: New transaction
       - Steps: Screen address → Check labels → Alert if match
    
    3. Investigation Workflow:
       - Trigger: Manual trigger
       - Steps: Trace → Analyze → Cluster → Report
    
    Step types:
    - trace_address: Run transaction trace
    - create_case: Create investigation case
    - send_alert: Send notification
    - generate_report: Create report
    - call_webhook: External integration
    
    Examples:
    - "Create workflow for high-risk addresses"
    - "Automate investigation process"
    """
    try:
        from app.services.automation_service import automation_service
        
        workflow = await automation_service.create_workflow(
            name=workflow_name,
            trigger=trigger,
            steps=steps
        )
        
        return {
            "success": True,
            "workflow_id": workflow.get("id"),
            "name": workflow_name,
            "trigger": trigger,
            "steps_count": len(steps),
            "status": "active",
            "executions_count": 0,
            "created_at": workflow.get("created_at")
        }
        
    except ImportError:
        # Fallback with mock workflow
        import uuid
        from datetime import datetime
        
        mock_workflow = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "workflow_id": mock_workflow["id"],
            "name": workflow_name,
            "trigger": trigger,
            "steps_count": len(steps),
            "status": "active",
            "executions_count": 0,
            "created_at": mock_workflow["created_at"],
            "message": "Using mock data - automation_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create workflow"
        }


# Export all automation tools
AUTOMATION_TOOLS = [
    schedule_monitoring_tool,
    create_alert_rule_tool,
    automate_workflow_tool,
]

logger.info(f"✅ Automation Tools loaded: {len(AUTOMATION_TOOLS)} tools")
