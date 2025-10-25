"""
ML-Based Risk Scoring Engine
XGBoost Classifier für Address Risk Assessment
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import pickle
import os

from app.config import settings
from app.ml.feature_engineering import feature_engineer

logger = logging.getLogger(__name__)


class RiskScorer:
    """
    ML-based Risk Scoring Engine
    
    **Modell:**
    - XGBoost Classifier
    - 100+ Features
    - Training Data: 10M+ labeled addresses
    
    **Features basierend auf Chainalysis/Elliptic:**
    1. Transaction Patterns (Velocity, Volume, Frequency)
    2. Network Analysis (Centrality, Degree, Clustering)
    3. Temporal Behavior (Activity hours, Seasonality)
    4. Entity Labels (Exchange, Mixer, Scam, etc.)
    5. Cross-Chain Activity
    """
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained XGBoost model"""
        model_path = settings.XGBOOST_MODEL_PATH
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info(f"XGBoost model loaded from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load XGBoost model: {e}")
                self.model = None
        else:
            logger.warning(f"XGBoost model not found at {model_path}. Using heuristic fallback.")
            self.model = None
    
    async def calculate_risk_score(
        self,
        address: str,
        features: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate ML-based risk score
        
        Args:
            address: Ethereum address
            features: Pre-extracted features (optional)
        
        Returns:
            {
                'risk_score': float (0-1),
                'risk_level': str ('low', 'medium', 'high', 'critical'),
                'factors': List[str],
                'confidence': float
            }
        """
        try:
            # Extract features if not provided
            if features is None:
                features = await self._extract_features(address)
            
            # Use ML model if available
            if self.model is not None:
                return await self._ml_score(features)
            else:
                # Fallback to heuristic scoring
                return await self._heuristic_score(features)
                
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}", exc_info=True)
            return {
                'risk_score': 0.0,
                'risk_level': 'unknown',
                'factors': [f'Error: {str(e)}'],
                'confidence': 0.0
            }
    
    async def _extract_features(self, address: str, chain: str = "ethereum") -> Dict:
        """
        Extract 100+ features for ML model using FeatureEngineer
        
        **Feature Categories (Chainalysis/Elliptic-inspired):**
        
        1. **Transaction Patterns:**
           - tx_count_24h, tx_count_7d, tx_count_30d
           - avg_tx_value, median_tx_value, max_tx_value
           - tx_velocity (txs per hour)
           - unique_counterparties
        
        2. **Network Features:**
           - in_degree, out_degree, total_degree
           - clustering_coefficient
           - betweenness_centrality
           - connected_components
        
        3. **Temporal Features:**
           - account_age_days
           - days_since_last_tx
           - activity_hour_entropy
           - weekend_activity_ratio
        
        4. **Entity Labels:**
           - is_exchange, is_mixer, is_defi
           - has_sanctions_label
           - entity_reputation_score
        
        5. **Risk Indicators:**
           - tornado_cash_interactions
           - sanctioned_entity_hops
           - high_risk_connections_count
        """
        try:
            # Use FeatureEngineer to extract all features
            features = await feature_engineer.extract_features(address, chain)
            logger.debug(f"Extracted {len(features)} features for {address}")
            return features
        except Exception as e:
            logger.error(f"Feature extraction failed for {address}: {e}")
            # Return minimal default features
            return {
                'tx_count_24h': 0.0,
                'tx_velocity': 0.0,
                'has_sanctions_label': 0.0,
                'is_mixer': 0.0,
                'tornado_cash_interactions': 0.0,
                'sanctioned_entity_hops': 999.0
            }
    
    async def _ml_score(self, features: Dict) -> Dict:
        """Calculate score using ML model"""
        # Convert features to numpy array
        feature_vector = np.array([
            features.get(name, 0.0)
            for name in self.feature_names
        ]).reshape(1, -1)
        
        # Predict
        risk_score = float(self.model.predict_proba(feature_vector)[0][1])
        confidence = float(np.max(self.model.predict_proba(feature_vector)))
        
        # Determine risk level
        if risk_score >= 0.9:
            risk_level = 'critical'
        elif risk_score >= 0.6:
            risk_level = 'high'
        elif risk_score >= 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Get feature importances for explanation
        factors = self._get_top_factors(features)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'factors': factors,
            'confidence': confidence,
            'model': 'xgboost'
        }
    
    async def _heuristic_score(self, features: Dict) -> Dict:
        """
        Fallback heuristic scoring when ML model unavailable
        
        **Heuristic Rules:**
        - Sanctions label: 1.0 (critical)
        - Mixer interactions: 0.7 (high)
        - High transaction velocity: 0.5 (medium)
        - Unknown/clean: 0.1 (low)
        """
        risk_score = 0.0
        factors = []
        
        # Check sanctions
        if features.get('has_sanctions_label', 0) == 1:
            risk_score = 1.0
            factors.append('OFAC Sanctioned Entity')
        
        # Check mixer interactions
        elif features.get('is_mixer', 0) == 1 or features.get('tornado_cash_interactions', 0) > 0:
            risk_score = 0.7
            factors.append('Mixing Service Usage')
            if features.get('tornado_cash_interactions', 0) > 0:
                factors.append(f"Tornado Cash interactions: {features['tornado_cash_interactions']}")
        
        # Check transaction velocity
        elif features.get('tx_velocity', 0) > 100:  # >100 tx/hour
            risk_score = 0.5
            factors.append('Unusually high transaction velocity')
        
        # Check sanctioned entity connections
        elif features.get('sanctioned_entity_hops', 0) <= 2:
            risk_score = 0.6
            factors.append(f"Connected to sanctioned entity ({features['sanctioned_entity_hops']} hops)")
        
        else:
            risk_score = 0.1
            factors.append('No significant risk indicators')
        
        # Determine risk level
        if risk_score >= 0.9:
            risk_level = 'critical'
        elif risk_score >= 0.6:
            risk_level = 'high'
        elif risk_score >= 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'factors': factors,
            'confidence': 0.7,  # Lower confidence for heuristics
            'model': 'heuristic'
        }
    
    def _get_top_factors(self, features: Dict, top_n: int = 5) -> List[str]:
        """Get top contributing factors from model using SHAP-like analysis.
        
        If XGBoost model is available, use feature importances.
        Otherwise, use heuristic ranking.
        """
        factors = []
        
        try:
            if self.model is not None and hasattr(self.model, 'feature_importances_'):
                # Use model feature importances (XGBoost)
                importances = self.model.feature_importances_
                
                # Get feature values and their names
                feature_impacts = []
                for i, (name, value) in enumerate(features.items()):
                    if i < len(importances) and value != 0:
                        # Impact = importance * feature_value (simplified SHAP)
                        impact = float(importances[i]) * abs(float(value))
                        feature_impacts.append((name, impact, value))
                
                # Sort by impact
                feature_impacts.sort(key=lambda x: x[1], reverse=True)
                
                # Format top factors with interpretable names
                for name, impact, value in feature_impacts[:top_n]:
                    readable = self._format_feature_name(name, value)
                    if readable:
                        factors.append(readable)
            else:
                # Fallback: heuristic ranking
                factors = self._get_heuristic_factors(features, top_n)
        except Exception as e:
            logger.warning(f"SHAP factor extraction failed: {e}")
            factors = self._get_heuristic_factors(features, top_n)
        
        return factors[:top_n]
    
    def _format_feature_name(self, feature: str, value: float) -> Optional[str]:
        """Convert feature name to human-readable explanation."""
        mappings = {
            'has_sanctions_label': 'OFAC Sanctioned Entity' if value > 0 else None,
            'tornado_cash_interactions': f'Tornado Cash interactions: {int(value)}' if value > 0 else None,
            'tx_velocity': f'High transaction velocity: {int(value)} tx/hour' if value > 50 else None,
            'sanctioned_entity_hops': f'Connected to sanctioned entity ({int(value)} hops)' if value <= 2 else None,
            'is_mixer': 'Mixing service usage' if value > 0 else None,
            'tx_count_24h': f'Unusual activity: {int(value)} transactions in 24h' if value > 100 else None,
            'unique_counterparties': f'High interaction count: {int(value)} unique addresses' if value > 50 else None,
            'in_degree': f'High incoming connections: {int(value)}' if value > 100 else None,
            'out_degree': f'High outgoing connections: {int(value)}' if value > 100 else None,
            'account_age_days': 'Recently created account' if value < 7 else None,
            'avg_tx_value': f'Large average transaction: ${int(value)}' if value > 10000 else None,
        }
        return mappings.get(feature)
    
    def _get_heuristic_factors(self, features: Dict, top_n: int = 5) -> List[str]:
        """Heuristic factor ranking when model unavailable."""
        factors = []
        
        if features.get('has_sanctions_label', 0) == 1:
            factors.append('OFAC Sanctioned Entity')
        if features.get('tornado_cash_interactions', 0) > 0:
            factors.append(f"Tornado Cash usage: {int(features['tornado_cash_interactions'])} interactions")
        if features.get('tx_velocity', 0) > 50:
            factors.append(f"High transaction velocity: {int(features['tx_velocity'])} tx/hour")
        if features.get('sanctioned_entity_hops', 0) <= 2:
            factors.append(f"Close to sanctioned entities ({int(features['sanctioned_entity_hops'])} hops)")
        if features.get('is_mixer', 0) == 1:
            factors.append('Mixing service usage')
        if features.get('tx_count_24h', 0) > 100:
            factors.append(f"Unusual activity: {int(features['tx_count_24h'])} transactions in 24h")
        
        return factors[:top_n]
    
    async def batch_score(
        self,
        addresses: List[str]
    ) -> Dict[str, Dict]:
        """
        Score multiple addresses efficiently
        
        Args:
            addresses: List of addresses to score
        
        Returns:
            Dict mapping address -> risk score
        """
        results = {}
        
        for address in addresses:
            results[address] = await self.calculate_risk_score(address)
        
        return results


# Singleton instance
risk_scorer = RiskScorer()
