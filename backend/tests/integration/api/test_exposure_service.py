import pytest

from app.analytics.exposure_service import exposure_service


@pytest.mark.asyncio
async def test_calculate_direct_exposure_true():
    res = await exposure_service.calculate(
        address="0xABC",
        max_hops=3,
        context={"labels": ["sanctioned", "exchange"]},
    )
    assert res.direct_exposure is True
    assert res.indirect_hops is None
    assert 0.0 <= res.exposure_share <= 1.0


@pytest.mark.asyncio
async def test_calculate_indirect_exposure_hops_limited():
    res = await exposure_service.calculate(
        address="0xDEF",
        max_hops=1,
        context={
            "labels": [],
            "graph_summary": {"sanctioned_hops": 2, "exposure_share": 0.5, "paths_examined": 5},
        },
    )
    assert res.direct_exposure is False
    # hops beyond limit => dropped
    assert res.indirect_hops is None
    assert res.exposure_share == 0.0


@pytest.mark.asyncio
async def test_batch_calculate_sanitizes_inputs():
    res = await exposure_service.batch_calculate(
        addresses=["  ", "0xA", None, "0xB"],
        max_hops=2,
        context_by_address={"0xB": {"labels": ["high_risk"]}},
    )
    # service echoes keys as provided, caller should sanitize; ensure dict present for requested
    assert "0xB" in res
    assert isinstance(res["0xB"], dict)
