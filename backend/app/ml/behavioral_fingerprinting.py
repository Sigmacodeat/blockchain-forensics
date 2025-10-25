"""
Behavioral Fingerprinting System
=================================

Machine Learning für Wallet-Verhaltensmuster
**Überlegenheit gegenüber Chainalysis:** Erkennt psychologische und zeitliche Muster

**Features:**
- Circadian Rhythm Analysis (Tageszeitmuster)
- Amount Selection Psychology (Betragswahl-Verhalten)
- Gas Price Strategy Fingerprinting
- Wallet Software Detection (MetaMask vs. Ledger vs. Exchange)
- Bot vs. Human Classification
- Entity Type Prediction
"""

import logging
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter

try:
    import xgboost as xgb
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import DBSCAN
    HAS_ML = True
except ImportError:
    HAS_ML = False
    logging.warning("ML libraries not installed. Install: pip install xgboost scikit-learn")

logger = logging.getLogger(__name__)


class BehavioralFingerprinter:
    """
    Behavioral Analysis für Wallet Clustering
    
    **Methoden:**
    1. Temporal Patterns (wann aktiv?)
    2. Amount Psychology (wie viel?)
    3. Gas Strategy (wie schnell?)
    4. Interaction Patterns (mit wem?)
    """
    
    def __init__(self):
        self.models = {}
        self.fingerprint_db = {}  # Cache für berechnete Fingerprints
        
        if HAS_ML:
            # Bot vs Human Classifier
            self.bot_classifier = xgb.XGBClassifier(
                max_depth=6,
                learning_rate=0.1,
                n_estimators=100
            )
            
            # Anomaly Detector
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            logger.info("Behavioral Fingerprinter initialized with ML models")
        else:
            logger.warning("ML not available - using rule-based fallback")
    
    async def generate_fingerprint(
        self,
        address: str,
        postgres_client,
        chain: str = "ethereum"
    ) -> Dict:
        """
        Generate comprehensive behavioral fingerprint
        
        Returns:
            {
                'circadian_pattern': List[float],  # 24-hour activity distribution
                'amount_distribution': Dict,
                'gas_strategy': str,
                'bot_probability': float,
                'entity_type': str,
                'anomaly_score': float,
                'fingerprint_vector': np.ndarray
            }
        """
        # Check cache
        cache_key = f"{address.lower()}_{chain}"
        if cache_key in self.fingerprint_db:
            logger.debug(f"Using cached fingerprint for {address}")
            return self.fingerprint_db[cache_key]
        
        try:
            # 1. Extract transaction data
            query = """
                SELECT 
                    timestamp,
                    value::decimal as amount,
                    gas_price,
                    gas_used,
                    to_address,
                    from_address
                FROM transactions
                WHERE (from_address = $1 OR to_address = $1)
                  AND chain = $2
                  AND timestamp > NOW() - INTERVAL '90 days'
                ORDER BY timestamp DESC
                LIMIT 1000
            """
            
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch(query, address, chain)
            
            if len(rows) < 10:
                logger.warning(f"Insufficient data for behavioral analysis: {address}")
                return self._default_fingerprint()
            
            # 2. Circadian Pattern
            circadian = self._analyze_circadian_rhythm(rows)
            
            # 3. Amount Distribution
            amount_dist = self._analyze_amount_distribution(rows)
            
            # 4. Gas Strategy
            gas_strategy = self._analyze_gas_strategy(rows, chain)
            
            # 5. Bot Probability
            bot_prob = self._calculate_bot_probability(rows)
            
            # 6. Entity Type
            entity_type = self._predict_entity_type(rows)
            
            # 7. Anomaly Score
            anomaly_score = self._calculate_anomaly_score(rows)
            
            # 8. Create fingerprint vector
            fingerprint_vec = self._create_fingerprint_vector(
                circadian, amount_dist, gas_strategy, bot_prob
            )
            
            result = {
                'circadian_pattern': circadian,
                'amount_distribution': amount_dist,
                'gas_strategy': gas_strategy,
                'bot_probability': bot_prob,
                'entity_type': entity_type,
                'anomaly_score': anomaly_score,
                'fingerprint_vector': fingerprint_vec.tolist(),
                'tx_count': len(rows)
            }
            
            # Cache result
            self.fingerprint_db[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Fingerprinting error for {address}: {e}", exc_info=True)
            return self._default_fingerprint()
    
    def _analyze_circadian_rhythm(self, transactions: List) -> List[float]:
        """
        Analyze 24-hour activity pattern
        
        Returns:
            24-element list of activity probabilities
        """
        hour_counts = Counter()
        
        for tx in transactions:
            hour = tx['timestamp'].hour
            hour_counts[hour] += 1
        
        # Normalize to probabilities
        total = sum(hour_counts.values())
        pattern = [hour_counts.get(h, 0) / total for h in range(24)]
        
        return pattern
    
    def _analyze_amount_distribution(self, transactions: List) -> Dict:
        """
        Analyze transaction amount patterns
        
        Detects:
        - Round number preference
        - Power-law distribution (exchanges)
        - Fixed amounts (bots)
        """
        amounts = [float(tx['amount']) for tx in transactions if tx['amount'] > 0]
        
        if not amounts:
            return {'type': 'unknown'}
        
        amounts = np.array(amounts)
        
        # Round number ratio
        round_count = sum(1 for a in amounts if a == round(a, 0))
        round_ratio = round_count / len(amounts)
        
        # Check for fixed amounts (bot pattern)
        unique_amounts = len(set(amounts))
        fixed_amount_score = 1 - (unique_amounts / len(amounts))
        
        # Distribution type
        if fixed_amount_score > 0.7:
            dist_type = 'fixed_bot'
        elif round_ratio > 0.8:
            dist_type = 'human_round'
        else:
            dist_type = 'varied'
        
        return {
            'type': dist_type,
            'round_ratio': float(round_ratio),
            'fixed_score': float(fixed_amount_score),
            'unique_amounts': unique_amounts,
            'mean': float(np.mean(amounts)),
            'std': float(np.std(amounts))
        }
    
    def _analyze_gas_strategy(self, transactions: List, chain: str) -> str:
        """
        Analyze gas price strategy
        
        Strategies:
        - 'fixed': Bot with hardcoded gas
        - 'aggressive': MEV/arbitrage bot
        - 'conservative': Manual wallet
        - 'dynamic': Automated wallet with gas oracle
        """
        if chain not in ['ethereum', 'polygon', 'bsc']:
            return 'n/a'
        
        gas_prices = [tx['gas_price'] for tx in transactions if tx.get('gas_price')]
        
        if len(gas_prices) < 5:
            return 'unknown'
        
        gas_prices = np.array(gas_prices)
        
        # Check variance
        cv = np.std(gas_prices) / np.mean(gas_prices) if np.mean(gas_prices) > 0 else 0
        
        # Check for fixed values
        unique_count = len(set(gas_prices))
        
        if unique_count <= 2:
            return 'fixed'
        elif cv < 0.1:
            return 'dynamic'
        elif np.percentile(gas_prices, 75) > np.median(gas_prices) * 2:
            return 'aggressive'
        else:
            return 'conservative'
    
    def _calculate_bot_probability(self, transactions: List) -> float:
        """
        Calculate probability that address is a bot
        
        Indicators:
        - High transaction frequency
        - Regular intervals
        - Fixed gas prices
        - Fixed amounts
        - No dormancy periods
        """
        if len(transactions) < 10:
            return 0.0
        
        # 1. Time regularity
        timestamps = [tx['timestamp'] for tx in transactions]
        timestamps.sort()
        intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                     for i in range(len(timestamps) - 1)]
        
        if intervals:
            interval_std = np.std(intervals)
            interval_mean = np.mean(intervals)
            regularity_score = 1 - min(1.0, interval_std / (interval_mean + 1))
        else:
            regularity_score = 0.0
        
        # 2. Fixed amounts
        amounts = [float(tx['amount']) for tx in transactions if tx['amount'] > 0]
        if amounts:
            unique_ratio = len(set(amounts)) / len(amounts)
            amount_score = 1 - unique_ratio
        else:
            amount_score = 0.0
        
        # 3. High frequency
        days_active = (timestamps[-1] - timestamps[0]).days + 1
        tx_per_day = len(transactions) / days_active
        frequency_score = min(1.0, tx_per_day / 10)  # >10 tx/day = likely bot
        
        # Weighted combination
        bot_prob = (
            regularity_score * 0.4 +
            amount_score * 0.3 +
            frequency_score * 0.3
        )
        
        return float(bot_prob)
    
    def _predict_entity_type(self, transactions: List) -> str:
        """
        Predict entity type
        
        Types:
        - individual: Human user
        - exchange: Centralized exchange
        - defi_protocol: Smart contract
        - bot: Automated trading bot
        - mixer: Privacy service
        """
        if len(transactions) < 20:
            return 'individual'
        
        # High volume + many counterparties = exchange
        unique_counterparties = len(set(
            [tx['to_address'] for tx in transactions] +
            [tx['from_address'] for tx in transactions]
        ))
        
        if unique_counterparties > 100:
            return 'exchange'
        
        # High bot probability = bot
        bot_prob = self._calculate_bot_probability(transactions)
        if bot_prob > 0.7:
            return 'bot'
        
        # Many small fixed amounts = mixer
        amounts = [float(tx['amount']) for tx in transactions if tx['amount'] > 0]
        if amounts:
            small_count = sum(1 for a in amounts if a < np.median(amounts) * 0.1)
            if small_count / len(amounts) > 0.5:
                return 'mixer'
        
        return 'individual'
    
    def _calculate_anomaly_score(self, transactions: List) -> float:
        """
        Calculate anomaly score using Isolation Forest
        
        Returns:
            0.0 = normal, 1.0 = highly anomalous
        """
        if not HAS_ML or len(transactions) < 10:
            return 0.0
        
        try:
            # Build feature matrix
            features = []
            for tx in transactions:
                feat = [
                    tx['timestamp'].hour,
                    tx['timestamp'].weekday(),
                    float(tx['amount']) if tx['amount'] else 0,
                    float(tx['gas_price']) if tx.get('gas_price') else 0
                ]
                features.append(feat)
            
            X = np.array(features)
            
            # Fit and predict
            self.anomaly_detector.fit(X)
            scores = self.anomaly_detector.score_samples(X)
            
            # Convert to 0-1 range (more negative = more anomalous)
            anomaly_score = 1 / (1 + np.exp(np.mean(scores)))
            
            return float(anomaly_score)
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return 0.0
    
    def _create_fingerprint_vector(
        self,
        circadian: List[float],
        amount_dist: Dict,
        gas_strategy: str,
        bot_prob: float
    ) -> np.ndarray:
        """
        Create unified fingerprint vector for similarity comparison
        
        Returns:
            64-dimensional vector
        """
        vec = []
        
        # Circadian (24 dims)
        vec.extend(circadian)
        
        # Amount features (5 dims)
        vec.append(amount_dist.get('round_ratio', 0.0))
        vec.append(amount_dist.get('fixed_score', 0.0))
        vec.append(min(1.0, amount_dist.get('mean', 0.0) / 1000000))  # Normalized
        vec.append(min(1.0, amount_dist.get('std', 0.0) / 1000000))
        vec.append(float(amount_dist.get('unique_amounts', 0)) / 100)
        
        # Gas strategy (4 dims - one-hot)
        gas_strategies = ['fixed', 'dynamic', 'aggressive', 'conservative']
        for s in gas_strategies:
            vec.append(1.0 if gas_strategy == s else 0.0)
        
        # Bot probability (1 dim)
        vec.append(bot_prob)
        
        # Pad to 64 dimensions
        while len(vec) < 64:
            vec.append(0.0)
        
        return np.array(vec[:64])
    
    def compare_fingerprints(
        self,
        fp1: Dict,
        fp2: Dict
    ) -> Tuple[float, List[str]]:
        """
        Compare two behavioral fingerprints
        
        Returns:
            (similarity_score, evidence_list)
        """
        evidence = []
        scores = []
        
        # 1. Circadian similarity (cosine similarity)
        circ1 = np.array(fp1['circadian_pattern'])
        circ2 = np2.array(fp2['circadian_pattern'])
        circ_sim = np.dot(circ1, circ2) / (np.linalg.norm(circ1) * np.linalg.norm(circ2) + 1e-9)
        scores.append(circ_sim)
        
        if circ_sim > 0.8:
            evidence.append(f"Similar activity times (similarity: {circ_sim:.2f})")
        
        # 2. Amount behavior similarity
        amt1 = fp1['amount_distribution']
        amt2 = fp2['amount_distribution']
        
        if amt1['type'] == amt2['type']:
            scores.append(0.9)
            evidence.append(f"Same amount pattern: {amt1['type']}")
        else:
            scores.append(0.3)
        
        # 3. Gas strategy
        if fp1['gas_strategy'] == fp2['gas_strategy']:
            scores.append(0.8)
            evidence.append(f"Same gas strategy: {fp1['gas_strategy']}")
        else:
            scores.append(0.4)
        
        # 4. Entity type
        if fp1['entity_type'] == fp2['entity_type']:
            scores.append(0.7)
            evidence.append(f"Same entity type: {fp1['entity_type']}")
        else:
            scores.append(0.3)
        
        # 5. Vector similarity
        vec1 = np.array(fp1['fingerprint_vector'])
        vec2 = np.array(fp2['fingerprint_vector'])
        vec_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-9)
        scores.append(vec_sim)
        
        # Overall similarity (weighted average)
        overall = np.mean(scores)
        
        return (float(overall), evidence)
    
    def _default_fingerprint(self) -> Dict:
        """Return default fingerprint for addresses with insufficient data"""
        return {
            'circadian_pattern': [1/24] * 24,
            'amount_distribution': {'type': 'unknown'},
            'gas_strategy': 'unknown',
            'bot_probability': 0.0,
            'entity_type': 'unknown',
            'anomaly_score': 0.0,
            'fingerprint_vector': [0.0] * 64,
            'tx_count': 0
        }


# Singleton
behavioral_fingerprinter = BehavioralFingerprinter()

__all__ = ['BehavioralFingerprinter', 'behavioral_fingerprinter']
