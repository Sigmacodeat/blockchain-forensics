"""
Chain utility endpoints to quickly test adapter RPCs
"""
from fastapi import APIRouter, Query
from typing import Any, Dict, cast

from app.schemas.chain_responses import (
    SolanaBlockResponse,
    SolanaTxResponse,
    SolanaCanonicalResponse,
    BitcoinBlockResponse,
    BitcoinTxResponse,
    BitcoinTxNormalized,
    BitcoinEdgesResponse,
    EthereumTxResponse,
    EthereumCanonicalResponse,
)
from app.services.graph_service import service as graph_service
from app.observability.metrics import CHAIN_REQUESTS, CHAIN_LATENCY
import time
import importlib

router = APIRouter()


@router.get("/solana/block", summary="Fetch Solana block by slot", response_model=SolanaBlockResponse)
async def solana_block(slot: int = Query(..., ge=0)) -> Dict[str, Any]:
    op = "block"
    chain = "solana"
    start = time.time()
    try:
        create_solana_adapter = getattr(importlib.import_module("app.adapters.solana_adapter"), "create_solana_adapter")
        adapter = create_solana_adapter()
        res = await adapter.get_block(slot)
        return {"slot": slot, "result": res}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/solana/health", summary="Solana adapter health check")
async def solana_health() -> Dict[str, Any]:
    op = "health"
    chain = "solana"
    start = time.time()
    try:
        create_solana_adapter = getattr(importlib.import_module("app.adapters.solana_adapter"), "create_solana_adapter")
        adapter = create_solana_adapter()
        return await adapter.health()
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/solana/tx", summary="Fetch Solana transaction by signature", response_model=SolanaTxResponse)
async def solana_tx(signature: str) -> Dict[str, Any]:
    op = "tx"
    chain = "solana"
    start = time.time()
    try:
        create_solana_adapter = getattr(importlib.import_module("app.adapters.solana_adapter"), "create_solana_adapter")
        adapter = create_solana_adapter()
        res = await adapter.get_transaction(signature)
        return {"signature": signature, "result": res}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/solana/tx/canonical", summary="Fetch and map Solana transaction to canonical event", response_model=SolanaCanonicalResponse)
async def solana_tx_canonical(signature: str) -> Dict[str, Any]:
    op = "tx_canonical"
    chain = "solana"
    start = time.time()
    try:
        create_solana_adapter = getattr(importlib.import_module("app.adapters.solana_adapter"), "create_solana_adapter")
        adapter = create_solana_adapter()
        raw = await adapter.get_transaction(signature)
        if not raw:
            CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
            CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
            return {"signature": signature, "error": "not_found"}
        evt = await adapter.to_canonical(raw)
        payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
        return {"signature": signature, "canonical": payload}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.post("/solana/tx/canonical/ingest", summary="Fetch canonical and ingest into graph")
async def solana_tx_canonical_ingest(signature: str) -> Dict[str, Any]:
    op = "tx_canonical_ingest"
    chain = "solana"
    start = time.time()
    try:
        create_solana_adapter = getattr(importlib.import_module("app.adapters.solana_adapter"), "create_solana_adapter")
        adapter = create_solana_adapter()
        raw = await adapter.get_transaction(signature)
        if not raw:
            CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
            CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
            return {"signature": signature, "status": "not_found"}
        evt = await adapter.to_canonical(raw)
        payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
        res = graph_service.ingest_canonical(payload)
        return {"signature": signature, "ingested": res}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/bitcoin/block", summary="Fetch Bitcoin block by height", response_model=BitcoinBlockResponse)
async def bitcoin_block(height: int = Query(..., ge=0)) -> Dict[str, Any]:
    op = "block"
    chain = "bitcoin"
    start = time.time()
    try:
        BitcoinAdapter = getattr(importlib.import_module("app.adapters.bitcoin_adapter"), "BitcoinAdapter")
        adapter = BitcoinAdapter()
        res = await adapter.fetch_block(height)
        return res
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/bitcoin/block/summary", summary="Fetch Bitcoin block and provide lightweight tx summary")
async def bitcoin_block_summary(height: int = Query(..., ge=0)) -> Dict[str, Any]:
    op = "block_summary"
    chain = "bitcoin"
    start = time.time()
    BitcoinAdapter = getattr(importlib.import_module("app.adapters.bitcoin_adapter"), "BitcoinAdapter")
    adapter = BitcoinAdapter()
    blk = await adapter.fetch_block(height)
    raw = blk.get("raw", {})
    txs = raw.get("tx", [])
    summary = [
        {
            "txid": t.get("txid"),
            "vin": len(t.get("vin", [])),
            "vout": len(t.get("vout", [])),
            "size": t.get("size"),
            "fee_sat": t.get("fee"),
        }
        for t in txs
    ]
    res = {"height": blk.get("height"), "hash": blk.get("hash"), "txs": summary}
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    return res


