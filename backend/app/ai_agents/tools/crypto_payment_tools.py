"""
AI Agent Tools for Crypto Payments
Allows AI to create payments, check status, and provide payment info
"""
import logging
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.crypto_payments import crypto_payment_service
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class GetAvailableCurrenciesInput(BaseModel):
    """Input for getting available cryptocurrencies"""
    pass


class GetAvailableCurrenciesTool(BaseTool):
    """Tool to get list of available cryptocurrencies"""
    name: str = "get_available_cryptocurrencies"
    description: str = """
    Get list of all available cryptocurrencies for payments.
    Use this when user asks about payment options or which coins are supported.
    Returns list of 30+ cryptocurrencies with names and symbols.
    """
    args_schema: type[BaseModel] = GetAvailableCurrenciesInput
    
    async def _arun(self) -> str:
        """Get available cryptocurrencies"""
        try:
            currencies = await crypto_payment_service.get_available_currencies()
            
            # Format as readable list
            result = "📋 **Verfügbare Kryptowährungen** (30+):\n\n"
            result += "**Top Cryptos:**\n"
            
            popular = ["btc", "eth", "usdt", "usdc", "bnb", "sol", "matic", "avax"]
            for curr in popular:
                if curr in currencies:
                    info = crypto_payment_service.get_currency_info(curr)
                    result += f"- {info['logo']} **{info['name']}** ({info['symbol'].upper()})\n"
            
            result += f"\n... und {len(currencies) - len(popular)} weitere Coins!\n"
            result += "\n💡 **Tipp**: Du kannst mit jeder dieser Währungen bezahlen!"
            
            return result
        except Exception as e:
            logger.error(f"Error getting currencies: {e}")
            return "❌ Fehler beim Abrufen der Währungen. Bitte versuche es später erneut."


class GetPaymentEstimateInput(BaseModel):
    """Input for getting payment estimate"""
    plan: str = Field(..., description="Subscription plan name (e.g., 'pro', 'business', 'plus')")
    currency: str = Field(..., description="Crypto currency code (e.g., 'btc', 'eth', 'usdt')")


class GetPaymentEstimateTool(BaseTool):
    """Tool to get payment estimate in crypto"""
    name: str = "get_payment_estimate"
    description: str = """
    Get payment estimate for a subscription plan in a specific cryptocurrency.
    Use this when user asks "How much is Pro plan in Bitcoin?" or similar questions.
    Input: plan (e.g., 'pro'), currency (e.g., 'btc')
    Returns: Estimated crypto amount, exchange rate, and USD price.
    """
    args_schema: type[BaseModel] = GetPaymentEstimateInput
    
    async def _arun(self, plan: str, currency: str) -> str:
        """Get payment estimate"""
        try:
            # Get plan price
            price_usd = crypto_payment_service.PLAN_PRICES.get(plan.lower())
            if not price_usd:
                return f"❌ Plan '{plan}' nicht gefunden. Verfügbare Pläne: community, starter, pro, business, plus, enterprise"
            
            # Get estimate
            estimate = await crypto_payment_service.get_estimate(
                amount_usd=price_usd,
                currency_from="usd",
                currency_to=currency.lower()
            )
            
            if not estimate:
                return f"❌ Fehler beim Abrufen der Schätzung für {currency.upper()}"
            
            crypto_amount = estimate.get("estimated_amount", 0)
            currency_info = crypto_payment_service.get_currency_info(currency.lower())
            
            result = "💰 **Payment-Schätzung**\n\n"
            result += f"**Plan**: {plan.title()}\n"
            result += f"**Preis**: ${price_usd} USD\n\n"
            result += "**Du zahlst**:\n"
            result += f"{currency_info['logo']} **{crypto_amount:.8f} {currency_info['symbol'].upper()}**\n\n"
            result += "💡 Die finale Amount wird bei Payment-Erstellung berechnet (Live Exchange-Rate)."
            
            return result
        except Exception as e:
            logger.error(f"Error getting estimate: {e}")
            return "❌ Fehler beim Berechnen der Schätzung."


class CreateCryptoPaymentInput(BaseModel):
    """Input for creating crypto payment"""
    user_id: str = Field(..., description="User ID from context")
    plan: str = Field(..., description="Subscription plan (e.g., 'pro', 'business')")
    currency: str = Field(..., description="Crypto currency code (e.g., 'eth', 'btc')")


