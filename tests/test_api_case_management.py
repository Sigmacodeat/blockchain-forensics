import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_case_management_flow_json_and_csv_export():
    # Create case
    r = client.post(
        "/api/v1/forensics/cases/create",
        json={
            "case_id": "CASE-TEST-001",
            "title": "Test Case",
            "description": "Unit test case",
            "lead_investigator": "tester",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "case_created"
    assert data["case"]["case_id"] == "CASE-TEST-001"

    # Add entity
    r = client.post(
        "/api/v1/forensics/cases/CASE-TEST-001/entities/add",
        json={
            "address": "0x1111111111111111111111111111111111111111",
            "chain": "ethereum",
            "labels": {"role": "suspect"},
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "entity_added"
    assert data["case_id"] == "CASE-TEST-001"

    # Link evidence
    r = client.post(
        "/api/v1/forensics/cases/CASE-TEST-001/evidence/link",
        json={
            "resource_id": "tx_0xabc",
            "resource_type": "bridge_log",
            "record_hash": "deadbeef",
            "notes": "initial link",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "evidence_linked"
    assert data["case_id"] == "CASE-TEST-001"

    # Export JSON
    r = client.get("/api/v1/forensics/cases/CASE-TEST-001/export")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "export_ready"
    export = data["export"]
    assert export["case"]["case_id"] == "CASE-TEST-001"
    assert len(export["entities"]) >= 1
    assert len(export["evidence"]) >= 1

    # Export CSV
    r = client.get("/api/v1/forensics/cases/CASE-TEST-001/export.csv")
    assert r.status_code == 200, r.text
    csvs = r.json()
    assert csvs["status"] == "export_ready"
    assert csvs["format"] == "csv"
    assert "address,chain,labels" in csvs["entities_csv"]
    assert "resource_id,resource_type,record_hash,notes,timestamp" in csvs["evidence_csv"]
