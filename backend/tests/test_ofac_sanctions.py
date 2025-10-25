"""
Tests for OFAC Sanctions Service
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.services.ofac_sanctions import OFACSanctionsService


@pytest.fixture
def ofac_service():
    """Create OFAC service instance"""
    return OFACSanctionsService()


@pytest.fixture
def mock_csv_data():
    """Mock OFAC CSV data"""
    return """ent_num,SDN_Name,SDN_Type,Program,Title,Call_Sign,Vess_type,Tonnage,GRT,Vess_flag,Vess_owner,Remarks
1234,TEST ENTITY,individual,CYBER2,"","","","","","","","Digital Currency Address - ETH 0x1234567890123456789012345678901234567890"
5678,SANCTIONED ORG,entity,IRAN,"","","","","","","","BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
"""


@pytest.mark.asyncio
async def test_parse_sanctions(ofac_service, mock_csv_data):
    """Test CSV parsing"""
    parsed = await ofac_service._parse_sanctions(mock_csv_data)
    
    assert len(parsed["addresses"]) == 2
    assert "0x1234567890123456789012345678901234567890" in parsed["addresses"][0].lower()
    assert len(parsed["entities"]) == 2


@pytest.mark.asyncio
async def test_extract_crypto_addresses(ofac_service):
    """Test address extraction"""
    
    # Ethereum
    text_eth = "Digital Currency Address - ETH 0xABCDEF1234567890123456789012345678901234"
    addresses = ofac_service._extract_crypto_addresses(text_eth)
    assert len(addresses) == 1
    assert addresses[0].startswith("0x")
    
    # Bitcoin
    text_btc = "BTC Address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    addresses = ofac_service._extract_crypto_addresses(text_btc)
    assert len(addresses) >= 1


@pytest.mark.asyncio
async def test_is_sanctioned_not_found(ofac_service):
    """Test non-sanctioned address"""
    result = await ofac_service.is_sanctioned("0x0000000000000000000000000000000000000000")
    assert result == False


@pytest.mark.asyncio
async def test_update_sanctions_list(ofac_service):
    """Test full update workflow (mocked)"""
    
    with patch.object(ofac_service, '_download_sanctions', new_callable=AsyncMock) as mock_download:
        with patch.object(ofac_service, '_store_sanctions', new_callable=AsyncMock) as mock_store:
            with patch.object(ofac_service, '_update_cache', new_callable=AsyncMock) as mock_cache:
                
                # Mock CSV data
                mock_download.return_value = """ent_num,SDN_Name,SDN_Type,Program,Remarks
1,Test,entity,CYBER2,"ETH 0x1234567890123456789012345678901234567890"
"""
                mock_store.return_value = 1
                
                # Run update
                stats = await ofac_service.update_sanctions_list()
                
                assert stats["success"] == True
                assert stats["addresses_added"] >= 0
                
                # Verify calls
                mock_download.assert_called_once()
                mock_store.assert_called_once()
                mock_cache.assert_called_once()
