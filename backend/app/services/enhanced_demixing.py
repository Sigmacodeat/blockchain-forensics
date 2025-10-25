"""
Enhanced Privacy Demixing (Tornado Cash v2++)
===============================================

Advanced demixing für Privacy Protocols:
- Tornado Cash (Classic + Nova)
- Railgun
- Aztec
- zk.money
- Cyclone
"""

import logging
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class EnhancedDemixer:
    """
    Advanced Privacy Protocol Demixing
    
    Features:
    - Tornado Cash v2 Support (Nova + Relayers)
    - Cross-Protocol Correlation
    - Timing Analysis
    - Gas Pattern Matching
    - Relayer Fingerprinting
    """
    
    # Known mixing pools
    TORNADO_POOLS = {
        'ethereum': {
            '0.1': '0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc',
            '1': '0x47CE0C6eD5B0Ce3d3A51fdb1C52DC66a7c3c2936',
            '10': '0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF',
            '100': '0xA160cdAB225685dA1d56aa342Ad8841c3b53f291'
        }
    }
    
    def __init__(self):
        self.deposit_cache: Dict[str, List[Dict]] = defaultdict(list)
        self.withdrawal_cache: Dict[str, List[Dict]] = defaultdict(list)
        logger.info("Enhanced Demixer initialized")
    
    # =========================================================================
    # TORNADO CASH CLASSIC
    # =========================================================================
    
    async def analyze_tornado_classic(
        self,
        deposit_address: str,
        withdrawal_address: str,
        deposits: List[Dict],
        withdrawals: List[Dict]
    ) -> Dict:
        """
        Analyze Tornado Cash Classic mixing
        
        Heuristics:
        - Timing correlation
        - Amount matching
        - Gas pattern similarity
        - Relayer usage
        """
        results = {
            'confidence': 0.0,
            'indicators': [],
            'deposits': [],
            'withdrawals': [],
            'links': []
        }
        
        # 1. Amount Matching
        for dep in deposits:
            dep_amount = float(dep.get('value', 0))
            dep_time = self._parse_timestamp(dep.get('timestamp'))
            
            for wd in withdrawals:
                wd_amount = float(wd.get('value', 0))
                wd_time = self._parse_timestamp(wd.get('timestamp'))
                
                # Same pool amount
                if abs(dep_amount - wd_amount) < 0.001:
                    time_diff = (wd_time - dep_time).total_seconds()
                    
                    # Timing heuristic: 1 hour - 30 days
                    if 3600 < time_diff < 30 * 86400:
                        link_confidence = 0.3
                        
                        # 2. Gas Pattern Matching
                        dep_gas = float(dep.get('gas_price', 0))
                        wd_gas = float(wd.get('gas_price', 0))
                        
                        if abs(dep_gas - wd_gas) / max(dep_gas, 1) < 0.1:  # 10% diff
                            link_confidence += 0.2
                            results['indicators'].append("Similar gas prices")
                        
                        # 3. Same relayer
                        dep_relayer = dep.get('relayer')
                        wd_relayer = wd.get('relayer')
                        
                        if dep_relayer and wd_relayer and dep_relayer == wd_relayer:
                            link_confidence += 0.3
                            results['indicators'].append(f"Same relayer: {dep_relayer}")
                        
                        # 4. Timing patterns
                        hour_of_day_dep = dep_time.hour
                        hour_of_day_wd = wd_time.hour
                        
                        if abs(hour_of_day_dep - hour_of_day_wd) <= 2:
                            link_confidence += 0.1
                            results['indicators'].append("Similar time-of-day")
                        
                        results['links'].append({
                            'deposit_tx': dep.get('tx_hash'),
                            'withdrawal_tx': wd.get('tx_hash'),
                            'amount': dep_amount,
                            'time_diff_hours': time_diff / 3600,
                            'confidence': link_confidence
                        })
                        
                        results['confidence'] = max(results['confidence'], link_confidence)
        
        return results
    
    # =========================================================================
    # TORNADO CASH NOVA (zk-SNARK Pools)
    # =========================================================================
    
    async def analyze_tornado_nova(
        self,
        address: str,
        transactions: List[Dict]
    ) -> Dict:
        """
        Analyze Tornado Nova (Arbitrary Amounts)
        
        Nova allows arbitrary deposit/withdrawal amounts.
        Harder to demix, but still patterns:
        - Unique amounts
        - Timing
        - Gas patterns
        - Transaction graphs
        """
        results = {
            'confidence': 0.0,
            'indicators': [],
            'unique_amounts': [],
            'potential_links': []
        }
        
        # Extract deposits and withdrawals
        deposits = [tx for tx in transactions if self._is_nova_deposit(tx)]
        withdrawals = [tx for tx in transactions if self._is_nova_withdrawal(tx)]
        
        # Unique amount tracking
        amount_freq = defaultdict(int)
        for tx in deposits + withdrawals:
            amount = float(tx.get('value', 0))
            amount_freq[round(amount, 4)] += 1
        
        # Rare amounts = higher linkability
        for amount, freq in amount_freq.items():
            if freq == 2:  # Exactly 1 deposit + 1 withdrawal
                results['unique_amounts'].append(amount)
                results['confidence'] += 0.4
                results['indicators'].append(f"Unique amount: {amount} ETH")
        
        return results
    
    # =========================================================================
    # CROSS-PROTOCOL CORRELATION
    # =========================================================================
    
    async def correlate_cross_protocol(
        self,
        address: str,
        transactions: List[Dict]
    ) -> Dict:
        """
        Correlate across multiple privacy protocols
        
        Patterns:
        - User deposits to Tornado, withdraws to Railgun
        - Chain of mixers (Tornado -> Aztec -> zk.money)
        - Timing patterns across protocols
        """
        results = {
            'protocols_used': [],
            'cross_protocol_links': [],
            'confidence': 0.0
        }
        
        # Detect protocol usage
        for tx in transactions:
            to_address = tx.get('to_address', '').lower()
            
            if self._is_tornado(to_address):
                results['protocols_used'].append('tornado_cash')
            elif self._is_railgun(to_address):
                results['protocols_used'].append('railgun')
            elif self._is_aztec(to_address):
                results['protocols_used'].append('aztec')
            elif self._is_zk_money(to_address):
                results['protocols_used'].append('zk_money')
        
        # Multiple protocols = higher scrutiny
        unique_protocols = len(set(results['protocols_used']))
        if unique_protocols >= 2:
            results['confidence'] += 0.3 * unique_protocols
            results['cross_protocol_links'].append(
                f"Used {unique_protocols} different privacy protocols"
            )
        
        return results
    
    # =========================================================================
    # RELAYER ANALYSIS
    # =========================================================================
    
    async def analyze_relayers(
        self,
        transactions: List[Dict]
    ) -> Dict:
        """
        Analyze Relayer Usage Patterns
        
        Relayers are a weak point:
        - Same relayer = potential link
        - Relayer fees reveal patterns
        - Timing via relayer
        """
        relayer_usage = defaultdict(list)
        
        for tx in transactions:
            relayer = tx.get('relayer')
            if relayer:
                relayer_usage[relayer].append(tx)
        
        results = {
            'unique_relayers': len(relayer_usage),
            'relayers': dict(relayer_usage),
            'confidence': 0.0,
            'indicators': []
        }
        
        # Using same relayer multiple times
        for relayer, txs in relayer_usage.items():
            if len(txs) >= 3:
                results['confidence'] += 0.2
                results['indicators'].append(
                    f"Heavy relayer usage: {relayer} ({len(txs)} txs)"
                )
        
        return results
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _is_tornado(self, address: str) -> bool:
        """Check if address is Tornado Cash"""
        for chain_pools in self.TORNADO_POOLS.values():
            if address.lower() in [p.lower() for p in chain_pools.values()]:
                return True
        return False
    
    def _is_railgun(self, address: str) -> bool:
        """Check if address is Railgun"""
        # Simplified
        return 'railgun' in address.lower()
    
    def _is_aztec(self, address: str) -> bool:
        """Check if address is Aztec"""
        return 'aztec' in address.lower()
    
    def _is_zk_money(self, address: str) -> bool:
        """Check if address is zk.money"""
        return 'zk.money' in address.lower() or 'zkmoney' in address.lower()
    
    def _is_nova_deposit(self, tx: Dict) -> bool:
        """Check if transaction is Tornado Nova deposit"""
        method = tx.get('method', '').lower()
        return 'deposit' in method and 'nova' in str(tx.get('to_address', '')).lower()
    
    def _is_nova_withdrawal(self, tx: Dict) -> bool:
        """Check if transaction is Tornado Nova withdrawal"""
        method = tx.get('method', '').lower()
        return 'withdraw' in method and 'nova' in str(tx.get('to_address', '')).lower()
    
    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse timestamp"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return datetime.utcnow()


# Singleton
enhanced_demixer = EnhancedDemixer()

__all__ = ['EnhancedDemixer', 'enhanced_demixer']
