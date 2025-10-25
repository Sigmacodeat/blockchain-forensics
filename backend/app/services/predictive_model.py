"""
Predictive Risk Modeling (Zeitreihen-basierte Prognosen)
==========================================================

Endpunkt für zeitreihenbasierte Risiko-Prognosen:
- Nutzer-Aktivität Trends
- Alert-Entwicklung
- Risiko-Scores über Zeit

Verwendet einfache Zeitreihen-Modelle (MA, naive Forecast).
Erweiterbar mit LSTM/PyTorch für komplexere Modelle.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PredictiveModel:
    """Einfache Zeitreihen-Prognosen"""

    def __init__(self) -> None:
        self.redis_client = None
        self.postgres_client = None

    async def _get_clients(self):
        """Lazy Client-Loading"""
        if self.redis_client is None:
            try:
                from app.db.redis_client import redis_client
                self.redis_client = redis_client
            except Exception:
                pass
        if self.postgres_client is None:
            try:
                from app.db.postgres_client import postgres_client as pc
                self.postgres_client = pc
            except Exception:
                pass

    async def predict_user_activity(
        self,
        user_id: str,
        days_ahead: int = 7,
        metric: str = "tokens_used"  # tokens_used, alerts_triggered, traces_run
    ) -> Dict[str, Any]:
        """Prognostiziert Nutzer-Aktivität basierend auf historischen Daten"""
        await self._get_clients()
        if not self.redis_client or not self.postgres_client:
            return {"error": "Databases unavailable", "predictions": []}

        # Sammle historische Daten (letzte 30 Tage)
        predictions: List[Dict[str, Any]] = []
        try:
            async with self.postgres_client.acquire() as conn:
                # Query je nach Metric
                if metric == "tokens_used":
                    # Monatliche Tokens aus usage_logs
                    rows = await conn.fetch(
                        """
                        SELECT DATE_TRUNC('day', created_at) as day,
                               SUM(tokens) as value
                        FROM usage_logs
                        WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
                        GROUP BY day
                        ORDER BY day DESC
                        """,
                        user_id
                    )
                elif metric == "alerts_triggered":
                    # Alerts aus alerts_v2
                    rows = await conn.fetch(
                        """
                        SELECT DATE_TRUNC('day', created_at) as day,
                               COUNT(*) as value
                        FROM alerts_v2
                        WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
                        GROUP BY day
                        ORDER BY day DESC
                        """,
                        user_id
                    )
                else:
                    # Default: traces
                    rows = await conn.fetch(
                        """
                        SELECT DATE_TRUNC('day', created_at) as day,
                               COUNT(*) as value
                        FROM trace_requests
                        WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
                        GROUP BY day
                        ORDER BY day DESC
                        """,
                        user_id
                    )

            # Berechne Simple Moving Average (SMA)
            values = [float(r["value"]) for r in rows[::-1]]  # Reverse to chronological
            if len(values) < 7:
                return {"error": "Insufficient historical data (need >=7 days)", "predictions": []}

            # SMA über letzte 7 Tage
            sma = sum(values[-7:]) / 7
            trend = "stable"
            if len(values) >= 14:
                prev_sma = sum(values[-14:-7]) / 7
                if sma > prev_sma * 1.1:
                    trend = "increasing"
                elif sma < prev_sma * 0.9:
                    trend = "decreasing"

            # Naive Forecast: Extrapoliere SMA für nächste Tage
            for i in range(1, min(days_ahead, 30) + 1):
                forecast_date = datetime.utcnow() + timedelta(days=i)
                forecast_value = sma  # Naive: gleicher Wert wie aktueller SMA
                predictions.append({
                    "date": forecast_date.date().isoformat(),
                    "predicted_value": round(forecast_value, 2),
                    "confidence": 0.6,  # Feste Confidence für naive Methode
                    "method": "simple_moving_average"
                })

            return {
                "user_id": user_id,
                "metric": metric,
                "historical_days": len(values),
                "current_sma": round(sma, 2),
                "trend": trend,
                "predictions": predictions,
                "model": "naive_sma"
            }

        except Exception as e:
            logger.error(f"Predictive modeling failed for {user_id}: {e}")
            return {"error": str(e), "predictions": []}

    async def predict_system_risk_trends(
        self,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """System-weite Risiko-Trends prognostizieren"""
        await self._get_clients()
        if not self.postgres_client:
            return {"error": "Database unavailable", "predictions": []}

        try:
            async with self.postgres_client.acquire() as conn:
                # Durchschnittliche Risk-Scores über Zeit
                rows = await conn.fetch(
                    """
                    SELECT DATE_TRUNC('day', created_at) as day,
                           AVG(risk_score) as avg_risk
                    FROM trace_results
                    WHERE risk_score IS NOT NULL
                      AND created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY day
                    ORDER BY day DESC
                    """,
                )

            values = [float(r["avg_risk"]) for r in rows[::-1]]
            if len(values) < 7:
                return {"error": "Insufficient risk data", "predictions": []}

            # Trend-Analyse
            sma = sum(values[-7:]) / 7
            predictions = []
            for i in range(1, min(days_ahead, 14) + 1):
                forecast_date = datetime.utcnow() + timedelta(days=i)
                predictions.append({
                    "date": forecast_date.date().isoformat(),
                    "predicted_avg_risk": round(sma, 3),
                    "confidence": 0.5,
                    "method": "historical_average"
                })

            return {
                "scope": "system",
                "metric": "average_risk_score",
                "historical_days": len(values),
                "current_avg_risk": round(sma, 3),
                "predictions": predictions
            }

        except Exception as e:
            logger.error(f"System risk prediction failed: {e}")
            return {"error": str(e), "predictions": []}


predictive_model = PredictiveModel()
