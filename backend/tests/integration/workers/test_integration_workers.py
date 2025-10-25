"""
Integration Tests für Kafka Workers

Testet das Zusammenspiel von:
- Trace Consumer
- Enrichment Consumer
- Alert Consumer
- Message Flow
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestWorkerIntegration:
    """Integration Tests für Worker Pipeline"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_trace_consumer_flow(self):
        """Test kompletter Trace Consumer Workflow"""
        from app.workers.trace_consumer import TraceConsumerWorker
        
        worker = TraceConsumerWorker(group_id="test-trace-consumer")
        
        # Mock trace request
        trace_request = {
            "trace_id": "test-trace-123",
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "direction": "forward",
            "max_depth": 3,
            "taint_model": "proportional"
        }
        
        # Process request
        with patch.object(worker.tracer, 'trace') as mock_trace:
            mock_trace.return_value = AsyncMock()
            mock_trace.return_value.model_dump.return_value = {
                "source_address": trace_request["address"],
                "nodes": [],
                "edges": []
            }
            
            result = await worker._process_trace_request(trace_request)
            
            assert result is not None
            assert result["trace_id"] == "test-trace-123"
    
    @pytest.mark.asyncio
    async def test_enrichment_consumer_flow(self):
        """Test Enrichment Consumer Workflow"""
        from app.workers.enrichment_consumer import EnrichmentConsumerWorker
        
        worker = EnrichmentConsumerWorker(group_id="test-enrichment-consumer")
        
        # Test address enrichment
        enrichment = await worker._enrich_address(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "ethereum"
        )
        
        assert "address" in enrichment
        assert "labels" in enrichment
        assert "risk_score" in enrichment
    
    @pytest.mark.asyncio
    async def test_alert_consumer_flow(self):
        """Test Alert Consumer Workflow"""
        from app.workers.alert_consumer import AlertConsumerWorker
        
        worker = AlertConsumerWorker(group_id="test-alert-consumer")
        
        # Mock alert
        alert = {
            "alert_type": "high_risk_transaction",
            "severity": "HIGH",
            "address": "0x123abc",
            "chain": "ethereum",
            "risk_score": 85,
            "reason": "Test alert"
        }
        
        # Process alert (mock DB/Email)
        with patch.object(worker, '_save_alert_to_db') as mock_save:
            with patch.object(worker, '_send_email_notification') as mock_email:
                with patch.object(worker, '_broadcast_websocket') as mock_ws:
                    success = await worker._process_alert(alert)
                    
                    assert success
                    mock_save.assert_called_once()
                    mock_ws.assert_called_once()
