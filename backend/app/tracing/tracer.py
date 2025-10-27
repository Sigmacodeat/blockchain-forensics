"""Recursive Transaction Tracing Engine with Taint Propagation"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from decimal import Decimal
from collections import deque, defaultdict
from datetime import datetime
import time as _time
import asyncio
import uuid

from app.tracing.models import (
    TraceRequest,
    TraceResult,
    TraceNode,
    TraceEdge,
    TaintedTransaction,
    TaintModel,
    TraceDirection
)
# Lazy-safe imports to avoid settings side-effects in tests
try:
    from app.enrichment.labels_service import labels_service  # type: ignore
except Exception:
    class _DummyLabels:
        async def get_labels(self, *args, **kwargs):
            return []
    labels_service = _DummyLabels()  # type: ignore

try:
    from app.db.neo4j_client import neo4j_client  # type: ignore
except Exception:
    class _DummyNeo4j:
        async def run_query(self, *args, **kwargs):
            return []
    neo4j_client = _DummyNeo4j()  # type: ignore

from app.observability.metrics import TRACE_REQUESTS, TRACE_LATENCY, TRACE_EDGES_CREATED, BRIDGE_EVENTS

logger = logging.getLogger(__name__)


class TransactionTracer:
    """
    Recursive transaction tracer with taint propagation.
    Implements FIFO and Proportional taint models as per Chainalysis methodology.
    """
    
    def __init__(self, db_client):
        """
        Args:
            db_client: Database client for fetching transactions (Postgres/Neo4j)
        """
        self.db = db_client
        self.labels_service = labels_service
        
    async def trace(self, request: TraceRequest) -> TraceResult:
        """
        Execute trace request
        
        Algorithm:
        1. Initialize source node with 100% taint
        2. Queue-based BFS/DFS traversal
        3. For each transaction:
           - Calculate taint using selected model
           - Propagate to next hop if > threshold
           - Stop at max depth or max nodes
        4. Build result graph
        """
        start_time = datetime.utcnow()
        start_ts = _time.monotonic()
        last_emit = start_ts
        processed_steps = 0
        trace_id = str(uuid.uuid4())
        
        logger.info(f"Starting trace {trace_id} from {request.source_address}")
        
        # Initialize result
        result = TraceResult(
            trace_id=trace_id,
            source_address=request.source_address.lower(),
            direction=request.direction,
            taint_model=request.taint_model,
            max_depth=request.max_depth,
            min_taint_threshold=request.min_taint_threshold
        )
        
        try:
            # Initialize source node
            source_node = TraceNode(
                address=request.source_address.lower(),
                taint_received=Decimal(1.0),  # Source has 100% taint
                hop_distance=0
            )
            result.nodes[source_node.address] = source_node
            
            # Queue for BFS: (address, current_taint, hop_distance, path)
            queue: deque = deque([
                (source_node.address, Decimal(1.0), 0, [source_node.address])
            ])
            
            visited: Set[str] = set()
            
            # Trace loop
            while queue and result.total_nodes < request.max_nodes:
                # Global wall-clock timeout
                now_ts = _time.monotonic()
                if now_ts - start_ts > float(getattr(request, "max_execution_seconds", 25)):
                    result.error = "timeout"
                    logger.warning(f"Trace {trace_id} aborted due to timeout after {now_ts - start_ts:.2f}s")
                    break
                current_address, current_taint, hop, path = queue.popleft()
                processed_steps += 1
                
                # Skip if already visited at this hop or deeper
                visit_key = f"{current_address}_{hop}"
                if visit_key in visited:
                    continue
                visited.add(visit_key)
                
                # Check depth limit
                if hop >= request.max_depth:
                    continue
                
                # Check taint threshold
                if current_taint < Decimal(str(request.min_taint_threshold)):
                    logger.debug(f"Taint {current_taint} below threshold at {current_address}")
                    continue
                
                # Fetch transactions
                io_timeout = float(getattr(request, "io_timeout_seconds", 5.0))
                if request.direction == TraceDirection.FORWARD:
                    try:
                        transactions = await asyncio.wait_for(
                            self._get_outgoing_transactions(
                                current_address,
                                request.start_timestamp,
                                request.end_timestamp
                            ),
                            timeout=io_timeout,
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"trace {trace_id}: outgoing tx timeout @ {current_address}")
                        transactions = []
                elif request.direction == TraceDirection.BACKWARD:
                    try:
                        transactions = await asyncio.wait_for(
                            self._get_incoming_transactions(
                                current_address,
                                request.start_timestamp,
                                request.end_timestamp
                            ),
                            timeout=io_timeout,
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"trace {trace_id}: incoming tx timeout @ {current_address}")
                        transactions = []
                else:  # BOTH
                    try:
                        outgoing = await asyncio.wait_for(
                            self._get_outgoing_transactions(current_address), timeout=io_timeout
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"trace {trace_id}: outgoing(BOTH) timeout @ {current_address}")
                        outgoing = []
                    try:
                        incoming = await asyncio.wait_for(
                            self._get_incoming_transactions(current_address), timeout=io_timeout
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"trace {trace_id}: incoming(BOTH) timeout @ {current_address}")
                        incoming = []
                    transactions = (outgoing or []) + (incoming or [])
                
                # Fetch UTXO flows (BTC-like), best-effort
                utxo_txs: List[Dict] = []
                try:
                    if request.enable_utxo and request.direction == TraceDirection.FORWARD:
                        try:
                            utxo_txs = await asyncio.wait_for(
                                self._get_utxo_outgoing(
                                    current_address,
                                    request.start_timestamp,
                                    request.end_timestamp,
                                ),
                                timeout=io_timeout,
                            )
                        except asyncio.TimeoutError:
                            logger.warning(f"trace {trace_id}: utxo_outgoing timeout @ {current_address}")
                            utxo_txs = []
                    elif request.enable_utxo and request.direction == TraceDirection.BACKWARD:
                        try:
                            utxo_txs = await asyncio.wait_for(
                                self._get_utxo_incoming(
                                    current_address,
                                    request.start_timestamp,
                                    request.end_timestamp,
                                ),
                                timeout=io_timeout,
                            )
                        except asyncio.TimeoutError:
                            logger.warning(f"trace {trace_id}: utxo_incoming timeout @ {current_address}")
                            utxo_txs = []
                    else:
                        try:
                            u_out = await asyncio.wait_for(self._get_utxo_outgoing(current_address), timeout=io_timeout) if request.enable_utxo else []
                        except asyncio.TimeoutError:
                            logger.warning(f"trace {trace_id}: utxo_outgoing(BOTH) timeout @ {current_address}")
                            u_out = []
                        try:
                            u_in = await asyncio.wait_for(self._get_utxo_incoming(current_address), timeout=io_timeout) if request.enable_utxo else []
                        except asyncio.TimeoutError:
                            logger.warning(f"trace {trace_id}: utxo_incoming(BOTH) timeout @ {current_address}")
                            u_in = []
                        utxo_txs = (u_out or []) + (u_in or [])
                except Exception:
                    utxo_txs = []

                combined = list(transactions) + list(utxo_txs)

                # Process transactions (same-chain and UTXO combined)
                for tx in combined:
                    next_address = tx['to_address'] if request.direction != TraceDirection.BACKWARD else tx['from_address']
                    if not next_address:
                        continue
                    
                    next_address = next_address.lower()
                    
                    # Calculate taint for this transaction
                    taint_value, taint_score = await self._calculate_taint(
                        tx,
                        current_address,
                        current_taint,
                        request.taint_model,
                        combined
                    )
                    
                    # Skip if below threshold
                    if taint_score < request.min_taint_threshold:
                        continue
                    
                    # If ERC20 token transfers metadata present, split taint across token transfers
                    meta = tx.get('metadata') or {}
                    erc20_transfers = meta.get('erc20_transfers') or []
                    if request.enable_token and erc20_transfers:
                        # Consider only transfers where current_address is sender
                        outgoing_token_xfers = [t for t in erc20_transfers if str(t.get('from','') or t.get('from_address','')).lower() == current_address]
                        total_token_amount = sum(Decimal(str(t.get('amount', 0))) for t in outgoing_token_xfers) or Decimal(0)
                        if total_token_amount > 0:
                            for t in outgoing_token_xfers:
                                to_tok = str(t.get('to','') or t.get('to_address','')).lower()
                                if not to_tok:
                                    continue
                                amount = Decimal(str(t.get('amount', 0)))
                                ratio = amount / total_token_amount
                                tok_taint = current_taint * Decimal(str(request.token_decay)) * ratio
                                # Create/update node
                                if to_tok not in result.nodes:
                                    next_node = TraceNode(
                                        address=to_tok,
                                        hop_distance=hop + 1,
                                        labels=await self.labels_service.get_labels(to_tok)
                                    )
                                    result.nodes[to_tok] = next_node
                                    result.total_nodes += 1
                                else:
                                    next_node = result.nodes[to_tok]
                                next_node.taint_received += tok_taint
                                if current_address in result.nodes:
                                    result.nodes[current_address].taint_sent += tok_taint
                                # Edge for token transfer
                                edge = TraceEdge(
                                    from_address=current_address,
                                    to_address=to_tok,
                                    tx_hash=tx.get('tx_hash') or '',
                                    value=amount,
                                    taint_value=tok_taint,
                                    timestamp=tx.get('timestamp') or datetime.utcnow().isoformat(),
                                    hop=hop + 1,
                                    event_type='token_transfer',
                                )
                                result.edges.append(edge)
                                try:
                                    TRACE_EDGES_CREATED.labels(event_type='token_transfer').inc()
                                except Exception:
                                    pass
                                result.total_edges += 1
                                # Enqueue
                                queue.append((
                                    to_tok,
                                    tok_taint,
                                    hop + 1,
                                    path + [to_tok]
                                ))
                            # Done handling token splits for this tx
                            continue

                    # ERC721 transfers: split taint evenly across outgoing transfers from current address
                    erc721_transfers = meta.get('erc721_transfers') or []
                    if request.enable_token and erc721_transfers:
                        outgoing_nft = [t for t in erc721_transfers if str(t.get('from','') or t.get('from_address','')).lower() == current_address]
                        count = len(outgoing_nft)
                        if count > 0:
                            per_share = (current_taint * Decimal(str(request.token_decay))) / Decimal(count)
                            for t in outgoing_nft:
                                to_tok = str(t.get('to','') or t.get('to_address','')).lower()
                                if not to_tok:
                                    continue
                                # node
                                if to_tok not in result.nodes:
                                    next_node = TraceNode(
                                        address=to_tok,
                                        hop_distance=hop + 1,
                                        labels=await self.labels_service.get_labels(to_tok)
                                    )
                                    result.nodes[to_tok] = next_node
                                    result.total_nodes += 1
                                else:
                                    next_node = result.nodes[to_tok]
                                next_node.taint_received += per_share
                                if current_address in result.nodes:
                                    result.nodes[current_address].taint_sent += per_share
                                # edge
                                edge = TraceEdge(
                                    from_address=current_address,
                                    to_address=to_tok,
                                    tx_hash=tx.get('tx_hash') or '',
                                    value=Decimal(0),
                                    taint_value=per_share,
                                    timestamp=tx.get('timestamp') or datetime.utcnow().isoformat(),
                                    hop=hop + 1,
                                    event_type='nft_transfer',
                                )
                                result.edges.append(edge)
                                result.total_edges += 1
                                queue.append((to_tok, per_share, hop + 1, path + [to_tok]))
                            continue

                    # ERC1155 transfers: weight by amount across outgoing transfers
                    erc1155_transfers = meta.get('erc1155_transfers') or []
                    if request.enable_token and erc1155_transfers:
                        outgoing_nft1155 = [t for t in erc1155_transfers if str(t.get('from','') or t.get('from_address','')).lower() == current_address]
                        total_amt = sum(Decimal(str(t.get('amount', 0))) for t in outgoing_nft1155) or Decimal(0)
                        if total_amt > 0:
                            for t in outgoing_nft1155:
                                to_tok = str(t.get('to','') or t.get('to_address','')).lower()
                                if not to_tok:
                                    continue
                                amount = Decimal(str(t.get('amount', 0)))
                                ratio = amount / total_amt if total_amt > 0 else Decimal(0)
                                share = current_taint * Decimal(str(request.token_decay)) * ratio
                                if to_tok not in result.nodes:
                                    next_node = TraceNode(
                                        address=to_tok,
                                        hop_distance=hop + 1,
                                        labels=await self.labels_service.get_labels(to_tok)
                                    )
                                    result.nodes[to_tok] = next_node
                                    result.total_nodes += 1
                                else:
                                    next_node = result.nodes[to_tok]
                                next_node.taint_received += share
                                if current_address in result.nodes:
                                    result.nodes[current_address].taint_sent += share
                                edge = TraceEdge(
                                    from_address=current_address,
                                    to_address=to_tok,
                                    tx_hash=tx.get('tx_hash') or '',
                                    value=amount,
                                    taint_value=share,
                                    timestamp=tx.get('timestamp') or datetime.utcnow().isoformat(),
                                    hop=hop + 1,
                                    event_type='nft1155_transfer',
                                )
                                result.edges.append(edge)
                                result.total_edges += 1
                                queue.append((to_tok, share, hop + 1, path + [to_tok]))
                            continue
                    
                    # Apply channel-specific decays for native/utxo flows
                    effective_taint = taint_value
                    ev_type = (tx.get('event_type') or '').lower()
                    if ev_type.startswith('utxo'):
                        effective_taint = effective_taint * Decimal(str(request.utxo_decay))
                    else:
                        effective_taint = effective_taint * Decimal(str(request.native_decay))

                    # Create/update nodes
                    if next_address not in result.nodes:
                        next_node = TraceNode(
                            address=next_address,
                            hop_distance=hop + 1,
                            labels=await self.labels_service.get_labels(next_address)
                        )
                        result.nodes[next_address] = next_node
                        result.total_nodes += 1
                    else:
                        next_node = result.nodes[next_address]
                    
                    # Update node taints
                    next_node.taint_received += effective_taint
                    if current_address in result.nodes:
                        result.nodes[current_address].taint_sent += effective_taint
                    
                    # Create edge with optional bridge metadata
                    edge_kwargs = dict(
                        from_address=current_address if request.direction != TraceDirection.BACKWARD else next_address,
                        to_address=next_address if request.direction != TraceDirection.BACKWARD else current_address,
                        tx_hash=tx['tx_hash'],
                        value=Decimal(str(tx['value'])),
                        taint_value=effective_taint,
                        timestamp=tx['timestamp'],
                        hop=hop + 1,
                    )
                    # Optional metadata passthrough if present in tx
                    if 'event_type' in tx:
                        edge_kwargs['event_type'] = tx.get('event_type')
                    if 'bridge' in tx:
                        edge_kwargs['bridge'] = tx.get('bridge')
                    if 'chain_from' in tx:
                        edge_kwargs['chain_from'] = tx.get('chain_from')
                    if 'chain_to' in tx:
                        edge_kwargs['chain_to'] = tx.get('chain_to')
                    # Heuristic: mark as bridge if labels indicate known bridges (when tx lacks metadata)
                    if 'event_type' not in edge_kwargs:
                        lbls = set(next_node.labels or [])
                        known = {
                            'bridge', 'wormhole', 'stargate', 'multichain', 'across',
                            'celer', 'synapse', 'layerzero', 'arbitrum-bridge', 'optimism-bridge', 'polygon-bridge'
                        }
                        hit = [l for l in lbls if l in known]
                        if hit:
                            edge_kwargs['event_type'] = 'bridge'
                            edge_kwargs['bridge'] = hit[0]
                    # Metric: detected bridge
                    try:
                        if edge_kwargs.get('event_type') == 'bridge':
                            BRIDGE_EVENTS.labels(stage="detected").inc()
                    except Exception:
                        pass
                    edge = TraceEdge(**edge_kwargs)
                    result.edges.append(edge)
                    try:
                        et = edge_kwargs.get('event_type') or 'native'
                        TRACE_EDGES_CREATED.labels(event_type=str(et)).inc()
                    except Exception:
                        pass
                    result.total_edges += 1
                    
                    # Create tainted transaction record
                    tainted_tx = TaintedTransaction(
                        tx_hash=tx['tx_hash'],
                        from_address=tx['from_address'],
                        to_address=tx['to_address'],
                        value=Decimal(str(tx['value'])),
                        timestamp=tx['timestamp'],
                        taint_amount=taint_value,
                        taint_score=float(taint_score),
                        hop_distance=hop + 1,
                        path=path + [next_address]
                    )
                    result.tainted_transactions.append(tainted_tx)
                    
                    # Add to queue for next hop
                    queue.append((
                        next_address,
                        effective_taint,
                        hop + 1,
                        path + [next_address]
                    ))

                # Cross-chain expansion via persisted BRIDGE_LINKs
                try:
                    if request.enable_bridge:
                        bridge_links = await asyncio.wait_for(self._get_bridge_links(current_address), timeout=io_timeout)
                    else:
                        bridge_links = []
                except asyncio.TimeoutError:
                    logger.warning(f"trace {trace_id}: bridge_links timeout @ {current_address}")
                    bridge_links = []
                except Exception:
                    bridge_links = []
                for bl in bridge_links:
                    # Build synthetic tx-like record for uniform handling
                    tx_hash = bl.get('tx_hash') or f"bridge_{bl.get('chain_from','')}_{bl.get('chain_to','')}"
                    next_address = bl.get('counterparty')
                    if not next_address:
                        continue
                    next_address = next_address.lower()
                    # Propagate taint across bridge using haircut model (slight decay)
                    cross_taint = current_taint * Decimal(str(request.bridge_decay))
                    # Create cross-chain edge
                    edge = TraceEdge(
                        from_address=current_address if request.direction != TraceDirection.BACKWARD else next_address,
                        to_address=next_address if request.direction != TraceDirection.BACKWARD else current_address,
                        tx_hash=tx_hash,
                        value=Decimal(0),
                        taint_value=cross_taint,
                        timestamp=bl.get('timestamp') or datetime.utcnow().isoformat(),
                        hop=hop + 1,
                        event_type='bridge',
                        bridge=bl.get('bridge'),
                        chain_from=bl.get('chain_from'),
                        chain_to=bl.get('chain_to'),
                    )
                    result.edges.append(edge)
                    try:
                        TRACE_EDGES_CREATED.labels(event_type='bridge').inc()
                    except Exception:
                        pass
                    result.total_edges += 1
                    # Create/update node on the other chain
                    if next_address not in result.nodes:
                        next_node = TraceNode(
                            address=next_address,
                            hop_distance=hop + 1,
                            labels=await self.labels_service.get_labels(next_address)
                        )
                        result.nodes[next_address] = next_node
                        result.total_nodes += 1
                    else:
                        next_node = result.nodes[next_address]
                    next_node.taint_received += cross_taint
                    if current_address in result.nodes:
                        result.nodes[current_address].taint_sent += cross_taint
                    # Metrics
                    try:
                        BRIDGE_EVENTS.labels(stage="detected").inc()
                    except Exception:
                        pass
                    # Enqueue next hop across chain
                    queue.append((
                        next_address,
                        cross_taint,
                        hop + 1,
                        path + [next_address]
                    ))
                
                # Emit progress status (throttled)
                emit_every = max(0.05, float(getattr(request, "progress_emit_interval_ms", 500)) / 1000.0)
                if (now_ts - last_emit) >= emit_every:
                    queue_len = len(queue)
                    denom = max(1, processed_steps + queue_len)
                    percent = int(min(100, max(0, (processed_steps / denom) * 100)))
                    logger.info(
                        f"Trace {trace_id} progress: {percent}% | processed={processed_steps} queue={queue_len} nodes={result.total_nodes} edges={result.total_edges} hop={hop}"
                    )
                    last_emit = now_ts

                result.max_hop_reached = max(result.max_hop_reached, hop)
            
            # Analyze results
            await self._analyze_results(result)
            
            result.completed = True
            
        except Exception as e:
            logger.error(f"Error in trace {trace_id}: {e}", exc_info=True)
            result.error = str(e)
        
        finally:
            end_time = datetime.utcnow()
            result.execution_time_seconds = (end_time - start_time).total_seconds()
            logger.info(
                f"Trace {trace_id} completed: {result.total_nodes} nodes, "
                f"{result.total_edges} edges in {result.execution_time_seconds:.2f}s"
            )

        
        return result

    async def _get_bridge_links(self, address: str) -> List[Dict]:
        """Fetch cross-chain bridge links for an address from Neo4j
        Returns list of dicts with keys: counterparty, chain_from, chain_to, bridge, tx_hash, timestamp
        """
        try:
            query = """
            MATCH (a:Address {address: $address})-[r:BRIDGE_LINK]->(b:Address)
            RETURN b.address AS counterparty, r.chain_from AS chain_from, r.chain_to AS chain_to,
                   r.bridge AS bridge, r.tx_hash AS tx_hash, r.timestamp AS timestamp
            LIMIT 100
            """
            rows = await neo4j_client.run_query(query, {"address": address.lower()})
            return rows or []
        except Exception as e:
            logger.debug(f"_get_bridge_links error for {address}: {e}")
            return []

    async def _get_utxo_outgoing(
        self,
        address: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch UTXO spends from address (best-effort)"""
        try:
            from app.db.postgres_client import postgres_client  # type: ignore
            rows = await postgres_client.get_utxo_transactions(
                address=address,
                direction='outgoing',
                start_time=datetime.fromisoformat(start_time) if start_time else None,
                end_time=datetime.fromisoformat(end_time) if end_time else None,
                limit=1000,
            )
            return rows or []
        except Exception:
            return []

    async def _get_utxo_incoming(
        self,
        address: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch UTXO receives to address (best-effort)"""
        try:
            from app.db.postgres_client import postgres_client  # type: ignore
            rows = await postgres_client.get_utxo_transactions(
                address=address,
                direction='incoming',
                start_time=datetime.fromisoformat(start_time) if start_time else None,
                end_time=datetime.fromisoformat(end_time) if end_time else None,
                limit=1000,
            )
            return rows or []
        except Exception:
            return []
    
    async def _calculate_taint(
        self,
        tx: Dict,
        current_address: str,
        current_taint: Decimal,
        model: TaintModel,
        all_transactions: List[Dict]
    ) -> Tuple[Decimal, float]:
        """
        Calculate taint for a transaction using specified model
        
        Returns:
            (taint_value, taint_score)
        """
        tx_value = Decimal(str(tx['value']))
        
        # Defaults (avoid unreachable else for Enum exhaustive checks)
        taint_value: Decimal = Decimal(0)
        taint_score: float = 0.0

        if model == TaintModel.PROPORTIONAL:
            # Taint proportional to transaction value / total outflow
            total_outflow = sum(
                Decimal(str(t['value']))
                for t in all_transactions
                if t['from_address'].lower() == current_address
            )
            
            if total_outflow > 0:
                taint_ratio = tx_value / total_outflow
                taint_value = current_taint * taint_ratio
                taint_score = float(taint_value / tx_value) if tx_value > 0 else 0
            else:
                taint_value = Decimal(0)
                taint_score = 0.0
        
        elif model == TaintModel.FIFO:
            # First-In-First-Out: Earlier transactions get full taint
            # Simplified: Give full taint until depleted
            remaining_taint = current_taint
            
            if remaining_taint >= tx_value:
                taint_value = tx_value
                taint_score = 1.0
            else:
                taint_value = remaining_taint
                taint_score = float(taint_value / tx_value) if tx_value > 0 else 0
        
        elif model == TaintModel.HAIRCUT:
            # Fixed percentage reduction per hop (e.g., 10% haircut)
            haircut_rate = Decimal("0.9")  # 90% propagates
            taint_value = current_taint * haircut_rate * (tx_value / sum(Decimal(str(t['value'])) for t in all_transactions))
            taint_score = float(taint_value / tx_value) if tx_value > 0 else 0
        
        # return computed values (defaults if none of the branches adjusted them)
        return taint_value, taint_score
    
    async def _get_outgoing_transactions(
        self,
        address: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict]:
        """Fetch outgoing transactions from database"""
        from app.db.postgres_client import postgres_client
        
        try:
            # Use TimescaleDB client
            transactions = await postgres_client.get_transactions(
                address=address,
                direction='outgoing',
                start_time=datetime.fromisoformat(start_time) if start_time else None,
                end_time=datetime.fromisoformat(end_time) if end_time else None,
                limit=1000
            )
            return transactions
        except Exception as e:
            logger.error(f"Error fetching outgoing transactions: {e}")
            return []
    
    async def _get_incoming_transactions(
        self,
        address: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict]:
        """Fetch incoming transactions from database"""
        from app.db.postgres_client import postgres_client
        
        try:
            transactions = await postgres_client.get_transactions(
                address=address,
                direction='incoming',
                start_time=datetime.fromisoformat(start_time) if start_time else None,
                end_time=datetime.fromisoformat(end_time) if end_time else None,
                limit=1000
            )
            return transactions
        except Exception as e:
            logger.error(f"Error fetching incoming transactions: {e}")
            return []
    
    async def _analyze_results(self, result: TraceResult):
        """Analyze trace results for high-risk patterns"""
        # Find high-risk addresses
        for address, node in result.nodes.items():
            # Check labels
            if "sanctioned" in node.labels or "ofac" in node.labels:
                result.sanctioned_addresses.append(address)
                result.high_risk_addresses.append(address)
            
            if "scam" in node.labels or "mixer" in node.labels:
                result.high_risk_addresses.append(address)
        
        # Calculate total taint traced
        result.total_taint_traced = sum(
            (edge.taint_value for edge in result.edges), start=Decimal(0)
        )
        
        logger.info(
            f"Analysis: {len(result.high_risk_addresses)} high-risk addresses, "
            f"{len(result.sanctioned_addresses)} sanctioned addresses"
        )