class CreateCryptoPaymentTool(BaseTool):
    """Tool to create a crypto payment"""
    name: str = "create_crypto_payment"
    description: str = """
    Create a new cryptocurrency payment for a subscription plan.
    Use this when user confirms they want to pay with crypto.
    Input: user_id (from context), plan (e.g., 'pro'), currency (e.g., 'eth')
    Returns: Payment details including deposit address, amount, and QR code info.
    IMPORTANT: User must be authenticated. Check user_id first.
    """
    args_schema: type[BaseModel] = CreateCryptoPaymentInput
    
    async def _arun(self, user_id: str, plan: str, currency: str) -> str:
        """Create crypto payment"""
        try:
            if not user_id:
                return "❌ Du musst eingeloggt sein um eine Zahlung zu erstellen. Bitte melde dich zuerst an."
            
            # Generate unique order ID
            import uuid
            order_id = f"order_{uuid.uuid4().hex[:16]}"
            
            # Create payment
            payment_data = await crypto_payment_service.create_payment(
                plan_name=plan.lower(),
                currency=currency.lower(),
                user_id=user_id,
                order_id=order_id
            )
            
            if not payment_data:
                return "❌ Fehler beim Erstellen der Zahlung. Bitte versuche es erneut."
            
            # Save to database
            try:
                query = """
                    INSERT INTO crypto_payments (
                        payment_id, order_id, user_id, plan_name,
                        price_amount, price_currency, pay_amount, pay_currency,
                        pay_address, payin_extra_id, payment_status,
                        invoice_url, purchase_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """
                await postgres_client.execute(
                    query,
                    payment_data["payment_id"],
                    order_id,
                    user_id,
                    plan.lower(),
                    float(payment_data["price_amount"]),
                    payment_data["price_currency"],
                    float(payment_data["pay_amount"]),
                    payment_data["pay_currency"],
                    payment_data.get("pay_address"),
                    payment_data.get("payin_extra_id"),
                    payment_data["payment_status"],
                    crypto_payment_service.get_payment_url(payment_data["payment_id"]),
                    payment_data.get("purchase_id")
                )
            except Exception as db_error:
                logger.error(f"Database error: {db_error}")
            
            # Format response with payment details
            currency_info = crypto_payment_service.get_currency_info(currency.lower())
            
            result = "✅ **Payment erstellt!**\n\n"
            result += f"**Plan**: {plan.title()}\n"
            result += f"**Order ID**: `{order_id}`\n\n"
            result += "💰 **Zu zahlender Betrag**:\n"
            result += f"{currency_info['logo']} **{payment_data['pay_amount']} {currency_info['symbol'].upper()}**\n"
            result += f"≈ ${payment_data['price_amount']} USD\n\n"
            result += "📍 **Zahlungsadresse**:\n"
            result += f"```\n{payment_data['pay_address']}\n```\n\n"
            
            if payment_data.get("payin_extra_id"):
                result += f"🔖 **Extra ID**: `{payment_data['payin_extra_id']}`\n\n"
            
            result += "⏰ **Gültigkeit**: 15 Minuten\n\n"
            result += f"⚠️ **WICHTIG**: Sende nur **{currency_info['symbol'].upper()}** an diese Adresse!\n\n"
            result += f"🔗 [Payment-Page öffnen]({crypto_payment_service.get_payment_url(payment_data['payment_id'])})\n\n"
            result += "💡 **Tipp**: Die Zahlung wird automatisch erkannt und dein Plan aktiviert!"
            
            # Return payment_id for frontend to display QR code
            result += f"\n\n[PAYMENT_ID:{payment_data['payment_id']}]"
            
            return result
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return f"❌ Fehler beim Erstellen der Zahlung: {str(e)}"


class CheckPaymentStatusInput(BaseModel):
    """Input for checking payment status"""
    payment_id: int = Field(..., description="Payment ID to check")


