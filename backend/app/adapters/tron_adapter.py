"""Tron Adapter (TRX/TRC20) - Non-EVM CanonicalEvent mapping (enhanced)

Fähigkeiten:
- TRX Transfers (Sun → TRX)
- TRC20 Transfer-Erkennung via Logs (Themenhash identisch zu ERC20)
- Adress-Normalisierung (Hex 41.. ↔ Base58Check T..)
- Robustes Timestamp-/Fee-Handling

Hinweis: Ohne echten Tron-Client werden Offline-Stubs genutzt.
"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List, List
from datetime import datetime
from decimal import Decimal

try:
    import base58  # type: ignore
    _BASE58_AVAILABLE = True
except Exception:  # pragma: no cover
    base58 = None  # type: ignore
    _BASE58_AVAILABLE = False

from app.schemas import CanonicalEvent
from app.services.multi_chain import ChainInfo, ChainType

logger = logging.getLogger(__name__)

# TRC20 Transfer topic (identisch zu ERC20 Transfer(address,address,uint256))
_TRC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def _ensure_hex_prefix(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    return s if s.startswith("0x") else ("0x" + s)


def tron_hex_to_base58(hex_addr: Optional[str]) -> Optional[str]:
    """Konvertiert Tron-Hexadresse (41 + 20 Bytes) → Base58Check (T...)

    Akzeptiert auch 0x-prefixed 20-Byte Adressen und fügt 0x41 Präfix hinzu.
    Fallback: Gibt None bei Fehler zurück.
    """
    try:
        if not hex_addr:
            return None
        h = str(hex_addr).lower().strip()
        if h.startswith("0x"):
            h = h[2:]
        # Wenn nur 20 Byte (40 Hex), Tron packt 0x41 Prefix (Version + AddressType)
        if len(h) == 40:
            h = "41" + h
        raw = bytes.fromhex(h)
        if not _BASE58_AVAILABLE:
            return None
        # base58 lib kann b58encode_check bereitstellen, sonst manuell checksum
        try:
            enc = base58.b58encode_check(raw)  # type: ignore[attr-defined]
            return enc.decode() if isinstance(enc, (bytes, bytearray)) else str(enc)
        except Exception:
            import hashlib
            chk = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
            enc = base58.b58encode(raw + chk)  # type: ignore[attr-defined]
            return enc.decode() if isinstance(enc, (bytes, bytearray)) else str(enc)
    except Exception:
        return None


def tron_base58_to_hex(b58_addr: Optional[str], with_prefix: bool = True) -> Optional[str]:
    """Konvertiert Base58Check T.. → Hex (41 + 20 Bytes), optional mit 0x Prefix."""
    try:
        if not b58_addr or not _BASE58_AVAILABLE:
            return None
        raw = base58.b58decode_check(b58_addr)  # type: ignore[attr-defined]
        hx = raw.hex()
        return ("0x" + hx) if with_prefix else hx
    except Exception:
        return None


def _ts_from_any(ts_val: Optional[int]) -> datetime:
    """Normalisiert Tron-Timestamps (ms oder s) zu datetime."""
    try:
        if ts_val is None:
            return datetime.utcnow()
        # Tron liefert häufig ms
        if ts_val > 10**12:
            return datetime.fromtimestamp(ts_val / 1000.0)
        return datetime.fromtimestamp(ts_val)
    except Exception:
        return datetime.utcnow()


def _extract_trc20_transfers(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extrahiert TRC20-Transfers (heuristisch) aus Tron Logs (receipt.log[].topics).

    Gibt Liste {token, from, to, amount} in best-effort zurück (Adressen Base58, Werte int/str).
    """
    transfers: List[Dict[str, Any]] = []
    for lg in logs or []:
        try:
            topics = lg.get("topics") or []
            if not topics:
                continue
            # Topics können als Hex ohne 0x vorliegen
            t0 = topics[0]
            t0s = str(t0)
            t0s = _ensure_hex_prefix(t0s).lower()
            if t0s != _TRC20_TRANSFER_TOPIC:
                continue
            token_hex = lg.get("address") or lg.get("contract_address")
            token = tron_hex_to_base58(_ensure_hex_prefix(str(token_hex))) or str(token_hex)
            frm_raw = str(topics[1]) if len(topics) > 1 else ""
            to_raw = str(topics[2]) if len(topics) > 2 else ""
            # letzten 20 Bytes der 32-Byte Topic laden
            def _tail20(x: str) -> str:
                xs = x.lower().replace("0x", "")
                return xs[-40:]
            frm = tron_hex_to_base58("0x" + _tail20(frm_raw)) or None
            to = tron_hex_to_base58("0x" + _tail20(to_raw)) or None
            # Amount im data-Feld (Hex)
            data = lg.get("data")
            amt = None
            if data is not None:
                try:
                    ds = str(data)
                    ds = ds[2:] if ds.startswith("0x") else ds
                    amt = int(ds, 16)
                except Exception:
                    amt = data
            transfers.append({"token": token, "from": frm, "to": to, "amount": amt})
        except Exception:
            continue
    return transfers


