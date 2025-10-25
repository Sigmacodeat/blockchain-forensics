"""
AppSumo License Integration
Handles license verification, activation, and plan management
"""

from typing import Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import hashlib
import re

class License(BaseModel):
    license_key: str
    email: str
    plan_tier: int  # 1, 2, or 3
    product_id: str
    status: str = "active"  # active, cancelled, refunded
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class PlanLimits(BaseModel):
    tier: int
    features: Dict[str, bool]
    limits: Dict[str, int]

# Plan Limits Configuration
PLAN_LIMITS = {
    1: PlanLimits(
        tier=1,
        features={
            "basic_features": True,
            "advanced_features": False,
            "api_access": False,
            "white_label": False,
            "priority_support": False
        },
        limits={
            "api_calls_per_day": 100,
            "saved_items": 10,
            "team_members": 1,
            "websites": 1
        }
    ),
    2: PlanLimits(
        tier=2,
        features={
            "basic_features": True,
            "advanced_features": True,
            "api_access": False,
            "white_label": True,
            "priority_support": True
        },
        limits={
            "api_calls_per_day": 500,
            "saved_items": 50,
            "team_members": 3,
            "websites": 3
        }
    ),
    3: PlanLimits(
        tier=3,
        features={
            "basic_features": True,
            "advanced_features": True,
            "api_access": True,
            "white_label": True,
            "priority_support": True
        },
        limits={
            "api_calls_per_day": -1,  # Unlimited
            "saved_items": -1,  # Unlimited
            "team_members": 10,
            "websites": 10
        }
    )
}

def validate_license_format(license_key: str) -> bool:
    """Validate license key format: XXXX-XXXX-XXXX-XXXX"""
    pattern = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
    return bool(re.match(pattern, license_key))

def extract_tier_from_license(license_key: str) -> int:
    """Extract tier from license key (simplified - replace with real logic)"""
    # In production: API call to AppSumo or database lookup
    # For now: derive from key (T1/T2/T3 in key)
    if "T1" in license_key or license_key.endswith("1"):
        return 1
    elif "T2" in license_key or license_key.endswith("2"):
        return 2
    elif "T3" in license_key or license_key.endswith("3"):
        return 3
    return 1  # Default to tier 1

async def verify_license(license_key: str, product_id: str) -> Optional[License]:
    """
    Verify AppSumo license key
    
    In production: Call AppSumo API or check database
    For MVP: Simple validation
    """
    if not validate_license_format(license_key):
        return None
    
    # Extract tier
    tier = extract_tier_from_license(license_key)
    
    # Create license object
    license = License(
        license_key=license_key,
        email="",  # Will be filled during activation
        plan_tier=tier,
        product_id=product_id,
        status="active",
        activated_at=datetime.utcnow()
    )
    
    return license

async def activate_license(license_key: str, email: str, product_id: str) -> Optional[Dict]:
    """
    Activate AppSumo license for a user
    
    Returns user data with plan info
    """
    # Verify license
    license = await verify_license(license_key, product_id)
    if not license:
        return None
    
    # Get plan limits
    limits = PLAN_LIMITS.get(license.plan_tier)
    if not limits:
        return None
    
    # Create user data
    user_data = {
        "email": email,
        "license_key": license_key,
        "plan": f"tier_{license.plan_tier}",
        "plan_tier": license.plan_tier,
        "features": limits.features,
        "limits": limits.limits,
        "activated_at": datetime.utcnow().isoformat(),
        "product_id": product_id
    }
    
    return user_data

def check_feature_access(user_plan_tier: int, feature: str) -> bool:
    """Check if user has access to a feature"""
    limits = PLAN_LIMITS.get(user_plan_tier)
    if not limits:
        return False
    
    return limits.features.get(feature, False)

def check_usage_limit(user_plan_tier: int, limit_type: str, current_usage: int) -> bool:
    """Check if user is within usage limits"""
    limits = PLAN_LIMITS.get(user_plan_tier)
    if not limits:
        return False
    
    limit_value = limits.limits.get(limit_type, 0)
    
    # -1 means unlimited
    if limit_value == -1:
        return True
    
    return current_usage < limit_value

def get_upgrade_message(current_tier: int, required_tier: int) -> str:
    """Get upgrade message for feature"""
    return f"This feature requires Tier {required_tier}. You are on Tier {current_tier}. Please upgrade your plan."
