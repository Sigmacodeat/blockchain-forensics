"""
Pattern Detection Service

Erkennt verdächtige Muster im Transaction Graph:
- Circle Detection (Geldwäsche-Kreise)
- Layering Schemes (Komplexe Splitting-Strukturen)
- Smurf Patterns (Viele kleine Transaktionen)
- Rapid Movement (Schnelle Funds-Bewegung)
- Peel Chains (Schrittweiser Abbau)
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class PatternDetector:
    """Service für Pattern Detection im Transaction Graph"""
    
    def __init__(self):
        self.client = neo4j_client
        
    async def detect_circles(
        self,
        trace_id: Optional[str] = None,
        min_circle_length: int = 3,
        max_circle_length: int = 10,
        min_total_value: float = 0.0
    ) -> Dict[str, Any]:
        """
        Erkennt zirkuläre Transaktionsketten (potenzielle Geldwäsche).
        
        Args:
            trace_id: Optional - beschränkt auf Trace
            min_circle_length: Minimale Kreis-Länge
            max_circle_length: Maximale Kreis-Länge  
            min_total_value: Minimaler Gesamtwert (ETH)
            
        Returns:
            Dict mit detected circles und statistics
        """
        try:
            # Query für Kreise
            if trace_id:
                query = f"""
                MATCH (t:Trace {{trace_id: '{trace_id}'}})-[:INCLUDES]->(start:Address)
                MATCH path = (start)-[:TRANSACTION*{min_circle_length}..{max_circle_length}]->(start)
                WHERE ALL(r IN relationships(path) WHERE r.value >= {min_total_value})
                WITH path, 
                     [r IN relationships(path) | r.value] as values,
                     [n IN nodes(path) | n.address] as addresses
                RETURN addresses, 
                       values,
                       reduce(sum=0.0, v IN values | sum + v) as total_value,
                       length(path) as circle_length
                ORDER BY total_value DESC
                LIMIT 100
                """
            else:
                query = f"""
                MATCH path = (start:Address)-[:TRANSACTION*{min_circle_length}..{max_circle_length}]->(start)
                WHERE ALL(r IN relationships(path) WHERE r.value >= {min_total_value})
                WITH path,
                     [r IN relationships(path) | r.value] as values,
                     [n IN nodes(path) | n.address] as addresses
                RETURN addresses,
                       values,
                       reduce(sum=0.0, v IN values | sum + v) as total_value,
                       length(path) as circle_length
                ORDER BY total_value DESC
                LIMIT 100
                """
            
            async with self.client.get_session() as session:
                result = await session.run(query)
                circles = []
                
                async for record in result:
                    circles.append({
                        "addresses": record["addresses"],
                        "values": [float(v) for v in record["values"]],
                        "total_value": float(record["total_value"]),
                        "length": record["circle_length"],
                        "risk_score": self._calculate_circle_risk(
                            record["circle_length"],
                            float(record["total_value"])
                        )
                    })
                
                return {
                    "pattern": "circles",
                    "trace_id": trace_id,
                    "detected": circles,
                    "count": len(circles),
                    "statistics": {
                        "avg_circle_length": sum(c["length"] for c in circles) / len(circles) if circles else 0,
                        "total_value_circulated": sum(c["total_value"] for c in circles),
                        "high_risk_count": len([c for c in circles if c["risk_score"] >= 70])
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Circle detection failed: {e}")
            raise
            
    def _calculate_circle_risk(self, length: int, total_value: float) -> int:
        """Berechnet Risk Score für einen Circle (0-100)"""
        # Längere Kreise = höheres Risiko (Layering)
        length_score = min(30, length * 3)
        
        # Höhere Werte = höheres Risiko
        value_score = min(40, int(total_value * 10))
        
        # Perfect circle (gleiche Werte) = höheres Risiko
        base_score = 30
        
        return min(100, base_score + length_score + value_score)
    
    async def detect_layering(
        self,
        source_address: str,
        max_depth: int = 5,
        min_split_count: int = 3
    ) -> Dict[str, Any]:
        """
        Erkennt Layering Schemes (komplexe Splitting-Strukturen).
        
        Args:
            source_address: Start-Adresse
            max_depth: Maximale Tiefe
            min_split_count: Minimale Anzahl Splits pro Layer
            
        Returns:
            Dict mit layering structure und risk assessment
        """
        try:
            query = """
            MATCH path = (source:Address {address: $address})-[:TRANSACTION*1..$max_depth]->(end:Address)
            WITH path, nodes(path) as nodes_in_path
            UNWIND range(0, size(nodes_in_path)-2) as idx
            WITH nodes_in_path[idx] as from_node, 
                 nodes_in_path[idx+1] as to_node,
                 idx as depth
            WITH from_node, depth, collect(to_node) as targets
            WHERE size(targets) >= $min_splits
            RETURN from_node.address as address,
                   depth,
                   size(targets) as split_count,
                   [t IN targets | t.address] as target_addresses
            ORDER BY depth, split_count DESC
            """
            
            async with self.client.get_session() as session:
                result = await session.run(
                    query,
                    address=source_address.lower(),
                    max_depth=max_depth,
                    min_splits=min_split_count
                )
                
                layers = []
                async for record in result:
                    layers.append({
                        "address": record["address"],
                        "depth": record["depth"],
                        "split_count": record["split_count"],
                        "targets": record["target_addresses"]
                    })
                
                # Calculate risk
                total_splits = sum(l["split_count"] for l in layers)
                max_splits = max([l["split_count"] for l in layers]) if layers else 0
                depth_count = len(set(l["depth"] for l in layers))
                
                risk_score = min(100, 
                    20 + (depth_count * 15) + (max_splits * 5) + (len(layers) * 3)
                )
                
                return {
                    "pattern": "layering",
                    "source_address": source_address,
                    "layers": layers,
                    "statistics": {
                        "total_layers": len(layers),
                        "total_splits": total_splits,
                        "max_splits_per_layer": max_splits,
                        "depth_levels": depth_count,
                        "risk_score": risk_score
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Layering detection failed: {e}")
            raise
    
    async def detect_smurf_patterns(
        self,
        address: str,
        time_window_hours: int = 24,
        min_tx_count: int = 10,
        max_tx_value: float = 0.1
    ) -> Dict[str, Any]:
        """
        Erkennt Smurfing (viele kleine Transaktionen in kurzer Zeit).
        
        Args:
            address: Ziel-Adresse
            time_window_hours: Zeitfenster in Stunden
            min_tx_count: Minimale TX-Anzahl
            max_tx_value: Maximaler Wert pro TX
            
        Returns:
            Dict mit smurf pattern details
        """
        try:
            # Zeitbereich berechnen
            now = datetime.utcnow()
            start_time = now - timedelta(hours=time_window_hours)
            
            query = """
            MATCH (source:Address)-[tx:TRANSACTION]->(target:Address {address: $address})
            WHERE tx.timestamp >= $start_time
              AND tx.value <= $max_value
              AND tx.value > 0
            WITH source, target, collect(tx) as transactions
            WHERE size(transactions) >= $min_count
            RETURN source.address as source_address,
                   size(transactions) as tx_count,
                   reduce(sum=0.0, tx IN transactions | sum + tx.value) as total_value,
                   [tx IN transactions | tx.value] as values,
                   [tx IN transactions | tx.timestamp] as timestamps
            ORDER BY tx_count DESC
            """
            
            async with self.client.get_session() as session:
                result = await session.run(
                    query,
                    address=address.lower(),
                    start_time=start_time.isoformat(),
                    max_value=max_tx_value,
                    min_count=min_tx_count
                )
                
                patterns = []
                async for record in result:
                    avg_value = record["total_value"] / record["tx_count"]
                    
                    patterns.append({
                        "source_address": record["source_address"],
                        "tx_count": record["tx_count"],
                        "total_value": float(record["total_value"]),
                        "avg_value": float(avg_value),
                        "values": [float(v) for v in record["values"]],
                        "risk_score": self._calculate_smurf_risk(
                            record["tx_count"],
                            float(record["total_value"])
                        )
                    })
                
                return {
                    "pattern": "smurfing",
                    "target_address": address,
                    "time_window_hours": time_window_hours,
                    "detected_sources": patterns,
                    "count": len(patterns),
                    "statistics": {
                        "total_transactions": sum(p["tx_count"] for p in patterns),
                        "total_value": sum(p["total_value"] for p in patterns),
                        "high_risk_count": len([p for p in patterns if p["risk_score"] >= 70])
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Smurf pattern detection failed: {e}")
            raise
            
    def _calculate_smurf_risk(self, tx_count: int, total_value: float) -> int:
        """Berechnet Risk Score für Smurfing (0-100)"""
        # Mehr Transaktionen = höheres Risiko
        count_score = min(50, tx_count * 2)
        
        # Höherer Gesamtwert = höheres Risiko
        value_score = min(40, int(total_value * 20))
        
        base_score = 10
        
        return min(100, base_score + count_score + value_score)
    
    async def detect_peel_chains(
        self,
        source_address: str,
        min_chain_length: int = 5,
        peel_percentage: float = 0.9
    ) -> Dict[str, Any]:
        """
        Erkennt Peel Chains (schrittweiser Abbau durch viele kleine Abzweigungen).
        
        Args:
            source_address: Start-Adresse
            min_chain_length: Minimale Chain-Länge
            peel_percentage: Prozentsatz der Hauptkette (vs. Abzweigungen)
            
        Returns:
            Dict mit peel chain details
        """
        try:
            query = """
            MATCH path = (source:Address {address: $address})-[:TRANSACTION*1..20]->(end:Address)
            WITH path, relationships(path) as rels
            WHERE size(rels) >= $min_length
            WITH path, rels,
                 [r IN rels | r.value] as values
            WITH path, values,
                 reduce(total=0.0, v IN values | total + v) as total_value
            WHERE values[0] * $peel_pct <= total_value
            RETURN [n IN nodes(path) | n.address] as addresses,
                   values,
                   total_value,
                   size(values) as chain_length
            ORDER BY chain_length DESC, total_value DESC
            LIMIT 50
            """
            
            async with self.client.get_session() as session:
                result = await session.run(
                    query,
                    address=source_address.lower(),
                    min_length=min_chain_length,
                    peel_pct=peel_percentage
                )
                
                chains = []
                async for record in result:
                    values = [float(v) for v in record["values"]]
                    
                    # Berechne Peel-Rate (Abnahme pro Hop)
                    peel_rates = []
                    for i in range(len(values) - 1):
                        if values[i] > 0:
                            peel_rates.append(1 - (values[i+1] / values[i]))
                    
                    avg_peel_rate = sum(peel_rates) / len(peel_rates) if peel_rates else 0
                    
                    chains.append({
                        "addresses": record["addresses"],
                        "values": values,
                        "total_value": float(record["total_value"]),
                        "chain_length": record["chain_length"],
                        "avg_peel_rate": float(avg_peel_rate),
                        "risk_score": self._calculate_peel_risk(
                            record["chain_length"],
                            avg_peel_rate
                        )
                    })
                
                return {
                    "pattern": "peel_chain",
                    "source_address": source_address,
                    "detected_chains": chains,
                    "count": len(chains),
                    "statistics": {
                        "avg_chain_length": sum(c["chain_length"] for c in chains) / len(chains) if chains else 0,
                        "longest_chain": max([c["chain_length"] for c in chains]) if chains else 0,
                        "total_value_peeled": sum(c["total_value"] for c in chains)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Peel chain detection failed: {e}")
            raise
            
    def _calculate_peel_risk(self, chain_length: int, avg_peel_rate: float) -> int:
        """Berechnet Risk Score für Peel Chain (0-100)"""
        # Längere Chains = höheres Risiko
        length_score = min(40, chain_length * 4)
        
        # Konsistente Peel-Rate = höheres Risiko (strukturiert)
        rate_score = min(40, int(avg_peel_rate * 100))
        
        base_score = 20
        
        return min(100, base_score + length_score + rate_score)
    
    async def detect_rapid_movement(
        self,
        address: str,
        max_time_seconds: int = 300,
        min_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Erkennt schnelle Geldbewegungen (potenzielle Flucht).
        
        Args:
            address: Start-Adresse
            max_time_seconds: Maximale Zeit zwischen Hops
            min_hops: Minimale Hop-Anzahl
            
        Returns:
            Dict mit rapid movement paths
        """
        try:
            query = """
            MATCH path = (source:Address {address: $address})-[:TRANSACTION*1..10]->(end:Address)
            WITH path, relationships(path) as rels
            WHERE size(rels) >= $min_hops
            WITH path, rels,
                 [r IN rels | r.timestamp] as timestamps,
                 [r IN rels | r.value] as values
            WITH path, timestamps, values,
                 duration.inSeconds(
                     datetime(timestamps[0]), 
                     datetime(timestamps[size(timestamps)-1])
                 ).seconds as duration_seconds
            WHERE duration_seconds <= $max_seconds AND duration_seconds > 0
            RETURN [n IN nodes(path) | n.address] as addresses,
                   values,
                   timestamps,
                   duration_seconds,
                   size(values) as hop_count
            ORDER BY duration_seconds ASC
            LIMIT 50
            """
            
            async with self.client.get_session() as session:
                result = await session.run(
                    query,
                    address=address.lower(),
                    max_seconds=max_time_seconds,
                    min_hops=min_hops
                )
                
                movements = []
                async for record in result:
                    duration = record["duration_seconds"]
                    hop_count = record["hop_count"]
                    hops_per_minute = (hop_count / duration) * 60 if duration > 0 else 0
                    
                    movements.append({
                        "addresses": record["addresses"],
                        "values": [float(v) for v in record["values"]],
                        "timestamps": record["timestamps"],
                        "duration_seconds": duration,
                        "hop_count": hop_count,
                        "hops_per_minute": float(hops_per_minute),
                        "risk_score": self._calculate_rapid_risk(hop_count, duration)
                    })
                
                return {
                    "pattern": "rapid_movement",
                    "source_address": address,
                    "detected_movements": movements,
                    "count": len(movements),
                    "statistics": {
                        "fastest_movement_seconds": min([m["duration_seconds"] for m in movements]) if movements else 0,
                        "avg_hops_per_minute": sum(m["hops_per_minute"] for m in movements) / len(movements) if movements else 0,
                        "high_risk_count": len([m for m in movements if m["risk_score"] >= 70])
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Rapid movement detection failed: {e}")
            raise
            
    def _calculate_rapid_risk(self, hop_count: int, duration_seconds: int) -> int:
        """Berechnet Risk Score für Rapid Movement (0-100)"""
        # Mehr Hops in kurzer Zeit = höheres Risiko
        speed = hop_count / (duration_seconds / 60) if duration_seconds > 0 else 0
        speed_score = min(60, int(speed * 10))
        
        # Viele Hops = höheres Risiko
        hop_score = min(30, hop_count * 3)
        
        base_score = 10
        
        return min(100, base_score + speed_score + hop_score)


# Singleton instance
pattern_detector = PatternDetector()
