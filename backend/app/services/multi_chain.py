"""
Multi-Chain Support für Blockchain Forensics
============================================

Unterstützung für 50+ Chains mit einheitlicher API:
- Ethereum & EVM-kompatible Chains
- Bitcoin & UTXO-basierte Chains
- Solana, Cosmos, Polkadot
- Layer 2 Solutions
- Cross-Chain Bridges
"""

import logging
import os
import asyncio
from typing import Dict, List, Optional, Any, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from time import monotonic

logger = logging.getLogger(__name__)
try:
    from app.services.cache_service import cache_service
except Exception:
    cache_service = None  # type: ignore
try:
    from app.observability.metrics import CHAIN_REQUESTS, CHAIN_LATENCY, BRIDGE_EVENTS
except Exception:
    CHAIN_REQUESTS = None  # type: ignore
    CHAIN_LATENCY = None  # type: ignore
    BRIDGE_EVENTS = None  # type: ignore
try:
    # Lightweight ABI-less decoding for common bridge events
    from app.services.evm_log_decoder import decode_bridge_log
except Exception:
    decode_bridge_log = None  # type: ignore
try:
    from app.services.price_service import price_service
except Exception:
    price_service = None  # type: ignore


class ChainType(str, Enum):
    """Chain-Typ Klassifikation"""
    EVM = "evm"                    # Ethereum Virtual Machine
    UTXO = "utxo"                  # Unspent Transaction Output
    SVM = "svm"                    # Solana Virtual Machine
    COSMOS = "cosmos"             # Cosmos SDK
    POLKADOT = "polkadot"         # Substrate/Polkadot
    LAYER2 = "layer2"             # Layer 2 Solutions


