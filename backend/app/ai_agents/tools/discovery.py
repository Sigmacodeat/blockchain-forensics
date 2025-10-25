"""
Discovery Tools for AI Agent.
Enable agent to discover available tools and API endpoints.
Meta-tools that provide self-awareness.
"""

import logging
from typing import Optional, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# Input Schemas
class DiscoverToolsInput(BaseModel):
    """Input for discover_tools tool"""
    category: Optional[str] = Field(None, description="Filter by category: case, reporting, analytics, etc.")
    search: Optional[str] = Field(None, description="Search in tool names/descriptions")


class APIExplorerInput(BaseModel):
    """Input for api_explorer tool"""
    endpoint: Optional[str] = Field(None, description="Filter by endpoint path")
    method: Optional[str] = Field(None, description="Filter by HTTP method: GET, POST, PUT, DELETE")


# Tools Implementation
@tool("discover_tools", args_schema=DiscoverToolsInput)
async def discover_tools_tool(
    category: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Discover available tools that the agent can use.
    
    This is a meta-tool that provides self-awareness.
    Agent can query what capabilities it has.
    
    Categories:
    - case: Case management tools
    - reporting: Report generation tools
    - analytics: Analytics and statistics tools
    - defi: DeFi analysis tools
    - nft: NFT analysis tools
    - darkweb: Dark web intelligence tools
    - automation: Automation and scheduling tools
    - collaboration: Team collaboration tools
    - forensics: Forensic analysis tools (trace, risk, etc.)
    
    Examples:
    - "What tools do I have?"
    - "Show me all case management tools"
    - "What tools are available for DeFi analysis?"
    """
    try:
        from app.ai_agents.tools import ALL_TOOLS
        
        tools_info = []
        
        for tool in ALL_TOOLS:
            tool_name = getattr(tool, "name", "unknown")
            tool_desc = getattr(tool, "description", "")
            
            # Apply category filter
            if category and category.lower() not in tool_name.lower():
                continue
            
            # Apply search filter
            if search and search.lower() not in tool_name.lower() and search.lower() not in tool_desc.lower():
                continue
            
            # Extract category from tool name (first word before underscore)
            tool_category = tool_name.split("_")[0] if "_" in tool_name else "other"
            
            # Get parameters if available
            params = []
            if hasattr(tool, "args_schema"):
                schema = tool.args_schema
                if hasattr(schema, "__fields__"):
                    params = list(schema.__fields__.keys())
            
            tools_info.append({
                "name": tool_name,
                "description": tool_desc[:200] if tool_desc else "No description",
                "category": tool_category,
                "params": params
            })
        
        # Group by category
        categories = {}
        for t in tools_info:
            cat = t["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(t)
        
        return {
            "success": True,
            "total_tools": len(tools_info),
            "tools": tools_info,
            "categories": {cat: len(tools) for cat, tools in categories.items()},
            "filtered_by": {
                "category": category,
                "search": search
            }
        }
        
    except Exception as e:
        logger.error(f"Error discovering tools: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to discover tools"
        }


@tool("api_explorer", args_schema=APIExplorerInput)
async def api_explorer_tool(
    endpoint: Optional[str] = None,
    method: Optional[str] = None
) -> Dict[str, Any]:
    """
    Explore available API endpoints.
    
    This meta-tool allows the agent to discover all API endpoints
    available in the platform.
    
    Use cases:
    - Find specific endpoints
    - Discover API capabilities
    - Generate API documentation
    - Learn about available integrations
    
    Examples:
    - "What APIs are available?"
    - "Show me all case-related endpoints"
    - "What POST endpoints exist?"
    """
    try:
        endpoints = []
        
        # Import all routers from API
        try:
            from app.api.v1 import (
                agent, cases, forensics, trace, alerts,
                compliance, analytics, chat, risk
            )
            
            routers = [
                ("agent", agent.router),
                ("cases", cases.router),
                ("forensics", forensics.router),
                ("trace", trace.router),
                ("alerts", alerts.router),
                ("compliance", compliance.router),
                ("analytics", analytics.router),
                ("chat", chat.router),
                ("risk", risk.router),
            ]
            
            for router_name, router in routers:
                if not hasattr(router, "routes"):
                    continue
                
                for route in router.routes:
                    route_path = getattr(route, "path", "")
                    route_methods = getattr(route, "methods", set())
                    route_name = getattr(route, "name", "")
                    
                    # Apply filters
                    if endpoint and endpoint not in route_path:
                        continue
                    
                    if method and method.upper() not in route_methods:
                        continue
                    
                    endpoints.append({
                        "path": route_path,
                        "methods": list(route_methods),
                        "name": route_name,
                        "module": router_name
                    })
        
        except ImportError as e:
            logger.warning(f"Could not import all routers: {e}")
            # Return mock data
            endpoints = [
                {
                    "path": "/api/v1/agent/investigate",
                    "methods": ["POST"],
                    "name": "investigate",
                    "module": "agent"
                },
                {
                    "path": "/api/v1/cases",
                    "methods": ["GET", "POST"],
                    "name": "cases",
                    "module": "cases"
                },
                {
                    "path": "/api/v1/trace",
                    "methods": ["POST"],
                    "name": "trace",
                    "module": "trace"
                }
            ]
        
        # Group by module
        by_module = {}
        for ep in endpoints:
            module = ep["module"]
            if module not in by_module:
                by_module[module] = []
            by_module[module].append(ep)
        
        return {
            "success": True,
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
            "by_module": {module: len(eps) for module, eps in by_module.items()},
            "filtered_by": {
                "endpoint": endpoint,
                "method": method
            }
        }
        
    except Exception as e:
        logger.error(f"Error exploring APIs: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to explore APIs"
        }


# Export all discovery tools
DISCOVERY_TOOLS = [
    discover_tools_tool,
    api_explorer_tool,
]

logger.info(f"✅ Discovery Tools loaded: {len(DISCOVERY_TOOLS)} tools")
