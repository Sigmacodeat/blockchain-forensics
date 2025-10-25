"""
AI-Agent Tools für Institutionellen Rabatt & Verification
"""

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Tool Schemas
# ============================================================================

class CheckInstitutionalStatusInput(BaseModel):
    """Input for check_institutional_status tool"""
    user_id: int = Field(description="ID of the user to check")

class RequestVerificationInput(BaseModel):
    """Input for request_institutional_verification tool"""
    user_id: int = Field(description="ID of the user")
    organization_type: str = Field(description="Type of organization: police, detective, lawyer, government, exchange, other")
    organization_name: Optional[str] = Field(default=None, description="Name of the organization (optional)")

class CheckDiscountEligibilityInput(BaseModel):
    """Input for check_discount_eligibility tool"""
    email: str = Field(description="User's email address to check domain")
    organization_type: Optional[str] = Field(default=None, description="Type of organization")

# ============================================================================
# Trusted Domains for Auto-Verification
# ============================================================================

TRUSTED_DOMAINS = {
    'police': [
        'polizei.de',
        'polizei.bund.de',
        'bka.de',
        'lka.*.de',
        'fbi.gov',
        'police.uk',
        'police.gov.au',
        'rcmp-grc.gc.ca',
        'interpol.int',
        'europol.europa.eu'
    ],
    'government': [
        'bund.de',
        '.gov',
        '.gov.uk',
        '.gouv.fr',
        '.gob.es',
        '.gov.au',
        '.gc.ca',
        '.govt.nz'
    ],
    'detective': [
        # Meist privat, braucht manuelle Verification
    ],
    'lawyer': [
        # Meist privat, aber manche @staatsanwaltschaft.de
        'staatsanwaltschaft.de',
        'justiz.de'
    ]
}

def check_email_domain(email: str, organization_type: str) -> bool:
    """
    Check if email domain is trusted for auto-verification
    """
    domain = email.split('@')[1] if '@' in email else ''
    
    if not domain or organization_type not in TRUSTED_DOMAINS:
        return False
    
    trusted = TRUSTED_DOMAINS.get(organization_type, [])
    
    for pattern in trusted:
        if pattern.startswith('.') and domain.endswith(pattern):
            return True
        elif '*' in pattern:
            # Wildcard matching (z.B. lka.*.de)
            parts = pattern.split('*')
            if all(p in domain for p in parts if p):
                return True
        elif pattern in domain or domain.endswith(pattern):
            return True
    
    return False

# ============================================================================
# Tool Functions
# ============================================================================

async def check_institutional_status(user_id: int) -> dict:
    """
    Check user's institutional discount status and verification state
    """
    try:
        # Import hier um circular imports zu vermeiden
        from app.db.database import get_db
        
        async with get_db() as db:
            user = await db.execute(
                "SELECT organization_type, organization_name, "
                "institutional_discount_requested, institutional_discount_verified, "
                "verification_status, verified_at "
                "FROM users WHERE id = $1",
                user_id
            )
            
            if not user:
                return {
                    'error': 'User not found',
                    'has_discount': False
                }
            
            user = dict(user[0]) if user else {}
            
            # Status-Message generieren
            status_message = ""
            if user.get('institutional_discount_verified'):
                status_message = "✅ Institutional discount ACTIVE (10% off)"
            elif user.get('verification_status') == 'pending':
                status_message = "⏳ Verification PENDING - Admin review within 24-48h"
            elif user.get('verification_status') == 'rejected':
                status_message = "❌ Verification REJECTED - Please contact support"
            elif user.get('organization_type'):
                status_message = "💡 You can request 10% institutional discount"
            else:
                status_message = "ℹ️ No institutional discount requested"
            
            return {
                'has_institutional_discount': user.get('institutional_discount_verified', False),
                'organization_type': user.get('organization_type'),
                'organization_name': user.get('organization_name'),
                'verification_status': user.get('verification_status', 'none'),
                'discount_amount': '10%' if user.get('institutional_discount_verified') else '0%',
                'can_request': not user.get('institutional_discount_requested', False),
                'status_message': status_message,
                'verified_at': str(user.get('verified_at')) if user.get('verified_at') else None,
                'total_discount': '30%' if user.get('institutional_discount_verified') else '20%',
                'total_discount_info': '20% annual + 10% institutional' if user.get('institutional_discount_verified') else '20% annual only'
            }
            
    except Exception as e:
        logger.error(f"Error checking institutional status: {e}")
        return {
            'error': str(e),
            'has_discount': False
        }

