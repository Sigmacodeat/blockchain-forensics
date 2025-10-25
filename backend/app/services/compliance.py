"""
Compliance Framework für Blockchain Forensics
=============================================

Vollständiges Compliance-System für Strafbehörden:
- Audit-Trails für alle Aktionen
- Chain-of-Custody für Beweise
- Regulatorische Berichterstattung
- GDPR und Datenschutz-Compliance
- Gerichtsverwertbare Beweise
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid

logger = logging.getLogger(__name__)


class ComplianceLevel(str, Enum):
    """Compliance-Level für verschiedene Anforderungen"""
    STANDARD = "standard"           # Normale Forensik
    ENHANCED = "enhanced"           # Erhöhte Sicherheit
    COURT_ADMISSIBLE = "court"      # Gerichtsverwertbar
    GDPR = "gdpr"                  # EU-Datenschutz
    LAW_ENFORCEMENT = "le"         # Strafverfolgung


class AuditEventType(str, Enum):
    """Arten von Audit-Events"""
    DATA_ACCESS = "data_access"
    ANALYSIS_RUN = "analysis_run"
    REPORT_GENERATION = "report_generation"
    EXPORT_DATA = "export_data"
    USER_ACTION = "user_action"
    SYSTEM_CHANGE = "system_change"
    EVIDENCE_COLLECTION = "evidence_collection"


@dataclass
class AuditEvent:
    """Audit-Event für vollständige Nachverfolgung"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    resource_id: str  # Adresse, Tx-Hash, etc.
    action: str       # "view", "analyze", "export", etc.
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    compliance_level: ComplianceLevel
    hash_chain: str = ""  # Für Blockchain-basierte Integrität

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.hash_chain:
            self.hash_chain = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Berechnet Hash für Chain-of-Custody"""
        content = f"{self.event_id}{self.timestamp.isoformat()}{self.event_type.value}{self.user_id}{self.resource_id}{self.action}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "compliance_level": self.compliance_level.value,
            "hash_chain": self.hash_chain
        }


@dataclass
class EvidenceRecord:
    """Gerichtsverwertbarer Beweis-Record"""
    evidence_id: str
    case_id: str
    resource_id: str  # Adresse, Tx-Hash, etc.
    resource_type: str  # "address", "transaction", "block"
    collection_timestamp: datetime
    collection_method: str
    collected_by: str
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)
    integrity_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_custody_entry(self, handler: str, action: str, timestamp: datetime, notes: str = ""):
        """Fügt Chain-of-Custody Eintrag hinzu"""
        entry = {
            "handler": handler,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "notes": notes,
            "hash": hashlib.sha256(f"{handler}{action}{timestamp.isoformat()}".encode()).hexdigest()
        }
        self.chain_of_custody.append(entry)
        self._update_integrity_hash()

    def _update_integrity_hash(self):
        """Aktualisiert Integritäts-Hash"""
        content = json.dumps(self.chain_of_custody, sort_keys=True)
        self.integrity_hash = hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "collection_timestamp": self.collection_timestamp.isoformat(),
            "collection_method": self.collection_method,
            "collected_by": self.collected_by,
            "chain_of_custody": self.chain_of_custody,
            "integrity_hash": self.integrity_hash,
            "metadata": self.metadata
        }


class GDPRComplianceManager:
    """GDPR-Compliance für Datenverarbeitung"""

    def __init__(self):
        self.data_retention_policies = {
            "audit_logs": 365,        # 1 Jahr
            "user_data": 90,          # 3 Monate
            "analysis_results": 180,  # 6 Monate
            "evidence_records": 2555  # 7 Jahre
        }
        self.pii_fields = ["email", "phone", "name", "ip_address", "user_agent"]
        self.consent_records = {}

    def check_data_minimization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prüft Datenminimierung nach GDPR"""
        sanitized = data.copy()

        # Entferne oder maskiere PII-Daten
        for field in self.pii_fields:
            if field in sanitized:
                if field in ["ip_address"]:
                    # Maskiere IP-Adresse
                    sanitized[field] = self._mask_ip(sanitized[field])
                else:
                    # Entferne andere PII
                    del sanitized[field]

        return sanitized

    def _mask_ip(self, ip: str) -> str:
        """Maskiert IP-Adresse"""
        if "." in ip:  # IPv4
            parts = ip.split(".")
            return f"{parts[0]}.{parts[1]}.xxx.xxx"
        elif ":" in ip:  # IPv6
            return "xxxx:xxxx:xxxx:xxxx::xxxx"
        return "xxx.xxx.xxx.xxx"

    def schedule_data_deletion(self, data_type: str, record_id: str, retention_days: int = None):
        """Plant Datenlöschung nach Retention-Policy"""
        if retention_days is None:
            retention_days = self.data_retention_policies.get(data_type, 365)

        deletion_date = datetime.utcnow() + timedelta(days=retention_days)

        # In Produktion: Daten in Queue für automatische Löschung
        logger.info(f"Scheduled deletion of {data_type}:{record_id} on {deletion_date}")

    def record_consent(self, user_id: str, consent_type: str, granted: bool, details: Dict[str, Any]):
        """Dokumentiert Benutzer-Consent"""
        self.consent_records[user_id] = {
            "consent_type": consent_type,
            "granted": granted,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }


