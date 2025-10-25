"""
Wallet Scanner Reports & Evidence Export
PDF, CSV, Signierte JSON (Chain-of-Custody)
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
import csv
import io

logger = logging.getLogger(__name__)

class WalletScannerReports:
    """Generate forensic reports for wallet scans"""
    
    def generate_csv(self, scan_result: Dict[str, Any]) -> str:
        """Generate CSV export of scan results"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Scan ID", "Wallet Type", "Scanned At", "Chain", "Address", 
            "Balance USD", "Transactions", "Risk Score", "Risk Level", 
            "Activity Level", "Labels", "Illicit Connections"
        ])
        
        # Rows
        for addr in scan_result.get("addresses", []):
            writer.writerow([
                scan_result.get("scan_id", ""),
                scan_result.get("wallet_type", ""),
                scan_result.get("scanned_at", ""),
                addr.get("chain", ""),
                addr.get("address", ""),
                addr.get("balance", {}).get("usd", 0),
                addr.get("transaction_count", 0),
                addr.get("risk_score", 0),
                addr.get("risk_level", ""),
                addr.get("activity_level", ""),
                ";".join(addr.get("labels", [])),
                len(addr.get("illicit_connections", []))
            ])
        
        return output.getvalue()
    
    def generate_signed_json(self, scan_result: Dict[str, Any], private_key_pem: Optional[str] = None) -> Dict[str, Any]:
        """Generate signed JSON for chain-of-custody (evidence)"""
        # Canonical JSON (sorted keys)
        canonical = json.dumps(scan_result, sort_keys=True, separators=(',', ':'))
        
        # SHA256 Hash
        evidence_hash = hashlib.sha256(canonical.encode()).hexdigest()
        
        # Timestamp & Metadata
        timestamp = datetime.utcnow().isoformat()
        evidence = {
            "scan_result": scan_result,
            "evidence_metadata": {
                "generated_at": timestamp,
                "sha256_hash": evidence_hash,
                "canonical_json_sha256": evidence_hash,
                "version": "1.0",
                "format": "blockchain-forensics-evidence"
            },
            "timestamp": timestamp,
            "created_at": timestamp
        }
        
        # Optional: Digital signature (würde echte PKI/eIDAS benötigen)
        if private_key_pem:
            try:
                from cryptography.hazmat.primitives import hashes, serialization
                from cryptography.hazmat.primitives.asymmetric import padding
                from cryptography.hazmat.backends import default_backend
                
                # Load private key
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode(),
                    password=None,
                    backend=default_backend()
                )
                
                # Sign hash
                signature = private_key.sign(
                    evidence_hash.encode(),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                
                evidence["evidence_metadata"]["digital_signature"] = signature.hex()
                evidence["evidence_metadata"]["signature_algorithm"] = "RSA-PSS-SHA256"
            except Exception as e:
                logger.warning(f"Digital signature failed (optional): {e}")
        
        return evidence
    
    def generate_pdf_html(self, scan_result: Dict[str, Any]) -> str:
        """Generate HTML for PDF rendering (via browser print or wkhtmltopdf)"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Wallet Scan Report - {scan_result.get('scan_id', 'N/A')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #6366f1; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f3f4f6; }}
        .risk-high {{ color: #dc2626; font-weight: bold; }}
        .risk-medium {{ color: #f59e0b; }}
        .risk-low {{ color: #10b981; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <h1>Blockchain Forensics - Wallet Scan Report</h1>
    <p><strong>Scan ID:</strong> {scan_result.get('scan_id', 'N/A')}</p>
    <p><strong>Wallet Type:</strong> {scan_result.get('wallet_type', 'N/A')}</p>
    <p><strong>Scanned At:</strong> {scan_result.get('scanned_at', 'N/A')}</p>
    <p><strong>Total Balance (USD):</strong> ${scan_result.get('total_balance_usd', 0):,.2f}</p>
    <p><strong>Total Transactions:</strong> {scan_result.get('total_transactions', 0):,}</p>
    <p><strong>Aggregate Risk Score:</strong> {scan_result.get('risk_score', 0):.2f}</p>
    
    <h2>Addresses</h2>
    <table>
        <thead>
            <tr>
                <th>Chain</th>
                <th>Address</th>
                <th>Balance (USD)</th>
                <th>Transactions</th>
                <th>Risk Level</th>
                <th>Labels</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for addr in scan_result.get("addresses", []):
            risk_class = f"risk-{addr.get('risk_level', 'low')}"
            html += f"""
            <tr>
                <td>{addr.get('chain', '')}</td>
                <td><code>{addr.get('address', '')}</code></td>
                <td>${addr.get('balance', {}).get('usd', 0):,.2f}</td>
                <td>{addr.get('transaction_count', 0):,}</td>
                <td class="{risk_class}">{addr.get('risk_level', '').upper()}</td>
                <td>{', '.join(addr.get('labels', []))}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <div class="footer">
        <p>Generated by Blockchain Forensics Platform</p>
        <p>This report is for forensic analysis purposes only.</p>
    </div>
</body>
</html>
"""
        return html


# Singleton
wallet_scanner_reports = WalletScannerReports()
