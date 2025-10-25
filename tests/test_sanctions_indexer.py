import os
import sys
import pathlib
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.intel.sanctions import SanctionsIndexer, SanctionsSource  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402


class TestSanctionsIndexer:
    """Test the SanctionsIndexer functionality"""

    def test_source_initialization(self):
        """Test that sources are properly initialized"""
        indexer = SanctionsIndexer()
        assert len(indexer.sources) == 4  # OFAC, EU, UK, UN

        source_names = [s.name for s in indexer.sources]
        expected_names = ["ofac_sdn", "eu_sanctions", "uk_hmt", "un_sanctions"]
        assert source_names == expected_names

    def test_should_fetch_logic(self):
        """Test the should_fetch logic"""
        source = SanctionsSource(
            name="test",
            url="http://test.com",
            format_type="xml",
            parser_func=lambda x: [],
            refresh_interval=timedelta(hours=1)
        )

        # Should fetch if never fetched before
        assert asyncio.run(source.should_fetch())

        # Set last fetch
        source.last_fetch = datetime.utcnow()
        assert not asyncio.run(source.should_fetch())

        # Should fetch if interval passed
        source.last_fetch = datetime.utcnow() - timedelta(hours=2)
        assert asyncio.run(source.should_fetch())

    @pytest.mark.asyncio
    async def test_parse_ofac_xml(self):
        """Test OFAC XML parsing"""
        indexer = SanctionsIndexer()

        # Mock XML content
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <sdnList>
            <sdnEntry>
                <firstName>John</firstName>
                <lastName>Doe</lastName>
                <program>SDNT</program>
                <address>
                    <addressType>Wallet</addressType>
                    <address>0x1234567890abcdef1234567890abcdef12345678</address>
                </address>
            </sdnEntry>
        </sdnList>"""

        entries = indexer._parse_ofac_xml(xml_content)
        assert len(entries) == 1
        assert entries[0]['chain'] == 'ethereum'
        assert entries[0]['address'] == '0x1234567890abcdef1234567890abcdef12345678'
        assert entries[0]['label'] == 'sanctioned'
        assert entries[0]['source'] == 'ofac'

    @pytest.mark.asyncio
    async def test_parse_uk_csv(self):
        """Test UK CSV parsing"""
        indexer = SanctionsIndexer()

        csv_content = """Name,DOB,Nationality,Address,Other Info
