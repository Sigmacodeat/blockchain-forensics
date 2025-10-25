"""Ethereum Chain Adapter"""

import logging
from typing import Optional, AsyncGenerator, AsyncIterator, Dict, Any, cast
from datetime import datetime
from decimal import Decimal
try:
    from web3 import Web3, AsyncWeb3, AsyncHTTPProvider  # type: ignore
    from web3.types import BlockData, TxData, HexStr  # type: ignore
    _WEB3_AVAILABLE = True
except Exception:  # pragma: no cover
    Web3 = None  # type: ignore
    AsyncWeb3 = None  # type: ignore
    AsyncHTTPProvider = None  # type: ignore
    HexStr = str  # type: ignore
    _WEB3_AVAILABLE = False
try:
    from eth_utils import is_address, to_checksum_address  # type: ignore
    _ETH_UTILS_AVAILABLE = True
except Exception:  # pragma: no cover
    _ETH_UTILS_AVAILABLE = False
    def is_address(addr: str) -> bool:  # type: ignore
        return isinstance(addr, str) and addr.startswith("0x") and len(addr) in (42, 40)
    def to_checksum_address(addr: str) -> str:  # type: ignore
        return addr

from app.schemas import CanonicalEvent
from .base import IChainAdapter
from app.enrichment.abi_decoder import decode_input, abi_decoder
from app.enrichment.abi_signatures import resolve_selector_name
from app.observability.metrics import DEX_SWAPS_TOTAL

logger = logging.getLogger(__name__)

# Simple in-memory cache for pool token mapping to avoid repetitive RPC calls
_PAIR_TOKEN_CACHE: Dict[str, Dict[str, str]] = {}

def _resolve_pair_tokens(addr: Optional[str]) -> Optional[Dict[str, str]]:
    """Best-effort resolution of token0/token1 for UniswapV2-like pools.
    Uses web3 if available; caches results in-process.
    """
    try:
        if not addr:
            return None
        a = str(addr).lower()
        if a in _PAIR_TOKEN_CACHE:
            return _PAIR_TOKEN_CACHE[a]
        if not _WEB3_AVAILABLE:
            return None
        # Lazy import to avoid circulars
        from app.adapters.web3_client import web3_client  # type: ignore
        w3 = getattr(web3_client, 'w3', None)
        if w3 is None:
            return None
        # Minimal ABIs we try in order
        abi_univ2 = [
            {"name": "token0", "outputs": [{"type": "address"}], "inputs": [], "stateMutability": "view", "type": "function"},
            {"name": "token1", "outputs": [{"type": "address"}], "inputs": [], "stateMutability": "view", "type": "function"},
        ]
        abi_curve_like = [
            {"name": "coins", "outputs": [{"type": "address"}], "inputs": [{"type": "uint256", "name": "i"}], "stateMutability": "view", "type": "function"},
        ]
        # Try UniswapV2-style first
        try:
            c = w3.eth.contract(address=a, abi=abi_univ2)
            t0 = c.functions.token0().call()
            t1 = c.functions.token1().call()
            mapping = {"token0": str(t0).lower(), "token1": str(t1).lower()}
            _PAIR_TOKEN_CACHE[a] = mapping
            return mapping
        except Exception:
            pass
        # Fallback: Curve-like coins(0)/coins(1)
        try:
            c2 = w3.eth.contract(address=a, abi=abi_curve_like)
            t0 = c2.functions.coins(0).call()
            t1 = c2.functions.coins(1).call()
            mapping = {"token0": str(t0).lower(), "token1": str(t1).lower()}
            _PAIR_TOKEN_CACHE[a] = mapping
            return mapping
        except Exception:
            pass
        return None
    except Exception:
        return None


