"""
AI-Powered Analytics Engine
Auto-Optimization & Predictive Insights
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class AIAnalyticsEngine:
    """
    KI-basierte Analytics & Auto-Optimization
    
    Features:
    - Conversion Prediction (ML-based)
    - Churn Risk Detection
    - Behavior Pattern Recognition
    - Performance Issue Detection
    - Auto-Generated Optimizations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """
        Analyze single session with AI
        
        Returns:
        - Conversion Probability
        - Engagement Score
        - Drop-Off Risk
        - Recommended Actions
        """
        from app.models.analytics_data import AnalyticsEvent
        
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.session_id == session_id
        ).order_by(AnalyticsEvent.created_at).all()
        
        if not events:
            return {"error": "Session not found"}
        
        # Calculate Metrics
        total_time = sum(e.behavior.get('timeOnPage', 0) for e in events)
        total_clicks = sum(len(e.behavior.get('clicks', [])) for e in events)
        avg_scroll_depth = sum(e.behavior.get('scrollDepth', 0) for e in events) / len(events) if events else 0
        total_errors = sum(len(e.errors) for e in events)
        
        # Simple Scoring (can upgrade to ML model)
        engagement_score = min(1.0, (total_time / 300) * 0.4 + (total_clicks / 20) * 0.3 + (avg_scroll_depth / 100) * 0.3)
        
        # Conversion Probability
        conversion_prob = self._predict_conversion(events)
        
        # Churn Risk
        churn_risk = self._predict_churn(events)
        
        # Recommendations
        recommendations = []
        if engagement_score < 0.3:
            recommendations.append("Low engagement. Consider adding interactive elements.")
        if avg_scroll_depth < 30:
            recommendations.append("Low scroll depth. Move key content higher.")
        if total_errors > 2:
            recommendations.append(f"{total_errors} errors detected. Fix immediately!")
        if conversion_prob < 0.2:
            recommendations.append("Low conversion probability. Consider showing discount or demo.")
        
        return {
            "session_id": session_id,
            "engagement_score": round(engagement_score, 2),
            "conversion_probability": round(conversion_prob, 2),
            "churn_risk": round(churn_risk, 2),
            "metrics": {
                "total_time_seconds": total_time,
                "total_clicks": total_clicks,
                "avg_scroll_depth": round(avg_scroll_depth, 1),
                "total_errors": total_errors,
                "pages_visited": len(set(e.page_url for e in events))
            },
            "recommendations": recommendations
        }
    
    async def analyze_user(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Analyze user across multiple sessions
        """
        from app.models.analytics_data import AnalyticsEvent
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        events = self.db.query(AnalyticsEvent).filter(
            and_(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.created_at >= start_date
            )
        ).order_by(AnalyticsEvent.created_at).all()
        
        if not events:
            return {"error": "No data for user"}
        
        sessions = set(e.session_id for e in events)
        
        # Aggregate metrics
        total_time = sum(e.behavior.get('timeOnPage', 0) for e in events)
        total_clicks = sum(len(e.behavior.get('clicks', [])) for e in events)
        pages_visited = set(e.page_url for e in events)
        
        # Behavior patterns
        patterns = self._detect_behavior_patterns(events)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "sessions_count": len(sessions),
            "total_time_seconds": total_time,
            "total_clicks": total_clicks,
            "pages_visited": len(pages_visited),
            "behavior_patterns": patterns,
            "is_power_user": len(sessions) > 10,
            "retention_risk": "low" if len(sessions) > 5 else "high"
        }
    
    async def analyze_global(self, days: int = 7) -> Dict[str, Any]:
        """
        Global Analytics with AI Insights
        """
        from app.models.analytics_data import AnalyticsEvent
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.created_at >= start_date
        ).all()
        
        if not events:
            return {"error": "No data"}
        
        # Global Metrics
        total_sessions = len(set(e.session_id for e in events))
        total_users = len(set(e.user_id for e in events if e.user_id))
        
        # Performance Issues
        slow_pages = self._detect_slow_pages(events)
        error_prone_pages = self._detect_error_prone_pages(events)
        
        # Drop-Off Points
        drop_offs = self._detect_drop_off_points(events)
        
        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "total_users": total_users,
            "total_events": len(events),
            "performance_issues": {
                "slow_pages": slow_pages[:5],  # Top 5
            },
            "error_prone_pages": error_prone_pages[:5],
            "drop_off_points": drop_offs[:5]
        }
    
    async def generate_optimizations(self) -> List[Dict[str, Any]]:
        """
        Auto-Generate Optimizations
        
        AI analyzes data and suggests:
        - A/B Test Variants
        - Performance Fixes
        - UI/UX Improvements
        """
        from app.models.analytics_data import AnalyticsEvent, AutoOptimization
        
        # Analyze last 7 days
        start_date = datetime.utcnow() - timedelta(days=7)
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.created_at >= start_date
        ).all()
        
        if not events:
            return []
        
        optimizations = []
        
        # 1. Slow Pages → Performance Optimization
        slow_pages = self._detect_slow_pages(events)
        for page in slow_pages[:3]:
            opt = AutoOptimization(
                optimization_type='performance',
                target_page=page['url'],
                description=f"Page load time is {page['avg_load']}ms (slow)",
                rationale="Slow pages increase bounce rate by 40%",
                expected_impact="+15% retention",
                implementation_code="// Add lazy loading, compress images, minify JS",
                priority=9,
                confidence=0.9
            )
            self.db.add(opt)
            optimizations.append({
                "type": "performance",
                "target": page['url'],
                "issue": f"{page['avg_load']}ms load time",
                "suggestion": "Optimize assets, lazy load images"
            })
        
        # 2. Low Engagement Elements → UI/UX Improvement
        low_engagement = self._detect_low_engagement_elements(events)
        for element in low_engagement[:2]:
            opt = AutoOptimization(
                optimization_type='ui_ux',
                target_element=element['selector'],
                description=f"Element '{element['selector']}' has low click rate ({element['clicks']} clicks)",
                rationale="Low engagement suggests poor visibility or unclear CTA",
                expected_impact="+25% click-through rate",
                ab_test_variants={
                    "A": "Current design",
                    "B": "Larger button with gradient",
                    "C": "Animated pulse effect"
                },
                priority=7,
                confidence=0.75
            )
            self.db.add(opt)
            optimizations.append({
                "type": "ui_ux",
                "target": element['selector'],
                "issue": f"Only {element['clicks']} clicks",
                "suggestion": "A/B test: Larger button, gradient, animation"
            })
        
        # 3. Error-Prone Pages → Error Fix
        error_pages = self._detect_error_prone_pages(events)
        for page in error_pages[:2]:
            opt = AutoOptimization(
                optimization_type='error_fix',
                target_page=page['url'],
                description=f"Page has {page['error_count']} errors",
                rationale="Errors degrade user experience and trust",
                expected_impact="+10% satisfaction",
                implementation_code="// Review console errors, add error boundaries",
                priority=10,
                confidence=1.0
            )
            self.db.add(opt)
            optimizations.append({
                "type": "error_fix",
                "target": page['url'],
                "issue": f"{page['error_count']} errors",
                "suggestion": "Debug and fix errors immediately"
            })
        
        self.db.commit()
        
        return optimizations
    
    def _predict_conversion(self, events: List) -> float:
        """Simple conversion prediction (upgrade to ML model)"""
        if not events:
            return 0.0
        
        # Simple heuristic (can upgrade to trained ML model)
        latest = events[-1]
        time_on_page = latest.behavior.get('timeOnPage', 0)
        scroll_depth = latest.behavior.get('scrollDepth', 0)
        clicks = len(latest.behavior.get('clicks', []))
        
        score = min(1.0, (time_on_page / 180) * 0.4 + (scroll_depth / 100) * 0.3 + (clicks / 10) * 0.3)
        return score
    
    def _predict_churn(self, events: List) -> float:
        """Churn risk prediction"""
        if not events:
            return 1.0
        
        latest = events[-1]
        errors = len(latest.errors)
        time_on_page = latest.behavior.get('timeOnPage', 0)
        
        # High errors = high churn risk
        # Low time = high churn risk
        churn = min(1.0, (errors / 5) * 0.5 + (1 - min(1.0, time_on_page / 120)) * 0.5)
        return churn
    
    def _detect_behavior_patterns(self, events: List) -> List[str]:
        """Detect user behavior patterns"""
        patterns = []
        
        if not events:
            return patterns
        
        # Check if user scrolls a lot
        avg_scroll = sum(e.behavior.get('scrollDepth', 0) for e in events) / len(events)
        if avg_scroll > 70:
            patterns.append("Deep reader - scrolls through content")
        
        # Check if user clicks a lot
        total_clicks = sum(len(e.behavior.get('clicks', [])) for e in events)
        if total_clicks > 50:
            patterns.append("Active explorer - clicks many elements")
        
        # Check session frequency
        sessions = set(e.session_id for e in events)
        if len(sessions) > 5:
            patterns.append("Frequent visitor - returns often")
        
        return patterns
    
    def _detect_slow_pages(self, events: List) -> List[Dict[str, Any]]:
        """Find pages with slow load times"""
        page_loads = {}
        
        for event in events:
            url = event.page_url
            load_time = event.performance.get('pageLoad', 0)
            
            if load_time > 0:
                if url not in page_loads:
                    page_loads[url] = []
                page_loads[url].append(load_time)
        
        results = []
        for url, times in page_loads.items():
            avg = sum(times) / len(times)
            if avg > 3000:  # > 3 seconds
                results.append({
                    "url": url,
                    "avg_load": round(avg, 0),
                    "samples": len(times)
                })
        
        return sorted(results, key=lambda x: x['avg_load'], reverse=True)
    
    def _detect_error_prone_pages(self, events: List) -> List[Dict[str, Any]]:
        """Find pages with most errors"""
        page_errors = {}
        
        for event in events:
            url = event.page_url
            error_count = len(event.errors)
            
            if error_count > 0:
                page_errors[url] = page_errors.get(url, 0) + error_count
        
        results = [
            {"url": url, "error_count": count}
            for url, count in page_errors.items()
        ]
        
        return sorted(results, key=lambda x: x['error_count'], reverse=True)
    
    def _detect_drop_off_points(self, events: List) -> List[Dict[str, Any]]:
        """Find where users drop off"""
        page_exits = {}
        page_entries = {}
        
        for event in events:
            url = event.page_url
            page_entries[url] = page_entries.get(url, 0) + 1
            
            # Simple heuristic: low time = drop-off
            if event.behavior.get('timeOnPage', 0) < 10:
                page_exits[url] = page_exits.get(url, 0) + 1
        
        results = []
        for url in page_entries:
            entries = page_entries[url]
            exits = page_exits.get(url, 0)
            drop_off_rate = (exits / entries * 100) if entries > 0 else 0
            
            if drop_off_rate > 50:
                results.append({
                    "url": url,
                    "drop_off_rate": round(drop_off_rate, 1),
                    "entries": entries,
                    "exits": exits
                })
        
        return sorted(results, key=lambda x: x['drop_off_rate'], reverse=True)
    
    def _detect_low_engagement_elements(self, events: List) -> List[Dict[str, Any]]:
        """Find elements with low engagement"""
        element_clicks = {}
        
        for event in events:
            clicks = event.behavior.get('clicks', [])
            for click in clicks:
                selector = click.get('element', 'unknown')
                element_clicks[selector] = element_clicks.get(selector, 0) + 1
        
        # Elements that should be clicked but aren't
        # (Simple heuristic - can improve with ML)
        cta_elements = [sel for sel in element_clicks if 'button' in sel.lower() or 'cta' in sel.lower()]
        
        results = [
            {"selector": sel, "clicks": clicks}
            for sel, clicks in element_clicks.items()
            if clicks < 10 and sel in cta_elements
        ]
        
        return sorted(results, key=lambda x: x['clicks'])