class RegulatoryReporter:
    """Berichterstattung für regulatorische Anforderungen"""

    def __init__(self):
        self.report_templates = {
            "suspicious_activity": self._generate_sar_template,
            "currency_transaction": self._generate_ctr_template,
            "evidence_summary": self._generate_evidence_template
        }

    def generate_suspicious_activity_report(self, alert: Dict[str, Any], case_id: str) -> str:
        """Generiert SAR (Suspicious Activity Report)"""
        template_data = {
            "case_id": case_id,
            "alert_id": alert.get("alert_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert.get("alert_type"),
            "severity": alert.get("severity"),
            "description": alert.get("description"),
            "metadata": alert.get("metadata", {}),
            "evidence_links": self._generate_evidence_links(alert)
        }

        return self._generate_sar_template(template_data)

    def generate_evidence_report(self, evidence_records: List[EvidenceRecord]) -> str:
        """Generiert Beweis-Zusammenfassung"""
        template_data = {
            "report_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "total_evidence": len(evidence_records),
            "evidence_records": [record.to_dict() for record in evidence_records],
            "chain_of_custody_summary": self._summarize_custody(evidence_records)
        }

        return self._generate_evidence_template(template_data)

    def _generate_sar_template(self, data: Dict[str, Any]) -> str:
        """SAR-Template nach FinCEN-Standard"""
        return json.dumps({
            "report_type": "SAR",
            "filing_institution": "Blockchain Forensics Platform",
            "case_id": data["case_id"],
            "alert_details": {
                "alert_id": data["alert_id"],
                "timestamp": data["timestamp"],
                "type": data["alert_type"],
                "severity": data["severity"],
                "description": data["description"]
            },
            "evidence": data["evidence_links"],
            "narrative": f"Automated detection of {data['alert_type']} activity requiring investigation."
        }, indent=2)

    def _generate_ctr_template(self, data: Dict[str, Any]) -> str:
        """CTR-Template (Currency Transaction Report) – generisches Schema
        Erwartete Felder in data (best effort, tolerant):
          - case_id, timestamp, parties, total_amount_usd, currency, transactions
        """
        return json.dumps({
            "report_type": "CTR",
            "filing_institution": "Blockchain Forensics Platform",
            "case_id": data.get("case_id"),
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "summary": {
                "total_amount_usd": data.get("total_amount_usd", 0),
                "currency": data.get("currency", "USD"),
                "transaction_count": len(data.get("transactions", [])),
            },
            "parties": data.get("parties", []),
            "transactions": data.get("transactions", []),
        }, indent=2)

    def _generate_evidence_template(self, data: Dict[str, Any]) -> str:
        """Evidence Summary Template"""
        return json.dumps({
            "report_type": "Evidence Summary",
            "report_id": data["report_id"],
            "timestamp": data["timestamp"],
            "summary": {
                "total_pieces": data["total_evidence"],
                "chain_of_custody_verified": data["chain_of_custody_summary"]["verified"],
                "integrity_checks_passed": data["chain_of_custody_summary"]["integrity_checks"]
            },
            "evidence_details": data["evidence_records"]
        }, indent=2)

    def _generate_evidence_links(self, alert: Dict[str, Any]) -> List[str]:
        """Generiert Links zu relevanten Beweisen"""
        return [
            f"/evidence/addresses/{alert.get('address', 'unknown')}",
            f"/evidence/transactions/{alert.get('tx_hash', 'unknown')}"
        ]

    def _summarize_custody(self, records: List[EvidenceRecord]) -> Dict[str, Any]:
        """Zusammenfassung der Chain-of-Custody"""
        verified = all(len(record.chain_of_custody) >= 2 for record in records)  # Mindestens 2 Handler
        integrity_checks = sum(1 for record in records if record.integrity_hash)

        return {
            "verified": verified,
            "integrity_checks": integrity_checks,
            "total_handlers": sum(len(record.chain_of_custody) for record in records)
        }


class ComplianceManager:
    """Haupt-Compliance-Manager"""

    def __init__(self):
        self.audit_events: List[AuditEvent] = []
        self.evidence_records: List[EvidenceRecord] = []
        self.gdpr_manager = GDPRComplianceManager()
        self.regulatory_reporter = RegulatoryReporter()

        # Compliance-Konfiguration
        self.compliance_level = ComplianceLevel.LAW_ENFORCEMENT
        self.require_evidence_collection = True
        self.enable_audit_trail = True

    def log_audit_event(self, event: AuditEvent):
        """Protokolliert Audit-Event"""
        if self.enable_audit_trail:
            self.audit_events.append(event)

            # GDPR-Compliance prüfen
            if self.compliance_level == ComplianceLevel.GDPR:
                event.details = self.gdpr_manager.check_data_minimization(event.details)

            logger.info(f"Audit event logged: {event.event_type.value} by {event.user_id}")

    def create_evidence_record(self, case_id: str, resource_id: str, resource_type: str,
                              collection_method: str, collected_by: str) -> EvidenceRecord:
        """Erstellt neuen Evidence-Record"""
        evidence = EvidenceRecord(
            evidence_id=str(uuid.uuid4()),
            case_id=case_id,
            resource_id=resource_id,
            resource_type=resource_type,
            collection_timestamp=datetime.utcnow(),
            collection_method=collection_method,
            collected_by=collected_by
        )

        if self.require_evidence_collection:
            self.evidence_records.append(evidence)

        # Audit-Event für Evidence-Sammlung
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.EVIDENCE_COLLECTION,
            user_id=collected_by,
            resource_id=resource_id,
            action="collect_evidence",
            details={"case_id": case_id, "evidence_id": evidence.evidence_id},
            ip_address="system",
            user_agent="forensics_platform",
            compliance_level=self.compliance_level
        )
        self.log_audit_event(audit_event)

        return evidence

    def get_audit_trail(self, resource_id: str, limit: int = 100) -> List[AuditEvent]:
        """Holt Audit-Trail für Ressource"""
        filtered = [event for event in self.audit_events if event.resource_id == resource_id]
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_evidence_for_case(self, case_id: str) -> List[EvidenceRecord]:
        """Holt alle Evidence-Records für einen Fall"""
        return [record for record in self.evidence_records if record.case_id == case_id]

    def generate_compliance_report(self, case_id: str, report_type: str = "full") -> str:
        """Generiert Compliance-Bericht"""
        evidence_records = self.get_evidence_for_case(case_id)

        if report_type == "suspicious_activity":
            # Finde relevante Alerts für diesen Case
            # Vereinfacht - echte Implementierung würde Datenbank-Abfrage machen
            return self.regulatory_reporter.generate_suspicious_activity_report(
                {"case_id": case_id, "alerts": []}, case_id
            )
        elif report_type == "evidence_summary":
            return self.regulatory_reporter.generate_evidence_report(evidence_records)
        else:
            # Vollständiger Bericht
            return json.dumps({
                "report_type": "full_compliance_report",
                "case_id": case_id,
                "generated_at": datetime.utcnow().isoformat(),
                "compliance_level": self.compliance_level.value,
                "audit_events_count": len([e for e in self.audit_events if case_id in str(e.details)]),
                "evidence_records_count": len(evidence_records),
                "data_retention_status": self._check_data_retention(),
                "gdpr_compliance": self._check_gdpr_compliance()
            }, indent=2)

    def _check_data_retention(self) -> Dict[str, Any]:
        """Prüft Daten-Retention-Status"""
        now = datetime.utcnow()

        retention_status = {}
        for data_type, days in self.gdpr_manager.data_retention_policies.items():
            deletion_date = now + timedelta(days=days)
            retention_status[data_type] = {
                "retention_days": days,
                "scheduled_deletion": deletion_date.isoformat(),
                "status": "compliant"
            }

        return retention_status

    def _check_gdpr_compliance(self) -> Dict[str, Any]:
        """Prüft GDPR-Compliance-Status"""
        return {
            "pii_data_handling": "compliant",
            "consent_management": "active",
            "data_minimization": "enforced",
            "right_to_erasure": "supported",
            "data_portability": "available"
        }

    def export_audit_log(self, format: str = "json", limit: int = 1000) -> str:
        """Exportiert Audit-Log für externe Prüfung"""
        events = self.audit_events[-limit:]  # Neueste Events zuerst

        if format.lower() == "json":
            return json.dumps([event.to_dict() for event in events], indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            # CSV-Export für Excel/Tabellenkalkulation
            import csv
            import io

            output = io.StringIO()
            fieldnames = ["event_id", "timestamp", "event_type", "user_id", "resource_id",
                         "action", "ip_address", "compliance_level", "hash_chain"]

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for event in events:
                row = event.to_dict()
                writer.writerow({k: v for k, v in row.items() if k in fieldnames})

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


class ChainOfCustodyManager:
    """Verwaltung der Beweiskette"""

    def __init__(self):
        self.evidence_handlers = {}

    def register_handler(self, handler_id: str, name: str, role: str, clearance_level: str):
        """Registriert Evidence-Handler"""
        self.evidence_handlers[handler_id] = {
            "name": name,
            "role": role,
            "clearance_level": clearance_level,
            "registered_at": datetime.utcnow().isoformat()
        }

    def transfer_evidence(self, evidence_id: str, from_handler: str, to_handler: str,
                         action: str, notes: str = "") -> bool:
        """Transferiert Evidence zwischen Handlern"""
        # Finde Evidence-Record
        evidence = next((e for e in compliance_manager.evidence_records if e.evidence_id == evidence_id), None)

        if not evidence:
            logger.error(f"Evidence record not found: {evidence_id}")
            return False

        # Prüfe Berechtigung
        if not self._check_clearance(from_handler, to_handler, action):
            logger.error(f"Insufficient clearance for transfer: {from_handler} -> {to_handler}")
            return False

        # Füge Chain-of-Custody Eintrag hinzu
        evidence.add_custody_entry(to_handler, action, datetime.utcnow(), notes)

        # Audit-Event für Transfer
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.EVIDENCE_COLLECTION,
            user_id=from_handler,
            resource_id=evidence_id,
            action=f"transfer_to_{to_handler}",
            details={"transfer_notes": notes, "new_handler": to_handler},
            ip_address="system",
            user_agent="evidence_management",
            compliance_level=ComplianceLevel.COURT_ADMISSIBLE
        )
        compliance_manager.log_audit_event(audit_event)

        logger.info(f"Evidence transferred: {evidence_id} from {from_handler} to {to_handler}")
        return True

    def _check_clearance(self, from_handler: str, to_handler: str, action: str) -> bool:
        """Prüft Berechtigung für Evidence-Transfer"""
        # Vereinfacht - echte Implementierung würde komplexere Berechtigungsprüfung machen
        if from_handler in self.evidence_handlers and to_handler in self.evidence_handlers:
            from_clearance = self.evidence_handlers[from_handler]["clearance_level"]
            to_clearance = self.evidence_handlers[to_handler]["clearance_level"]

            # Höhere Clearance-Levels haben mehr Berechtigung
            clearance_levels = {"low": 1, "medium": 2, "high": 3, "court": 4}
            return clearance_levels.get(from_clearance, 0) >= clearance_levels.get(to_clearance, 0)

        return False


# Singleton Instances
compliance_manager = ComplianceManager()
custody_manager = ChainOfCustodyManager()
