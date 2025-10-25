"""
ML Model Service für Blockchain Forensics
Unterstützt Anomalie-Erkennung und ML-basierte Alert-Regeln
"""

import logging
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix


logger = logging.getLogger(__name__)


class MLModelService:
    """Service für ML-Modelle in Blockchain Forensics"""

    def __init__(self):
        self.models_dir = Path("/tmp/ml_models")
        self.models_dir.mkdir(exist_ok=True)

        # In-Memory Model Cache
        self.models: Dict[str, Dict[str, Any]] = {}

        # Feature Engineering Configuration
        self.feature_config = {
            "transaction_features": [
                "value", "gas_used", "gas_price", "timestamp",
                "block_number", "tx_index", "value_usd"
            ],
            "address_features": [
                "balance", "tx_count", "first_seen", "last_seen",
                "avg_tx_value", "max_tx_value", "min_tx_value"
            ],
            "temporal_features": [
                "hour_of_day", "day_of_week", "is_weekend",
                "time_since_last_tx", "tx_frequency_1h", "tx_frequency_24h"
            ]
        }

        # Model Performance Tracking
        self.model_performance: Dict[str, Dict[str, Any]] = {}

    def extract_features(self, transaction_data: Dict[str, Any]) -> np.ndarray:
        """Extrahiere Features aus Transaktionsdaten für ML-Modelle"""
        features = []

        # Transaction Features
        for feature in self.feature_config["transaction_features"]:
            if feature in transaction_data:
                value = transaction_data[feature]
                if isinstance(value, (int, float)):
                    features.append(float(value))
                elif isinstance(value, str):
                    # Timestamp parsing
                    try:
                        if feature == "timestamp":
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            features.append(dt.timestamp())
                        else:
                            features.append(0.0)
                    except:
                        features.append(0.0)
                else:
                    features.append(0.0)
            else:
                features.append(0.0)

        # Address Features (wenn verfügbar)
        address_data = transaction_data.get("address_features", {})
        for feature in self.feature_config["address_features"]:
            if feature in address_data:
                val = address_data[feature]
                try:
                    if isinstance(val, (int, float)):
                        features.append(float(val))
                    elif isinstance(val, str):
                        # Parse timestamps for first_seen / last_seen
                        if feature in ("first_seen", "last_seen"):
                            dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
                            features.append(dt.timestamp())
                        else:
                            features.append(float(val))
                    else:
                        features.append(0.0)
                except Exception:
                    features.append(0.0)
            else:
                features.append(0.0)

        # Temporal Features
        temporal_data = transaction_data.get("temporal_features", {})
        for feature in self.feature_config["temporal_features"]:
            if feature in temporal_data:
                features.append(float(temporal_data[feature]))
            else:
                features.append(0.0)

        return np.array(features).reshape(1, -1)

    def train_anomaly_detection_model(
        self,
        training_data: List[Dict[str, Any]],
        model_id: str = "isolation_forest_v1",
        contamination: float = 0.1
    ) -> Dict[str, Any]:
        """Trainiere ein Anomalie-Erkennungsmodell"""
        try:
            logger.info(f"Training anomaly detection model {model_id} with {len(training_data)} samples")

            # Extract features from training data
            X = []
            for sample in training_data:
                features = self.extract_features(sample)
                X.append(features.flatten())

            n_samples = len(X)
            if n_samples == 0:
                raise ValueError("No training data provided")

            X = np.array(X)

            # Scale features (works for single sample; std will be zero -> zeros after transform)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model = None
            if n_samples >= 10:
                # Train Isolation Forest
                model = IsolationForest(
                    n_estimators=100,
                    contamination=contamination,
                    random_state=42,
                    max_samples=max(0.8, min(1.0, (n_samples - 1) / max(1, n_samples)))
                )
                model.fit(X_scaled)
                baseline = None
            else:
                # Fallback Baseline: mean vector in feature space
                baseline = X_scaled.mean(axis=0)

            # Save model
            model_data = {
                "model": model,
                "scaler": scaler,
                "feature_config": self.feature_config,
                "contamination": contamination,
                "training_samples": len(training_data),
                "training_timestamp": datetime.utcnow(),
                "model_version": "1.0",
                "baseline": baseline,
            }

            model_path = self.models_dir / f"{model_id}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)

            # Update cache
            self.models[model_id] = model_data

            # Calculate performance metrics on training data
            if model is not None:
                anomaly_scores = model.decision_function(X_scaled)
                predictions = model.predict(X_scaled)
                performance = {
                    "training_samples": len(training_data),
                    "anomalies_detected": int(np.sum(predictions == -1)),
                    "contamination_actual": float(np.mean(predictions == -1)),
                    "avg_anomaly_score": float(np.mean(anomaly_scores)),
                    "min_anomaly_score": float(np.min(anomaly_scores)),
                    "max_anomaly_score": float(np.max(anomaly_scores))
                }
            else:
                performance = {
                    "training_samples": len(training_data),
                    "anomalies_detected": 0,
                    "contamination_actual": 0.0,
                    "avg_anomaly_score": 0.0,
                    "min_anomaly_score": 0.0,
                    "max_anomaly_score": 0.0
                }

            self.model_performance[model_id] = performance

            logger.info(f"Model {model_id} trained successfully. Detected {performance['anomalies_detected']} anomalies")

            return {
                "model_id": model_id,
                "status": "trained",
                "performance": performance,
                "training_timestamp": model_data["training_timestamp"].isoformat()
            }

        except Exception as e:
            logger.error(f"Error training model {model_id}: {e}")
            raise

    def predict_anomaly(self, transaction_data: Dict[str, Any], model_id: str = "isolation_forest_v1") -> Dict[str, Any]:
        """Führe Anomalie-Vorhersage durch"""
        try:
            # Load model if not in cache
            if model_id not in self.models:
                model_path = self.models_dir / f"{model_id}.pkl"
                if model_path.exists():
                    with open(model_path, 'rb') as f:
                        self.models[model_id] = pickle.load(f)
                else:
                    raise ValueError(f"Model {model_id} not found")

            model_data = self.models[model_id]

            # Extract features
            features = self.extract_features(transaction_data)

            # Scale features
            scaler = model_data["scaler"]
            features_scaled = scaler.transform(features)

            # Predict anomaly
            model = model_data["model"]
            baseline = model_data.get("baseline")
            if model is not None:
                anomaly_score = model.decision_function(features_scaled)[0]
                prediction = model.predict(features_scaled)[0]
                # Convert to our scoring system (0.0 to 1.0, where 1.0 is most anomalous)
                normalized_score = max(0.0, min(1.0, (0.5 - anomaly_score) * 2))
                is_anomaly = prediction == -1
            else:
                # Baseline distance heuristic
                if baseline is None:
                    baseline = np.zeros(features_scaled.shape[1])
                dist = float(np.linalg.norm(features_scaled[0] - baseline))
                # Heuristic normalization: map distance to [0,1] via tanh
                normalized_score = float(np.tanh(dist))
                is_anomaly = normalized_score > 0.8
            confidence = normalized_score if is_anomaly else 1.0 - normalized_score

            result = {
                "model_id": model_id,
                "is_anomaly": is_anomaly,
                "anomaly_score": normalized_score,
                "confidence": confidence,
                "prediction_timestamp": datetime.utcnow().isoformat(),
                "feature_count": features.shape[1],
                "model_version": model_data.get("model_version", "unknown")
            }

            # Log prediction for monitoring
            logger.info(f"Anomaly prediction for model {model_id}: score={normalized_score:.3f}, anomaly={is_anomaly}")

            return result

        except Exception as e:
            logger.error(f"Error predicting anomaly with model {model_id}: {e}")
            return {
                "model_id": model_id,
                "error": str(e),
                "prediction_timestamp": datetime.utcnow().isoformat()
            }

    def get_model_performance(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Hole Performance-Metriken für ein Modell"""
        return self.model_performance.get(model_id)

    def list_models(self) -> List[Dict[str, Any]]:
        """Liste alle verfügbaren Modelle auf"""
        models = []

        for model_id in self.models.keys():
            model_info = {
                "model_id": model_id,
                "training_timestamp": self.models[model_id].get("training_timestamp"),
                "training_samples": self.models[model_id].get("training_samples"),
                "model_version": self.models[model_id].get("model_version"),
                "performance": self.model_performance.get(model_id)
            }
            models.append(model_info)

        # Also check for models on disk that aren't in memory
        for model_file in self.models_dir.glob("*.pkl"):
            model_id = model_file.stem
            if model_id not in self.models:
                models.append({
                    "model_id": model_id,
                    "status": "on_disk",
                    "model_version": "unknown"
                })

        return models

    def delete_model(self, model_id: str) -> bool:
        """Lösche ein Modell"""
        try:
            # Remove from memory
            if model_id in self.models:
                del self.models[model_id]

            # Remove from disk
            model_path = self.models_dir / f"{model_id}.pkl"
            if model_path.exists():
                model_path.unlink()

            # Remove performance data
            if model_id in self.model_performance:
                del self.model_performance[model_id]

            logger.info(f"Model {model_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting model {model_id}: {e}")
            return False

    def generate_training_data_from_events(self, events: List[Dict[str, Any]], lookback_days: int = 30) -> List[Dict[str, Any]]:
        """Generiere Trainingsdaten aus historischen Events"""
        training_data = []

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        for event in events:
            if isinstance(event.get("timestamp"), str):
                try:
                    event_time = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
                    if event_time < cutoff_date:
                        continue
                except:
                    continue

            # Extract features for this event
            features = self.extract_features(event)

            # Add anomaly indicators if available
            anomaly_indicators = event.get("anomaly_indicators", [])

            training_sample = {
                "features": features.flatten().tolist(),
                "timestamp": event.get("timestamp"),
                "address": event.get("address"),
                "tx_hash": event.get("tx_hash"),
                "anomaly_indicators": anomaly_indicators,
                "is_labeled_anomaly": len(anomaly_indicators) > 0
            }

            training_data.append(training_sample)

            logger.info(f"Generated {len(training_data)} training samples from {len(events)} events")
        return training_data

    def validate_model_performance(self, model_id: str, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validiere Modell-Performance mit Validierungsdaten"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")

            model_data = self.models[model_id]
            model = model_data["model"]
            scaler = model_data["scaler"]

            # Extract features from validation data
            X = []
            y_true = []

            for sample in validation_data:
                features = self.extract_features(sample)
                X.append(features.flatten())
                y_true.append(1 if sample.get("is_anomaly", False) else 0)

            if len(X) == 0:
                return {"error": "No validation data provided"}

            X = np.array(X)
            y_true = np.array(y_true)

            # Scale and predict
            X_scaled = scaler.transform(X)
            y_pred = model.predict(X_scaled)
            anomaly_scores = model.decision_function(X_scaled)

            # Convert predictions (-1 for anomaly, 1 for normal)
            y_pred_binary = (y_pred == -1).astype(int)

            # Calculate metrics
            report = classification_report(y_true, y_pred_binary, output_dict=True, zero_division=0)
            conf_matrix = confusion_matrix(y_true, y_pred_binary).tolist()

            validation_results = {
                "model_id": model_id,
                "validation_samples": len(validation_data),
                "true_anomalies": np.sum(y_true),
                "predicted_anomalies": np.sum(y_pred_binary),
                "accuracy": report.get("accuracy", 0),
                "precision": report.get("1", {}).get("precision", 0),
                "recall": report.get("1", {}).get("recall", 0),
                "f1_score": report.get("1", {}).get("f1-score", 0),
                "confusion_matrix": conf_matrix,
                "avg_anomaly_score": float(np.mean(anomaly_scores)),
                "validation_timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Model validation completed for {model_id}: F1={validation_results['f1_score']:.3f}")

            return validation_results

        except Exception as e:
            logger.error(f"Error validating model {model_id}: {e}")
            return {"error": str(e)}


# Singleton instance
ml_model_service = MLModelService()
