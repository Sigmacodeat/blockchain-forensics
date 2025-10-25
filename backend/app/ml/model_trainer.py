"""
XGBoost Model Training Pipeline
================================

Training, Evaluation und Deployment von ML Risk Scoring Models
"""

import logging
import pickle
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

# ML Libraries
try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        classification_report,
        confusion_matrix,
        roc_auc_score,
        precision_recall_curve,
        roc_curve
    )
    import shap
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("XGBoost or sklearn not available. ML training disabled.")

from app.config import settings
from app.ml.feature_engineering import feature_engineer

logger = logging.getLogger(__name__)


class RiskModelTrainer:
    """
    XGBoost Risk Model Trainer
    
    **Training Pipeline:**
    1. Data Collection (labeled addresses)
    2. Feature Engineering (100+ features)
    3. Model Training (XGBoost)
    4. Evaluation (ROC-AUC, Precision, Recall)
    5. Explainability (SHAP values)
    6. Model Export
    """
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.training_metrics = {}
        self.explainer = None
        
        # Model hyperparameters (optimized for imbalanced data)
        self.params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': 10,  # Handle imbalanced data (10:1 ratio)
            'min_child_weight': 5,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42
        }
    
    async def train_model(
        self,
        training_data_path: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> Dict:
        """
        Train XGBoost risk model
        
        Args:
            training_data_path: Path to labeled training data (CSV)
            save_path: Where to save trained model
        
        Returns:
            Training metrics and evaluation results
        """
        if not XGBOOST_AVAILABLE:
            raise RuntimeError("XGBoost not available. Install with: pip install xgboost")
        
        logger.info("Starting XGBoost model training...")
        
        # 1. Load and prepare data
        X_train, X_test, y_train, y_test = await self._prepare_training_data(
            training_data_path
        )
        
        # 2. Train model
        self.model = xgb.XGBClassifier(**self.params)
        
        logger.info(f"Training on {len(X_train)} samples...")
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            early_stopping_rounds=20,
            verbose=True
        )
        
        # 3. Evaluate
        metrics = self._evaluate_model(X_test, y_test)
        self.training_metrics = metrics
        
        # 4. Feature importance
        feature_importance = self._get_feature_importance()
        
        # 5. SHAP explainability
        if len(X_test) > 0:
            self.explainer = shap.TreeExplainer(self.model)
            shap_values = self.explainer.shap_values(X_test[:100])  # Sample for speed
            
            # Save SHAP summary
            metrics['shap_summary'] = {
                'top_features': self._get_top_shap_features(shap_values, X_test[:100])
            }
        
        # 6. Save model
        if save_path is None:
            save_path = settings.XGBOOST_MODEL_PATH
        
        self._save_model(save_path)
        
        logger.info(f"Model training complete. ROC-AUC: {metrics.get('roc_auc', 0):.4f}")
        
        return {
            'metrics': metrics,
            'feature_importance': feature_importance,
            'model_path': save_path
        }
    
    async def _prepare_training_data(
        self,
        data_path: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare training data
        
        Data format (CSV):
        - address, chain, label (0/1), label_source
        
        If no data_path provided, generate synthetic data for demo
        """
        if data_path and Path(data_path).exists():
            # Load real labeled data
            df = pd.read_csv(data_path)
            logger.info(f"Loaded {len(df)} labeled addresses from {data_path}")
        else:
            # Generate synthetic training data for demo
            logger.warning("No training data found. Generating synthetic demo data...")
            df = await self._generate_synthetic_data(n_samples=1000)
        
        # Extract features for each address
        features_list = []
        labels = []
        
        for idx, row in df.iterrows():
            try:
                features = await feature_engineer.extract_features(
                    row['address'],
                    row.get('chain', 'ethereum')
                )
                features_list.append(features)
                labels.append(row['label'])
                
                if idx % 100 == 0:
                    logger.info(f"Extracted features for {idx}/{len(df)} addresses")
                    
            except Exception as e:
                logger.error(f"Feature extraction failed for {row['address']}: {e}")
                continue
        
        # Convert to DataFrame
        X = pd.DataFrame(features_list)
        y = pd.Series(labels)
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Train/test split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42,
            stratify=y  # Preserve class distribution
        )
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        logger.info(f"Class distribution: {y.value_counts().to_dict()}")
        
        return X_train, X_test, y_train, y_test
    
    async def _generate_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic training data for demo/testing
        
        Creates realistic-looking addresses with labels
        """
        import random
        
        data = []
        
        # High-risk patterns
        high_risk_addresses = [
            '0x' + ''.join(random.choices('0123456789abcdef', k=40))
            for _ in range(n_samples // 10)  # 10% high-risk
        ]
        
        # Low-risk (normal) addresses
        low_risk_addresses = [
            '0x' + ''.join(random.choices('0123456789abcdef', k=40))
            for _ in range(n_samples - len(high_risk_addresses))
        ]
        
        # Label high-risk
        for addr in high_risk_addresses:
            data.append({
                'address': addr,
                'chain': 'ethereum',
                'label': 1,  # High-risk
                'label_source': 'synthetic'
            })
        
        # Label low-risk
        for addr in low_risk_addresses:
            data.append({
                'address': addr,
                'chain': 'ethereum',
                'label': 0,  # Low-risk
                'label_source': 'synthetic'
            })
        
        return pd.DataFrame(data)
    
    def _evaluate_model(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Evaluate model performance
        """
        # Predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Classification report
        class_report = classification_report(
            y_test, y_pred,
            target_names=['Low-Risk', 'High-Risk'],
            output_dict=True
        )
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # ROC-AUC
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Precision-Recall curve
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        
        # False Positive Rate, True Positive Rate
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        
        metrics = {
            'roc_auc': roc_auc,
            'accuracy': class_report['accuracy'],
            'precision': class_report['High-Risk']['precision'],
            'recall': class_report['High-Risk']['recall'],
            'f1_score': class_report['High-Risk']['f1-score'],
            'confusion_matrix': cm.tolist(),
            'classification_report': class_report,
            'fpr': fpr.tolist()[:100],  # Truncate for storage
            'tpr': tpr.tolist()[:100],
            'precision_curve': precision.tolist()[:100],
            'recall_curve': recall.tolist()[:100]
        }
        
        logger.info("Model Evaluation:")
        logger.info(f"  ROC-AUC: {roc_auc:.4f}")
        logger.info(f"  Precision: {metrics['precision']:.4f}")
        logger.info(f"  Recall: {metrics['recall']:.4f}")
        logger.info(f"  F1-Score: {metrics['f1_score']:.4f}")
        
        return metrics
    
    def _get_feature_importance(self, top_n: int = 20) -> List[Dict]:
        """
        Get feature importance from trained model
        """
        importances = self.model.feature_importances_
        
        # Create list of (feature, importance) tuples
        feature_importance = [
            {
                'feature': name,
                'importance': float(imp)
            }
            for name, imp in zip(self.feature_names, importances)
        ]
        
        # Sort by importance
        feature_importance = sorted(
            feature_importance,
            key=lambda x: x['importance'],
            reverse=True
        )
        
        logger.info(f"Top {top_n} important features:")
        for i, feat in enumerate(feature_importance[:top_n]):
            logger.info(f"  {i+1}. {feat['feature']}: {feat['importance']:.4f}")
        
        return feature_importance[:top_n]
    
    def _get_top_shap_features(
        self,
        shap_values: np.ndarray,
        X: pd.DataFrame,
        top_n: int = 10
    ) -> List[Dict]:
        """
        Get top features by SHAP values
        """
        # Mean absolute SHAP value per feature
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        top_features = [
            {
                'feature': self.feature_names[i],
                'mean_abs_shap': float(mean_abs_shap[i])
            }
            for i in np.argsort(mean_abs_shap)[::-1][:top_n]
        ]
        
        return top_features
    
    def _save_model(self, path: str):
        """
        Save trained model to disk
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save metadata
        metadata_path = path.replace('.pkl', '_metadata.json')
        metadata = {
            'training_date': datetime.now().isoformat(),
            'feature_names': self.feature_names,
            'params': self.params,
            'metrics': self.training_metrics,
            'n_features': len(self.feature_names)
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model saved to {path}")
        logger.info(f"Metadata saved to {metadata_path}")
    
    async def evaluate_on_new_data(
        self,
        test_data_path: str
    ) -> Dict:
        """
        Evaluate trained model on new test data
        """
        if self.model is None:
            raise ValueError("No model loaded. Train or load a model first.")
        
        # Load test data
        df = pd.read_csv(test_data_path)
        
        # Extract features
        features_list = []
        labels = []
        
        for idx, row in df.iterrows():
            features = await feature_engineer.extract_features(
                row['address'],
                row.get('chain', 'ethereum')
            )
            features_list.append(features)
            labels.append(row['label'])
        
        X_test = pd.DataFrame(features_list)
        y_test = pd.Series(labels)
        
        # Evaluate
        metrics = self._evaluate_model(X_test, y_test)
        
        return metrics
    
    def explain_prediction(
        self,
        address: str,
        features: Dict
    ) -> Dict:
        """
        Explain prediction using SHAP values
        
        Args:
            address: Address being scored
            features: Extracted features
        
        Returns:
            SHAP explanation with top contributing features
        """
        if self.model is None or self.explainer is None:
            return {
                'explanation': 'Model not trained or SHAP not available',
                'top_features': []
            }
        
        # Convert features to DataFrame
        X = pd.DataFrame([features])
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # Get top contributing features
        feature_contributions = [
            {
                'feature': name,
                'value': float(features[name]),
                'shap_value': float(shap_values[0][i]),
                'contribution': 'positive' if shap_values[0][i] > 0 else 'negative'
            }
            for i, name in enumerate(self.feature_names)
        ]
        
        # Sort by absolute SHAP value
        feature_contributions = sorted(
            feature_contributions,
            key=lambda x: abs(x['shap_value']),
            reverse=True
        )
        
        return {
            'address': address,
            'prediction': float(self.model.predict_proba(X)[0][1]),
            'top_features': feature_contributions[:10],
            'base_value': float(self.explainer.expected_value)
        }


# Singleton instance
model_trainer = RiskModelTrainer()