class TronAdapter:
    """Minimal Tron adapter to map TRX transfers to CanonicalEvent.
    Note: Uses offline-safe stubs unless a real client is provided.
    """

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or "mock://tron"
        self._client = None  # lazy (tronpy or http client)
        self._chain_name = "tron"
        # Minimal ChainInfo for factory compatibility
        self.chain_info = ChainInfo(
            chain_id="tron",
            name="Tron",
            symbol="TRX",
            chain_type=ChainType.EVM,  # reuse EVM routing bucket in factory
            rpc_urls=[self.api_url],
            block_explorer_url="https://tronscan.org",
            native_currency={"name": "Tron", "symbol": "TRX", "decimals": 6},
            features=["payments"]
        )
        logger.info(f"Initialized Tron adapter with API: {self.api_url}")

    @property
    def chain_name(self) -> str:
        return self._chain_name

    async def initialize(self):
        """Initialize underlying client (no-op for offline tests)."""
        logger.info("Tron adapter initialize() called")

    async def get_transaction(self, tx_id: str) -> Dict[str, Any]:
        if self._client is None:
            # Offline stub
            return {"txID": tx_id, "raw_data": {"contract": []}, "ret": [{"contractRet": "SUCCESS"}]}
        # Real client integration could go here (tronpy/http)
        raise NotImplementedError

    async def transform_transaction(self, raw_tx: Dict[str, Any], block_data: Dict[str, Any]) -> CanonicalEvent:
        """Transform Tron tx → CanonicalEvent (TRX + TRC20 best-effort)"""
        try:
            def _hash_str(hv: Any) -> str:
                try:
                    if hasattr(hv, 'hex'):
                        return hv.hex()
                except Exception:
                    pass
                return str(hv)

            tx_hash = _hash_str(raw_tx.get('hash') or raw_tx.get('txID') or "")

            # Blocknummer/Zeitstempel normalisieren (ms/s)
            blk_num = (
                block_data.get('number')
                or block_data.get('height')
                or block_data.get('block_number')
                or 0
            )
            ts_raw = (
                block_data.get('timestamp')
                or block_data.get('time')
                or block_data.get('block_time')
                or (block_data.get('block_header', {}).get('raw_data', {}).get('timestamp') if isinstance(block_data, dict) else None)
            )
            blk_ts = _ts_from_any(ts_raw if isinstance(ts_raw, int) else None)

            # Versuche, TRX-Transferfelder aus contract/value zu ziehen
            value_sun = raw_tx.get('value') or raw_tx.get('amount') or 0
            owner_b58 = raw_tx.get('owner_address') or raw_tx.get('from')
            to_b58 = raw_tx.get('to_address') or raw_tx.get('to')

            # Falls Adressen in Hex vorliegen, nach Base58 normalisieren
            from_address = owner_b58
            if from_address and isinstance(from_address, str) and from_address.lower().startswith(('0x', '41')):
                from_address = tron_hex_to_base58(from_address) or str(owner_b58)
            to_address = to_b58
            if to_address and isinstance(to_address, str) and to_address.lower().startswith(('0x', '41')):
                to_address = tron_hex_to_base58(to_address) or str(to_b58)

            # Fees/Energy best-effort
            fee = Decimal(0)
            gas_used: Optional[int] = None
            gas_price: Optional[int] = None
            try:
                receipt = raw_tx.get('receipt') or raw_tx.get('ret') or {}
                if isinstance(receipt, list) and receipt:
                    receipt0 = receipt[0]
                else:
                    receipt0 = receipt if isinstance(receipt, dict) else {}
                # energy usage
                gas_used = int(receipt0.get('energy_usage_total') or receipt0.get('energy_usage') or raw_tx.get('energy_used') or 0)
                # fee may be present as integer in Sun
                fee_val = receipt0.get('fee') or receipt0.get('net_fee') or 0
                if isinstance(fee_val, str):
                    try:
                        fee_val = int(fee_val, 16) if fee_val.startswith('0x') else int(fee_val)
                    except Exception:
                        fee_val = 0
                fee = Decimal(fee_val) / Decimal(10**6)
            except Exception:
                pass

            # Status bestimmen
            status = 1
            try:
                ret = raw_tx.get('ret')
                if isinstance(ret, list) and ret:
                    status = 1 if (ret[0].get('contractRet') or '').upper() == 'SUCCESS' else 0
                elif isinstance(ret, dict):
                    status = 1 if (ret.get('contractRet') or '').upper() == 'SUCCESS' else 0
            except Exception:
                pass

            # TRC20 Logs extrahieren (falls vorhanden)
            logs = []
            try:
                logs = raw_tx.get('log') or raw_tx.get('logs') or []
            except Exception:
                logs = []
            trc20 = _extract_trc20_transfers(logs if isinstance(logs, list) else [])

            # Event-Type bestimmen
            event_type = "transfer" if (value_sun or 0) > 0 else ("token_transfer" if trc20 else "contract_call")

            # Falls TRC20-Transfer vorhanden, versuche from/to aus Logs zu nehmen
            if trc20:
                first = trc20[0]
                from_address = first.get('from') or from_address
                to_address = first.get('to') or to_address

            event = CanonicalEvent(
                event_id=f"tron_tx_{tx_hash}",
                chain=self.chain_name,
                block_number=int(blk_num) if isinstance(blk_num, int) else 0,
                block_timestamp=blk_ts,
                tx_hash=tx_hash,
                tx_index=raw_tx.get('transactionIndex', 0),
                from_address=str(from_address) if from_address else "",
                to_address=str(to_address) if to_address else None,
                value=Decimal(value_sun or 0) / Decimal(10**6),  # Sun → TRX
                value_usd=None,
                gas_used=gas_used if isinstance(gas_used, int) else None,
                gas_price=gas_price,
                fee=fee,
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
                idempotency_key=f"tron_{int(blk_num) if isinstance(blk_num, int) else 0}_{raw_tx.get('transactionIndex', 0)}",
                source="rpc" if self._client else "api",
                metadata={
                    "trc20_transfers": trc20,
                }
            )
            return event
        except Exception as e:
            logger.error(f"Error transforming Tron tx: {e}")
            raise

    # Minimal API expected by MultiChain fallbacks
    async def get_block_height(self) -> int:
        return 0

    async def get_address_balance(self, address: str) -> float:
        """Return TRX balance (stubbed to 0.0 offline)."""
        return 0.0

    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Return recent transactions for address (stubbed empty)."""
        return []

    async def get_block_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        return []
