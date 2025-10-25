"""
Smart Money Tracking System (Nansen-Style)
==========================================

Automatisches Tracking von Top Traders, Whales, und Smart Money Wallets.
Identifiziert profitables Trading-Verhalten und ermöglicht Copy-Trading-Signals.

**Features:**
- Top Trader Identification (Profitability + Win Rate)
- Whale Movement Tracking (Large Transfers)
- Smart Money Labels (Early DeFi Adopters, MEV Bots, etc.)
- Portfolio Analysis
- Copy-Trading Signals
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SmartMoneyProfile:
    """Profile eines Smart Money Wallets"""
    address: str
    classification: str  # 'whale', 'smart_trader', 'mev_bot', 'early_adopter', 'fund'
    confidence: float  # 0.0 - 1.0
    metrics: Dict[str, Any]
    portfolio: List[Dict[str, Any]]
    recent_moves: List[Dict[str, Any]]
    labels: List[str]
    total_value_usd: float
    profit_loss_30d: float
    win_rate: float
    timestamp: datetime


@dataclass
class TradingSignal:
    """Copy-Trading Signal"""
    signal_type: str  # 'buy', 'sell', 'swap'
    trader_address: str
    trader_reputation: float
    token_address: str
    token_symbol: str
    amount: float
    amount_usd: float
    timestamp: datetime
    confidence: float
    reasoning: List[str]


class SmartMoneyTracker:
    """
    Smart Money Tracking Engine
    
    Identifiziert und trackt Smart Money Wallets wie:
    - Whales (>$1M Holdings)
    - Top Traders (High Win Rate + Profitability)
    - MEV Bots (Frontrunning/Arbitrage)
    - Early Adopters (Early DeFi Protocol Users)
    - Crypto Funds (Multi-Sig + Large Holdings)
    """
    
    # Thresholds für Klassifizierung
    WHALE_THRESHOLD_USD = 1_000_000  # $1M+
    TOP_TRADER_WIN_RATE = 0.65  # 65%+ win rate
    TOP_TRADER_MIN_TRADES = 50
    MEV_BOT_GAS_THRESHOLD = 500  # Gwei
    EARLY_ADOPTER_DAYS = 365  # 1 Jahr früher als Durchschnitt
    
    def __init__(self):
        self.tracked_wallets: Dict[str, SmartMoneyProfile] = {}
        logger.info("Smart Money Tracker initialized")
    
    # =========================================================================
    # CLASSIFICATION: TOP TRADER
    # =========================================================================
    
    async def classify_top_trader(
        self,
        address: str,
        transactions: List[Dict[str, Any]]
    ) -> Optional[SmartMoneyProfile]:
        """
        Klassifiziere als Top Trader basierend auf Win Rate und Profitability
        
        Metrics:
        - Win Rate (profitable trades / total trades)
        - Average Profit per Trade
        - Total Volume
        - Consistency (profitable months)
        """
        if len(transactions) < self.TOP_TRADER_MIN_TRADES:
            return None
        
        # Analyze trading history
        trades = self._extract_trades(transactions)
        
        if len(trades) < self.TOP_TRADER_MIN_TRADES:
            return None
        
        # Calculate metrics
        profitable_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        win_rate = profitable_trades / len(trades)
        
        if win_rate < self.TOP_TRADER_WIN_RATE:
            return None
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        avg_profit = total_pnl / len(trades)
        total_volume = sum(t.get('volume_usd', 0) for t in trades)
        
        # Consistency check (profitable in 70%+ of months)
        monthly_pnl = self._calculate_monthly_pnl(trades)
        profitable_months = sum(1 for pnl in monthly_pnl.values() if pnl > 0)
        consistency = profitable_months / len(monthly_pnl) if monthly_pnl else 0
        
        # Confidence scoring
        confidence = 0.0
        indicators = []
        
        if win_rate >= 0.70:
            confidence += 0.3
            indicators.append(f"High win rate: {win_rate*100:.1f}%")
        elif win_rate >= 0.65:
            confidence += 0.2
            indicators.append(f"Good win rate: {win_rate*100:.1f}%")
        
        if total_volume > 1_000_000:
            confidence += 0.2
            indicators.append(f"High volume: ${total_volume:,.0f}")
        
        if consistency >= 0.7:
            confidence += 0.3
            indicators.append(f"Consistent performer: {consistency*100:.0f}% profitable months")
        
        if avg_profit > 1000:
            confidence += 0.2
            indicators.append(f"High avg profit: ${avg_profit:,.0f}")
        
        if confidence >= 0.5:
            return SmartMoneyProfile(
                address=address,
                classification='smart_trader',
                confidence=min(confidence, 1.0),
                metrics={
                    'win_rate': win_rate,
                    'total_trades': len(trades),
                    'profitable_trades': profitable_trades,
                    'total_pnl': total_pnl,
                    'avg_profit': avg_profit,
                    'total_volume': total_volume,
                    'consistency': consistency
                },
                portfolio=[],  # Would fetch from external API
                recent_moves=trades[-10:],  # Last 10 trades
                labels=['Top Trader', f'Win Rate: {win_rate*100:.0f}%'],
                total_value_usd=0,  # Would calculate
                profit_loss_30d=self._calculate_recent_pnl(trades, 30),
                win_rate=win_rate,
                timestamp=datetime.utcnow()
            )
        
        return None
    
    # =========================================================================
    # CLASSIFICATION: WHALE
    # =========================================================================
    
    async def classify_whale(
        self,
        address: str,
        balance_usd: float,
        transactions: List[Dict[str, Any]]
    ) -> Optional[SmartMoneyProfile]:
        """
        Klassifiziere als Whale basierend auf Holdings und Movement Size
        
        Criteria:
        - Total Balance > $1M
        - Large transaction sizes
        - Diversified portfolio
        """
        if balance_usd < self.WHALE_THRESHOLD_USD:
            return None
        
        # Analyze transaction sizes
        tx_values = [float(tx.get('value_usd', 0)) for tx in transactions if tx.get('value_usd')]
        
        if not tx_values:
            return None
        
        avg_tx = np.mean(tx_values)
        max_tx = max(tx_values)
        
        # Confidence scoring
        confidence = 0.0
        indicators = []
        
        if balance_usd >= 10_000_000:
            confidence += 0.4
            indicators.append(f"Ultra whale: ${balance_usd/1e6:.1f}M")
        elif balance_usd >= 5_000_000:
            confidence += 0.3
            indicators.append(f"Large whale: ${balance_usd/1e6:.1f}M")
        else:
            confidence += 0.2
            indicators.append(f"Whale: ${balance_usd/1e6:.1f}M")
        
        if avg_tx > 100_000:
            confidence += 0.2
            indicators.append(f"Large avg tx: ${avg_tx:,.0f}")
        
        if max_tx > 1_000_000:
            confidence += 0.2
            indicators.append(f"Massive single tx: ${max_tx:,.0f}")
        
        # Recent activity
        recent_txs = [tx for tx in transactions if self._is_recent(tx.get('timestamp'), days=7)]
        if len(recent_txs) > 10:
            confidence += 0.2
            indicators.append(f"Active: {len(recent_txs)} txs last week")
        
        return SmartMoneyProfile(
            address=address,
            classification='whale',
            confidence=min(confidence, 1.0),
            metrics={
                'balance_usd': balance_usd,
                'avg_transaction_usd': avg_tx,
                'max_transaction_usd': max_tx,
                'recent_activity': len(recent_txs)
            },
            portfolio=[],
            recent_moves=transactions[-20:],
            labels=['Whale', f'${balance_usd/1e6:.1f}M Holdings'],
            total_value_usd=balance_usd,
            profit_loss_30d=0,  # Would track changes
            win_rate=0,
            timestamp=datetime.utcnow()
        )
    
    # =========================================================================
    # CLASSIFICATION: MEV BOT
    # =========================================================================
    
    async def classify_mev_bot(
        self,
        address: str,
        transactions: List[Dict[str, Any]]
    ) -> Optional[SmartMoneyProfile]:
        """
        Klassifiziere als MEV Bot basierend auf Gas Usage und Timing
        
        Characteristics:
        - Very high gas prices (frontrunning)
        - Sandwich attacks pattern
        - Flash loan usage
        - High-frequency trading
        """
        if len(transactions) < 100:  # MEV bots sind sehr aktiv
            return None
        
        # Gas analysis
        gas_prices = [float(tx.get('gas_price', 0)) for tx in transactions if tx.get('gas_price')]
        
        if not gas_prices:
            return None
        
        avg_gas = np.mean(gas_prices)
        max_gas = max(gas_prices)
        
        # Check for MEV patterns
        confidence = 0.0
        indicators = []
        
        # High gas usage
        if avg_gas > self.MEV_BOT_GAS_THRESHOLD:
            confidence += 0.3
            indicators.append(f"High avg gas: {avg_gas:.0f} gwei")
        
        # Sandwich attack pattern (rapid tx pairs)
        sandwich_count = self._detect_sandwich_attacks(transactions)
        if sandwich_count > 10:
            confidence += 0.3
            indicators.append(f"Sandwich attacks detected: {sandwich_count}")
        
        # Flash loan usage
        flash_loan_txs = [tx for tx in transactions if 'flash' in str(tx.get('method', '')).lower()]
        if len(flash_loan_txs) > 5:
            confidence += 0.2
            indicators.append(f"Flash loan user: {len(flash_loan_txs)} txs")
        
        # High frequency (>100 txs/day average)
        days = (datetime.utcnow() - self._parse_timestamp(transactions[0].get('timestamp'))).days or 1
        txs_per_day = len(transactions) / days
        if txs_per_day > 100:
            confidence += 0.2
            indicators.append(f"High frequency: {txs_per_day:.0f} txs/day")
        
        if confidence >= 0.5:
            return SmartMoneyProfile(
                address=address,
                classification='mev_bot',
                confidence=min(confidence, 1.0),
                metrics={
                    'avg_gas_gwei': avg_gas,
                    'max_gas_gwei': max_gas,
                    'sandwich_attacks': sandwich_count,
                    'flash_loans': len(flash_loan_txs),
                    'txs_per_day': txs_per_day
                },
                portfolio=[],
                recent_moves=transactions[-50:],
                labels=['MEV Bot', 'Frontrunner'],
                total_value_usd=0,
                profit_loss_30d=0,
                win_rate=0,
                timestamp=datetime.utcnow()
            )
        
        return None
    
    # =========================================================================
    # TRADING SIGNALS
    # =========================================================================
    
    async def generate_copy_trading_signal(
        self,
        trader_profile: SmartMoneyProfile,
        transaction: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """
        Generiere Copy-Trading Signal basierend auf Smart Money Move
        
        Nur Signale von Tradern mit:
        - Confidence > 0.7
        - Win Rate > 70%
        - Recent profitable streak
        """
        if trader_profile.confidence < 0.7:
            return None
        
        if trader_profile.win_rate < 0.70:
            return None
        
        # Parse transaction
        signal_type = self._classify_transaction_type(transaction)
        token_address = transaction.get('token_address', '')
        token_symbol = transaction.get('token_symbol', 'UNKNOWN')
        amount = float(transaction.get('value', 0))
        amount_usd = float(transaction.get('value_usd', 0))
        
        # Only generate signals for significant trades
        if amount_usd < 10_000:  # Min $10k trade
            return None
        
        # Confidence based on trader metrics
        signal_confidence = trader_profile.confidence * 0.5
        
        reasoning = [
            f"Trader win rate: {trader_profile.win_rate*100:.0f}%",
            f"Trader reputation: {trader_profile.confidence*100:.0f}%"
        ]
        
        # Recent performance boost
        if trader_profile.profit_loss_30d > 0:
            signal_confidence += 0.2
            reasoning.append(f"Recent profit: ${trader_profile.profit_loss_30d:,.0f}")
        
        # Transaction size boost
        if amount_usd > 100_000:
            signal_confidence += 0.2
            reasoning.append(f"Large position: ${amount_usd:,.0f}")
        
        return TradingSignal(
            signal_type=signal_type,
            trader_address=trader_profile.address,
            trader_reputation=trader_profile.confidence,
            token_address=token_address,
            token_symbol=token_symbol,
            amount=amount,
            amount_usd=amount_usd,
            timestamp=datetime.utcnow(),
            confidence=min(signal_confidence, 1.0),
            reasoning=reasoning
        )
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _extract_trades(self, transactions: List[Dict]) -> List[Dict]:
        """Extract trading activity from transactions"""
        trades = []
        
        # Simplified: Would parse swap events, analyze buys/sells
        for tx in transactions:
            method = tx.get('method', '').lower()
            if 'swap' in method or 'trade' in method:
                trades.append({
                    'tx_hash': tx.get('tx_hash'),
                    'timestamp': tx.get('timestamp'),
                    'value_usd': float(tx.get('value_usd', 0)),
                    'pnl': 0,  # Would calculate from price changes
                    'volume_usd': float(tx.get('value_usd', 0))
                })
        
        return trades
    
    def _calculate_monthly_pnl(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate PnL per month"""
        monthly = defaultdict(float)
        
        for trade in trades:
            ts = self._parse_timestamp(trade.get('timestamp'))
            month_key = ts.strftime('%Y-%m')
            monthly[month_key] += trade.get('pnl', 0)
        
        return dict(monthly)
    
    def _calculate_recent_pnl(self, trades: List[Dict], days: int) -> float:
        """Calculate PnL for recent period"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [t for t in trades if self._parse_timestamp(t.get('timestamp')) > cutoff]
        return sum(t.get('pnl', 0) for t in recent)
    
    def _detect_sandwich_attacks(self, transactions: List[Dict]) -> int:
        """Detect sandwich attack patterns"""
        count = 0
        
        # Simplified: Look for rapid buy-sell pairs
        for i in range(len(transactions) - 2):
            tx1 = transactions[i]
            tx2 = transactions[i + 1]
            tx3 = transactions[i + 2]
            
            ts1 = self._parse_timestamp(tx1.get('timestamp'))
            ts2 = self._parse_timestamp(tx2.get('timestamp'))
            ts3 = self._parse_timestamp(tx3.get('timestamp'))
            
            # Within same block or very close
            if (ts3 - ts1).total_seconds() < 30:
                count += 1
        
        return count
    
    def _classify_transaction_type(self, tx: Dict) -> str:
        """Classify transaction as buy/sell/swap"""
        method = tx.get('method', '').lower()
        
        if 'swap' in method:
            return 'swap'
        elif 'buy' in method or 'deposit' in method:
            return 'buy'
        elif 'sell' in method or 'withdraw' in method:
            return 'sell'
        
        return 'unknown'
    
    def _is_recent(self, timestamp, days: int = 7) -> bool:
        """Check if timestamp is recent"""
        ts = self._parse_timestamp(timestamp)
        cutoff = datetime.utcnow() - timedelta(days=days)
        return ts > cutoff
    
    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse timestamp to datetime"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return datetime.utcnow()


# Singleton
smart_money_tracker = SmartMoneyTracker()

__all__ = ['SmartMoneyTracker', 'smart_money_tracker', 'SmartMoneyProfile', 'TradingSignal']
