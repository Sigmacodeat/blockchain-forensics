from typing import Optional, Dict, Any  # ensure types available for top-level helper

from typing import Optional, Dict, Any

def resolve_counterpart_chain(receipt: Optional[Dict[str, Any]], to_addr: Optional[str], chain: Optional[str] = None) -> str:
    """Resolve destination chain for a bridge tx using registry and log topic hints.

    Args:
        receipt: Transaction receipt with optional `logs` entries (each with topics[])
        to_addr: Destination contract address (bridge contract)
        chain: Source chain name (optional)

    Returns:
        Counterpart chain name or "unknown" if ambiguous.
    """
    try:
        if to_addr:
            c = bridge_registry.get_contract(str(to_addr), (chain or "").lower() or ("ethereum"))
            if c:
                if len(c.counterpart_chains) == 1:
                    return c.counterpart_chains[0]
        # Topic-based hints from settings/ENV mapping
        topic_chain_map: Dict[str, str] = {}
        cfg = getattr(settings, "BRIDGE_TOPICS_CHAIN_HINTS", None)
        if isinstance(cfg, dict):
            topic_chain_map = cfg
        else:
            env_val = os.getenv("BRIDGE_TOPICS_CHAIN_HINTS")
            if env_val:
                try:
                    parsed = json.loads(env_val)
                    if isinstance(parsed, dict):
                        topic_chain_map = parsed
                except Exception:
                    topic_chain_map = {}
        if receipt and isinstance(receipt.get("logs"), list) and topic_chain_map:
            for lg in receipt.get("logs", []):
                try:
                    topics = lg.get("topics") or []
                    if not topics:
                        continue
                    t0 = topics[0].hex() if hasattr(topics[0], "hex") else str(topics[0])
                    if isinstance(t0, str):
                        hint = topic_chain_map.get(t0.lower())
                        if isinstance(hint, str) and hint:
                            return hint
                except Exception:
                    continue
    except Exception:
        pass
    return "unknown"

