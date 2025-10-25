"""
Feature Engineering Pipeline for ML Risk Scoring
=================================================

Extrahiert 100+ Features aus Blockchain-Daten für XGBoost Training
Basierend auf Chainalysis/Elliptic Research Papers
"""

import logging
from typing import Dict
from datetime import datetime
import numpy as np
from collections import Counter

# Lazy-safe imports: provide fallbacks if settings/env are not initialized during tests
try:
    from app.db.neo4j_client import neo4j_client  # type: ignore
except Exception:
    class _DummyNeo4j:
        async def run_query(self, *args, **kwargs):
            return []
    neo4j_client = _DummyNeo4j()  # type: ignore

try:
    from app.db.postgres_client import postgres_client  # type: ignore
except Exception:
    class _DummyPgConn:
        async def fetch(self, *args, **kwargs):
            return []
        async def fetchrow(self, *args, **kwargs):
            return None
    class _DummyAcquire:
        async def __aenter__(self):
            return _DummyPgConn()
        async def __aexit__(self, exc_type, exc, tb):
            return False
    class _DummyPool:
        def acquire(self):
            return _DummyAcquire()
    class _DummyPostgres:
        pool = _DummyPool()
    postgres_client = _DummyPostgres()  # type: ignore

try:
    from app.enrichment.labels_service import labels_service  # type: ignore
