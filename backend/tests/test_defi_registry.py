import os
import json

from app.intel.defi.registry import get_all_protocols, get_labels_seed


def test_registry_minimum_protocols():
    prots = get_all_protocols()
    slugs = {p['slug'] for p in prots}
    # sanity: core protocols present
    assert 'uniswap-v3' in slugs
    assert 'curve' in slugs
    assert 'aave' in slugs


def test_labels_seed_without_extras():
    # ensure no external sources
    if 'DEFI_PROTOCOL_CONTRACT_SOURCES' in os.environ:
        del os.environ['DEFI_PROTOCOL_CONTRACT_SOURCES']
    items = get_labels_seed()
    # no built-in contracts yet, should be empty
    assert isinstance(items, list)


def test_labels_seed_with_extra_file(tmp_path):
    data = [
        {"slug": "uniswap-v3", "chain": "ethereum", "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "label": "Uniswap V3 USDC/WETH 0.05%", "type": "pool"}
    ]
    f = tmp_path / 'uniswap.json'
    f.write_text(json.dumps(data), encoding='utf-8')
    os.environ['DEFI_PROTOCOL_CONTRACT_SOURCES'] = json.dumps([str(f)])

    items = get_labels_seed()
    assert any(it['address'] == data[0]['address'] for it in items)
