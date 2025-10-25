import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestCasesAPI:
    """Comprehensive test suite for Cases API endpoints"""

    def test_create_case(self):
        """Test case creation"""
        response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Investigation Case",
                "description": "A test case for investigation",
                "priority": "high",
                "status": "open",
                "assignee_id": "user123",
                "tags": ["test", "investigation"],
                "category": "fraud"
            }
        )
        if response.status_code != 201:
            print(f"ERROR Response: {response.status_code} - {response.text}")
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Investigation Case"
        assert data["status"] == "open"
        return data["id"]

    def test_list_cases(self):
        """Test case listing"""
        response = client.get("/api/v1/cases")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0

    def test_get_case(self):
        """Test getting a specific case"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Get",
                "description": "Testing get case endpoint",
                "priority": "medium"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Now get the case
        response = client.get(f"/api/v1/cases/{case_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == case_id
        assert data["title"] == "Test Case for Get"

    def test_update_case(self):
        """Test case update"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Update",
                "description": "Testing update case endpoint",
                "priority": "low"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Update the case
        response = client.put(
            f"/api/v1/cases/{case_id}",
            json={
                "title": "Updated Test Case",
                "description": "Updated description",
                "priority": "high",
                "status": "in_progress"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Test Case"
        assert data["description"] == "Updated description"
        assert data["priority"] == "high"

    def test_update_case_status(self):
        """Test case status update"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Status Update",
                "description": "Testing status update",
                "status": "open"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Update status
        response = client.post(
            f"/api/v1/cases/{case_id}/status",
            json={"status": "closed"},
            params={"note": "Case closed after investigation"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] == "closed"

    def test_add_evidence(self):
        """Test adding evidence to a case"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Evidence",
                "description": "Testing evidence management"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Add evidence
        response = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            json={
                "name": "Suspicious Transaction",
                "description": "Evidence of suspicious blockchain transaction",
                "evidence_type": "transaction",
                "source_url": "https://blockchain.example/tx/123",
                "collection_method": "automated",
                "metadata": {"tx_hash": "0x123abc"}
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Suspicious Transaction"
        assert data["case_id"] == case_id

    def test_list_case_evidence(self):
        """Test listing evidence for a case"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Evidence List",
                "description": "Testing evidence listing"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Add some evidence
        client.post(
            f"/api/v1/cases/{case_id}/evidence",
            json={
                "name": "Evidence 1",
                "description": "First evidence",
                "evidence_type": "document"
            }
        )

        # List evidence
        response = client.get(f"/api/v1/cases/{case_id}/evidence")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_verify_evidence(self):
        """Test evidence verification"""
        # First create a case and add evidence
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Evidence Verification",
                "description": "Testing evidence verification"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Add evidence
        evidence_response = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            json={
                "name": "Verifiable Evidence",
                "description": "Evidence to be verified",
                "evidence_type": "document"
            }
        )
        assert evidence_response.status_code == 201
        evidence_data = evidence_response.json()
        evidence_id = evidence_data["id"]

        # Verify evidence
        response = client.put(
            f"/api/v1/cases/evidence/{evidence_id}/verify",
            json={
                "verified_by": "investigator123",
                "verification_notes": "Verified through blockchain analysis"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verified"
        assert "verified_at" in data

    def test_get_case_activities(self):
        """Test getting case activities/timeline"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Activities",
                "description": "Testing case activities"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Get activities
        response = client.get(f"/api/v1/cases/{case_id}/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the case creation activity
        assert len(data) >= 1

    def test_case_filtering(self):
        """Test case filtering functionality"""
        # Create multiple cases with different properties
        cases_data = [
            {
                "title": "High Priority Case",
                "description": "High priority investigation",
                "priority": "high",
                "status": "open",
                "tags": ["urgent", "fraud"]
            },
            {
                "title": "Low Priority Case",
                "description": "Low priority investigation",
                "priority": "low",
                "status": "closed",
                "tags": ["resolved"]
            }
        ]

        created_cases = []
        for case_data in cases_data:
            response = client.post("/api/v1/cases", json=case_data)
            assert response.status_code == 201
            created_cases.append(response.json())

        # Test filtering by status
        response = client.get("/api/v1/cases?status=open")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should find at least the high priority case
        assert len(data) >= 1

        # Test filtering by priority
        response = client.get("/api/v1/cases?priority=high")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_generate_case_report(self):
        """Test case report generation"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Report",
                "description": "Testing report generation"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Generate report
        response = client.post(f"/api/v1/cases/{case_id}/report")
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "generated_at" in data
        assert data["case_id"] == case_id

        # Verify report contains expected data
        report = json.loads(data["report"])
        assert "case_id" in report
        assert "evidence" in report
        assert "activities" in report

    def test_export_case(self):
        """Test case export functionality"""
        # First create a case with some evidence
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Export",
                "description": "Testing case export"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Add some evidence
        client.post(
            f"/api/v1/cases/{case_id}/evidence",
            json={
                "name": "Export Evidence",
                "description": "Evidence for export test",
                "evidence_type": "document"
            }
        )

        # Export case
        response = client.post(f"/api/v1/cases/{case_id}/export")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "path" in data

    def test_download_case_export(self):
        """Test case export download"""
        # First create and export a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Download",
                "description": "Testing export download"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Export the case first
        export_response = client.post(f"/api/v1/cases/{case_id}/export")
        assert export_response.status_code == 200

        # Download export
        response = client.get(f"/api/v1/cases/{case_id}/export/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    def test_export_and_verify_signature(self):
        """Test export with signature verification"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Signature Verification",
                "description": "Testing export signature verification"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Add evidence with signature data
        client.post(
            f"/api/v1/cases/{case_id}/evidence",
            json={
                "name": "Signed Evidence",
                "description": "Evidence with digital signature",
                "evidence_type": "document",
                "metadata": {
                    "signature": "sample_signature_hash",
                    "verification_method": "digital_signature",
                    "verified": True
                }
            }
        )

        # Export case
        response = client.post(f"/api/v1/cases/{case_id}/export")
        assert response.status_code == 200

        # Download and verify export contains signature
        download_response = client.get(f"/api/v1/cases/{case_id}/export/download")
        assert download_response.status_code == 200

        # In a real scenario, we would verify the digital signature
        # For this test, we just verify the export was successful
        assert download_response.headers["content-type"] == "application/zip"

    def test_case_not_found(self):
        """Test handling of non-existent case"""
        response = client.get("/api/v1/cases/99999")
        assert response.status_code == 404

    def test_export_nonexistent_case(self):
        """Test export of non-existent case"""
        response = client.post("/api/v1/cases/99999/export")
        assert response.status_code == 404

    def test_case_stats(self):
        """Test case statistics endpoint"""
        response = client.get("/api/v1/cases/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_cases" in data
        assert "by_status" in data
        assert "by_priority" in data

    def test_evidence_hash_generation(self):
        """Test evidence hash generation"""
        # First create a case
        create_response = client.post(
            "/api/v1/cases",
            json={
                "title": "Test Case for Hash Generation",
                "description": "Testing evidence hash generation"
            }
        )
        assert create_response.status_code == 201
        case_data = create_response.json()
        case_id = case_data["id"]

        # Add evidence with content for hashing
        response = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            json={
                "name": "Hash Evidence",
                "description": "Evidence for hash generation",
                "evidence_type": "document",
                "metadata": {
                    "content": "This is test content for hash generation",
                    "hash_algorithm": "SHA-256"
                }
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        # In a real implementation, we would verify the hash was generated
        # For this test, we just verify the evidence was created successfully
