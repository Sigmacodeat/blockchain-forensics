"""
Billing & Subscription Schemas
================================

Pydantic-Models für Billing-API-Endpunkte
"""

from pydantic import BaseModel, Field
from typing import Optional


class ProrationRequest(BaseModel):
    """Request für Proration-Berechnung"""
    current_plan: str = Field(..., description="Aktueller Plan (z.B. 'starter')")
    target_plan: str = Field(..., description="Ziel-Plan (z.B. 'pro')")
    billing_cycle_start: str = Field(..., description="Start des Billing-Cycles (ISO format)")
    billing_cycle_end: str = Field(..., description="Ende des Billing-Cycles (ISO format)")


class ProrationResponse(BaseModel):
    """Response für Proration-Berechnung"""
    prorated_amount: float = Field(..., description="Prorated Betrag (kann negativ sein bei Credit)")
    days_remaining: int = Field(..., description="Verbleibende Tage im Cycle")
    current_plan_cost: float = Field(..., description="Kosten des aktuellen Plans")
    target_plan_cost: float = Field(..., description="Kosten des Ziel-Plans")
    credit_from_current: float = Field(..., description="Credit vom aktuellen Plan")
    charge_for_target: float = Field(..., description="Charge für Ziel-Plan")


class DowngradeRequest(BaseModel):
    """Request für Plan-Downgrade"""
    target_plan: str = Field(..., description="Ziel-Plan (muss niedriger sein)")
    reason: Optional[str] = Field(None, description="Grund für Downgrade (optional)")


class DowngradeResponse(BaseModel):
    """Response für Plan-Downgrade"""
    message: str
    current_plan: str
    target_plan: str
    effective_date: str = Field(..., description="Datum an dem Downgrade wirksam wird")
    days_until_downgrade: int
    active_features_warning: Optional[list] = Field(None, description="Features die verloren gehen")


class SubscriptionRequest(BaseModel):
    """Request für Subscription-Erstellung"""
    plan: str = Field(..., description="Plan-ID (z.B. 'pro')")
    billing_period: str = Field("monthly", description="monthly oder annual")
    payment_method: Optional[str] = Field(None, description="Payment-Method-ID")


class SubscriptionResponse(BaseModel):
    """Response für Subscription"""
    subscription_id: str
    user_id: str
    plan: str
    status: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool = False
    created_at: str


class UpgradeRequest(BaseModel):
    """Request für Plan-Upgrade"""
    target_plan: str = Field(..., description="Ziel-Plan (muss höher sein)")
    payment_method: Optional[str] = Field(None, description="Payment-Method-ID (optional)")


class UpgradeResponse(BaseModel):
    """Response für Plan-Upgrade"""
    message: str
    old_plan: str
    new_plan: str
    prorated_amount: float
    subscription_id: str
    effective_date: str
