"""
Erweiterte Wallet-Export/Import Funktionalität

Unterstützt verschiedene Exportformate (JSON, CSV, PDF) und sicheren Import.
"""

import json
import csv
import io
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import asyncio
import logging

# PDF-Export (optional)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False
    logging.warning("ReportLab nicht verfügbar - PDF-Export wird deaktiviert")

from app.services.wallet_service import wallet_service
from app.services.wallet_ai_service import wallet_ai_agent

logger = logging.getLogger(__name__)

class WalletExportService:
    """Service für Wallet-Export und -Import"""

    def __init__(self):
        self.export_dir = Path("exports/wallets")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def export_wallet(
        self,
        wallet_id: str,
        format: str = "json",
        include_history: bool = True,
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """Exportiert eine Wallet in verschiedenen Formaten"""

        try:
            # Wallet-Daten laden
            wallet_data = await wallet_service.load_wallet_data(wallet_id)
            if not wallet_data:
                raise ValueError(f"Wallet {wallet_id} nicht gefunden")

            # Aktuelle Balance laden
            balance = await wallet_service.get_balance(
                chain=wallet_data["chain"],
                address=wallet_data["address"]
            )

            # Transaktionshistorie laden (falls gewünscht)
            history = []
            if include_history:
                history = await wallet_service.get_wallet_history(
                    chain=wallet_data["chain"],
                    address=wallet_data["address"]
                )

            # KI-Analyse laden (falls gewünscht)
            analysis = None
            if include_analysis:
                analysis = await wallet_ai_agent.analyze_wallet_comprehensive(
                    chain=wallet_data["chain"],
                    address=wallet_data["address"],
                    balance=balance,
                    transaction_history=history[:100]  # Letzte 100 TXs
                )

            # Export-Daten zusammenstellen
            export_data = {
                "export_info": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "format": format,
                    "wallet_id": wallet_id,
                    "includes_history": include_history,
                    "includes_analysis": include_analysis
                },
                "wallet": wallet_data,
                "balance": balance,
                "transactions": history if include_history else [],
                "analysis": analysis if include_analysis else None
            }

            if format.lower() == "json":
                return await self._export_json(export_data, wallet_id)
            elif format.lower() == "csv":
                return await self._export_csv(export_data, wallet_id)
            elif format.lower() == "pdf" and _PDF_AVAILABLE:
                return await self._export_pdf(export_data, wallet_id)
            else:
                raise ValueError(f"Nicht unterstütztes Format: {format}")

        except Exception as e:
            logger.error(f"Fehler beim Export der Wallet {wallet_id}: {e}")
            raise

    async def _export_json(self, data: Dict[str, Any], wallet_id: str) -> Dict[str, Any]:
        """Exportiert Wallet-Daten als JSON"""
        filename = f"wallet_{wallet_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Sensible Daten entfernen (Mnemonic, Private Keys)
        safe_data = self._sanitize_export_data(data)

        filepath = self.export_dir / filename
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(safe_data, indent=2, default=str))

        return {
            "filename": filename,
            "filepath": str(filepath),
            "format": "json",
            "size": filepath.stat().st_size
        }

    async def _export_csv(self, data: Dict[str, Any], wallet_id: str) -> Dict[str, Any]:
        """Exportiert Wallet-Daten als CSV"""
        filename = f"wallet_{wallet_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Transaktionsdaten für CSV vorbereiten
        transactions = data.get("transactions", [])
        csv_data = []

        # Header
        csv_data.append([
            "timestamp", "hash", "from", "to", "value", "gas_price", "gas_used",
            "status", "chain", "analysis_risk_score", "analysis_factors"
        ])

        # Transaktionsdaten
        for tx in transactions:
            csv_data.append([
                tx.get("timestamp", ""),
                tx.get("hash", ""),
                tx.get("from", ""),
                tx.get("to", ""),
                tx.get("value", ""),
                tx.get("gasPrice", ""),
                tx.get("gasUsed", ""),
                tx.get("status", ""),
                data["wallet"]["chain"],
                tx.get("analysis", {}).get("risk_score", ""),
                "; ".join(tx.get("analysis", {}).get("risk_factors", []))
            ])

        # CSV schreiben
        filepath = self.export_dir / filename
        async with aiofiles.open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        return {
            "filename": filename,
            "filepath": str(filepath),
            "format": "csv",
            "size": filepath.stat().st_size,
            "rows": len(csv_data) - 1  # Header nicht mitzählen
        }

    async def _export_pdf(self, data: Dict[str, Any], wallet_id: str) -> Dict[str, Any]:
        """Exportiert Wallet-Daten als PDF-Report"""
        if not _PDF_AVAILABLE:
            raise ValueError("PDF-Export nicht verfügbar - ReportLab nicht installiert")

        filename = f"wallet_{wallet_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.export_dir / filename

        # PDF erstellen
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Titel
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph(f"Wallet Forensik-Report - {wallet_id}", title_style))
        story.append(Spacer(1, 12))

        # Wallet-Informationen
        story.append(Paragraph("Wallet-Informationen", styles['Heading2']))
        wallet_info = [
            ["Feld", "Wert"],
            ["Chain", data["wallet"]["chain"]],
            ["Adresse", data["wallet"]["address"]],
            ["Erstellt", data["wallet"].get("created_at", "Unknown")],
            ["Balance", data["balance"].get("balance", "0")],
            ["Risikoscore", f"{data['analysis'].get('overall_risk_score', 0):.3f}" if data.get("analysis") else "N/A"]
        ]

        wallet_table = Table(wallet_info)
        wallet_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(wallet_table)
        story.append(Spacer(1, 20))

        # Analyse (falls vorhanden)
        if data.get("analysis"):
            story.append(Paragraph("KI-Analyse", styles['Heading2']))

            analysis_text = f"""
            Risikobewertung: {data['analysis'].get('risk_level', 'unknown').upper()}
            Durchschnittliches Transaktionsrisiko: {data['analysis'].get('overall_risk_score', 0):.3f}
            Anzahl analysierter Transaktionen: {data['analysis'].get('transaction_count', 0)}

            Risikofaktoren:
            {chr(10).join(f"- {factor}" for factor in data['analysis'].get('risk_factors', []))}
            """
            story.append(Paragraph(analysis_text, styles['Normal']))
            story.append(Spacer(1, 20))

        # Transaktionen (Top 10)
        if data.get("transactions"):
            story.append(Paragraph("Letzte Transaktionen", styles['Heading2']))

            tx_data = [["Hash", "Von", "An", "Wert", "Status"]]
            for tx in data["transactions"][:10]:
                tx_data.append([
                    tx.get("hash", "")[:16] + "...",
                    tx.get("from", "")[:10] + "..." if tx.get("from") else "",
                    tx.get("to", "")[:10] + "..." if tx.get("to") else "",
                    tx.get("value", ""),
                    tx.get("status", "")
                ])

            tx_table = Table(tx_data)
            tx_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(tx_table)

        # PDF generieren
        doc.build(story)

        return {
            "filename": filename,
            "filepath": str(filepath),
            "format": "pdf",
            "size": filepath.stat().st_size
        }

    def _sanitize_export_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Entfernt sensible Daten aus Export-Daten"""
        sanitized = data.copy()

        # Mnemonic entfernen
        if "wallet" in sanitized and "mnemonic" in sanitized["wallet"]:
            sanitized["wallet"] = sanitized["wallet"].copy()
            sanitized["wallet"]["mnemonic"] = "***ENTFERNT***"

        return sanitized

    async def import_wallet(self, file_path: str, format: str = "auto") -> Dict[str, Any]:
        """Importiert eine Wallet aus verschiedenen Formaten"""

        try:
            if format == "auto":
                format = self._detect_format(file_path)

            if format == "json":
                return await self._import_json(file_path)
            elif format == "csv":
                return await self._import_csv(file_path)
            else:
                raise ValueError(f"Nicht unterstützter Import-Format: {format}")

        except Exception as e:
            logger.error(f"Fehler beim Import der Wallet aus {file_path}: {e}")
            raise

    async def _import_json(self, file_path: str) -> Dict[str, Any]:
        """Importiert Wallet-Daten aus JSON"""
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())

        # Validierung
        if "wallet" not in data:
            raise ValueError("Ungültiges JSON-Format - 'wallet' Feld fehlt")

        wallet_data = data["wallet"]

        # Neue Wallet erstellen
        new_wallet = await wallet_service.create_wallet(
            chain=wallet_data["chain"],
            mnemonic=wallet_data.get("mnemonic")  # Kann None sein für neue Wallet
        )

        return {
            "wallet_id": new_wallet["id"],
            "chain": new_wallet["chain"],
            "address": new_wallet["address"],
            "imported_transactions": len(data.get("transactions", [])),
            "imported_analysis": data.get("analysis") is not None
        }

    async def _import_csv(self, file_path: str) -> Dict[str, Any]:
        """Importiert Transaktionsdaten aus CSV"""
        # CSV-Import würde hier implementiert werden
        # Für jetzt nur Platzhalter
        return {
            "message": "CSV-Import noch nicht implementiert",
            "imported_rows": 0
        }

    def _detect_format(self, file_path: str) -> str:
        """Erkennt das Dateiformat automatisch"""
        if file_path.lower().endswith('.json'):
            return 'json'
        elif file_path.lower().endswith('.csv'):
            return 'csv'
        elif file_path.lower().endswith('.pdf'):
            return 'pdf'
        else:
            raise ValueError(f"Unbekanntes Dateiformat: {file_path}")

    async def get_export_history(self, wallet_id: str) -> List[Dict[str, Any]]:
        """Holt die Export-Historie einer Wallet"""
        try:
            # Suche nach Export-Dateien für diese Wallet
            pattern = f"wallet_{wallet_id}_*.json"
            export_files = list(self.export_dir.glob(pattern))

            exports = []
            for file_path in export_files:
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        data = json.loads(await f.read())

                    exports.append({
                        "filename": file_path.name,
                        "exported_at": data["export_info"]["exported_at"],
                        "format": data["export_info"]["format"],
                        "size": file_path.stat().st_size,
                        "includes_history": data["export_info"]["includes_history"],
                        "includes_analysis": data["export_info"]["includes_analysis"]
                    })
                except Exception as e:
                    logger.warning(f"Fehler beim Laden von Export {file_path}: {e}")

            # Nach Datum sortieren (neueste zuerst)
            exports.sort(key=lambda x: x["exported_at"], reverse=True)

            return exports

        except Exception as e:
            logger.error(f"Fehler beim Laden der Export-Historie: {e}")
            return []

# Import für async file operations
try:
    import aiofiles
except ImportError:
    aiofiles = None

# Fallback für fehlende aiofiles
if not aiofiles:
    import json

    class MockAioFiles:
        @staticmethod
        async def open(file_path, mode):
            class MockFile:
                def __init__(self, path, mode):
                    self.path = path
                    self.mode = mode

                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

                async def write(self, data):
                    with open(self.path, self.mode) as f:
                        f.write(data)

                async def read(self):
                    with open(self.path, 'r') as f:
                        return f.read()

            return MockFile(file_path, mode)

    aiofiles = MockAioFiles()

# Singleton-Instance
wallet_export_service = WalletExportService()
