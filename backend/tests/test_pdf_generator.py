"""
Tests für PDF Report Generator
"""
import pytest
from app.reports.pdf_generator import PDFReportGenerator


class TestPDFReportGenerator:
    """Tests für PDF Generator"""
    
    @pytest.fixture
    def generator(self):
        return PDFReportGenerator()
    
    @pytest.fixture
    def sample_trace_data(self):
        return {
            "source_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "direction": "forward",
            "taint_model": "proportional",
            "max_depth": 5,
            "nodes": [
                {
                    "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                    "taint_received": 1.0,
                    "risk_level": "MEDIUM",
                    "labels": ["Exchange"]
                },
                {
                    "address": "0x123abc456def",
                    "taint_received": 0.85,
                    "risk_level": "HIGH",
                    "labels": ["Mixer"]
                }
            ],
            "edges": [
                {
                    "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                    "to": "0x123abc456def",
                    "value": 10.5,
                    "taint": 0.85,
                    "tx_hash": "0xabc123"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_generate_trace_report(self, generator, sample_trace_data):
        """Test PDF report generation"""
        trace_id = "test-trace-123"
        
        pdf_bytes, manifest = await generator.generate_trace_report(
            trace_id=trace_id,
            trace_data=sample_trace_data
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert isinstance(manifest, dict)
        assert manifest['report_id'] == trace_id
        assert 'content_hash' in manifest
        
        # Check for PDF header or text content
        if pdf_bytes.startswith(b'%PDF'):
            # ReportLab PDF generated
            assert b'%PDF' in pdf_bytes
        else:
            # Text fallback
            assert b'BLOCKCHAIN FORENSIC' in pdf_bytes
    
    @pytest.mark.asyncio
    async def test_report_with_findings(self, generator, sample_trace_data):
        """Test report with additional findings"""
        trace_id = "test-trace-findings"
        findings = {
            "summary": "High-risk activity detected",
            "recommendations": ["Further investigation recommended"]
        }
        
        pdf_bytes, manifest = await generator.generate_trace_report(
            trace_id=trace_id,
            trace_data=sample_trace_data,
            findings=findings
        )
        
        assert len(pdf_bytes) > 0
        assert isinstance(manifest, dict)
        assert manifest['report_id'] == trace_id
    
    def test_text_report_fallback(self, generator, sample_trace_data):
        """Test text report generation"""
        trace_id = "test-trace-text"
        
        text_report = generator._generate_text_report(
            trace_id=trace_id,
            trace_data=sample_trace_data,
            findings=None
        )
        
        assert "BLOCKCHAIN FORENSIC" in text_report
        assert trace_id in text_report
        assert "0x742d35Cc" in text_report