class CheckPaymentStatusTool(BaseTool):
    """Tool to check payment status"""
    name: str = "check_payment_status"
    description: str = """
    Check the status of a crypto payment.
    Use this when user asks "Is my payment confirmed?" or "What's the status?".
    Input: payment_id (from previous create_payment call)
    Returns: Current payment status, transaction hash if confirmed, and next steps.
    """
    args_schema: type[BaseModel] = CheckPaymentStatusInput
    
    async def _arun(self, payment_id: int) -> str:
        """Check payment status"""
        try:
            # Get status from database
            payment = await postgres_client.fetchrow(
                "SELECT * FROM crypto_payments WHERE payment_id = $1",
                payment_id
            )
            
            if not payment:
                return f"❌ Payment mit ID {payment_id} nicht gefunden."
            
            status = payment["payment_status"]
            currency = payment["pay_currency"].upper()
            amount = payment["pay_amount"]
            
            # Status messages
            status_messages = {
                "pending": "⏳ **Warte auf Zahlung**\n\nBitte sende die Krypto an die angegebene Adresse.",
                "waiting": "⏳ **Warte auf Blockchain-Bestätigung**\n\nTransaktion wurde erkannt, warte auf Confirmations...",
                "confirming": "🔄 **Bestätigung läuft**\n\nDeine Transaktion wird gerade bestätigt...",
                "confirmed": "✅ **Bestätigt!**\n\nZahlung wurde bestätigt, wird jetzt verarbeitet...",
                "sending": "📤 **Wird verarbeitet**\n\nZahlung wird an unser Wallet gesendet...",
                "finished": "🎉 **Zahlung erfolgreich!**\n\nDein Plan wurde aktiviert! Willkommen!",
                "failed": "❌ **Zahlung fehlgeschlagen**\n\nBitte kontaktiere den Support.",
                "expired": "⏱️ **Zahlung abgelaufen**\n\nBitte erstelle eine neue Zahlung."
            }
            
            result = "📊 **Payment-Status**\n\n"
            result += f"**Order ID**: `{payment['order_id']}`\n"
            result += f"**Betrag**: {amount} {currency}\n\n"
            result += status_messages.get(status, f"Status: {status}")
            
            if payment.get("pay_in_hash"):
                result += f"\n\n**TX-Hash**: `{payment['pay_in_hash'][:16]}...`"
            
            return result
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return "❌ Fehler beim Abrufen des Status."


class GetUserPaymentHistoryInput(BaseModel):
    """Input for getting user payment history"""
    user_id: str = Field(..., description="User ID from context")


class GetUserPaymentHistoryTool(BaseTool):
    """Tool to get user's payment history"""
    name: str = "get_user_payment_history"
    description: str = """
    Get user's crypto payment history.
    Use this when user asks "Show my payments" or "What payments did I make?".
    Input: user_id (from context)
    Returns: List of recent payments with status.
    """
    args_schema: type[BaseModel] = GetUserPaymentHistoryInput
    
    async def _arun(self, user_id: str) -> str:
        """Get payment history"""
        try:
            if not user_id:
                return "❌ Du musst eingeloggt sein. Bitte melde dich an."
            
            payments = await postgres_client.fetch(
                """
                SELECT * FROM crypto_payments
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 10
                """,
                user_id
            )
            
            if not payments:
                return "📭 Du hast noch keine Crypto-Zahlungen getätigt."
            
            result = f"📋 **Deine Zahlungen** ({len(payments)}):\n\n"
            
            for i, p in enumerate(payments[:5], 1):
                status_emoji = {
                    "finished": "✅",
                    "pending": "⏳",
                    "waiting": "⏳",
                    "confirming": "🔄",
                    "failed": "❌",
                    "expired": "⏱️"
                }.get(p["payment_status"], "❓")
                
                result += f"{i}. {status_emoji} **{p['plan_name'].title()}** Plan\n"
                result += f"   {p['pay_amount']} {p['pay_currency'].upper()}"
                result += f" • {p['payment_status']}\n"
                result += f"   {p['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            
            if len(payments) > 5:
                result += f"... und {len(payments) - 5} weitere.\n"
            
            return result
        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return "❌ Fehler beim Abrufen der Zahlungshistorie."


# Export all tools
crypto_payment_tools = [
    GetAvailableCurrenciesTool(),
    GetPaymentEstimateTool(),
    CreateCryptoPaymentTool(),
    CheckPaymentStatusTool(),
    GetUserPaymentHistoryTool()
]
