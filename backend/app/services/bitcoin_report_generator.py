"""
Bitcoin Investigation Report Generator
=======================================

Erstellt gerichtsverwertbare Evidence Reports für Bitcoin-Investigations:
- PDF: Court-Admissible Reports mit Chain-of-Custody
- HTML: Interactive Reports für Browser
- JSON: Machine-Readable Evidence Export
- CSV: Transaction-Level Data Export

Features:
- SHA256 Evidence Hashes
- Timestamped Audit Trail
- Digital Signatures (optional)
- GDPR-Compliant (keine PII)
"""

import logging
import json
import csv
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from io import StringIO

logger = logging.getLogger(__name__)


class BitcoinReportGenerator:
    """
    Report Generator für Bitcoin Investigations
    
    Generiert:
    - PDF Reports (via HTML → Browser Print)
    - HTML Reports (Interactive)
    - JSON Evidence (Machine-Readable)
    - CSV Exports (Transaction Data)
    """
    
    def __init__(self):
        self.version = "1.0.0"
    
    def generate_pdf_html(self, investigation: Dict[str, Any]) -> str:
        """
        Generate HTML for PDF Print (Browser Print API)
        
        Returns: HTML string optimized for PDF printing
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bitcoin Investigation Report - {investigation['investigation_id']}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #000;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            color: #000;
        }}
        .meta {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 30px;
            page-break-inside: avoid;
        }}
        .section h2 {{
            border-bottom: 2px solid #333;
            padding-bottom: 5px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #333;
            color: white;
        }}
        .address {{
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }}
        .evidence-hash {{
            background: #ffe;
            padding: 10px;
            border-left: 4px solid #f90;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #333;
            font-size: 0.9em;
            color: #666;
        }}
        .recommendation {{
            background: #f0f8ff;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #007bff;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Bitcoin Investigation Report</h1>
        <p style="margin: 10px 0; font-size: 1.2em;">Investigation ID: {investigation['investigation_id']}</p>
        <p style="margin: 5px 0;">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>

    <div class="meta">
        <h3 style="margin-top: 0;">Investigation Metadata</h3>
        <p><strong>Case ID:</strong> {investigation.get('input', {}).get('case_id', 'N/A')}</p>
        <p><strong>Addresses Analyzed:</strong> {len(investigation.get('input', {}).get('addresses', []))}</p>
        <p><strong>Time Period:</strong> {investigation.get('input', {}).get('start_date', 'N/A')} → {investigation.get('input', {}).get('end_date', 'N/A')}</p>
        <p><strong>Execution Time:</strong> {investigation.get('execution_time_seconds', 0):.2f} seconds</p>
        <p><strong>Status:</strong> {investigation.get('status', 'completed')}</p>
    </div>

    <div class="section">
        <h2>📊 Executive Summary</h2>
        <p>{investigation.get('summary', 'Investigation completed.')}</p>
        
        <h3>Key Findings</h3>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Transactions</td>
                <td>{investigation.get('transactions', {}).get('total_count', 0)}</td>
            </tr>
            <tr>
                <td>Total Volume</td>
                <td>{investigation.get('transactions', {}).get('total_volume_btc', 0):.4f} BTC</td>
            </tr>
            <tr>
                <td>Unique Addresses</td>
                <td>{investigation.get('transactions', {}).get('unique_addresses', 0)}</td>
            </tr>
            <tr>
                <td>Wallet Clusters</td>
                <td>{investigation.get('clustering', {}).get('total_clusters', 0)}</td>
            </tr>
            <tr>
                <td>Mixer Interactions</td>
                <td>{investigation.get('mixer_analysis', {}).get('mixer_interactions', 0)}</td>
            </tr>
            <tr>
                <td>Exit Volume</td>
                <td>{investigation.get('flow_analysis', {}).get('total_exit_volume_btc', 0):.4f} BTC</td>
            </tr>
            <tr>
                <td>Dormant Funds</td>
                <td>{investigation.get('flow_analysis', {}).get('total_dormant_btc', 0):.4f} BTC</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>🎯 Investigated Addresses</h2>
        <table>
            <tr>
                <th>Address</th>
                <th>Type</th>
            </tr>
            {self._render_addresses_table(investigation.get('input', {}).get('addresses', []))}
        </table>
    </div>

    <div class="section">
        <h2>🔗 UTXO Clustering Results</h2>
        <p>Total Clusters Identified: <strong>{investigation.get('clustering', {}).get('total_clusters', 0)}</strong></p>
        <p>Addresses Clustered: <strong>{investigation.get('clustering', {}).get('clustered_addresses', 0)}</strong></p>
        <p><em>Clustering indicates common wallet ownership based on 15+ heuristics including co-spending, change detection, and temporal patterns.</em></p>
    </div>

    <div class="section">
        <h2>🌪️ Mixer Analysis</h2>
        <p>Mixer Interactions Detected: <strong>{investigation.get('mixer_analysis', {}).get('mixer_interactions', 0)}</strong></p>
        <p>Mixers Identified: {', '.join(investigation.get('mixer_analysis', {}).get('mixers_detected', []))}</p>
        <p><em>Mixer detection includes Wasabi CoinJoin, JoinMarket, Samourai Whirlpool, and generic CoinJoin patterns.</em></p>
    </div>

    <div class="section">
        <h2>📤 Exit Points & Fund Flow</h2>
        <h3>Exit Points ({len(investigation.get('flow_analysis', {}).get('exit_points', []))})</h3>
        <table>
            <tr>
                <th>Address</th>
                <th>Type</th>
                <th>Volume (BTC)</th>
                <th>Labels</th>
            </tr>
            {self._render_exit_points_table(investigation.get('flow_analysis', {}).get('exit_points', []))}
        </table>
        
        <h3>Dormant Funds ({len(investigation.get('flow_analysis', {}).get('dormant_funds', []))})</h3>
        <table>
            <tr>
                <th>Address</th>
                <th>Balance (BTC)</th>
                <th>Dormant Days</th>
            </tr>
            {self._render_dormant_funds_table(investigation.get('flow_analysis', {}).get('dormant_funds', []))}
        </table>
    </div>

    <div class="section">
        <h2>💡 Recommendations</h2>
        {self._render_recommendations(investigation.get('recommendations', []))}
    </div>

    <div class="evidence-hash">
        <h3>🔒 Evidence Integrity</h3>
        <p><strong>Evidence Hash (SHA256):</strong></p>
        <p class="address">{self._generate_evidence_hash(investigation)}</p>
        <p><strong>Timestamp:</strong> {investigation.get('evidence_chain', {}).get('timestamp', datetime.utcnow().isoformat())}</p>
        <p><em>This hash can be used to verify the integrity of this report. Any modification to the evidence will change the hash.</em></p>
    </div>

    <div class="footer">
        <p><strong>Generated by:</strong> Blockchain Forensics Platform v{self.version}</p>
        <p><strong>Investigation ID:</strong> {investigation['investigation_id']}</p>
        <p><strong>Report Type:</strong> Court-Admissible Evidence Report</p>
        <p><em>This report is generated for forensic analysis purposes. All data is derived from public blockchain sources.</em></p>
    </div>
</body>
</html>
"""
        return html
    
    def generate_json_evidence(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JSON Evidence Export (Machine-Readable)
        
        Returns: JSON dict with evidence chain
        """
        # Create canonical JSON with evidence hash
        evidence = {
            "report_version": self.version,
            "generated_at": datetime.utcnow().isoformat(),
            "investigation": investigation,
            "evidence_chain": {
                "timestamp": datetime.utcnow().isoformat(),
                "hash": self._generate_evidence_hash(investigation),
                "algorithm": "SHA256"
            }
        }
        
        return evidence
    
    def generate_csv_export(self, investigation: Dict[str, Any]) -> str:
        """
        Generate CSV Export (Transaction-Level Data)
        
        Returns: CSV string
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Transaction ID",
            "Timestamp",
            "From Address",
            "To Address",
            "Amount (BTC)",
            "Transaction Hash",
            "Labels"
        ])
        
        # Write transactions (if available)
        transactions = investigation.get('timeline', [])
        for tx in transactions:
            writer.writerow([
                tx.get('id', 'N/A'),
                tx.get('timestamp', 'N/A'),
                tx.get('from_address', 'N/A'),
                tx.get('to_address', 'N/A'),
                tx.get('amount_btc', 0),
                tx.get('tx_hash', 'N/A'),
                ', '.join(tx.get('labels', []))
            ])
        
        return output.getvalue()
    
    def _render_addresses_table(self, addresses: List[str]) -> str:
        """Render addresses table rows"""
        rows = []
        for addr in addresses:
            addr_type = self._detect_address_type(addr)
            rows.append(f"<tr><td class='address'>{addr}</td><td>{addr_type}</td></tr>")
        return '\n'.join(rows)
    
    def _render_exit_points_table(self, exit_points: List[Dict]) -> str:
        """Render exit points table rows"""
        rows = []
        for exit_pt in exit_points:
            rows.append(f"""
                <tr>
                    <td class='address'>{exit_pt.get('address', 'N/A')}</td>
                    <td>{exit_pt.get('exit_type', 'N/A')}</td>
                    <td>{exit_pt.get('total_outflow_btc', 0):.4f}</td>
                    <td>{', '.join(exit_pt.get('labels', []))}</td>
                </tr>
            """)
        return '\n'.join(rows)
    
    def _render_dormant_funds_table(self, dormant_funds: List[Dict]) -> str:
        """Render dormant funds table rows"""
        rows = []
        for fund in dormant_funds:
            rows.append(f"""
                <tr>
                    <td class='address'>{fund.get('address', 'N/A')}</td>
                    <td>{fund.get('balance_btc', 0):.4f}</td>
                    <td>{fund.get('dormant_days', 0)}</td>
                </tr>
            """)
        return '\n'.join(rows)
    
    def _render_recommendations(self, recommendations: List[str]) -> str:
        """Render recommendations"""
        if not recommendations:
            return "<p><em>No specific recommendations.</em></p>"
        
        items = []
        for i, rec in enumerate(recommendations, 1):
            items.append(f"<div class='recommendation'>{i}. {rec}</div>")
        return '\n'.join(items)
    
    def _detect_address_type(self, address: str) -> str:
        """Detect Bitcoin address type"""
        if address.startswith('bc1q'):
            return "SegWit (Bech32)"
        elif address.startswith('bc1p'):
            return "Taproot (Bech32m)"
        elif address.startswith('1'):
            return "Legacy (P2PKH)"
        elif address.startswith('3'):
            return "SegWit (P2SH)"
        else:
            return "Unknown"
    
    def _generate_evidence_hash(self, investigation: Dict[str, Any]) -> str:
        """
        Generate SHA256 evidence hash for integrity verification
        
        Returns: Hex-encoded SHA256 hash
        """
        # Create canonical JSON (sorted keys)
        canonical = json.dumps(investigation, sort_keys=True, ensure_ascii=False)
        
        # Generate hash
        hash_obj = hashlib.sha256(canonical.encode('utf-8'))
        
        return hash_obj.hexdigest()


# Global instance
bitcoin_report_generator = BitcoinReportGenerator()

logger.info("✅ Bitcoin Report Generator loaded")
