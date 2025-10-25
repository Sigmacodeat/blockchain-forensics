"""
Advanced Differentiators für Wallet Scanner
- Privacy Mixer Demixing (Tornado Cash, etc.)
- Bridge Path Reconstruction
- Advanced Indirect Risk Scoring
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class WalletScannerAdvanced:
    """Advanced forensic features für Wallet Scanner"""
    
    async def detect_mixer_activity(self, address: str, chain: str, transactions: List[Dict]) -> Dict[str, Any]:
        """
        Erkenne Mixer-Aktivität (Tornado Cash, etc.) in Transaktionen.
        
        Returns:
            {
                "has_mixer_activity": bool,
                "mixer_protocols": ["tornado_cash", ...],
                "deposits": [...],
                "withdrawals": [...],
                "demixing_heuristics": {...}
            }
        """
        # Bekannte Mixer-Adressen (vereinfacht)
        tornado_contracts = {
            "ethereum": [
                "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc",  # Tornado 0.1 ETH
                "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",  # Tornado 1 ETH
                # ... weitere
            ]
        }
        
        mixer_txs = []
        deposits = []
        withdrawals = []
        
        for tx in transactions:
            to_addr = tx.get("to_address", "").lower()
            from_addr = tx.get("from_address", "").lower()
            
            if chain in tornado_contracts:
                if to_addr in tornado_contracts[chain]:
                    deposits.append(tx)
                    mixer_txs.append(tx)
                elif from_addr in tornado_contracts[chain]:
                    withdrawals.append(tx)
                    mixer_txs.append(tx)
        
        # Demixing Heuristiken (vereinfacht)
        demixing_hints = {}
        if deposits and withdrawals:
            # Zeitbasierte Heuristik
            deposit_times = [d.get("timestamp", 0) for d in deposits]
            withdrawal_times = [w.get("timestamp", 0) for w in withdrawals]
            
            if deposit_times and withdrawal_times:
                avg_delay = sum(withdrawal_times) / len(withdrawal_times) - sum(deposit_times) / len(deposit_times)
                demixing_hints["avg_mixing_delay_seconds"] = avg_delay
                
                # Wenn Delay < 1h: höhere Wahrscheinlichkeit, dass gleicher User
                if avg_delay < 3600:
                    demixing_hints["likely_same_user"] = True
                    demixing_hints["confidence"] = 0.65
        
        return {
            "has_mixer_activity": len(mixer_txs) > 0,
            "mixer_protocols": ["tornado_cash"] if mixer_txs else [],
            "deposits": deposits,
            "withdrawals": withdrawals,
            "demixing_heuristics": demixing_hints,
        }
    
    async def reconstruct_bridge_path(self, address: str, chain: str, transactions: List[Dict]) -> List[Dict[str, Any]]:
        """
        Rekonstruiere Bridge-Pfade (Source Chain → Bridge → Target Chain).
        
        Returns:
            [
                {
                    "source_chain": "ethereum",
                    "target_chain": "polygon",
                    "bridge_protocol": "polygon_pos_bridge",
                    "source_tx": {...},
                    "bridge_tx": {...},
                    "target_address": "0x...",
                    "amount": 1.5,
                }
            ]
        """
        # Bekannte Bridge-Contracts (vereinfacht)
        bridge_contracts = {
            "ethereum": {
                "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": "polygon_pos_bridge",
                "0x8484ef722627bf18ca5ae6bcf031c23e6e922b30": "arbitrum_bridge",
                # ... weitere
            }
        }
        
        bridge_paths = []
        
        for tx in transactions:
            to_addr = tx.get("to_address", "").lower()
            
            if chain in bridge_contracts and to_addr in bridge_contracts[chain]:
                bridge_protocol = bridge_contracts[chain][to_addr]
                
                # Vereinfachte Rekonstruktion
                bridge_paths.append({
                    "source_chain": chain,
                    "target_chain": self._infer_target_chain(bridge_protocol),
                    "bridge_protocol": bridge_protocol,
                    "source_tx": tx,
                    "bridge_tx": tx,  # In echt: separater TX auf Target-Chain
                    "target_address": address,  # Vereinfacht
                    "amount": tx.get("value", 0),
                })
        
        return bridge_paths
    
    def _infer_target_chain(self, bridge_protocol: str) -> str:
        """Leite Ziel-Chain aus Bridge-Protocol ab."""
        if "polygon" in bridge_protocol:
            return "polygon"
        elif "arbitrum" in bridge_protocol:
            return "arbitrum"
        elif "optimism" in bridge_protocol:
            return "optimism"
        return "unknown"
    
    async def calculate_indirect_risk(
        self,
        address: str,
        direct_risk: float,
        counterparties: List[str],
        labels_service
    ) -> Dict[str, Any]:
        """
        Berechne indirekten Risiko-Score basierend auf Counterparties.
        
        Returns:
            {
                "indirect_risk_score": float,
                "high_risk_counterparties": int,
                "sanctioned_counterparties": int,
                "risk_factors": [...]
            }
        """
        high_risk_count = 0
        sanctioned_count = 0
        risk_factors = []
        
        # Batch-Labels holen (effizienter)
        try:
            labels_map = await labels_service.bulk_get_labels(counterparties[:100])  # Limit für Performance
        except Exception as e:
            logger.warning(f"Indirect risk calculation failed: {e}")
            labels_map = {}
        
        for cp_addr, cp_labels in labels_map.items():
            if any(l in ("sanctioned", "ofac") for l in cp_labels):
                sanctioned_count += 1
                risk_factors.append(f"Direct interaction with sanctioned address {cp_addr[:10]}...")
            
            if any(l in ("scam", "high_risk", "mixer") for l in cp_labels):
                high_risk_count += 1
        
        # Berechne indirekten Score
        # 20% des direkten Scores + Penalty basierend auf Counterparties
        indirect_base = direct_risk * 0.2
        counterparty_penalty = 0.0
        
        if sanctioned_count > 0:
            counterparty_penalty += 0.3  # +30% für Sanctions-Contact
        
        if high_risk_count > 0:
            counterparty_penalty += min(0.2, high_risk_count * 0.05)  # +5% pro high-risk, max 20%
        
        indirect_risk_score = min(1.0, indirect_base + counterparty_penalty)
        
        return {
            "indirect_risk_score": indirect_risk_score,
            "high_risk_counterparties": high_risk_count,
            "sanctioned_counterparties": sanctioned_count,
            "risk_factors": risk_factors,
        }


# Singleton
wallet_scanner_advanced = WalletScannerAdvanced()
