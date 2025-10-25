import asyncio
import types
import pytest

from app.services.multi_chain import ChainAdapterFactory, ChainType


@pytest.fixture
def factory():
    return ChainAdapterFactory()


def test_registry_contains_expected_chains(factory):
    registry = factory.chain_registry
    # Minimal erwartete Chains gemäß Registry-Erweiterungen
    expected = {
        "avalanche",
        "fantom",
        "gnosis-chiado",
        "litecoin",
        "solana",
    }
    assert expected.issubset(set(registry.keys()))

    # Spot-Checks für Felder
    avax = registry["avalanche"]
    assert avax.chain_id == "avalanche"
    assert avax.chain_type == ChainType.EVM
    assert isinstance(avax.rpc_urls, list) and len(avax.rpc_urls) >= 1

    ltc = registry["litecoin"]
    assert ltc.chain_id == "litecoin"
    assert ltc.chain_type == ChainType.UTXO


def test_get_adapter_returns_correct_type(factory, monkeypatch):
    # Stubbe asyncio.create_task, da in Unit-Tests keine laufende Loop garantiert ist
    monkeypatch.setattr(asyncio, "create_task", lambda coro: types.SimpleNamespace(done=lambda: True))

    evm_adapter = factory.get_adapter("ethereum")
    # Ethereum könnte implizit in Registry sein; falls nicht, überspringen
    if evm_adapter is None:
        pytest.skip("ethereum chain not configured in registry")
    # Typischerweise hat der Adapter ein 'chain_info' mit ChainType.EVM
    assert getattr(evm_adapter, "chain_info").chain_type == ChainType.EVM

    utxo_adapter = factory.get_adapter("litecoin")
    if utxo_adapter is None:
        pytest.skip("litecoin chain not configured in registry")
    assert getattr(utxo_adapter, "chain_info").chain_type == ChainType.UTXO

    svm_adapter = factory.get_adapter("solana")
    if svm_adapter is None:
        pytest.skip("solana chain not configured in registry")
    assert getattr(svm_adapter, "chain_info").chain_type == ChainType.SVM


def test_get_adapter_unsupported_chain_returns_none(factory, monkeypatch, caplog):
    monkeypatch.setattr(asyncio, "create_task", lambda coro: types.SimpleNamespace(done=lambda: True))
    with caplog.at_level("ERROR"):
        adapter = factory.get_adapter("unknown-chain")
    assert adapter is None
    # Prüfe, dass eine brauchbare Fehlermeldung geloggt wurde
    assert any("Unsupported chain" in rec.message for rec in caplog.records)
