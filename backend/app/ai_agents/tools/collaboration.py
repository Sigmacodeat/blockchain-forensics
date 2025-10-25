"""
Collaboration Tools for AI Agent.
Enable team collaboration, sharing, and commenting on investigations.
"""

import logging
from typing import Optional, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# Input Schemas
class InviteTeamMemberInput(BaseModel):
    """Input for invite_team_member tool"""
    email: str = Field(..., description="Email address of team member")
    role: str = Field(..., description="Role: admin, analyst, viewer")
    case_id: Optional[str] = Field(None, description="Specific case to share (optional)")


class ShareInvestigationInput(BaseModel):
    """Input for share_investigation tool"""
    investigation_id: str = Field(..., description="Case or trace ID to share")
    with_user: str = Field(..., description="User email or ID")
    permissions: str = Field(default="view", description="Permissions: view, edit, admin")


class CommentOnCaseInput(BaseModel):
    """Input for comment_on_case tool"""
    case_id: str = Field(..., description="Case ID")
    comment: str = Field(..., description="Comment text")
    mention_users: Optional[list] = Field(None, description="Users to mention/notify")


# Tools Implementation
@tool("invite_team_member", args_schema=InviteTeamMemberInput)
async def invite_team_member_tool(
    email: str,
    role: str,
    case_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invite a team member to collaborate.
    
    Roles:
    - admin: Full access, can manage team
    - analyst: Can create cases, run investigations
    - viewer: Read-only access
    - auditor: View + export capabilities
    
    Use cases:
    - Add team members to organization
    - Share specific cases
    - Collaborate on investigations
    - Compliance oversight
    
    Examples:
    - "Invite analyst@company.com as an analyst"
    - "Add a viewer to this case"
    """
    try:
        from app.services.collaboration_service import collaboration_service
        
        invitation = await collaboration_service.invite_member(
            email=email,
            role=role,
            case_id=case_id
        )
        
        return {
            "success": True,
            "invitation_id": invitation.get("id"),
            "email": email,
            "role": role,
            "case_id": case_id,
            "status": "pending",
            "expires_at": invitation.get("expires_at"),
            "invitation_link": invitation.get("link")
        }
        
    except ImportError:
        # Fallback with mock invitation
        import uuid
        from datetime import datetime, timedelta
        
        mock_invitation = {
            "id": str(uuid.uuid4()),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "link": f"https://app.example.com/invite/{uuid.uuid4()}"
        }
        
        return {
            "success": True,
            "invitation_id": mock_invitation["id"],
            "email": email,
            "role": role,
            "case_id": case_id,
            "status": "pending",
            "expires_at": mock_invitation["expires_at"],
            "invitation_link": mock_invitation["link"],
            "message": "Using mock data - collaboration_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error inviting team member: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to invite team member"
        }


@tool("share_investigation", args_schema=ShareInvestigationInput)
async def share_investigation_tool(
    investigation_id: str,
    with_user: str,
    permissions: str = "view"
) -> Dict[str, Any]:
    """
    Share an investigation with another user.
    
    Permissions levels:
    - view: Read-only access
    - comment: View + add comments
    - edit: View + comment + modify
    - admin: Full control
    
    Sharing options:
    - Individual cases
    - Trace results
    - Reports
    - Alert configurations
    
    Examples:
    - "Share this case with analyst@company.com"
    - "Give edit access to this investigation"
    """
    try:
        from app.services.collaboration_service import collaboration_service
        
        share = await collaboration_service.share_investigation(
            investigation_id=investigation_id,
            with_user=with_user,
            permissions=permissions
        )
        
        return {
            "success": True,
            "share_id": share.get("id"),
            "investigation_id": investigation_id,
            "shared_with": with_user,
            "permissions": permissions,
            "shared_at": share.get("shared_at"),
            "access_link": share.get("access_link")
        }
        
    except ImportError:
        # Fallback with mock share
        import uuid
        from datetime import datetime
        
        mock_share = {
            "id": str(uuid.uuid4()),
            "shared_at": datetime.utcnow().isoformat(),
            "access_link": f"https://app.example.com/shared/{uuid.uuid4()}"
        }
        
        return {
            "success": True,
            "share_id": mock_share["id"],
            "investigation_id": investigation_id,
            "shared_with": with_user,
            "permissions": permissions,
            "shared_at": mock_share["shared_at"],
            "access_link": mock_share["access_link"],
            "message": "Using mock data - collaboration_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error sharing investigation: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to share investigation"
        }


@tool("comment_on_case", args_schema=CommentOnCaseInput)
async def comment_on_case_tool(
    case_id: str,
    comment: str,
    mention_users: Optional[list] = None
) -> Dict[str, Any]:
    """
    Add a comment to a case.
    
    Features:
    - Mention team members (@username)
    - Attach evidence
    - Thread discussions
    - Notifications
    
    Use cases:
    - Document findings
    - Ask questions
    - Provide updates
    - Request review
    
    Examples:
    - "Add comment: Found suspicious transaction"
    - "Comment on case: Need analyst review @john"
    """
    try:
        from app.services.collaboration_service import collaboration_service
        
        comment_obj = await collaboration_service.add_comment(
            case_id=case_id,
            comment=comment,
            mention_users=mention_users or []
        )
        
        return {
            "success": True,
            "comment_id": comment_obj.get("id"),
            "case_id": case_id,
            "comment": comment,
            "mentioned_users": mention_users or [],
            "created_at": comment_obj.get("created_at"),
            "notifications_sent": len(mention_users or [])
        }
        
    except ImportError:
        # Fallback with mock comment
        import uuid
        from datetime import datetime
        
        mock_comment = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "comment_id": mock_comment["id"],
            "case_id": case_id,
            "comment": comment,
            "mentioned_users": mention_users or [],
            "created_at": mock_comment["created_at"],
            "notifications_sent": len(mention_users or []),
            "message": "Using mock data - collaboration_service not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to add comment"
        }


# Export all collaboration tools
COLLAB_TOOLS = [
    invite_team_member_tool,
    share_investigation_tool,
    comment_on_case_tool,
]

logger.info(f"✅ Collaboration Tools loaded: {len(COLLAB_TOOLS)} tools")
