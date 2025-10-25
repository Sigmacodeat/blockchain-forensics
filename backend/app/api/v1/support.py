"""
Support API Endpoints - Contact Form & Ticket Management
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
import logging

from app.services.support_service import support_service
from app.auth.dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support"])


class ContactFormRequest(BaseModel):
    """Contact form submission"""
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    subject: str = Field(..., min_length=5, max_length=200, description="Subject line")
    message: str = Field(..., min_length=10, max_length=5000, description="Message body")
    country: Optional[str] = Field(None, max_length=2, description="Country code (ISO 3166-1)")
    language: Optional[str] = Field("en", max_length=5, description="Language code (e.g., 'de', 'en')")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class TicketListResponse(BaseModel):
    """Ticket list response"""
    tickets: List[Dict[str, Any]]
    total: int
    page: int
    limit: int


@router.post("/contact", status_code=201)
async def submit_contact_form(
    request: Request,
    data: ContactFormRequest
) -> Dict[str, Any]:
    """
    Submit contact form / create support ticket
    Public endpoint - no authentication required
    
    Features:
    - Multi-language support (42 languages)
    - Country-based routing
    - AI-powered auto-replies
    - Priority classification
    - Email notifications
    """
    try:
        # Get client metadata
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        referrer = request.headers.get("referer")
        
        # Extract user_id if authenticated (optional)
        user_id = None
        try:
            user = await get_current_user(request)
            user_id = user.id if user else None
        except:
            pass  # Not authenticated, continue as guest
        
        # Submit ticket
        result = await support_service.submit_contact_form(
            name=data.name,
            email=data.email,
            subject=data.subject,
            message=data.message,
            country=data.country,
            language=data.language or "en",
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            referrer=referrer,
            metadata=data.metadata
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to submit ticket"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in contact form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets", dependencies=[Depends(require_admin)])
async def list_support_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    country: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> TicketListResponse:
    """
    List support tickets (Admin only)
    
    Filters:
    - status: open, in_progress, resolved, closed
    - priority: critical, high, medium, low
    - category: technical, billing, sales, general, feature_request
    - country: ISO 3166-1 alpha-2 code
    """
    try:
        offset = (page - 1) * limit
        
        tickets = await support_service.list_tickets(
            status=status,
            priority=priority,
            category=category,
            country=country,
            limit=limit,
            offset=offset
        )
        
        # Get total count (simplified)
        total = len(tickets)  # In production, do separate COUNT query
        
        return TicketListResponse(
            tickets=tickets,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/{ticket_id}", dependencies=[Depends(require_admin)])
async def get_ticket_details(ticket_id: str) -> Dict[str, Any]:
    """Get ticket details (Admin only)"""
    try:
        ticket = await support_service.get_ticket(ticket_id)
        
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        return ticket
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", dependencies=[Depends(require_admin)])
async def get_support_stats() -> Dict[str, Any]:
    """
    Get support statistics (Admin only)
    Returns metrics by priority, category, country, etc.
    """
    try:
        # Get all tickets (in production, optimize with aggregation queries)
        all_tickets = await support_service.list_tickets(limit=1000)
        
        # Calculate stats
        stats = {
            "total_tickets": len(all_tickets),
            "by_status": {},
            "by_priority": {},
            "by_category": {},
            "by_country": {},
            "by_language": {},
            "avg_response_time": "N/A"  # Placeholder
        }
        
        for ticket in all_tickets:
            # Status
            status = ticket.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Priority
            priority = ticket.get("priority", "unknown")
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Category
            category = ticket.get("category", "unknown")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # Country
            country = ticket.get("country") or "unknown"
            stats["by_country"][country] = stats["by_country"].get(country, 0) + 1
            
            # Language
            language = ticket.get("language", "unknown")
            stats["by_language"][language] = stats["by_language"].get(language, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
