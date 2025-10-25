"""
EVM Decoder API
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
import time

from app.enrichment.abi_decoder import decode_input, abi_decoder
from app.observability.metrics import CHAIN_REQUESTS, CHAIN_LATENCY

router = APIRouter()


class DecodeInputRequest(BaseModel):
    input: str = Field(..., description="EVM input data (0x-prefixed)")


@router.post("/decode/input", summary="Decode EVM input data")
async def evm_decode_input(payload: DecodeInputRequest = Body(...)) -> Dict[str, Any]:
    op = "decode_input"
    chain = "ethereum"
    t0 = time.time()
    try:
        res = decode_input(payload.input)
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
        return {"decoded": res}
    except Exception as e:
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - t0)


class DecodeLogsRequest(BaseModel):
    logs: List[Dict[str, Any]] = Field(..., description="Array of log objects with topics/data/address")


@router.post("/decode/logs", summary="Decode EVM logs")
async def evm_decode_logs(payload: DecodeLogsRequest = Body(...)) -> Dict[str, Any]:
    op = "decode_logs"
    chain = "ethereum"
    t0 = time.time()
    try:
        out: List[Dict[str, Any]] = []
        for lg in payload.logs:
            try:
                ev = abi_decoder.decode_log(lg)
                if ev:
                    out.append(ev)
            except Exception:
                continue
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="ok").inc()
        return {"decoded": out}
    except Exception as e:
        CHAIN_REQUESTS.labels(chain=chain, op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        CHAIN_LATENCY.labels(chain=chain, op=op).observe(time.time() - t0)
