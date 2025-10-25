"""
ML Anomaly Detection für Blockchain Transactions
================================================

Implementiert einfache ML-Modelle zur Erkennung anomaler Transaktionen:
- Isolation Forest für unsupervised Anomaly Detection
- Feature Engineering aus Canonical Events
- Integration in die bestehende Risk-Engine
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class TransactionAnomalyDetector:
    """
    ML-basierte Anomaly Detection für Blockchain-Transaktionen
    """

    def __init__(self, model_path: str = "ml/models/anomaly_detector.pkl"):
        self.model_path = model_path
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns = [
            'value_usd', 'gas_used', 'gas_price', 'fee',
            'risk_score', 'from_address_entropy', 'to_address_entropy',
            'tx_frequency', 'amount_deviation', 'time_gap'
        ]
        self._load_model()

    def _load_model(self):
        """Lade trainiertes Modell oder initialisiere neu"""
        try:
            if os.path.exists(self.model_path):
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.scaler = data['scaler']
                logger.info(f"Loaded anomaly detection model from {self.model_path}")
            else:
                logger.info("No trained model found, initializing new model")
                self._initialize_model()
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._initialize_model()

    def _initialize_model(self):
        """Initialisiere neues Isolation Forest Modell"""
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,  # 10% Anomalien erwartet
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()

    def _extract_features(self, event: Dict[str, Any]) -> np.ndarray:
        """Extrahiere Features aus einem Event für ML-Modell"""
        features = []

        # Grundlegende Transaction-Features
        features.append(float(event.get('value_usd', 0)))
        features.append(float(event.get('gas_used', 0)))
        features.append(float(event.get('gas_price', 0)))
        features.append(float(event.get('fee', 0)))
        features.append(float(event.get('risk_score', 0)))

        # Address-Entropie (einfache Heuristik)
        from_addr = event.get('from_address', '')
        to_addr = event.get('to_address', '')
        features.append(len(set(from_addr)) / max(len(from_addr), 1))  # Simple entropy proxy
        features.append(len(set(to_addr)) / max(len(to_addr), 1))

        # Transaction-Frequenz (aus Metadata)
        features.append(float(event.get('metadata', {}).get('tx_frequency', 1)))

        # Amount Deviation (verglichen mit Durchschnitt)
        features.append(float(event.get('metadata', {}).get('amount_deviation', 0)))

        # Zeit-Gap (seit letzter Transaction)
        features.append(float(event.get('metadata', {}).get('time_gap', 3600)))  # Default 1h

        return np.array(features).reshape(1, -1)

    def _train_model(self, events: List[Dict[str, Any]]) -> bool:
        """Trainiere Modell mit historischen Events"""
        try:
            if len(events) < 50:
                logger.warning("Not enough data for training (need at least 50 events)")
                return False

            # Extrahiere Features
            X = []
            for event in events:
                features = self._extract_features(event)
                X.append(features[0])

            X = np.array(X)

            # Skaliere Features
            X_scaled = self.scaler.fit_transform(X)

            # Trainiere Modell
            self.model.fit(X_scaled)

            # Speichere Modell
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'trained_at': datetime.utcnow(),
                'training_size': len(events)
            }, self.model_path)

            logger.info(f"Trained anomaly detection model with {len(events)} events")
            return True

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False

    def predict_anomaly(self, event: Dict[str, Any]) -> float:
        """
        Berechne Anomaly-Score für ein Event (0-1, höher = anomaler)

        Returns:
            Anomaly score between 0 and 1 (1 = hoch anomal)
        """
        try:
            if self.model is None or self.scaler is None:
                return 0.0

            features = self._extract_features(event)
            features_scaled = self.scaler.transform(features)

            # Isolation Forest gibt -1 für Anomalien, 1 für normal
            prediction = self.model.predict(features_scaled)[0]

            # Konvertiere zu Score (0-1)
            if prediction == -1:
                # Für Anomalien: berechne Distanz zum nächsten Cluster
                scores = self.model.decision_function(features_scaled)[0]
                anomaly_score = max(0, min(1, (scores * -1) + 0.5))  # Normalize
            else:
                anomaly_score = 0.0

            return anomaly_score

        except Exception as e:
            logger.error(f"Error predicting anomaly: {e}")
            return 0.0

    def update_risk_score(self, event: Dict[str, Any], current_risk: float) -> float:
        """
        Aktualisiere Risk-Score basierend auf ML-Anomaly-Erkennung

        Args:
            event: Transaction event
            current_risk: Aktueller Risk-Score

        Returns:
            Aktualisierter Risk-Score
        """
        anomaly_score = self.predict_anomaly(event)

        # Kombiniere aktuellen Risk mit Anomaly-Score (gewichtete Summe)
        combined_risk = (current_risk * 0.7) + (anomaly_score * 0.3)

        # Füge Anomaly-Score zu Metadata hinzu
        if 'metadata' not in event:
            event['metadata'] = {}
        event['metadata']['ml_anomaly_score'] = anomaly_score

        return min(combined_risk, 1.0)

    async def train_from_historical_data(self, events: List[Dict[str, Any]]) -> bool:
        """Trainiere Modell mit historischen Daten (Async für DB-Integration)"""
        return self._train_model(events)

    def get_model_info(self) -> Dict[str, Any]:
        """Gib Informationen über das trainierte Modell zurück"""
        if not os.path.exists(self.model_path):
            return {"status": "not_trained"}

        try:
            data = joblib.load(self.model_path)
            return {
                "status": "trained",
                "trained_at": data.get('trained_at'),
                "training_size": data.get('training_size'),
                "contamination": self.model.contamination if self.model else None
            }
        except Exception:
            return {"status": "error"}


# Global Detector-Instanz
anomaly_detector = TransactionAnomalyDetector()


def extract_features_from_events(events: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Extrahiere Features aus einer Liste von Events für Batch-Verarbeitung

    Returns:
        DataFrame mit Features für ML-Training
    """
    features_list = []

    for event in events:
        features = anomaly_detector._extract_features(event)
        features_list.append(features[0])

    df = pd.DataFrame(features_list, columns=anomaly_detector.feature_columns)
    return df
