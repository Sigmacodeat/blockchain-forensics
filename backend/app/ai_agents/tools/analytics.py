"""
Analytics Tools for AI Agent.
Provides platform statistics, trends, and insights.
"""

import logging
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# Input Schemas
class PlatformStatsInput(BaseModel):
    """Input for get_platform_statistics tool"""
    timeframe: str = Field(default="30d", description="Time period: 24h, 7d, 30d, 90d, 1y, all")
    metrics: Optional[List[str]] = Field(
        None, 
        description="Specific metrics to retrieve (all if not specified)"
    )


class RiskTrendsInput(BaseModel):
    """Input for get_risk_trends tool"""
    timeframe: str = Field(default="30d", description="Time period: 24h, 7d, 30d, 90d")
    granularity: str = Field(default="daily", description="Granularity: hourly, daily, weekly")


class TopRiskAddressesInput(BaseModel):
    """Input for get_top_risk_addresses tool"""
    limit: int = Field(default=10, description="Number of addresses to return")
    timeframe: str = Field(default="30d", description="Time period")
    min_risk_score: float = Field(default=0.7, description="Minimum risk score (0-1)")


class AlertStatsInput(BaseModel):
    """Input for get_alert_statistics tool"""
    timeframe: str = Field(default="30d", description="Time period")
    group_by: str = Field(default="type", description="Group by: type, severity, status")


class ComparePeriodsInput(BaseModel):
    """Input for compare_periods tool"""
    period1: str = Field(..., description="First period (YYYY-MM-DD:YYYY-MM-DD)")
    period2: str = Field(..., description="Second period (YYYY-MM-DD:YYYY-MM-DD)")
    metrics: List[str] = Field(
        default=["traces", "cases", "alerts", "risk_score"],
        description="Metrics to compare"
    )


