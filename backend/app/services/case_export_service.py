"""
Case Export Service
Generates reports and exports for investigation cases
"""

import logging
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.case import Case, get_case, get_case_evidence, get_case_activities

logger = logging.getLogger(__name__)


class CaseExporter:
    """Service for exporting cases to various formats"""

    def __init__(self):
        self.export_dir = Path("/tmp/case_exports")
        self.export_dir.mkdir(exist_ok=True)

    def generate_case_report(self, case: Case) -> str:
        """Generate a detailed case report in JSON format"""
        evidence_list = get_case_evidence(case.id)
        activities = get_case_activities(case.id, limit=100)

        report = {
            "case_id": case.id,
            "title": case.title,
            "description": case.description,
            "status": case.status.value,
            "priority": case.priority.value,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
            "closed_at": case.closed_at.isoformat() if case.closed_at else None,
            "assigned_to": case.assigned_to,
            "tags": case.tags,
            "category": case.category,
            "source": case.source,
            "confidentiality_level": case.confidentiality_level,
            "retention_period_years": case.retention_period_years,
            "related_addresses": case.related_addresses,
            "related_transactions": case.related_transactions,
            "related_cases": case.related_cases,
            "evidence": [
                {
                    "id": ev.id,
                    "name": ev.name,
                    "description": ev.description,
                    "evidence_type": ev.evidence_type,
                    "status": ev.status.value,
                    "collected_at": ev.collected_at.isoformat(),
                    "verified_at": ev.verified_at.isoformat() if ev.verified_at else None,
                    "hash_value": ev.hash_value,
                    "source_url": ev.source_url,
                    "collection_method": ev.collection_method,
                    "metadata": ev.metadata
                }
                for ev in evidence_list
            ],
            "activities": [
                {
                    "id": act.id,
                    "activity_type": act.activity_type,
                    "description": act.description,
                    "performed_by": act.performed_by,
                    "performed_at": act.performed_at.isoformat(),
                    "metadata": act.metadata
                }
                for act in activities
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "report_version": "1.0"
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

    def export_case_pdf(self, case_id: str) -> Optional[str]:
        """Export case as PDF (placeholder - would use reportlab or similar)"""
        case = get_case(case_id)
        if not case:
            return None

        # For now, return JSON as placeholder for PDF
        # In production, this would generate a proper PDF
        report_json = self.generate_case_report(case)

        pdf_path = self.export_dir / f"case_{case_id}_report.json"
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(report_json)

        return str(pdf_path)

    def export_case_zip(self, case_id: str) -> str:
        """Export case as ZIP bundle with all evidence and reports"""
        case = get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        zip_path = self.export_dir / f"case_{case_id}_export.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add case report
            report_content = self.generate_case_report(case)
            zipf.writestr(f"case_{case_id}_report.json", report_content)

            # Add evidence metadata
            evidence_list = get_case_evidence(case_id)
            if evidence_list:
                evidence_data = {
                    "evidence_items": [
                        {
                            "id": ev.id,
                            "name": ev.name,
                            "description": ev.description,
                            "evidence_type": ev.evidence_type,
                            "status": ev.status.value,
                            "collected_at": ev.collected_at.isoformat(),
                            "verified_at": ev.verified_at.isoformat() if ev.verified_at else None,
                            "hash_value": ev.hash_value,
                            "source_url": ev.source_url,
                            "collection_method": ev.collection_method,
                            "metadata": ev.metadata
                        }
                        for ev in evidence_list
                    ]
                }
                zipf.writestr(f"case_{case_id}_evidence.json", json.dumps(evidence_data, indent=2))

            # Add activities log
            activities = get_case_activities(case_id, limit=500)
            if activities:
                activities_data = {
                    "activities": [
                        {
                            "id": act.id,
                            "activity_type": act.activity_type,
                            "description": act.description,
                            "performed_by": act.performed_by,
                            "performed_at": act.performed_at.isoformat(),
                            "metadata": act.metadata
                        }
                        for act in activities
                    ]
                }
                zipf.writestr(f"case_{case_id}_activities.json", json.dumps(activities_data, indent=2))

            # Add export metadata
            export_metadata = {
                "exported_at": datetime.utcnow().isoformat(),
                "case_id": case_id,
                "exported_by": "system",
                "format_version": "1.0",
                "files": [
                    f"case_{case_id}_report.json",
                    f"case_{case_id}_evidence.json",
                    f"case_{case_id}_activities.json"
                ]
            }
            zipf.writestr("export_metadata.json", json.dumps(export_metadata, indent=2))

        return str(zip_path)

    def cleanup_old_exports(self, max_age_hours: int = 24) -> int:
        """Clean up old export files"""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0

        for file_path in self.export_dir.glob("*"):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete old export file {file_path}: {e}")

        logger.info(f"Cleaned up {cleaned_count} old export files")
        return cleaned_count


# Global exporter instance
case_exporter = CaseExporter()
