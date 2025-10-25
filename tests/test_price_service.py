import os
import sys
import pathlib
import asyncio
import pytest

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.price_service import price_service  # noqa: E402


@pytest.mark.asyncio
async def test_price_overrides_env(monkeypatch):
    monkeypatch.setenv("PRICE_OVERRIDES_JSON", '{"ETH": 2000, "USDC": 1.0}')
    # Clear internal cache
    price_service._cache.clear()

    p_eth = await price_service.get_usd_price("ethereum", None, "ETH")
    p_usdc = await price_service.get_usd_price("ethereum", None, "USDC")

    assert p_eth == 2000.0
    assert p_usdc == 1.0


@pytest.mark.asyncio
async def test_price_defaults_and_eth_env(monkeypatch):
    # No overrides; USDC defaults to 1.0
    monkeypatch.delenv("PRICE_OVERRIDES_JSON", raising=False)
    monkeypatch.setenv("ETH_USD_PRICE", "2500")
    price_service._cache.clear()

    p_usdc = await price_service.get_usd_price("ethereum", None, "USDC")
    p_eth = await price_service.get_usd_price("ethereum", None, "ETH")

    assert p_usdc == 1.0
    assert p_eth == 2500.0