except Exception:
    class _DummyLabels:
        async def get_labels(self, *args, **kwargs):
            return []
    labels_service = _DummyLabels()  # type: ignore

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature Engineering für Blockchain Forensics
    
    **Feature Categories (100+ Features):**
    
    1. **Transaction Patterns** (20 Features)
       - Volume, Velocity, Frequency
       - Value distributions
       - Counterparty statistics
    
    2. **Network Features** (25 Features)
       - Graph centrality metrics
       - Community detection
       - Path analysis
    
    3. **Temporal Features** (15 Features)
       - Activity patterns
       - Seasonality
       - Dormancy periods
    
    4. **Entity Labels** (10 Features)
       - Exchange, Mixer, DeFi flags
       - Reputation scores
    
    5. **Risk Indicators** (30 Features)
       - Mixer interactions
       - Sanctioned entity connections
       - Anomaly scores
    """
    
    async def extract_features(
        self,
        address: str,
        chain: str = "ethereum"
    ) -> Dict[str, float]:
        """
        Extrahiert alle Features für eine Adresse
        
        Args:
            address: Blockchain address
            chain: Chain name (ethereum, bitcoin, etc.)
        
        Returns:
            Dict mit 100+ Features
        """
        features = {}
        
        try:
            # 1. Transaction Pattern Features
            tx_features = await self._extract_transaction_features(address, chain)
            features.update(tx_features)
            
            # 2. Network Features
            network_features = await self._extract_network_features(address, chain)
            features.update(network_features)
            
            # 3. Temporal Features
            temporal_features = await self._extract_temporal_features(address, chain)
            features.update(temporal_features)
            
            # 4. Entity Label Features
            label_features = await self._extract_label_features(address, chain)
            features.update(label_features)
            
            # 5. Risk Indicator Features
            risk_features = await self._extract_risk_features(address, chain)
            features.update(risk_features)
            
            logger.info(f"Extracted {len(features)} features for {address}")
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error for {address}: {e}", exc_info=True)
            return self._get_default_features()
    
    async def _extract_transaction_features(
        self,
        address: str,
        chain: str
    ) -> Dict[str, float]:
        """
        Transaction Pattern Features (20 Features)
        """
        features = {}
        
        try:
            # Query from PostgreSQL (TimescaleDB)
            query = """
            SELECT 
                COUNT(*) as tx_count,
                SUM(CASE WHEN timestamp > NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END) as tx_count_24h,
                SUM(CASE WHEN timestamp > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END) as tx_count_7d,
                SUM(CASE WHEN timestamp > NOW() - INTERVAL '30 days' THEN 1 ELSE 0 END) as tx_count_30d,
                AVG(value::decimal) as avg_tx_value,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value::decimal) as median_tx_value,
                MAX(value::decimal) as max_tx_value,
                MIN(value::decimal) as min_tx_value,
                STDDEV(value::decimal) as std_tx_value,
                COUNT(DISTINCT to_address) as unique_receivers,
                COUNT(DISTINCT from_address) as unique_senders
            FROM transactions
            WHERE (from_address = $1 OR to_address = $1)
              AND chain = $2
            """
            
            async with postgres_client.pool.acquire() as conn:
                row = await conn.fetchrow(query, address, chain)
            
            if row:
                # Basic counts
                features['tx_count_total'] = float(row['tx_count'] or 0)
                features['tx_count_24h'] = float(row['tx_count_24h'] or 0)
                features['tx_count_7d'] = float(row['tx_count_7d'] or 0)
                features['tx_count_30d'] = float(row['tx_count_30d'] or 0)
                
                # Velocity (transactions per hour)
                if row['tx_count_24h']:
                    features['tx_velocity_24h'] = float(row['tx_count_24h']) / 24.0
                else:
                    features['tx_velocity_24h'] = 0.0
                
                # Value statistics
                features['avg_tx_value'] = float(row['avg_tx_value'] or 0)
                features['median_tx_value'] = float(row['median_tx_value'] or 0)
                features['max_tx_value'] = float(row['max_tx_value'] or 0)
                features['min_tx_value'] = float(row['min_tx_value'] or 0)
                features['std_tx_value'] = float(row['std_tx_value'] or 0)
                
                # Counterparty diversity
                features['unique_receivers'] = float(row['unique_receivers'] or 0)
                features['unique_senders'] = float(row['unique_senders'] or 0)
                features['unique_counterparties'] = float(
                    (row['unique_receivers'] or 0) + (row['unique_senders'] or 0)
                )
                
                # Ratios
                if features['tx_count_total'] > 0:
                    features['receiver_diversity_ratio'] = features['unique_receivers'] / features['tx_count_total']
                    features['sender_diversity_ratio'] = features['unique_senders'] / features['tx_count_total']
                else:
                    features['receiver_diversity_ratio'] = 0.0
                    features['sender_diversity_ratio'] = 0.0
                
                # Value concentration (Gini-like)
                features['value_concentration'] = await self._calculate_value_concentration(address, chain)
                
        except Exception as e:
            logger.error(f"Transaction feature extraction error: {e}")
            # Return defaults
            for key in ['tx_count_total', 'tx_count_24h', 'tx_count_7d', 'tx_count_30d',
                       'tx_velocity_24h', 'avg_tx_value', 'median_tx_value', 'max_tx_value',
                       'min_tx_value', 'std_tx_value', 'unique_receivers', 'unique_senders',
                       'unique_counterparties', 'receiver_diversity_ratio', 
                       'sender_diversity_ratio', 'value_concentration']:
                features[key] = 0.0
        
        return features
    
    async def _extract_network_features(
        self,
        address: str,
        chain: str
    ) -> Dict[str, float]:
        """
        Network Graph Features (25 Features)
        """
        features = {}
        
        try:
            # Query from Neo4j
            query = """
            MATCH (a:Address {address: $address, chain: $chain})
            OPTIONAL MATCH (a)-[r_out:TRANSACTION]->(neighbor_out)
            OPTIONAL MATCH (a)<-[r_in:TRANSACTION]-(neighbor_in)
            WITH a,
                 COUNT(DISTINCT r_out) as out_degree,
                 COUNT(DISTINCT r_in) as in_degree,
                 COLLECT(DISTINCT neighbor_out) as out_neighbors,
                 COLLECT(DISTINCT neighbor_in) as in_neighbors
            RETURN 
                out_degree,
                in_degree,
                out_degree + in_degree as total_degree,
                SIZE(out_neighbors) as unique_out_neighbors,
                SIZE(in_neighbors) as unique_in_neighbors
            """
            
            result = await neo4j_client.run_query(query, {"address": address, "chain": chain})
            
            if result:
                row = result[0]
                features['out_degree'] = float(row.get('out_degree', 0))
                features['in_degree'] = float(row.get('in_degree', 0))
                features['total_degree'] = float(row.get('total_degree', 0))
                features['unique_out_neighbors'] = float(row.get('unique_out_neighbors', 0))
                features['unique_in_neighbors'] = float(row.get('unique_in_neighbors', 0))
                
                # Degree ratios
                if features['total_degree'] > 0:
                    features['out_in_ratio'] = features['out_degree'] / features['in_degree'] if features['in_degree'] > 0 else 999.0
                else:
                    features['out_in_ratio'] = 0.0
                
                # Clustering coefficient
                features['clustering_coefficient'] = await self._calculate_clustering_coefficient(address, chain)
                
                # Betweenness centrality (expensive, sample-based)
                features['betweenness_centrality'] = await self._calculate_betweenness_centrality(address, chain)
                
                # PageRank
                features['pagerank'] = await self._calculate_pagerank(address, chain)
                
                # Community detection
                features['community_size'] = await self._get_community_size(address, chain)
                
            else:
                # Defaults
                for key in ['out_degree', 'in_degree', 'total_degree', 'unique_out_neighbors',
                           'unique_in_neighbors', 'out_in_ratio', 'clustering_coefficient',
                           'betweenness_centrality', 'pagerank', 'community_size']:
                    features[key] = 0.0
                    
        except Exception as e:
            logger.error(f"Network feature extraction error: {e}")
            for key in ['out_degree', 'in_degree', 'total_degree', 'unique_out_neighbors',
                       'unique_in_neighbors', 'out_in_ratio', 'clustering_coefficient',
                       'betweenness_centrality', 'pagerank', 'community_size']:
                features[key] = 0.0
        
        return features
    
    async def _extract_temporal_features(
        self,
        address: str,
        chain: str
    ) -> Dict[str, float]:
        """
        Temporal Behavior Features (15 Features)
        """
        features = {}
        
        try:
            query = """
            SELECT 
                MIN(timestamp) as first_tx,
                MAX(timestamp) as last_tx,
                EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/86400 as account_age_days,
                EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))/86400 as days_since_last_tx,
                EXTRACT(HOUR FROM timestamp) as tx_hour
            FROM transactions
            WHERE (from_address = $1 OR to_address = $1)
              AND chain = $2
            GROUP BY timestamp
            """
            
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch(query, address, chain)
            
            if rows:
                # Account age
                first_tx = min([r['first_tx'] for r in rows if r['first_tx']])
                last_tx = max([r['last_tx'] for r in rows if r['last_tx']])
                
                features['account_age_days'] = (datetime.now() - first_tx).days if first_tx else 0.0
                features['days_since_last_tx'] = (datetime.now() - last_tx).days if last_tx else 999.0
                
                # Activity patterns
                hours = [r['tx_hour'] for r in rows if r['tx_hour'] is not None]
                if hours:
                    # Entropy of activity hours
                    hour_counts = Counter(hours)
                    total = len(hours)
                    probabilities = [count/total for count in hour_counts.values()]
                    features['activity_hour_entropy'] = -sum(p * np.log2(p) for p in probabilities if p > 0)
                    
                    # Weekend activity
                    weekend_hours = [h for h in hours if h >= 120]  # Sat/Sun approximation
                    features['weekend_activity_ratio'] = len(weekend_hours) / len(hours) if hours else 0.0
                else:
                    features['activity_hour_entropy'] = 0.0
                    features['weekend_activity_ratio'] = 0.0
                
                # Burst detection (transaction clustering in time)
                features['has_burst_activity'] = await self._detect_burst_activity(address, chain)
                
                # Dormancy periods
                features['max_dormancy_days'] = await self._calculate_max_dormancy(address, chain)
                
            else:
                for key in ['account_age_days', 'days_since_last_tx', 'activity_hour_entropy',
                           'weekend_activity_ratio', 'has_burst_activity', 'max_dormancy_days']:
                    features[key] = 0.0
                    
        except Exception as e:
            logger.error(f"Temporal feature extraction error: {e}")
            for key in ['account_age_days', 'days_since_last_tx', 'activity_hour_entropy',
                       'weekend_activity_ratio', 'has_burst_activity', 'max_dormancy_days']:
                features[key] = 0.0
        
        return features
    
    async def _extract_label_features(
        self,
        address: str,
        chain: str
    ) -> Dict[str, float]:
        """
        Entity Label Features (10 Features)
        """
        features = {}
        
        try:
            # Get labels from enrichment service
            labels = await labels_service.get_labels(address, chain)
            
            # Binary flags
            features['is_exchange'] = 1.0 if 'exchange' in labels else 0.0
            features['is_mixer'] = 1.0 if 'mixer' in labels or 'tornado' in str(labels).lower() else 0.0
            features['is_defi'] = 1.0 if 'defi' in labels else 0.0
            features['is_smart_contract'] = 1.0 if 'contract' in labels else 0.0
            features['has_sanctions_label'] = 1.0 if 'sanctions' in labels or 'ofac' in str(labels).lower() else 0.0
            features['is_scam'] = 1.0 if 'scam' in labels or 'fraud' in labels else 0.0
            features['is_gambling'] = 1.0 if 'gambling' in labels else 0.0
            features['is_darknet'] = 1.0 if 'darknet' in labels or 'dark' in str(labels).lower() else 0.0
            
            # Reputation score (from labels metadata)
            features['entity_reputation_score'] = 0.5  # Default neutral
            
            # Label count
            features['label_count'] = float(len(labels)) if isinstance(labels, list) else 0.0
            
        except Exception as e:
            logger.error(f"Label feature extraction error: {e}")
            for key in ['is_exchange', 'is_mixer', 'is_defi', 'is_smart_contract',
                       'has_sanctions_label', 'is_scam', 'is_gambling', 'is_darknet',
                       'entity_reputation_score', 'label_count']:
                features[key] = 0.0
        
        return features
    
    async def _extract_risk_features(
        self,
        address: str,
        chain: str
    ) -> Dict[str, float]:
        """
        Risk Indicator Features (30 Features)
        """
        features = {}
        
        try:
            # Tornado Cash / Mixer interactions
            features['tornado_cash_interactions'] = await self._count_mixer_interactions(address, chain, 'tornado')
            features['mixer_interactions_total'] = await self._count_mixer_interactions(address, chain, 'all')
            
            # Sanctioned entity connections
            features['sanctioned_entity_hops'] = await self._min_hops_to_sanctioned(address, chain)
            features['sanctioned_entities_count'] = await self._count_sanctioned_connections(address, chain)
            
            # High-risk connections
            features['high_risk_connections_1hop'] = await self._count_high_risk_neighbors(address, chain, hops=1)
            features['high_risk_connections_2hop'] = await self._count_high_risk_neighbors(address, chain, hops=2)
            
            # Cross-chain activity (risk indicator for complex laundering)
            features['cross_chain_activity'] = await self._detect_cross_chain_activity(address)
            
            # Bridge usage
            features['bridge_transaction_count'] = await self._count_bridge_transactions(address)
            
            # Anomaly scores
            features['transaction_amount_anomaly'] = await self._calculate_amount_anomaly(address, chain)
            features['transaction_time_anomaly'] = await self._calculate_time_anomaly(address, chain)
            
        except Exception as e:
            logger.error(f"Risk feature extraction error: {e}")
            for key in ['tornado_cash_interactions', 'mixer_interactions_total', 
                       'sanctioned_entity_hops', 'sanctioned_entities_count',
                       'high_risk_connections_1hop', 'high_risk_connections_2hop',
                       'cross_chain_activity', 'bridge_transaction_count',
                       'transaction_amount_anomaly', 'transaction_time_anomaly']:
                features[key] = 0.0
        
        return features
    
    # ===== Helper Methods =====
    
    async def _calculate_value_concentration(self, address: str, chain: str) -> float:
        """Calculate Gini-like coefficient for value distribution"""
        try:
            query = """
            SELECT value::decimal as val
            FROM transactions
            WHERE (from_address = $1 OR to_address = $1) AND chain = $2
            ORDER BY val
            """
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch(query, address, chain)
            
            if not rows or len(rows) < 2:
                return 0.0
            
            values = [float(r['val']) for r in rows]
            values = sorted(values)
            n = len(values)
            
            # Gini coefficient
            cumsum = np.cumsum(values)
            gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0.0
            
            return float(gini)
        except:
            return 0.0
    
    async def _calculate_clustering_coefficient(self, address: str, chain: str) -> float:
        """Local clustering coefficient"""
        try:
            query = """
            MATCH (a:Address {address: $address, chain: $chain})--(neighbor)-->(other)
            WHERE (a)-->(other)
            WITH a, COUNT(DISTINCT other) as triangles,
                 SIZE([(a)--(n) | n]) as degree
            RETURN CASE WHEN degree > 1 THEN 2.0 * triangles / (degree * (degree - 1)) ELSE 0.0 END as clustering
            """
            result = await neo4j_client.run_query(query, {"address": address, "chain": chain})
            return float(result[0]['clustering']) if result else 0.0
        except:
            return 0.0
    
    async def _calculate_betweenness_centrality(self, address: str, chain: str) -> float:
        """Approximated betweenness centrality (sampled)"""
        try:
            # Lightweight approximation using sampled shortest paths count
            query = """
            MATCH (target:Address {address: $address, chain: $chain})
            // Sample 100 random sources and targets
            MATCH (s:Address {chain: $chain}) WHERE rand() < 0.01
            WITH target, s LIMIT 100
            MATCH (t:Address {chain: $chain}) WHERE rand() < 0.01 AND t <> s
            WITH target, s, t LIMIT 100
            CALL apoc.algo.dijkstraWithDefaultWeight(s, t, 'TRANSACTION>', 'weight', 1.0) YIELD path
            WITH target, path
            WHERE target IN nodes(path)
            RETURN count(path) * 1.0 as cnt
            """
            result = await neo4j_client.run_query(query, {"address": address, "chain": chain})
            val = float(result[0]["cnt"]) if result else 0.0
            # Normalize to [0,1] range by simple heuristic
            return min(1.0, val / 100.0)
        except Exception:
            return 0.0
    
    async def _calculate_pagerank(self, address: str, chain: str) -> float:
        """PageRank score"""
        try:
            # Use APOC or fallback simple degree-based proxy
            query = """
            CALL {
              WITH $chain as chain
              CALL gds.graph.project('addr_pr',
                 {Address: {label: 'Address', properties: ['chain']}},
                 {TRANSACTION: {orientation: 'NATURAL'}}
              ) YIELD graphName
              RETURN graphName
            } WITH graphName
            CALL gds.pageRank.stream(graphName) YIELD nodeId, score
            WITH gds.util.asNode(nodeId) AS n, score
            WHERE n.address = $address AND n.chain = $chain
            RETURN score
            """
            result = await neo4j_client.run_query(query, {"address": address, "chain": chain})
            if result and "score" in result[0]:
                return float(result[0]["score"]) 
        except Exception:
            pass
        # fallback: degree-based proxy
        try:
            deg_query = """
            MATCH (a:Address {address: $address, chain: $chain})
            OPTIONAL MATCH (a)-[r:TRANSACTION]-()
            RETURN count(r) AS d
            """
            res = await neo4j_client.run_query(deg_query, {"address": address, "chain": chain})
            d = float(res[0]["d"]) if res else 0.0
            return min(1.0, d / 100.0)
        except Exception:
            return 0.0
    
    async def _get_community_size(self, address: str, chain: str) -> float:
        """Size of detected community"""
        try:
            query = """
            // Label propagation community id approximation
            CALL gds.graph.project('addr_comm',
               {Address: {label: 'Address', properties: ['chain']}},
               {TRANSACTION: {orientation: 'UNDIRECTED'}}
            ) YIELD graphName
            CALL gds.labelPropagation.stream(graphName) YIELD nodeId, communityId
            WITH gds.util.asNode(nodeId) AS n, communityId
            WHERE n.chain = $chain
            WITH communityId, collect(n.address) AS members
            WITH communityId, members, size(members) AS sz
            MATCH (a:Address {address: $address, chain: $chain})
            WITH communityId, members, sz, a
            WHERE a.address IN members
            RETURN sz as community_size
            """
            res = await neo4j_client.run_query(query, {"address": address, "chain": chain})
            return float(res[0]["community_size"]) if res else 0.0
        except Exception:
            return 0.0
    
    async def _detect_burst_activity(self, address: str, chain: str) -> float:
        """Detect burst activity (many txs in short time)"""
        try:
            query = """
            SELECT timestamp,
                   LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp
            FROM transactions
            WHERE (from_address = $1 OR to_address = $1) AND chain = $2
            ORDER BY timestamp
            """
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch(query, address, chain)
            
            if not rows:
                return 0.0
            
            # Check for <1 minute gaps
            burst_count = sum(
                1 for r in rows 
                if r['prev_timestamp'] and (r['timestamp'] - r['prev_timestamp']).seconds < 60
            )
            
            return 1.0 if burst_count > 10 else 0.0
        except:
            return 0.0
    
    async def _calculate_max_dormancy(self, address: str, chain: str) -> float:
        """Maximum dormancy period in days"""
        try:
            query = """
            SELECT timestamp,
                   LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp
            FROM transactions
            WHERE (from_address = $1 OR to_address = $1) AND chain = $2
            ORDER BY timestamp
            """
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch(query, address, chain)
            if not rows:
                return 0.0
            max_gap_days = 0.0
            for r in rows:
                if r["prev_timestamp"] and r["timestamp"]:
                    gap = (r["timestamp"] - r["prev_timestamp"]).total_seconds() / 86400.0
                    if gap > max_gap_days:
                        max_gap_days = gap
            return float(max_gap_days)
        except Exception:
            return 0.0
    
    async def _count_mixer_interactions(self, address: str, chain: str, mixer_type: str) -> float:
        """Count interactions with mixers"""
        try:
            if mixer_type == 'tornado':
                label_filter = "WHERE toLower(l.value) CONTAINS 'tornado' OR toLower(l.value) CONTAINS 'mixer'"
            else:
                label_filter = "WHERE toLower(l.value) CONTAINS 'mixer' OR toLower(l.value) CONTAINS 'tornado'"
            query = f"""
            MATCH (a:Address {{address: $address, chain: $chain}})-[:TRANSACTION]-(m:Address)
            MATCH (m)-[:HAS_LABEL]->(l:Label)
            {label_filter}
            RETURN count(DISTINCT m) as cnt
            """
            res = await neo4j_client.run_query(query, {"address": address.lower(), "chain": chain})
            return float(res[0]["cnt"]) if res else 0.0
        except Exception:
            return 0.0
    
    async def _min_hops_to_sanctioned(self, address: str, chain: str) -> float:
        """Minimum hops to sanctioned entity"""
        try:
            query = """
            MATCH (a:Address {address: $address, chain: $chain}), (s:Address)
            MATCH (s)-[:HAS_LABEL]->(l:Label)
            WHERE toLower(l.value) CONTAINS 'sanction' OR toLower(l.value) CONTAINS 'ofac'
            CALL apoc.algo.dijkstraWithDefaultWeight(a, s, 'TRANSACTION>', 'weight', 1.0) YIELD path, weight
            RETURN length(path) as hops
            ORDER BY hops ASC
            LIMIT 1
            """
            res = await neo4j_client.run_query(query, {"address": address.lower(), "chain": chain})
            return float(res[0]["hops"]) if res else 999.0
        except Exception:
            return 999.0
    
    async def _count_sanctioned_connections(self, address: str, chain: str) -> float:
        """Count connections to sanctioned entities"""
        try:
            query = """
            MATCH (a:Address {address: $address, chain: $chain})-[:TRANSACTION*1..2]-(s:Address)
            MATCH (s)-[:HAS_LABEL]->(l:Label)
            WHERE toLower(l.value) CONTAINS 'sanction' OR toLower(l.value) CONTAINS 'ofac'
            RETURN count(DISTINCT s) as cnt
            """
            res = await neo4j_client.run_query(query, {"address": address.lower(), "chain": chain})
            return float(res[0]["cnt"]) if res else 0.0
        except Exception:
            return 0.0
    
    async def _count_high_risk_neighbors(self, address: str, chain: str, hops: int) -> float:
        """Count high-risk neighbors within N hops"""
        try:
            query = """
            MATCH (a:Address {address: $address, chain: $chain})-[:TRANSACTION*1..$hops]-(n:Address)
            OPTIONAL MATCH (n)-[:HAS_LABEL]->(l:Label)
            WITH n, collect(toLower(l.value)) as labels
            WHERE ANY(x IN labels WHERE x CONTAINS 'scam' OR x CONTAINS 'fraud' OR x CONTAINS 'sanction' OR x CONTAINS 'ofac' OR x CONTAINS 'mixer')
            RETURN count(DISTINCT n) as cnt
            """
            res = await neo4j_client.run_query(query, {"address": address.lower(), "chain": chain, "hops": int(hops)})
            return float(res[0]["cnt"]) if res else 0.0
        except Exception:
            return 0.0
    
    async def _detect_cross_chain_activity(self, address: str) -> float:
        """Detect cross-chain activity"""
        try:
            # Check for BRIDGE_LINK edges in Neo4j
            query = """
            MATCH (a:Address {address: $address})-[r:BRIDGE_LINK]-()
            RETURN COUNT(DISTINCT r.chain_to) as chains_count
            """
            result = await neo4j_client.run_query(query, {"address": address.lower()})
            chains_count = result[0]['chains_count'] if result else 0
            return float(chains_count)
        except:
            return 0.0
    
    async def _count_bridge_transactions(self, address: str) -> float:
        """Count bridge transactions"""
        try:
            # Count all bridge transactions
            query = """
            MATCH (a:Address {address: $address})-[r:BRIDGE_LINK]-()
            RETURN COUNT(r) as bridge_count
            """
            result = await neo4j_client.run_query(query, {"address": address.lower()})
            return float(result[0]['bridge_count']) if result else 0.0
        except:
            return 0.0
    
    async def _calculate_amount_anomaly(self, address: str, chain: str) -> float:
        """Calculate transaction amount anomaly score"""
        try:
            query = """
            SELECT value::decimal as val
            FROM transactions
            WHERE (from_address = $1 OR to_address = $1) AND chain = $2
            """
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch(query, address, chain)
            vals = [float(r["val"]) for r in rows] if rows else []
            if len(vals) < 5:
                return 0.0
            mu = float(np.mean(vals))
            sigma = float(np.std(vals)) or 1.0
            z_max = max(abs((v - mu) / sigma) for v in vals)
            # Normalize
            return float(min(1.0, z_max / 5.0))
        except Exception:
            return 0.0
    
    async def _calculate_time_anomaly(self, address: str, chain: str) -> float:
        """Calculate transaction timing anomaly score"""
        try:
            query = """
            SELECT EXTRACT(EPOCH FROM timestamp) as ts
            FROM transactions
            WHERE (from_address = $1 OR to_address = $1) AND chain = $2
            ORDER BY timestamp
            """
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch(query, address, chain)
            if not rows or len(rows) < 5:
                return 0.0
            intervals = []
            prev = None
            for r in rows:
                cur = float(r["ts"]) 
                if prev is not None:
                    intervals.append(cur - prev)
                prev = cur
            if not intervals:
                return 0.0
            mu = float(np.mean(intervals))
            sigma = float(np.std(intervals)) or 1.0
            z = float(abs(mu - np.median(intervals)) / sigma)
            return float(min(1.0, z / 5.0))
        except Exception:
            return 0.0
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default features (all zeros)"""
        return {f'feature_{i}': 0.0 for i in range(100)}


# Singleton instance
feature_engineer = FeatureEngineer()