@router.get("/bitcoin/tx", summary="Fetch Bitcoin transaction (decoded)", response_model=BitcoinTxResponse)
async def bitcoin_tx(txid: str) -> Dict[str, Any]:
    op = "tx"
    chain = "bitcoin"
    start = time.time()
    BitcoinAdapter = getattr(importlib.import_module("app.adapters.bitcoin_adapter"), "BitcoinAdapter")
    adapter = BitcoinAdapter()
    tx = await adapter.fetch_tx(txid)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok" if tx else "not_found").inc()
    return tx if tx else {"txid": txid, "status": "not_found"}


@router.get("/bitcoin/tx/normalized", summary="Fetch Bitcoin transaction and return normalized view", response_model=BitcoinTxNormalized)
async def bitcoin_tx_normalized(txid: str) -> Dict[str, Any]:
    op = "tx_normalized"
    chain = "bitcoin"
    start = time.time()
    BitcoinAdapter = getattr(importlib.import_module("app.adapters.bitcoin_adapter"), "BitcoinAdapter")
    adapter = BitcoinAdapter()
    tx = await adapter.fetch_tx(txid)
    if not tx:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"txid": txid, "status": "not_found"}
    res = adapter.normalize_tx(tx)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    return res


@router.get("/bitcoin/tx/edges", summary="Compute basic UTXO flow edges for a transaction", response_model=BitcoinEdgesResponse)
async def bitcoin_tx_edges(txid: str, method: str = Query("proportional")) -> Dict[str, Any]:
    op = f"tx_edges_{method}"
    chain = "bitcoin"
    start = time.time()
    BitcoinAdapter = getattr(importlib.import_module("app.adapters.bitcoin_adapter"), "BitcoinAdapter")
    adapter = BitcoinAdapter()
    tx = await adapter.fetch_tx(txid)
    if not tx or not tx.get("txid"):
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"txid": txid, "status": "not_found"}
    edges = await adapter.build_tx_edges(tx, method=method)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    return edges


@router.post("/bitcoin/tx/edges/ingest", summary="Fetch edges and ingest into graph")
async def bitcoin_tx_edges_ingest(txid: str, method: str = Query("proportional")) -> Dict[str, Any]:
    op = f"tx_edges_ingest_{method}"
    chain = "bitcoin"
    start = time.time()
    BitcoinAdapter = getattr(importlib.import_module("app.adapters.bitcoin_adapter"), "BitcoinAdapter")
    adapter = BitcoinAdapter()
    tx = await adapter.fetch_tx(txid)
    if not tx or not tx.get("txid"):
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"txid": txid, "status": "not_found"}
    edges = await adapter.build_tx_edges(tx, method=method)
    res = graph_service.ingest_btc_edges(txid, edges.get("edges", []), edges.get("fee"))
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    return {"txid": txid, "ingested": res, "method": method}


# Ethereum utilities
@router.get("/ethereum/tx", summary="Fetch Ethereum transaction by hash", response_model=EthereumTxResponse)
async def ethereum_tx(hash: str) -> Dict[str, Any]:
    op = "tx"
    chain = "ethereum"
    start = time.time()
    EthereumAdapter = getattr(importlib.import_module("app.adapters.ethereum_adapter"), "EthereumAdapter")
    adapter = EthereumAdapter()
    tx = await adapter.get_transaction(hash)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok" if tx else "not_found").inc()
    if tx:
        return tx
    else:
        return {"hash": str(hash), "status": "not_found"}


@router.get("/ethereum/tx/canonical", summary="Fetch Ethereum transaction and map to canonical event", response_model=EthereumCanonicalResponse)
async def ethereum_tx_canonical(hash: str) -> Dict[str, Any]:
    op = "tx_canonical"
    chain = "ethereum"
    start = time.time()
    EthereumAdapter = getattr(importlib.import_module("app.adapters.ethereum_adapter"), "EthereumAdapter")
    adapter = EthereumAdapter()
    raw_tx = await adapter.get_transaction(hash)
    if not raw_tx:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"hash": hash, "status": "not_found"}
    block_num = raw_tx.get('blockNumber')
    if block_num is None:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="pending").inc()
        return {"hash": hash, "status": "pending_or_no_block"}
    block = await adapter.get_block(block_num)
    evt = await adapter.transform_transaction(raw_tx, block)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
    return {"hash": hash, "canonical": payload}


