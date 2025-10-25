"""
Tests für Multi-Sanctions Integration (OFAC, UN, EU, UK, Canada, Australia)
"""
import pytest
from app.compliance.sanctions.service import SanctionsService


def test_sanctions_service_has_all_sources():
    """Teste, dass alle 6 Sanctions-Quellen konfiguriert sind"""
    service = SanctionsService()
    
    expected_sources = ["ofac", "un", "eu", "uk", "canada", "australia"]
    assert service._sources == expected_sources
    assert len(service._versions) == 6
    assert len(service._last_updated) == 6


def test_sanctions_service_initialization():
    """Teste Initialisierung des Service"""
    service = SanctionsService()
    
    assert service._counts["entities"] == 0
    assert service._counts["aliases"] == 0
    assert all(v == "v0" for v in service._versions.values())
    assert all(v is None for v in service._last_updated.values())


def test_sanctions_stats():
    """Teste Stats-Endpoint"""
    service = SanctionsService()
    stats = service.stats()
    
    assert "sources" in stats
    assert "versions" in stats
    assert "counts" in stats
    assert "last_updated" in stats
    assert "totals" in stats
    
    assert len(stats["sources"]) == 6
    assert "canada" in stats["sources"]
    assert "australia" in stats["sources"]


def test_sanctions_screening_address_not_found():
    """Teste Screening wenn keine Matches gefunden werden"""
    service = SanctionsService()
    
    result = service.screen(address="0x0000000000000000000000000000000000000000")
    
    assert result["matched"] is False
    assert result["entity_id"] is None
    assert result["canonical_name"] is None
    assert len(result["lists"]) == 6


def test_sanctions_screening_with_list_filter():
    """Teste Screening mit spezifischen Listen"""
    service = SanctionsService()
    
    result = service.screen(
        address="0x0000000000000000000000000000000000000000",
        lists=["canada", "australia"]
    )
    
    assert result["matched"] is False
    assert "canada" in result["lists"]
    assert "australia" in result["lists"]


@pytest.mark.asyncio
async def test_sanctions_reload():
    """Teste Reload-Funktion (mit Stubs)"""
    service = SanctionsService()
    
    # Mit Stub-Loadern sollte dies ohne Fehler laufen
    result = service.reload()
    
    assert "success" in result
    assert "sources" in result
    assert "versions" in result
    assert len(result["sources"]) == 6
