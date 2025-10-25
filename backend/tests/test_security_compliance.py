"""
Tests for Security & Compliance Services
"""

import pytest
import json
from datetime import datetime, timedelta
from app.services.security_compliance import (
    digital_signature_service, audit_trail_service,
    compliance_service, security_service
)


def test_digital_signature_creation():
    """Test digital signature creation and verification"""
    test_data = {
        "case_id": "test_case_123",
        "evidence_id": "evidence_456",
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": "user_789"
    }

    # Sign data
    signature = digital_signature_service.sign_data(test_data)

    # Verify signature
    is_valid = digital_signature_service.verify_signature(test_data, signature)

    assert is_valid
    assert isinstance(signature, str)
    assert len(signature) > 0


def test_signature_tampering_detection():
    """Test that signature verification detects tampering"""
    test_data = {
        "case_id": "test_case_123",
        "evidence_id": "evidence_456"
    }

    # Sign original data
    signature = digital_signature_service.sign_data(test_data)

    # Tamper with data
    tampered_data = test_data.copy()
    tampered_data["evidence_id"] = "tampered_evidence_456"

    # Verification should fail
    is_valid = digital_signature_service.verify_signature(tampered_data, signature)
    assert not is_valid


def test_audit_trail_logging():
    """Test audit trail logging functionality"""
    # Log a case action
    audit_trail_service.log_case_action(
        case_id="test_case_123",
        action="created",
        user_id="test_user_456",
        details={"priority": "high"},
        ip_address="192.168.1.100"
    )

    # Check that entry was logged
    entries = audit_trail_service.get_audit_trail(limit=10)
    case_entries = [e for e in entries if e["resource_id"] == "test_case_123"]

    assert len(case_entries) >= 1
    entry = case_entries[0]
    assert entry["action"] == "case_created"
    assert entry["user_id"] == "test_user_456"
    assert entry["resource_type"] == "case"


def test_audit_trail_filtering():
    """Test audit trail filtering"""
    # Clear audit log to avoid interference from other tests
    audit_trail_service.audit_log = []
    
    # Log multiple entries
    for i in range(5):
        audit_trail_service.log_action(
            action=f"test_action_{i}",
            user_id="test_user",
            resource_type="test_resource",
            resource_id=f"test_id_{i}"
        )

    # Test filtering by user
    user_entries = audit_trail_service.get_audit_trail(user_id="test_user", limit=10)
    assert len(user_entries) == 5
    assert all(e["user_id"] == "test_user" for e in user_entries)

    # Test filtering by action
    action_entries = audit_trail_service.get_audit_trail(action_filter="test_action_1", limit=10)
    assert len(action_entries) == 1
    assert action_entries[0]["action"] == "test_action_1"


def test_audit_trail_integrity_verification():
    """Test audit trail integrity verification"""
    # Log some entries
    for i in range(3):
        audit_trail_service.log_action(f"test_action_{i}", resource_type="test")

    # Verify integrity
    integrity = audit_trail_service.verify_audit_integrity()

    assert "total_entries_checked" in integrity
    assert "verified_entries" in integrity
    assert "tampered_entries" in integrity
    assert integrity["tampered_entries"] == 0  # Should be no tampering


def test_compliance_anonymization():
    """Test GDPR data anonymization"""
    user_data = {
        "user_id": "user_123",
        "email": "user@example.com",
        "phone": "+1234567890",
        "name": "John Doe",
        "address": "123 Main St",
        "case_count": 5,
        "last_login": datetime.utcnow().isoformat()
    }

    anonymized = compliance_service.anonymize_data(user_data, "user_profiles")

    # PII fields should be anonymized
    assert anonymized["email"] != user_data["email"]
    assert anonymized["phone"] != user_data["phone"]
    assert anonymized["name"] != user_data["name"]
    assert anonymized["address"] != user_data["address"]

    # Non-PII fields should remain unchanged
    assert anonymized["case_count"] == user_data["case_count"]
    assert anonymized["last_login"] == user_data["last_login"]


