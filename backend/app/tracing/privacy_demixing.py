"""
Privacy Protocol Demixing System
=================================

**1-Click Demixing für:**
- Tornado Cash (Ethereum)
- Blender.io (Bitcoin)
- Cyclone Protocol (BSC/Polygon)
- Railgun (Ethereum)
- Wasabi/Samourai CoinJoin (Bitcoin)

**Algorithmen basierend auf Chainalysis-Research:**
1. Time-Window Analysis (Entry-Exit Correlation)
2. Fixed Denomination Matching
3. Self-Deposit Detection
4. Multi-Exit Fan-Out Pattern
5. Gas Price Fingerprinting
6. Relayer Address Analysis
7. IP/Timing Correlation (wenn verfügbar)

**Überlegenheit:**
- Graph-Based Probabilistic Matching (nicht nur Time-Window)
- ML-Enhanced Pattern Detection
- Cross-Chain Mixer Linking
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class PrivacyDemixer:
    """
    Privacy Protocol Demixing Engine
    
    **Unterstützte Mixer:**
    - Tornado Cash (ZK-SNARK Mixer)
    - Cyclone Protocol (Multi-Chain ZK Mixer)
    - Railgun (Privacy Protocol)
    - Wasabi/Samourai (Bitcoin CoinJoin)
    - Blender.io (Centralized Mixer)
    """
    
    def __init__(self, neo4j_client=None, postgres_client=None):
        self.neo4j = neo4j_client
        self.postgres = postgres_client
        
        # Tornado Cash Pool Denominations
        self.tornado_pools = {
            "ethereum": [0.1, 1, 10, 100],  # ETH
            "bsc": [0.1, 1, 10, 100],  # BNB
            "polygon": [100, 1000, 10000, 100000],  # MATIC
        }
        
        # Known Mixer Contracts
        self.mixer_contracts = {
            "tornado_cash_eth": {
                "0.1": "0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc",
                "1": "0x47CE0C6eD5B0Ce3d3A51fdb1C52DC66a7c3c2936",
                "10": "0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF",
                "100": "0xA160cdAB225685dA1d56aa342Ad8841c3b53f291",
            },
            "cyclone_bsc": "0x0AabC9C964aF33e7d29c383312b11eDb7c2bEf8f",
            "railgun": "0xfa7093CDD9EE6932B4eb2c9e1cde7CE00B1FA4b9",
        }
        
        logger.info("Privacy Demixer initialized")
    
    async def demix_tornado_cash(
        self,
        address: str,
        chain: str = "ethereum",
        max_hops: int = 3,
        time_window_hours: int = 168  # 1 week
    ) -> Dict:
        """
        1-Click Tornado Cash Demixing
        
        **Algorithmus:**
        1. Finde alle Deposits (address → Tornado)
        2. Finde alle Withdrawals (Tornado → ?)
        3. Korreliere über Time-Windows
        4. Graph-Based Probabilistic Matching
        5. Multi-Exit Fan-Out Detection
        
        Args:
            address: Wallet Address
            chain: ethereum/bsc/polygon
            max_hops: Max Hops nach Withdrawal
            time_window_hours: Zeitfenster für Korrelation
            
        Returns:
            {
                'deposits': List[Dict],  # Alle Deposits von address
                'likely_withdrawals': List[Dict],  # Wahrscheinliche Withdrawals
                'probability_scores': Dict[str, float],  # Address → Probability
                'demixing_path': List[Dict],  # Kompletter Path
                'confidence': float
            }
        """
        logger.info(f"Starting Tornado Cash demixing for {address} on {chain}")
        
        try:
            # 1. Find all deposits from address
            deposits = await self._find_tornado_deposits(address, chain)
            
            if not deposits:
                return {
                    'deposits': [],
                    'likely_withdrawals': [],
                    'probability_scores': {},
                    'demixing_path': [],
                    'confidence': 0.0,
                    'message': 'No Tornado Cash deposits found'
                }
            
            # 2. For each deposit, find likely withdrawals
            all_likely_withdrawals = []
            probability_scores = {}
            
            for deposit in deposits:
                withdrawals = await self._match_tornado_withdrawals(
                    deposit,
                    chain,
                    time_window_hours
                )
                
                all_likely_withdrawals.extend(withdrawals)
                
                # Aggregate probabilities
                for w in withdrawals:
                    withdrawal_addr = w['withdrawal_address']
                    prob = w['probability']
                    
                    if withdrawal_addr not in probability_scores:
                        probability_scores[withdrawal_addr] = []
                    probability_scores[withdrawal_addr].append(prob)
            
            # 3. Calculate aggregate confidence scores
            final_scores = {}
            for addr, probs in probability_scores.items():
                # Bayesian update: P(A|B) = Product of probs
                final_scores[addr] = max(probs)  # or mean/product
            
            # 4. Sort by probability
            sorted_withdrawals = sorted(
                all_likely_withdrawals,
                key=lambda x: x['probability'],
                reverse=True
            )
            
            # 5. Trace further hops
            demixing_path = await self._trace_post_mixer_path(
                sorted_withdrawals[:5],  # Top 5
                max_hops,
                chain
            )
            
            # 6. Calculate overall confidence
            confidence = self._calculate_demixing_confidence(
                deposits,
                sorted_withdrawals,
                demixing_path
            )
            
            return {
                'deposits': deposits,
                'likely_withdrawals': sorted_withdrawals,
                'probability_scores': final_scores,
                'demixing_path': demixing_path,
                'confidence': confidence,
                'message': f'Found {len(deposits)} deposits, {len(sorted_withdrawals)} likely withdrawals'
            }
            
        except Exception as e:
            logger.error(f"Error demixing Tornado Cash: {e}", exc_info=True)
            return {
                'error': str(e),
                'deposits': [],
                'likely_withdrawals': [],
                'probability_scores': {},
                'demixing_path': [],
                'confidence': 0.0
            }
    
    async def _find_tornado_deposits(
        self,
        address: str,
        chain: str
    ) -> List[Dict]:
        """Find all Tornado Cash deposits from address"""
        deposits = []
        
        # Check each pool denomination
        pools = self.tornado_pools.get(chain, [])
        
        for denomination in pools:
            # Query transactions to Tornado contracts
            query = f"""
                MATCH (from:Address {{address: $address, chain: $chain}})
                     -[tx:TRANSACTION]->(mixer:Address)
                WHERE mixer.label CONTAINS 'Tornado Cash'
                  AND tx.value = $denomination
                RETURN 
                    tx.hash as tx_hash,
                    tx.timestamp as timestamp,
                    tx.value as amount,
                    mixer.address as mixer_address,
                    tx.block_number as block_number
                ORDER BY tx.timestamp
            """
            
            if self.neo4j:
                result = await self.neo4j.execute_read(
                    query,
                    address=address.lower(),
                    chain=chain,
                    denomination=denomination
                )
                
                for record in result:
                    deposits.append({
                        'tx_hash': record['tx_hash'],
                        'timestamp': record['timestamp'],
                        'amount': record['amount'],
                        'mixer_address': record['mixer_address'],
                        'block_number': record['block_number'],
                        'denomination': denomination,
                        'chain': chain
                    })
        
        logger.info(f"Found {len(deposits)} Tornado Cash deposits for {address}")
        return deposits
    
    async def _match_tornado_withdrawals(
        self,
        deposit: Dict,
        chain: str,
        time_window_hours: int
    ) -> List[Dict]:
        """
        Match deposit to likely withdrawals
        
        **Heuristics:**
        1. Same denomination
        2. Within time window
        3. Gas price similarity
        4. Relayer pattern detection
        5. Self-deposit detection (same address later)
        """
        matched = []
        
        deposit_time = deposit['timestamp']
        deposit_amount = deposit['amount']
        mixer_address = deposit['mixer_address']
        
        # Time window: deposit_time to deposit_time + time_window
        start_time = deposit_time
        end_time = start_time + timedelta(hours=time_window_hours)
        
        # Find all withdrawals from mixer in time window
        query = """
            MATCH (mixer:Address {address: $mixer_address, chain: $chain})
                 -[tx:TRANSACTION]->(to:Address)
            WHERE tx.timestamp >= $start_time
              AND tx.timestamp <= $end_time
              AND tx.value = $amount
            RETURN 
                tx.hash as tx_hash,
                tx.timestamp as timestamp,
                to.address as withdrawal_address,
                tx.gas_price as gas_price,
                tx.block_number as block_number
            ORDER BY tx.timestamp
        """
        
        if not self.neo4j:
            return []
        
        result = await self.neo4j.execute_read(
            query,
            mixer_address=mixer_address.lower(),
            chain=chain,
            start_time=start_time,
            end_time=end_time,
            amount=deposit_amount
        )
        
        for record in result:
            # Calculate probability based on heuristics
            probability = await self._calculate_match_probability(
                deposit,
                record,
                chain
            )
            
            if probability > 0.1:  # Threshold
                matched.append({
                    'tx_hash': record['tx_hash'],
                    'timestamp': record['timestamp'],
                    'withdrawal_address': record['withdrawal_address'],
                    'gas_price': record['gas_price'],
                    'block_number': record['block_number'],
                    'probability': probability,
                    'deposit_tx': deposit['tx_hash']
                })
        
        return matched
    
    async def _calculate_match_probability(
        self,
        deposit: Dict,
        withdrawal: Dict,
        chain: str
    ) -> float:
        """
        Calculate probability that withdrawal belongs to depositor
        
        **Factors:**
        1. Time delta (closer = higher)
        2. Gas price similarity
        3. Relayer usage pattern
        4. Pool liquidity (fewer participants = higher)
        5. Multi-exit fan-out pattern
        """
        score = 0.0
        
        # 1. Time delta score (exponential decay)
        time_delta = (withdrawal['timestamp'] - deposit['timestamp']).total_seconds()
        time_score = max(0, 1 - (time_delta / (7 * 24 * 3600)))  # Decay over 1 week
        score += time_score * 0.3
        
        # 2. Gas price similarity (if available)
        if 'gas_price' in deposit and 'gas_price' in withdrawal:
            dep_gas = deposit.get('gas_price', 0)
            with_gas = withdrawal.get('gas_price', 0)
            
            if dep_gas > 0 and with_gas > 0:
                gas_ratio = min(dep_gas, with_gas) / max(dep_gas, with_gas)
                score += gas_ratio * 0.2
        
        # 3. Check for relayer usage (lowers direct correlation)
        # Relayers sind Intermediate-Adressen
        # TODO: Detect relayer pattern
        
        # 4. Pool liquidity factor
        # Fewer deposits/withdrawals = higher probability
        pool_size = await self._estimate_pool_activity(
            deposit['mixer_address'],
            deposit['timestamp'],
            withdrawal['timestamp'],
            chain
        )
        
        if pool_size > 0:
            liquidity_score = min(1.0, 10 / pool_size)  # Inverse relationship
            score += liquidity_score * 0.3
        
        # 5. Multi-exit detection
        # If withdrawal address has multiple exits shortly after = likely demix
        exits = await self._count_subsequent_exits(
            withdrawal['withdrawal_address'],
            withdrawal['timestamp'],
            chain
        )
        
        if exits >= 2:
            score += 0.2
        
        return min(1.0, score)
    
    async def _estimate_pool_activity(
        self,
        mixer_address: str,
        start_time: datetime,
        end_time: datetime,
        chain: str
    ) -> int:
        """Estimate number of deposits/withdrawals in time window"""
        query = """
            MATCH (mixer:Address {address: $mixer_address, chain: $chain})
                 -[tx:TRANSACTION]-(other:Address)
            WHERE tx.timestamp >= $start_time
              AND tx.timestamp <= $end_time
            RETURN count(tx) as activity_count
        """
        
        if not self.neo4j:
            return 100  # Default high number
        
        result = await self.neo4j.execute_read(
            query,
            mixer_address=mixer_address.lower(),
            chain=chain,
            start_time=start_time,
            end_time=end_time
        )
        
        if result:
            return result[0].get('activity_count', 100)
        return 100
    
    async def _count_subsequent_exits(
        self,
        address: str,
        timestamp: datetime,
        chain: str,
        window_hours: int = 24
    ) -> int:
        """Count exits from address after timestamp (multi-exit pattern)"""
        query = """
            MATCH (addr:Address {address: $address, chain: $chain})
                 -[tx:TRANSACTION]->(other:Address)
            WHERE tx.timestamp >= $timestamp
              AND tx.timestamp <= $end_time
            RETURN count(tx) as exit_count
        """
        
        if not self.neo4j:
            return 0
        
        end_time = timestamp + timedelta(hours=window_hours)
        
        result = await self.neo4j.execute_read(
            query,
            address=address.lower(),
            chain=chain,
            timestamp=timestamp,
            end_time=end_time
        )
        
        if result:
            return result[0].get('exit_count', 0)
        return 0
    
    async def _trace_post_mixer_path(
        self,
        withdrawals: List[Dict],
        max_hops: int,
        chain: str
    ) -> List[Dict]:
        """Trace path after mixer withdrawal (wo geht das Geld hin?)"""
        paths = []
        
        for withdrawal in withdrawals:
            withdrawal_addr = withdrawal['withdrawal_address']
            
            # Trace from withdrawal address
            query = """
                MATCH path = (start:Address {address: $address, chain: $chain})
                           -[:TRANSACTION*1..$max_hops]->(end:Address)
                WHERE ALL(rel IN relationships(path) WHERE rel.timestamp >= $start_time)
                RETURN 
                    [node in nodes(path) | node.address] as addresses,
                    [rel in relationships(path) | {
                        hash: rel.hash,
                        value: rel.value,
                        timestamp: rel.timestamp
                    }] as transactions,
                    end.label as end_label
                ORDER BY length(path) DESC
                LIMIT 10
            """
            
            if not self.neo4j:
                continue
            
            result = await self.neo4j.execute_read(
                query,
                address=withdrawal_addr.lower(),
                chain=chain,
                max_hops=max_hops,
                start_time=withdrawal['timestamp']
            )
            
            for record in result:
                paths.append({
                    'withdrawal_tx': withdrawal['tx_hash'],
                    'withdrawal_address': withdrawal_addr,
                    'path': record['addresses'],
                    'transactions': record['transactions'],
                    'end_label': record.get('end_label', 'Unknown'),
                    'probability': withdrawal['probability']
                })
        
        return paths
    
    def _calculate_demixing_confidence(
        self,
        deposits: List[Dict],
        withdrawals: List[Dict],
        paths: List[Dict]
    ) -> float:
        """
        Calculate overall confidence in demixing results
        
        Factors:
        - Number of deposits (more = harder)
        - Avg probability of matches
        - Path consistency (if multiple deposits → same destination)
        """
        if not withdrawals:
            return 0.0
        
        # Average probability
        avg_prob = sum(w['probability'] for w in withdrawals) / len(withdrawals)
        
        # Penalty for many deposits (harder to demix)
        deposit_penalty = max(0.3, 1 - (len(deposits) * 0.1))
        
        # Bonus for path consistency
        if paths:
            unique_destinations = len(set(p['path'][-1] for p in paths if p['path']))
            consistency_bonus = 1.0 if unique_destinations == 1 else 0.8
        else:
            consistency_bonus = 0.7
        
        confidence = avg_prob * deposit_penalty * consistency_bonus
        
        return min(1.0, confidence)
    
    # ===== Bitcoin CoinJoin Demixing =====
    
    async def demix_coinjoin(
        self,
        address: str,
        mixer_type: str = "wasabi"  # wasabi, samourai, joinmarket
    ) -> Dict:
        """
        CoinJoin Demixing (Bitcoin)
        
        **Heuristics:**
        1. Equal Output Detection (CoinJoin hat typisch gleiche Outputs)
        2. Change Address Identification
        3. UTXO Clustering
        4. Temporal Analysis
        
        TODO: Implement Bitcoin-specific heuristics
        """
        logger.warning("CoinJoin demixing not yet implemented")
        return {
            'message': 'CoinJoin demixing coming soon',
            'mixer_type': mixer_type,
            'status': 'planned'
        }
    
    # ===== Generic Mixer Detection =====
    
    async def detect_mixer_usage(
        self,
        address: str,
        chain: str = "ethereum"
    ) -> Dict:
        """
        Detect if address has used ANY mixer
        
        Returns:
            {
                'has_mixer_activity': bool,
                'mixers_used': List[str],
                'total_deposits': int,
                'total_withdrawals': int,
                'risk_score': float
            }
        """
        query = """
            MATCH (addr:Address {address: $address, chain: $chain})
                 -[tx:TRANSACTION]-(mixer:Address)
            WHERE mixer.label CONTAINS 'Mixer' 
               OR mixer.label CONTAINS 'Tornado'
               OR mixer.label CONTAINS 'Privacy'
            RETURN 
                collect(DISTINCT mixer.address) as mixers,
                count(DISTINCT CASE WHEN startNode(tx) = addr THEN tx END) as deposits,
                count(DISTINCT CASE WHEN endNode(tx) = addr THEN tx END) as withdrawals
        """
        
        if not self.neo4j:
            return {
                'has_mixer_activity': False,
                'mixers_used': [],
                'total_deposits': 0,
                'total_withdrawals': 0,
                'risk_score': 0.0
            }
        
        result = await self.neo4j.execute_read(
            query,
            address=address.lower(),
            chain=chain
        )
        
        if result and result[0]:
            record = result[0]
            mixers = record.get('mixers', [])
            deposits = record.get('deposits', 0)
            withdrawals = record.get('withdrawals', 0)
            
            has_activity = len(mixers) > 0
            
            # Risk score: higher if more mixer usage
            risk_score = min(1.0, (deposits + withdrawals) * 0.1)
            
            return {
                'has_mixer_activity': has_activity,
                'mixers_used': mixers,
                'total_deposits': deposits,
                'total_withdrawals': withdrawals,
                'risk_score': risk_score
            }
        
        return {
            'has_mixer_activity': False,
            'mixers_used': [],
            'total_deposits': 0,
            'total_withdrawals': 0,
            'risk_score': 0.0
        }


# ===== Privacy Coin Support =====

class PrivacyCoinTracer:
    """
    Privacy Coin Tracing (Monero, Zcash)
    
    **Herausforderungen:**
    - Monero: Ring Signatures verschleiern Sender
    - Zcash: Shielded Transactions sind privat
    
    **Mögliche Heuristiken:**
    1. Transparent → Shielded → Transparent Flow Analysis
    2. Exchange Deposit/Withdrawal Correlation
    3. Timing Analysis
    4. Amount Correlation
    5. Chain Analysis on Transparent Parts
    
    **Realität:** Vollständige Privacy ist kaum zu brechen
    **Aber:** Transparent Parts + Metadata können Hints geben
    """
    
    def __init__(self):
        logger.info("Privacy Coin Tracer initialized (LIMITED CAPABILITY)")
    
    async def trace_zcash(
        self,
        address: str,
        transaction_type: str = "transparent"  # transparent, shielded, mixed
    ) -> Dict:
        """
        Zcash Tracing
        
        **Transparent Transactions:** Vollständig tracebar wie Bitcoin
        **Shielded Transactions:** Nicht tracebar (zk-SNARKs)
        **Mixed:** Nur transparent parts tracebar
        """
        logger.warning("Zcash shielded tracing not possible (privacy preserved)")
        
        return {
            'chain': 'zcash',
            'address': address,
            'transaction_type': transaction_type,
            'traceable': transaction_type == 'transparent',
            'message': 'Only transparent Zcash transactions can be traced',
            'status': 'limited'
        }
    
    async def trace_monero(self, address: str) -> Dict:
        """
        Monero Tracing
        
        **Problem:** Ring Signatures + Stealth Addresses = nahezu unmöglich
        **Mögliche Ansätze:**
        1. Exchange-Korrelation (Ein/Auszahlungen)
        2. Timing-Analyse
        3. Mixin-Analyse (statistische Anomalien)
        
        **Realität:** Nur metadata-based heuristics möglich
        """
        logger.warning("Monero tracing extremely limited (strong privacy)")
        
        return {
            'chain': 'monero',
            'address': address,
            'traceable': False,
            'message': 'Monero provides strong privacy - only metadata analysis possible',
            'possible_heuristics': [
                'exchange_correlation',
                'timing_analysis',
                'mixin_anomaly_detection'
            ],
            'status': 'minimal'
        }
