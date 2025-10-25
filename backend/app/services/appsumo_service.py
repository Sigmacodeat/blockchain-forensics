"""
AppSumo Code Management Service
Handles code generation, validation, redemption
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AppSumoService:
    """AppSumo Code Management"""
    
    # Product configuration
    PRODUCTS = {
        'chatbot': {
            'name': 'AI ChatBot Pro',
            'tiers': {
                1: {'price': 59, 'features': {'websites': 1, 'chats_per_month': 1000}},
                2: {'price': 119, 'features': {'websites': 3, 'chats_per_month': 5000, 'white_label': True}},
                3: {'price': 199, 'features': {'websites': 10, 'chats_per_month': -1, 'api_access': True}}
            }
        },
        'wallet-guardian': {
            'name': 'ShieldGuard Pro',
            'tiers': {
                1: {'price': 79, 'features': {'wallets': 1, 'scans_per_day': 100}},
                2: {'price': 149, 'features': {'wallets': 3, 'scans_per_day': 500}},
                3: {'price': 249, 'features': {'wallets': -1, 'scans_per_day': -1}}
            }
        },
        'transaction-inspector': {
            'name': 'ChainTracer Pro',
            'tiers': {
                1: {'price': 69, 'features': {'addresses': 10}},
                2: {'price': 149, 'features': {'addresses': 50}},
                3: {'price': 229, 'features': {'addresses': -1}}
            }
        },
        'analytics': {
            'name': 'CryptoMetrics Pro',
            'tiers': {
                1: {'price': 79, 'features': {'portfolios': 3}},
                2: {'price': 149, 'features': {'portfolios': 10, 'api_access': True}},
                3: {'price': 249, 'features': {'portfolios': -1, 'white_label': True, 'api_access': True}}
            }
        }
    }
    
    @staticmethod
    def generate_code(product: str, tier: int) -> str:
        """Generate unique AppSumo code"""
        # Format: PRODUCT-TIER-RANDOM (e.g., CHATBOT-1-ABC123XYZ)
        product_prefix = product.upper().replace('-', '')[:8]
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(9))
        return f"{product_prefix}-{tier}-{random_suffix}"
    
    @staticmethod
    async def generate_codes_bulk(
        db: AsyncSession,
        product: str,
        tier: int,
        count: int,
        admin_id: str,
        expires_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple codes"""
        from app.models.appsumo import AppSumoCode
        
        codes = []
        expires_at = datetime.utcnow() + timedelta(days=expires_days) if expires_days else None
        
        for _ in range(count):
            code_str = AppSumoService.generate_code(product, tier)
            
            code = AppSumoCode(
                code=code_str,
                product=product,
                tier=tier,
                status='active',
                created_by_admin_id=admin_id,
                expires_at=expires_at
            )
            db.add(code)
            codes.append({
                'code': code_str,
                'product': product,
                'tier': tier,
                'expires_at': expires_at
            })
        
        await db.commit()
        logger.info(f"Generated {count} codes for {product} tier {tier}")
        return codes
    
    @staticmethod
    async def validate_code(db: AsyncSession, code: str) -> Optional[Dict[str, Any]]:
        """Validate code and check status"""
        from app.models.appsumo import AppSumoCode
        
        result = await db.execute(
            select(AppSumoCode).where(AppSumoCode.code == code.upper())
        )
        code_obj = result.scalar_one_or_none()
        
        if not code_obj:
            return {'valid': False, 'reason': 'Code not found'}
        
        if code_obj.status != 'active':
            return {'valid': False, 'reason': f'Code is {code_obj.status}'}
        
        if code_obj.expires_at and code_obj.expires_at < datetime.utcnow():
            return {'valid': False, 'reason': 'Code expired'}
        
        return {
            'valid': True,
            'product': code_obj.product,
            'tier': code_obj.tier,
            'product_name': AppSumoService.PRODUCTS[code_obj.product]['name'],
            'features': AppSumoService.PRODUCTS[code_obj.product]['tiers'][code_obj.tier]['features']
        }
    
    @staticmethod
    async def redeem_code(
        db: AsyncSession,
        code: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Redeem code for user"""
        from app.models.appsumo import AppSumoCode, AppSumoActivation
        
        # Validate code
        validation = await AppSumoService.validate_code(db, code)
        if not validation['valid']:
            return {'success': False, 'error': validation['reason']}
        
        # Get code object
        result = await db.execute(
            select(AppSumoCode).where(AppSumoCode.code == code.upper())
        )
        code_obj = result.scalar_one()
        
        # Check if user already has this product
        existing = await db.execute(
            select(AppSumoActivation).where(
                and_(
                    AppSumoActivation.user_id == user_id,
                    AppSumoActivation.product == code_obj.product
                )
            )
        )
        if existing.scalar_one_or_none():
            return {'success': False, 'error': 'You already have this product activated'}
        
        # Mark code as redeemed
        code_obj.status = 'redeemed'
        code_obj.redeemed_by_user_id = user_id
        code_obj.redeemed_at = datetime.utcnow()
        code_obj.redemption_ip = ip_address
        code_obj.redemption_user_agent = user_agent
        
        # Create activation
        activation = AppSumoActivation(
            user_id=user_id,
            code_id=code_obj.id,
            product=code_obj.product,
            tier=code_obj.tier,
            status='active',
            features=validation['features'],
            limits=AppSumoService.PRODUCTS[code_obj.product]['tiers'][code_obj.tier]['features']
        )
        db.add(activation)
        
        await db.commit()
        
        logger.info(f"Code {code} redeemed by user {user_id} for {code_obj.product} tier {code_obj.tier}")
        
        return {
            'success': True,
            'product': code_obj.product,
            'product_name': validation['product_name'],
            'tier': code_obj.tier,
            'features': validation['features']
        }
    
    @staticmethod
    async def get_user_activations(db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        """Get all user activations"""
        from app.models.appsumo import AppSumoActivation
        
        result = await db.execute(
            select(AppSumoActivation).where(
                and_(
                    AppSumoActivation.user_id == user_id,
                    AppSumoActivation.status == 'active'
                )
            )
        )
        activations = result.scalars().all()
        
        return [
            {
                'product': act.product,
                'product_name': AppSumoService.PRODUCTS[act.product]['name'],
                'tier': act.tier,
                'features': act.features,
                'limits': act.limits,
                'activated_at': act.activated_at
            }
            for act in activations
        ]
    
    @staticmethod
    async def get_analytics(db: AsyncSession) -> Dict[str, Any]:
        """Get AppSumo analytics"""
        from app.models.appsumo import AppSumoCode, AppSumoActivation
        
        # Total codes
        total_codes = await db.execute(select(func.count(AppSumoCode.id)))
        total = total_codes.scalar()
        
        # By status
        by_status = await db.execute(
            select(AppSumoCode.status, func.count(AppSumoCode.id))
            .group_by(AppSumoCode.status)
        )
        status_stats = {row[0]: row[1] for row in by_status}
        
        # By product
        by_product = await db.execute(
            select(AppSumoCode.product, func.count(AppSumoCode.id))
            .group_by(AppSumoCode.product)
        )
        product_stats = {row[0]: row[1] for row in by_product}
        
        # Active activations
        active_acts = await db.execute(
            select(func.count(AppSumoActivation.id))
            .where(AppSumoActivation.status == 'active')
        )
        active_activations = active_acts.scalar()
        
        return {
            'total_codes': total,
            'by_status': status_stats,
            'by_product': product_stats,
            'active_activations': active_activations,
            'redemption_rate': round((status_stats.get('redeemed', 0) / total * 100), 2) if total > 0 else 0
        }
