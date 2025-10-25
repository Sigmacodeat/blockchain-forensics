"""
Bitcoin Adapter (Full UTXO Implementation)
JSON-RPC based UTXO tracing with heuristics:
- Change detection
- Co-spending (multi-input) clustering
- CoinJoin detection
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from decimal import Decimal
from app.utils.jsonrpc import json_rpc
from app.config import settings
from app.schemas import CanonicalEvent
from app.adapters.base import IChainAdapter


class BitcoinAdapter(IChainAdapter):
    def __init__(self, rpc_url: Optional[str] = None, rpc_user: Optional[str] = None, rpc_password: Optional[str] = None):
        self.rpc_url = rpc_url or getattr(settings, "BITCOIN_RPC_URL", None)
        self.rpc_user = rpc_user or getattr(settings, "BITCOIN_RPC_USER", None)
        self.rpc_password = rpc_password or getattr(settings, "BITCOIN_RPC_PASSWORD", None)

    @property
    def chain_name(self) -> str:
        """Chain identifier for Bitcoin"""
        return "bitcoin"

    async def health(self) -> Dict[str, Any]:
        if not self.rpc_url:
            return {"chain": "bitcoin", "status": "stub", "rpc": False}
        try:
            # Simple ping: getblockcount
            rpc_url: str = str(self.rpc_url)
            res = await json_rpc(rpc_url, "getblockcount", [], self.rpc_user, self.rpc_password)
            ok = "result" in res and isinstance(res["result"], int)
            return {"chain": "bitcoin", "status": "ready" if ok else "beta", "rpc": True, "height": res.get("result")}
        except Exception:
            return {"chain": "bitcoin", "status": "beta", "rpc": True}

    async def fetch_block(self, height: int) -> Dict[str, Any]:
        """Fetch and lightly normalize a block (verbosity=2 returns tx details)"""
        if not self.rpc_url:
            return {"height": height, "tx_count": 0, "status": "no_rpc"}
        # getblockhash -> getblock
        rpc_url: str = str(self.rpc_url)
        h = await json_rpc(rpc_url, "getblockhash", [height], self.rpc_user, self.rpc_password)
        block_hash = h.get("result")
        blk = await json_rpc(rpc_url, "getblock", [block_hash, 2], self.rpc_user, self.rpc_password)
        b = blk.get("result", {})
        return {
            "height": b.get("height", height),
            "hash": b.get("hash"),
            "time": b.get("time"),
            "tx_count": len(b.get("tx", [])),
            "raw": b,
            "status": "ok",
        }

    async def trace_utxo(self, txid: str) -> List[Dict[str, Any]]:
        """Trace UTXO flows for a given transaction.
        Returns a list of edges: { from: {txid, vout}, to: {txid, vout}, value }
        """
        # If no RPC configured, return empty best-effort
        if not self.rpc_url:
            return []
        # Fetch and normalize transaction
        raw = await self.fetch_tx(txid)
        if not raw or raw.get("txid") != txid:
            return []
        # Build proportional edges (default method)
        try:
            edges_res = await self.build_tx_edges(raw, method="proportional")
            return edges_res.get("edges", [])
        except Exception:
            return []

    async def fetch_tx(self, txid: str) -> Dict[str, Any]:
        """Fetch and decode a Bitcoin transaction via getrawtransaction (verbose)."""
        if not self.rpc_url:
            return {"txid": txid, "status": "no_rpc"}
        rpc_url: str = str(self.rpc_url)
        res = await json_rpc(rpc_url, "getrawtransaction", [txid, True], self.rpc_user, self.rpc_password)
        return res.get("result", {})

    def normalize_tx(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight normalized view of a decoded transaction."""
        vouts = []
        for o in tx.get("vout", []):
            spk = o.get("scriptPubKey", {})
            addrs = spk.get("addresses") or ([spk.get("address")] if spk.get("address") else [])
            vouts.append({
                "n": o.get("n"),
                "value": o.get("value"),
                "addresses": addrs,
                "type": spk.get("type"),
            })

        vins = []
        for i in tx.get("vin", []):
            vins.append({
                "txid": i.get("txid"),
                "vout": i.get("vout"),
                "coinbase": i.get("coinbase"),
                "sequence": i.get("sequence"),
            })

        return {
            "txid": tx.get("txid"),
            "size": tx.get("size"),
            "version": tx.get("version"),
            "locktime": tx.get("locktime"),
            "vin": vins,
            "vout": vouts,
        }

    async def _fetch_prev_output_value(self, txid: str, vout_index: int) -> Optional[float]:
        """Fetch previous transaction and return the value of the referenced output (in BTC)."""
        try:
            rpc_url: str = str(self.rpc_url)
            prev = await json_rpc(rpc_url, "getrawtransaction", [txid, True], self.rpc_user, self.rpc_password)
            prev_tx = prev.get("result", {})
            outs = prev_tx.get("vout", [])
            for o in outs:
                if o.get("n") == vout_index:
                    return o.get("value")
        except Exception:
            return None
        return None

    async def _fetch_prev_output_addresses(self, txid: str, vout_index: int) -> List[str]:
        """Fetch addresses for a referenced previous output (if available)."""
        try:
            rpc_url: str = str(self.rpc_url)
            prev = await json_rpc(rpc_url, "getrawtransaction", [txid, True], self.rpc_user, self.rpc_password)
            prev_tx = prev.get("result", {})
            outs = prev_tx.get("vout", [])
            for o in outs:
                if o.get("n") == vout_index:
                    spk = o.get("scriptPubKey", {})
                    addrs = spk.get("addresses") or ([spk.get("address")] if spk.get("address") else [])
                    return [a for a in addrs if a]
        except Exception:
            return []
        return []

    async def build_tx_edges(self, tx: Dict[str, Any], method: str = "proportional") -> Dict[str, Any]:
        """Compute basic UTXO flow edges by distributing each input value proportionally across outputs.
        Requires fetching previous tx outputs to get input values.
        """
        txid = tx.get("txid")
        vins = tx.get("vin", [])
        vouts = tx.get("vout", [])

        # Collect output values and total
        out_values = []  # list of (n, value)
        total_out = 0.0
        for o in vouts:
            n = o.get("n")
            val = float(o.get("value", 0.0) or 0.0)
            out_values.append((n, val))
            total_out += val

        # Edge list
        edges: List[Dict[str, Any]] = []

        # Prepare input totals and (optionally) input addresses
        input_values: List[float] = []
        input_addresses: List[str] = []
        for vin in vins:
            prev_txid = vin.get("txid")
            prev_vout = vin.get("vout")
            if prev_txid is None or prev_vout is None:
                # coinbase or unknown; skip value distribution
                continue
            in_value = await self._fetch_prev_output_value(prev_txid, prev_vout)
            if in_value is None:
                continue
            input_values.append(in_value)
            # collect input addresses for heuristic change detection
            addrs = await self._fetch_prev_output_addresses(prev_txid, prev_vout)
            input_addresses.extend(addrs)

        input_total = sum(input_values)
        fee = max(0.0, input_total - total_out) if input_values else 0.0

        # Heuristic change detection: output address intersects input addresses
        change_vout_index: Optional[int] = None
        if method == "heuristic" and input_addresses:
            input_addr_set = set(input_addresses)
            for o in vouts:
                spk = o.get("scriptPubKey", {})
                addrs = spk.get("addresses") or ([spk.get("address")] if spk.get("address") else [])
                for a in addrs or []:
                    if a in input_addr_set:
                        change_vout_index = o.get("n")
                        break
                if change_vout_index is not None:
                    break

        # Determine distribution outputs
        dist_out_values = [(n, val) for (n, val) in out_values if change_vout_index is None or n != change_vout_index]
        dist_total = sum(val for (_, val) in dist_out_values) or total_out

        # For each input, distribute to selected outputs
        for vin in vins:
            prev_txid = vin.get("txid")
            prev_vout = vin.get("vout")
            if prev_txid is None or prev_vout is None:
                continue
            in_value = await self._fetch_prev_output_value(prev_txid, prev_vout)
            if in_value is None or dist_total == 0:
                continue
            for n, out_val in dist_out_values:
                if out_val <= 0:
                    continue
                proportion = out_val / dist_total
                edge_val = in_value * proportion
                edges.append({
                    "from": {"txid": prev_txid, "vout": prev_vout},
                    "to": {"txid": txid, "vout": n},
                    "value": edge_val,
                })

        return {"txid": txid, "edges": edges, "fee": fee, "method": method}

    def detect_change_output(self, tx: Dict[str, Any], input_addresses: List[str]) -> Optional[int]:
        """
        Heuristic: Change output is the one that shares an address with inputs.
        Returns the vout index of the likely change output, or None.
        """
        if not input_addresses:
            return None
        
        input_addr_set = set(input_addresses)
        vouts = tx.get("vout", [])
        
        for o in vouts:
            spk = o.get("scriptPubKey", {})
            addrs = spk.get("addresses") or ([spk.get("address")] if spk.get("address") else [])
            for a in addrs or []:
                if a in input_addr_set:
                    return o.get("n")
        
        return None

    def detect_coinjoin(self, tx: Dict[str, Any]) -> bool:
        """
        Heuristic: CoinJoin transactions have many inputs and outputs with similar values.
        Simple check: >= 3 inputs, >= 3 outputs, and at least 2 outputs have equal values.
        """
        vins = tx.get("vin", [])
        vouts = tx.get("vout", [])
        
        # Need sufficient mixing
        if len(vins) < 3 or len(vouts) < 3:
            return False
        
        # Check for equal-value outputs
        values = [float(o.get("value", 0.0) or 0.0) for o in vouts]
        value_counts = {}
        for v in values:
            if v > 0:
                # Round to avoid floating point issues
                rounded = round(v, 8)
                value_counts[rounded] = value_counts.get(rounded, 0) + 1
        
        # If any value appears >= 2 times, likely CoinJoin
        for count in value_counts.values():
            if count >= 2:
                return True
        
        return False

    def extract_co_spend_addresses(self, tx: Dict[str, Any], input_addresses: List[str]) -> List[str]:
        """
        Multi-input heuristic: All inputs in the same transaction are likely controlled by the same entity.
        Returns the list of unique addresses from inputs (co-spending evidence).
        """
        return list(set(input_addresses))

    async def get_block(self, block_number: int) -> dict:
        """Fetch raw block data (implements IChainAdapter)"""
        return await self.fetch_block(block_number)

    async def get_transaction(self, tx_hash: str) -> dict:
        """Fetch raw transaction data (implements IChainAdapter)"""
        return await self.fetch_tx(tx_hash)

    async def get_latest_block_number(self) -> int:
        """Get latest block number"""
        if not self.rpc_url:
            return 0
        rpc_url: str = str(self.rpc_url)
        res = await json_rpc(rpc_url, "getblockcount", [], self.rpc_user, self.rpc_password)
        return res.get("result", 0)

    async def is_contract(self, address: str) -> bool:
        """Bitcoin doesn't have contracts in the Ethereum sense"""
        return False

    async def transform_transaction(self, raw_tx: dict, block_data: dict) -> CanonicalEvent:
        """
        Transform Bitcoin transaction to CanonicalEvent.
        UTXO model: each transaction consumes inputs and creates outputs.
        For CanonicalEvent, we create one event per UTXO flow (input -> output).
        
        For simplicity, we'll create a summary event representing the main transfer,
        and store full UTXO details in metadata.
        """
        txid = raw_tx.get("txid", "")
        vins = raw_tx.get("vin", [])
        vouts = raw_tx.get("vout", [])
        
        # Collect input addresses and values
        input_addresses: List[str] = []
        input_total = 0.0
        
        for vin in vins:
            if vin.get("coinbase"):
                # Coinbase transaction
                continue
            prev_txid = vin.get("txid")
            prev_vout = vin.get("vout")
            if prev_txid and prev_vout is not None:
                addrs = await self._fetch_prev_output_addresses(prev_txid, prev_vout)
                input_addresses.extend(addrs)
                val = await self._fetch_prev_output_value(prev_txid, prev_vout)
                if val:
                    input_total += val
        
        # Collect output addresses and values
        output_addresses: List[str] = []
        output_total = 0.0
        
        for vout in vouts:
            spk = vout.get("scriptPubKey", {})
            addrs = spk.get("addresses") or ([spk.get("address")] if spk.get("address") else [])
            output_addresses.extend([a for a in addrs if a])
            val = float(vout.get("value", 0.0) or 0.0)
            output_total += val
        
        # Fee calculation
        fee = max(0.0, input_total - output_total)
        
        # Heuristics
        change_vout = self.detect_change_output(raw_tx, input_addresses)
        is_coinjoin = self.detect_coinjoin(raw_tx)
        co_spend_addrs = self.extract_co_spend_addresses(raw_tx, input_addresses)
        
        # Determine primary from/to addresses
        from_address = input_addresses[0] if input_addresses else "coinbase"
        # To address: first non-change output
        to_address = None
        main_value = 0.0
        
        for vout in vouts:
            if change_vout is not None and vout.get("n") == change_vout:
                continue
            spk = vout.get("scriptPubKey", {})
            addrs = spk.get("addresses") or ([spk.get("address")] if spk.get("address") else [])
            if addrs:
                to_address = addrs[0]
                main_value = float(vout.get("value", 0.0) or 0.0)
                break
        
        if not to_address and output_addresses:
            to_address = output_addresses[0]
            main_value = output_total
        
        # Block info
        block_number = block_data.get("height", 0)
        block_hash = block_data.get("hash", "")
        block_time = block_data.get("time", 0)
        block_timestamp = datetime.utcfromtimestamp(block_time) if block_time else datetime.utcnow()
        
        # Build metadata with UTXO details
        metadata = {
            "bitcoin": {
                "txid": txid,
                "inputs": [
                    {
                        "txid": vin.get("txid"),
                        "vout": vin.get("vout"),
                        "coinbase": vin.get("coinbase"),
                        "addresses": []  # We'd need to fetch these
                    }
                    for vin in vins
                ],
                "outputs": [
                    {
                        "n": vout.get("n"),
                        "value": float(vout.get("value", 0.0) or 0.0),
                        "addresses": (vout.get("scriptPubKey", {}).get("addresses") or 
                                     ([vout.get("scriptPubKey", {}).get("address")] 
                                      if vout.get("scriptPubKey", {}).get("address") else [])),
                        "type": vout.get("scriptPubKey", {}).get("type")
                    }
                    for vout in vouts
                ],
                "change_vout": change_vout,
                "is_coinjoin": is_coinjoin,
                "co_spend_addresses": co_spend_addrs,
                "fee": fee
            }
        }
        
        # Generate idempotency key
        idempotency_key = f"btc_{block_number}_{txid}"
        
        # Create CanonicalEvent
        return CanonicalEvent(
            event_id=f"btc_tx_{txid}",
            chain="bitcoin",
            block_number=block_number,
            block_timestamp=block_timestamp,
            tx_hash=txid,
            tx_index=0,  # Bitcoin doesn't have tx_index like Ethereum
            from_address=from_address,
            to_address=to_address,
            value=Decimal(str(main_value)),
            value_usd=None,  # Would need price oracle
            gas_used=None,
            gas_price=None,
            fee=Decimal(str(fee)),
            status=1,  # Bitcoin transactions are always valid once mined
            error_message=None,
            event_type="transfer" if not is_coinjoin else "coinjoin",
            contract_address=None,
            method_name=None,
            token_address=None,
            token_symbol="BTC",
            token_decimals=8,
            risk_score=None,
            cluster_id=None,
            cross_chain_links=[],
            labels=[],
            tags=["coinjoin"] if is_coinjoin else [],
            source="rpc",
            idempotency_key=idempotency_key,
            metadata=metadata
        )

    async def stream_blocks(
        self,
        start_block: int,
        end_block: Optional[int] = None
    ) -> AsyncGenerator[CanonicalEvent, None]:
        """
        Stream transactions from blocks as Canonical Events.
        For Bitcoin, this iterates through blocks and yields events for each transaction.
        """
        current_block = start_block
        latest_block = end_block if end_block is not None else await self.get_latest_block_number()
        
        while current_block <= latest_block:
            try:
                block_data = await self.get_block(current_block)
                raw_block = block_data.get("raw", {})
                
                for raw_tx in raw_block.get("tx", []):
                    try:
                        event = await self.transform_transaction(raw_tx, block_data)
                        yield event
                    except Exception as e:
                        # Log error but continue
                        print(f"Error transforming tx {raw_tx.get('txid')}: {e}")
                        continue
                
                current_block += 1
            except Exception as e:
                print(f"Error fetching block {current_block}: {e}")
                current_block += 1
                continue
