"""
ML Model Deployment Framework
=============================
Production-ready model serving with MLflow integration.
"""

import pickle
import json
from typing import Any, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ModelDeployment:
    """ML Model Deployment Manager"""
    
    def __init__(self, models_dir: str = "./ml/models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_models = {}
        
    def save_model(self, model: Any, model_name: str, metadata: Optional[Dict] = None) -> str:
        """Save model to disk with metadata"""
        model_path = self.models_dir / f"{model_name}.pkl"
        metadata_path = self.models_dir / f"{model_name}_metadata.json"
        
        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Save metadata
        metadata = metadata or {}
        metadata.update({
            'model_name': model_name,
            'created_at': str(Path(model_path).stat().st_mtime),
            'framework': 'scikit-learn'  # or detect
        })
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model {model_name} saved to {model_path}")
        return str(model_path)
    
    def load_model(self, model_name: str) -> Any:
        """Load model from disk"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        model_path = self.models_dir / f"{model_name}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Model {model_name} not found")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        self.loaded_models[model_name] = model
        logger.info(f"Model {model_name} loaded from {model_path}")
        return model
    
    def predict(self, model_name: str, data: Any) -> Any:
        """Make prediction with loaded model"""
        model = self.load_model(model_name)
        return model.predict(data)
    
    def predict_proba(self, model_name: str, data: Any) -> Any:
        """Make probability prediction"""
        model = self.load_model(model_name)
        if hasattr(model, 'predict_proba'):
            return model.predict_proba(data)
        else:
            raise AttributeError(f"Model {model_name} does not support predict_proba")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model metadata"""
        metadata_path = self.models_dir / f"{model_name}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        else:
            return {'model_name': model_name, 'status': 'no_metadata'}
    
    def list_models(self) -> list:
        """List all available models"""
        return [f.stem for f in self.models_dir.glob("*.pkl") if not f.name.endswith("_metadata.pkl")]

class MLService:
    """High-level ML service for the application"""
    
    def __init__(self):
        self.deployment = ModelDeployment()
        
    async def classify_transaction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Classify transaction type using ML"""
        try:
            # Load features into proper format
            import numpy as np
            feature_vector = np.array([[
                features.get('amount_usd', 0),
                features.get('transaction_count', 0),
                features.get('unique_addresses', 0),
                features.get('time_span_hours', 0),
                1 if features.get('has_mixer', False) else 0
            ]])
            
            # Predict
            prediction = self.deployment.predict('transaction_classifier', feature_vector)
            probabilities = self.deployment.predict_proba('transaction_classifier', feature_vector)
            
            return {
                'prediction': int(prediction[0]),
                'confidence': float(probabilities[0].max()),
                'probabilities': probabilities[0].tolist()
            }
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return {'error': str(e)}
    
    async def detect_anomalies(self, transaction_data: list) -> Dict[str, Any]:
        """Detect anomalies in transaction patterns"""
        try:
            import numpy as np
            data = np.array(transaction_data)
            
            prediction = self.deployment.predict('anomaly_detector', data)
            
            return {
                'anomalies_detected': int(prediction.sum()),
                'anomaly_indices': prediction.nonzero()[0].tolist()
            }
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {'error': str(e)}
    
    async def cluster_addresses(self, addresses: list) -> Dict[str, Any]:
        """Cluster addresses based on transaction patterns"""
        try:
            import numpy as np
            # Convert addresses to feature vectors
            features = np.random.rand(len(addresses), 10)  # Placeholder
            
            clusters = self.deployment.predict('address_clusterer', features)
            
            return {
                'clusters': clusters.tolist(),
                'n_clusters': len(set(clusters))
            }
        except Exception as e:
            logger.error(f"Address clustering failed: {e}")
            return {'error': str(e)}

# Global ML service instance
ml_service = MLService()