@router.post("/ethereum/tx/canonical/ingest", summary="Fetch canonical and ingest into graph")
async def ethereum_tx_canonical_ingest(hash: str) -> Dict[str, Any]:
    EthereumAdapter = getattr(importlib.import_module("app.adapters.ethereum_adapter"), "EthereumAdapter")
    adapter = EthereumAdapter()
    raw_tx = await adapter.get_transaction(hash)
    if not raw_tx:
        return {"hash": hash, "status": "not_found"}
    block_num = raw_tx.get('blockNumber')
    if block_num is None:
        return {"hash": hash, "status": "pending_or_no_block"}
    block = await adapter.get_block(block_num)
    evt = await adapter.transform_transaction(raw_tx, block)
    payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
    res = graph_service.ingest_canonical(payload)
    return {"hash": hash, "ingested": res}


# L2 Chain Endpoints (Polygon, Arbitrum, Optimism, Base)

@router.get("/polygon/block/{block_number}", summary="Fetch Polygon block by number")
async def polygon_block(block_number: int) -> Dict[str, Any]:
    op = "block"
    chain = "polygon"
    start = time.time()
    try:
        PolygonAdapter = getattr(importlib.import_module("app.adapters.polygon_adapter"), "PolygonAdapter")
        adapter = PolygonAdapter()
        block = await adapter.get_block(block_number)
        return {"block_number": block_number, "chain": chain, "result": block}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/polygon/tx/{hash}", summary="Fetch Polygon transaction by hash")
async def polygon_tx(hash: str) -> Dict[str, Any]:
    op = "tx"
    chain = "polygon"
    start = time.time()
    try:
        PolygonAdapter = getattr(importlib.import_module("app.adapters.polygon_adapter"), "PolygonAdapter")
        adapter = PolygonAdapter()
        tx = await adapter.get_transaction(hash)
        return {"hash": hash, "chain": chain, "result": tx}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/polygon/tx/{hash}/canonical", summary="Fetch Polygon transaction as canonical event")
async def polygon_tx_canonical(hash: str) -> Dict[str, Any]:
    op = "tx_canonical"
    chain = "polygon"
    start = time.time()
    PolygonAdapter = getattr(importlib.import_module("app.adapters.polygon_adapter"), "PolygonAdapter")
    adapter = PolygonAdapter()
    raw_tx = await adapter.get_transaction(hash)
    if not raw_tx:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"hash": hash, "status": "not_found"}
    block_num = raw_tx.get('blockNumber')
    if block_num is None:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="pending").inc()
        return {"hash": hash, "status": "pending_or_no_block"}
    block = await adapter.get_block(block_num)
    evt = await adapter.transform_transaction(raw_tx, block)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
    return {"hash": hash, "canonical": payload}


@router.get("/arbitrum/block/{block_number}", summary="Fetch Arbitrum block by number")
async def arbitrum_block(block_number: int) -> Dict[str, Any]:
    op = "block"
    chain = "arbitrum"
    start = time.time()
    try:
        ArbitrumAdapter = getattr(importlib.import_module("app.adapters.arbitrum_adapter"), "ArbitrumAdapter")
        adapter = ArbitrumAdapter()
        block = await adapter.get_block(block_number)
        return {"block_number": block_number, "chain": chain, "result": block}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/arbitrum/tx/{hash}", summary="Fetch Arbitrum transaction by hash")
async def arbitrum_tx(hash: str) -> Dict[str, Any]:
    op = "tx"
    chain = "arbitrum"
    start = time.time()
    try:
        ArbitrumAdapter = getattr(importlib.import_module("app.adapters.arbitrum_adapter"), "ArbitrumAdapter")
        adapter = ArbitrumAdapter()
        tx = await adapter.get_transaction(hash)
        return {"hash": hash, "chain": chain, "result": tx}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/arbitrum/tx/{hash}/canonical", summary="Fetch Arbitrum transaction as canonical event")
