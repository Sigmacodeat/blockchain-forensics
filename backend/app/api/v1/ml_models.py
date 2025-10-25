"""
ML Model API für Blockchain Forensics
Endpoints für ML-Modelle und Anomalie-Erkennung
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
import json
from datetime import datetime

from app.services.ml_model_service import ml_model_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ModelTrainingRequest(BaseModel):
    """Request model for training ML models"""
    model_id: str = Field(..., min_length=1, max_length=100)
    training_data: List[Dict[str, Any]] = Field(..., min_length=10)
    contamination: float = Field(0.1, ge=0.01, le=0.5)
    model_config = {"protected_namespaces": ()}


class AnomalyPredictionRequest(BaseModel):
    """Request model for anomaly prediction"""
    transaction_data: Dict[str, Any]
    model_id: str = Field("isolation_forest_v1")
    model_config = {"protected_namespaces": ()}


class ModelValidationRequest(BaseModel):
    """Request model for model validation"""
    model_id: str
    validation_data: List[Dict[str, Any]]
    model_config = {"protected_namespaces": ()}


@router.post("/models/train")
async def train_model(request: ModelTrainingRequest) -> Dict[str, Any]:
    """
    Trainiere ein ML-Modell für Anomalie-Erkennung

    **Request Body:**
    - model_id: Eindeutige ID für das Modell
    - training_data: Liste von Trainingsdaten-Samples
    - contamination: Erwarteter Anteil von Anomalien (0.01-0.5)
    """
    try:
        result = ml_model_service.train_anomaly_detection_model(
            training_data=request.training_data,
            model_id=request.model_id,
            contamination=request.contamination
        )

        return {
            "status": "success",
            "model_id": result["model_id"],
            "performance": result["performance"],
            "training_timestamp": result["training_timestamp"]
        }

    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/predict")
async def predict_anomaly(request: AnomalyPredictionRequest) -> Dict[str, Any]:
    """
    Führe Anomalie-Vorhersage durch

    **Request Body:**
    - transaction_data: Transaktionsdaten für Vorhersage
    - model_id: ID des zu verwendenden Modells (optional)
    """
    try:
        result = ml_model_service.predict_anomaly(
            transaction_data=request.transaction_data,
            model_id=request.model_id
        )

        return result

    except Exception as e:
        logger.error(f"Error predicting anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models() -> List[Dict[str, Any]]:
    """
    Liste alle verfügbaren ML-Modelle auf
    """
    try:
        models = ml_model_service.list_models()
        return models

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}")
async def get_model(model_id: str) -> Dict[str, Any]:
    """
    Hole Details zu einem spezifischen Modell

    **Path Parameters:**
    - model_id: ID des Modells
    """
    try:
        models = ml_model_service.list_models()
        model = next((m for m in models if m["model_id"] == model_id), None)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Add performance data if available
        performance = ml_model_service.get_model_performance(model_id)
        if performance:
            model["performance"] = performance

        return model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{model_id}")
async def delete_model(model_id: str) -> Dict[str, Any]:
    """
    Lösche ein ML-Modell

    **Path Parameters:**
    - model_id: ID des zu löschenden Modells
    """
    try:
        success = ml_model_service.delete_model(model_id)

        if not success:
            raise HTTPException(status_code=404, detail="Model not found or could not be deleted")

        return {
            "status": "deleted",
            "model_id": model_id,
            "deleted_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/validate")
async def validate_model(request: ModelValidationRequest) -> Dict[str, Any]:
    """
    Validiere ein ML-Modell mit Validierungsdaten

    **Request Body:**
    - model_id: ID des zu validierenden Modells
    - validation_data: Validierungsdaten für Performance-Bewertung
    """
    try:
        result = ml_model_service.validate_model_performance(
            model_id=request.model_id,
            validation_data=request.validation_data
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "validated",
            "model_id": request.model_id,
            "validation_results": result,
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating model {request.model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/generate-training-data")
async def generate_training_data(
    events: List[Dict[str, Any]] = Body(...),
    lookback_days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Generiere Trainingsdaten aus historischen Events

    **Query Parameters:**
    - lookback_days: Anzahl Tage zurückblickend (1-365)

    **Request Body:**
    - events: Liste von historischen Events
    """
    try:
        training_data = ml_model_service.generate_training_data_from_events(
            events=events,
            lookback_days=lookback_days
        )

        return {
            "status": "generated",
            "training_samples": len(training_data),
            "lookback_days": lookback_days,
            "generated_at": datetime.utcnow().isoformat(),
            "sample_features": len(training_data[0]["features"]) if training_data else 0
        }

    except Exception as e:
        logger.error(f"Error generating training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}/performance")
async def get_model_performance(model_id: str) -> Dict[str, Any]:
    """
    Hole Performance-Metriken für ein Modell

    **Path Parameters:**
    - model_id: ID des Modells
    """
    try:
        performance = ml_model_service.get_model_performance(model_id)

        if not performance:
            raise HTTPException(status_code=404, detail="Performance data not found")

        return {
            "model_id": model_id,
            "performance": performance,
            "retrieved_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model performance {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/feature-config")
async def get_feature_config() -> Dict[str, Any]:
    """
    Hole die Feature-Konfiguration für ML-Modelle
    """
    try:
        return {
            "feature_config": ml_model_service.feature_config,
            "total_features": sum(len(features) for features in ml_model_service.feature_config.values()),
            "config_timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting feature config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