John Doe,1980-01-01,British,0xabcdef1234567890abcdef1234567890abcdef12,Crypto wallet"""

        entries = indexer._parse_uk_csv(csv_content)
        assert len(entries) == 1
        assert entries[0]['chain'] == 'ethereum'
        assert entries[0]['address'] == '0xabcdef1234567890abcdef1234567890abcdef12'
        assert entries[0]['label'] == 'sanctioned'
        assert entries[0]['source'] == 'uk_hmt'

    @pytest.mark.asyncio
    async def test_normalize_entries(self):
        """Test entry normalization and deduplication"""
        indexer = SanctionsIndexer()

        entries = [
            {
                'chain': 'ethereum',
                'address': '0x1234567890abcdef1234567890abcdef12345678',
                'label': 'sanctioned',
                'category': 'sanctions',
                'source': 'ofac',
                'confidence': 1.0,
                'metadata': {'name': 'John Doe'}
            },
            {
                'chain': 'ETHEREUM',  # Different case
                'address': '0x1234567890ABCDEF1234567890ABCDEF12345678',  # Different case
                'label': 'sanctioned',
                'category': 'sanctions',
                'source': 'eu',
                'confidence': 0.9,
                'metadata': {'name': 'Jane Doe'}
            },
            # Duplicate of first entry
            {
                'chain': 'ethereum',
                'address': '0x1234567890abcdef1234567890abcdef12345678',
                'label': 'sanctioned',
                'category': 'sanctions',
                'source': 'un',
                'confidence': 0.8,
                'metadata': {'name': 'John Doe'}
            }
        ]

        normalized = indexer.normalize_entries(entries)
        assert len(normalized) == 2  # Should dedupe
        assert normalized[0]['chain'] == 'ethereum'
        assert normalized[0]['address'] == '0x1234567890abcdef1234567890abcdef12345678'
        assert normalized[0]['confidence'] == 1.0  # Should take higher confidence
        assert normalized[1]['confidence'] == 0.9

    def test_extract_address_from_text(self):
        """Test crypto address extraction from text"""
        indexer = SanctionsIndexer()

        # Test Ethereum address
        text = "Transfer funds to wallet 0x1234567890abcdef1234567890abcdef12345678 for payment"
        addr = indexer._extract_address_from_text(text)
        assert addr == '0x1234567890abcdef1234567890abcdef12345678'

        # Test Bitcoin address
        text = "Bitcoin address: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        addr = indexer._extract_address_from_text(text)
        assert addr == 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'

        # Test no address
        text = "No crypto address here"
        addr = indexer._extract_address_from_text(text)
        assert addr is None

    def test_is_crypto_relevant(self):
        """Test crypto relevance detection"""
        indexer = SanctionsIndexer()

        # Should detect crypto keywords
        assert indexer._is_crypto_relevant(None, "wallet address 0x1234")
        assert indexer._is_crypto_relevant(None, "bitcoin transfer")
        assert indexer._is_crypto_relevant(None, "ethereum wallet")

        # Should not detect non-crypto
        assert not indexer._is_crypto_relevant(None, "bank account")
        assert not indexer._is_crypto_relevant(None, "phone number")


class TestSanctionsSource:
    """Test individual SanctionsSource functionality"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset any global state before each test"""
        # Clear any cached imports or state
        yield
        # Cleanup after test

    @pytest.mark.asyncio
    async def test_fetch_data_304_not_modified(self):
        """Test handling of 304 Not Modified responses"""
        source = SanctionsSource(
            name="test",
            url="http://test.com",
            format_type="xml",
            parser_func=lambda x: []
        )

        # Mock a 304 response
        # WICHTIG: das im Zielmodul referenzierte Symbol patchen
        with patch('app.intel.sanctions.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 304
            mock_response.headers = {}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await source.fetch_data()
            assert result is None  # Should return None for 304

    @pytest.mark.asyncio
    @pytest.mark.asyncio_cooperative  # Run in isolation
    async def test_fetch_data_success(self):
        """Test successful data fetch (may be flaky in parallel runs)"""
        source = SanctionsSource(
            name="test",
            url="http://test.com",
            format_type="xml",
            parser_func=lambda x: []
        )

        from unittest.mock import AsyncMock
        # WICHTIG: das im Zielmodul referenzierte Symbol patchen (nicht das globale httpx)
        with patch('app.intel.sanctions.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<xml>test</xml>"
            mock_response.headers = {"ETag": "abc123"}

            # Simuliere async Kontextmanager und async get()
            mock_ctx = mock_client.return_value
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_ctx.get = AsyncMock(return_value=mock_response)

            result = await source.fetch_data()
            assert result == "<xml>test</xml>"
            assert source.etag == "abc123"
            assert source.last_fetch is not None


@pytest.mark.integration
class TestSanctionsIntegration:
    """Integration tests for the full sanctions workflow"""

    @pytest.mark.asyncio
    async def test_full_update_cycle_mock(self):
        """Test full update cycle with mocked sources"""
        indexer = SanctionsIndexer()

        # Mock all source fetches to return empty data
        for source in indexer.sources:
            source.fetch_data = AsyncMock(return_value="<empty></empty>")

        result = await indexer.run_update()

        assert result["status"] == "success"
        assert result["total_entries"] == 0

    @pytest.mark.asyncio
    async def test_run_update_with_db_integration(self):
        """Test update with DB integration (if available)"""
        # This test will be skipped if DB integration is not available
        if not hasattr(SanctionsIndexer(), '_normalize_entries'):
            pytest.skip("DB integration not available")

        indexer = SanctionsIndexer()

        # Mock sources to return test data
        test_entries = [{
            'chain': 'ethereum',
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'label': 'sanctioned',
            'category': 'sanctions',
            'source': 'test',
            'confidence': 1.0,
            'metadata': {'test': 'data'}
        }]

        for source in indexer.sources:
            source.fetch_data = AsyncMock(return_value="<test>data</test>")
            source.parser_func = Mock(return_value=test_entries)

        with patch('app.intel.sanctions.bulk_upsert') as mock_bulk_upsert:
            mock_bulk_upsert.return_value = (1, 0)  # 1 inserted, 0 existing

            result = await indexer.run_update()

            assert result["status"] == "success"
            assert result["total_entries"] == 4  # 4 sources * 1 entry each
            assert result["db_inserted"] == 1
            assert result["db_existing"] == 0
