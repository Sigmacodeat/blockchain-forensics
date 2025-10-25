"""
Report Bundle Helper
====================

Kleiner Helfer zum Erstellen eines ZIP-Bundles aus:
- PDF-Bytes
- Trace/Exposure JSON
- Manifest (Signatur/Hash)

Rückgabe: (zip_bytes: bytes, filename: str)
"""
from __future__ import annotations

import io
import json
import time
import zipfile
from typing import Dict, Any, Tuple, Optional


def build_report_bundle(
    report_id: str,
    pdf_bytes: bytes,
    trace_json: Dict[str, Any],
    manifest: Dict[str, Any],
    appendix_json: Optional[Dict[str, Any]] = None,
) -> Tuple[bytes, str]:
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_id = (report_id or "report").replace(" ", "_")[:64]
    bundle_name = f"{safe_id}_{ts}.zip"

    memfile = io.BytesIO()
    with zipfile.ZipFile(memfile, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # PDF
        zf.writestr(f"{safe_id}.pdf", pdf_bytes or b"")
        # JSON (Trace)
        zf.writestr(
            f"{safe_id}.json",
            json.dumps(trace_json or {}, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        # Manifest
        zf.writestr(
            f"{safe_id}.manifest.json",
            json.dumps(manifest or {}, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        # Appendix (optional)
        if appendix_json is not None:
            zf.writestr(
                f"{safe_id}.appendix.json",
                json.dumps(appendix_json or {}, ensure_ascii=False, indent=2).encode("utf-8"),
            )

    return memfile.getvalue(), bundle_name


__all__ = ["build_report_bundle"]
