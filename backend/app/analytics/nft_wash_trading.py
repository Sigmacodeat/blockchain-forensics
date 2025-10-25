"""
NFT Wash Trading Detection
===========================

Detektiert Wash-Trading-Patterns bei NFT-Transaktionen basierend auf:
- Self-trading (gleicher Owner über Zwischenwallets)
- Round-trip patterns (A→B→A)
- Preis-Anomalien (künstliche Preiserhöhung)
- Wiederholte Gegenparteien in kurzer Zeit
- Koordinierte Gebots-Muster

Inspiriert von Chainalysis/Elliptic NFT-Forensics.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NFTTrade:
    """Einzelne NFT-Trade"""
    tx_hash: str
    timestamp: datetime
    token_address: str
    token_id: str
    from_address: str
    to_address: str
    price: float  # in ETH/Native Currency
    marketplace: Optional[str] = None
    block_number: Optional[int] = None


@dataclass
class WashTradingFinding:
    """Wash-Trading Detection Result"""
    pattern_type: str  # self_trade|round_trip|repeated_counterparty|price_anomaly|coordinated_bidding
    confidence: float  # 0.0-1.0
    addresses_involved: List[str]
    trades_involved: List[str]  # tx_hashes
    description: str
    evidence: Dict[str, Any]


class NFTWashTradingDetector:
    """
    NFT Wash Trading Detector mit 5 Heuristiken
    """

    def __init__(
        self,
        round_trip_window_hours: int = 168,  # 7 Tage
        repeated_counterparty_threshold: int = 3,
        price_spike_threshold: float = 2.0,  # 200% increase
    ):
        self.round_trip_window = timedelta(hours=round_trip_window_hours)
        self.repeated_threshold = repeated_counterparty_threshold
        self.price_spike_threshold = price_spike_threshold

    async def detect_wash_trading(
        self,
        trades: List[NFTTrade],
        check_clustering: bool = False,
    ) -> List[WashTradingFinding]:
        """
        Hauptfunktion: Analysiert Trades und liefert Findings zurück
        """
        findings: List[WashTradingFinding] = []

        # Heuristik 1: Self-Trading (gleiche Adresse via Zwischenwallets)
        findings.extend(await self._detect_self_trading(trades))

        # Heuristik 2: Round-Trip Patterns (A→B→A)
        findings.extend(await self._detect_round_trips(trades))

        # Heuristik 3: Repeated Counterparties
        findings.extend(await self._detect_repeated_counterparties(trades))

        # Heuristik 4: Price Anomalies (künstliche Spikes)
        findings.extend(await self._detect_price_anomalies(trades))

        # Heuristik 5: Coordinated Bidding (zeitlich korrelierte Trades)
        findings.extend(await self._detect_coordinated_bidding(trades))

        return findings

    async def _detect_self_trading(self, trades: List[NFTTrade]) -> List[WashTradingFinding]:
        """
        Detektiert Self-Trading: gleicher Owner kauft/verkauft über Zwischenwallet
        """
        findings: List[WashTradingFinding] = []

        # Gruppiere nach Token
        by_token: Dict[Tuple[str, str], List[NFTTrade]] = defaultdict(list)
        for t in trades:
            by_token[(t.token_address, t.token_id)].append(t)

        for (token_addr, token_id), token_trades in by_token.items():
            # Sortiere chronologisch
            token_trades = sorted(token_trades, key=lambda x: x.timestamp)

            # Prüfe auf gleichen from_address nach 2+ Hops
            addresses_seen: Set[str] = set()
            for i, trade in enumerate(token_trades):
                if trade.from_address in addresses_seen and i > 0:
                    # from_address war bereits Seller/Buyer → potentielles Self-Trading
                    evidence_trades = [t.tx_hash for t in token_trades[:i+1] if trade.from_address in (t.from_address, t.to_address)]
                    findings.append(WashTradingFinding(
                        pattern_type="self_trade",
                        confidence=0.75,
                        addresses_involved=[trade.from_address],
                        trades_involved=evidence_trades,
                        description=f"Address {trade.from_address[:10]}... appears as both buyer and seller",
                        evidence={
                            "token": f"{token_addr}:{token_id}",
                            "trades_count": len(evidence_trades),
                        }
                    ))
                    break  # Ein Finding pro Token genügt
                addresses_seen.add(trade.from_address)
                addresses_seen.add(trade.to_address)

        return findings

    async def _detect_round_trips(self, trades: List[NFTTrade]) -> List[WashTradingFinding]:
        """
        Detektiert Round-Trips: A→B→A innerhalb eines Zeitfensters
        """
        findings: List[WashTradingFinding] = []

        by_token: Dict[Tuple[str, str], List[NFTTrade]] = defaultdict(list)
        for t in trades:
            by_token[(t.token_address, t.token_id)].append(t)

        for (token_addr, token_id), token_trades in by_token.items():
            token_trades = sorted(token_trades, key=lambda x: x.timestamp)

            for i in range(len(token_trades) - 1):
                t1 = token_trades[i]
                for j in range(i + 1, len(token_trades)):
                    t2 = token_trades[j]
                    # Prüfe: t1.from → t1.to, dann t2.from → t2.to, wobei t2.to == t1.from (Round-Trip)
                    if t2.to_address.lower() == t1.from_address.lower():
                        time_diff = t2.timestamp - t1.timestamp
                        if time_diff <= self.round_trip_window:
                            confidence = 0.9 if time_diff <= timedelta(days=1) else 0.7
                            findings.append(WashTradingFinding(
                                pattern_type="round_trip",
                                confidence=confidence,
                                addresses_involved=[t1.from_address, t1.to_address],
                                trades_involved=[t1.tx_hash, t2.tx_hash],
                                description=f"Round-trip detected: {t1.from_address[:10]}...→{t1.to_address[:10]}...→{t1.from_address[:10]}...",
                                evidence={
                                    "token": f"{token_addr}:{token_id}",
                                    "time_diff_hours": time_diff.total_seconds() / 3600,
                                    "price_first": t1.price,
                                    "price_return": t2.price,
                                }
                            ))
                            break  # Ein Finding pro Token-Paar genügt

        return findings

    async def _detect_repeated_counterparties(self, trades: List[NFTTrade]) -> List[WashTradingFinding]:
        """
        Detektiert wiederholte Transaktionen zwischen gleichen Gegenparteien
        """
        findings: List[WashTradingFinding] = []

        # Zähle Pair-Häufigkeit (from, to)
        pair_counts: Dict[Tuple[str, str], List[NFTTrade]] = defaultdict(list)
        for t in trades:
            key = tuple(sorted([t.from_address.lower(), t.to_address.lower()]))
            pair_counts[key].append(t)

        for (addr1, addr2), pair_trades in pair_counts.items():
            if len(pair_trades) >= self.repeated_threshold:
                confidence = min(0.6 + (len(pair_trades) - self.repeated_threshold) * 0.1, 0.95)
                findings.append(WashTradingFinding(
                    pattern_type="repeated_counterparty",
                    confidence=confidence,
                    addresses_involved=[addr1, addr2],
                    trades_involved=[t.tx_hash for t in pair_trades],
                    description=f"Repeated trades ({len(pair_trades)}x) between {addr1[:10]}... and {addr2[:10]}...",
                    evidence={
                        "trades_count": len(pair_trades),
                        "total_volume": sum(t.price for t in pair_trades),
                        "avg_price": sum(t.price for t in pair_trades) / len(pair_trades),
                    }
                ))

        return findings

    async def _detect_price_anomalies(self, trades: List[NFTTrade]) -> List[WashTradingFinding]:
        """
        Detektiert künstliche Preiserhöhungen (Spikes)
        """
        findings: List[WashTradingFinding] = []

        by_token: Dict[Tuple[str, str], List[NFTTrade]] = defaultdict(list)
        for t in trades:
            by_token[(t.token_address, t.token_id)].append(t)

        for (token_addr, token_id), token_trades in by_token.items():
            token_trades = sorted(token_trades, key=lambda x: x.timestamp)

            for i in range(1, len(token_trades)):
                prev_price = token_trades[i - 1].price
                curr_price = token_trades[i].price

                if prev_price > 0 and curr_price / prev_price >= self.price_spike_threshold:
                    confidence = min(0.6 + (curr_price / prev_price - self.price_spike_threshold) * 0.1, 0.9)
                    findings.append(WashTradingFinding(
                        pattern_type="price_anomaly",
                        confidence=confidence,
                        addresses_involved=[token_trades[i - 1].to_address, token_trades[i].from_address],
                        trades_involved=[token_trades[i - 1].tx_hash, token_trades[i].tx_hash],
                        description=f"Price spike detected: {prev_price:.4f} → {curr_price:.4f} ({curr_price/prev_price:.1f}x)",
                        evidence={
                            "token": f"{token_addr}:{token_id}",
                            "prev_price": prev_price,
                            "curr_price": curr_price,
                            "spike_factor": curr_price / prev_price,
                        }
                    ))

        return findings

    async def _detect_coordinated_bidding(self, trades: List[NFTTrade]) -> List[WashTradingFinding]:
        """
        Detektiert koordinierte Gebotsmuster (mehrere Trades in kurzer Zeit)
        """
        findings: List[WashTradingFinding] = []

        by_token: Dict[Tuple[str, str], List[NFTTrade]] = defaultdict(list)
        for t in trades:
            by_token[(t.token_address, t.token_id)].append(t)

        for (token_addr, token_id), token_trades in by_token.items():
            if len(token_trades) < 3:
                continue

            token_trades = sorted(token_trades, key=lambda x: x.timestamp)

            # Prüfe auf 3+ Trades innerhalb 1 Stunde
            for i in range(len(token_trades) - 2):
                cluster = [token_trades[i]]
                for j in range(i + 1, len(token_trades)):
                    if token_trades[j].timestamp - cluster[0].timestamp <= timedelta(hours=1):
                        cluster.append(token_trades[j])
                    else:
                        break

                if len(cluster) >= 3:
                    unique_addresses = set()
                    for t in cluster:
                        unique_addresses.add(t.from_address.lower())
                        unique_addresses.add(t.to_address.lower())

                    confidence = min(0.5 + len(cluster) * 0.1, 0.85)
                    findings.append(WashTradingFinding(
                        pattern_type="coordinated_bidding",
                        confidence=confidence,
                        addresses_involved=list(unique_addresses),
                        trades_involved=[t.tx_hash for t in cluster],
                        description=f"Coordinated bidding: {len(cluster)} trades within 1 hour",
                        evidence={
                            "token": f"{token_addr}:{token_id}",
                            "trades_count": len(cluster),
                            "unique_addresses": len(unique_addresses),
                            "time_span_minutes": (cluster[-1].timestamp - cluster[0].timestamp).total_seconds() / 60,
                        }
                    ))
                    break  # Ein Finding pro Cluster genügt

        return findings


# Singleton
nft_wash_detector = NFTWashTradingDetector()
