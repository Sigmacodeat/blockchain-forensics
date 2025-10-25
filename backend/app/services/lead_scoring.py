"""
Lead Scoring Engine
Scores leads 0-100 based on engagement, intent, and demographic signals.

Routing:
- 85-100: SQL (Sales-Qualified Lead) → Alert Sales + Founder Intro
- 70-84: MQL (Marketing-Qualified Lead) → Drip Campaign
- 0-69: Cold Lead → Newsletter

Expected Conversion:
- SQL → Trial: 60%+
- MQL → Trial: 25%+
- Cold → Trial: 5%+
"""

import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class LeadScoringEngine:
    """
    Lead scoring with behavioral + demographic signals
    """
    
    def calculate_score(self, session_data: Dict) -> int:
        """
        Calculate lead score (0-100)
        
        Args:
            session_data: User behavior and demographic data
            
        Returns:
            Score 0-100
        """
        score = 0
        
        # === ENGAGEMENT SIGNALS (max 35 points) ===
        time_on_site = session_data.get("time_on_site", 0)
        if time_on_site > 300:  score += 20  # 5+ minutes
        elif time_on_site > 180: score += 15  # 3-5 minutes
        elif time_on_site > 60:  score += 10  # 1-3 minutes
        
        pages_viewed = session_data.get("pages_viewed", 0)
        if pages_viewed >= 5:   score += 15
        elif pages_viewed >= 3: score += 10
        elif pages_viewed >= 2: score += 5
        
        # === INTENT SIGNALS (max 50 points - highest weight!) ===
        if session_data.get("pricing_viewed"):      score += 25
        if session_data.get("demo_requested"):      score += 30
        if session_data.get("pricing_compared"):    score += 20
        if session_data.get("trial_clicked"):       score += 40
        if session_data.get("chatbot_engaged"):     score += 20
        if session_data.get("case_study_downloaded"): score += 25
        
        # === DEMOGRAPHIC SIGNALS (max 25 points) ===
        company_size = session_data.get("company_size", "")
        if company_size == "enterprise":  score += 15
        elif company_size == "medium":    score += 10
        elif company_size == "small":     score += 5
        
        role = session_data.get("role", "")
        if role in ["C-Level", "Director", "VP"]:  score += 20
        elif role in ["Manager", "Lead"]:          score += 10
        
        industry = session_data.get("industry", "")
        if industry in ["banking", "law_enforcement", "exchange"]:  score += 25
        elif industry in ["fintech", "crypto"]:  score += 15
        
        # === NEGATIVE SIGNALS (penalties) ===
        if session_data.get("exit_intent_dismissed"):  score -= 10
        if session_data.get("bounce_rate_history", 0) > 0.7:  score -= 15
        if session_data.get("chat_ignored"):  score -= 5
        
        return min(100, max(0, score))
    
    async def route_lead(self, lead_score: int, user_data: Dict):
        """
        Smart routing: Don't waste sales time on low-intent!
        
        Args:
            lead_score: Score 0-100
            user_data: User information
        """
        user_id = user_data.get("user_id")
        email = user_data.get("email")
        
        if lead_score >= 85:  # SQL
            logger.info(f"SQL detected: {email} (score: {lead_score})")
            
            # 1. Alert Sales Team (Slack/Email)
            await self._alert_sales_team({
                "lead_id": user_id,
                "score": lead_score,
                "email": email,
                "context": user_data,
                "priority": "HIGH",
                "action": "Call within 1 hour",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 2. Send Founder-Intro Email
            await self._send_email(
                to=email,
                template="founder_intro",
                subject="Quick intro from SIGMACODE founder",
                context={
                    "name": user_data.get("name"),
                    "calendly_link": "https://calendly.com/sigmacode-founder/30min"
                }
            )
            
            # 3. Add to CRM (HubSpot) with "Hot Lead" Tag
            await self._add_to_crm(user_data, tags=["SQL", "Hot"])
        
        elif lead_score >= 70:  # MQL
            logger.info(f"MQL detected: {email} (score: {lead_score})")
            
            # 1. Enroll in 7-Day Nurture Campaign
            await self._enroll_in_drip_campaign(
                email=email,
                campaign="7_day_nurture",
                context=user_data
            )
            
            # 2. Add to CRM with "Warm Lead" Tag
            await self._add_to_crm(user_data, tags=["MQL", "Warm"])
        
        else:  # Cold Lead
            logger.info(f"Cold lead: {email} (score: {lead_score})")
            
            # Just newsletter signup
            await self._add_to_newsletter(email)
            await self._add_to_crm(user_data, tags=["Cold", "Newsletter"])
    
    async def _alert_sales_team(self, alert_data: Dict):
        """Send alert to sales team (Slack/Email)"""
        # TODO: Implement Slack webhook
        logger.info(f"Sales alert: {alert_data}")
    
    async def _send_email(self, to: str, template: str, subject: str, context: Dict):
        """Send email via email service"""
        # TODO: Implement email service (SendGrid/Mailchimp)
        logger.info(f"Email sent to {to}: {subject}")
    
    async def _enroll_in_drip_campaign(self, email: str, campaign: str, context: Dict):
        """Enroll in automated drip campaign"""
        # TODO: Implement drip campaign enrollment
        logger.info(f"Enrolled {email} in campaign: {campaign}")
    
    async def _add_to_crm(self, user_data: Dict, tags: list):
        """Add lead to CRM (HubSpot/Salesforce)"""
        # TODO: Implement CRM integration
        logger.info(f"Added to CRM: {user_data.get('email')} with tags: {tags}")
    
    async def _add_to_newsletter(self, email: str):
        """Add to newsletter"""
        # TODO: Implement newsletter service
        logger.info(f"Added to newsletter: {email}")


# Global instance
lead_scoring_engine = LeadScoringEngine()
