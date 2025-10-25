"""
Chainalysis Integration für Blockchain-Forensik

Integriert Chainalysis APIs für erweiterte Blockchain-Analyse und Compliance.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Chainalysis SDK (optional)
try:
    import chainalysis
    from chainalysis.api import ChainalysisAPI
    _CHAINALYSIS_AVAILABLE = True
except ImportError:
    _CHAINALYSIS_AVAILABLE = False
    logging.warning("Chainalysis SDK nicht verfügbar - Chainalysis-Integration wird deaktiviert")

from app.services.wallet_service import wallet_service
from app.services.wallet_ai_service import wallet_ai_agent

logger = logging.getLogger(__name__)

class ChainalysisService:
    """Service für Chainalysis-Integration"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.api_client = None

        if _CHAINALYSIS_AVAILABLE and api_key:
            try:
                self.api_client = ChainalysisAPI(api_key=api_key)
                logger.info("Chainalysis API-Client initialisiert")
            except Exception as e:
                logger.error(f"Chainalysis API-Client Initialisierung fehlgeschlagen: {e}")
                self.api_client = None

    async def analyze_address(self, chain: str, address: str) -> Dict[str, Any]:
        """Analysiert eine Adresse mit Chainalysis"""
        if not self.api_client:
            # Fallback zu KI-basierter Analyse
            return await self._fallback_address_analysis(chain, address)

        try:
            # Chainalysis API aufrufen
            if chain.lower() == "bitcoin":
                # Bitcoin-Adresse analysieren
                response = await self.api_client.get_address_risk(address)
            elif chain.lower() == "ethereum":
                # Ethereum-Adresse analysieren
                response = await self.api_client.get_address_risk(address, blockchain="ethereum")
            else:
                # Andere Chains - Fallback
                return await self._fallback_address_analysis(chain, address)

            # Chainalysis-Daten verarbeiten
            return {
                "chainalysis_score": response.get("risk_score", 0),
                "chainalysis_rating": response.get("rating", "unknown"),
                "chainalysis_category": response.get("category", "unknown"),
                "chainalysis_clusters": response.get("clusters", []),
                "chainalysis_first_seen": response.get("first_seen"),
                "chainalysis_last_seen": response.get("last_seen"),
                "confidence": response.get("confidence", 0),
                "source": "chainalysis"
            }

        except Exception as e:
            logger.error(f"Chainalysis-Adressanalyse fehlgeschlagen: {e}")
            return await self._fallback_address_analysis(chain, address)

    async def analyze_transaction(self, chain: str, tx_hash: str) -> Dict[str, Any]:
        """Analysiert eine Transaktion mit Chainalysis"""
        if not self.api_client:
            return await self._fallback_transaction_analysis(chain, tx_hash)

        try:
            # Chainalysis Transaction API
            response = await self.api_client.get_transaction_risk(tx_hash, blockchain=chain)

            return {
                "chainalysis_risk_score": response.get("risk_score", 0),
                "chainalysis_category": response.get("category", "unknown"),
                "chainalysis_clusters": response.get("clusters", []),
                "chainalysis_entities": response.get("entities", []),
                "confidence": response.get("confidence", 0),
                "source": "chainalysis"
            }

        except Exception as e:
            logger.error(f"Chainalysis-Transaktionsanalyse fehlgeschlagen: {e}")
            return await self._fallback_transaction_analysis(chain, tx_hash)

    async def get_sanctions_data(self, address: str, chain: str) -> Dict[str, Any]:
        """Prüft Adresse auf Sanktionen"""
        if not self.api_client:
            return {"sanctions_check": "unavailable", "details": "Chainalysis nicht verfügbar"}

        try:
            response = await self.api_client.check_sanctions(address, blockchain=chain)

            return {
                "is_sanctioned": response.get("is_sanctioned", False),
                "sanctions_list": response.get("sanctions_list", []),
                "sanctions_details": response.get("details", {}),
                "confidence": response.get("confidence", 0),
                "source": "chainalysis"
            }

        except Exception as e:
            logger.error(f"Chainalysis-Sanktionsprüfung fehlgeschlagen: {e}")
            return {"sanctions_check": "error", "error": str(e)}

    async def _fallback_address_analysis(self, chain: str, address: str) -> Dict[str, Any]:
        """Fallback-Analyse ohne Chainalysis"""
        # KI-basierte Analyse verwenden
        try:
            balance = await wallet_service.get_balance(chain, address)
            analysis = await wallet_ai_agent.analyze_wallet_risk(chain, address, balance)

            return {
                "chainalysis_score": analysis.get("risk_score", 0),
                "chainalysis_rating": "unknown",
                "chainalysis_category": "analyzed",
                "chainalysis_clusters": [],
                "confidence": 0.7,  # KI-basierte Confidence
                "source": "ai_fallback",
                "ai_analysis": analysis
            }

        except Exception as e:
            logger.error(f"Fallback-Adressanalyse fehlgeschlagen: {e}")
            return {
                "chainalysis_score": 0.5,
                "chainalysis_rating": "unknown",
                "chainalysis_category": "error",
                "confidence": 0,
                "source": "error"
            }

    async def _fallback_transaction_analysis(self, chain: str, tx_hash: str) -> Dict[str, Any]:
        """Fallback-Transaktionsanalyse ohne Chainalysis"""
        try:
            analysis = await wallet_ai_agent.analyze_transaction(chain, tx_hash)

            return {
                "chainalysis_risk_score": analysis.get("risk_score", 0),
                "chainalysis_category": "analyzed",
                "chainalysis_clusters": [],
                "chainalysis_entities": [],
                "confidence": 0.6,
                "source": "ai_fallback",
                "ai_analysis": analysis
            }

        except Exception as e:
            logger.error(f"Fallback-Transaktionsanalyse fehlgeschlagen: {e}")
            return {
                "chainalysis_risk_score": 0.5,
                "chainalysis_category": "error",
                "confidence": 0,
                "source": "error"
            }

