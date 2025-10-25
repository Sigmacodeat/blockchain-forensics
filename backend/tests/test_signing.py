"""
Tests für Signing und Manifest Service
"""

import pytest
from app.services.signing import (
    SigningProvider,
    DummySigningProvider,
    ManifestService,
    manifest_service,
    generate_report_hash_and_manifest
)


class TestSigningProvider:
    """Tests für Signing Provider"""

    def test_dummy_signing_provider(self):
        """Test Dummy Signing Provider"""
        provider = DummySigningProvider()

        test_data = b"test data"
        signature = provider.sign_data(test_data)

        assert signature.startswith("dummy_sig_")
        assert len(signature) > 10

        # Verification should always pass for dummy
        assert provider.verify_signature(test_data, signature)
        assert provider.verify_signature(b"different data", signature)


class TestManifestService:
    """Tests für Manifest Service"""

    @pytest.fixture
    def service(self):
        return ManifestService()

    def test_generate_manifest(self, service):
        """Test Manifest Generation"""
        manifest = service.generate_manifest(
            report_id="test-report-123",
            report_type="trace_report",
            content_hash="abc123",
            metadata={"key": "value"}
        )

        assert manifest["manifest_version"] == "1.0"
        assert manifest["report_id"] == "test-report-123"
        assert manifest["report_type"] == "trace_report"
        assert manifest["content_hash"] == "abc123"
        assert manifest["hash_algorithm"] == "SHA-256"
        assert manifest["platform"] == "Blockchain Forensics Platform v1.0.0"
        assert manifest["metadata"]["key"] == "value"
        assert "signature" in manifest
        assert "generated_at" in manifest

    def test_verify_manifest_valid(self, service):
        """Test Manifest Verification (Valid)"""
        manifest = service.generate_manifest(
            report_id="test-report-456",
            report_type="trace_report",
            content_hash="def456"
        )

        assert service.verify_manifest(manifest)

    def test_verify_manifest_invalid(self, service):
        """Test Manifest Verification (Invalid)"""
        manifest = service.generate_manifest(
            report_id="test-report-789",
            report_type="trace_report",
            content_hash="ghi789"
        )

        # Modify manifest to invalidate signature
        manifest["content_hash"] = "modified"

        assert not service.verify_manifest(manifest)

    def test_compute_content_hash(self, service):
        """Test Content Hash Computation"""
        test_content = b"test content for hashing"
        expected_hash = "2c26b46b68ffc68ff99b453c1d3043c3b8b2b4e8b8e9c8e9c8e9c8e9c8e9c8e9c"

        # Manually compute hash for comparison
        import hashlib
        actual_hash = hashlib.sha256(test_content).hexdigest()

        computed_hash = service.compute_content_hash(test_content)

        assert computed_hash == actual_hash


class TestGenerateReportHashAndManifest:
    """Tests für generate_report_hash_and_manifest Funktion"""

    def test_generate_report_hash_and_manifest(self):
        """Test Report Hash and Manifest Generation"""
        content = b"sample report content"
        content_hash, manifest = generate_report_hash_and_manifest(
            report_id="test-report-999",
            report_type="test_report",
            content=content,
            metadata={"test": True}
        )

        assert len(content_hash) == 64  # SHA-256 hex length
        assert manifest["report_id"] == "test-report-999"
        assert manifest["content_hash"] == content_hash
        assert manifest["metadata"]["test"] is True
        assert manifest_service.verify_manifest(manifest)


if __name__ == "__main__":
    pytest.main([__file__])
