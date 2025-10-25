"""
Solana Blockchain Adapter

Full implementation for Solana blockchain:
- solana-py library integration
- RPC endpoint configuration  
- Transaction parsing for Solana format
- SPL Token transfers
- Program interactions
"""

import logging
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
from datetime import datetime
from decimal import Decimal
try:
    import base58  # type: ignore
    _BASE58_AVAILABLE = True
except Exception:
    base58 = None  # type: ignore
    _BASE58_AVAILABLE = False
from cachetools import TTLCache
from app.utils.jsonrpc import json_rpc

logger = logging.getLogger(__name__)

try:
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.types import TxOpts
    from solders.pubkey import Pubkey
    from solders.signature import Signature
    SOLANA_AVAILABLE = True
except ImportError:
    AsyncClient = None
    SOLANA_AVAILABLE = False
    logger.warning("solana-py not installed - Solana adapter will use placeholder mode")

from app.adapters.base import IChainAdapter
from app.schemas.canonical_event import CanonicalEvent
from app.config import settings
from app.observability.metrics import SOLANA_RPC_RETRIES, SOLANA_RPC_ERRORS

logger = logging.getLogger(__name__)


class SolanaAdapter(IChainAdapter):
    """
    Solana blockchain adapter
    
    **Features:**
    - SPL Token transfers
    - Program interactions
    - Account state changes
    
    **TODO:**
    - Install solana-py: pip install solana
    - Configure Solana RPC endpoint
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        self.chain_id = "solana-mainnet"
        self.rpc_url = rpc_url or getattr(settings, "SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        
        if SOLANA_AVAILABLE:
            self.client = AsyncClient(self.rpc_url)
            logger.info(f"Solana adapter initialized: {self.rpc_url}")
        else:
            self.client = None
            logger.warning("Solana adapter in placeholder mode - install solana-py for full functionality")
        
        # TTL cache for token account owner lookups (5 min TTL, max 10k)
        self._owner_cache: TTLCache[str, Optional[str]] = TTLCache(maxsize=10000, ttl=300)
        # Robustness configuration (configurable via settings)
        self._rpc_timeout: int = int(getattr(settings, "SOL_RPC_TIMEOUT_SECS", 20))
        self._max_retries: int = int(getattr(settings, "SOL_RPC_MAX_RETRIES", 5))
        self._base_delay: float = max(0.0, float(getattr(settings, "SOL_RPC_BASE_DELAY_MS", 250)) / 1000.0)
        self._max_delay: float = max(
            self._base_delay,
            float(getattr(settings, "SOL_RPC_MAX_DELAY_MS", 5000)) / 1000.0,
        )
    
    @property
    def chain_name(self) -> str:
        """Chain identifier for base interface compatibility"""
        return "solana"
    
    async def health(self) -> dict:
        """Lightweight health check using getSlot."""
        if not self.rpc_url:
            return {"chain": "solana", "status": "stub", "rpc": False}
        try:
            res = await self._rpc_call("getSlot", [])
            ok = "result" in res and isinstance(res["result"], int)
            return {"chain": "solana", "status": "ready" if ok else "beta", "rpc": True, "slot": res.get("result")}
        except Exception:
            return {"chain": "solana", "status": "beta", "rpc": True}
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Fetches Solana transaction by signature"""
        if not SOLANA_AVAILABLE or not self.client:
            logger.warning("Solana client not available")
            return None
        
        try:
            # Parse signature
            signature = Signature.from_string(tx_hash)
            
            # Fetch transaction
            response = await self.client.get_transaction(
                signature,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            
            if not response.value:
                logger.warning(f"Transaction not found: {tx_hash}")
                return None
            
            tx_data = response.value
            
            # Parse transaction data
            return self._parse_transaction(tx_data, tx_hash)
            
        except Exception as e:
            logger.error(f"Error fetching Solana transaction {tx_hash}: {e}")
            return None
    
    async def get_account_owner(self, pubkey: str) -> Optional[str]:
        """Return owner of a token account via getAccountInfo (jsonParsed)."""
        if not self.rpc_url:
            return None
        try:
            # cache first
            cached = self._owner_cache.get(pubkey)
            if cached is not None:
                return cached
            params = [
                pubkey,
                {"encoding": "jsonParsed", "commitment": "confirmed"},
            ]
            res = await self._rpc_call("getAccountInfo", params)
            acc = (res.get("result") or {}).get("value")
            if not acc:
                self._owner_cache[pubkey] = None
                return None
            data = acc.get("data", {})
            parsed = data.get("parsed", {})
            info = parsed.get("info", {})
            # For SPL token accounts, the owner field is the wallet owner
            owner = info.get("owner") or info.get("mintAuthority")
            # cache result (including None)
            self._owner_cache[pubkey] = owner
            return owner
        except Exception:
            return None
    
    async def get_block(self, slot: int) -> Dict:
        """
        Get Solana block
        
        Args:
            slot: Slot number
        
        Returns:
            Block dict or empty dict on failure
        """
        if not self.rpc_url:
            return {}
        try:
            params = [
                slot,
                {
                    "transactionDetails": "full",
                    "rewards": False,
                    "maxSupportedTransactionVersion": 0,
                    "commitment": "confirmed",
                },
            ]
            res = await self._rpc_call("getBlock", params)
            # Some RPCs return {"result": None} for not-yet-available slots
            result = res.get("result")
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"get_block error: {e}")
            return {}
    
    async def get_latest_block_number(self) -> int:
        """Return latest slot number (stub if no RPC)."""
        try:
            if not self.rpc_url:
                return 0
            res = await self._rpc_call("getSlot", [])
            return int(res.get("result") or 0)
        except Exception:
            return 0
    
    async def is_contract(self, address: str) -> bool:
        """Solana doesn't have EVM-style contracts; return False."""
        return False

    async def transform_transaction(self, raw_tx: dict, block_data: dict) -> CanonicalEvent:
        """Implements IChainAdapter.transform_transaction by delegating to to_canonical."""
        return await self.to_canonical(raw_tx)
    
    def is_valid_address(self, address: str) -> bool:
        """Validates Solana address format"""
        try:
            if SOLANA_AVAILABLE:
                # Use Solana library validation
                Pubkey.from_string(address)
                return True
            else:
                # Fallback: basic validation
                # Solana addresses are base58 encoded, 32-44 characters
                if not (32 <= len(address) <= 44):
                    return False
                # If base58 lib available, try to decode; otherwise simple alphabet check
                if _BASE58_AVAILABLE and base58 is not None:
                    base58.b58decode(address)  # type: ignore[attr-defined]
                    return True
                # Minimal base58 alphabet validation as fallback
                _alphabet = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
                return all(c in _alphabet for c in address)
        except:
            return False
    
    async def get_balance(self, address: str) -> Decimal:
        """Gets SOL balance for an address"""
        if not SOLANA_AVAILABLE or not self.client:
            return Decimal("0")
        
        try:
            pubkey = Pubkey.from_string(address)
            response = await self.client.get_balance(pubkey)
            
            if response.value is not None:
                # Convert lamports to SOL (1 SOL = 1e9 lamports)
                balance_sol = Decimal(response.value) / Decimal(10**9)
                return balance_sol
            
            return Decimal("0")
            
        except Exception as e:
            logger.error(f"Error fetching Solana balance: {e}")
            return Decimal("0")
    
    def stream_blocks(self, start_block: int, end_block: Optional[int] = None) -> AsyncGenerator[CanonicalEvent, None]:
        """Stream Solana blocks and yield CanonicalEvents for each transaction.
        - Tolerates missing/unavailable blocks (retries with backoff then skip)
        - Avoids hot-looping with a small sleep
        - Supports open-ended streaming if end_block is None (poll latest)
        """

        async def gen() -> AsyncGenerator[CanonicalEvent, None]:
            current = start_block
            # Resolve initial last if not provided
            last = end_block if end_block is not None else await self.get_latest_block_number()
            if last < current:
                last = current
            while True:
                # Break condition for bounded range
                if end_block is not None and current > last:
                    break
                # For open-ended streaming, refresh tail window
                if end_block is None and current > last:
                    # poll for new head
                    latest = await self.get_latest_block_number()
                    last = max(latest, last)
                    await asyncio.sleep(0.25)
                    continue

                retries = 0
                while retries < 3:
                    try:
                        blk = await self.get_block(current)
                        if not blk:
                            # Block not ready; backoff then retry
                            await asyncio.sleep(0.2 * (retries + 1))
                            retries += 1
                            continue
                        for tx in blk.get("transactions", []) or []:
                            try:
                                evt = await self.to_canonical(tx)
                                yield evt
                            except Exception:
                                continue
                        break  # processed block
                    except Exception:
                        await asyncio.sleep(0.2 * (retries + 1))
                        retries += 1
                # advance even if failed after retries, to avoid stall
                current += 1
                # light pacing to avoid tight loops
                await asyncio.sleep(0.05)

        return gen()
    
    # transform_transaction implemented above
    
    async def to_canonical(self, raw_tx: Dict) -> CanonicalEvent:
        """
        Convert Solana transaction to canonical format
        
        Args:
            raw_tx: Raw Solana transaction
        
        Returns:
            Canonical event
        """
        # Minimal mapping: we attempt to extract signature, slot, and basic parties if available.
        signature = raw_tx.get("transaction", {}).get("signatures", [None])[0] or raw_tx.get("signature", "")
        slot = raw_tx.get("slot") or 0
        block_time = raw_tx.get("blockTime")
        # From/To are non-trivial on Solana; as minimal placeholder, take first two accountKeys
        msg = (raw_tx.get("transaction", {}) or {}).get("message", {})
        acct_keys = msg.get("accountKeys", [])
        from_addr = acct_keys[0] if acct_keys else ""
        to_addr = acct_keys[1] if len(acct_keys) > 1 else ""

        # Compute value: use fee payer (account 0) pre/post balances difference as SOL delta (lamports -> SOL)
        meta = raw_tx.get("meta", {}) or {}
        pre_bal = meta.get("preBalances") or []
        post_bal = meta.get("postBalances") or []
        value_sol = "0"
        try:
            if pre_bal and post_bal and len(pre_bal) > 0 and len(post_bal) > 0:
                # fee payer at index 0
                delta_lamports = (post_bal[0] or 0) - (pre_bal[0] or 0)
                # Represent outgoing value as positive amount (absolute), convert lamports->SOL
                value_sol = str(abs(delta_lamports) / 1_000_000_000)
        except Exception:
            value_sol = "0"

        # Detect SPL token transfer via parsed instructions first
        event_type = "transfer"
        metadata = {}
        transfers = []  # aggregate list of detected token transfers
        try:
            # include top-level instructions as well as innerInstructions
            def iter_parsed_instructions():
                for ins in ((raw_tx.get("transaction", {}) or {}).get("message", {}) or {}).get("instructions", []) or []:
                    parsed = ins.get("parsed")
                    if parsed:
                        yield parsed
                for inner in (raw_tx.get("meta", {}) or {}).get("innerInstructions", []) or []:
                    for ins in inner.get("instructions", []) or []:
                        parsed = ins.get("parsed")
                        if parsed:
                            yield parsed

            for parsed in iter_parsed_instructions():
                info = parsed.get("info", {})
                typ = parsed.get("type")
                if typ in ("transfer", "transferChecked"):
                    # token program parsed transfer
                    mint = info.get("mint") or info.get("tokenAddress")
                    src = info.get("source") or info.get("owner") or info.get("authority")
                    dst = info.get("destination") or info.get("dest")
                    amt = info.get("tokenAmount", {}).get("uiAmount")
                    dec = info.get("tokenAmount", {}).get("decimals")
                    if mint and src and dst:
                        event_type = "token_transfer"
                        from_addr = src
                        to_addr = dst
                        transfers.append({
                            "mint": mint,
                            "from": src,
                            "to": dst,
                            "amount_ui": amt,
                            "decimals": dec,
                        })
                        metadata.update({
                            "token_mint": mint,
                            "from_owner": src,
                            "to_owner": dst,
                            "token_amount_ui": amt,
                            "token_decimals": dec,
                            "parsed": True,
                        })
        except Exception:
            # fall back to balance-diff method below
            pass

        # If not found via parsed, infer via pre/post token balances
        try:
            pre_tokens = meta.get("preTokenBalances") or []
            post_tokens = meta.get("postTokenBalances") or []
            # Build map: (owner, mint) -> amount (uiTokenAmount.amount as string lamports of token)
            def to_map(arr):
                m = {}
                for x in arr:
                    owner = x.get("owner") or ""
                    mint = x.get("mint") or ""
                    amt = ((x.get("uiTokenAmount") or {}).get("amount"))
                    try:
                        amt_val = int(amt) if amt is not None else 0
                    except Exception:
                        amt_val = 0
                    m[(owner, mint)] = m.get((owner, mint), 0) + amt_val
                return m
            pre_map = to_map(pre_tokens)
            post_map = to_map(post_tokens)
            # Find any mint with net change
            deltas = {}
            keys = set(pre_map.keys()) | set(post_map.keys())
            for k in keys:
                delta = (post_map.get(k, 0) - pre_map.get(k, 0))
                if delta != 0:
                    deltas[k] = delta
            if deltas and metadata.get("parsed") != True:
                # Choose first delta as primary token transfer indication
                (owner, mint), delta_amt = next(iter(deltas.items()))
                event_type = "token_transfer"
                # find decimals from pre/post entries for this (owner, mint)
                def find_decimals(arr, owner_s, mint_s):
                    for x in arr:
                        if (x.get("owner") or "") == owner_s and (x.get("mint") or "") == mint_s:
                            d = ((x.get("uiTokenAmount") or {}).get("decimals"))
                            if isinstance(d, int):
                                return d
                    return None
                decimals = find_decimals(post_tokens, owner, mint) or find_decimals(pre_tokens, owner, mint) or 0
                ui_amt = float(delta_amt) / (10 ** decimals) if decimals and decimals >= 0 else float(delta_amt)
                metadata = {
                    "token_mint": mint,
                    "owner": owner,
                    "token_delta_raw": delta_amt,
                    "token_decimals": decimals,
                    "token_delta_ui": ui_amt,
                }
                # Determine sender/receiver by aggregating deltas per owner for this mint
                owner_deltas: dict[str, int] = {}
                for (own, m), d in deltas.items():
                    if m == mint:
                        owner_deltas[own] = owner_deltas.get(own, 0) + d
                # sender: most negative; receiver: most positive
                if owner_deltas and metadata.get("parsed") != True:
                    sender = min(owner_deltas.items(), key=lambda kv: kv[1])[0]
                    receiver = max(owner_deltas.items(), key=lambda kv: kv[1])[0]
                    if owner_deltas.get(sender, 0) < 0:
                        from_addr = sender
                    if owner_deltas.get(receiver, 0) > 0:
                        to_addr = receiver
                    metadata.update({
                        "from_owner": from_addr,
                        "to_owner": to_addr,
                        "token_amount_ui": abs(ui_amt),
                    })
                    transfers.append({
                        "mint": mint,
                        "from": from_addr,
                        "to": to_addr,
                        "amount_ui": abs(ui_amt),
                        "decimals": decimals,
                    })
        except Exception:
            pass

        # Bridge detection via configured program IDs
        try:
            from app.config import settings as app_settings
            bridge_programs = set(getattr(app_settings, "BRIDGE_PROGRAMS_SOL", []) or [])
            if bridge_programs:
                # direct accountKeys scan
                keys_lower = {str(k).lower() for k in acct_keys or []}
                if any(p.lower() in keys_lower for p in bridge_programs):
                    event_type = "bridge"
                    metadata["bridge_program"] = next((p for p in bridge_programs if p.lower() in keys_lower), None)
                else:
                    # scan parsed instructions owner/program ids if present
                    parsed_any = False
                    for ins in ((raw_tx.get("transaction", {}) or {}).get("message", {}) or {}).get("instructions", []) or []:
                        pid = (ins.get("programId") or ins.get("programIdIndex") or "")
                        if isinstance(pid, str) and pid.lower() in {p.lower() for p in bridge_programs}:
                            event_type = "bridge"
                            metadata["bridge_program"] = pid
                            parsed_any = True
                            break
                    if not parsed_any:
                        for inner in (raw_tx.get("meta", {}) or {}).get("innerInstructions", []) or []:
                            for ins in inner.get("instructions", []) or []:
                                pid = (ins.get("programId") or ins.get("programIdIndex") or "")
                                if isinstance(pid, str) and pid.lower() in {p.lower() for p in bridge_programs}:
                                    event_type = "bridge"
                                    metadata["bridge_program"] = pid
                                    parsed_any = True
                                    break
                            if parsed_any:
                                break
        except Exception:
            pass

        if transfers and event_type != "bridge":
            # Aggregate same (mint, from, to)
            agg: dict[tuple[str, str, str], dict] = {}
            for t in transfers:
                key = (str(t.get("mint") or ""), str(t.get("from") or ""), str(t.get("to") or ""))
                if key not in agg:
                    agg[key] = {
                        "mint": str(t.get("mint") or ""),
                        "from": str(t.get("from") or ""),
                        "to": str(t.get("to") or ""),
                        "amount_ui": float(t.get("amount_ui") or 0),
                        "decimals": t.get("decimals"),
                    }
                else:
                    agg[key]["amount_ui"] += float(t.get("amount_ui") or 0)
            metadata["transfers"] = list(agg.values())

        # Try resolving token account owners for from/to if they look like token accounts (SPL)
        try:
            if event_type == "token_transfer":
                # only attempt if addresses are present and seem different from previously resolved owners
                if from_addr and (not metadata.get("from_owner") or metadata.get("from_owner") == from_addr):
                    resolved_from = await self.get_account_owner(from_addr)
                    if resolved_from:
                        metadata["from_owner"] = resolved_from
                if to_addr and (not metadata.get("to_owner") or metadata.get("to_owner") == to_addr):
                    resolved_to = await self.get_account_owner(to_addr)
                    if resolved_to:
                        metadata["to_owner"] = resolved_to
        except Exception:
            pass

        from decimal import Decimal
        status = 1
        try:
            if isinstance(meta, dict) and meta.get("err"):
                status = 0
        except Exception:
            status = 1

        return CanonicalEvent(
            event_id=f"sol_tx_{signature}",
            chain="solana",
            block_number=int(slot) if isinstance(slot, int) else 0,
            block_timestamp=(datetime.utcfromtimestamp(block_time) if isinstance(block_time, (int, float)) else datetime.utcnow()),
            tx_hash=signature or "",
            tx_index=0,
            from_address=from_addr,
            to_address=to_addr if to_addr else None,
            value=Decimal(str(value_sol)),
            value_usd=None,
            gas_used=None,
            gas_price=None,
            fee=None,
            status=status,
            error_message=None,
            event_type=event_type,
            contract_address=None,
            method_name=None,
            token_address=None,
            token_symbol=None,
            token_decimals=None,
            risk_score=None,
            cluster_id=None,
            cross_chain_links=[],
            labels=[],
            tags=[],
            source="rpc",
            idempotency_key=f"sol_{slot}_{signature}",
            metadata=metadata,
        )

    async def _rpc_call(self, method: str, params: list, *, ttl: float = 10.0, no_cache: bool = False) -> Dict:
        if not self.rpc_url:
            return {}
        attempts = 0
        delay = self._base_delay
        last_exc: Optional[Exception] = None
        while attempts < self._max_retries:
            try:
                return await json_rpc(
                    self.rpc_url,
                    method,
                    params,
                    None,
                    None,
                    timeout=self._rpc_timeout,
                    no_cache=no_cache,
                    ttl=ttl,
                )
            except Exception as e:
                # Classify common transient conditions
                msg = str(e).lower()
                transient = (
                    "timeout" in msg
                    or "temporarily" in msg
                    or "connection" in msg
                    or "http 429" in msg
                    or "too many requests" in msg
                    or "http 5" in msg  # any 5xx
                    or "url error" in msg
                )
                last_exc = e
                attempts += 1
                try:
                    SOLANA_RPC_RETRIES.labels(method=method).inc()
                except Exception:
                    pass
                await asyncio.sleep(delay)
                delay *= 2
        if last_exc:
            try:
                SOLANA_RPC_ERRORS.labels(method=method).inc()
            except Exception:
                pass
            raise last_exc
        return {}



# Factory function
def create_solana_adapter(rpc_url: str = "https://api.mainnet-beta.solana.com") -> SolanaAdapter:
    """Create Solana adapter instance"""
    return SolanaAdapter(rpc_url)