def test_compliance_retention_check():
    """Test data retention compliance checking"""
    retention_status = compliance_service.check_data_retention()

    assert "generated_at" in retention_status
    assert "retention_violations" in retention_status
    assert "compliance_status" in retention_status
    assert isinstance(retention_status["retention_violations"], dict)


def test_compliance_report_generation():
    """Test comprehensive compliance report generation"""
    report = compliance_service.generate_compliance_report()

    assert "generated_at" in report
    assert "data_retention_periods" in report
    assert "pii_handling" in report
    assert "gdpr_compliance" in report
    assert "audit_trail_integrity" in report
    assert "certifications" in report

    # Check GDPR compliance structure
    gdpr = report["gdpr_compliance"]
    assert "right_to_erasure" in gdpr
    assert "data_portability" in gdpr
    assert "consent_management" in gdpr


def test_security_rate_limiting():
    """Test security rate limiting functionality"""
    identifier = "test_user_123"
    action = "login"

    # Should allow first few attempts
    for i in range(3):
        allowed = security_service.check_rate_limiting(identifier, action)
        assert allowed

    # Record some failed attempts
    for i in range(3):
        security_service.record_failed_attempt(
            identifier,
            "192.168.1.100",
            "test-user-agent"
        )

    # Should now be rate limited
    allowed = security_service.check_rate_limiting(identifier, action)
    assert not allowed


def test_security_suspicious_activity_detection():
    """Test suspicious activity detection"""
    # Test rapid requests
    request_data = {
        "ip_address": "192.168.1.100",
        "path": "/api/v1/cases",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Add some rapid requests to trigger detection
    for i in range(15):
        security_service.detect_suspicious_activity({
            "ip_address": "192.168.1.100",
            "timestamp": (datetime.utcnow() - timedelta(seconds=i)).isoformat()
        })

    # Should detect rapid requests
    indicators = security_service.detect_suspicious_activity(request_data)
    assert "rapid_requests" in indicators


def test_security_privilege_escalation_detection():
    """Test privilege escalation detection"""
    # Analyst trying to access admin endpoints
    request_data = {
        "user_role": "analyst",
        "path": "/admin/users",
        "resource_type": "admin_panel"
    }

    indicators = security_service.detect_suspicious_activity(request_data)
    assert "privilege_escalation" in indicators


def test_security_report_generation():
    """Test security report generation"""
    report = security_service.generate_security_report()

    assert "generated_at" in report
    assert "failed_login_attempts" in report
    assert "suspicious_activities" in report
    assert "rate_limited_ips" in report
    assert "security_incidents" in report
    assert "compliance_status" in report


def test_audit_trail_export():
    """Test audit trail export functionality"""
    # Log some test entries
    for i in range(3):
        audit_trail_service.log_action(
            action=f"export_test_{i}",
            resource_type="test",
            details={"test": True}
        )

    # Test JSON export
    json_export = audit_trail_service.export_audit_trail(format="json")
    assert isinstance(json_export, str)

    exported_data = json.loads(json_export)
    assert "entries" in exported_data
    assert "total_entries" in exported_data
    assert exported_data["total_entries"] >= 3

    # Test CSV export
    csv_export = audit_trail_service.export_audit_trail(format="csv")
    assert isinstance(csv_export, str)
    assert "timestamp" in csv_export
    assert "action" in csv_export


def test_compliance_data_deletion_scheduling():
    """Test data deletion scheduling for compliance"""
    data_ids = ["user_123", "user_456", "case_789"]

    schedule = compliance_service.schedule_data_deletion("user_data", data_ids)

    assert schedule["data_type"] == "user_data"
    assert schedule["data_ids"] == data_ids
    assert "scheduled_deletion" in schedule
    assert "reason" in schedule
    assert schedule["reason"] == "compliance_retention_policy"