"""Bridge Detection Service - Erkennung und Persistierung von Cross-Chain Bridge-Events"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.bridge.registry import bridge_registry, BridgeContract
from app.config import settings
import os
import json
from app.schemas import CanonicalEvent
try:
    # Prefer central metrics module
    from app.metrics import BRIDGE_EVENTS  # type: ignore
except Exception:
    try:
        # Fallback for legacy path
        from app.observability.metrics import BRIDGE_EVENTS  # type: ignore
    except Exception:
        BRIDGE_EVENTS = None  # type: ignore

logger = logging.getLogger(__name__)


class BridgeDetectionService:
    """
    Service zur Erkennung von Bridge-Transaktionen und Persistierung von Bridge-Links.
    
    Features:
    - Automatische Bridge-Erkennung in Transaktionen
    - Extraktion von Bridge-Parametern
    - Inferenz von Source/Destination Chains
    - Persistierung von :BRIDGE_LINK Edges in Neo4j
    """
    
    def __init__(self):
        self.registry = bridge_registry
    
    def detect_bridge_transaction(
        self,
        event: CanonicalEvent,
        raw_tx: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Erkenne ob eine Transaktion ein Bridge-Event ist.
        
        Args:
            event: Canonical Event
            raw_tx: Optional raw transaction data für erweiterte Analyse
            
        Returns:
            Bridge-Info dict oder None wenn kein Bridge erkannt
        """
        # Check contract address
        if event.contract_address:
            contract = self.registry.get_contract(event.contract_address, event.chain)
            if contract:
                info = self._extract_bridge_info(event, contract, raw_tx)
                try:
                    if BRIDGE_EVENTS is not None:
                        BRIDGE_EVENTS.labels(stage="detected").inc()
                except Exception:
                    pass
                return info
        
        # Check to_address (for simple transfers to bridge contracts)
        if event.to_address:
            contract = self.registry.get_contract(event.to_address, event.chain)
            if contract:
                info = self._extract_bridge_info(event, contract, raw_tx)
                try:
                    if BRIDGE_EVENTS is not None:
                        BRIDGE_EVENTS.labels(stage="detected").inc()
                except Exception:
                    pass
                return info
        
        # Check method selector in metadata
        if event.metadata.get('bridge_method'):
            method = event.metadata['bridge_method']
            if self.registry.is_bridge_method(method):
                # Bridge detected via method, try to find contract
                info = self._extract_bridge_info_from_method(event, method, raw_tx)
                try:
                    if BRIDGE_EVENTS is not None:
                        BRIDGE_EVENTS.labels(stage="detected").inc()
                except Exception:
                    pass
                return info
        
        return None
    
    def _extract_bridge_info(
        self,
        event: CanonicalEvent,
        contract: BridgeContract,
        raw_tx: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extrahiere Bridge-Informationen aus Event und Contract"""
        
        # Inferiere Destination-Chain
        destination_chain = self._infer_destination_chain(event, contract, raw_tx)
        
        bridge_info = {
            "bridge_contract": contract.address,
            "bridge_name": contract.name,
            "bridge_type": contract.bridge_type,
            "source_chain": event.chain,
            "destination_chain": destination_chain,
            "tx_hash": event.tx_hash,
            "from_address": event.from_address,
            "to_address": event.to_address,
            "value": str(event.value),
            "timestamp": event.block_timestamp.isoformat(),
            "detected_at": datetime.utcnow().isoformat(),
        }
        
        # Füge Token-Info hinzu wenn vorhanden
        if event.token_address:
            bridge_info["token_address"] = event.token_address
            bridge_info["token_symbol"] = event.token_symbol
        
        # ERC20 Transfers aus Metadata
        if event.metadata.get("erc20_transfers"):
            bridge_info["erc20_transfers"] = event.metadata["erc20_transfers"]
        
        return bridge_info
    
    def _extract_bridge_info_from_method(
        self,
        event: CanonicalEvent,
        method: str,
        raw_tx: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extrahiere Bridge-Info wenn nur Method-Selector bekannt ist"""
        
        return {
            "bridge_method": method,
            "source_chain": event.chain,
            "destination_chain": "unknown",  # Kann nicht inferiert werden
            "tx_hash": event.tx_hash,
            "from_address": event.from_address,
            "to_address": event.to_address,
            "value": str(event.value),
            "timestamp": event.block_timestamp.isoformat(),
            "detected_at": datetime.utcnow().isoformat(),
        }
    
    def persist_bridge_link(
        self,
        from_address: str,
        to_address: str,
        props: Dict[str, Any]
    ) -> bool:
        """Persistiere einen :BRIDGE_LINK Edge idempotent in Neo4j.

        Args:
            from_address: Quelladresse
            to_address: Zieladresse (Destination Address)
            props: Properties inkl. chain_from, chain_to, bridge, tx_hash, timestamp, value, token_*

        Returns:
            True bei Erfolg, sonst False (z.B. wenn DB nicht verfügbar).
        """
        try:
            from app.db.neo4j_client import neo4j_client
            if not getattr(neo4j_client, "driver", None) and not getattr(neo4j_client, "query_sync", None):
                return False

            cypher = (
                """
                MERGE (a:Address {address: $from})
                MERGE (b:Address {address: $to})
                MERGE (a)-[r:BRIDGE_LINK {tx_hash: $tx_hash}]->(b)
                SET r.bridge = $bridge,
                    r.bridge_contract = coalesce($bridge_contract, r.bridge_contract),
                    r.chain_from = $chain_from,
                    r.chain_to = $chain_to,
                    r.timestamp = $timestamp,
                    r.value = $value,
                    r.token_address = $token_address,
                    r.token_symbol = $token_symbol
                RETURN 1 AS ok
                """
            )
            params = {
                "from": (from_address or "").lower(),
                "to": (to_address or "").lower(),
                "tx_hash": props.get("tx_hash"),
                "bridge": props.get("bridge") or props.get("bridge_name"),
                "bridge_contract": props.get("bridge_contract"),
                "chain_from": props.get("chain_from") or props.get("source_chain"),
                "chain_to": props.get("chain_to") or props.get("destination_chain"),
                "timestamp": props.get("timestamp"),
                "value": props.get("value"),
                "token_address": props.get("token_address"),
                "token_symbol": props.get("token_symbol"),
            }
            if hasattr(neo4j_client, "query_sync"):
                neo4j_client.query_sync(cypher, params)  # type: ignore
                try:
                    if BRIDGE_EVENTS is not None:
                        BRIDGE_EVENTS.labels(stage="persisted").inc()
                except Exception:
                    pass
                return True
            return False
        except Exception as e:
            logger.warning(f"persist_bridge_link error: {e}")
            return False

    def analyze_bridge_flow(
        self,
        address: str,
        max_hops: int = 5
    ) -> Dict[str, Any]:
        """Analysiere Bridge-Flows ab einer Adresse über :BRIDGE_LINK Kanten.

        Returns:
            { address, total_flows, max_hops_found, flows: [...], analysis_timestamp }
        """
        try:
            from app.db.neo4j_client import neo4j_client
            if not getattr(neo4j_client, "driver", None) and not getattr(neo4j_client, "query_sync", None):
                return {
                    "address": address,
                    "total_flows": 0,
                    "max_hops_found": 0,
                    "flows": [],
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                }

            # Pfade bis max_hops extrahieren und zusammenfassen
            cypher = (
                """
                MATCH p=(a:Address {address: $address})- [r:BRIDGE_LINK*1..$max_hops]->(dest:Address)
                WITH p, relationships(p) AS rels
                WITH p, rels, size(rels) AS hops
                RETURN hops,
                       rels[0].chain_from AS chain_from,
                       rels[-1].chain_to AS chain_to,
                       [x IN rels | x.tx_hash] AS tx_path,
                       [x IN rels | coalesce(x.bridge, '')] AS bridges
                ORDER BY hops DESC
                LIMIT 200
                """
            )
            params = {"address": (address or "").lower(), "max_hops": int(max(1, min(max_hops, 10)))}
            if hasattr(neo4j_client, "query_sync"):
                rows = neo4j_client.query_sync(cypher, params)  # type: ignore
            else:
                rows = []

            flows = [
                {
                    "hops": int(r.get("hops", 0)),
                    "chain_from": r.get("chain_from"),
                    "chain_to": r.get("chain_to"),
                    "tx_path": r.get("tx_path") or [],
                    "bridges": r.get("bridges") or [],
                }
                for r in rows
            ]
            total = len(flows)
            max_found = max((f.get("hops", 0) for f in flows), default=0)

            return {
                "address": address,
                "total_flows": total,
                "max_hops_found": max_found,
                "flows": flows,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"analyze_bridge_flow error: {e}")
            return {
                "address": address,
                "total_flows": 0,
                "max_hops_found": 0,
                "flows": [],
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }
    def _infer_destination_chain(
        self,
        event: CanonicalEvent,
        contract: BridgeContract,
        raw_tx: Optional[Dict[str, Any]]
    ) -> str:
        """
        Inferiere Destination-Chain aus verfügbaren Daten.
        
        Heuristiken:
        1. Check metadata für explizite Chain-Info
        2. Check counterpart_chains wenn nur eine Option
        3. Fallback zu "unknown"
        """
        # Check metadata
        if event.metadata.get("destination_chain"):
            return event.metadata["destination_chain"]
        # Some adapters may provide richer hints
        for k in ("bridge_destination", "counterpart_chain", "to_chain"):
            v = event.metadata.get(k)
            if isinstance(v, str) and v:
                return v
        
        # Wenn nur eine Counterpart-Chain, nehme diese
        if len(contract.counterpart_chains) == 1:
            return contract.counterpart_chains[0]

        # Heuristik: Logs parsen und anhand bekannter Topics Chain ableiten (konfigurierbar)
        try:
            # Expect mapping like { topic0_hex_lower: "chain_name" }
            topic_chain_map: Dict[str, str] = {}
            
            # First check env var (for testing), then settings
            env_val = os.getenv("BRIDGE_TOPICS_CHAIN_HINTS")
            if env_val:
                try:
                    parsed = json.loads(env_val)
                    if isinstance(parsed, dict):
                        topic_chain_map = parsed
                except Exception:
                    pass
            
            # If no env var or parse failed, use settings
            if not topic_chain_map:
                cfg = getattr(settings, "BRIDGE_TOPICS_CHAIN_HINTS", None)
                if isinstance(cfg, dict):
                    topic_chain_map = cfg
            
            logger.debug(f"Bridge topic_chain_map: {topic_chain_map}, raw_tx logs: {raw_tx.get('logs') if raw_tx else None}")
            # First, use compact logs stored in event.metadata['logs'] (address + topics hex)
            if isinstance(event.metadata, dict) and isinstance(event.metadata.get("logs"), list) and topic_chain_map:
                for lg in event.metadata.get("logs", []):
                    try:
                        topics = lg.get("topics") or []
                        if not topics:
                            continue
                        # topics are already hex strings, lowercase in adapter
                        t0 = topics[0]
                        if isinstance(t0, str):
                            chain_hint = topic_chain_map.get(t0.lower())
                            if isinstance(chain_hint, str) and chain_hint:
                                return chain_hint
                    except Exception:
                        continue
            # Fallback: inspect raw_tx logs if provided
            if raw_tx and isinstance(raw_tx.get("logs"), list) and topic_chain_map:
                for lg in raw_tx.get("logs", []):
                    try:
                        topics = lg.get("topics") or []
                        if not topics:
                            continue
                        t0 = topics[0].hex() if hasattr(topics[0], "hex") else str(topics[0])
                        if isinstance(t0, str):
                            chain_hint = topic_chain_map.get(t0.lower())
                            if isinstance(chain_hint, str) and chain_hint:
                                return chain_hint
                    except Exception as e:
                        logger.debug(f"Bridge topic parsing error: {e}")
                        continue
        except Exception:
            pass

        # Fallback: unbekannt bei Mehrdeutigkeit
        return "unknown"
    
    def create_bridge_link_data(
        self,
        bridge_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Erstelle Daten für Neo4j :BRIDGE_LINK Edge.
        
        Returns:
            Dict mit Edge-Properties
        """
        return {
            "chain_from": bridge_info["source_chain"],
            "chain_to": bridge_info.get("destination_chain", "unknown"),
            "bridge": bridge_info.get("bridge_name", "unknown"),
            "bridge_contract": bridge_info.get("bridge_contract", ""),
            "tx_hash": bridge_info["tx_hash"],
            "timestamp": bridge_info["timestamp"],
            "value": bridge_info.get("value", "0"),
            "token_address": bridge_info.get("token_address"),
            "token_symbol": bridge_info.get("token_symbol"),
        }
    
    def get_bridge_links_for_address(
        self,
        address: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Hole Bridge-Links für eine Adresse.
        
        Args:
            address: Wallet-Adresse
            limit: Max Anzahl Results
            
        Returns:
            Liste von Bridge-Link-Dicts
            
        Note: Nutzt Neo4j, wenn Client/Driver verfügbar. Fällt ansonsten auf leere Liste zurück.
        """
        try:
            from app.db.neo4j_client import neo4j_client
            if not getattr(neo4j_client, "driver", None):
                return []
            query = (
                """
                MATCH (a:Address {address: $address})-[r:BRIDGE_LINK]->(dest:Address)
                RETURN r.bridge AS bridge_name,
                       r.chain_from AS chain_from,
                       r.chain_to AS chain_to,
                       r.tx_hash AS tx_hash,
                       r.timestamp AS timestamp,
                       r.value AS value,
                       dest.address AS destination_address
                ORDER BY r.timestamp DESC
                LIMIT $limit
                """
            )
            params = {"address": address.lower(), "limit": int(limit)}
            # Prefer sync helper; avoid awaiting in sync context
            if hasattr(neo4j_client, "query_sync"):
                results = neo4j_client.query_sync(query, params)  # type: ignore
            else:
                # No sync API available in this context
                return []

            links: List[Dict[str, Any]] = [
                {
                    "bridge_name": r.get("bridge_name"),
                    "chain_from": r.get("chain_from"),
                    "chain_to": r.get("chain_to"),
                    "tx_hash": r.get("tx_hash"),
                    "timestamp": r.get("timestamp"),
                    "value": r.get("value"),
                    "destination_address": r.get("destination_address"),
                }
                for r in results
            ]
            return links
        except Exception as e:
            logger.warning(f"get_bridge_links_for_address error: {e}")
            return []


# Global Service-Instanz
bridge_detection_service = BridgeDetectionService()
