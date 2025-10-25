"""
VASP Screening and Management Service
======================================

Enterprise-grade VASP (Virtual Asset Service Provider) screening:
- Sanctions screening against OFAC, UN, EU, UK
- PEP (Politically Exposed Person) checks
- Adverse media screening
- Regulatory compliance verification
- Risk scoring
- Travel Rule capability verification
"""
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import os
import httpx
import re

from .models import (
    Vasp,
    VaspProfile,
    VaspScreeningResult,
    VaspType,
    VaspRiskLevel,
    ComplianceStatus
)

logger = logging.getLogger(__name__)


class VaspService:
    """VASP screening and management service"""
    
    def __init__(self) -> None:
        self._vasps: Dict[str, Vasp] = {}
        self._profiles: Dict[str, VaspProfile] = {}
        
        # Initialize with known major VASPs
        self._initialize_known_vasps()
    
    def _initialize_known_vasps(self):
        """Initialize database with known major VASPs"""
        major_vasps = [
            # Tier 1 Exchanges
            Vasp(
                id="binance",
                legal_name="Binance Holdings Limited",
                vasp_type=VaspType.EXCHANGE,
                jurisdiction="Cayman Islands",
                licenses=["VASP-Malta", "FCA-UK"],
                website="https://binance.com",
                compliance_status=ComplianceStatus.COMPLIANT,
                travel_rule_capable=True,
                supported_protocols=["TRISA", "TRP"],
                risk_level=VaspRiskLevel.LOW,
                risk_score=0.15,
                supported_chains=["ethereum", "bitcoin", "bsc", "polygon"],
                daily_volume_usd=15000000000.0,  # $15B
                verified=True,
                metadata={"tier": 1, "kyc_required": True}
            ),
            Vasp(
                id="coinbase",
                legal_name="Coinbase Global, Inc.",
                vasp_type=VaspType.EXCHANGE,
                jurisdiction="USA",
                registration_number="SEC-Listed",
                licenses=["NYDFS-BitLicense", "FCA-UK", "BaFin-DE"],
                regulatory_authorities=["SEC", "FinCEN", "NYDFS"],
                website="https://coinbase.com",
                compliance_status=ComplianceStatus.COMPLIANT,
                travel_rule_capable=True,
                supported_protocols=["TRISA"],
                risk_level=VaspRiskLevel.LOW,
                risk_score=0.1,
                supported_chains=["ethereum", "bitcoin", "polygon", "solana"],
                daily_volume_usd=3000000000.0,  # $3B
                verified=True,
                metadata={"tier": 1, "publicly_listed": True, "kyc_required": True}
            ),
            Vasp(
                id="kraken",
                legal_name="Payward, Inc.",
                dba_name="Kraken",
                vasp_type=VaspType.EXCHANGE,
                jurisdiction="USA",
                licenses=["NYDFS-BitLicense", "FCA-UK"],
                website="https://kraken.com",
                compliance_status=ComplianceStatus.COMPLIANT,
                travel_rule_capable=True,
                supported_protocols=["TRISA", "TRP"],
                risk_level=VaspRiskLevel.LOW,
                risk_score=0.12,
                supported_chains=["ethereum", "bitcoin", "polygon"],
                daily_volume_usd=1000000000.0,  # $1B
                verified=True,
                metadata={"tier": 1, "kyc_required": True}
            ),
            # Tier 2 Exchanges
            Vasp(
                id="gemini",
                legal_name="Gemini Trust Company, LLC",
                vasp_type=VaspType.EXCHANGE,
                jurisdiction="USA",
                licenses=["NYDFS-BitLicense"],
                regulatory_authorities=["NYDFS"],
                website="https://gemini.com",
                compliance_status=ComplianceStatus.COMPLIANT,
                travel_rule_capable=True,
                supported_protocols=["TRISA"],
                risk_level=VaspRiskLevel.LOW,
                risk_score=0.11,
                supported_chains=["ethereum", "bitcoin"],
                daily_volume_usd=200000000.0,  # $200M
                verified=True,
                metadata={"tier": 2, "trust_company": True}
            ),
            # DeFi Protocols (Higher risk due to less regulation)
            Vasp(
                id="uniswap",
                legal_name="Uniswap Labs",
                vasp_type=VaspType.DEFI_PROTOCOL,
                jurisdiction="USA",
                website="https://uniswap.org",
                compliance_status=ComplianceStatus.PENDING_REVIEW,
                travel_rule_capable=False,
                risk_level=VaspRiskLevel.MEDIUM,
                risk_score=0.45,
                supported_chains=["ethereum", "polygon", "arbitrum", "optimism"],
                daily_volume_usd=1500000000.0,  # $1.5B
                verified=True,
                metadata={"tier": 2, "decentralized": True, "no_kyc": True}
            ),
            # High-risk examples
            Vasp(
                id="mixer_xyz",
                legal_name="Unknown",
                dba_name="Mixer XYZ",
                vasp_type=VaspType.OTHER,
                jurisdiction="Unknown",
                compliance_status=ComplianceStatus.SANCTIONED,
                travel_rule_capable=False,
                risk_level=VaspRiskLevel.CRITICAL,
                risk_score=0.95,
                supported_chains=["ethereum", "bitcoin"],
                verified=False,
                metadata={"mixer": True, "sanctioned": True}
            )
        ]
        
        for vasp in major_vasps:
            self._vasps[vasp.id] = vasp

    def get(self, vasp_id: str) -> Optional[Vasp]:
        """Get VASP by ID"""
        return self._vasps.get(vasp_id)

    def upsert(self, vasp: Vasp) -> Vasp:
        """Insert or update VASP"""
        vasp.updated_at = datetime.utcnow()
        if not vasp.created_at:
            vasp.created_at = datetime.utcnow()
        
        self._vasps[vasp.id] = vasp
        return vasp
    
    def search(
        self,
        query: str,
        vasp_type: Optional[VaspType] = None,
        jurisdiction: Optional[str] = None,
        limit: int = 50
    ) -> List[Vasp]:
        """
        Search VASPs by name, type, or jurisdiction.
        
        Args:
            query: Search query (name or ID)
            vasp_type: Filter by VASP type
            jurisdiction: Filter by jurisdiction
            limit: Maximum results
            
        Returns:
            List of matching VASPs
        """
        results = []
        query_lower = query.lower() if query else ""
        
        for vasp in self._vasps.values():
            # Type filter
            if vasp_type and vasp.vasp_type != vasp_type:
                continue
            
            # Jurisdiction filter
            if jurisdiction and vasp.jurisdiction != jurisdiction:
                continue
            
            # Text search
            if query:
                searchable = f"{vasp.id} {vasp.legal_name} {vasp.dba_name or ''}".lower()
                if query_lower not in searchable:
                    continue
            
            results.append(vasp)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def screen_vasp(
        self,
        vasp_id: str,
        check_sanctions: bool = True,
        check_pep: bool = True,
        check_adverse_media: bool = True
    ) -> VaspScreeningResult:
        """
        Screen VASP for compliance risks.
        
        Args:
            vasp_id: VASP identifier
            check_sanctions: Check sanctions lists
            check_pep: Check PEP lists
            check_adverse_media: Check adverse media
            
        Returns:
            Screening result with risk assessment
        """
        vasp = self.get(vasp_id)
        
        if not vasp:
            return VaspScreeningResult(
                vasp_id=vasp_id,
                vasp_name="Unknown",
                overall_risk=VaspRiskLevel.UNKNOWN,
                recommended_action="reject",
                compliance_issues=["VASP not found in database"]
            )
        
        # Initialize result
        result = VaspScreeningResult(
            vasp_id=vasp.id,
            vasp_name=vasp.legal_name,
            overall_risk=vasp.risk_level,
            risk_score=vasp.risk_score or 0.5,
            compliance_status=vasp.compliance_status
        )
        
        # Sanctions screening
        if check_sanctions:
            sanctions_hit = await self._check_sanctions(vasp)
            result.sanctions_hit = sanctions_hit["matched"]
            result.sanctions_lists = sanctions_hit.get("lists", [])
            
            if sanctions_hit["matched"]:
                result.risk_factors.append("Sanctions list match")
                result.compliance_issues.append(f"Matched on {', '.join(sanctions_hit.get('lists', []))}")
        
        # PEP screening (simplified - would integrate with real PEP databases)
        if check_pep:
            pep_hit = self._check_pep(vasp)
            result.pep_hit = pep_hit
            if pep_hit:
                result.risk_factors.append("PEP connection")
        
        # Adverse media screening
        if check_adverse_media:
            adverse_media = self._check_adverse_media(vasp)
            result.adverse_media_hit = adverse_media["hit"]
            result.adverse_media_count = adverse_media["count"]
            
            if adverse_media["hit"]:
                result.risk_factors.append(f"{adverse_media['count']} adverse media mentions")
        
        # Calculate overall risk
        result.overall_risk, result.risk_score = self._calculate_risk(vasp, result)
        
        # Compliance issues
        if not vasp.travel_rule_capable:
            result.compliance_issues.append("Travel Rule not supported")
        
        if not vasp.licenses:
            result.compliance_issues.append("No regulatory licenses")
        
        if vasp.vasp_type == VaspType.DEFI_PROTOCOL:
            result.warnings.append("Decentralized protocol - limited KYC")
        
        # Recommended action
        result.recommended_action = self._determine_action(result)
        
        return result
    
    async def _check_sanctions(self, vasp: Vasp) -> Dict[str, Any]:
        """Check VASP against sanctions lists"""
        # Import sanctions service
        try:
            from app.compliance.sanctions.service import sanctions_service
            
            # Check legal name
            name_result = sanctions_service.screen(name=vasp.legal_name)
            
            # Check DBA name if different
            if vasp.dba_name and vasp.dba_name != vasp.legal_name:
                dba_result = sanctions_service.screen(name=vasp.dba_name)
                if dba_result["matched"]:
                    return {
                        "matched": True,
                        "lists": dba_result.get("lists", []),
                        "entity_id": dba_result.get("entity_id")
                    }
            
            if name_result["matched"]:
                return {
                    "matched": True,
                    "lists": name_result.get("lists", []),
                    "entity_id": name_result.get("entity_id")
                }
        
        except Exception as e:
            logger.warning(f"Sanctions check failed: {e}")
        
        # Check if explicitly sanctioned
        if vasp.compliance_status == ComplianceStatus.SANCTIONED:
            return {
                "matched": True,
                "lists": ["internal"],
                "entity_id": vasp.id
            }
        
        return {"matched": False}
    
    def _check_pep(self, vasp: Vasp) -> bool:
        """Check for PEP connections.

        Behavior:
        - If provider configured (PEP_API_URL/PEP_API_KEY), query provider.
        - Else fallback to metadata flag.
        """
        # Safe ENV lookup only; avoid optional app.config import during tests
        api_url = os.getenv("PEP_API_URL")
        api_key = os.getenv("PEP_API_KEY")
        if api_url and api_key:
            try:
                q = vasp.legal_name
                headers = {"Authorization": f"Bearer {api_key}"}
                params = {"q": q}
                timeout = float(os.getenv("PEP_API_TIMEOUT", "8"))
                with httpx.Client(timeout=timeout) as client:
                    resp = client.get(str(api_url).rstrip("/") + "/search", headers=headers, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Expect provider returns { matches: int } or list
                        if isinstance(data, dict) and int(data.get("matches", 0)) > 0:
                            return True
                        if isinstance(data, list) and len(data) > 0:
                            return True
                    else:
                        logger.warning(f"PEP provider non-200: {resp.status_code}")
            except Exception as e:
                logger.warning(f"PEP provider error: {e}")
        # Fallback
        return vasp.metadata.get("pep_connected", False)
    
    def _check_adverse_media(self, vasp: Vasp) -> Dict[str, Any]:
        """Check adverse media mentions.

        Behavior:
        - If provider configured (MEDIA_API_URL/MEDIA_API_KEY), query provider.
        - Else fallback to metadata count.
        """
        # Safe ENV lookup only; avoid optional app.config import during tests
        api_url = os.getenv("MEDIA_API_URL")
        api_key = os.getenv("MEDIA_API_KEY")
        if api_url and api_key:
            try:
                q = vasp.legal_name
                headers = {"Authorization": f"Bearer {api_key}"}
                params = {"q": q, "since_days": int(os.getenv("MEDIA_SINCE_DAYS", "365"))}
                timeout = float(os.getenv("MEDIA_API_TIMEOUT", "8"))
                with httpx.Client(timeout=timeout) as client:
                    resp = client.get(str(api_url).rstrip("/") + "/adverse-media", headers=headers, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict):
                            cnt = int(data.get("count", 0))
                            return {"hit": cnt > 0, "count": cnt}
                        if isinstance(data, list):
                            return {"hit": len(data) > 0, "count": len(data)}
                    else:
                        logger.warning(f"Adverse media provider non-200: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Adverse media provider error: {e}")
        # Fallback
        count = vasp.metadata.get("adverse_media_count", 0)
        return {"hit": count > 0, "count": count}
    
    def _calculate_risk(
        self,
        vasp: Vasp,
        screening: VaspScreeningResult
    ) -> tuple[VaspRiskLevel, float]:
        """Calculate overall risk score"""
        score = vasp.risk_score or 0.5
        
        # Adjust for screening results
        if screening.sanctions_hit:
            score = max(score, 0.9)
        
        if screening.pep_hit:
            score = min(1.0, score + 0.2)
        
        if screening.adverse_media_hit:
            score = min(1.0, score + (screening.adverse_media_count * 0.05))
        
        # Adjust for compliance status
        if vasp.compliance_status == ComplianceStatus.SANCTIONED:
            score = 1.0
        elif vasp.compliance_status == ComplianceStatus.NON_COMPLIANT:
            score = max(score, 0.7)
        elif vasp.compliance_status == ComplianceStatus.COMPLIANT:
            score = max(0.1, score - 0.1)
        
        # Determine risk level
        if score >= 0.8:
            level = VaspRiskLevel.CRITICAL
        elif score >= 0.6:
            level = VaspRiskLevel.HIGH
        elif score >= 0.3:
            level = VaspRiskLevel.MEDIUM
        else:
            level = VaspRiskLevel.LOW
        
        return level, score
    
    def _determine_action(self, result: VaspScreeningResult) -> str:
        """Determine recommended action"""
        if result.sanctions_hit:
            return "reject"
        
        if result.overall_risk == VaspRiskLevel.CRITICAL:
            return "reject"
        elif result.overall_risk == VaspRiskLevel.HIGH:
            return "review"
        elif result.overall_risk == VaspRiskLevel.MEDIUM:
            return "monitor"
        else:
            return "approve"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get VASP database statistics"""
        total = len(self._vasps)
        
        by_type = {}
        by_risk = {}
        by_jurisdiction = {}
        travel_rule_count = 0
        
        for vasp in self._vasps.values():
            # By type
            type_str = vasp.vasp_type.value
            by_type[type_str] = by_type.get(type_str, 0) + 1
            
            # By risk
            risk_str = vasp.risk_level.value
            by_risk[risk_str] = by_risk.get(risk_str, 0) + 1
            
            # By jurisdiction
            juris = vasp.jurisdiction or "Unknown"
            by_jurisdiction[juris] = by_jurisdiction.get(juris, 0) + 1
            
            # Travel Rule capable
            if vasp.travel_rule_capable:
                travel_rule_count += 1
        
        return {
            "total_vasps": total,
            "by_type": by_type,
            "by_risk_level": by_risk,
            "by_jurisdiction": by_jurisdiction,
            "travel_rule_capable": travel_rule_count,
            "travel_rule_percentage": (travel_rule_count / total * 100) if total > 0 else 0
        }


vasp_service = VaspService()
