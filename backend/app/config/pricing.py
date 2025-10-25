# Pricing Configuration
# Zentralisierte Preise für alle Pläne (erweitert bestehende plans.json)
import json
import os
from typing import Dict, Any

# Pfad zur bestehenden plans.json
_PLANS_PATH = os.path.join(os.path.dirname(__file__), "plans.json")

# Fallback-Preise für Payment-System (wenn plans.json nicht verfügbar)
FALLBACK_PRICING_PLANS = {
    'free': {
        'name': 'Free',
        'price_usd': 0.00,
        'features': ['basic_tracing', 'limited_cases']
    },
    'starter': {
        'name': 'Starter',
        'price_usd': 39.00,
        'features': ['advanced_tracing', 'unlimited_cases', 'priority_support']
    },
    'pro': {
        'name': 'Professional',
        'price_usd': 99.00,
        'features': ['all_basic', 'ai_insights', 'bulk_export', 'api_access']
    },
    'enterprise': {
        'name': 'Enterprise',
        'price_usd': 4999.00,
        'features': ['all_pro', 'custom_integrations', 'dedicated_support', 'white_label']
    }
}

# Crypto Payment Multipliers (für NOWPayments)
CRYPTO_MULTIPLIERS = {
    'btc': 1.0,    # Base currency
    'eth': 15.0,   # Approximate ETH/BTC ratio
    'usdt': 1.0,   # Stablecoin
    'usdc': 1.0,   # Stablecoin
    'trx': 0.1,    # TRX/BTC ratio
    'bnb': 300.0,  # BNB/BTC ratio
    'matic': 0.5,  # MATIC/BTC ratio
}

def load_plans_config() -> Dict[str, Any]:
    """Load plans configuration from plans.json"""
    try:
        with open(_PLANS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'currency': 'EUR',
            'annual_discount_percent': 20,
            'plans': [
                {'id': k, **v} for k, v in FALLBACK_PRICING_PLANS.items()
            ]
        }

_PLANS_CONFIG = load_plans_config()

def get_plan_config(plan_name: str) -> dict:
    """Get pricing configuration for a plan"""
    plans = _PLANS_CONFIG.get('plans', [])
    plan = next((p for p in plans if p.get('id') == plan_name.lower()), None)

    if not plan:
        # Fallback to hardcoded config
        return FALLBACK_PRICING_PLANS.get(plan_name.lower(), FALLBACK_PRICING_PLANS['free'])

    return {
        'name': plan.get('name', plan_name),
        'price_usd': plan.get('monthly_price_usd', 0.00),
        'features': plan.get('features', {}),
        'quotas': plan.get('quotas', {}),
        'sla': plan.get('sla', {})
    }

def calculate_crypto_amount(usd_amount: float, crypto_symbol: str) -> float:
    """Calculate crypto amount from USD using multipliers"""
    multiplier = CRYPTO_MULTIPLIERS.get(crypto_symbol.lower(), 1.0)
    # This is simplified - in production, use real-time exchange rates
    return usd_amount * multiplier

def get_all_plans() -> list:
    """Get all available plans"""
    return _PLANS_CONFIG.get('plans', [])

def get_currency() -> str:
    """Get default currency"""
    return _PLANS_CONFIG.get('currency', 'EUR')
