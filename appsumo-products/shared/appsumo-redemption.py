"""
AppSumo Code Redemption System
Handles lifetime deal code validation and activation
"""

from fastapi import HTTPException
from typing import Dict, Optional
import hashlib
import datetime

# AppSumo Plan Tiers
APPSUMO_TIERS = {
    "tier1": {"price": 59, "features": {"limit": "basic"}},
    "tier2": {"price": 119, "features": {"limit": "pro"}},
    "tier3": {"price": 199, "features": {"limit": "unlimited"}},
}

class AppSumoRedemption:
    """Handle AppSumo code redemption"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def validate_code(self, code: str) -> Dict:
        """
        Validate AppSumo redemption code
        Format: APPSUMO-PRODUCT-TIER-XXXXX
        """
        if not code.startswith("APPSUMO-"):
            raise HTTPException(status_code=400, detail="Invalid code format")
        
        parts = code.split("-")
        if len(parts) != 4:
            raise HTTPException(status_code=400, detail="Invalid code format")
        
        _, product, tier, code_id = parts
        
        if tier.lower() not in APPSUMO_TIERS:
            raise HTTPException(status_code=400, detail="Invalid tier")
        
        # Check if code already redeemed (would check in real DB)
        # For now, return mock validation
        return {
            "valid": True,
            "product": product,
            "tier": tier.lower(),
            "code_id": code_id,
            "plan_details": APPSUMO_TIERS[tier.lower()]
        }
    
    def redeem_code(self, code: str, user_email: str) -> Dict:
        """
        Redeem AppSumo code for user
        Creates lifetime access subscription
        """
        validation = self.validate_code(code)
        
        # Create subscription (would insert to DB)
        subscription = {
            "user_email": user_email,
            "product": validation["product"],
            "tier": validation["tier"],
            "plan": "lifetime",
            "activated_at": datetime.datetime.utcnow().isoformat(),
            "status": "active",
            "code": code,
            "features": validation["plan_details"]["features"]
        }
        
        return subscription
    
    def check_subscription(self, user_email: str, product: str) -> Optional[Dict]:
        """
        Check if user has active subscription for product
        """
        # Would query DB - mock for now
        return {
            "active": True,
            "tier": "tier2",
            "plan": "lifetime",
            "features": APPSUMO_TIERS["tier2"]["features"]
        }

# API Endpoints Example
"""
@app.post("/api/appsumo/redeem")
async def redeem_appsumo_code(code: str, email: str):
    redemption = AppSumoRedemption(db)
    result = redemption.redeem_code(code, email)
    return {"success": True, "subscription": result}

@app.get("/api/appsumo/verify/{email}/{product}")
async def verify_subscription(email: str, product: str):
    redemption = AppSumoRedemption(db)
    sub = redemption.check_subscription(email, product)
    return {"active": sub["active"], "tier": sub["tier"]}
"""
