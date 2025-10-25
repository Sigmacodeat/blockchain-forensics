import pytest
from unittest.mock import AsyncMock

from app.ml.heuristics_library import heuristics_lib, HeuristicResult


@pytest.mark.asyncio
async def test_h024_flashbots_bundle_patterns_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xSearchEr1", "cnt": 4},
        {"addr": "0xSearchEr2", "cnt": 6},
    ]
    res: HeuristicResult = await heuristics_lib.h024_flashbots_bundle_patterns(
        address="0xdeadbeef", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H024_flashbots_bundles"
    assert "0xsearcher1" in res.related_addresses
    assert len(res.related_addresses) == 2
    assert res.confidence == 0.65


@pytest.mark.asyncio
async def test_h025_mev_searcher_identification_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xmev", "dex_cnt": 7}
    ]
    res = await heuristics_lib.h025_mev_searcher_identification(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H025_mev_searcher"
    assert "0xmev" in res.related_addresses
    assert res.confidence == 0.70


@pytest.mark.asyncio
async def test_h026_sandwich_attack_pattern_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xsand", "s_cnt": 5},
        {"addr": "0xsand2", "s_cnt": 3},
    ]
    res = await heuristics_lib.h026_sandwich_attack_pattern(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H026_sandwich_pattern"
    assert "0xsand" in res.related_addresses
    assert len(res.related_addresses) == 2
    assert res.confidence == 0.65


@pytest.mark.asyncio
async def test_h029_tornado_cash_timing_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xmix1"}, {"addr": "0xmix2"}
    ]
    res = await heuristics_lib.h029_tornado_cash_timing(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H029_tornado_timing"
    assert res.confidence == 0.75
    assert len(res.related_addresses) == 2


@pytest.mark.asyncio
async def test_h032_gnosis_safe_cosigners_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xsafe1", "cosign_cnt": 3},
        {"addr": "0xsafe2", "cosign_cnt": 4},
    ]
    res = await heuristics_lib.h032_gnosis_safe_cosigners(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H032_gnosis_safe_cosigners"
    assert res.confidence == 0.80
    assert "0xsafe1" in res.related_addresses
    assert len(res.evidence) == 2


@pytest.mark.asyncio
async def test_h048_compound_collateral_pattern_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xcomp1"},
        {"addr": "0xcomp2"},
    ]
    res = await heuristics_lib.h048_compound_collateral_pattern(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H048_compound_pattern"
    assert res.confidence == 0.60
    assert "0xcomp1" in res.related_addresses
    assert len(res.related_addresses) == 2


@pytest.mark.asyncio
async def test_h049_curve_pool_correlation_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xcurve1", "common_pools": 2},
        {"addr": "0xcurve2", "common_pools": 3},
    ]
    res = await heuristics_lib.h049_curve_pool_correlation(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H049_curve_pool_correlation"
    assert res.confidence == 0.65
    assert "0xcurve1" in res.related_addresses
    assert len(res.evidence) == 2


@pytest.mark.asyncio
async def test_h028_mev_liquidation_bots_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xliq1", "liq_cnt": 3},
        {"addr": "0xliq2", "liq_cnt": 5},
    ]
    res = await heuristics_lib.h028_mev_liquidation_bots(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H028_mev_liquidations"
    assert res.confidence == 0.70
    assert "0xliq1" in res.related_addresses
    assert len(res.evidence) == 2


@pytest.mark.asyncio
async def test_h030_aztec_privacy_pool_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xaz1"}, {"addr": "0xaz2"}
    ]
    res = await heuristics_lib.h030_aztec_privacy_pool(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H030_aztec_privacy"
    assert res.confidence == 0.65
    assert len(res.related_addresses) == 2


@pytest.mark.asyncio
async def test_h031_railgun_shielding_detection_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xrg1"}, {"addr": "0xrg2"}, {"addr": "0xrg3"}
    ]
    res = await heuristics_lib.h031_railgun_shielding_detection(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H031_railgun"
    assert res.confidence == 0.65
    assert "0xrg1" in res.related_addresses


@pytest.mark.asyncio
async def test_h050_yearn_vault_strategy_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xy1", "common_vaults": 1}
    ]
    res = await heuristics_lib.h050_yearn_vault_strategy(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H050_yearn_vault"
    assert res.confidence == 0.60
    assert "0xy1" in res.related_addresses


@pytest.mark.asyncio
async def test_h056_gmx_perp_trading_basic():
    neo4j = AsyncMock()
    neo4j.execute_read.return_value = [
        {"addr": "0xgmx1"}, {"addr": "0xgmx2"}
    ]
    res = await heuristics_lib.h056_gmx_perp_trading(
        address="0xabc", neo4j_client=neo4j
    )
    assert res.heuristic_name == "H056_gmx_perp"
    assert res.confidence == 0.60
    assert len(res.related_addresses) == 2