async def request_institutional_verification(
    user_id: int,
    organization_type: str,
    organization_name: Optional[str] = None
) -> dict:
    """
    Start institutional verification process for user
    """
    try:
        from app.db.database import get_db
        
        # Validate organization_type
        valid_types = ['police', 'detective', 'lawyer', 'government', 'exchange', 'other']
        if organization_type not in valid_types:
            return {
                'error': f'Invalid organization_type. Must be one of: {", ".join(valid_types)}',
                'status': 'error'
            }
        
        async with get_db() as db:
            # Check if already requested
            existing = await db.execute(
                "SELECT institutional_discount_requested FROM users WHERE id = $1",
                user_id
            )
            
            if existing and existing[0]['institutional_discount_requested']:
                return {
                    'status': 'already_requested',
                    'message': 'Verification already requested. Check status with check_institutional_status.',
                    'verification_status': 'pending'
                }
            
            # Check email domain for auto-verification
            user_email = await db.execute(
                "SELECT email FROM users WHERE id = $1",
                user_id
            )
            
            auto_verified = False
            if user_email:
                email = user_email[0]['email']
                if check_email_domain(email, organization_type):
                    auto_verified = True
            
            # Update user
            await db.execute(
                """UPDATE users SET 
                   organization_type = $1,
                   organization_name = $2,
                   institutional_discount_requested = TRUE,
                   verification_status = $3,
                   institutional_discount_verified = $4,
                   verified_at = $5
                   WHERE id = $6""",
                organization_type,
                organization_name,
                'approved' if auto_verified else 'pending',
                auto_verified,
                'NOW()' if auto_verified else None,
                user_id
            )
            
            if auto_verified:
                # Send success email
                # await send_verification_email(user_id, status='approved')
                
                return {
                    'status': 'auto_approved',
                    'message': '🎉 Your email domain is trusted! Institutional discount automatically activated.',
                    'discount_active': True,
                    'discount_amount': '10%',
                    'total_discount': '30% (20% annual + 10% institutional)',
                    'verification_method': 'email_domain'
                }
            else:
                # Send pending email with upload instructions
                # await send_verification_email(user_id, status='pending')
                
                return {
                    'status': 'verification_started',
                    'message': 'Verification request submitted. Please upload verification documents.',
                    'verification_status': 'pending',
                    'upload_link': f'/verify/{user_id}',
                    'next_steps': [
                        '1. Upload your ID/License/Business documents',
                        '2. Admin reviews within 24-48 hours',
                        '3. Discount automatically activates upon approval'
                    ],
                    'upload_methods': [
                        'Chat: You can upload documents right here in the chat',
                        'Web: Visit the verification page',
                        'Email: Send documents to verify@sigmacode.io'
                    ]
                }
        
    except Exception as e:
        logger.error(f"Error requesting verification: {e}")
        return {
            'error': str(e),
            'status': 'error'
        }

async def check_discount_eligibility(
    email: str,
    organization_type: Optional[str] = None
) -> dict:
    """
    Check if email domain is eligible for auto-verification
    """
    try:
        domain = email.split('@')[1] if '@' in email else ''
        
        if not domain:
            return {
                'eligible': False,
                'reason': 'Invalid email format'
            }
        
        # Check für jede Org-Type
        eligible_for = []
        for org_type, domains in TRUSTED_DOMAINS.items():
            if check_email_domain(email, org_type):
                eligible_for.append(org_type)
        
        if eligible_for:
            return {
                'eligible': True,
                'eligible_for_types': eligible_for,
                'auto_verification': True,
                'message': f'✅ Your email domain ({domain}) is trusted! You can get instant verification for: {", ".join(eligible_for)}',
                'discount_amount': '10%',
                'next_step': 'Request verification with request_institutional_verification'
            }
        else:
            return {
                'eligible': True,
                'eligible_for_types': ['manual_verification'],
                'auto_verification': False,
                'message': f'Your email domain ({domain}) requires manual verification.',
                'upload_required': True,
                'accepted_documents': [
                    'Police: Badge/ID, Official Letter',
                    'Detective: Business License, Professional Registration',
                    'Lawyer: Bar Association ID, Court Registration',
                    'Government: Official ID, Department Letter'
                ],
                'discount_amount': '10% (after verification)',
                'next_step': 'Request verification and upload documents'
            }
        
    except Exception as e:
        logger.error(f"Error checking eligibility: {e}")
        return {
            'eligible': False,
            'error': str(e)
        }

# ============================================================================
# Register Tools
# ============================================================================

check_institutional_status_tool = StructuredTool.from_function(
    coroutine=check_institutional_status,
    name="check_institutional_status",
    description="""Check if user has institutional discount and verification status.
    
    Use this when:
    - User asks about their discount status
    - User wants to know if they have institutional discount
    - User asks about verification status
    
    Returns:
    - has_institutional_discount: boolean
    - verification_status: none/pending/approved/rejected
    - discount_amount: 10% or 0%
    - total_discount: 30% or 20%
    - status_message: human-readable status
    """,
    args_schema=CheckInstitutionalStatusInput
)

request_institutional_verification_tool = StructuredTool.from_function(
    coroutine=request_institutional_verification,
    name="request_institutional_verification",
    description="""Start institutional verification process for user.
    
    Use this when:
    - User wants to request institutional discount
    - User identifies as police/detective/lawyer/government
    - User wants to get 10% extra discount
    
    Organization types:
    - police: Police, Law Enforcement, Investigative Agencies
    - detective: Private Investigators, Investigation Agencies
    - lawyer: Lawyers, Prosecutors, Legal Professionals
    - government: Government Agencies, Public Sector
    - exchange: Crypto Exchanges, Financial Institutions
    - other: Other organizations
    
    Auto-verification:
    - If email domain is trusted (e.g. @polizei.de), instant approval
    - Otherwise, user needs to upload verification documents
    
    Returns:
    - status: auto_approved/verification_started/error
    - upload_link: if manual verification needed
    - next_steps: instructions for user
    """,
    args_schema=RequestVerificationInput
)

check_discount_eligibility_tool = StructuredTool.from_function(
    coroutine=check_discount_eligibility,
    name="check_discount_eligibility",
    description="""Check if user's email domain is eligible for auto-verification.
    
    Use this when:
    - User asks if they qualify for institutional discount
    - Before requesting verification
    - User wants to know if they get instant approval
    
    Returns:
    - eligible: boolean
    - auto_verification: boolean (instant approval if true)
    - accepted_documents: list (if manual verification needed)
    """,
    args_schema=CheckDiscountEligibilityInput
)

# Export
INSTITUTIONAL_VERIFICATION_TOOLS = [
    check_institutional_status_tool,
    request_institutional_verification_tool,
    check_discount_eligibility_tool
]
