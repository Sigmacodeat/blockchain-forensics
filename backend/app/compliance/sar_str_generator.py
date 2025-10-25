"""
Automated SAR/STR Report Generation
====================================

Generate Suspicious Activity Reports (SAR) and Suspicious Transaction Reports (STR)
for regulatory compliance.

SUPPORTED JURISDICTIONS:
- USA: FinCEN SAR (Form 111)
- EU: STR (various formats)
- UK: SARs Online
- Canada: FINTRAC STR
- Singapore: MAS STR
- Australia: AUSTRAC SMR
- Raw: JSON export
- USA: FinCEN SAR (Form 111)
- EU: STR (various formats)
- UK: SARs Online
- Canada: FINTRAC STR
- Singapore: STR
- Australia: SMR

FEATURES:
- Template-based generation
- Auto-populate from case data
- Risk score integration
- Evidence attachment
- Regulatory format compliance
- E-filing support
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class SARReport:
    """Suspicious Activity Report"""
    report_id: str
    jurisdiction: str
    report_type: str  # SAR, STR, SMR
    filing_institution: str
    subject_name: str
    subject_addresses: List[str]
    suspicious_activity: str
    amount_usd: float
    transaction_date: str
    narrative: str
    risk_score: float
    evidence_files: List[str]
    
    def to_fincen_format(self) -> Dict[str, Any]:
        """Convert to FinCEN SAR XML format"""
        return {
            "SARXReport": {
                "ReportID": self.report_id,
                "FilingInstitution": self.filing_institution,
                "SubjectInformation": {
                    "Name": self.subject_name,
                    "Addresses": self.subject_addresses
                },
                "SuspiciousActivity": {
                    "Type": self.suspicious_activity,
                    "Amount": self.amount_usd,
                    "Date": self.transaction_date
                },
                "Narrative": self.narrative,
                "RiskAssessment": {"Score": self.risk_score}
            }
        }
    
    def to_eu_str_format(self) -> Dict[str, Any]:
        """Convert to EU STR format"""
        return {
            "STR": {
                "ReportNumber": self.report_id,
                "ReportingEntity": self.filing_institution,
                "SuspectedPerson": {
                    "Name": self.subject_name,
                    "KnownAddresses": self.subject_addresses
                },
                "SuspiciousTransaction": {
                    "Description": self.suspicious_activity,
                    "Value": self.amount_usd,
                    "Date": self.transaction_date
                },
                "Reasons": self.narrative
            }
        }

class SARSTRGenerator:
    """Generate SAR/STR reports from cases"""
    
    async def generate_from_case(self, case_id: str, case_data: Dict) -> SARReport:
        """Generate SAR/STR from case data"""
        logger.info(f"Generating SAR for case {case_id}")
        
        # Extract key information
        subject_addresses = case_data.get("addresses", [])
        risk_score = case_data.get("risk_score", 0.0)
        
        # Generate narrative
        narrative = self._generate_narrative(case_data)
        
        report = SARReport(
            report_id=f"SAR-{case_id}",
            jurisdiction="US",  # Would be configurable
            report_type="SAR",
            filing_institution="Blockchain Forensics Platform",
            subject_name=case_data.get("subject_name", "Unknown"),
            subject_addresses=subject_addresses,
            suspicious_activity="Cryptocurrency Money Laundering",
            amount_usd=case_data.get("total_amount_usd", 0.0),
            transaction_date=datetime.utcnow().isoformat(),
            narrative=narrative,
            risk_score=risk_score,
            evidence_files=case_data.get("attachments", [])
        )
        
        return report
    
    def _generate_narrative(self, case_data: Dict) -> str:
        """Auto-generate detailed narrative from case data"""
        parts = []
        
        # Basis-Informationen
        addresses = case_data.get('addresses', [])
        tx_count = len(addresses)
        total_usd = case_data.get('total_amount_usd', 0.0)
        risk_score = case_data.get('risk_score', 0.0)
        
        parts.append(f"Investigation identified suspicious cryptocurrency activity involving {tx_count} addresses with a total transaction volume of ${total_usd:,.2f} USD.")
        
        # Risk-Faktoren
        risk_factors = case_data.get('risk_factors', [])
        if risk_factors:
            parts.append(f"Key risk indicators include: {', '.join(risk_factors)}.")
        
        # Sanctions & OFAC
        if case_data.get('sanctions_hit'):
            sanctioned_entities = case_data.get('sanctioned_entities', [])
            if sanctioned_entities:
                parts.append(f"Subject is associated with sanctioned entities: {', '.join(sanctioned_entities)}.")
            else:
                parts.append("OFAC sanctions match detected on involved addresses.")
        
        # Mixer & Privacy
        if case_data.get('mixer_usage'):
            parts.append("Transactions involve cryptocurrency mixers/tumblers, indicating attempts to obscure transaction origins.")
        
        # Bridges & Cross-Chain
        bridges = case_data.get('bridge_transactions', [])
        if bridges:
            parts.append(f"Cross-chain bridge transactions detected: {len(bridges)} instances, potentially used for asset movement between blockchains.")
        
        # Taint Analysis
        tainted_funds = case_data.get('tainted_funds_percentage', 0.0)
        if tainted_funds > 0:
            parts.append(f"Taint analysis indicates {tainted_funds:.1f}% of funds originate from high-risk sources.")
        
        # Clustering
        cluster_size = case_data.get('wallet_cluster_size', 1)
        if cluster_size > 1:
            parts.append(f"Wallet clustering analysis revealed {cluster_size} interconnected addresses, suggesting coordinated activity.")
        
        # Dark Web & Intel
        if case_data.get('dark_web_mentions'):
            parts.append("Addresses associated with dark web marketplaces or illicit activities based on threat intelligence.")
        
        # PEP Exposure
        if case_data.get('pep_exposure'):
            parts.append("Subject has Politically Exposed Person (PEP) associations, increasing compliance risk.")
        
        # Geographic Risk
        high_risk_countries = case_data.get('high_risk_countries', [])
        if high_risk_countries:
            parts.append(f"Transactions involve entities in high-risk jurisdictions: {', '.join(high_risk_countries)}.")
        
        # Narrative zusammenfügen
        narrative = ' '.join(parts)
        
        # Risk-Score Integration
        if risk_score >= 0.8:
            narrative += f" Overall risk assessment score: {risk_score:.2f}/1.0 (Critical). Immediate action recommended."
        elif risk_score >= 0.6:
            narrative += f" Overall risk assessment score: {risk_score:.2f}/1.0 (High). Enhanced monitoring advised."
        else:
            narrative += f" Overall risk assessment score: {risk_score:.2f}/1.0 (Medium). Further investigation warranted."
        
        return narrative

    async def export_report(self, report: SARReport, format: str = "fincen", validate: bool = True) -> str:
        """Export report in specified format"""
        if format == "fincen":
            data = report.to_fincen_format()
        elif format == "eu":
            data = report.to_eu_str_format()
        else:
            data = report.__dict__
        
        # Convert to JSON/XML
        return json.dumps(data, indent=2)

    def to_uk_sar_format(self) -> Dict[str, Any]:
        """Convert to UK SAR format (SARs Online)"""
        return {
            "SAR": {
                "ReportID": self.report_id,
                "ReportingEntity": self.filing_institution,
                "Subject": {
                    "Name": self.subject_name,
                    "Addresses": self.subject_addresses
                },
                "SuspiciousActivity": {
                    "Description": self.suspicious_activity,
                    "Value": self.amount_usd,
                    "Date": self.transaction_date
                },
                "Narrative": self.narrative,
                "RiskScore": self.risk_score
            }
        }

    def to_canada_fintrac_format(self) -> Dict[str, Any]:
        """Convert to Canada FINTRAC STR format"""
        return {
            "STR": {
                "ReportNumber": self.report_id,
                "ReportingEntity": self.filing_institution,
                "PersonOrEntity": {
                    "Name": self.subject_name,
                    "Addresses": self.subject_addresses
                },
                "Transaction": {
                    "Description": self.suspicious_activity,
                    "Amount": self.amount_usd,
                    "Date": self.transaction_date
                },
                "Reasons": self.narrative,
                "RiskAssessment": self.risk_score
            }
        }

    def to_singapore_mas_format(self) -> Dict[str, Any]:
        """Convert to Singapore MAS STR format"""
        return {
            "STR": {
                "ReportID": self.report_id,
                "ReportingInstitution": self.filing_institution,
                "Subject": {
                    "Name": self.subject_name,
                    "Addresses": self.subject_addresses
                },
                "SuspiciousTransaction": {
                    "Details": self.suspicious_activity,
                    "Amount": self.amount_usd,
                    "Date": self.transaction_date
                },
                "Narrative": self.narrative,
                "RiskScore": self.risk_score
            }
        }

    def to_australia_smr_format(self) -> Dict[str, Any]:
        """Convert to Australia SMR format"""
        return {
            "SMR": {
                "ReportID": self.report_id,
                "ReportingEntity": self.filing_institution,
                "Suspect": {
                    "Name": self.subject_name,
                    "Addresses": self.subject_addresses
                },
                "Activity": {
                    "Description": self.suspicious_activity,
                    "Value": self.amount_usd,
                    "Date": self.transaction_date
                },
                "Narrative": self.narrative,
                "RiskLevel": self.risk_score
            }
        }


sar_generator = SARSTRGenerator()
__all__ = ['SARSTRGenerator', 'sar_generator', 'SARReport']
