import pytest
from app.compliance.sources.sanctions_indexer import EUSource

@pytest.mark.asyncio
async def test_eu_parser_basic():
    """Test basic EU parser functionality with mock data."""
    source = EUSource()
    
    # Mock CSV data with some crypto-like strings
    mock_csv = """name,address,remarks
Test Entity 1,0x1234567890abcdef1234567890abcdef12345678,Some ETH address
Test Entity 2,bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4,Some BTC address
"""
    
    result = await source._parse_csv(mock_csv)
    
    # Should find at least the ETH and BTC addresses
    addresses = [item['address'] for item in result]
    assert '0x1234567890abcdef1234567890abcdef12345678' in addresses
    assert 'bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4' in addresses
    
    # Check metadata
    for item in result:
        assert item['source'] == 'EU'
        assert item['category'] == 'sanctions'
        assert item['label'] == 'sanctioned'
        assert item['confidence'] == 0.75

@pytest.mark.asyncio
async def test_eu_parser_empty():
    """Test EU parser with empty data."""
    source = EUSource()
    
    result = await source._parse_csv("")
    assert result == []
    
    # Test with header only
    result = await source._parse_csv("name,address,remarks")
    assert result == []