class EthereumAdapter(IChainAdapter):
    """Ethereum blockchain adapter with EVM support"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        # Lazy settings import to avoid Settings() validation during tests
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                self.rpc_url = getattr(settings, 'ETHEREUM_RPC_URL', None)
            except Exception:
                self.rpc_url = None
        else:
            self.rpc_url = rpc_url

        if not self.rpc_url:
            # Fallback to a mock URL to allow offline tests
            self.rpc_url = "mock://ethereum"
        # Initialize web3 only if available
        if _WEB3_AVAILABLE and AsyncWeb3 is not None and AsyncHTTPProvider is not None:
            try:
                self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))  # type: ignore[attr-defined]
            except Exception:
                self.w3 = None  # type: ignore
        else:
            self.w3 = None  # type: ignore
        self._chain_name = "ethereum"
        logger.info(f"Initialized Ethereum adapter with RPC: {self.rpc_url}")
    
    @property
    def chain_name(self) -> str:
        return self._chain_name
    
    async def get_block(self, block_number: int) -> Dict[str, Any]:
        """Fetch block with transactions"""
        if not self.w3:
            # Minimal offline-safe response
            return {"number": block_number, "timestamp": int(datetime.utcnow().timestamp()), "transactions": []}
        try:
            block = await self.w3.eth.get_block(block_number, full_transactions=True)  # type: ignore[attr-defined]
            return cast(Dict[str, Any], block)
        except Exception as e:
            logger.error(f"Error fetching block {block_number}: {e}")
            raise
    
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Fetch transaction by hash"""
        if not self.w3:
            return {}
        try:
            tx = await self.w3.eth.get_transaction(cast(HexStr, tx_hash))  # type: ignore[attr-defined]
            return cast(Dict[str, Any], tx)
        except Exception as e:
            logger.error(f"Error fetching tx {tx_hash}: {e}")
            raise
    
    async def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """Fetch transaction receipt"""
        if not self.w3:
            return {"status": 1, "gasUsed": 0, "logs": []}
        try:
            receipt = await self.w3.eth.get_transaction_receipt(cast(HexStr, tx_hash))  # type: ignore[attr-defined]
            return cast(Dict[str, Any], receipt)
        except Exception as e:
            logger.error(f"Error fetching receipt {tx_hash}: {e}")
            raise
    
    async def transform_transaction(
        self,
        raw_tx: Dict[str, Any],
        block_data: Dict[str, Any]
    ) -> CanonicalEvent:
        """Transform Ethereum transaction → Canonical Event"""
        try:
            def _hash_str(hv: Any) -> str:
                try:
                    if isinstance(hv, (bytes, bytearray)):
                        if _WEB3_AVAILABLE and Web3 is not None:
                            return cast(str, Web3.to_hex(hv))  # type: ignore[attr-defined]
                        return "0x" + hv.hex()
                    if hasattr(hv, 'hex'):
                        return cast(str, hv.hex())
                except Exception:
                    pass
                return str(hv)

            # Get transaction receipt for status and gas used
            receipt = await self.get_transaction_receipt(_hash_str(raw_tx.get('hash')))
            
            # Normalize addresses
            from_address = to_checksum_address(raw_tx['from']) if _ETH_UTILS_AVAILABLE else str(raw_tx['from'])
            to_address = (to_checksum_address(raw_tx['to']) if _ETH_UTILS_AVAILABLE else str(raw_tx.get('to'))) if raw_tx.get('to') else None
            
            # Calculate fee
            gas_used = receipt.get('gasUsed', 0)
            gas_price = raw_tx.get('gasPrice', 0)
            fee = Decimal(gas_used * gas_price) / Decimal(10**18)  # Convert to ETH
            
            # Determine event type
            event_type = self._determine_event_type(raw_tx, receipt)
            
            # Extract contract info
            contract_address = None
            method_name = None
            inp = raw_tx.get('input', '0x') or '0x'
            if raw_tx.get('to') and len(str(inp)) >= 10:
                try:
                    contract_address = to_checksum_address(raw_tx['to'])
                except Exception:
                    contract_address = raw_tx.get('to')
                # First 4 bytes of input = method selector
                if isinstance(inp, (bytes, bytearray)):
                    method_selector = ((Web3.to_hex(inp) if (_WEB3_AVAILABLE and Web3 is not None) else ("0x" + inp.hex())) or '0x')[:10]
                else:
                    method_selector = (str(inp) or '0x')[:10]
                # Fallback to selector→name map; otherwise keep selector string
                method_name = resolve_selector_name(method_selector) or method_selector

            # Try ABI decode of input to get human-readable method
            try:
                dec = decode_input(str(inp))
                if dec and dec.get('decoded') and dec.get('function_name'):
                    method_name = dec.get('function_name')
            except Exception:
                pass
            
            # Create canonical event
            meta: Dict[str, Any] = {
                'raw_to': (raw_tx.get('to') or '').lower(),
                'nonce': raw_tx.get('nonce'),
                'chain_id': raw_tx.get('chainId'),
                'input': (raw_tx.get('input', '0x') or '0x')[:100],  # Truncate
            }
            # Heuristik: bekannte DEX-Router-Adressen -> als Swap markieren
            try:
                # Lazy import settings to avoid hard dependency during tests
                from app.config import settings  # type: ignore
                dex_routers = set([str(x).lower() for x in getattr(settings, 'DEX_ROUTERS_EVM', []) or []])
                to_lower = (raw_tx.get('to') or '').lower()
                if dex_routers and to_lower in dex_routers and event_type != 'bridge':
                    event_type = 'dex_swap'
                    meta['dex_router'] = to_lower
                    try:
                        DEX_SWAPS_TOTAL.inc()
                    except Exception:
                        pass
            except Exception:
                pass
            if event_type == "bridge":
                meta.update({
                    'bridge_contract': contract_address or (raw_tx.get('to') or '').lower(),
                    'bridge_method': method_name,
                })

            # Decode logs to detect ERC20/ERC721/ERC1155 Transfers and enrich token fields
            try:
                logs = receipt.get('logs') or []
                # Store compact raw logs (address + topic0..n) for downstream bridge detection heuristics
                try:
                    compact_logs = []
                    for lg in logs:
                        try:
                            addr = lg.get('address')
                            tps = lg.get('topics') or []
                            # Normalize topics to hex strings
                            topics_hex = []
                            for t in tps:
                                try:
                                    th = t.hex() if hasattr(t, 'hex') else str(t)
                                except Exception:
                                    th = str(t)
                                topics_hex.append(str(th).lower())
                            compact_logs.append({
                                'address': (addr or '').lower(),
                                'topics': topics_hex,
                            })
                        except Exception:
                            continue
                    if compact_logs:
                        meta.setdefault('logs', compact_logs)
                except Exception:
                    pass
                for lg in logs:
                    ev = abi_decoder.decode_log(lg)
                    if not ev:
                        # Fallback heuristic: detect ERC20 Transfer topic directly
                        try:
                            topics = lg.get('topics') or []
                            first = topics[0].hex() if topics and hasattr(topics[0], 'hex') else (topics[0] if topics else None)
                            if isinstance(first, str) and first.lower() == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                                token_addr = lg.get('address') or contract_address
                                meta.setdefault('erc20_transfers', []).append({
                                    'token': token_addr,
                                    'from': None,
                                    'to': None,
                                    'amount': None,
                                })
                                if event_type not in ("bridge", "token_transfer"):
                                    event_type = "token_transfer"
                                    contract_address = contract_address or token_addr
                        except Exception:
                            pass
                        continue

                    # From here, ev is decoded
                    if ev.get('event') in ('Approval', 'ApprovalForAll', 'ERC721_Approval'):
                        token_addr = lg.get('address') or contract_address
                        meta.setdefault('approvals', []).append({
                            'token': token_addr,
                            'owner': ev['params'].get('param_0'),
                            'spender': ev['params'].get('param_1'),
                            'value': ev['params'].get('param_2'),
                        })
                        if event_type not in ("bridge", "token_transfer", "nft_transfer"):
                            event_type = "token_approval"
                            contract_address = contract_address or token_addr
                    elif ev.get('event') in ('Swap', 'Sync'):
                        token_addr = lg.get('address') or contract_address
                        # Versuche, Beträge aus den Standardfeldern zu ziehen (Uniswap V2/V3 ähnlich)
                        p = ev.get('params', {}) or {}
                        amounts = {
                            'amount0_in': p.get('amount0In') or p.get('param_2') or None,
                            'amount1_in': p.get('amount1In') or p.get('param_3') or None,
                            'amount0_out': p.get('amount0Out') or p.get('param_4') or None,
                            'amount1_out': p.get('amount1Out') or p.get('param_5') or None,
                        }
                        entry = {
                            'pair_or_pool': token_addr,
                            **{k: v for k, v in amounts.items() if v is not None},
                        }
                        # enrich with token0/token1 if resolvable
                        mapping = _resolve_pair_tokens(token_addr)
                        if mapping:
                            entry.update(mapping)
                        meta.setdefault('dex_swaps', []).append(entry)
                        meta.setdefault('dex_events', []).append({'event': ev.get('event'), 'address': token_addr})
                        if event_type not in ("bridge",):
                            event_type = "dex_swap"
                        try:
                            DEX_SWAPS_TOTAL.inc()
                        except Exception:
                            pass
                    if ev.get('event') == 'Transfer':  # ERC20
                        frm = ev['params'].get('param_0')
                        to = ev['params'].get('param_1')
                        amount = ev['params'].get('param_2')
                        token_addr = lg.get('address') or contract_address
                        meta.setdefault('erc20_transfers', []).append({
                            'token': token_addr,
                            'from': frm,
                            'to': to,
                            'amount': int(amount) if isinstance(amount, int) else amount,
                        })
                        # If no event type assigned yet and transfer exists, mark as token_transfer
                        if event_type not in ("bridge", "token_transfer"):
                            event_type = "token_transfer"
                            # set token fields best-effort
                            to_address = to_address or to
                            from_address = from_address or frm
                            # store token address hint
                            contract_address = contract_address or token_addr
                    elif ev.get('event') == 'ERC721_Transfer':
                        frm = ev['params'].get('param_0')
                        to = ev['params'].get('param_1')
                        token_id = ev['params'].get('param_2')
                        token_addr = lg.get('address') or contract_address
                        meta.setdefault('erc721_transfers', []).append({
                            'token': token_addr,
                            'from': frm,
                            'to': to,
                            'token_id': int(token_id) if isinstance(token_id, int) else token_id,
                        })
                        if event_type not in ("bridge", "nft_transfer", "token_transfer"):
                            event_type = "nft_transfer"
                            to_address = to_address or to
                            from_address = from_address or frm
                            contract_address = contract_address or token_addr
                    elif ev.get('event') == 'TransferSingle':
                        operator = ev['params'].get('param_0')
                        frm = ev['params'].get('param_1')
                        to = ev['params'].get('param_2')
                        token_id = ev['params'].get('param_3')
                        value = ev['params'].get('param_4')
                        token_addr = lg.get('address') or contract_address
                        meta.setdefault('erc1155_transfers', []).append({
                            'type': 'single',
                            'token': token_addr,
                            'operator': operator,
                            'from': frm,
                            'to': to,
                            'id': int(token_id) if isinstance(token_id, int) else token_id,
                            'value': int(value) if isinstance(value, int) else value,
                        })
                        if event_type not in ("bridge", "nft_transfer", "token_transfer"):
                            event_type = "nft_transfer"
                            to_address = to_address or to
                            from_address = from_address or frm
                            contract_address = contract_address or token_addr
                    elif ev.get('event') == 'TransferBatch':
                        operator = ev['params'].get('param_0')
                        frm = ev['params'].get('param_1')
                        to = ev['params'].get('param_2')
                        ids = ev['params'].get('param_3')
                        values = ev['params'].get('param_4')
                        token_addr = lg.get('address') or contract_address
                        meta.setdefault('erc1155_transfers', []).append({
                            'type': 'batch',
                            'token': token_addr,
                            'operator': operator,
                            'from': frm,
                            'to': to,
                            'ids': ids,
                            'values': values,
                        })
                        if event_type not in ("bridge", "nft_transfer", "token_transfer"):
                            event_type = "nft_transfer"
                            to_address = to_address or to
                            from_address = from_address or frm
                            contract_address = contract_address or token_addr
            except Exception:
                pass

            event = CanonicalEvent(
                event_id=f"eth_tx_{_hash_str(raw_tx.get('hash'))}",
                chain=self.chain_name,
                block_number=block_data['number'],
                block_timestamp=datetime.fromtimestamp(block_data['timestamp']),
                tx_hash=_hash_str(raw_tx.get('hash')),
                tx_index=raw_tx.get('transactionIndex', 0),
                from_address=from_address,
                to_address=to_address,
                value=Decimal(raw_tx.get('value', 0)) / Decimal(10**18),  # Wei to ETH
                value_usd=None,
                gas_used=gas_used,
                gas_price=gas_price,
                fee=fee,
                status=receipt.get('status', 0),
                error_message=None,
                event_type=event_type,
                contract_address=contract_address,
                method_name=method_name,
                token_address=None,
                token_symbol=None,
                token_decimals=None,
                risk_score=None,
                cluster_id=None,
                idempotency_key=f"eth_{block_data['number']}_{raw_tx.get('transactionIndex', 0)}",
                source="rpc",
                metadata=meta,
            )
            
            return event
            
        except Exception as e:
            def _hash_str(hv: Any) -> str:
                try:
                    if isinstance(hv, (bytes, bytearray)):
                        return cast(str, Web3.to_hex(hv))
                    if hasattr(hv, 'hex'):
                        return cast(str, hv.hex())
                except Exception:
                    pass
                return str(hv)
            h_str = _hash_str(raw_tx.get('hash'))
            logger.error(f"Error transforming tx {h_str}: {e}")
            raise
    
    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """Determine transaction type"""
        # Known bridge contract addresses (checksummed or lower acceptable)
        default_bridges = [
            # Wormhole, Stargate placeholders (add/override via settings)
            "0x3ee18b2214aff97000d974cf647e7c347e8fa585",
            "0x8731d54e9d02c286767d56ac03e8037c07e01e98",
        ]
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_ETH", None)
        except Exception:
            cfg = None
        cfg_list = [x.strip().lower() for x in cfg.split(",") if x.strip()] if isinstance(cfg, str) else []
        KNOWN_BRIDGES = set([a.lower() for a in (cfg_list or default_bridges)])
        to_addr = tx.get('to') or ''
        if to_addr and to_addr.lower() in KNOWN_BRIDGES:
            return "bridge"
        # Method selectors that commonly indicate bridging (heuristic placeholders)
        selector = (tx.get('input') or '0x')[:10]
        try:
            from app.config import settings  # type: ignore
            known_selectors = getattr(settings, "BRIDGE_METHOD_SELECTORS", None)
        except Exception:
            known_selectors = None
        selector_set = set(known_selectors) if isinstance(known_selectors, (list, tuple, set)) else {"0x12345678", "0xabcdef12"}
        if selector in selector_set:
            return "bridge"
        # Contract creation
        if not tx.get('to'):
            return "contract_creation"
        
        # Check for logs (events)
        if receipt.get('logs'):
            # Inspect topics to classify common events before defaulting
            try:
                logs = receipt.get('logs') or []
                for lg in logs:
                    topics = lg.get('topics') or []
                    # Normalize topic0 to hex string
                    t0 = None
                    if topics:
                        try:
                            t0 = topics[0].hex() if hasattr(topics[0], 'hex') else str(topics[0])
                        except Exception:
                            t0 = str(topics[0])
                    if not isinstance(t0, str):
                        continue
                    t0_low = t0.lower()
                    # ERC20 Transfer
                    if t0_low == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                        return 'token_transfer'
                    # ERC721 Transfer (same topic as ERC20 Transfer, classification refined later via decoded logs)
                    # ERC1155 TransferSingle / TransferBatch
                    if t0_low in {
                        '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62',  # TransferSingle
                        '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e3e7d6c3c7f7a6bf2bdda',  # TransferBatch
                    }:
                        return 'nft_transfer'
                    # Approvals (ERC20/721)
                    if t0_low in {
                        '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925',  # Approval
                        '0x17307eab39c6c1d0c2487b9103a6f3c6db2a26c96f1a3b2a7a2f1bde7e2a6c7f',  # ApprovalForAll (common hash)
                    }:
                        return 'token_approval'
                    # Uniswap V2/V3 Swap-like events (heuristic topic0 matches)
                    if t0_low in {
                        '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822',  # Swap (Uniswap V2)
                        '0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1',  # Sync (Uniswap V2)
                    }:
                        return 'dex_swap'
            except Exception:
                pass
            # Default classification when logs present but unknown signature
            return "contract_call"
        
        # Simple ETH transfer
        if tx.get('value', 0) > 0 and len(tx.get('input', '0x')) <= 2:
            return "transfer"
        
        # Contract interaction
        if len(tx.get('input', '0x')) > 10:
            return "contract_call"
        
        return "unknown"
    
    def stream_blocks(
        self,
        start_block: int,
        end_block: Optional[int] = None
    ) -> AsyncGenerator[CanonicalEvent, None]:
        """Stream transactions from blocks"""
        async def gen() -> AsyncGenerator[CanonicalEvent, None]:
            current_block = start_block
            latest_block = end_block or await self.get_latest_block_number()

            logger.info(f"Streaming blocks {start_block} to {latest_block}")

            while current_block <= latest_block:
                try:
                    block = await self.get_block(current_block)

                    # Process all transactions in block
                    for tx in block.get('transactions', []):
                        if not isinstance(tx, dict):
                            continue
                        try:
                            event = await self.transform_transaction(tx, block)
                            yield event
                        except Exception as e:
                            logger.error(f"Error processing tx in block {current_block}: {e}")
                            continue

                    current_block += 1

                except Exception as e:
                    logger.error(f"Error streaming block {current_block}: {e}")
                    # Retry or skip
                    current_block += 1
                    continue

        return gen()
    
    async def get_latest_block_number(self) -> int:
        """Get latest block number"""
        try:
            return await self.w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting latest block: {e}")
            raise
    
    async def is_contract(self, address: str) -> bool:
        """Check if address is a contract"""
        try:
            if not is_address(address):
                return False
            
            code = await self.w3.eth.get_code(to_checksum_address(address))
            return len(code) > 0
        except Exception as e:
            logger.error(f"Error checking contract {address}: {e}")
            return False
    
    async def get_balance(self, address: str, block: Optional[int] = None) -> Decimal:
        """Get address balance"""
        try:
            balance_wei = await self.w3.eth.get_balance(
                to_checksum_address(address),
                block_identifier=block or 'latest'
            )
            return Decimal(balance_wei) / Decimal(10**18)
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            raise
    
    async def get_transaction_count(self, address: str) -> int:
        """Get transaction count (nonce)"""
        try:
            return await self.w3.eth.get_transaction_count(to_checksum_address(address))
        except Exception as e:
            logger.error(f"Error getting tx count for {address}: {e}")
            raise
