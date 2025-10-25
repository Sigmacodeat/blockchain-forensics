"""
Tests for ML Model Service
"""

import numpy as np
from datetime import datetime, timedelta
from app.services.ml_model_service import ml_model_service


def test_extract_features():
    """Test feature extraction from transaction data"""
    # Test transaction data
    transaction_data = {
        "value": 1000000000000000000,  # 1 ETH in wei
        "gas_used": 21000,
        "gas_price": 20000000000,
        "timestamp": "2023-01-01T12:00:00Z",
        "block_number": 12345678,
        "tx_index": 5,
        "value_usd": 2000.0,
        "address_features": {
            "balance": 5000000000000000000,  # 5 ETH
            "tx_count": 150,
            "first_seen": "2022-06-01T00:00:00Z",
            "last_seen": "2023-01-01T11:00:00Z",
            "avg_tx_value": 800000000000000000,  # 0.8 ETH
            "max_tx_value": 2000000000000000000,  # 2 ETH
            "min_tx_value": 100000000000000000   # 0.1 ETH
        },
        "temporal_features": {
            "hour_of_day": 12,
            "day_of_week": 1,  # Monday
            "is_weekend": False,
            "time_since_last_tx": 3600,  # 1 hour
            "tx_frequency_1h": 0.5,
            "tx_frequency_24h": 6.2
        }
    }

    features = ml_model_service.extract_features(transaction_data)

    # Should return a 2D array
    assert features.ndim == 2
    assert features.shape[0] == 1  # One sample

    # Should have expected number of features
    expected_features = (
        len(ml_model_service.feature_config["transaction_features"]) +
        len(ml_model_service.feature_config["address_features"]) +
        len(ml_model_service.feature_config["temporal_features"])
    )

    assert features.shape[1] == expected_features

    # Check some specific values
    assert features[0, 0] == 1000000000000000000  # value
    assert features[0, 1] == 21000  # gas_used
    assert features[0, 2] == 20000000000  # gas_price


def test_anomaly_detection_training():
    """Test training an anomaly detection model"""
    # Generate synthetic training data
    training_data = []
    for i in range(50):
        # Normal transactions
        if i < 45:
            sample = {
                "value": np.random.uniform(100000000000000000, 1000000000000000000),  # 0.1-1 ETH
                "gas_used": np.random.uniform(21000, 50000),
                "gas_price": np.random.uniform(10000000000, 50000000000),
                "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "block_number": 12345678 + i,
                "tx_index": i % 10,
                "value_usd": np.random.uniform(200, 2000),
                "address_features": {
                    "balance": np.random.uniform(1000000000000000000, 10000000000000000000),
                    "tx_count": np.random.randint(10, 1000),
                    "first_seen": (datetime.utcnow() - timedelta(days=365)).isoformat(),
                    "last_seen": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "avg_tx_value": np.random.uniform(500000000000000000, 2000000000000000000),
                    "max_tx_value": np.random.uniform(1000000000000000000, 5000000000000000000),
                    "min_tx_value": np.random.uniform(100000000000000000, 1000000000000000000)
                },
                "temporal_features": {
                    "hour_of_day": np.random.randint(0, 24),
                    "day_of_week": np.random.randint(0, 7),
                    "is_weekend": np.random.choice([True, False]),
                    "time_since_last_tx": np.random.uniform(60, 3600),
                    "tx_frequency_1h": np.random.uniform(0.1, 5.0),
                    "tx_frequency_24h": np.random.uniform(1, 20)
                }
            }
        else:
            # Anomalous transactions (larger values, unusual patterns)
            sample = {
                "value": np.random.uniform(10000000000000000000, 100000000000000000000),  # 10-100 ETH
                "gas_used": np.random.uniform(100000, 1000000),
                "gas_price": np.random.uniform(100000000000, 1000000000000),
                "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "block_number": 12345678 + i,
                "tx_index": i % 10,
                "value_usd": np.random.uniform(20000, 200000),
                "address_features": {
                    "balance": np.random.uniform(100000000000000000000, 1000000000000000000000),
                    "tx_count": np.random.randint(1, 10),  # Very few transactions
                    "first_seen": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "last_seen": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "avg_tx_value": np.random.uniform(5000000000000000000, 50000000000000000000),
                    "max_tx_value": np.random.uniform(10000000000000000000, 100000000000000000000),
                    "min_tx_value": np.random.uniform(1000000000000000000, 10000000000000000000)
                },
                "temporal_features": {
                    "hour_of_day": np.random.randint(0, 24),
                    "day_of_week": np.random.randint(0, 7),
                    "is_weekend": np.random.choice([True, False]),
                    "time_since_last_tx": np.random.uniform(86400, 604800),  # 1-7 days
                    "tx_frequency_1h": np.random.uniform(0.01, 0.1),  # Very low frequency
                    "tx_frequency_24h": np.random.uniform(0.1, 1.0)
                },
                "anomaly_indicators": ["unusual_value", "new_address", "high_frequency_change"]
            }

        training_data.append(sample)

    # Train model
    result = ml_model_service.train_anomaly_detection_model(
        training_data=training_data,
        model_id="test_isolation_forest",
        contamination=0.1
    )

    # Verify training result
    assert result["status"] == "trained"
    assert result["model_id"] == "test_isolation_forest"
    assert "performance" in result
    assert result["performance"]["training_samples"] == 50
    assert result["performance"]["anomalies_detected"] >= 0

    # Check that model is cached
    assert "test_isolation_forest" in ml_model_service.models