@dataclass
class ChainInfo:
    """Informationen über eine Blockchain"""
    chain_id: str
    name: str
    symbol: str
    chain_type: ChainType
    rpc_urls: List[str]
    block_explorer_url: Optional[str] = None
    native_currency: Dict[str, Any] = None
    features: List[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.native_currency is None:
            self.native_currency = {"name": self.symbol, "symbol": self.symbol, "decimals": 18}


class IChainAdapter(Protocol):
    """Interface für Chain-Adapter"""

    async def get_block_height(self) -> int:
        """Aktuelle Blockhöhe"""
        ...

    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Transaktion abrufen"""
        ...

    async def get_address_balance(self, address: str) -> float:
        """Adresse-Balance abrufen"""
        ...

    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Transaktionen einer Adresse abrufen"""
        ...

    async def get_block_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """Transaktionen eines Blocks abrufen"""
        ...


class BaseChainAdapter(ABC):
    """Basis-Adapter für alle Chains"""

    def __init__(self, chain_info: ChainInfo):
        self.chain_info = chain_info
        self.session = None

    @abstractmethod
    async def initialize(self):
        """Adapter initialisieren"""
        pass

    @abstractmethod
    async def get_block_height(self) -> int:
        """Aktuelle Blockhöhe"""
        pass

    async def make_request(self, method: str, params: List = None) -> Dict[str, Any]:
        """Generische RPC-Anfrage"""
        # Basis-Implementierung für HTTP-RPC mit Retry/Backoff/Timeout
        import aiohttp

        if not self.session:
            self.session = aiohttp.ClientSession()

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }

        try:
            max_retries = int(os.getenv("RPC_MAX_RETRIES", "3"))
        except Exception:
            max_retries = 3
        try:
            backoff_base = float(os.getenv("RPC_BACKOFF_BASE", "0.5"))
        except Exception:
            backoff_base = 0.5
        try:
            request_timeout = float(os.getenv("RPC_REQUEST_TIMEOUT", "15"))
        except Exception:
            request_timeout = 15.0

        last_error: Optional[Exception] = None
        for rpc_url in self.chain_info.rpc_urls:
            for attempt in range(max_retries + 1):
                try:
                    timeout = aiohttp.ClientTimeout(total=request_timeout)
                    async with self.session.post(rpc_url, json=payload, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.json()
                        # Retry bei 429/5xx
                        if response.status in (429, 500, 502, 503, 504):
                            body = await response.text()
                            logger.warning(f"RPC {rpc_url} status {response.status} attempt {attempt}: {body}")
                        else:
                            logger.warning(f"RPC request failed for {rpc_url}: {response.status}")
                            break
                except Exception as e:
                    last_error = e
                    logger.warning(f"RPC request error {rpc_url} attempt {attempt}: {e}")

                # Backoff wenn weiterer Versuch folgt
                if attempt < max_retries:
                    delay = backoff_base * (2 ** attempt)
                    await asyncio.sleep(delay)
            # Nächsten RPC-Endpoint probieren

        raise Exception(f"All RPC endpoints failed for chain {self.chain_info.chain_id}: {last_error}")


class EthereumAdapter(BaseChainAdapter):
    """Adapter für Ethereum und EVM-kompatible Chains"""

    async def initialize(self):
        """Ethereum-Adapter initialisieren"""
        logger.info(f"Initializing Ethereum adapter for {self.chain_info.name}")

    async def get_block_height(self) -> int:
        """Aktuelle Blockhöhe"""
        response = await self.make_request("eth_blockNumber")
        return int(response["result"], 16)

    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Transaktion abrufen"""
        response = await self.make_request("eth_getTransactionByHash", [tx_hash])
        tx_data = response.get("result")

        if not tx_data:
            return None

        # Normalisiere Daten
        return {
            "tx_hash": tx_hash,
            "block_number": int(tx_data["blockNumber"], 16),
            "from_address": tx_data["from"],
            "to_address": tx_data.get("to"),
            "value": int(tx_data["value"], 16) / 1e18,  # Wei to ETH
            "gas_price": int(tx_data["gasPrice"], 16) / 1e9,  # Gwei
            "gas_used": int(tx_data.get("gas", "0x0"), 16),
            "timestamp": await self._get_block_timestamp(int(tx_data["blockNumber"], 16)),
            "chain": self.chain_info.chain_id,
            "chain_type": "evm"
        }

    async def get_address_balance(self, address: str) -> float:
        """Adresse-Balance abrufen"""
        response = await self.make_request("eth_getBalance", [address, "latest"])
        balance_wei = int(response["result"], 16)
        return balance_wei / 1e18  # Wei to ETH

    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Transaktionen einer Adresse abrufen"""
        # Strategie: Jüngste Blöcke rückwärts scannen und Transaktionen filtern,
        # bis 'limit' erreicht ist. Dies vermeidet externe Explorer-APIs.
        # Hinweis: Für große Limits ist dies kostenintensiv; daher Kappung.
        transactions: List[Dict[str, Any]] = []
        try:
            latest_block = await self.get_block_height()
        except Exception as e:
            logger.error(f"Failed to get latest block for {self.chain_info.chain_id}: {e}")
            return transactions

        # Maximal zu scannende Blöcke, um RPC-Last zu begrenzen (konfigurierbar)
        try:
            max_blocks = int(os.getenv("ETH_SCAN_MAX_BLOCKS", "2000"))
        except Exception:
            max_blocks = 2000
        scanned = 0
        target = limit

        # Normalisiere Adresse in lowercase
        target_addr = address.lower()

        block_number = latest_block
        while block_number >= 0 and scanned < max_blocks and len(transactions) < target:
            try:
                resp = await self.make_request("eth_getBlockByNumber", [hex(block_number), True])
                block = resp.get("result")
                if block and block.get("transactions"):
                    for tx_data in block["transactions"]:
                        # Filter auf from/to
                        from_addr = (tx_data.get("from") or "").lower()
                        to_addr = (tx_data.get("to") or "").lower()
                        if from_addr == target_addr or to_addr == target_addr:
                            tx = await self.get_transaction(tx_data["hash"])  # normalisierte Form
                            if tx:
                                transactions.append(tx)
                                if len(transactions) >= target:
                                    break
                scanned += 1
                block_number -= 1
            except Exception as e:
                logger.warning(f"Error scanning block {block_number} on {self.chain_info.chain_id}: {e}")
                scanned += 1
                block_number -= 1

        return transactions

    async def get_block_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """Transaktionen eines Blocks abrufen"""
        response = await self.make_request("eth_getBlockByNumber", [hex(block_number), True])
        block_data = response.get("result", {})

        if not block_data or not block_data.get("transactions"):
            return []

        transactions = []
        for tx_data in block_data["transactions"]:
            tx = await self.get_transaction(tx_data["hash"])
            if tx:
                transactions.append(tx)

        return transactions

    async def _get_block_timestamp(self, block_number: int) -> int:
        """Block-Timestamp abrufen"""
        response = await self.make_request("eth_getBlockByNumber", [hex(block_number), False])
        block_data = response.get("result", {})
        return int(block_data.get("timestamp", "0x0"), 16)

    async def get_address_transactions_in_range(self, address: str, from_block: int, to_block: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Adresse-TXs in Blockbereich [from_block, to_block] sammeln (EVM)."""
        results: List[Dict[str, Any]] = []
        target_addr = address.lower()
        if from_block > to_block:
            from_block, to_block = to_block, from_block
        current = to_block
        while current >= from_block and len(results) < limit:
            try:
                resp = await self.make_request("eth_getBlockByNumber", [hex(current), True])
                block = resp.get("result")
                if block and block.get("transactions"):
                    for tx_data in block["transactions"]:
                        if len(results) >= limit:
                            break
                        from_addr = (tx_data.get("from") or "").lower()
                        to_addr = (tx_data.get("to") or "").lower()
                        if from_addr == target_addr or to_addr == target_addr:
                            tx = await self.get_transaction(tx_data["hash"])
                            if tx:
                                results.append(tx)
                current -= 1
            except Exception as e:
                logger.warning(f"Range scan error block {current} {self.chain_info.chain_id}: {e}")
                current -= 1
        return results

    async def get_address_transactions_paged(self, address: str, limit: int = 100, start_height: Optional[int] = None, end_height: Optional[int] = None) -> List[Dict[str, Any]]:
        """Paginierte Adress-TXs (UTXO); nutzt Range-Helper, wenn Höhen-Grenzen übergeben wurden."""
        if start_height is not None and end_height is not None:
            return await self.get_address_transactions_in_range(address, start_height, end_height, limit)
        return await self.get_address_transactions(address, limit)

    async def get_address_transactions_paged(self, address: str, limit: int = 100, start_height: Optional[int] = None, end_height: Optional[int] = None) -> List[Dict[str, Any]]:
        """Paginierte Adress-TXs; nutzt Range-Helper, wenn Höhen-Grenzen übergeben wurden."""
        if start_height is not None and end_height is not None:
            return await self.get_address_transactions_in_range(address, start_height, end_height, limit)
        return await self.get_address_transactions(address, limit)

    async def get_address_transactions_paged(self, address: str, limit: int = 100, from_block: Optional[int] = None, to_block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Paginierte Adress-TXs; nutzt Range-Helper, wenn Blockgrenzen übergeben wurden."""
        if from_block is not None and to_block is not None:
            return await self.get_address_transactions_in_range(address, from_block, to_block, limit)
        # Fallback: Standard-Scan wie get_address_transactions
        return await self.get_address_transactions(address, limit)

    async def estimate_block_range_for_time(self, start_time: int, end_time: int, max_scan: int = 5000) -> Optional[Dict[str, int]]:
        """
        Grobe Abschätzung des Blockbereichs (from_block, to_block) für ein Zeitfenster.
        Rückwärts iterativ, begrenzt durch max_scan, um RPC-Last zu vermeiden.
        """
        try:
            latest = await self.get_block_height()
        except Exception as e:
            logger.error(f"Cannot get latest block for range estimation on {self.chain_info.chain_id}: {e}")
            return None

        to_block = latest
        # Rückwärts bis wir vor start_time sind oder max_scan erreicht
        scanned = 0
        from_block = max(0, latest - 1)

        while from_block >= 0 and scanned < max_scan:
            try:
                ts = await self._get_block_timestamp(from_block)
                if ts <= start_time:
                    break
                from_block -= 1
                scanned += 1
            except Exception as e:
                logger.warning(f"Timestamp check failed for block {from_block} on {self.chain_info.chain_id}: {e}")
                from_block -= 1
                scanned += 1

        # Korrigiere obere Grenze basierend auf end_time (optional)
        scanned_up = 0
        while to_block >= 0 and scanned_up < max_scan:
            try:
                ts = await self._get_block_timestamp(to_block)
                if ts <= end_time:
                    break
                to_block -= 1
                scanned_up += 1
            except Exception as e:
                logger.warning(f"Timestamp check failed for block {to_block} on {self.chain_info.chain_id}: {e}")
                to_block -= 1
                scanned_up += 1

        if to_block < from_block:
            to_block = from_block
        return {"from_block": from_block, "to_block": to_block}


class BSCAdapter(EthereumAdapter):
    """Adapter für Binance Smart Chain (EVM)"""

    async def initialize(self):
        logger.info(f"Initializing BSC adapter for {self.chain_info.name}")


class AvalancheAdapter(EthereumAdapter):
    """Adapter für Avalanche C-Chain (EVM)"""

    async def initialize(self):
        logger.info(f"Initializing Avalanche adapter for {self.chain_info.name}")


class BitcoinAdapter(BaseChainAdapter):
    """Adapter für Bitcoin und UTXO-basierte Chains"""

    async def initialize(self):
        """Bitcoin-Adapter initialisieren"""
        logger.info(f"Initializing Bitcoin adapter for {self.chain_info.name}")

    async def get_block_height(self) -> int:
        """Aktuelle Blockhöhe"""
        # Bitcoin Core RPC
        response = await self.make_request("getblockcount")
        return response["result"]

    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Transaktion abrufen"""
        response = await self.make_request("getrawtransaction", [tx_hash, True])

        if "error" in response:
            return None

        tx_data = response["result"]

        # Normalisiere Bitcoin-Daten
        return {
            "tx_hash": tx_hash,
            "block_height": tx_data.get("height"),
            "inputs": len(tx_data.get("vin", [])),
            "outputs": len(tx_data.get("vout", [])),
            "total_input": sum(inp.get("value", 0) for inp in tx_data.get("vin", [])),
            "total_output": sum(out.get("value", 0) for out in tx_data.get("vout", [])),
            "timestamp": tx_data.get("time"),
            "chain": self.chain_info.chain_id,
            "chain_type": "utxo"
        }

    async def get_address_balance(self, address: str) -> float:
        """Adresse-Balance abrufen"""
        response = await self.make_request("getaddressbalance", [{"addresses": [address]}])
        return response["result"].get("balance", 0) / 100000000  # Satoshi to BTC

    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Transaktionen einer Adresse abrufen"""
        results: List[Dict[str, Any]] = []
        try:
            tip_resp = await self.make_request("getblockcount")
            latest_height = tip_resp["result"]
        except Exception as e:
            logger.error(f"Failed to get latest height for {self.chain_info.chain_id}: {e}")
            return results

        try:
            max_blocks = int(os.getenv("BTC_SCAN_MAX_BLOCKS", "2000"))
        except Exception:
            max_blocks = 2000
        scanned = 0
        height = latest_height

        while height >= 0 and scanned < max_blocks and len(results) < limit:
            try:
                hsh_resp = await self.make_request("getblockhash", [height])
                block_hash = hsh_resp["result"]
                blk_resp = await self.make_request("getblock", [block_hash, 2])
                block = blk_resp.get("result", {})
                for tx in block.get("tx", []):
                    if len(results) >= limit:
                        break
                    matched = False
                    for vout in tx.get("vout", []):
                        spk = vout.get("scriptPubKey", {})
                        addrs = spk.get("addresses") or []
                        if address in addrs:
                            matched = True
                            break
                    if matched:
                        results.append({
                            "tx_hash": tx.get("txid"),
                            "block_height": height,
                            "inputs": len(tx.get("vin", [])),
                            "outputs": len(tx.get("vout", [])),
                            "timestamp": block.get("time"),
                            "chain": self.chain_info.chain_id,
                            "chain_type": "utxo"
                        })
                scanned += 1
                height -= 1
            except Exception as e:
                logger.warning(f"Error scanning block {height} on {self.chain_info.chain_id}: {e}")
                scanned += 1
                height -= 1

        return results

    async def get_block_transactions(self, block_height: int) -> List[Dict[str, Any]]:
        """Transaktionen eines Blocks abrufen"""
        response = await self.make_request("getblockhash", [block_height])
        block_hash = response["result"]

        response = await self.make_request("getblock", [block_hash, 2])  # Verbosity 2 für Transaktionen
        block_data = response["result"]

        transactions = []
        for tx_id in block_data.get("tx", []):
            tx = await self.get_transaction(tx_id)
            if tx:
                transactions.append(tx)

        return transactions

    async def get_address_transactions_in_range(self, address: str, start_height: int, end_height: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Adresse-TXs in Blockhöhe [start_height, end_height] sammeln (UTXO)."""
        results: List[Dict[str, Any]] = []
        lo = min(start_height, end_height)
        hi = max(start_height, end_height)
        h = hi
        while h >= lo and len(results) < limit:
            try:
                hsh_resp = await self.make_request("getblockhash", [h])
                block_hash = hsh_resp["result"]
                blk_resp = await self.make_request("getblock", [block_hash, 2])
                block = blk_resp.get("result", {})
                for tx in block.get("tx", []):
                    if len(results) >= limit:
                        break
                    matched = False
                    for vout in tx.get("vout", []):
                        spk = vout.get("scriptPubKey", {})
                        addrs = spk.get("addresses") or []
                        if address in addrs:
                            matched = True
                            break
                    if matched:
                        results.append({
                            "tx_hash": tx.get("txid"),
                            "block_height": h,
                            "inputs": len(tx.get("vin", [])),
                            "outputs": len(tx.get("vout", [])),
                            "timestamp": block.get("time"),
                            "chain": self.chain_info.chain_id,
                            "chain_type": "utxo"
                        })
                h -= 1
            except Exception as e:
                logger.warning(f"Range scan error block {h} {self.chain_info.chain_id}: {e}")
                h -= 1
        return results

    async def get_address_transactions_paged(self, address: str, limit: int = 100, start_height: Optional[int] = None, end_height: Optional[int] = None) -> List[Dict[str, Any]]:
        """Paginierte Adress-TXs; nutzt Range-Helper, wenn Höhen-Grenzen übergeben wurden."""
        if start_height is not None and end_height is not None:
            return await self.get_address_transactions_in_range(address, start_height, end_height, limit)
        return await self.get_address_transactions(address, limit)


class SolanaAdapter(BaseChainAdapter):
    """Adapter für Solana"""

    async def initialize(self):
        """Solana-Adapter initialisieren"""
        logger.info(f"Initializing Solana adapter for {self.chain_info.name}")

    async def get_block_height(self) -> int:
        """Aktuelle Slot-Höhe"""
        response = await self.make_request("getSlot")
        return response["result"]

    async def get_transaction(self, tx_signature: str) -> Optional[Dict[str, Any]]:
        """Transaktion abrufen"""
        response = await self.make_request("getTransaction", [tx_signature, "json"])

        if "error" in response:
            return None

        tx_data = response["result"]

        return {
            "tx_signature": tx_signature,
            "slot": tx_data.get("slot"),
            "block_time": tx_data.get("blockTime"),
            "fee": tx_data.get("meta", {}).get("fee", 0) / 1e9,  # Lamports to SOL
            "compute_units": tx_data.get("meta", {}).get("computeUnitsConsumed"),
            "chain": self.chain_info.chain_id,
            "chain_type": "svm"
        }

    async def get_address_balance(self, address: str) -> float:
        """Adresse-Balance abrufen"""
        response = await self.make_request("getBalance", [address])
        return response["result"] / 1e9  # Lamports to SOL

    async def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Transaktionen einer Adresse abrufen"""
        response = await self.make_request("getSignaturesForAddress", [address, {"limit": limit}])
        signatures = response["result"]

        transactions = []
        for sig_data in signatures:
            tx = await self.get_transaction(sig_data["signature"])
            if tx:
                transactions.append(tx)

        return transactions

    async def get_block_transactions(self, slot: int) -> List[Dict[str, Any]]:
        """Transaktionen eines Slots abrufen"""
        response = await self.make_request("getBlock", [slot, {"encoding": "json", "transactionDetails": "full"}])
        block_data = response["result"]

        transactions = []
        for tx_data in block_data.get("transactions", []):
            # Solana-spezifische Verarbeitung
            tx_signature = tx_data.get("transaction", {}).get("signatures", [""])[0]
            tx = await self.get_transaction(tx_signature)
            if tx:
                transactions.append(tx)

        return transactions


class ChainAdapterFactory:
    """Factory für Chain-Adapter"""

    def __init__(self):
        self.adapters: Dict[str, BaseChainAdapter] = {}
        self.chain_registry = self._build_chain_registry()

    def _build_chain_registry(self) -> Dict[str, ChainInfo]:
        """Erstellt Registry aller unterstützten Chains"""
        # Lazy import settings to avoid hard dependency during tests
        try:
            from app.config import settings  # type: ignore
        except Exception:
            settings = None  # type: ignore

        def _cfg(name: str, default: Optional[str] = None) -> Optional[str]:
            try:
                return getattr(settings, name) if settings is not None else default
            except Exception:
                return default

        return {
            # Ethereum & EVM-kompatible
            "ethereum": ChainInfo(
                chain_id="ethereum",
                name="Ethereum",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[
                    url for url in [
                        _cfg("ETHEREUM_RPC_URL", None),
                        "https://eth-mainnet.g.alchemy.com/v2/demo",
                        "https://rpc.ankr.com/eth",
                    ] if url
                ],
                block_explorer_url="https://etherscan.io",
                native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
                features=["smart_contracts", "defi", "nft", "layer2"]
            ),
            "base": ChainInfo(
                chain_id="base",
                name="Base",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("BASE_RPC_URL", None), "https://mainnet.base.org"] if url],
                block_explorer_url="https://basescan.org",
                features=["layer2", "op_stack"]
            ),
            "gnosis": ChainInfo(
                chain_id="gnosis",
                name="Gnosis Chain",
                symbol="xDAI",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("GNOSIS_RPC_URL", None), "https://rpc.gnosischain.com"] if url],
                block_explorer_url="https://gnosisscan.io",
                features=["payments", "pos"]
            ),
            "linea": ChainInfo(
                chain_id="linea",
                name="Linea",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("LINEA_RPC_URL", None), "https://rpc.linea.build"] if url],
                block_explorer_url="https://lineascan.build",
                features=["zk_rollup"]
            ),
            "scroll": ChainInfo(
                chain_id="scroll",
                name="Scroll",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("SCROLL_RPC_URL", None), "https://rpc.scroll.io"] if url],
                block_explorer_url="https://scrollscan.com",
                features=["zk_rollup"]
            ),
            "zksync": ChainInfo(
                chain_id="zksync",
                name="zkSync Era",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("ZKSYNC_RPC_URL", None), "https://mainnet.era.zksync.io"] if url],
                block_explorer_url="https://explorer.zksync.io",
                features=["zk_rollup"]
            ),
            "mantle": ChainInfo(
                chain_id="mantle",
                name="Mantle",
                symbol="MNT",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("MANTLE_RPC_URL", None), "https://rpc.mantle.xyz"] if url],
                block_explorer_url="https://mantlescan.info",
                features=["layer2"]
            ),
            "blast": ChainInfo(
                chain_id="blast",
                name="Blast",
                symbol="BLAST",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("BLAST_RPC_URL", None), "https://rpc.blast.io"] if url],
                block_explorer_url="https://blastscan.io",
                features=["layer2"]
            ),
            "polygon": ChainInfo(
                chain_id="polygon",
                name="Polygon",
                symbol="MATIC",
                chain_type=ChainType.EVM,
                rpc_urls=[
                    url for url in [
                        _cfg("POLYGON_RPC_URL", None),
                        "https://polygon-rpc.com",
                        "https://rpc-mainnet.matic.network",
                    ] if url
                ],
                block_explorer_url="https://polygonscan.com",
                features=["layer2", "pos"]
            ),
            "bsc": ChainInfo(
                chain_id="bsc",
                name="Binance Smart Chain",
                symbol="BNB",
                chain_type=ChainType.EVM,
                rpc_urls=[
                    url for url in [
                        _cfg("ARBITRARY_BSC_RPC_URL", None),  # optional override if configured
                        "https://bsc-dataseed.binance.org",
                        "https://bsc-dataseed1.binance.org",
                    ] if url
                ],
                block_explorer_url="https://bscscan.com",
                features=["defi", "exchange"]
            ),
            "arbitrum": ChainInfo(
                chain_id="arbitrum",
                name="Arbitrum",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("ARBITRUM_RPC_URL", None), "https://arb1.arbitrum.io/rpc"] if url],
                block_explorer_url="https://arbiscan.io",
                features=["layer2", "optimistic_rollup"]
            ),
            "optimism": ChainInfo(
                chain_id="optimism",
                name="Optimism",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("OPTIMISM_RPC_URL", None), "https://mainnet.optimism.io"] if url],
                block_explorer_url="https://optimistic.etherscan.io",
                features=["layer2", "optimistic_rollup"]
            ),

            # Bitcoin & UTXO
            "bitcoin": ChainInfo(
                chain_id="bitcoin",
                name="Bitcoin",
                symbol="BTC",
                chain_type=ChainType.UTXO,
                rpc_urls=[url for url in [_cfg("BITCOIN_RPC_URL", None)] if url] or ["https://btc-node.example.com"],
                block_explorer_url="https://blockchain.com/explorer",
                native_currency={"name": "Bitcoin", "symbol": "BTC", "decimals": 8},
                features=["utxo", "proof_of_work"]
            ),

            # Solana
            "solana": ChainInfo(
                chain_id="solana",
                name="Solana",
                symbol="SOL",
                chain_type=ChainType.SVM,
                rpc_urls=[url for url in [_cfg("SOLANA_RPC_URL", None), "https://api.mainnet-beta.solana.com"] if url],
                block_explorer_url="https://solscan.io",
                native_currency={"name": "Solana", "symbol": "SOL", "decimals": 9},
                features=["high_throughput", "proof_of_history"]
            ),
            "tron": ChainInfo(
                chain_id="tron",
                name="Tron",
                symbol="TRX",
                chain_type=ChainType.EVM,  # route via EVM branch with explicit adapter mapping
                rpc_urls=[url for url in [_cfg("TRON_API_URL", None), "https://api.trongrid.io"] if url],
                block_explorer_url="https://tronscan.org",
                native_currency={"name": "Tron", "symbol": "TRX", "decimals": 6},
                features=["payments"]
            ),

            # Weitere wichtige Chains (vereinfacht)
            "avalanche": ChainInfo(
                chain_id="avalanche",
                name="Avalanche",
                symbol="AVAX",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("AVALANCHE_RPC_URL", None), "https://api.avax.network/ext/bc/C/rpc"] if url],
                features=["subnet", "defi"]
            ),
            "fantom": ChainInfo(
                chain_id="fantom",
                name="Fantom",
                symbol="FTM",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("FANTOM_RPC_URL", None), "https://rpc.ftm.tools"] if url],
                block_explorer_url="https://ftmscan.com",
                native_currency={"name": "Fantom", "symbol": "FTM", "decimals": 18},
                features=["defi", "fast_finality"]
            ),
            "gnosis-chiado": ChainInfo(
                chain_id="gnosis-chiado",
                name="Gnosis Chiado",
                symbol="xDAI",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("GNOSIS_CHIADO_RPC_URL", None)] if url],
                features=["testnet"]
            ),
            "litecoin": ChainInfo(
                chain_id="litecoin",
                name="Litecoin",
                symbol="LTC",
                chain_type=ChainType.UTXO,
                rpc_urls=[url for url in [_cfg("LITECOIN_RPC_URL", None)] if url] or ["https://ltc-node.example.com"],
                block_explorer_url="https://litecoinspace.org/",
                native_currency={"name": "Litecoin", "symbol": "LTC", "decimals": 8},
                features=["utxo", "pow"]
            ),
            "bitcoin-cash": ChainInfo(
                chain_id="bitcoin-cash",
                name="Bitcoin Cash",
                symbol="BCH",
                chain_type=ChainType.UTXO,
                rpc_urls=[url for url in [_cfg("BITCOIN_CASH_RPC_URL", None)] if url] or ["https://bch-node.example.com"],
                block_explorer_url="https://blockchair.com/bitcoin-cash",
                native_currency={"name": "Bitcoin Cash", "symbol": "BCH", "decimals": 8},
                features=["utxo", "pow"]
            ),
            "zcash": ChainInfo(
                chain_id="zcash",
                name="Zcash",
                symbol="ZEC",
                chain_type=ChainType.UTXO,
                rpc_urls=[url for url in [_cfg("ZCASH_RPC_URL", None)] if url] or ["https://zec-node.example.com"],
                block_explorer_url="https://zcashblockexplorer.com/",
                native_currency={"name": "Zcash", "symbol": "ZEC", "decimals": 8},
                features=["utxo", "shielded"]
            ),
            
            # Additional EVM-compatible chains
            "celo": ChainInfo(
                chain_id="celo",
                name="Celo",
                symbol="CELO",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("CELO_RPC_URL", None), "https://forno.celo.org"] if url],
                block_explorer_url="https://celoscan.io",
                native_currency={"name": "Celo", "symbol": "CELO", "decimals": 18},
                features=["mobile_payments", "stable_coins"]
            ),
            "moonbeam": ChainInfo(
                chain_id="moonbeam",
                name="Moonbeam",
                symbol="GLMR",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("MOONBEAM_RPC_URL", None), "https://rpc.api.moonbeam.network"] if url],
                block_explorer_url="https://moonscan.io",
                native_currency={"name": "Glimmer", "symbol": "GLMR", "decimals": 18},
                features=["polkadot_parachain", "cross_chain"]
            ),
            "aurora": ChainInfo(
                chain_id="aurora",
                name="Aurora",
                symbol="ETH",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("AURORA_RPC_URL", None), "https://mainnet.aurora.dev"] if url],
                block_explorer_url="https://aurorascan.dev",
                native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
                features=["near_protocol", "low_fees"]
            ),
            
            # Layer 2 - Cairo VM
            "starknet": ChainInfo(
                chain_id="starknet",
                name="Starknet",
                symbol="ETH",
                chain_type=ChainType.LAYER2,
                rpc_urls=[url for url in [_cfg("STARKNET_RPC_URL", None), "https://starknet-mainnet.public.blastapi.io"] if url],
                block_explorer_url="https://starkscan.co",
                native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
                features=["zk_rollup", "cairo_vm"]
            ),
            
            # Non-EVM chains
            "cardano": ChainInfo(
                chain_id="cardano",
                name="Cardano",
                symbol="ADA",
                chain_type=ChainType.UTXO,
                rpc_urls=[url for url in [_cfg("CARDANO_RPC_URL", None), "https://cardano-mainnet.blockfrost.io/api/v0"] if url],
                block_explorer_url="https://cardanoscan.io",
                native_currency={"name": "Cardano", "symbol": "ADA", "decimals": 6},
                features=["proof_of_stake", "eutxo", "smart_contracts"]
            ),
            "near": ChainInfo(
                chain_id="near",
                name="NEAR Protocol",
                symbol="NEAR",
                chain_type=ChainType.COSMOS,
                rpc_urls=[url for url in [_cfg("NEAR_RPC_URL", None), "https://rpc.mainnet.near.org"] if url],
                block_explorer_url="https://nearblocks.io",
                native_currency={"name": "NEAR", "symbol": "NEAR", "decimals": 24},
                features=["sharding", "proof_of_stake"]
            ),
            "sui": ChainInfo(
                chain_id="sui",
                name="Sui",
                symbol="SUI",
                chain_type=ChainType.COSMOS,
                rpc_urls=[url for url in [_cfg("SUI_RPC_URL", None), "https://fullnode.mainnet.sui.io"] if url],
                block_explorer_url="https://suiexplorer.com",
                native_currency={"name": "Sui", "symbol": "SUI", "decimals": 9},
                features=["move_vm", "object_centric"]
            ),
            "aptos": ChainInfo(
                chain_id="aptos",
                name="Aptos",
                symbol="APT",
                chain_type=ChainType.COSMOS,
                rpc_urls=[url for url in [_cfg("APTOS_RPC_URL", None), "https://fullnode.mainnet.aptoslabs.com/v1"] if url],
                block_explorer_url="https://explorer.aptoslabs.com",
                native_currency={"name": "Aptos", "symbol": "APT", "decimals": 8},
                features=["move_vm", "parallel_execution"]
            ),
            
            # Privacy Coins (Critical for Chainalysis parity)
            "monero": ChainInfo(
                chain_id="monero",
                name="Monero",
                symbol="XMR",
                chain_type=ChainType.UTXO,
                rpc_urls=[url for url in [_cfg("MONERO_RPC_URL", None)] if url] or ["https://xmr-node.example.com"],
                block_explorer_url="https://xmrchain.net",
                native_currency={"name": "Monero", "symbol": "XMR", "decimals": 12},
                features=["privacy", "ring_signatures", "stealth_addresses"]
            ),
            
            # Cosmos Ecosystem
            "cosmos": ChainInfo(
                chain_id="cosmos",
                name="Cosmos Hub",
                symbol="ATOM",
                chain_type=ChainType.COSMOS,
                rpc_urls=[url for url in [_cfg("COSMOS_RPC_URL", None), "https://cosmos-rpc.polkachu.com"] if url],
                block_explorer_url="https://www.mintscan.io/cosmos",
                native_currency={"name": "Cosmos", "symbol": "ATOM", "decimals": 6},
                features=["ibc", "proof_of_stake", "cross_chain"]
            ),
            "osmosis": ChainInfo(
                chain_id="osmosis",
                name="Osmosis",
                symbol="OSMO",
                chain_type=ChainType.COSMOS,
                rpc_urls=[url for url in [_cfg("OSMOSIS_RPC_URL", None), "https://rpc.osmosis.zone"] if url],
                block_explorer_url="https://www.mintscan.io/osmosis",
                native_currency={"name": "Osmosis", "symbol": "OSMO", "decimals": 6},
                features=["dex", "amm", "ibc"]
            ),
            
            # Polkadot Ecosystem
            "polkadot": ChainInfo(
                chain_id="polkadot",
                name="Polkadot",
                symbol="DOT",
                chain_type=ChainType.POLKADOT,
                rpc_urls=[url for url in [_cfg("POLKADOT_RPC_URL", None), "https://rpc.polkadot.io"] if url],
                block_explorer_url="https://polkadot.subscan.io",
                native_currency={"name": "Polkadot", "symbol": "DOT", "decimals": 10},
                features=["relay_chain", "parachains", "cross_chain"]
            ),
            "kusama": ChainInfo(
                chain_id="kusama",
                name="Kusama",
                symbol="KSM",
                chain_type=ChainType.POLKADOT,
                rpc_urls=[url for url in [_cfg("KUSAMA_RPC_URL", None), "https://kusama-rpc.polkadot.io"] if url],
                block_explorer_url="https://kusama.subscan.io",
                native_currency={"name": "Kusama", "symbol": "KSM", "decimals": 12},
                features=["canary_network", "parachains"]
            ),
            
            # Additional Major L1s
            "cronos": ChainInfo(
                chain_id="cronos",
                name="Cronos",
                symbol="CRO",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("CRONOS_RPC_URL", None), "https://evm.cronos.org"] if url],
                block_explorer_url="https://cronoscan.com",
                native_currency={"name": "Cronos", "symbol": "CRO", "decimals": 18},
                features=["cosmos_sdk", "evm_compatible", "defi"]
            ),
            "klaytn": ChainInfo(
                chain_id="klaytn",
                name="Klaytn",
                symbol="KLAY",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("KLAYTN_RPC_URL", None), "https://public-node-api.klaytnapi.com/v1/cypress"] if url],
                block_explorer_url="https://scope.klaytn.com",
                native_currency={"name": "Klaytn", "symbol": "KLAY", "decimals": 18},
                features=["enterprise", "metaverse"]
            ),
            "harmony": ChainInfo(
                chain_id="harmony",
                name="Harmony",
                symbol="ONE",
                chain_type=ChainType.EVM,
                rpc_urls=[url for url in [_cfg("HARMONY_RPC_URL", None), "https://api.harmony.one"] if url],
                block_explorer_url="https://explorer.harmony.one",
                native_currency={"name": "Harmony", "symbol": "ONE", "decimals": 18},
                features=["sharding", "fast_finality"]
            ),
            
            # Layer 2 Extensions
            "polygon-zkevm": ChainInfo(
                chain_id="polygon-zkevm",
                name="Polygon zkEVM",
                symbol="ETH",
                chain_type=ChainType.LAYER2,
                rpc_urls=[url for url in [_cfg("POLYGON_ZKEVM_RPC_URL", None), "https://zkevm-rpc.com"] if url],
                block_explorer_url="https://zkevm.polygonscan.com",
                native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
                features=["zk_rollup", "evm_equivalent"]
            ),
            "arbitrum-nova": ChainInfo(
                chain_id="arbitrum-nova",
                name="Arbitrum Nova",
                symbol="ETH",
                chain_type=ChainType.LAYER2,
                rpc_urls=[url for url in [_cfg("ARBITRUM_NOVA_RPC_URL", None), "https://nova.arbitrum.io/rpc"] if url],
                block_explorer_url="https://nova.arbiscan.io",
                native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
                features=["gaming", "social", "anytrust_da"]
            ),
            "boba": ChainInfo(
                chain_id="boba",
                name="Boba Network",
                symbol="ETH",
                chain_type=ChainType.LAYER2,
                rpc_urls=[url for url in [_cfg("BOBA_RPC_URL", None), "https://mainnet.boba.network"] if url],
                block_explorer_url="https://bobascan.com",
                native_currency={"name": "Ethereum", "symbol": "ETH", "decimals": 18},
                features=["optimistic_rollup", "hybrid_compute"]
            ),
            
            # Emerging Chains (2024-2025)
            "sei": ChainInfo(
                chain_id="sei",
                name="Sei Network",
                symbol="SEI",
                chain_type=ChainType.COSMOS,
                rpc_urls=[url for url in [_cfg("SEI_RPC_URL", None), "https://rpc.sei-apis.com"] if url],
                block_explorer_url="https://www.seiscan.app",
                native_currency={"name": "Sei", "symbol": "SEI", "decimals": 6},
                features=["orderbook", "trading_optimized"]
            ),
            "celestia": ChainInfo(
                chain_id="celestia",
                name="Celestia",
                symbol="TIA",
                chain_type=ChainType.COSMOS,
                rpc_urls=[url for url in [_cfg("CELESTIA_RPC_URL", None)] if url] or ["https://rpc.celestia.pops.one"],
                block_explorer_url="https://celenium.io",
                native_currency={"name": "Celestia", "symbol": "TIA", "decimals": 6},
                features=["modular_blockchain", "data_availability"]
            ),
        }

    def get_adapter(self, chain_id: str) -> Optional[BaseChainAdapter]:
        """Gibt Adapter für Chain zurück"""
        if chain_id in self.adapters:
            return self.adapters[chain_id]

        chain_info = self.chain_registry.get(chain_id)
        if not chain_info:
            logger.error(f"Unsupported chain: {chain_id}")
            return None

        # Erstelle Adapter basierend auf Chain-Typ / spezifischer Chain
        if chain_info.chain_type == ChainType.EVM:
            if chain_info.chain_id == "bsc":
                adapter = BSCAdapter(chain_info)
            elif chain_info.chain_id == "avalanche":
                adapter = AvalancheAdapter(chain_info)
            elif chain_info.chain_id == "fantom":
                from app.adapters.fantom_adapter import FantomAdapter
                adapter = FantomAdapter()
            elif chain_info.chain_id == "celo":
                from app.adapters.celo_adapter import CeloAdapter
                adapter = CeloAdapter()
            elif chain_info.chain_id == "gnosis":
                from app.adapters.gnosis_adapter import GnosisAdapter
                adapter = GnosisAdapter()
            elif chain_info.chain_id == "tron":
                from app.adapters.tron_adapter import TronAdapter
                adapter = TronAdapter()
            elif chain_info.chain_id == "zksync":
                from app.adapters.zksync_adapter import ZkSyncAdapter
                adapter = ZkSyncAdapter()
            elif chain_info.chain_id == "scroll":
                from app.adapters.scroll_adapter import ScrollAdapter
                adapter = ScrollAdapter()
            elif chain_info.chain_id == "linea":
                from app.adapters.linea_adapter import LineaAdapter
                adapter = LineaAdapter()
            elif chain_info.chain_id == "moonbeam":
                from app.adapters.moonbeam_adapter import MoonbeamAdapter
                adapter = MoonbeamAdapter()
            elif chain_info.chain_id == "aurora":
                from app.adapters.aurora_adapter import AuroraAdapter
                adapter = AuroraAdapter()
            else:
                adapter = EthereumAdapter(chain_info)
        elif chain_info.chain_type == ChainType.UTXO:
            if chain_info.chain_id == "cardano":
                from app.adapters.cardano_adapter import CardanoAdapter
                adapter = CardanoAdapter()
            else:
                adapter = BitcoinAdapter(chain_info)
        elif chain_info.chain_type == ChainType.SVM:
            adapter = SolanaAdapter(chain_info)
        elif chain_info.chain_type == ChainType.LAYER2:
            if chain_info.chain_id == "starknet":
                from app.adapters.starknet_adapter import StarknetAdapter
                adapter = StarknetAdapter()
            else:
                # Fallback to EVM for other L2s
                adapter = EthereumAdapter(chain_info)
        elif chain_info.chain_type == ChainType.COSMOS:
            # Non-EVM chains: Near, Sui, Aptos
            if chain_info.chain_id == "near":
                from app.adapters.near_adapter import NearAdapter
                adapter = NearAdapter()
            elif chain_info.chain_id == "sui":
                from app.adapters.sui_adapter import SuiAdapter
                adapter = SuiAdapter()
            elif chain_info.chain_id == "aptos":
                from app.adapters.aptos_adapter import AptosAdapter
                adapter = AptosAdapter()
            else:
                logger.error(f"Unsupported COSMOS-type chain: {chain_info.chain_id}")
                return None
        else:
            logger.error(f"Unsupported chain type: {chain_info.chain_type}")
            return None

        # Initialisiere Adapter
        asyncio.create_task(adapter.initialize())
        self.adapters[chain_id] = adapter

        return adapter

    def get_supported_chains(self) -> List[ChainInfo]:
        """Gibt Liste aller unterstützten Chains zurück"""
        return list(self.chain_registry.values())

    def get_chains_by_type(self, chain_type: ChainType) -> List[ChainInfo]:
        """Gibt Chains nach Typ zurück"""
        return [chain for chain in self.chain_registry.values() if chain.chain_type == chain_type]


