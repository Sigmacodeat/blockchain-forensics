"""Machine Learning Package
ML Module - Machine Learning for Risk Scoring and Analysis

Lightweight __init__: avoid eager imports of heavy modules to prevent
configuration side effects during test collection. Modules should be
imported explicitly by consumers (e.g., `from app.ml.feature_engineering import feature_engineer`).
"""

__all__ = [
    "risk_scorer",
    "wallet_clusterer",
    "feature_engineer",
    "model_trainer",
]
