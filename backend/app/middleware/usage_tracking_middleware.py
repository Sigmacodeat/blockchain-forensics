"""
Usage-Tracking-Middleware
===========================

Tracked automatisch alle API-Calls und enforced Quotas
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.services.usage_tracking import usage_tracking_service
import logging
import time

logger = logging.getLogger(__name__)


# ============================================================================
# ENDPOINT-TO-FEATURE MAPPING
# ============================================================================

ENDPOINT_TO_FEATURE = {
    "/api/v1/trace/start": "trace_start",
    "/api/v1/trace/expand": "trace_expand",
    "/api/v1/agent/query": "ai_agent_query",
    "/api/v1/chat": "ai_agent_query",
    "/api/v1/graph/nodes": "graph_query",
    "/api/v1/graph/subgraph": "graph_query",
    "/api/v1/graph/cross-chain": "graph_query",
    "/api/v1/patterns/detect": "pattern_detection",
    "/api/v1/wallet-scanner/scan/addresses": "wallet_scan",
    "/api/v1/wallet-scanner/scan/bulk": "wallet_scan",
    "/api/v1/enrich/risk-score": "risk_score",
    "/api/v1/risk/address": "risk_score",
    "/api/v1/risk/stream": "risk_score",
    "/api/v1/kyt/analyze": "kyt_analyze",
    "/api/v1/threat-intel/enrich": "threat_enrich",
    "/api/v1/threat-intel/query": "threat_query",
    "/api/v1/threat-intel/darkweb": "darkweb_search",
    "/api/v1/cases": "case_create",  # POST only
    "/api/v1/reports": "report_generate"
}


# Whitelist: Endpunkte die NICHT getrackt werden
EXCLUDED_PATHS = [
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/static",
    "/api/v1/usage",  # Usage-Endpunkte selbst
    "/api/v1/billing",  # Billing nicht tracken
    "/api/v1/auth",  # Auth nicht tracken
]


# ============================================================================
# USAGE-TRACKING-MIDDLEWARE
# ============================================================================

class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware für automatisches Usage-Tracking
    
    Features:
    - Auto-Tracking aller API-Calls
    - Quota-Enforcement BEFORE Request
    - Feature-spezifische Token-Kosten
    - Graceful Degradation (bei Redis-Fehler)
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Dispatch-Methode der Middleware
        
        Flow:
        1. Check ob Endpoint tracked werden soll
        2. Check User-Auth
        3. Check Quota BEFORE Request
        4. Wenn OK: Request durchlassen
        5. Wenn Success: Track Usage AFTER Request
        """
        
        # Check ob Endpoint getrackt werden soll
        path = request.url.path
        
        # Whitelist-Check
        if any(path.startswith(excluded) for excluded in EXCLUDED_PATHS):
            return await call_next(request)
        
        # Feature ermitteln
        feature = None
        for endpoint, feat in ENDPOINT_TO_FEATURE.items():
            if path.startswith(endpoint):
                feature = feat
                break
        
        # Kein Feature gefunden = nicht tracken
        if not feature:
            return await call_next(request)
        
        # User aus Request-State holen (gesetzt von Auth-Middleware)
        user = getattr(request.state, "user", None)
        
        if not user:
            # Kein User = nicht tracken (evtl. public endpoint)
            return await call_next(request)
        
        user_id = user.get("user_id") or user.get("id")
        plan = user.get("plan", "community")
        
        # ========================================================================
        # QUOTA-CHECK BEFORE REQUEST
        # ========================================================================
        
        try:
            can_proceed = await usage_tracking_service.check_quota(user_id, plan)
            
            if not can_proceed:
                logger.warning(f"Quota exceeded for user {user_id} (plan: {plan})")
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Monthly quota exceeded. Please upgrade your plan or wait for quota reset.",
                        "error_code": "QUOTA_EXCEEDED",
                        "upgrade_url": "/billing/upgrade",
                        "plan": plan
                    },
                    headers={
                        "Retry-After": "3600",  # 1 hour
                        "X-RateLimit-Exceeded": "true"
                    }
                )
        
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            # Fail-open: Bei Fehler Request durchlassen
        
        # ========================================================================
        # REQUEST DURCHLASSEN
        # ========================================================================
        
        response = await call_next(request)
        
        # ========================================================================
        # TRACK USAGE AFTER REQUEST (nur bei Success)
        # ========================================================================
        
        if response.status_code < 400:
            try:
                metadata = {
                    "endpoint": path,
                    "method": request.method,
                    "status_code": response.status_code
                }
                
                await usage_tracking_service.track_api_call(
                    user_id=user_id,
                    feature=feature,
                    metadata=metadata
                )
            
            except Exception as e:
                logger.error(f"Error tracking usage: {e}")
                # Non-fatal: Response trotzdem zurückgeben
        
        return response