# Tools Implementation
@tool("get_platform_statistics", args_schema=PlatformStatsInput)
async def get_platform_statistics_tool(
    timeframe: str = "30d",
    metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get platform-wide statistics and metrics.
    
    Available metrics:
    - total_traces: Number of transaction traces
    - total_cases: Number of investigation cases
    - addresses_analyzed: Unique addresses analyzed
    - alerts_triggered: Total alerts
    - high_risk_detected: High-risk addresses found
    - avg_risk_score: Average risk score
    
    Examples:
    - "Show me platform statistics for the last 30 days"
    - "What are our key metrics this week?"
    """
    try:
        from app.services.analytics_service import analytics_service
        
        stats = await analytics_service.get_platform_stats(
            timeframe=timeframe,
            metrics=metrics
        )
        
        return {
            "success": True,
            "timeframe": timeframe,
            "stats": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except ImportError:
        # Fallback with mock data
        return {
            "success": True,
            "timeframe": timeframe,
            "stats": {
                "total_traces": 1250,
                "total_cases": 87,
                "addresses_analyzed": 5430,
                "alerts_triggered": 156,
                "high_risk_detected": 23,
                "avg_risk_score": 0.34
            },
            "message": "Using mock data - analytics_service not yet implemented",
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting platform stats: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get platform statistics"
        }


@tool("get_risk_trends", args_schema=RiskTrendsInput)
async def get_risk_trends_tool(
    timeframe: str = "30d",
    granularity: str = "daily"
) -> Dict[str, Any]:
    """
    Analyze risk trends over time.
    Shows how many high-risk addresses were detected per period.
    
    Granularity options:
    - hourly: Data points every hour
    - daily: Data points every day
    - weekly: Data points every week
    
    Examples:
    - "Show me risk trends for the last week"
    - "How has risk evolved over the past month?"
    """
    try:
        from app.services.analytics_service import analytics_service
        
        trends = await analytics_service.get_risk_trends(
            timeframe=timeframe,
            granularity=granularity
        )
        
        return {
            "success": True,
            "timeframe": timeframe,
            "granularity": granularity,
            "trends": trends,
            "summary": {
                "avg_risk_score": trends.get("avg", 0.0),
                "highest_period": trends.get("peak", "N/A"),
                "trend_direction": trends.get("direction", "stable")
            }
        }
        
    except ImportError:
        # Fallback with mock trend data
        mock_trends = {
            "data_points": [
                {"date": "2025-10-01", "avg_risk": 0.32, "high_risk_count": 15},
                {"date": "2025-10-08", "avg_risk": 0.38, "high_risk_count": 21},
                {"date": "2025-10-15", "avg_risk": 0.35, "high_risk_count": 18},
            ],
            "avg": 0.35,
            "peak": "2025-10-08",
            "direction": "increasing"
        }
        
        return {
            "success": True,
            "timeframe": timeframe,
            "granularity": granularity,
            "trends": mock_trends,
            "summary": {
                "avg_risk_score": mock_trends["avg"],
                "highest_period": mock_trends["peak"],
                "trend_direction": mock_trends["direction"]
            },
            "message": "Using mock data - analytics_service not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error getting risk trends: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get risk trends"
        }


@tool("get_top_risk_addresses", args_schema=TopRiskAddressesInput)
async def get_top_risk_addresses_tool(
    limit: int = 10,
    timeframe: str = "30d",
    min_risk_score: float = 0.7
) -> Dict[str, Any]:
    """
    Get the highest-risk addresses discovered recently.
    
    Useful for:
    - Identifying emerging threats
    - Prioritizing investigations
    - Monitoring high-risk entities
    
    Examples:
    - "Show me the top 10 riskiest addresses"
    - "What are the highest risk addresses this month?"
    """
    try:
        from app.services.analytics_service import analytics_service
        
        addresses = await analytics_service.get_top_risk_addresses(
            limit=limit,
            timeframe=timeframe,
            min_risk_score=min_risk_score
        )
        
        return {
            "success": True,
            "total": len(addresses),
            "timeframe": timeframe,
            "min_risk_score": min_risk_score,
            "addresses": addresses
        }
        
    except ImportError:
        # Fallback with mock addresses
        mock_addresses = [
            {
                "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "risk_score": 0.92,
                "labels": ["mixer", "sanctioned"],
                "first_seen": "2025-10-01T10:30:00Z"
            },
            {
                "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "risk_score": 0.85,
                "labels": ["scam", "phishing"],
                "first_seen": "2025-10-05T14:20:00Z"
            }
        ]
        
        return {
            "success": True,
            "total": len(mock_addresses),
            "timeframe": timeframe,
            "min_risk_score": min_risk_score,
            "addresses": mock_addresses[:limit],
            "message": "Using mock data - analytics_service not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error getting top risk addresses: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get top risk addresses"
        }


@tool("get_alert_statistics", args_schema=AlertStatsInput)
async def get_alert_statistics_tool(
    timeframe: str = "30d",
    group_by: str = "type"
) -> Dict[str, Any]:
    """
    Get alert statistics grouped by various dimensions.
    
    Group by options:
    - type: Group by alert type (high_risk, sanctioned, mixer, etc.)
    - severity: Group by severity (critical, high, medium, low)
    - status: Group by status (open, acknowledged, resolved)
    
    Examples:
    - "Show me alert statistics by type"
    - "How many alerts by severity this month?"
    """
    try:
        from app.services.analytics_service import analytics_service
        
        stats = await analytics_service.get_alert_statistics(
            timeframe=timeframe,
            group_by=group_by
        )
        
        return {
            "success": True,
            "timeframe": timeframe,
            "group_by": group_by,
            "stats": stats
        }
        
    except ImportError:
        # Fallback with mock stats
        if group_by == "type":
            mock_stats = {
                "high_risk": {"count": 45, "resolved": 32},
                "sanctioned": {"count": 12, "resolved": 12},
                "mixer": {"count": 28, "resolved": 15},
                "large_transfer": {"count": 67, "resolved": 60}
            }
        elif group_by == "severity":
            mock_stats = {
                "critical": {"count": 8, "resolved": 5},
                "high": {"count": 34, "resolved": 28},
                "medium": {"count": 89, "resolved": 75},
                "low": {"count": 21, "resolved": 21}
            }
        else:  # status
            mock_stats = {
                "open": 35,
                "acknowledged": 67,
                "resolved": 50
            }
        
        return {
            "success": True,
            "timeframe": timeframe,
            "group_by": group_by,
            "stats": mock_stats,
            "message": "Using mock data - analytics_service not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get alert statistics"
        }


@tool("compare_periods", args_schema=ComparePeriodsInput)
async def compare_periods_tool(
    period1: str,
    period2: str,
    metrics: List[str] = ["traces", "cases", "alerts", "risk_score"]
) -> Dict[str, Any]:
    """
    Compare metrics between two time periods.
    
    Period format: "YYYY-MM-DD:YYYY-MM-DD"
    
    Available metrics:
    - traces: Number of traces
    - cases: Number of cases
    - alerts: Number of alerts
    - risk_score: Average risk score
    - addresses: Unique addresses analyzed
    
    Examples:
    - "Compare October vs September metrics"
    - "How do this month's stats compare to last month?"
    """
    try:
        from app.services.analytics_service import analytics_service
        
        comparison = await analytics_service.compare_periods(
            period1=period1,
            period2=period2,
            metrics=metrics
        )
        
        return {
            "success": True,
            "period1": period1,
            "period2": period2,
            "comparison": comparison,
            "changes": comparison.get("changes", {})
        }
        
    except ImportError:
        # Fallback with mock comparison
        mock_comparison = {
            "period1_data": {
                "traces": 450,
                "cases": 32,
                "alerts": 78,
                "risk_score": 0.34
            },
            "period2_data": {
                "traces": 520,
                "cases": 28,
                "alerts": 92,
                "risk_score": 0.38
            },
            "changes": {
                "traces": "+15.6%",
                "cases": "-12.5%",
                "alerts": "+17.9%",
                "risk_score": "+11.8%"
            }
        }
        
        return {
            "success": True,
            "period1": period1,
            "period2": period2,
            "comparison": mock_comparison,
            "changes": mock_comparison["changes"],
            "message": "Using mock data - analytics_service not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error comparing periods: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to compare periods"
        }


# Export all analytics tools
ANALYTICS_TOOLS = [
    get_platform_statistics_tool,
    get_risk_trends_tool,
    get_top_risk_addresses_tool,
    get_alert_statistics_tool,
    compare_periods_tool,
]

logger.info(f"✅ Analytics Tools loaded: {len(ANALYTICS_TOOLS)} tools")
