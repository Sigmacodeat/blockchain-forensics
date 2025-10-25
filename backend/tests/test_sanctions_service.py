import pytest
from unittest.mock import patch
from app.compliance.sanctions import SanctionsService


@pytest.fixture
def sanctions_service():
    return SanctionsService()


class TestSanctionsService:
    """Tests für SanctionsService"""

    @patch('app.compliance.sanctions.query_labels_by_address')
    def test_screen_matched_address(self, mock_query, sanctions_service):
        """Test screening einer sanktionierten Adresse"""
        mock_query.return_value = [
            {
                'id': 'label_1',
                'label': 'sanctioned',
                'source': 'ofac',
                'metadata': {'name': 'Test Entity'}
            }
        ]

        result = sanctions_service.screen(address='0x1234567890abcdef1234567890abcdef12345678')

        assert result['matched'] is True
        assert result['entity_id'] == 'label_1'
        assert result['canonical_name'] == 'Test Entity'
        assert 'ofac' in result['lists']
        assert len(result['alias_hits']) == 1
        assert result['alias_hits'][0]['alias'] == '0x1234567890abcdef1234567890abcdef12345678'
        assert result['explain'] == 'Address matched 1 sanctions entries'

    @patch('app.compliance.sanctions.query_labels_by_address')
    def test_screen_clean_address(self, mock_query, sanctions_service):
        """Test screening einer sauberen Adresse"""
        mock_query.return_value = []  # Keine sanktionierten Labels

        result = sanctions_service.screen(address='0xabcdefabcdefabcdefabcdefabcdefabcdefabcd')

        assert result['matched'] is False
        assert result['entity_id'] is None
        assert result['canonical_name'] is None
        assert result['lists'] == ['ofac', 'un', 'eu', 'uk']
        assert result['alias_hits'] == []
        assert result['explain'] == 'No matches found'

    @patch('app.compliance.sanctions.query_labels_by_address')
    def test_screen_with_name(self, mock_query, sanctions_service):
        """Test screening mit Name (ohne Adresse)"""
        mock_query.return_value = []

        result = sanctions_service.screen(name='Test Name')

        assert result['matched'] is False  # Da nur Adresse-Query gemockt

    def test_screen_no_input(self, sanctions_service):
        """Test screening ohne Input"""
        result = sanctions_service.screen()

        assert result['matched'] is False
        assert result['explain'] == 'No matches found'

    def test_stats(self, sanctions_service):
        """Test Stats-Methode"""
        result = sanctions_service.stats()

        assert 'sources' in result
        assert 'versions' in result
        assert 'counts' in result
        assert result['sources'] == ['ofac', 'un', 'eu', 'uk']

    @patch('app.compliance.sanctions._SANCTIONS_AVAILABLE', False)
    def test_screen_fallback_when_unavailable(self, sanctions_service):
        """Test Fallback, wenn Sanctions nicht verfügbar"""
        result = sanctions_service.screen(address='0x123')

        assert result['matched'] is False
        assert result['explain'] == 'Sanctions service not available'
