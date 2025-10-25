"""
Advanced Analytics & ML Engine für Blockchain Forensics
======================================================

Predictive Analytics und Machine Learning für:
- Anomalie-Erkennung
- Risiko-Vorhersage
- Muster-Erkennung
- Fraud Detection
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class MLModel:
    """ML-Modell für Forensik-Analysen"""
    model_id: str
    model_type: str  # "anomaly_detection", "risk_scoring", "pattern_recognition"
    version: str
    accuracy: float
    features: List[str]
    created_at: datetime
    last_trained: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_type": self.model_type,
            "version": self.version,
            "accuracy": self.accuracy,
            "features": self.features,
            "created_at": self.created_at.isoformat(),
            "last_trained": self.last_trained.isoformat()
        }


class AnomalyDetector:
    """ML-basierte Anomalie-Erkennung"""

    def __init__(self):
        self.models = {}
        self.feature_columns = [
            "tx_value", "gas_used", "gas_price", "tx_count_24h",
            "unique_addresses_24h", "volume_24h", "avg_tx_value_24h"
        ]

    def train_model(self, historical_data: pd.DataFrame) -> MLModel:
        """Trainiert Anomalie-Erkennungsmodell"""
        # Vereinfachte Implementierung - in Produktion: Isolation Forest, One-Class SVM
        model_id = f"anomaly_detector_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Feature Engineering
        features = historical_data[self.feature_columns].fillna(0)

        # Einfache Anomalie-Erkennung basierend auf statistischen Abweichungen
        means = features.mean()
        stds = features.std()

        # Berechne Anomalie-Scores (Z-Score-basierend)
        anomaly_scores = np.abs((features - means) / stds).max(axis=1)

        # Modell speichern
        model = MLModel(
            model_id=model_id,
            model_type="anomaly_detection",
            version="1.0",
            accuracy=0.85,  # Platzhalter - echte Accuracy aus Validierung
            features=self.feature_columns,
            created_at=datetime.utcnow(),
            last_trained=datetime.utcnow()
        )

        self.models[model_id] = {
            "model": model,
            "means": means.to_dict(),
            "stds": stds.to_dict(),
            "threshold": np.percentile(anomaly_scores, 95)  # 95. Perzentil als Threshold
        }

        logger.info(f"Trained anomaly detection model: {model_id}")
        return model

    def detect_anomalies(self, current_data: pd.DataFrame, model_id: str = None) -> List[Dict[str, Any]]:
        """Erkennt Anomalien in aktuellen Daten"""
        if not self.models:
            return []

        if model_id and model_id in self.models:
            model_data = self.models[model_id]
        else:
            # Verwende neuestes Modell
            model_id = max(self.models.keys(), key=lambda x: self.models[x]["model"].last_trained)
            model_data = self.models[model_id]

        model = model_data["model"]
        means = model_data["means"]
        stds = model_data["stds"]
        threshold = model_data["threshold"]

        features = current_data[self.feature_columns].fillna(0)

        # Berechne Anomalie-Scores
        anomaly_scores = np.abs((features - pd.Series(means)) / pd.Series(stds)).max(axis=1)

        anomalies = []
        for idx, (score, (_, row)) in enumerate(zip(anomaly_scores, current_data.iterrows())):
            if score > threshold:
                anomalies.append({
                    "index": idx,
                    "anomaly_score": float(score),
                    "address": row.get("address"),
                    "tx_hash": row.get("tx_hash"),
                    "timestamp": row.get("timestamp"),
                    "anomaly_factors": self._identify_anomaly_factors(row, means, stds),
                    "ml_model": model_id,
                    "confidence": min(score / threshold, 1.0)
                })

        logger.info(f"Detected {len(anomalies)} anomalies using model {model_id}")
        return anomalies

    def _identify_anomaly_factors(self, row: pd.Series, means: Dict, stds: Dict) -> List[str]:
        """Identifiziert spezifische Anomalie-Faktoren"""
        factors = []
        for col in self.feature_columns:
            if col in row.index:
                value = row[col]
                mean_val = means.get(col, 0)
                std_val = stds.get(col, 1)

                if abs(value - mean_val) > 2 * std_val:  # 2-Sigma-Regel
                    factors.append(f"{col}: {value:.2f} (vs. expected {mean_val:.2f})")

        return factors


class RiskPredictor:
    """ML-basierte Risiko-Vorhersage"""

    def __init__(self):
        self.models = {}
        self.risk_factors = [
            "tx_frequency", "avg_tx_value", "unique_counterparties",
            "cross_chain_activity", "mixer_usage", "sanction_hits",
            "large_transfers", "anomaly_score"
        ]

    def train_risk_model(self, labeled_data: pd.DataFrame) -> MLModel:
        """Trainiert Risiko-Vorhersagemodell"""
        model_id = f"risk_predictor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Feature Engineering
        features = labeled_data[self.risk_factors].fillna(0)
        labels = labeled_data["risk_label"]  # 0: low, 1: high risk

        # Vereinfachtes Modell - in Produktion: Random Forest, XGBoost
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)

        # Accuracy berechnen
        y_pred = rf_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        model = MLModel(
            model_id=model_id,
            model_type="risk_scoring",
            version="1.0",
            accuracy=accuracy,
            features=self.risk_factors,
            created_at=datetime.utcnow(),
            last_trained=datetime.utcnow()
        )

        self.models[model_id] = {
            "model": model,
            "rf_model": rf_model,
            "feature_importance": dict(zip(self.risk_factors, rf_model.feature_importances_))
        }

        logger.info(f"Trained risk prediction model: {model_id} (accuracy: {accuracy:.3f})")
        return model

    def predict_risk(self, address_data: Dict[str, Any], model_id: str = None) -> Dict[str, Any]:
        """Vorhersagt Risiko für eine Adresse"""
        if not self.models:
            return {"risk_score": 0.0, "confidence": 0.0, "factors": []}

        if model_id and model_id in self.models:
            model_data = self.models[model_id]
        else:
            model_id = max(self.models.keys(), key=lambda x: self.models[x]["model"].last_trained)
            model_data = self.models[model_id]

        rf_model = model_data["rf_model"]
        feature_importance = model_data["feature_importance"]

        # Feature-Vektor erstellen
        features = np.array([[address_data.get(factor, 0) for factor in self.risk_factors]])

        # Vorhersage
        risk_prob = rf_model.predict_proba(features)[0][1]  # Wahrscheinlichkeit für High Risk
        prediction = rf_model.predict(features)[0]

        # Wichtigste Faktoren identifizieren
        top_factors = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "risk_score": float(risk_prob),
            "risk_level": "high" if prediction == 1 else "low",
            "confidence": float(max(risk_prob, 1 - risk_prob)),
            "top_factors": [factor for factor, _ in top_factors],
            "ml_model": model_id,
            "timestamp": datetime.utcnow().isoformat()
        }


class PatternRecognizer:
    """Erkennung von komplexen Mustern"""

    def __init__(self):
        self.patterns = {}
        self.transaction_sequences = []

    def train_pattern_model(self, sequence_data: List[List[Dict]]) -> MLModel:
        """Trainiert Muster-Erkennungsmodell"""
        model_id = f"pattern_recognizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Vereinfachte Pattern-Erkennung - in Produktion: LSTM, Transformer
        # Hier: Einfache Sequenz-Analyse

        patterns_found = {}
        for sequence in sequence_data:
            if len(sequence) >= 3:  # Mindestens 3 Transaktionen für Pattern
                pattern = self._extract_sequence_pattern(sequence)
                if pattern:
                    patterns_found[pattern] = patterns_found.get(pattern, 0) + 1

        # Häufigste Patterns als "bekannte" Muster speichern
        common_patterns = {k: v for k, v in patterns_found.items() if v >= 5}

        model = MLModel(
            model_id=model_id,
            model_type="pattern_recognition",
            version="1.0",
            accuracy=0.78,  # Platzhalter
            features=["sequence_length", "tx_types", "value_patterns"],
            created_at=datetime.utcnow(),
            last_trained=datetime.utcnow()
        )

        self.patterns[model_id] = {
            "model": model,
            "common_patterns": common_patterns,
            "threshold": 0.7
        }

        logger.info(f"Trained pattern recognition model: {model_id}")
        return model

    def recognize_patterns(self, new_sequence: List[Dict], model_id: str = None) -> List[Dict[str, Any]]:
        """Erkennt Muster in neuen Sequenzen"""
        if not self.patterns:
            return []

        if model_id and model_id in self.patterns:
            model_data = self.patterns[model_id]
        else:
            model_id = max(self.patterns.keys(), key=lambda x: self.patterns[x]["model"].last_trained)
            model_data = self.patterns[model_id]

        common_patterns = model_data["common_patterns"]
        threshold = model_data["threshold"]

        detected_patterns = []

        if len(new_sequence) >= 3:
            pattern = self._extract_sequence_pattern(new_sequence)
            if pattern in common_patterns:
                similarity = common_patterns[pattern] / max(common_patterns.values())

                if similarity >= threshold:
                    detected_patterns.append({
                        "pattern_type": pattern,
                        "confidence": similarity,
                        "sequence_length": len(new_sequence),
                        "pattern_frequency": common_patterns[pattern],
                        "ml_model": model_id
                    })

        return detected_patterns

    def _extract_sequence_pattern(self, sequence: List[Dict]) -> str:
        """Extrahiert Pattern aus Transaktionssequenz"""
        if len(sequence) < 2:
            return ""

        # Einfache Pattern-Extraktion basierend auf Transaktions-Typen und Werten
        tx_types = [tx.get("type", "unknown") for tx in sequence]
        values = [tx.get("value", 0) for tx in sequence]

        # Pattern-Kategorisierung
        if all(t == "transfer" for t in tx_types):
            if all(v > 1000000 for v in values):  # Alle großen Transfers
                return "large_transfers"
            elif len(set(values)) == 1:  # Gleiche Werte
                return "equal_value_transfers"
        elif "bridge" in tx_types:
            return "cross_chain_activity"
        elif any(v > 10000000 for v in values):  # Sehr große Transfers
            return "whale_activity"

        return "mixed_activity"


class ForensicAnalyticsEngine:
    """Haupt-Engine für Advanced Analytics"""

    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.risk_predictor = RiskPredictor()
        self.pattern_recognizer = PatternRecognizer()

        # Modell-Registry
        self.models: Dict[str, MLModel] = {}

    def train_all_models(self, training_data: Dict[str, pd.DataFrame]) -> Dict[str, MLModel]:
        """Trainiert alle ML-Modelle"""
        trained_models = {}

        # Anomalie-Modell trainieren
        if "anomalies" in training_data:
            anomaly_model = self.anomaly_detector.train_model(training_data["anomalies"])
            trained_models["anomaly"] = anomaly_model
            self.models[anomaly_model.model_id] = anomaly_model

        # Risiko-Modell trainieren
        if "risk_labels" in training_data:
            risk_model = self.risk_predictor.train_risk_model(training_data["risk_labels"])
            trained_models["risk"] = risk_model
            self.models[risk_model.model_id] = risk_model

        # Pattern-Modell trainieren
        if "sequences" in training_data:
            pattern_model = self.pattern_recognizer.train_pattern_model(training_data["sequences"])
            trained_models["pattern"] = pattern_model
            self.models[pattern_model.model_id] = pattern_model

        logger.info(f"Trained {len(trained_models)} ML models")
        return trained_models

    def analyze_entity(self, address: str, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Vollständige Analyse einer Entität"""
        analysis = {
            "address": address,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_assessment": {},
            "anomalies": [],
            "patterns": [],
            "recommendations": []
        }

        # Risiko-Vorhersage
        if self.models:
            risk_prediction = self.risk_predictor.predict_risk(historical_data)
            analysis["risk_assessment"] = risk_prediction

            # Empfehlungen basierend auf Risiko
            if risk_prediction["risk_score"] > 0.8:
                analysis["recommendations"].append("Enhanced monitoring required")
            if risk_prediction["risk_score"] > 0.9:
                analysis["recommendations"].append("Immediate investigation recommended")

        # Anomalie-Erkennung
        df_data = pd.DataFrame([historical_data])
        anomalies = self.anomaly_detector.detect_anomalies(df_data)
        analysis["anomalies"] = anomalies

        # Pattern-Erkennung
        tx_sequence = historical_data.get("transaction_sequence", [])
        patterns = self.pattern_recognizer.recognize_patterns(tx_sequence)
        analysis["patterns"] = patterns

        return analysis

    def get_model_performance(self) -> Dict[str, Any]:
        """Gibt Performance-Metriken aller Modelle zurück"""
        return {
            "total_models": len(self.models),
            "models_by_type": {},
            "average_accuracy": 0.0
        }


# Singleton Instance
analytics_engine = ForensicAnalyticsEngine()
