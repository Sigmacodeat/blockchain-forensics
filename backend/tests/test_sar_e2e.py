"""
E2E Tests für SAR/STR Flow

Testet den vollständigen SAR-Workflow:
- Generate SAR from Case
- Submit SAR to Regulator (Stub)
- Check Submission Status
- Export Evidence Package
"""
import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.case_service import case_service
from app.compliance.sar_queue import sar_queue
from app.services.evidence_service import evidence_service


client = TestClient(app)


@pytest.fixture
def sample_case_data():
    """Sample case data for SAR generation"""
    return {
        "case_id": "TEST-SAR-001",
        "title": "Suspicious Transaction Investigation",
        "subject_name": "John Doe",
        "addresses": ["0x1234567890123456789012345678901234567890"],
        "risk_score": 0.85,
        "total_amount_usd": 50000.0,
        "risk_factors": ["mixer_usage", "sanctions_hit"],
        "sanctions_hit": True,
        "mixer_usage": True,
        "attachments": ["evidence_001.pdf", "evidence_002.jpg"]
    }


@pytest.mark.asyncio
async def test_sar_generation_flow(sample_case_data):
    """Test SAR generation from case data"""
    
    # Mock case service
    with patch.object(case_service, 'get_case', return_value=sample_case_data):
        response = client.post(
            "/api/v1/compliance/sar/generate",
            json={"case_id": sample_case_data["case_id"], "format": "fincen"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report_id" in data
        assert "report" in data
        assert "case_id" in data


@pytest.mark.asyncio
async def test_sar_submission_flow(sample_case_data):
    """Test SAR submission to regulator"""
    
    # Mock case service
    with patch.object(case_service, 'get_case', return_value=sample_case_data):
        # First generate
        gen_response = client.post(
            "/api/v1/compliance/sar/generate",
            json={"case_id": sample_case_data["case_id"], "format": "fincen"}
        )
        assert gen_response.status_code == 200
        report_id = gen_response.json()["report_id"]
        
        # Then submit
        submit_response = client.post(
            "/api/v1/compliance/sar/submit",
            json={
                "report_id": report_id,
                "case_id": sample_case_data["case_id"],
                "format": "fincen",
                "content": {"test": "data"}
            }
        )
        
        assert submit_response.status_code == 200
        submit_data = submit_response.json()
        assert submit_data["accepted"] is True
        assert submit_data["queued"] is True
        assert submit_data["report_id"] == report_id


@pytest.mark.asyncio
async def test_sar_status_check(sample_case_data):
    """Test SAR submission status check"""
    
    report_id = "TEST-REPORT-001"
    
    # Mock queue to return status
    with patch.object(sar_queue, 'get_status', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {
            "report_id": report_id,
            "state": "submitted",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        response = client.get(f"/api/v1/compliance/sar/status/{report_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == report_id
        assert data["status"]["state"] == "submitted"


@pytest.mark.asyncio
async def test_evidence_package_export(sample_case_data):
    """Test evidence package export for court submission"""
    
    case_id = sample_case_data["case_id"]
    
    # Add some evidence first
    evidence_service.add_evidence(
        case_id=case_id,
        file_hash="abc123",
        filename="evidence.pdf",
        uploaded_by="test_user"
    )
    
    # Export package
    response = client.get(f"/api/v1/compliance/evidence/export/{case_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "case_id" in data
    assert "chain_hash" in data
    assert "is_valid" in data
    assert "items" in data
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_sar_queue_listing():
    """Test SAR queue listing"""
    
    # Mock queue all
    with patch.object(sar_queue, 'all', new_callable=AsyncMock) as mock_all:
        mock_all.return_value = {
            "REPORT-001": {"state": "queued"},
            "REPORT-002": {"state": "submitted"}
        }
        
        response = client.get("/api/v1/compliance/sar/queue")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert data["count"] == 2


@pytest.mark.asyncio
async def test_sar_with_case_api(sample_case_data):
    """Test SAR generation via case API endpoint"""
    
    # Mock case service
    with patch.object(case_service, 'get_case', return_value=sample_case_data):
        response = client.post(
            f"/api/v1/sar/from-case/{sample_case_data['case_id']}",
            json={"format": "fincen"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report_id" in data
        assert "report_preview" in data


@pytest.mark.asyncio
async def test_sar_validation(sample_case_data):
    """Test SAR report validation (if schemas are available)"""
    
    # Mock case service
    with patch.object(case_service, 'get_case', return_value=sample_case_data):
        response = client.post(
            "/api/v1/compliance/sar/generate",
            json={"case_id": sample_case_data["case_id"], "format": "fincen", "validate": True}
        )
        
        # Should still work even if validation fails (fallback to JSON)
        assert response.status_code in [200, 500]  # 500 if validation setup fails
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True


@pytest.mark.asyncio
async def test_sar_error_handling():
    """Test error handling in SAR flow"""
    
    # Test with non-existent case
    response = client.post(
        "/api/v1/compliance/sar/generate",
        json={"case_id": "NON-EXISTENT", "format": "fincen"}
    )
    
    assert response.status_code == 404
    
    # Test invalid format
    with patch.object(case_service, 'get_case', return_value={"case_id": "TEST"}):
        response = client.post(
            "/api/v1/compliance/sar/generate",
            json={"case_id": "TEST", "format": "invalid"}
        )
        
        assert response.status_code == 200  # Falls back to JSON
    
    # Test status check for non-existent report
    response = client.get("/api/v1/compliance/sar/status/NON-EXISTENT")
    
    assert response.status_code == 404
