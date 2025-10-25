"""
Advanced Analytics Service
Premium analytics with real-time data, drill-down, and exports
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, case
from sqlalchemy.orm import Session
# TODO: Models need to be created - commented out for now
# from app.models.trace import Trace
# from app.models.case import Case
# from app.models.alert import Alert
import json
from collections import defaultdict
import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class RealtimeAnalyticsService:
    """Real-Time Analytics with Enterprise-Grade Features (formerly AdvancedAnalyticsService)"""

    def __init__(self, db: Session):
        self.db = db

    # ===================================
    # REAL-TIME METRICS
    # ===================================

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)

        # TODO: Trace/Case/Alert models not yet created - returning mock data
        active_traces = 0  # Mock
        active_cases = 0  # Mock
        critical_alerts = 0  # Mock
        
        # # Active traces (last hour)
        # active_traces = self.db.query(func.count(Trace.id)).filter(
        #     Trace.created_at >= last_hour
        # ).scalar() or 0

        # # Active cases
        # active_cases = self.db.query(func.count(Case.id)).filter(
        #     Case.status.in_(['open', 'in_progress'])
        # ).scalar() or 0

        # # Critical alerts (last 24h)
        # critical_alerts = self.db.query(func.count(Alert.id)).filter(
        #     and_(
        #         Alert.created_at >= last_24h,
        #         Alert.severity == 'critical'
        #     )
        # ).scalar() or 0

        # Active users (last 24h)
        active_users = 0  # Mock
        # active_users = self.db.query(func.count(func.distinct(Trace.user_id))).filter(
        #     Trace.created_at >= last_24h
        # ).scalar() or 0

        return {
            'active_traces': active_traces,
            'active_cases': active_cases,
            'critical_alerts': critical_alerts,
            'active_users': active_users,
            'timestamp': now.isoformat(),
        }

    # ===================================
    # TOP THREAT CATEGORIES
    # ===================================

    def get_top_threat_categories(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top threat categories with counts"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Query alerts grouped by category
        query = (
            self.db.query(
                Alert.category,
                func.count(Alert.id).label('count'),
                func.avg(Alert.risk_score).label('avg_risk_score')
            )
            .filter(
                and_(
                    Alert.created_at >= start_date,
                    Alert.created_at <= end_date
                )
            )
            .group_by(Alert.category)
            .order_by(func.count(Alert.id).desc())
            .limit(limit)
        )

        results = query.all()

        return [
            {
                'category': row.category or 'Unknown',
                'count': row.count,
                'avg_risk_score': round(float(row.avg_risk_score or 0), 2),
                'percentage': 0,  # Will be calculated after
            }
            for row in results
        ]

    # ===================================
    # RISK DISTRIBUTION OVER TIME
    # ===================================

    def get_risk_distribution_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = 'day'
    ) -> List[Dict[str, Any]]:
        """Get risk score distribution over time"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Define risk buckets
        risk_buckets = case(
            (Trace.risk_score >= 81, 'critical'),
            (Trace.risk_score >= 61, 'high'),
            (Trace.risk_score >= 31, 'medium'),
            else_='low'
        )

        # Group by date and risk level
        if interval == 'day':
            date_trunc = func.date_trunc('day', Trace.created_at)
        elif interval == 'week':
            date_trunc = func.date_trunc('week', Trace.created_at)
        elif interval == 'month':
            date_trunc = func.date_trunc('month', Trace.created_at)
        else:
            date_trunc = func.date_trunc('day', Trace.created_at)

        query = (
            self.db.query(
                date_trunc.label('date'),
                risk_buckets.label('risk_level'),
                func.count(Trace.id).label('count')
            )
            .filter(
                and_(
                    Trace.created_at >= start_date,
                    Trace.created_at <= end_date
                )
            )
            .group_by('date', 'risk_level')
            .order_by('date')
        )

        results = query.all()

        # Transform to time series format
        data_by_date = defaultdict(lambda: {'critical': 0, 'high': 0, 'medium': 0, 'low': 0})
        for row in results:
            date_str = row.date.isoformat() if row.date else 'unknown'
            data_by_date[date_str][row.risk_level] = row.count

        return [
            {
                'date': date,
                'critical': counts['critical'],
                'high': counts['high'],
                'medium': counts['medium'],
                'low': counts['low'],
                'total': sum(counts.values()),
            }
            for date, counts in sorted(data_by_date.items())
        ]

    # ===================================
    # GEOGRAPHIC HEAT MAP
    # ===================================

    def get_geographic_distribution(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get threat distribution by country (based on user IP or entity labels)"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # TODO: Implement IP geolocation or use entity labels
        # For now, return mock data structure
        return [
            {'country': 'US', 'count': 245, 'avg_risk_score': 65.3},
            {'country': 'CN', 'count': 189, 'avg_risk_score': 78.9},
            {'country': 'RU', 'count': 156, 'avg_risk_score': 82.1},
            {'country': 'DE', 'count': 134, 'avg_risk_score': 45.2},
            {'country': 'GB', 'count': 98, 'avg_risk_score': 52.7},
        ]

    # ===================================
    # TOP EXCHANGES & MIXERS
    # ===================================

    def get_top_entities(
        self,
        entity_type: str,  # 'exchange' or 'mixer'
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top exchanges or mixers by transaction volume"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # TODO: Query from labels database
        # For now, return mock data
        if entity_type == 'exchange':
            return [
                {'name': 'Binance', 'count': 1245, 'volume_usd': 45600000},
                {'name': 'Coinbase', 'count': 987, 'volume_usd': 32100000},
                {'name': 'Kraken', 'count': 654, 'volume_usd': 18900000},
                {'name': 'Huobi', 'count': 543, 'volume_usd': 15600000},
                {'name': 'Bitfinex', 'count': 432, 'volume_usd': 12300000},
            ]
        else:  # mixer
            return [
                {'name': 'Tornado Cash', 'count': 234, 'volume_usd': 8900000},
                {'name': 'ChipMixer', 'count': 156, 'volume_usd': 5600000},
                {'name': 'Blender.io', 'count': 89, 'volume_usd': 2100000},
                {'name': 'CoinJoin', 'count': 67, 'volume_usd': 1800000},
            ]

    # ===================================
    # COMPARISON MODE
    # ===================================

    def get_comparison_data(
        self,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict[str, Any]:
        """Compare two time periods"""

        def get_period_stats(start: datetime, end: datetime) -> Dict[str, Any]:
            # Total traces
            total_traces = self.db.query(func.count(Trace.id)).filter(
                and_(Trace.created_at >= start, Trace.created_at <= end)
            ).scalar() or 0

            # Avg risk score
            avg_risk = self.db.query(func.avg(Trace.risk_score)).filter(
                and_(Trace.created_at >= start, Trace.created_at <= end)
            ).scalar() or 0

            # Critical alerts
            critical_alerts = self.db.query(func.count(Alert.id)).filter(
                and_(
                    Alert.created_at >= start,
                    Alert.created_at <= end,
                    Alert.severity == 'critical'
                )
            ).scalar() or 0

            return {
                'total_traces': total_traces,
                'avg_risk_score': round(float(avg_risk), 2),
                'critical_alerts': critical_alerts,
            }

        period1 = get_period_stats(period1_start, period1_end)
        period2 = get_period_stats(period2_start, period2_end)

        # Calculate changes
        changes = {}
        for key in period1.keys():
            val1 = period1[key]
            val2 = period2[key]
            if val2 != 0:
                change_pct = ((val1 - val2) / val2) * 100
            else:
                change_pct = 100 if val1 > 0 else 0
            changes[f'{key}_change'] = round(change_pct, 2)

        return {
            'period1': period1,
            'period2': period2,
            'changes': changes,
        }

    # ===================================
    # DRILL-DOWN
    # ===================================

    def drill_down_category(
        self,
        category: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get detailed alerts for a specific category"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = (
            self.db.query(Alert)
            .filter(
                and_(
                    Alert.category == category,
                    Alert.created_at >= start_date,
                    Alert.created_at <= end_date
                )
            )
            .order_by(Alert.risk_score.desc())
            .limit(limit)
        )

        results = query.all()

        return [
            {
                'id': alert.id,
                'address': alert.address,
                'risk_score': alert.risk_score,
                'severity': alert.severity,
                'message': alert.message,
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
            }
            for alert in results
        ]

    # ===================================
    # EXPORTS
    # ===================================

    def export_to_csv(self, data: List[Dict[str, Any]]) -> BytesIO:
        """Export data to CSV"""
        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer

    def export_to_excel(self, data_sheets: Dict[str, List[Dict[str, Any]]]) -> BytesIO:
        """Export multiple datasets to Excel with sheets"""
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            for sheet_name, data in data_sheets.items():
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)  # Excel limits sheet names to 31 chars
        buffer.seek(0)
        return buffer

    def export_to_json(self, data: Any) -> str:
        """Export data to JSON"""
        return json.dumps(data, indent=2, default=str)

    # ===================================
    # SAVED DASHBOARDS
    # ===================================

    def save_dashboard_config(
        self,
        user_id: int,
        config_name: str,
        config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save dashboard configuration for user"""
        # TODO: Store in database (UserDashboardConfig table)
        return {
            'id': 'mock-id-123',
            'user_id': user_id,
            'config_name': config_name,
            'config_data': config_data,
            'created_at': datetime.utcnow().isoformat(),
        }

    def get_saved_dashboards(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's saved dashboard configurations"""
        # TODO: Query from database
        return [
            {
                'id': 'default',
                'config_name': 'Default Dashboard',
                'config_data': {},
                'created_at': datetime.utcnow().isoformat(),
            }
        ]
