import os
import json

import pytest

from app.ingest.defi_labels_ingester import run_once


class DummyBulk:
    def __init__(self):
        self.called = False
        self.items = None

    async def __call__(self, items):
        self.called = True
        self.items = items
        # pretend all inserted
        return (len(items), 0)


@pytest.mark.asyncio
async def test_ingester_with_external_file(monkeypatch, tmp_path):
    # prepare external contracts file
    data = [
        {"slug": "uniswap-v3", "chain": "ethereum", "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "label": "Uniswap V3 USDC/WETH 0.05%"},
        {"slug": "aave", "chain": "ethereum", "address": "0x3dfd23a6c5e8bbcfec3c9a9b9a6d5d6bbad9", "label": "Aave Lending Pool"}
    ]
    f = tmp_path / 'defi.json'
    f.write_text(json.dumps(data), encoding='utf-8')
    os.environ['DEFI_PROTOCOL_CONTRACT_SOURCES'] = json.dumps([str(f)])

    # patch bulk_upsert
    dummy = DummyBulk()
    monkeypatch.setattr('app.ingest.defi_labels_ingester.bulk_upsert', dummy)

    res = await run_once()

    assert dummy.called is True
    assert isinstance(res, dict)
    # Im normalen Modus (kein DRY_RUN) werden Items eingefügt
    assert res.get('inserted') == len(dummy.items)
    assert res.get('existing') == 0
    assert res.get('total') == len(dummy.items)


@pytest.mark.asyncio
async def test_ingester_without_sources(monkeypatch):
    if 'DEFI_PROTOCOL_CONTRACT_SOURCES' in os.environ:
        del os.environ['DEFI_PROTOCOL_CONTRACT_SOURCES']

    # patch bulk_upsert to ensure it's not called
    async def _fake_bulk(items):
        raise AssertionError("bulk_upsert should not be called with empty items")

    monkeypatch.setattr('app.ingest.defi_labels_ingester.bulk_upsert', _fake_bulk)

    res = await run_once()
    # Bei fehlenden Quellen keine Inserts, toleranter Vergleich (Dry-Run-Key optional)
    assert isinstance(res, dict)
    assert res.get('inserted') == 0
    assert res.get('existing') == 0
    assert res.get('total') == 0
