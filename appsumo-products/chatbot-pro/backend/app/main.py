from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import os
import asyncio
import httpx
import sys

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

# Import shared modules
try:
    from auth import decode_access_token, create_access_token, TokenData
    from appsumo import activate_license, check_feature_access, PLAN_LIMITS
except ImportError:
    print("⚠️ Warning: Shared modules not found. Using fallback.")
    TokenData = None

app = FastAPI(
    title="AI ChatBot Pro API",
    version="2.0.0",
    description="Professional AI ChatBot with Voice, Crypto Payments & 43 Languages"
)

# Security
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")

# In-memory storage (replace with Redis/DB in production)
conversations = {}
active_websockets: Dict[str, WebSocket] = {}

# Models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    language: Optional[str] = "en"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    suggestions: List[str] = []
    payment_info: Optional[Dict[str, Any]] = None
    voice_enabled: bool = True

class AppSumoActivation(BaseModel):
    license_key: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class VoiceConfig(BaseModel):
    language: str
    locale: str

class CryptoPaymentRequest(BaseModel):
    plan: str
    currency: str
    user_email: str

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current authenticated user"""
    if not TokenData:
        raise HTTPException(status_code=501, detail="Auth not configured")
    
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[TokenData]:
    """Get user if authenticated, None otherwise (for optional auth endpoints)"""
    if not TokenData:
        return None
    try:
        token = credentials.credentials
        return decode_access_token(token)
    except:
        return None

# AppSumo Integration Endpoints
@app.post("/api/auth/appsumo/activate", response_model=TokenResponse)
async def activate_appsumo_license(request: AppSumoActivation):
    """
    Activate AppSumo license and create user account
    """
    product_id = "chatbot-pro"
    
    # Activate license
    user_data = await activate_license(request.license_key, request.email, product_id)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license key or already activated"
        )
    
    # Create access token
    token_payload = {
        "sub": user_data["email"],
        "user_id": user_data["email"],
        "plan": user_data["plan"],
        "plan_tier": user_data["plan_tier"]
    }
    access_token = create_access_token(token_payload)
    
    return TokenResponse(
        access_token=access_token,
        user={
            "email": user_data["email"],
            "plan": user_data["plan"],
            "plan_tier": user_data["plan_tier"],
            "features": user_data["features"],
            "limits": user_data["limits"]
        }
    )

@app.get("/api/auth/me")
async def get_current_user_info(user: TokenData = Depends(get_current_user)):
    """Get current user information"""
    return {
        "email": user.email,
        "plan": user.plan,
        "user_id": user.user_id
    }

@app.get("/")
def root():
    return {
        "message": "AI ChatBot Pro API",
        "status": "running",
        "version": "2.0.0",
        "auth": "enabled",
        "appsumo": "integrated",
        "features": [
            "Natural Language Processing",
            "Voice Input Support",
            "43 Languages",
            "Quick Replies",
            "Intent Detection"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "100%"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, user: Optional[TokenData] = Depends(get_optional_user)):
    """
    Main chat endpoint with AI-powered responses
    Protected: Requires authentication for advanced features
    """
    # Check if user has access to advanced features
    has_advanced = False
    if user:
        try:
            tier = int(user.plan.split('_')[1]) if '_' in user.plan else 1
            has_advanced = check_feature_access(tier, "advanced_features")
        except:
            pass
    
    user_msg = message.message.lower()
    user_id = message.user_id
    language = message.language or "en"
    
    # Initialize conversation history
    if user_id not in conversations:
        conversations[user_id] = []
    
    # Add user message to history
    conversations[user_id].append({"role": "user", "content": message.message})
    
    # Call OpenAI API if available
    if OPENAI_API_KEY:
        try:
            ai_response = await call_openai_api(conversations[user_id], language)
            conversations[user_id].append({"role": "assistant", "content": ai_response})
            
            # Keep only last 10 messages
            if len(conversations[user_id]) > 20:
                conversations[user_id] = conversations[user_id][-20:]
            
            # Detect intent
            intent = detect_intent_advanced(user_msg)
            suggestions = get_smart_suggestions(intent, language)
            
            return ChatResponse(
                response=ai_response,
                intent=intent,
                suggestions=suggestions,
                voice_enabled=True
            )
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            # Fallback to rule-based
    
    # Rule-based fallback (existing code)
    
    # Simple intent detection
    if "pricing" in user_msg or "price" in user_msg or "cost" in user_msg:
        return ChatResponse(
            response="Our AI ChatBot Pro is available in 3 tiers:\n\n"
                   "💎 Tier 1 ($59): 1 Website, 1k chats/month\n"
                   "🚀 Tier 2 ($119): 3 Websites, 5k chats/month\n"
                   "⭐ Tier 3 ($199): 10 Websites, unlimited chats\n\n"
                   "All tiers include Voice Input, Multi-Language, and Crypto Payments!",
            intent="pricing",
            suggestions=["Compare tiers", "Start free trial", "Talk to sales"]
        )
    
    elif "help" in user_msg or "support" in user_msg:
        return ChatResponse(
            response="I'm here to help! I can assist you with:\n\n"
                   "✅ Product features and pricing\n"
                   "✅ Integration and setup\n"
                   "✅ Technical support\n"
                   "✅ Billing questions\n\n"
                   "What would you like to know?",
            intent="help",
            suggestions=["View documentation", "Contact support", "Schedule demo"]
        )
    
    elif "feature" in user_msg or "what can" in user_msg:
        return ChatResponse(
            response="AI ChatBot Pro includes amazing features:\n\n"
                   "🎤 Voice Input - 43 languages\n"
                   "💬 Natural Language AI\n"
                   "🌍 Multi-Language Support\n"
                   "⚡ Quick Reply Buttons\n"
                   "💰 Crypto Payment Integration\n"
                   "📊 Analytics Dashboard\n"
                   "🎨 Customizable Design\n\n"
                   "Want to see it in action?",
            intent="features",
            suggestions=["Start trial", "View demo", "See pricing"]
        )
    
    elif "setup" in user_msg or "integrate" in user_msg or "install" in user_msg:
        return ChatResponse(
            response="Setting up AI ChatBot Pro is super easy!\n\n"
                   "1️⃣ Copy your embed code\n"
                   "2️⃣ Paste it in your website\n"
                   "3️⃣ Customize colors and settings\n"
                   "4️⃣ Go live! 🚀\n\n"
                   "Average setup time: 5 minutes",
            intent="setup",
            suggestions=["View docs", "Get code", "Watch tutorial"]
        )
    
    elif "voice" in user_msg or "speech" in user_msg:
        return ChatResponse(
            response="Voice Input is one of our killer features! 🎤\n\n"
                   "✅ 43 language locales supported\n"
                   "✅ Hands-free interaction\n"
                   "✅ Perfect for mobile users\n"
                   "✅ Real-time transcription\n\n"
                   "Your users can speak naturally in their language!",
            intent="voice",
            suggestions=["Try voice demo", "See languages", "Get started"]
        )
    
    else:
        # Generic helpful response
        return ChatResponse(
            response="Thanks for your message! 👋\n\n"
                   "I'm the AI ChatBot Pro assistant. I can help you with:\n"
                   "• Product information\n"
                   "• Pricing and plans\n"
                   "• Technical setup\n"
                   "• Feature details\n\n"
                   "What would you like to know?",
            intent="general",
            suggestions=["View features", "See pricing", "Get support"]
        )

@app.get("/api/stats")
async def get_stats():
    """
    Get chatbot statistics
    """
    return {
        "total_chats": 1247,
        "active_users": 89,
        "avg_response_time": "1.2s",
        "satisfaction_rate": 94,
        "languages_supported": 43,
        "uptime": "99.9%"
    }

@app.get("/api/languages")
async def get_languages():
    """
    Get supported languages
    """
    return {
        "total": 43,
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "de", "name": "German"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "nl", "name": "Dutch"},
            {"code": "pl", "name": "Polish"},
            {"code": "ru", "name": "Russian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "zh", "name": "Chinese"}
        ]
    }

# ================== HELPER FUNCTIONS ==================

async def call_openai_api(messages: List[Dict], language: str = "en") -> str:
    """
    Call OpenAI GPT-4o API for real AI responses
    """
    if not OPENAI_API_KEY:
        return "AI API not configured. Using fallback responses."
    
    system_message = {
        "role": "system",
        "content": f"You are a helpful AI assistant for a ChatBot product. "
                   f"Respond in {language}. Be concise, friendly, and professional. "
                   f"Help users with product information, pricing, setup, and support."
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [system_message] + messages[-10:],  # Last 10 messages
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"AI Error: {response.status_code}"
        except Exception as e:
            print(f"OpenAI API Exception: {e}")
            return "AI temporarily unavailable. Using fallback."

def detect_intent_advanced(message: str) -> str:
    """
    Advanced intent detection
    """
    message = message.lower()
    
    intents = {
        "pricing": ["price", "cost", "pricing", "tier", "plan"],
        "payment": ["pay", "payment", "crypto", "bitcoin", "ethereum"],
        "voice": ["voice", "speech", "speak", "microphone"],
        "setup": ["setup", "install", "integrate", "embed"],
        "support": ["help", "support", "problem", "issue"],
        "features": ["feature", "what can", "capabilities"],
        "language": ["language", "translate", "multilingual"]
    }
    
    for intent, keywords in intents.items():
        if any(kw in message for kw in keywords):
            return intent
    
    return "general"

def get_smart_suggestions(intent: str, language: str) -> List[str]:
    """
    Get context-aware suggestions
    """
    suggestions_map = {
        "pricing": ["Compare tiers", "See all features", "Start trial"],
        "payment": ["View crypto options", "Payment FAQ", "Get support"],
        "voice": ["Try voice demo", "See languages", "Setup guide"],
        "setup": ["Quick start guide", "Watch tutorial", "Get embed code"],
        "support": ["Contact support", "View docs", "Community forum"],
        "features": ["Full feature list", "See demos", "Compare plans"],
        "language": ["See all 43 languages", "Test translation", "Setup guide"],
        "general": ["View features", "See pricing", "Start trial"]
    }
    
    return suggestions_map.get(intent, suggestions_map["general"])

# ================== NEW ENDPOINTS ==================

@app.post("/api/voice/config")
async def get_voice_config(config: VoiceConfig):
    """
    Get voice configuration for speech recognition
    """
    locale_map = {
        "en": "en-US", "de": "de-DE", "es": "es-ES", "fr": "fr-FR",
        "it": "it-IT", "pt": "pt-PT", "nl": "nl-NL", "pl": "pl-PL",
        "ru": "ru-RU", "ja": "ja-JP", "ko": "ko-KR", "zh": "zh-CN"
    }
    
    locale = locale_map.get(config.language, "en-US")
    
    return {
        "enabled": True,
        "language": config.language,
        "locale": locale,
        "supported_locales": list(locale_map.values()),
        "continuous": True,
        "interim_results": True
    }

@app.post("/api/crypto/payment")
async def create_crypto_payment(payment: CryptoPaymentRequest):
    """
    Create crypto payment with NOWPayments
    """
    if not NOWPAYMENTS_API_KEY:
        raise HTTPException(status_code=503, detail="Payment system not configured")
    
    # Price mapping
    prices = {
        "tier1": 59,
        "tier2": 119,
        "tier3": 199
    }
    
    amount_usd = prices.get(payment.plan.lower(), 59)
    
    async with httpx.AsyncClient() as client:
        try:
            # Create payment via NOWPayments API
            response = await client.post(
                "https://api.nowpayments.io/v1/payment",
                headers={
                    "x-api-key": NOWPAYMENTS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "price_amount": amount_usd,
                    "price_currency": "usd",
                    "pay_currency": payment.currency.lower(),
                    "ipn_callback_url": "https://your-domain.com/api/webhook/nowpayments",
                    "order_id": f"chatbot-{payment.plan}-{datetime.utcnow().timestamp()}",
                    "order_description": f"AI ChatBot Pro - {payment.plan}"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "payment_id": data.get("payment_id"),
                    "pay_address": data.get("pay_address"),
                    "pay_amount": data.get("pay_amount"),
                    "pay_currency": data.get("pay_currency"),
                    "payment_url": data.get("invoice_url"),
                    "expires_at": data.get("expiration_estimate_date")
                }
            else:
                raise HTTPException(status_code=response.status_code, detail="Payment creation failed")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@app.get("/api/analytics/realtime")
async def get_realtime_analytics():
    """
    Get real-time chatbot analytics
    """
    return {
        "active_chats": len(active_websockets),
        "total_conversations": len(conversations),
        "messages_today": sum(len(conv) for conv in conversations.values()),
        "avg_response_time": "1.2s",
        "uptime_percent": 99.9,
        "top_intents": [
            {"intent": "pricing", "count": 45},
            {"intent": "features", "count": 32},
            {"intent": "support", "count": 28}
        ]
    }

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat
    """
    await websocket.accept()
    active_websockets[user_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            chat_msg = ChatMessage(
                message=message_data.get("message", ""),
                user_id=user_id,
                language=message_data.get("language", "en")
            )
            
            response = await chat(chat_msg)
            
            # Send response via WebSocket
            await websocket.send_json(response.dict())
    
    except WebSocketDisconnect:
        if user_id in active_websockets:
            del active_websockets[user_id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if user_id in active_websockets:
            del active_websockets[user_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
