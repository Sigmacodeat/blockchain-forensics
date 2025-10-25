"""
Minimal Case Management Service (in-memory store + optional disk snapshots)
"""
from __future__ import annotations
from typing import Dict, List, Any
from datetime import datetime
import os
import json
from pathlib import Path
import csv
import io
import hashlib
import hmac

from app.cases.models import Case, Entity, EvidenceLink


class CaseService:
    def __init__(self) -> None:
        self._cases: Dict[str, Case] = {}
        self._entities_by_case: Dict[str, List[Entity]] = {}
        self._evidence_by_case: Dict[str, List[EvidenceLink]] = {}
        # persistence
        self._base_dir = Path(os.getenv("CASES_DIR", "data/cases"))
        self._base_dir.mkdir(parents=True, exist_ok=True)

    # ---------------
    # File IO Helpers
    # ---------------
    def _atomic_write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    def create_case(self, case_id: str, title: str, description: str, lead_investigator: str) -> Case:
        case = Case(case_id=case_id, title=title, description=description, lead_investigator=lead_investigator)
        self._cases[case.case_id] = case
        self._entities_by_case.setdefault(case.case_id, [])
        self._evidence_by_case.setdefault(case.case_id, [])
        self._write_snapshot(case.case_id)
        return case

    def add_entity(self, case_id: str, entity: Entity) -> None:
        self._entities_by_case.setdefault(case_id, []).append(entity)
        self._write_snapshot(case_id)

    def link_evidence(self, link: EvidenceLink) -> None:
        self._evidence_by_case.setdefault(link.case_id, []).append(link)
        self._write_snapshot(link.case_id)

    def export(self, case_id: str) -> Dict[str, Any]:
        case = self._cases.get(case_id)
        entities = [e.model_dump() for e in self._entities_by_case.get(case_id, [])]
        evidence = [e.model_dump() for e in self._evidence_by_case.get(case_id, [])]
        base = {
            "case": case.model_dump() if case else None,
            "entities": entities,
            "evidence": evidence,
            "format": "json",
        }
        # prev checksum from last snapshot if exists
        try:
            p = self._snapshot_path(case_id)
            if p.exists():
                prev = json.loads(p.read_text())
                prev_checksum = prev.get("checksum_sha256")
                if isinstance(prev_checksum, str) and prev_checksum:
                    base["prev_checksum_sha256"] = prev_checksum
        except Exception:
            pass
        # deterministische JSON für Hash: entferne volatile Felder (z.B. exported_at)
        payload_base = dict(base)
        payload_base.pop("exported_at", None)
        payload = json.dumps(payload_base, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        base["checksum_sha256"] = checksum
        # optional HMAC Signatur
        secret = os.getenv("CASES_SIGNING_SECRET")
        if secret:
            signature = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
            base["signature_hmac_sha256"] = signature
        return base

    def export_csv(self, case_id: str) -> Dict[str, str]:
        """Return CSV strings for entities and evidence."""
        entities = self._entities_by_case.get(case_id, [])
        evidence = self._evidence_by_case.get(case_id, [])

        # Entities CSV
        ent_buf = io.StringIO()
        ent_writer = csv.DictWriter(ent_buf, fieldnames=["address", "chain", "labels"], extrasaction="ignore")
        ent_writer.writeheader()
        for e in entities:
            ent_writer.writerow({
                "address": e.address,
                "chain": e.chain,
                "labels": json.dumps(e.labels, ensure_ascii=False),
            })
        entities_csv = ent_buf.getvalue()

        # Evidence CSV
        ev_buf = io.StringIO()
        ev_writer = csv.DictWriter(ev_buf, fieldnames=["case_id", "resource_id", "resource_type", "record_hash", "notes", "timestamp"], extrasaction="ignore")
        ev_writer.writeheader()
        for ev in evidence:
            ev_writer.writerow({
                "case_id": ev.case_id,
                "resource_id": ev.resource_id,
                "resource_type": ev.resource_type,
                "record_hash": ev.record_hash or "",
                "notes": ev.notes or "",
                "timestamp": ev.timestamp,
            })
        evidence_csv = ev_buf.getvalue()

        return {"entities_csv": entities_csv, "evidence_csv": evidence_csv, "format": "csv"}

    # -----------------
    # Internal helpers
    # -----------------
    def _snapshot_path(self, case_id: str) -> Path:
        return self._base_dir / f"{case_id}.json"

    def _write_snapshot(self, case_id: str) -> None:
        try:
            data = self.export(case_id)
            p = self._snapshot_path(case_id)
            self._atomic_write(p, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
            # optional .sha256 und .sig neben Datei
            self._atomic_write(p.with_suffix(p.suffix + ".sha256"), (data.get("checksum_sha256", "") or "").encode("utf-8"))
            sig = data.get("signature_hmac_sha256", "")
            if sig:
                self._atomic_write(p.with_suffix(p.suffix + ".sig"), sig.encode("utf-8"))
        except Exception:
            # Best-effort: Snapshot-Fehler sollen API nicht blockieren
            pass

    # Verification helpers
    def get_checksum(self, case_id: str) -> str:
        data = self.export(case_id)
        return data.get("checksum_sha256", "")

    def verify(self, case_id: str, checksum: str | None, signature: str | None = None) -> Dict[str, Any]:
        # recompute export deterministically and compare
        export = self.export(case_id)
        current_checksum = export.get("checksum_sha256", "")
        current_signature = export.get("signature_hmac_sha256")
        out = {
            "case_id": case_id,
            "checksum_sha256": current_checksum,
            "match": (checksum == current_checksum) if checksum else None,
        }
        if current_signature is not None:
            out["signature_hmac_sha256"] = current_signature
            out["signature_match"] = (signature == current_signature) if signature else None
        return out

    # Attachments
    def _attachments_dir(self, case_id: str) -> Path:
        return self._base_dir / case_id / "attachments"

    def _sanitize_filename(self, name: str) -> str:
        # prevent path traversal and remove unsafe characters
        base = os.path.basename(name or "attachment.bin")
        safe = "".join(c for c in base if c.isalnum() or c in (".", "_", "-"))
        return safe or "attachment.bin"

    def save_attachment(self, case_id: str, filename: str, content: bytes, content_type: str | None = None) -> Dict[str, Any]:
        """Persist file under case attachments, return metadata incl. sha256 and uri."""
        adir = self._attachments_dir(case_id)
        adir.mkdir(parents=True, exist_ok=True)
        # compute digest and deterministic name suffix
        sha256 = hashlib.sha256(content or b"").hexdigest()
        safe_name = self._sanitize_filename(filename)
        target = adir / f"{sha256}_{safe_name}"
        self._atomic_write(target, content or b"")
        meta = {
            "case_id": case_id,
            "filename": safe_name,
            "uri": str(target),
            "size": len(content),
            "mime": content_type or "application/octet-stream",
            "sha256": sha256,
            "stored_at": datetime.utcnow().isoformat(),
        }
        # best-effort sidecar meta json
        try:
            self._atomic_write(target.with_suffix(target.suffix + ".json"), json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"))
        except Exception:
            pass
        # snapshot update
        self._write_snapshot(case_id)
        return meta

    def link_attachment_as_evidence(self, case_id: str, meta: Dict[str, Any], notes: str = "") -> EvidenceLink:
        link = EvidenceLink(
            case_id=case_id,
            resource_id=meta.get("uri", ""),
            resource_type="attachment",
            record_hash=meta.get("sha256"),
            notes=notes,
        )
        self.link_evidence(link)
        return link


case_service = CaseService()
