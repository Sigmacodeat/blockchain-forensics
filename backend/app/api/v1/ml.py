"""
ML Model Management API
=======================

Endpoints für Model Training, Evaluation und Explainability
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field

from app.ml.model_trainer import model_trainer
from app.ml.feature_engineering import feature_engineer
from app.ml.risk_scorer import risk_scorer

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== Request/Response Models =====

class TrainModelRequest(BaseModel):
    """Request to train new model"""
    training_data_url: Optional[str] = Field(
        None,
        description="URL or path to training data CSV"
    )
    use_synthetic_data: bool = Field(
        True,
        description="Use synthetic data if no training data provided"
    )


class TrainModelResponse(BaseModel):
    """Response from model training"""
    status: str
    message: str
    metrics: Dict
    feature_importance: list
    model_path: str


class EvaluateModelRequest(BaseModel):
    """Request to evaluate model"""
    test_data_path: str


class EvaluateModelResponse(BaseModel):
    """Response from model evaluation"""
    metrics: Dict
    test_samples: int


class ExplainPredictionRequest(BaseModel):
    """Request to explain prediction"""
    address: str
    chain: str = "ethereum"


class ExplainPredictionResponse(BaseModel):
    """Response with SHAP explanation"""
    address: str
    risk_score: float
    risk_level: str
    shap_explanation: Dict
    top_contributing_features: list


class FeatureExtractionRequest(BaseModel):
    """Request to extract features"""
    address: str
    chain: str = "ethereum"


class FeatureExtractionResponse(BaseModel):
    """Response with extracted features"""
    address: str
    chain: str
    feature_count: int
    features: Dict


# ===== API Endpoints =====

@router.post("/train", response_model=TrainModelResponse)
async def train_ml_model(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks
) -> TrainModelResponse:
    """
    Train XGBoost risk scoring model
    
    **Process:**
    1. Load labeled training data
    2. Extract 100+ features
    3. Train XGBoost classifier
    4. Evaluate on test set
    5. Generate SHAP explanations
    6. Save model
    
    **Training Data Format (CSV):**
    ```csv
    address,chain,label,label_source
    0x123...,ethereum,1,chainalysis
    0x456...,ethereum,0,manual
    ```
    
    **Note:** Training can take 10-30 minutes depending on data size
    """
    try:
        logger.info("Starting model training...")
        
        # Train model (background task if large dataset)
        result = await model_trainer.train_model(
            training_data_path=request.training_data_url,
            save_path=None  # Use default path
        )
        
        return TrainModelResponse(
            status="success",
            message="Model training completed successfully",
            metrics=result['metrics'],
            feature_importance=result['feature_importance'],
            model_path=result['model_path']
        )
        
    except Exception as e:
        logger.error(f"Model training failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Model training failed: {str(e)}"
        )


@router.post("/evaluate", response_model=EvaluateModelResponse)
async def evaluate_model(
    request: EvaluateModelRequest
) -> EvaluateModelResponse:
    """
    Evaluate trained model on test data
    
    **Test Data Format:** Same as training data (CSV with labels)
    
    Returns evaluation metrics (ROC-AUC, Precision, Recall, etc.)
    """
    try:
        metrics = await model_trainer.evaluate_on_new_data(
            test_data_path=request.test_data_path
        )
        
        return EvaluateModelResponse(
            metrics=metrics,
            test_samples=metrics.get('n_samples', 0)
        )
        
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.post("/explain", response_model=ExplainPredictionResponse)
async def explain_prediction(
    request: ExplainPredictionRequest
) -> ExplainPredictionResponse:
    """
    Explain risk score prediction using SHAP values
    
    **Returns:**
    - Risk score (0-1)
    - Risk level (low/medium/high/critical)
    - SHAP explanation (top contributing features)
    - Feature values
    
    **Example:**
    ```json
    {
      "address": "0x123...",
      "risk_score": 0.85,
      "top_contributing_features": [
        {
          "feature": "tornado_cash_interactions",
          "value": 5,
          "shap_value": 0.45,
          "contribution": "positive"
        }
      ]
    }
    ```
    """
    try:
        # Extract features
        features = await feature_engineer.extract_features(
            request.address,
            request.chain
        )
        
        # Calculate risk score
        risk_result = await risk_scorer.calculate_risk_score(
            request.address,
            features
        )
        
        # Get SHAP explanation
        explanation = model_trainer.explain_prediction(
            request.address,
            features
        )
        
        return ExplainPredictionResponse(
            address=request.address,
            risk_score=risk_result['risk_score'],
            risk_level=risk_result['risk_level'],
            shap_explanation=explanation,
            top_contributing_features=explanation.get('top_features', [])
        )
        
    except Exception as e:
        logger.error(f"Prediction explanation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Explanation failed: {str(e)}"
        )


@router.post("/features/extract", response_model=FeatureExtractionResponse)
async def extract_features(
    request: FeatureExtractionRequest
) -> FeatureExtractionResponse:
    """
    Extract 100+ features for an address
    
    **Feature Categories:**
    1. Transaction Patterns (20 features)
    2. Network Features (25 features)
    3. Temporal Features (15 features)
    4. Entity Labels (10 features)
    5. Risk Indicators (30 features)
    
    **Use Case:**
    - Debugging feature extraction
    - Custom analysis
    - Data export for external ML tools
    """
    try:
        features = await feature_engineer.extract_features(
            request.address,
            request.chain
        )
        
        return FeatureExtractionResponse(
            address=request.address,
            chain=request.chain,
            feature_count=len(features),
            features=features
        )
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Feature extraction failed: {str(e)}"
        )


@router.get("/model/info")
async def get_model_info() -> Dict:
    """
    Get information about current ML model
    
    Returns model metadata, training metrics, feature names
    """
    try:
        if model_trainer.model is None:
            return {
                "status": "no_model",
                "message": "No model trained or loaded",
                "available_features": 100
            }
        
        return {
            "status": "active",
            "n_features": len(model_trainer.feature_names) if model_trainer.feature_names else 0,
            "feature_names": model_trainer.feature_names,
            "training_metrics": model_trainer.training_metrics,
            "model_params": model_trainer.params
        }
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.get("/features/list")
async def list_available_features() -> Dict:
    """
    List all available feature categories and names
    
    Returns comprehensive feature documentation
    """
    return {
        "total_features": "100+",
        "categories": {
            "transaction_patterns": {
                "count": 20,
                "features": [
                    "tx_count_total", "tx_count_24h", "tx_count_7d", "tx_count_30d",
                    "tx_velocity_24h", "avg_tx_value", "median_tx_value", "max_tx_value",
                    "unique_receivers", "unique_senders", "value_concentration"
                ]
            },
            "network_features": {
                "count": 25,
                "features": [
                    "out_degree", "in_degree", "total_degree", "clustering_coefficient",
                    "betweenness_centrality", "pagerank", "community_size"
                ]
            },
            "temporal_features": {
                "count": 15,
                "features": [
                    "account_age_days", "days_since_last_tx", "activity_hour_entropy",
                    "weekend_activity_ratio", "has_burst_activity", "max_dormancy_days"
                ]
            },
            "entity_labels": {
                "count": 10,
                "features": [
                    "is_exchange", "is_mixer", "is_defi", "is_smart_contract",
                    "has_sanctions_label", "is_scam", "entity_reputation_score"
                ]
            },
            "risk_indicators": {
                "count": 30,
                "features": [
                    "tornado_cash_interactions", "mixer_interactions_total",
                    "sanctioned_entity_hops", "high_risk_connections_1hop",
                    "cross_chain_activity", "bridge_transaction_count"
                ]
            }
        }
    }
