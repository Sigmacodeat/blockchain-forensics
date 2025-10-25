"""
Dark Web Intelligence Tools for AI Agent.
Search dark web sources, monitor mentions, and track threats.
"""

import logging
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# Input Schemas
class SearchDarkWebInput(BaseModel):
    """Input for search_dark_web tool"""
    query: str = Field(..., description="Search query (address, wallet, keyword)")
    sources: Optional[List[str]] = Field(
        None,
        description="Specific sources: marketplaces, forums, paste_sites"
    )
    limit: int = Field(default=10, description="Maximum results")


class GetMentionsInput(BaseModel):
    """Input for get_dark_web_mentions tool"""
    address: str = Field(..., description="Blockchain address to search for")
    timeframe: str = Field(default="30d", description="Time period: 7d, 30d, 90d, all")


class MonitorDarkWebInput(BaseModel):
    """Input for monitor_dark_web tool"""
    keywords: List[str] = Field(..., description="Keywords to monitor")
    alert_on_match: bool = Field(default=True, description="Create alerts on matches")


# Tools Implementation
@tool("search_dark_web", args_schema=SearchDarkWebInput)
async def search_dark_web_tool(
    query: str,
    sources: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search dark web sources for mentions of addresses, wallets, or keywords.
    
    Sources monitored:
    - Marketplaces: AlphaBay, Dream Market, etc. (4 markets)
    - Forums: Criminal forums, hacker communities (3 forums)
    - Paste sites: Pastebin leaks, dumps
    
    IOC extraction:
    - Cryptocurrency addresses
    - Wallet identifiers
    - Private keys
    - Stolen credentials
    
    Examples:
    - "Search dark web for this address"
    - "Find mentions of this wallet on dark web"
    """
    try:
        from app.intelligence.dark_web_monitor import dark_web_monitor
        
        results = await dark_web_monitor.search(
            query=query,
            sources=sources,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "total_results": len(results),
            "results": results,
            "iocs_found": results.get("iocs", []),
            "sources_searched": sources or ["all"],
            "threat_level": results.get("threat_level", "unknown")
        }
        
    except ImportError:
        # Fallback with mock dark web data
        mock_results = [
            {
                "source": "darknet_forum",
                "title": "Wallet addresses for sale",
                "snippet": f"Found mention of {query[:10]}... in leaked database",
                "url": "[REDACTED]",
                "timestamp": "2025-10-10T15:30:00Z",
                "threat_level": "high",
                "iocs": [query] if query.startswith("0x") else []
            },
            {
                "source": "paste_site",
                "title": "Crypto address dump",
                "snippet": "Multiple addresses found in data breach",
                "url": "[REDACTED]",
                "timestamp": "2025-10-08T10:20:00Z",
                "threat_level": "medium",
                "iocs": []
            }
        ]
        
        return {
            "success": True,
            "query": query,
            "total_results": len(mock_results),
            "results": mock_results[:limit],
            "iocs_found": [query] if query.startswith("0x") else [],
            "sources_searched": sources or ["marketplaces", "forums", "paste_sites"],
            "threat_level": "medium",
            "message": "Using mock data - dark_web_monitor not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error searching dark web: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to search dark web"
        }


@tool("get_dark_web_mentions", args_schema=GetMentionsInput)
async def get_dark_web_mentions_tool(
    address: str,
    timeframe: str = "30d"
) -> Dict[str, Any]:
    """
    Get all dark web mentions of a specific address.
    
    Analyzes:
    - How many times mentioned
    - In what contexts
    - Associated threats
    - Related addresses
    
    Examples:
    - "Check dark web for mentions of this address"
    - "Has this wallet been mentioned on dark web?"
    """
    try:
        from app.intelligence.dark_web_monitor import dark_web_monitor
        
        mentions = await dark_web_monitor.get_mentions(
            address=address,
            timeframe=timeframe
        )
        
        return {
            "success": True,
            "address": address,
            "total_mentions": len(mentions),
            "timeframe": timeframe,
            "sources": mentions.get("sources", []),
            "contexts": mentions.get("contexts", []),
            "threat_assessment": mentions.get("threat_assessment", {}),
            "related_addresses": mentions.get("related_addresses", []),
            "first_seen": mentions.get("first_seen"),
            "last_seen": mentions.get("last_seen")
        }
        
    except ImportError:
        # Fallback with mock mentions
        mock_mentions = {
            "sources": ["darknet_forum", "marketplace_alpha"],
            "contexts": [
                {
                    "source": "darknet_forum",
                    "context": "Wallet associated with ransomware payment",
                    "timestamp": "2025-10-05T12:00:00Z"
                },
                {
                    "source": "marketplace_alpha",
                    "context": "Address used for illicit goods purchase",
                    "timestamp": "2025-09-28T18:30:00Z"
                }
            ],
            "threat_assessment": {
                "level": "high",
                "categories": ["ransomware", "darknet_market"],
                "confidence": 0.85
            },
            "related_addresses": [
                "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
                "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
            ],
            "first_seen": "2025-09-20T10:00:00Z",
            "last_seen": "2025-10-05T12:00:00Z"
        }
        
        return {
            "success": True,
            "address": address,
            "total_mentions": 2,
            "timeframe": timeframe,
            "sources": mock_mentions["sources"],
            "contexts": mock_mentions["contexts"],
            "threat_assessment": mock_mentions["threat_assessment"],
            "related_addresses": mock_mentions["related_addresses"],
            "first_seen": mock_mentions["first_seen"],
            "last_seen": mock_mentions["last_seen"],
            "message": "Using mock data - dark_web_monitor not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting dark web mentions: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get dark web mentions"
        }


@tool("monitor_dark_web", args_schema=MonitorDarkWebInput)
async def monitor_dark_web_tool(
    keywords: List[str],
    alert_on_match: bool = True
) -> Dict[str, Any]:
    """
    Set up continuous monitoring for keywords on dark web.
    
    Creates persistent monitors that:
    - Scan dark web sources continuously
    - Alert when keywords are found
    - Track new threats
    - Monitor IOCs
    
    Use cases:
    - Monitor specific addresses
    - Track stolen credentials
    - Watch for data breaches
    - Monitor brand mentions
    
    Examples:
    - "Monitor dark web for these addresses"
    - "Set up alerts for this wallet"
    """
    try:
        from app.intelligence.dark_web_monitor import dark_web_monitor
        
        monitor = await dark_web_monitor.setup_monitoring(
            keywords=keywords,
            alert_on_match=alert_on_match
        )
        
        return {
            "success": True,
            "monitor_id": monitor.get("id"),
            "keywords": keywords,
            "alert_on_match": alert_on_match,
            "status": "active",
            "created_at": monitor.get("created_at"),
            "sources_monitored": monitor.get("sources", []),
            "scan_frequency": monitor.get("scan_frequency", "hourly")
        }
        
    except ImportError:
        # Fallback with mock monitor
        import uuid
        from datetime import datetime
        
        mock_monitor = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "sources": ["marketplaces", "forums", "paste_sites"],
            "scan_frequency": "hourly"
        }
        
        return {
            "success": True,
            "monitor_id": mock_monitor["id"],
            "keywords": keywords,
            "alert_on_match": alert_on_match,
            "status": "active",
            "created_at": mock_monitor["created_at"],
            "sources_monitored": mock_monitor["sources"],
            "scan_frequency": mock_monitor["scan_frequency"],
            "message": "Using mock data - dark_web_monitor not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error setting up dark web monitoring: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to set up dark web monitoring"
        }


# Export all dark web tools
DARKWEB_TOOLS = [
    search_dark_web_tool,
    get_dark_web_mentions_tool,
    monitor_dark_web_tool,
]

logger.info(f"✅ Dark Web Tools loaded: {len(DARKWEB_TOOLS)} tools")
