"""
Advanced Analytics Service
Funnel Analysis, Cohort Analysis, Retention Metrics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class AdvancedAnalyticsService:
    """Enterprise Analytics: Funnel, Cohort, Retention"""
    
    async def get_funnel_analysis(
        self,
        funnel_steps: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Funnel Analysis
        
        Example funnel_steps:
        - ['signup', 'first_login', 'first_trace', 'plan_upgrade']
        
        Returns conversion rates between steps
        """
        try:
            # Default date range: last 30 days
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            funnel_data = []
            total_users = 0
            
            for i, step in enumerate(funnel_steps):
                # Build query
                query = """
                    SELECT COUNT(DISTINCT user_id) as count
                    FROM web_events
                    WHERE event = $1
                    AND ts >= $2 AND ts <= $3
                """
                params = [step, start_date, end_date]
                
                # Add org filter if provided
                if org_id:
                    query += " AND org_id = $4"
                    params.append(org_id)
                
                # For subsequent steps, only count users who completed previous step
                if i > 0:
                    prev_step = funnel_steps[i - 1]
                    query = """
                        SELECT COUNT(DISTINCT e.user_id) as count
                        FROM web_events e
                        WHERE e.event = $1
                        AND e.ts >= $2 AND e.ts <= $3
                        AND e.user_id IN (
                            SELECT DISTINCT user_id 
                            FROM web_events 
                            WHERE event = $4
                            AND ts >= $2 AND ts <= $3
                        )
                    """
                    params = [step, start_date, end_date, prev_step]
                    
                    if org_id:
                        query += " AND e.org_id = $5"
                        params.append(org_id)
                
                # Execute query
                count = await postgres_client.fetchval(query, *params) or 0
                
                # Calculate conversion rate
                conversion_rate = 0.0
                if i == 0:
                    total_users = count
                    conversion_rate = 100.0
                elif total_users > 0:
                    conversion_rate = (count / total_users) * 100
                
                # Calculate drop-off
                drop_off = 0
                if i > 0 and funnel_data:
                    prev_count = funnel_data[-1]['count']
                    drop_off = prev_count - count
                
                funnel_data.append({
                    'step': step,
                    'step_number': i + 1,
                    'count': count,
                    'conversion_rate': round(conversion_rate, 2),
                    'drop_off': drop_off
                })
            
            # Calculate overall conversion (first to last)
            overall_conversion = 0.0
            if total_users > 0 and funnel_data:
                last_count = funnel_data[-1]['count']
                overall_conversion = (last_count / total_users) * 100
            
            return {
                'funnel_steps': funnel_data,
                'total_users': total_users,
                'overall_conversion_rate': round(overall_conversion, 2),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in funnel analysis: {e}")
            raise
    
    async def get_cohort_analysis(
        self,
        cohort_by: str = 'month',  # 'day', 'week', 'month'
        periods: int = 12,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cohort Analysis
        
        Groups users by signup date and tracks retention over time
        Returns retention percentage for each cohort over N periods
        """
        try:
            # Determine period format
            period_formats = {
                'day': 'YYYY-MM-DD',
                'week': 'IYYY-IW',  # ISO week
                'month': 'YYYY-MM'
            }
            period_format = period_formats.get(cohort_by, 'YYYY-MM')
            
            # Get cohorts
            query = f"""
                SELECT 
                    TO_CHAR(created_at, '{period_format}') as cohort,
                    COUNT(*) as cohort_size
                FROM users
                WHERE created_at >= NOW() - INTERVAL '{periods} {cohort_by}s'
            """
            
            if org_id:
                query += f" AND org_id = '{org_id}'"
            
            query += f"""
                GROUP BY TO_CHAR(created_at, '{period_format}')
                ORDER BY cohort
            """
            
            cohorts = await postgres_client.fetch(query)
            
            # For each cohort, calculate retention per period
            cohort_data = []
            for cohort_row in cohorts:
                cohort = cohort_row['cohort']
                cohort_size = cohort_row['cohort_size']
                
                # Get cohort start date
                if cohort_by == 'month':
                    cohort_start = datetime.strptime(cohort, '%Y-%m')
                elif cohort_by == 'week':
                    year, week = cohort.split('-')
                    cohort_start = datetime.strptime(f'{year}-{week}-1', '%G-%V-%u')
                else:  # day
                    cohort_start = datetime.strptime(cohort, '%Y-%m-%d')
                
                # Calculate retention for each period
                retention = []
                for period in range(periods):
                    period_start = cohort_start + timedelta(**{f'{cohort_by}s': period})
                    period_end = period_start + timedelta(**{f'{cohort_by}s': 1})
                    
                    # Count active users in this period
                    active_query = f"""
                        SELECT COUNT(DISTINCT user_id) as active
                        FROM web_events
                        WHERE user_id IN (
                            SELECT id FROM users
                            WHERE TO_CHAR(created_at, '{period_format}') = $1
                        )
                        AND ts >= $2 AND ts < $3
                    """
                    
                    active_count = await postgres_client.fetchval(
                        active_query,
                        cohort,
                        period_start,
                        period_end
                    ) or 0
                    
                    retention_rate = (active_count / cohort_size * 100) if cohort_size > 0 else 0
                    
                    retention.append({
                        'period': period,
                        'active_users': active_count,
                        'retention_rate': round(retention_rate, 2)
                    })
                
                cohort_data.append({
                    'cohort': cohort,
                    'cohort_size': cohort_size,
                    'retention': retention
                })
            
            return {
                'cohorts': cohort_data,
                'cohort_by': cohort_by,
                'periods': periods
            }
            
        except Exception as e:
            logger.error(f"Error in cohort analysis: {e}")
            raise
    
    async def get_retention_metrics(
        self,
        days: int = 30,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retention Metrics
        
        Calculates:
        - Day 1, 7, 30 retention
        - Weekly retention
        - Monthly retention
        - Churn rate
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get total active users in period
            total_users_query = """
                SELECT COUNT(DISTINCT user_id) as count
                FROM web_events
                WHERE ts >= $1 AND ts <= $2
            """
            params = [start_date, end_date]
            
            if org_id:
                total_users_query += " AND org_id = $3"
                params.append(org_id)
            
            total_users = await postgres_client.fetchval(total_users_query, *params) or 0
            
            # Calculate retention for specific days
            retention_days = [1, 7, 30]
            retention_data = {}
            
            for day in retention_days:
                if day > days:
                    continue
                
                # Users active on day N
                day_date = end_date - timedelta(days=day)
                
                # Users who were active on first day and again on day N
                retention_query = """
                    SELECT COUNT(DISTINCT e1.user_id) as count
                    FROM web_events e1
                    WHERE e1.user_id IN (
                        SELECT DISTINCT user_id
                        FROM web_events
                        WHERE ts >= $1 AND ts < $2
                    )
                    AND e1.ts >= $3 AND e1.ts < $4
                """
                params = [
                    start_date,
                    start_date + timedelta(days=1),
                    day_date,
                    day_date + timedelta(days=1)
                ]
                
                if org_id:
                    retention_query += " AND e1.org_id = $5"
                    params.append(org_id)
                
                retained_count = await postgres_client.fetchval(retention_query, *params) or 0
                retention_rate = (retained_count / total_users * 100) if total_users > 0 else 0
                
                retention_data[f'day_{day}_retention'] = {
                    'retained_users': retained_count,
                    'retention_rate': round(retention_rate, 2)
                }
            
            # Calculate churn rate (users who stopped using)
            # Users active in first half but not in second half
            mid_point = start_date + timedelta(days=days//2)
            
            churn_query = """
                SELECT COUNT(DISTINCT user_id) as count
                FROM web_events
                WHERE ts >= $1 AND ts < $2
                AND user_id NOT IN (
                    SELECT DISTINCT user_id
                    FROM web_events
                    WHERE ts >= $2 AND ts <= $3
                )
            """
            params = [start_date, mid_point, end_date]
            
            if org_id:
                churn_query += " AND org_id = $4"
                params.append(org_id)
            
            churned_users = await postgres_client.fetchval(churn_query, *params) or 0
            churn_rate = (churned_users / total_users * 100) if total_users > 0 else 0
            
            return {
                'total_active_users': total_users,
                'retention': retention_data,
                'churn': {
                    'churned_users': churned_users,
                    'churn_rate': round(churn_rate, 2)
                },
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in retention metrics: {e}")
            raise
    
    async def get_user_engagement_metrics(
        self,
        days: int = 30,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        User Engagement Metrics
        
        - DAU (Daily Active Users)
        - WAU (Weekly Active Users)
        - MAU (Monthly Active Users)
        - Stickiness (DAU/MAU)
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # DAU (average over period)
            dau_query = """
                SELECT AVG(daily_users) as dau
                FROM (
                    SELECT DATE(ts) as day, COUNT(DISTINCT user_id) as daily_users
                    FROM web_events
                    WHERE ts >= $1 AND ts <= $2
            """
            params = [start_date, end_date]
            
            if org_id:
                dau_query += " AND org_id = $3"
                params.append(org_id)
            
            dau_query += " GROUP BY DATE(ts)) daily_counts"
            
            dau = await postgres_client.fetchval(dau_query, *params) or 0
            
            # WAU (last 7 days)
            wau_start = end_date - timedelta(days=7)
            wau_query = """
                SELECT COUNT(DISTINCT user_id) as wau
                FROM web_events
                WHERE ts >= $1 AND ts <= $2
            """
            wau_params = [wau_start, end_date]
            
            if org_id:
                wau_query += " AND org_id = $3"
                wau_params.append(org_id)
            
            wau = await postgres_client.fetchval(wau_query, *wau_params) or 0
            
            # MAU (last 30 days)
            mau_start = end_date - timedelta(days=30)
            mau_query = """
                SELECT COUNT(DISTINCT user_id) as mau
                FROM web_events
                WHERE ts >= $1 AND ts <= $2
            """
            mau_params = [mau_start, end_date]
            
            if org_id:
                mau_query += " AND org_id = $3"
                mau_params.append(org_id)
            
            mau = await postgres_client.fetchval(mau_query, *mau_params) or 0
            
            # Stickiness (DAU/MAU ratio)
            stickiness = (dau / mau * 100) if mau > 0 else 0
            
            return {
                'dau': round(dau, 2),
                'wau': wau,
                'mau': mau,
                'stickiness': round(stickiness, 2),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error in engagement metrics: {e}")
            raise


# Global instance
advanced_analytics_service = AdvancedAnalyticsService()
