import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Postgres not available in default test env")
def test_cases_crud_and_export(tmp_path):
    # Create case
    payload = {"title": "Testfall A", "priority": "medium", "tags": ["demo", "unit"]}
    r = client.post("/api/v1/cases", json=payload)
    assert r.status_code == 201, r.text
    case = r.json()
    case_id = case["id"]

    # List
    r = client.get("/api/v1/cases")
    assert r.status_code == 200
    assert any(c["id"] == case_id for c in r.json())

    # Get single
    r = client.get(f"/api/v1/cases/{case_id}")
    assert r.status_code == 200

    # Add note item
    r = client.post(f"/api/v1/cases/{case_id}/items", json={
        "item_type": "note",
        "content": "Notiz 1"
    })
    assert r.status_code == 201, r.text

    # Export
    r = client.post(f"/api/v1/cases/{case_id}/export")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("path")


def test_create_case():
    """Test creating a new case"""
    payload = {
        "title": "Test Investigation Case",
        "description": "Testing case creation functionality",
        "priority": "high",
        "tags": ["test", "investigation"],
        "category": "financial_crime"
    }

    response = client.post("/api/v1/cases", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Test Investigation Case"
    assert data["description"] == "Testing case creation functionality"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert "test" in data["tags"]
    assert data["category"] == "financial_crime"
    assert "id" in data
    assert "created_at" in data


def test_list_cases():
    """Test listing cases"""
    response = client.get("/api/v1/cases")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    # Should have at least the case we just created
    assert len(data) >= 1


def test_get_case():
    """Test getting a specific case"""
    # First create a case to get its ID
    payload = {
        "title": "Test Case for Get",
        "description": "Testing case retrieval"
    }

    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Now get the case
    response = client.get(f"/api/v1/cases/{case_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == case_id
    assert data["title"] == "Test Case for Get"


def test_update_case():
    """Test updating a case"""
    # Create a case first
    payload = {
        "title": "Original Title",
        "description": "Original description"
    }

    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Update the case
    update_payload = {
        "title": "Updated Title",
        "description": "Updated description",
        "priority": "critical"
    }

    response = client.put(f"/api/v1/cases/{case_id}", json=update_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert data["priority"] == "critical"


def test_update_case_status():
    """Test updating case status"""
    # Create a case first
    payload = {"title": "Status Test Case", "description": "Testing status updates"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Update status
    response = client.post(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "investigating"},
        params={"note": "Starting investigation"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "updated"
    assert data["new_status"] == "investigating"


def test_add_evidence():
    """Test adding evidence to a case"""
    # Create a case first
    payload = {"title": "Evidence Test Case", "description": "Testing evidence addition"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Add evidence
    evidence_payload = {
        "name": "Suspicious Transaction",
        "description": "Large transfer from sanctioned address",
        "evidence_type": "transaction",
        "source_url": "https://etherscan.io/tx/0x123",
        "collection_method": "blockchain_analysis",
        "metadata": {"amount": "1000000", "currency": "ETH"}
    }

    response = client.post(f"/api/v1/cases/{case_id}/evidence", json=evidence_payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Suspicious Transaction"
    assert data["evidence_type"] == "transaction"
    assert data["case_id"] == case_id
    assert "id" in data


def test_list_case_evidence():
    """Test listing evidence for a case"""
    # Create a case and add evidence first
    payload = {"title": "Evidence List Test", "description": "Testing evidence listing"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Add evidence
    evidence_payload = {
        "name": "Test Evidence",
        "description": "Test evidence for listing",
        "evidence_type": "document"
    }
    client.post(f"/api/v1/cases/{case_id}/evidence", json=evidence_payload)

    # List evidence
    response = client.get(f"/api/v1/cases/{case_id}/evidence")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Test Evidence"


def test_verify_evidence():
    """Test verifying evidence"""
    # Create case and evidence first
    payload = {"title": "Verification Test", "description": "Testing evidence verification"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    evidence_payload = {
        "name": "Evidence to Verify",
        "description": "This evidence needs verification",
        "evidence_type": "analysis"
    }
    evidence_response = client.post(f"/api/v1/cases/{case_id}/evidence", json=evidence_payload)
    evidence_id = evidence_response.json()["id"]

    # Verify evidence
    response = client.put(f"/api/v1/evidence/{evidence_id}/verify", json={"verified_by": "investigator_jane"})
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "verified"
    assert "verified_at" in data


def test_get_case_activities():
    """Test getting case activities"""
    # Create a case first
    payload = {"title": "Activity Test Case", "description": "Testing activity logging"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Get activities
    response = client.get(f"/api/v1/cases/{case_id}/activities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    # Should have at least the case creation activity
    assert len(data) >= 1
    assert data[0]["activity_type"] == "case_created"


def test_case_stats():
    """Test getting case statistics"""
    response = client.get("/api/v1/cases/stats")
    assert response.status_code == 200

    data = response.json()
    assert "total_cases" in data
    assert "by_status" in data
    assert "by_priority" in data
    assert "total_evidence" in data
    assert "verified_evidence" in data
    assert "evidence_verification_rate" in data


def test_case_filtering():
    """Test filtering cases by various criteria"""
    # Create cases with different priorities and statuses
    cases_data = [
        {"title": "High Priority Case", "description": "High priority", "priority": "high"},
        {"title": "Medium Priority Case", "description": "Medium priority", "priority": "medium"},
        {"title": "Closed Case", "description": "Closed case", "status": "closed"}
    ]

    case_ids = []
    for case_data in cases_data:
        response = client.post("/api/v1/cases", json=case_data)
        case_ids.append(response.json()["id"])

    # Test filtering by priority
    response = client.get("/api/v1/cases?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(case["priority"] == "high" for case in data)

    # Test filtering by status
    response = client.get("/api/v1/cases?status=closed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(case["status"] == "closed" for case in data)


def test_case_not_found():
    """Test handling of non-existent case"""
    fake_id = "case_99999999999999999999999999999999"

    response = client.get(f"/api/v1/cases/{fake_id}")
    assert response.status_code == 404

    response = client.get(f"/api/v1/cases/{fake_id}/evidence")
    assert response.status_code == 404

def test_generate_case_report():
    """Test generating a case report"""
    # Create a case first
    payload = {"title": "Report Test Case", "description": "Testing report generation"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Add some evidence
    evidence_payload = {
        "name": "Test Evidence for Report",
        "description": "Evidence for report testing",
        "evidence_type": "document",
        "collection_method": "manual"
    }
    client.post(f"/api/v1/cases/{case_id}/evidence", json=evidence_payload)

    # Generate report
    response = client.post(f"/api/v1/cases/{case_id}/report")
    assert response.status_code == 200

    data = response.json()
    assert data["case_id"] == case_id
    assert "report" in data
    assert "generated_at" in data

    # Parse the report JSON to verify structure
    import json
    report = json.loads(data["report"])
    assert report["case_id"] == case_id
    assert "evidence" in report
    assert "activities" in report


def test_export_case():
    """Test exporting a case as ZIP"""
    # Create a case first
    payload = {"title": "Export Test Case", "description": "Testing case export"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Add evidence and activities
    evidence_payload = {
        "name": "Export Test Evidence",
        "description": "Evidence for export testing",
        "evidence_type": "analysis"
    }
    client.post(f"/api/v1/cases/{case_id}/evidence", json=evidence_payload)

    # Export case
    response = client.post(f"/api/v1/cases/{case_id}/export")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "path" in data


def test_download_case_export():
    """Test downloading a case export"""
    # Create a case first
    payload = {"title": "Download Test Case", "description": "Testing export download"}
    create_response = client.post("/api/v1/cases", json=payload)
    case_id = create_response.json()["id"]

    # Export first (this creates the file)
    export_response = client.post(f"/api/v1/cases/{case_id}/export")
    assert export_response.status_code == 200

    # Download the export
    response = client.get(f"/api/v1/cases/{case_id}/export/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers.get("content-disposition", "")


def test_export_nonexistent_case():
    """Test exporting a non-existent case"""
    fake_id = "case_99999999999999999999999999999999"

    response = client.post(f"/api/v1/cases/{fake_id}/export")
    assert response.status_code == 404


def test_evidence_hash_generation():
    """Test evidence hash generation and verification"""
    from app.models.case import generate_evidence_hash, verify_evidence_integrity

    # Test data
    test_data = b"test evidence data for hashing"

    # Generate hash
    hash_value = generate_evidence_hash(test_data)
    assert hash_value is not None
    assert len(hash_value) == 64  # SHA-256 produces 64 character hex string

    # Verify hash
    is_valid = verify_evidence_integrity("test_evidence_id", hash_value)
    assert is_valid is False  # No evidence with that ID exists

    # Test with wrong hash
    wrong_hash = "a" * 64
    is_valid = verify_evidence_integrity("test_evidence_id", wrong_hash)
    assert is_valid is False