class ChainalysisIntegrationManager:
    """Manager für Chainalysis-Integration"""

    def __init__(self):
        self.chainalysis_service = ChainalysisService()
        self.integration_enabled = _CHAINALYSIS_AVAILABLE and self.chainalysis_service.api_key is not None

    async def analyze_wallet_comprehensive(
        self,
        wallet_id: str,
        include_chainalysis: bool = True
    ) -> Dict[str, Any]:
        """Umfassende Wallet-Analyse mit Chainalysis-Integration"""

        try:
            # Wallet-Daten laden
            wallet_data = await wallet_service.load_wallet_data(wallet_id)
            if not wallet_data:
                raise ValueError(f"Wallet {wallet_id} nicht gefunden")

            # Basis-Analyse
            balance = await wallet_service.get_balance(
                chain=wallet_data["chain"],
                address=wallet_data["address"]
            )

            # Chainalysis-Analyse (falls verfügbar)
            chainalysis_data = None
            if include_chainalysis and self.integration_enabled:
                chainalysis_data = await self.chainalysis_service.analyze_address(
                    chain=wallet_data["chain"],
                    address=wallet_data["address"]
                )

            # KI-Analyse
            ai_analysis = await wallet_ai_agent.analyze_wallet_comprehensive(
                chain=wallet_data["chain"],
                address=wallet_data["address"],
                balance=balance,
                transaction_history=[]
            )

            # Kombinierte Analyse erstellen
            combined_risk_score = self._combine_risk_scores(
                ai_score=ai_analysis.get("overall_risk_score", 0),
                chainalysis_score=chainalysis_data.get("chainalysis_score", 0) if chainalysis_data else 0
            )

            return {
                "wallet_id": wallet_id,
                "combined_risk_score": combined_risk_score,
                "ai_analysis": ai_analysis,
                "chainalysis_data": chainalysis_data,
                "sources_used": ["ai"] + (["chainalysis"] if chainalysis_data else []),
                "confidence": self._calculate_overall_confidence(chainalysis_data, ai_analysis),
                "recommendations": self._generate_combined_recommendations(
                    ai_analysis.get("recommendations", []),
                    chainalysis_data
                ),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Chainalysis-Integration fehlgeschlagen: {e}")
            # Fallback zu reiner KI-Analyse
            return await wallet_ai_agent.analyze_wallet_comprehensive(
                chain=wallet_data["chain"],
                address=wallet_data["address"],
                balance=balance,
                transaction_history=[]
            )

    def _combine_risk_scores(self, ai_score: float, chainalysis_score: float) -> float:
        """Kombiniert AI- und Chainalysis-Risikoscores"""
        if chainalysis_score > 0:
            # Gewichtete Kombination
            return (ai_score * 0.4) + (chainalysis_score * 0.6)
        else:
            # Nur AI-Score
            return ai_score

    def _calculate_overall_confidence(self, chainalysis_data: Optional[Dict], ai_analysis: Dict) -> float:
        """Berechnet Gesamt-Confidence der Analyse"""
        base_confidence = ai_analysis.get("confidence", 0.5)

        if chainalysis_data:
            chainalysis_confidence = chainalysis_data.get("confidence", 0)
            # Kombinierte Confidence
            return (base_confidence * 0.6) + (chainalysis_confidence * 0.4)

        return base_confidence

    def _generate_combined_recommendations(self, ai_recommendations: List[str], chainalysis_data: Optional[Dict]) -> List[str]:
        """Generiert kombinierte Empfehlungen"""
        recommendations = list(ai_recommendations)

        if chainalysis_data:
            chainalysis_rating = chainalysis_data.get("chainalysis_rating", "").lower()

            if chainalysis_rating in ["high_risk", "sanctioned"]:
                recommendations.append("Erhöhte Überwachung aufgrund Chainalysis-Daten")
            elif chainalysis_rating in ["medium_risk"]:
                recommendations.append("Standard-Überwachung mit Chainalysis-Insights")

            # Sanktionshinweise
            if chainalysis_data.get("is_sanctioned", False):
                recommendations.append("Sanktionsprüfung erforderlich - Chainalysis-Alarm")

        return recommendations

    async def check_compliance_status(self, address: str, chain: str) -> Dict[str, Any]:
        """Prüft Compliance-Status einer Adresse"""
        try:
            # Chainalysis-Sanktionsprüfung
            sanctions_data = await self.chainalysis_service.get_sanctions_data(address, chain)

            # Basis-Compliance-Status
            compliance_status = {
                "address": address,
                "chain": chain,
                "is_compliant": True,
                "sanctions_check": sanctions_data,
                "risk_level": "low",
                "flags": [],
                "checked_at": datetime.utcnow().isoformat()
            }

            # Sanktions-Flags setzen
            if sanctions_data.get("is_sanctioned", False):
                compliance_status["is_compliant"] = False
                compliance_status["risk_level"] = "critical"
                compliance_status["flags"].append("sanctioned_address")

            # Chainalysis-Risiko-Level
            if sanctions_data.get("sanctions_list"):
                compliance_status["flags"].extend(
                    [f"sanctions_{list_item}" for list_item in sanctions_data["sanctions_list"]]
                )

            return compliance_status

        except Exception as e:
            logger.error(f"Compliance-Status-Prüfung fehlgeschlagen: {e}")
            return {
                "address": address,
                "chain": chain,
                "is_compliant": False,
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }

    def get_integration_status(self) -> Dict[str, Any]:
        """Holt Status der Chainalysis-Integration"""
        return {
            "chainalysis_available": _CHAINALYSIS_AVAILABLE,
            "api_key_configured": self.chainalysis_service.api_key is not None,
            "integration_enabled": self.integration_enabled,
            "supported_chains": ["bitcoin", "ethereum"] if self.integration_enabled else [],
            "features": [
                "address_risk_analysis",
                "transaction_risk_analysis",
                "sanctions_screening"
            ] if self.integration_enabled else []
        }

# Singleton-Instance
chainalysis_manager = ChainalysisIntegrationManager()