def test_anomaly_prediction():
    """Test anomaly prediction with trained model"""
    # First train a model
    training_data = [
        {
            "value": 1000000000000000000,
            "gas_used": 21000,
            "gas_price": 20000000000,
            "timestamp": datetime.utcnow().isoformat(),
            "block_number": 12345678,
            "tx_index": 1,
            "value_usd": 2000.0
        }
    ]

    ml_model_service.train_anomaly_detection_model(
        training_data=training_data,
        model_id="test_prediction_model",
        contamination=0.1
    )

    # Test prediction with normal transaction
    normal_transaction = {
        "value": 1000000000000000000,
        "gas_used": 21000,
        "gas_price": 20000000000,
        "timestamp": datetime.utcnow().isoformat(),
        "block_number": 12345679,
        "tx_index": 2,
        "value_usd": 2000.0,
        "address_features": {
            "balance": 5000000000000000000,
            "tx_count": 150,
            "first_seen": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "avg_tx_value": 800000000000000000,
            "max_tx_value": 2000000000000000000,
            "min_tx_value": 100000000000000000
        },
        "temporal_features": {
            "hour_of_day": 14,
            "day_of_week": 2,
            "is_weekend": False,
            "time_since_last_tx": 1800,
            "tx_frequency_1h": 0.8,
            "tx_frequency_24h": 12.5
        }
    }

    result = ml_model_service.predict_anomaly(
        transaction_data=normal_transaction,
        model_id="test_prediction_model"
    )

    assert "model_id" in result
    assert "is_anomaly" in result
    assert "anomaly_score" in result
    assert "confidence" in result
    assert result["model_id"] == "test_prediction_model"
    assert isinstance(result["anomaly_score"], float)
    assert 0.0 <= result["anomaly_score"] <= 1.0


def test_model_listing():
    """Test listing available models"""
    # Train a test model first
    training_data = [{"value": 1000, "gas_used": 21000}]
    ml_model_service.train_anomaly_detection_model(training_data, "test_list_model")

    models = ml_model_service.list_models()

    # Should include our test model
    model_ids = [m["model_id"] for m in models]
    assert "test_list_model" in model_ids

    # Each model should have expected fields
    test_model = next(m for m in models if m["model_id"] == "test_list_model")
    assert "training_timestamp" in test_model
    assert "training_samples" in test_model


def test_model_deletion():
    """Test model deletion"""
    # Train a test model
    training_data = [{"value": 1000, "gas_used": 21000}]
    ml_model_service.train_anomaly_detection_model(training_data, "test_delete_model")

    # Verify it exists
    models_before = ml_model_service.list_models()
    assert any(m["model_id"] == "test_delete_model" for m in models_before)

    # Delete it
    success = ml_model_service.delete_model("test_delete_model")
    assert success

    # Verify it's gone
    models_after = ml_model_service.list_models()
    assert not any(m["model_id"] == "test_delete_model" for m in models_after)


def test_model_validation():
    """Test model validation with synthetic data"""
    # Train a model first
    training_data = []
    for i in range(30):
        sample = {
            "value": 1000000000000000000 if i < 25 else 10000000000000000000,  # Normal vs anomalous
            "gas_used": 21000,
            "gas_price": 20000000000,
            "timestamp": datetime.utcnow().isoformat(),
            "is_anomaly": i >= 25  # Last 5 are anomalies
        }
        training_data.append(sample)

    ml_model_service.train_anomaly_detection_model(training_data, "test_validation_model")

    # Create validation data
    validation_data = [
        {"value": 1000000000000000000, "gas_used": 21000, "is_anomaly": False},  # Normal
        {"value": 1000000000000000000, "gas_used": 21000, "is_anomaly": False},  # Normal
        {"value": 10000000000000000000, "gas_used": 21000, "is_anomaly": True},  # Anomalous
        {"value": 10000000000000000000, "gas_used": 21000, "is_anomaly": True},  # Anomalous
    ]

    result = ml_model_service.validate_model_performance("test_validation_model", validation_data)

    # Should have validation results
    assert "model_id" in result
    assert "validation_samples" in result
    assert "accuracy" in result
    assert "f1_score" in result
    assert result["validation_samples"] == 4


def test_training_data_generation():
    """Test generating training data from events"""
    # Create mock events
    events = []
    for i in range(20):
        event = {
            "address": f"0xaddr{i}",
            "tx_hash": f"0xhash{i}",
            "value": 1000000000000000000,
            "gas_used": 21000,
            "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat()
        }
        events.append(event)

    training_data = ml_model_service.generate_training_data_from_events(events, lookback_days=7)

    # Should generate training samples
    assert len(training_data) > 0

    # Each sample should have required fields
    sample = training_data[0]
    assert "features" in sample
    assert "timestamp" in sample
    assert "address" in sample
    assert "tx_hash" in sample
    assert isinstance(sample["features"], list)


def test_feature_config():
    """Test feature configuration"""
    config = ml_model_service.feature_config

    # Should have expected feature categories
    assert "transaction_features" in config
    assert "address_features" in config
    assert "temporal_features" in config

    # Should have reasonable number of features
    total_features = sum(len(features) for features in config.values())
    assert total_features > 0

    # Transaction features should include expected fields
    tx_features = config["transaction_features"]
    assert "value" in tx_features
    assert "gas_used" in tx_features
    assert "timestamp" in tx_features