class MultiChainForensics:
    """Multi-Chain Forensik-Engine"""

    def __init__(self):
        self.adapter_factory = ChainAdapterFactory()
        self.active_chains = set()
        # Asynchron zusätzliche EVM-Chains nachladen (best-effort)
        try:
            asyncio.create_task(self.adapter_factory.load_extra_evm(limit=50))
        except Exception:
            pass

    async def initialize_chains(self, chain_ids: List[str]):
        """Initialisiert mehrere Chains"""
        for chain_id in chain_ids:
            adapter = self.adapter_factory.get_adapter(chain_id)
            if adapter:
                self.active_chains.add(chain_id)
                logger.info(f"Initialized chain: {chain_id}")

    async def cross_chain_analysis(self, addresses: List[str]) -> Dict[str, Any]:
        """Cross-Chain-Analyse für Adressen"""
        results = {}

        for address in addresses:
            chain_activities = {}

            for chain_id in self.active_chains:
                adapter = self.adapter_factory.get_adapter(chain_id)
                if adapter:
                    try:
                        balance = await adapter.get_address_balance(address)
                        tx_count = len(await adapter.get_address_transactions(address, limit=10))

                        if balance > 0 or tx_count > 0:
                            chain_activities[chain_id] = {
                                "balance": balance,
                                "tx_count": tx_count,
                                "chain_info": adapter.chain_info
                            }
                    except Exception as e:
                        logger.error(f"Error analyzing {address} on {chain_id}: {e}")

            if chain_activities:
                results[address] = {
                    "active_chains": len(chain_activities),
                    "total_balance_usd": await self._calculate_total_balance(chain_activities),
                    "chain_activities": chain_activities
                }

        return results

    async def _calculate_total_balance(self, chain_activities: Dict) -> float:
        """Berechnet Gesamtbalance über alle Chains"""
        # Vereinfacht - echte Implementierung würde Preis-Feeds verwenden
        total = 0
        for chain_id, activity in chain_activities.items():
            # Platzhalter-Preise
            prices = {
                "ethereum": 2000,  # $2000 pro ETH
                "polygon": 1,      # $1 pro MATIC
                "bsc": 300,        # $300 pro BNB
                "solana": 100      # $100 pro SOL
            }
            price = prices.get(chain_id, 1)
            total += activity["balance"] * price

        return total

    async def get_address_transactions_paged(self, chain_id: str, address: str, limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """
        Paginierte Adress-Transaktionen über Chains hinweg.
        EVM erwartet optional: from_block, to_block
        UTXO erwartet optional: start_height, end_height
        """
        _op = "address_txs_paged"
        _t0 = monotonic()
        _status = "success"
        # Optionales Caching aktivieren
        enable_cache = os.getenv("ENABLE_SCAN_CACHE", "1") == "1"
        ttl = int(os.getenv("SCAN_CACHE_TTL", "120"))
        cache_key_parts: List[str] = [
            "addr_txs",
            chain_id,
            address.lower(),
            str(limit),
            f"fb:{kwargs.get('from_block')}|tb:{kwargs.get('to_block')}",
            f"sh:{kwargs.get('start_height')}|eh:{kwargs.get('end_height')}",
        ]

        if enable_cache and cache_service is not None:
            cached = await cache_service.get(cache_key_parts)
            if cached is not None:
                return cached

        try:
            adapter = self.adapter_factory.get_adapter(chain_id)
            if not adapter:
                _status = "not_found"
                return []
            # EVM
            if isinstance(adapter, EthereumAdapter):
                from_block = kwargs.get("from_block")
                to_block = kwargs.get("to_block")
                if hasattr(adapter, "get_address_transactions_paged"):
                    res = await adapter.get_address_transactions_paged(address, limit=limit, from_block=from_block, to_block=to_block)
                else:
                    res = await adapter.get_address_transactions(address, limit)
                if enable_cache and cache_service is not None:
                    try:
                        await cache_service.set(cache_key_parts, res, ttl)
                    except Exception:
                        pass
                return res
            # UTXO
            if isinstance(adapter, BitcoinAdapter):
                start_height = kwargs.get("start_height")
                end_height = kwargs.get("end_height")
                if hasattr(adapter, "get_address_transactions_paged"):
                    res = await adapter.get_address_transactions_paged(address, limit=limit, start_height=start_height, end_height=end_height)
                else:
                    res = await adapter.get_address_transactions(address, limit)
                if enable_cache and cache_service is not None:
                    try:
                        await cache_service.set(cache_key_parts, res, ttl)
                    except Exception:
                        pass
                return res
            # Solana oder andere: Fallback
            res = await adapter.get_address_transactions(address, limit)
            if enable_cache and cache_service is not None:
                try:
                    await cache_service.set(cache_key_parts, res, ttl)
                except Exception:
                    pass
            return res
        except Exception:
            _status = "error"
            raise
        finally:
            try:
                if CHAIN_LATENCY is not None:
                    CHAIN_LATENCY.labels(chain=chain_id, op=_op).observe(max(monotonic() - _t0, 0))
                if CHAIN_REQUESTS is not None:
                    CHAIN_REQUESTS.labels(chain=chain_id, op=_op, status=_status).inc()
            except Exception:
                pass

    async def get_cross_chain_transfers(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Findet Cross-Chain-Transfers im Zeitraum"""
        transfers: List[Dict[str, Any]] = []
        # einfacher In-Memory-Cache pro Aufruf für Token-Metadaten
        token_meta_cache: Dict[str, Dict[str, Any]] = {}

        async def _erc20_decimals_and_symbol(ev_adapter: EthereumAdapter, token_addr: str) -> Dict[str, Any]:
            key = (token_addr or "").lower()
            if not key or not key.startswith("0x"):
                return {}
            if key in token_meta_cache:
                return token_meta_cache[key]
            meta: Dict[str, Any] = {}
            try:
                # decimals(): 0x313ce567
                dec_resp = await ev_adapter.make_request(
                    "eth_call",
                    [{"to": token_addr, "data": "0x313ce567"}, "latest"],
                )
                dec_hex = (dec_resp or {}).get("result")
                if isinstance(dec_hex, str) and dec_hex.startswith("0x"):
                    try:
                        meta["decimals"] = int(dec_hex, 16)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                # symbol(): 0x95d89b41 (kann bytes32 oder string sein)
                sym_resp = await ev_adapter.make_request(
                    "eth_call",
                    [{"to": token_addr, "data": "0x95d89b41"}, "latest"],
                )
                sym_hex = (sym_resp or {}).get("result")
                sym_str: Optional[str] = None
                if isinstance(sym_hex, str) and sym_hex.startswith("0x"):
                    try:
                        raw = bytes.fromhex(sym_hex[2:])
                        # naive decode: strip trailing nulls, try utf-8
                        sym_str = raw.rstrip(b"\x00").decode("utf-8", errors="ignore").strip() or None
                        # häufig ist bei dynamischen Rückgaben der eigentliche String am Ende
                        if not sym_str and len(raw) >= 64:
                            try:
                                # versuche die letzten 32-64 Bytes als String zu interpretieren
                                tail = raw[-64:]
                                sym_str = tail.rstrip(b"\x00").decode("utf-8", errors="ignore").strip() or None
                            except Exception:
                                pass
                    except Exception:
                        sym_str = None
                if sym_str:
                    meta["token_symbol"] = sym_str
            except Exception:
                pass
            token_meta_cache[key] = meta
            return meta

        # Bridge-Contracts & optionale Topics konfigurierbar über ENV (JSON):
        # BRIDGE_CONTRACTS_JSON: {"ethereum": ["0x...", "0x..."], "polygon": ["0x..."]}
        # BRIDGE_TOPICS_JSON: {"ethereum": {"0xaddr": ["0xtopic0"], "0xaddr2": ["0xtopic0b"]}}
        import json
        raw_cfg = os.getenv("BRIDGE_CONTRACTS_JSON", "{}")
        try:
            bridge_cfg = json.loads(raw_cfg)
        except Exception:
            bridge_cfg = {}
        raw_topics = os.getenv("BRIDGE_TOPICS_JSON", "{}")
        try:
            topics_cfg = json.loads(raw_topics)
        except Exception:
            topics_cfg = {}

        for chain_id in self.active_chains:
            adapter = self.adapter_factory.get_adapter(chain_id)
            if not adapter:
                continue

            # Nur EVM-Adapter aktuell unterstützen
            if isinstance(adapter, EthereumAdapter):
                contracts: List[str] = bridge_cfg.get(chain_id, [])
                if not contracts:
                    # Keine konfigurierten Contracts -> überspringen
                    continue

                # Zeit -> Blockbereich
                rng = await adapter.estimate_block_range_for_time(int(start_time.timestamp()), int(end_time.timestamp()))
                if not rng:
                    continue
                from_block = rng["from_block"]
                to_block = rng["to_block"]

                # Logs je Contract abrufen und als Transfers ausgeben
                for address in contracts:
                    try:
                        log_filter = {
                            "address": address,
                            "fromBlock": hex(from_block),
                            "toBlock": hex(to_block)
                        }
                        # Optional: topics[0] vorfiltern
                        addr_topics = topics_cfg.get(chain_id, {}).get(address, [])
                        if addr_topics:
                            # Nur topic0 berücksichtigen für schnelle Selektion
                            log_filter["topics"] = [addr_topics[0]]
                        params = [log_filter]
                        resp = await adapter.make_request("eth_getLogs", params)
                        logs = resp.get("result", []) if isinstance(resp, dict) else []
                        from datetime import datetime as _dt
                        for lg in logs:
                            item = {
                                "chain": chain_id,
                                "address": address,
                                "tx_hash": lg.get("transactionHash"),
                                "log_index": int(lg.get("logIndex", "0x0"), 16) if isinstance(lg.get("logIndex"), str) else lg.get("logIndex"),
                                "block_number": int(lg.get("blockNumber", "0x0"), 16) if isinstance(lg.get("blockNumber"), str) else lg.get("blockNumber"),
                                "block_hash": lg.get("blockHash"),
                                "data": lg.get("data"),
                                "topics": lg.get("topics", []),
                                # provenance
                                "adapter": type(adapter).__name__,
                                "rpc_endpoint": (adapter.chain_info.rpc_urls[0] if getattr(adapter, "chain_info", None) and adapter.chain_info.rpc_urls else None),
                                "collection_timestamp": _dt.utcnow().isoformat(),
                            }
                            # Versuche Event-Dekodierung (best-effort)
                            try:
                                if decode_bridge_log is not None:
                                    dec = decode_bridge_log(chain_id, address, {
                                        "topics": item.get("topics", []),
                                        "data": item.get("data")
                                    })
                                    if isinstance(dec, dict):
                                        if dec.get("event_name") is not None:
                                            item["event_name"] = dec.get("event_name")
                                        if dec.get("sender") is not None:
                                            item["sender"] = dec.get("sender")
                                        if dec.get("receiver") is not None:
                                            item["receiver"] = dec.get("receiver")
                                        if dec.get("amount") is not None:
                                            item["amount"] = dec.get("amount")
                                            item["amount_raw"] = dec.get("amount")
                                        if dec.get("token") is not None:
                                            item["token"] = dec.get("token")
                                        if dec.get("confidence") is not None:
                                            item["decode_confidence"] = dec.get("confidence")
                                        # Metrik pro Event zählen
                                        try:
                                            if BRIDGE_EVENTS is not None and dec.get("event_name"):
                                                BRIDGE_EVENTS.labels(stage="decoded").inc()
                                        except Exception:
                                            pass
                                    # Token-Metadaten anreichern (decimals, symbol)
                                    try:
                                        tok = item.get("token")
                                        if tok and isinstance(adapter, EthereumAdapter):
                                            meta = await _erc20_decimals_and_symbol(adapter, tok)
                                            if isinstance(meta, dict):
                                                if meta.get("decimals") is not None:
                                                    item["decimals"] = meta.get("decimals")
                                                if meta.get("token_symbol"):
                                                    item["token_symbol"] = meta.get("token_symbol")
                                                # value_usd berechnen, falls möglich
                                                try:
                                                    if price_service is not None and item.get("amount_raw") is not None and item.get("decimals") is not None:
                                                        sym = item.get("token_symbol")
                                                        price = await price_service.get_usd_price(chain_id, tok, sym)
                                                        if price is not None:
                                                            amt = item.get("amount_raw") or 0
                                                            decs = item.get("decimals") or 0
                                                            item["value_usd"] = float(amt) / (10 ** int(decs)) * float(price)
                                                except Exception:
                                                    pass
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            transfers.append(item)
                    except Exception as e:
                        logger.warning(f"Bridge log scan failed on {chain_id} {address}: {e}")

        # Metriken für erkannte Bridge-Logs
        try:
            if BRIDGE_EVENTS is not None and transfers:
                BRIDGE_EVENTS.labels(stage="detected").inc(len(transfers))
        except Exception:
            pass
        return transfers

    def get_chain_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über unterstützte Chains zurück"""
        chains = self.adapter_factory.get_supported_chains()

        return {
            "total_chains": len(chains),
            "chains_by_type": {
                chain_type.value: len(self.adapter_factory.get_chains_by_type(chain_type))
                for chain_type in ChainType
            },
            "active_chains": len(self.active_chains),
            "supported_features": list(set(
                feature
                for chain in chains
                for feature in chain.features
            ))
        }


# Singleton Instance
multi_chain_engine = MultiChainForensics()
