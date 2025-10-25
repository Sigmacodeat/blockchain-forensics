#!/usr/bin/env python3
"""
ML Risk Model Training Script
==============================

Trainiert LightGBM Risk Predictor mit labeled Address-Daten.

Usage:
    python scripts/train_risk_model.py --data data/labeled_addresses.csv --output models/risk_predictor_v1.txt

Features:
- Automated Feature Engineering
- Train/Test Split
- Hyperparameter Tuning (optional)
- Model Evaluation
- SHAP Feature Importance
"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check ML dependencies
try:
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, 
        f1_score, roc_auc_score, classification_report
    )
except ImportError as e:
    logger.error(f"Missing ML dependencies: {e}")
    logger.error("Install with: pip install lightgbm scikit-learn")
    sys.exit(1)

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    logger.warning("SHAP not installed - feature importance will be limited")


# Feature columns (must match RiskFeatures in risk_predictor.py)
FEATURE_COLUMNS = [
    'total_transactions',
    'log_total_value_usd',
    'log_avg_transaction_value',
    'log_max_transaction_value',
    'unique_counterparties',
    'account_age_days',
    'transactions_last_24h',
    'transactions_last_7d',
    'transactions_last_30d',
    'clustering_coefficient',
    'betweenness_centrality',
    'degree_centrality',
    'has_mixer_labels',
    'has_exchange_labels',
    'has_defi_labels',
    'has_sanctions_labels',
    'total_labels_count',
    'active_chains_count',
    'cross_chain_transfers_count',
    'bridge_usage_frequency',
    'avg_gas_price_ratio',
    'nonce_gaps_count',
    'failed_tx_ratio',
    'self_transfer_ratio',
]


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and validate training data"""
    logger.info(f"Loading data from {csv_path}")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} samples")
    
    # Validate required columns
    required = FEATURE_COLUMNS + ['is_high_risk']
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check for NaN values
    nan_cols = df[FEATURE_COLUMNS].columns[df[FEATURE_COLUMNS].isna().any()].tolist()
    if nan_cols:
        logger.warning(f"NaN values found in columns: {nan_cols}")
        logger.warning("Filling NaN with 0")
        df[FEATURE_COLUMNS] = df[FEATURE_COLUMNS].fillna(0)
    
    return df


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Extract X and y from dataframe"""
    X = df[FEATURE_COLUMNS].values
    y = df['is_high_risk'].values
    
    logger.info(f"Features shape: {X.shape}")
    logger.info(f"Labels shape: {y.shape}")
    logger.info(f"Class distribution: {np.bincount(y)} (0=low-risk, 1=high-risk)")
    
    return X, y


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    params: dict = None
) -> lgb.Booster:
    """Train LightGBM model"""
    
    # Default hyperparameters (optimized for imbalanced classification)
    if params is None:
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'min_data_in_leaf': 20,
            'max_depth': 8,
            'verbose': -1,
            'is_unbalance': True,
        }
    
    # Create datasets
    train_data = lgb.Dataset(X_train, label=y_train, feature_name=FEATURE_COLUMNS)
    val_data = lgb.Dataset(X_val, label=y_val, feature_name=FEATURE_COLUMNS, reference=train_data)
    
    # Train
    logger.info("Training LightGBM model...")
    logger.info(f"Hyperparameters: {params}")
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=200,
        valid_sets=[train_data, val_data],
        valid_names=['train', 'val'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=20, verbose=True),
            lgb.log_evaluation(period=10)
        ],
    )
    
    logger.info(f"Training completed. Best iteration: {model.best_iteration}")
    
    return model


def evaluate_model(model: lgb.Booster, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Evaluate model on test set"""
    logger.info("Evaluating model on test set...")
    
    # Predictions
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # Metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
    }
    
    logger.info("Model Performance:")
    logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
    logger.info(f"  Precision: {metrics['precision']:.4f}")
    logger.info(f"  Recall:    {metrics['recall']:.4f}")
    logger.info(f"  F1 Score:  {metrics['f1_score']:.4f}")
    logger.info(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
    
    # Classification Report
    logger.info("\nClassification Report:")
    report = classification_report(y_test, y_pred, target_names=['Low-Risk', 'High-Risk'])
    logger.info(f"\n{report}")
    
    return metrics


def analyze_feature_importance(model: lgb.Booster, X_test: np.ndarray = None):
    """Analyze and display feature importance"""
    logger.info("\nFeature Importance (Gain):")
    
    importance = model.feature_importance(importance_type='gain')
    feature_importance = sorted(
        zip(FEATURE_COLUMNS, importance),
        key=lambda x: x[1],
        reverse=True
    )
    
    for i, (feature, score) in enumerate(feature_importance[:10], 1):
        logger.info(f"  {i}. {feature:30s} {score:10.2f}")
    
    # SHAP values (if available and test data provided)
    if HAS_SHAP and X_test is not None:
        try:
            logger.info("\nCalculating SHAP values...")
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_test[:100])  # Sample 100 for speed
            
            logger.info("Top features by SHAP (absolute mean):")
            mean_shap = np.abs(shap_values).mean(axis=0)
            shap_importance = sorted(
                zip(FEATURE_COLUMNS, mean_shap),
                key=lambda x: x[1],
                reverse=True
            )
            
            for i, (feature, score) in enumerate(shap_importance[:10], 1):
                logger.info(f"  {i}. {feature:30s} {score:10.4f}")
                
        except Exception as e:
            logger.warning(f"SHAP analysis failed: {e}")


def save_model(model: lgb.Booster, output_path: Path, metrics: dict):
    """Save model and metadata"""
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model.save_model(str(output_path))
    logger.info(f"Model saved to: {output_path}")
    
    # Save metadata
    metadata_path = output_path.with_suffix('.json')
    metadata = {
        'trained_at': datetime.utcnow().isoformat(),
        'num_features': len(FEATURE_COLUMNS),
        'feature_names': FEATURE_COLUMNS,
        'best_iteration': model.best_iteration,
        'metrics': metrics,
        'params': model.params,
    }
    
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata saved to: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description='Train ML Risk Predictor')
    parser.add_argument(
        '--data',
        type=Path,
        required=True,
        help='Path to labeled CSV data'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('models/risk_predictor_v1.txt'),
        help='Output path for trained model'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Test set size (default: 0.2)'
    )
    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("ML Risk Model Training")
    logger.info("=" * 60)
    
    # Load data
    df = load_data(args.data)
    X, y = prepare_features(df)
    
    # Train/Test Split
    logger.info(f"Splitting data (test_size={args.test_size}, seed={args.random_seed})")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=args.test_size,
        random_state=args.random_seed,
        stratify=y
    )
    
    # Further split train into train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train,
        test_size=0.2,
        random_state=args.random_seed,
        stratify=y_train
    )
    
    logger.info(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
    
    # Train model
    model = train_model(X_train, y_train, X_val, y_val)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Feature importance
    analyze_feature_importance(model, X_test)
    
    # Save
    save_model(model, args.output, metrics)
    
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info("=" * 60)
    
    # Recommendations
    if metrics['roc_auc'] < 0.80:
        logger.warning("⚠️  ROC-AUC < 0.80 - Consider:")
        logger.warning("   - More training data")
        logger.warning("   - Feature engineering")
        logger.warning("   - Hyperparameter tuning")
    elif metrics['roc_auc'] >= 0.90:
        logger.info("✅ Excellent model performance (ROC-AUC >= 0.90)!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
