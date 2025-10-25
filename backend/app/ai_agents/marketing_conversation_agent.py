"""
Marketing Conversation Agent: 5-Stage Conversion Funnel
Optimizes chatbot conversations for maximum conversion (Target: 18%+)

Stages:
1. AWARENESS: 10s after landing, context-aware greeting
2. INTEREST: Role qualification, personalized value-prop
3. CONSIDERATION: Objection handling with social proof
4. INTENT: Strong buying signals, push to trial
5. PURCHASE: Remove friction, confirm choice
"""

import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationStage(BaseModel):
    """Represents a stage in the conversion funnel"""
    stage: str
    user_context: Dict[str, Any]
    next_message: str
    cta_buttons: List[str]
    tracking_event: str


class MarketingConversationAgent:
    """
    Psychologically optimized conversation flow for maximum conversion.
    
    Performance Goals:
    - Engagement Rate: 30%+
    - Conversation Rate: 18%+
    - MQL Rate: 40%+ (from engaged users)
    """
    
    def __init__(self):
        self.user_contexts: Dict[str, Dict] = {}
    
    async def determine_stage(self, session_id: str, user_data: Dict) -> str:
        """Smart stage detection based on user behavior"""
        context = self.user_contexts.get(session_id, {})
        
        # Check for strong intent signals first (highest priority)
        if user_data.get("trial_clicked"):
            return "purchase"
        
        if (user_data.get("time_on_site", 0) > 300 and 
            user_data.get("pricing_viewed") and
            user_data.get("pages_viewed", 0) >= 3):
            return "intent"
        
        if context.get("objection_raised"):
            return "consideration"
        
        if context.get("role_identified"):
            return "interest"
        
        # Default: First interaction
        return "awareness"
    
    async def get_response(self, session_id: str, user_data: Dict) -> ConversationStage:
        """Main entry point - routes to appropriate stage handler"""
        stage = await self.determine_stage(session_id, user_data)
        
        handlers = {
            "awareness": self._stage_awareness,
            "interest": self._stage_interest,
            "consideration": self._stage_consideration,
            "intent": self._stage_intent,
            "purchase": self._stage_purchase
        }
        
        handler = handlers.get(stage, self._stage_awareness)
        return await handler(session_id, user_data)
    
    async def _stage_awareness(self, session_id: str, user_data: Dict) -> ConversationStage:
        """
        TIMING: 10 seconds after landing (not immediately!)
        PSYCHOLOGY: Curiosity + Value-First (not pushy!)
        """
        section_viewed = user_data.get("current_section", "hero")
        
        messages = {
            "pricing": {
                "message": "👋 Hey! Ich bin Max, dein persönlicher Forensics-Berater.\n\n"
                          "Sehe gerade, du vergleichst Preise. Kann ich dir in 60 Sekunden "
                          "den perfekten Plan für dein Team empfehlen?",
                "cta": ["Ja, zeig mir!", "Später"],
                "intent": "pricing_consultant"
            },
            "features": {
                "message": "🔍 Interessierst du dich für Transaction Tracing?\n\n"
                          "Ich kann dir eine 2-Minuten-Demo zeigen, speziell für "
                          "Law Enforcement / Exchanges / Banks.",
                "cta": ["Demo ansehen", "Mehr erfahren"],
                "intent": "feature_demo"
            },
            "testimonials": {
                "message": "💡 Die Case Studies sind beeindruckend, oder?\n\n"
                          "Möchtest du mit einem dieser Kunden sprechen? Ich kann "
                          "ein Intro machen.",
                "cta": ["Ja, gerne!", "Nein danke"],
                "intent": "customer_reference"
            },
            "default": {
                "message": "👋 Hi! Schnelle Frage: Untersuchst du Krypto-Betrug oder "
                          "baust du AML-Compliance auf?\n\n"
                          "(Hilft mir, dir relevante Beispiele zu zeigen)",
                "cta": ["🕵️ Fraud Investigation", "🏦 AML Compliance", "🤷 Anderes"],
                "intent": "role_identification"
            }
        }
        
        config = messages.get(section_viewed, messages["default"])
        
        return ConversationStage(
            stage="awareness",
            user_context={"section_viewed": section_viewed},
            next_message=config["message"],
            cta_buttons=config["cta"],
            tracking_event=f"chatbot_awareness_{config['intent']}"
        )
    
    async def _stage_interest(self, session_id: str, user_data: Dict) -> ConversationStage:
        """
        User engaged! Now: Personalized value proposition
        PSYCHOLOGY: Reciprocity (give value BEFORE asking)
        """
        role = user_data.get("role", "other")
        
        role_configs = {
            "fraud_investigation": {
                "message": "Perfekt! 🕵️ Für Ermittler wie dich sind die Top-3-Features:\n\n"
                          "**1. AI-Tracing** – 12 Hops in 8 Sekunden (statt 2 Wochen)\n"
                          "**2. Mixer-Demixing** – Tornado Cash Flows tracken (65% Erfolgsrate)\n"
                          "**3. Court Evidence** – PDF-Reports mit Chain-of-Custody\n\n"
                          "Welches Feature möchtest du in Aktion sehen?",
                "cta": ["⚡ Tracing-Demo", "🌪️ Mixer-Demo", "📄 Evidence-Demo"]
            },
            "aml_compliance": {
                "message": "Exzellent! 🏦 Für Compliance-Teams sind das die Zeitsparer:\n\n"
                          "**1. Real-Time KYT** – Jede Transaktion automatisch screenen\n"
                          "**2. OFAC/UN Sanctions** – 9 Jurisdiktionen, auto-updated\n"
                          "**3. Travel Rule** – FATF-konform, VASP-Screening\n\n"
                          "Möchtest du eine Custom-Demo für deine Exchange?",
                "cta": ["📅 Demo buchen", "💰 Pricing zeigen", "ℹ️ Mehr Info"]
            },
            "other": {
                "message": "Verstehe! 👍 Lass mich mehr über deinen Use-Case erfahren.\n\n"
                          "Was ist deine größte Herausforderung mit Krypto-Forensik?",
                "cta": ["Zeit (Wochen pro Fall)", "Kosten (Team-Overhead)", "Komplexität (100+ Chains)"]
            }
        }
        
        config = role_configs.get(role, role_configs["other"])
        
        # Store role in context
        self.user_contexts.setdefault(session_id, {})["role"] = role
        self.user_contexts[session_id]["role_identified"] = True
        
        return ConversationStage(
            stage="interest",
            user_context={"role": role},
            next_message=config["message"],
            cta_buttons=config["cta"],
            tracking_event=f"chatbot_interest_{role}"
        )
    
    async def _stage_consideration(self, session_id: str, user_data: Dict) -> ConversationStage:
        """
        Objection handling with social proof + risk reversal
        PSYCHOLOGY: Authority + Scarcity + Guarantee
        """
        objection = user_data.get("objection", "pricing")
        
        objection_responses = {
            "pricing": {
                "message": "💰 Absolut nachvollziehbar – Budget ist wichtig!\n\n"
                          "Hier die ROI-Rechnung:\n\n"
                          "**Manuell**: 40h × $75/h = **$3,000 pro Fall**\n"
                          "**Mit SIGMACODE**: 4h × $75/h = **$300 pro Fall**\n\n"
                          "→ Break-even nach nur **1 Fall/Monat**\n\n"
                          "**Plus**:\n"
                          "✅ 14 Tage gratis testen (keine Kreditkarte)\n"
                          "✅ Jederzeit kündbar\n"
                          "✅ **ROI-Garantie**: Keine 10h+ gespart in Monat 1? 100% Geld zurück!\n\n"
                          "Klingt fair?",
                "cta": ["🚀 Gratis-Test starten", "📞 Sales anrufen", "📊 Case Study lesen"]
            },
            "security": {
                "message": "🔒 Security ist unsere #1 Priorität (besonders für Law Enforcement!):\n\n"
                          "**Zertifizierungen**:\n"
                          "✅ **SOC2 Type II** (audited annually)\n"
                          "✅ **ISO 27001** compliant\n"
                          "✅ **GDPR/CCPA** ready\n\n"
                          "**Deployment**:\n"
                          "✅ Cloud (AWS/GCP) ODER Self-Hosted\n"
                          "✅ Air-gapped Deployment verfügbar\n"
                          "✅ End-to-End Encryption (AES-256)\n\n"
                          "**Trust**: Genutzt von FBI, Interpol, BKA\n\n"
                          "Möchtest du unser Security-Whitepaper?",
                "cta": ["📄 Whitepaper Download", "👨‍💻 Security-Team sprechen", "✅ Okay, überzeugt!"]
            }
        }
        
        config = objection_responses.get(objection, objection_responses["pricing"])
        
        # Track objection
        self.user_contexts.setdefault(session_id, {})["objection_raised"] = objection
        
        return ConversationStage(
            stage="consideration",
            user_context={"objection": objection},
            next_message=config["message"],
            cta_buttons=config["cta"],
            tracking_event=f"chatbot_objection_{objection}"
        )
    
    async def _stage_intent(self, session_id: str, user_data: Dict) -> ConversationStage:
        """
        Strong buying signals detected! Push to trial.
        PSYCHOLOGY: Commitment & Consistency
        """
        time_on_site = user_data.get("time_on_site", 0)
        pages_viewed = user_data.get("pages_viewed", 0)
        
        message = f"🎯 Du bist jetzt seit **{time_on_site//60} Minuten** hier und hast **{pages_viewed} Seiten** angeschaut.\n\n"
        message += "Offensichtlich ernsthaftes Interesse! 😊\n\n"
        message += "**Was passiert als Nächstes**:\n\n"
        message += "1. Klick 'Trial starten' → **Sofortiger Zugang** (30 Sekunden)\n"
        message += "2. Onboarding-Wizard führt dich durch (2 Minuten)\n"
        message += "3. Starte **sofort mit Tracing** (funktioniert out-of-the-box)\n\n"
        message += "**Keine Kreditkarte. Jederzeit kündbar. 100% Risk-Free.**\n\n"
        message += "Bereit zum Loslegen?"
        
        return ConversationStage(
            stage="intent",
            user_context={"high_intent": True, "time_on_site": time_on_site},
            next_message=message,
            cta_buttons=["🚀 Ja, Trial starten!", "❓ Noch eine Frage..."],
            tracking_event="chatbot_high_intent"
        )
    
    async def _stage_purchase(self, session_id: str, user_data: Dict) -> ConversationStage:
        """
        Final push: Remove last friction
        PSYCHOLOGY: Loss Aversion
        """
        message = "🎉 **Perfekt! Lass uns loslegen...**\n\n"
        message += "Starte jetzt deinen **14-Tage-Gratis-Test**:\n\n"
        message += "✅ **Keine Kreditkarte** erforderlich\n"
        message += "✅ **Vollzugriff** auf alle Pro-Features\n"
        message += "✅ **Persönlicher Onboarding-Call** (wenn gewünscht)\n\n"
        message += "**Was du in den nächsten 60 Sekunden bekommst**:\n"
        message += "• Login-Credentials per Email\n"
        message += "• Quick-Start-Guide (5 min read)\n"
        message += "• Direkter Kalender-Link zu mir (für Fragen)\n\n"
        message += "Klick unten um Account zu erstellen 👇"
        
        return ConversationStage(
            stage="purchase",
            user_context={"conversion_ready": True},
            next_message=message,
            cta_buttons=["✅ Account erstellen", "📞 Lieber Sales-Call"],
            tracking_event="chatbot_trial_conversion"
        )


# Global instance
marketing_agent = MarketingConversationAgent()
