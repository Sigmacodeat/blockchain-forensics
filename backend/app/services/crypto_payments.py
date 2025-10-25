"""
NOWPayments Crypto Payment Service
Supports 150+ cryptocurrencies for subscription payments
"""
import aiohttp
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from io import BytesIO
import base64

from app.config import settings

logger = logging.getLogger(__name__)


class CryptoPaymentService:
    """
    NOWPayments API Integration for Crypto Payments
    Docs: https://documenter.getpostman.com/view/7907941/S1a32n38
    """
    
    BASE_URL = "https://api.nowpayments.io/v1"
    SANDBOX_URL = "https://api-sandbox.nowpayments.io/v1"
    
    # Supported cryptocurrencies (Top 30 most popular)
    SUPPORTED_CURRENCIES = [
        "btc", "eth", "usdt", "usdc", "bnb", "sol", "matic", "avax",
        "trx", "dai", "ada", "doge", "ltc", "xrp", "dot", "uni",
        "link", "xlm", "xmr", "etc", "bch", "atom", "algo", "xtz",
        "eos", "zec", "dash", "rvn", "dcr", "qtum"
    ]
    
    # Plan prices in USD
    PLAN_PRICES = {
        "community": 0,
        "starter": 99,
        "pro": 499,
        "business": 1499,
        "plus": 2999,
        "enterprise": 9999
    }
    
    def __init__(self):
        """Initialize NOWPayments service"""
        self.api_key = settings.NOWPAYMENTS_API_KEY
        self.ipn_secret = settings.NOWPAYMENTS_IPN_SECRET
        self.sandbox = settings.NOWPAYMENTS_SANDBOX
        self.base_url = self.SANDBOX_URL if self.sandbox else self.BASE_URL
        
    async def get_available_currencies(self) -> List[str]:
        """
        Get list of available cryptocurrencies
        
        Returns:
            List of currency codes (e.g., ['btc', 'eth', 'usdt'])
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/currencies",
                    headers={"x-api-key": self.api_key}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Filter to only supported currencies
                        available = data.get("currencies", [])
                        return [c for c in available if c in self.SUPPORTED_CURRENCIES]
                    else:
                        logger.error(f"Failed to fetch currencies: {response.status}")
                        return self.SUPPORTED_CURRENCIES  # Fallback
        except Exception as e:
            logger.error(f"Error fetching currencies: {e}")
            return self.SUPPORTED_CURRENCIES  # Fallback
    
    async def get_estimate(
        self,
        amount_usd: Decimal,
        currency_from: str = "usd",
        currency_to: str = "btc"
    ) -> Optional[Dict[str, Any]]:
        """
        Get estimated crypto amount for USD price
        
        Args:
            amount_usd: Amount in USD
            currency_from: Source currency (default: usd)
            currency_to: Target crypto (e.g., btc, eth)
            
        Returns:
            Estimate data with crypto amount
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/estimate",
                    params={
                        "amount": float(amount_usd),
                        "currency_from": currency_from,
                        "currency_to": currency_to
                    },
                    headers={"x-api-key": self.api_key}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get estimate: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting estimate: {e}")
            return None
    
    async def create_payment(
        self,
        plan_name: str,
        currency: str,
        user_id: int,
        order_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create crypto payment for subscription plan
        
        Args:
            plan_name: Subscription plan (e.g., 'pro', 'business')
            currency: Crypto currency code (e.g., 'btc', 'eth')
            user_id: User ID
            order_id: Unique order identifier
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            
        Returns:
            Payment data with address and amount
        """
        try:
            # Get plan price in USD
            price_usd = self.PLAN_PRICES.get(plan_name.lower(), 0)
            if price_usd == 0:
                logger.error(f"Invalid plan: {plan_name}")
                return None
            
            # Get estimate for crypto amount
            estimate = await self.get_estimate(Decimal(str(price_usd)), "usd", currency)
            if not estimate:
                return None
            
            # Create payment
            payload = {
                "price_amount": float(price_usd),
                "price_currency": "usd",
                "pay_currency": currency,
                "order_id": order_id,
                "order_description": f"Blockchain Forensics - {plan_name.title()} Plan",
                "ipn_callback_url": f"{settings.BACKEND_URL}/api/v1/webhooks/nowpayments",
                "success_url": success_url or f"{settings.FRONTEND_URL}/payment/success",
                "cancel_url": cancel_url or f"{settings.FRONTEND_URL}/payment/cancel",
                "is_fixed_rate": True,  # Lock exchange rate
                "is_fee_paid_by_user": False  # We pay network fees
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/payment",
                    json=payload,
                    headers={"x-api-key": self.api_key}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Created payment {data.get('payment_id')} for order {order_id}")
                        return data
                    else:
                        error = await response.text()
                        logger.error(f"Failed to create payment: {response.status} - {error}")
                        return None
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None
    
    async def get_payment_status(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get payment status by ID
        
        Args:
            payment_id: NOWPayments payment ID
            
        Returns:
            Payment status data
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/payment/{payment_id}",
                    headers={"x-api-key": self.api_key}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get payment status: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return None
    
    async def get_minimum_payment_amount(self, currency: str) -> Optional[Decimal]:
        """
        Get minimum payment amount for currency
        
        Args:
            currency: Crypto currency code
            
        Returns:
            Minimum amount in crypto
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/min-amount",
                    params={"currency_from": "usd", "currency_to": currency},
                    headers={"x-api-key": self.api_key}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return Decimal(str(data.get("min_amount", 0)))
                    else:
                        return Decimal("0")
        except Exception as e:
            logger.error(f"Error getting minimum amount: {e}")
            return Decimal("0")
    
    def verify_ipn_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify IPN (Instant Payment Notification) signature
        
        Args:
            payload: Raw request body
            signature: x-nowpayments-sig header value
            
        Returns:
            True if signature is valid
        """
        try:
            expected_sig = hmac.new(
                self.ipn_secret.encode(),
                payload,
                hashlib.sha512
            ).hexdigest()
            return hmac.compare_digest(expected_sig, signature)
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def get_payment_url(self, payment_id: int) -> str:
        """
        Get hosted payment page URL
        
        Args:
            payment_id: NOWPayments payment ID
            
        Returns:
            Payment page URL
        """
        return f"https://nowpayments.io/payment/?iid={payment_id}"
    
    async def create_recurring_payment(
        self,
        plan_name: str,
        currency: str,
        user_id: int,
        interval: str = "monthly"  # monthly, yearly
    ) -> Optional[Dict[str, Any]]:
        """
        Create recurring crypto payment (subscription)
        
        Args:
            plan_name: Subscription plan
            currency: Crypto currency
            user_id: User ID
            interval: Payment interval (monthly/yearly)
            
        Returns:
            Recurring payment data
        """
        # Note: NOWPayments doesn't support native recurring payments
        # We handle this by creating new payments each billing cycle
        # This is stored in our DB and triggered by background task
        
        price_usd = self.PLAN_PRICES.get(plan_name.lower(), 0)
        if price_usd == 0:
            return None
        
        # Calculate next billing date
        next_billing = datetime.utcnow()
        if interval == "monthly":
            next_billing += timedelta(days=30)
        elif interval == "yearly":
            next_billing += timedelta(days=365)
        
        return {
            "plan": plan_name,
            "currency": currency,
            "amount_usd": price_usd,
            "interval": interval,
            "next_billing_date": next_billing.isoformat(),
            "status": "pending_first_payment"
        }
    
    def generate_qr_code(
        self,
        address: str,
        amount: Optional[float] = None,
        currency: Optional[str] = None
    ) -> str:
        """
        Generate QR code for crypto payment address
        
        Args:
            address: Crypto wallet address
            amount: Optional amount to include in QR
            currency: Crypto currency code
            
        Returns:
            Base64-encoded QR code image (PNG)
        """
        try:
            # Lazy import to avoid hard dependency during test collection
            try:
                import qrcode  # type: ignore
            except Exception:
                logger.warning("qrcode module not available; returning empty QR string")
                return ""

            # Build payment URI based on currency
            if currency and amount:
                # Bitcoin URI format: bitcoin:ADDRESS?amount=AMOUNT
                # Ethereum URI format: ethereum:ADDRESS?value=AMOUNT
                currency_lower = currency.lower()
                if currency_lower == "btc":
                    uri = f"bitcoin:{address}?amount={amount}"
                elif currency_lower == "eth":
                    uri = f"ethereum:{address}?value={amount}"
                elif currency_lower in ["usdt", "usdc", "dai"]:
                    # ERC-20 tokens use ethereum scheme
                    uri = f"ethereum:{address}?value={amount}"
                else:
                    # Generic format for other currencies
                    uri = f"{currency_lower}:{address}?amount={amount}"
            else:
                uri = address
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return ""
    
    def get_currency_info(self, currency: str) -> Dict[str, Any]:
        """
        Get currency display information
        
        Args:
            currency: Crypto currency code
            
        Returns:
            Currency info (name, symbol, logo)
        """
        CURRENCY_INFO = {
            "btc": {"name": "Bitcoin", "symbol": "BTC", "logo": "₿", "network": "Bitcoin"},
            "eth": {"name": "Ethereum", "symbol": "ETH", "logo": "Ξ", "network": "Ethereum"},
            "usdt": {"name": "Tether", "symbol": "USDT", "logo": "₮", "network": "Multiple"},
            "usdc": {"name": "USD Coin", "symbol": "USDC", "logo": "$", "network": "Multiple"},
            "bnb": {"name": "Binance Coin", "symbol": "BNB", "logo": "BNB", "network": "BSC"},
            "sol": {"name": "Solana", "symbol": "SOL", "logo": "SOL", "network": "Solana"},
            "matic": {"name": "Polygon", "symbol": "MATIC", "logo": "MATIC", "network": "Polygon"},
            "avax": {"name": "Avalanche", "symbol": "AVAX", "logo": "AVAX", "network": "Avalanche"},
            "trx": {"name": "TRON", "symbol": "TRX", "logo": "TRX", "network": "TRON"},
            "dai": {"name": "Dai", "symbol": "DAI", "logo": "◈", "network": "Ethereum"},
            "ada": {"name": "Cardano", "symbol": "ADA", "logo": "₳", "network": "Cardano"},
            "doge": {"name": "Dogecoin", "symbol": "DOGE", "logo": "Ð", "network": "Dogecoin"},
            "ltc": {"name": "Litecoin", "symbol": "LTC", "logo": "Ł", "network": "Litecoin"},
            "xrp": {"name": "Ripple", "symbol": "XRP", "logo": "XRP", "network": "Ripple"},
        }
        return CURRENCY_INFO.get(currency.lower(), {
            "name": currency.upper(),
            "symbol": currency.upper(),
            "logo": currency.upper(),
            "network": "Unknown"
        })


# Singleton instance
crypto_payment_service = CryptoPaymentService()