async def arbitrum_tx_canonical(hash: str) -> Dict[str, Any]:
    op = "tx_canonical"
    chain = "arbitrum"
    start = time.time()
    ArbitrumAdapter = getattr(importlib.import_module("app.adapters.arbitrum_adapter"), "ArbitrumAdapter")
    adapter = ArbitrumAdapter()
    raw_tx = await adapter.get_transaction(hash)
    if not raw_tx:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"hash": hash, "status": "not_found"}
    block_num = raw_tx.get('blockNumber')
    if block_num is None:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="pending").inc()
        return {"hash": hash, "status": "pending_or_no_block"}
    block = await adapter.get_block(block_num)
    evt = await adapter.transform_transaction(raw_tx, block)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
    return {"hash": hash, "canonical": payload}


@router.get("/optimism/block/{block_number}", summary="Fetch Optimism block by number")
async def optimism_block(block_number: int) -> Dict[str, Any]:
    op = "block"
    chain = "optimism"
    start = time.time()
    try:
        OptimismAdapter = getattr(importlib.import_module("app.adapters.optimism_adapter"), "OptimismAdapter")
        adapter = OptimismAdapter()
        block = await adapter.get_block(block_number)
        return {"block_number": block_number, "chain": chain, "result": block}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/optimism/tx/{hash}", summary="Fetch Optimism transaction by hash")
async def optimism_tx(hash: str) -> Dict[str, Any]:
    op = "tx"
    chain = "optimism"
    start = time.time()
    try:
        OptimismAdapter = getattr(importlib.import_module("app.adapters.optimism_adapter"), "OptimismAdapter")
        adapter = OptimismAdapter()
        tx = await adapter.get_transaction(hash)
        return {"hash": hash, "chain": chain, "result": tx}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/optimism/tx/{hash}/canonical", summary="Fetch Optimism transaction as canonical event")
async def optimism_tx_canonical(hash: str) -> Dict[str, Any]:
    op = "tx_canonical"
    chain = "optimism"
    start = time.time()
    OptimismAdapter = getattr(importlib.import_module("app.adapters.optimism_adapter"), "OptimismAdapter")
    adapter = OptimismAdapter()
    raw_tx = await adapter.get_transaction(hash)
    if not raw_tx:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"hash": hash, "status": "not_found"}
    block_num = raw_tx.get('blockNumber')
    if block_num is None:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="pending").inc()
        return {"hash": hash, "status": "pending_or_no_block"}
    block = await adapter.get_block(block_num)
    evt = await adapter.transform_transaction(raw_tx, block)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
    return {"hash": hash, "canonical": payload}


@router.get("/base/block/{block_number}", summary="Fetch Base block by number")
async def base_block(block_number: int) -> Dict[str, Any]:
    op = "block"
    chain = "base"
    start = time.time()
    try:
        BaseAdapter = getattr(importlib.import_module("app.adapters.base_adapter"), "BaseAdapter")
        adapter = BaseAdapter()
        block = await adapter.get_block(block_number)
        return {"block_number": block_number, "chain": chain, "result": block}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/base/tx/{hash}", summary="Fetch Base transaction by hash")
async def base_tx(hash: str) -> Dict[str, Any]:
    op = "tx"
    chain = "base"
    start = time.time()
    try:
        BaseAdapter = getattr(importlib.import_module("app.adapters.base_adapter"), "BaseAdapter")
        adapter = BaseAdapter()
        tx = await adapter.get_transaction(hash)
        return {"hash": hash, "chain": chain, "result": tx}
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()


@router.get("/base/tx/{hash}/canonical", summary="Fetch Base transaction as canonical event")
async def base_tx_canonical(hash: str) -> Dict[str, Any]:
    op = "tx_canonical"
    chain = "base"
    start = time.time()
    BaseAdapter = getattr(importlib.import_module("app.adapters.base_adapter"), "BaseAdapter")
    adapter = BaseAdapter()
    raw_tx = await adapter.get_transaction(hash)
    if not raw_tx:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="not_found").inc()
        return {"hash": hash, "status": "not_found"}
    block_num = raw_tx.get('blockNumber')
    if block_num is None:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="pending").inc()
        return {"hash": hash, "status": "pending_or_no_block"}
    block = await adapter.get_block(block_num)
    evt = await adapter.transform_transaction(raw_tx, block)
    CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - start)
    CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
    payload: Dict[str, Any] = cast(Dict[str, Any], evt.dict() if hasattr(evt, 'dict') else evt)
    return {"hash": hash, "canonical": payload}
