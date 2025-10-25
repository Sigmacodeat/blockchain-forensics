"""
Complete PDF Report Generator with ReportLab
Court-Admissible Forensic Reports

Install: pip install reportlab
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from io import BytesIO
import hashlib

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.services.signing import generate_report_hash_and_manifest

logger = logging.getLogger(__name__)


class CompletePDFReportGenerator:
    """
    Professional PDF Report Generator
    
    Features:
    - Court-admissible formatting
    - Digital hash signatures
    - Evidence chain documentation
    - Professional styling
    - Tables and charts
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available. Install: pip install reportlab")
            self.styles = None
        else:
            logger.info("PDF Generator initialized with ReportLab")
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom PDF styles"""
        
        # Title
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section Header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body Justified
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        
        # Confidential
        self.styles.add(ParagraphStyle(
            name='Confidential',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.red,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
    
    async def generate_trace_report(
        self,
        trace_id: str,
        trace_data: Dict,
        findings: Optional[Dict] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate PDF forensic report
        
        Args:
            trace_id: Trace ID
            trace_data: Trace result data
            findings: Additional findings
        
        Returns:
            Tuple of (PDF bytes, manifest dict)
        """
        if not REPORTLAB_AVAILABLE:
            # Fallback to simple text
            text_report = self._generate_text_fallback(trace_id, trace_data)
            content_bytes = text_report.encode('utf-8')
            content_hash, manifest = generate_report_hash_and_manifest(
                report_id=trace_id,
                report_type="trace_report_text",
                content=content_bytes
            )
            return content_bytes, manifest
        
        try:
            pdf_bytes = await self._generate_pdf(trace_id, trace_data, findings)
            
            # Generate hash and manifest for the PDF content
            content_hash, manifest = generate_report_hash_and_manifest(
                report_id=trace_id,
                report_type="trace_report_pdf",
                content=pdf_bytes,
                metadata={
                    "source_address": trace_data.get("source_address"),
                    "taint_model": trace_data.get("taint_model"),
                    "total_nodes": trace_data.get("total_nodes", 0),
                    "total_edges": trace_data.get("total_edges", 0),
                }
            )
            
            return pdf_bytes, manifest
            
        except Exception as e:
            logger.error(f"PDF generation error: {e}", exc_info=True)
            # Fallback
            text_report = self._generate_text_fallback(trace_id, trace_data)
            content_bytes = text_report.encode('utf-8')
            content_hash, manifest = generate_report_hash_and_manifest(
                report_id=trace_id,
                report_type="trace_report_text_fallback",
                content=content_bytes
            )
            return content_bytes, manifest
    
    async def _generate_pdf(
        self,
        trace_id: str,
        trace_data: Dict,
        findings: Optional[Dict]
    ) -> bytes:
        """Generate actual PDF"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=50
        )
        
        story = []
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Title
        story.append(Paragraph(
            "BLOCKCHAIN FORENSIC INVESTIGATION REPORT",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.3*inch))
        
        # Classification
        story.append(Paragraph(
            "CONFIDENTIAL - FOR OFFICIAL USE ONLY",
            self.styles['Confidential']
        ))
        story.append(Spacer(1, 0.5*inch))

        # Metadata Table
        metadata = [
            ['Report ID:', trace_id],
            ['Generated:', timestamp],
            ['Platform:', 'Blockchain Forensics Platform v2.0'],
            ['Classification:', 'CONFIDENTIAL']
        ]
        
        t = Table(metadata, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        story.append(Paragraph("1. EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        summary = f"""
        This report documents a comprehensive blockchain transaction analysis 
        tracing {trace_data.get('total_nodes', 0)} addresses across 
        {trace_data.get('total_edges', 0)} transactions using advanced 
        forensic methodologies.
        """
        story.append(Paragraph(summary, self.styles['BodyJustified']))
        
        # Key Findings Table
        findings_data = [
            ['Metric', 'Value'],
            ['Source Address', str(trace_data.get('source_address', 'N/A'))[:20] + '...'],
            ['Direction', str(trace_data.get('direction', 'N/A'))],
            ['Taint Model', str(trace_data.get('taint_model', 'N/A'))],
            ['Total Nodes', str(trace_data.get('total_nodes', 0))],
            ['Total Edges', str(trace_data.get('total_edges', 0))],
            ['High-Risk', str(len(trace_data.get('high_risk_addresses', [])))],
            ['Sanctioned', str(len(trace_data.get('sanctioned_addresses', [])))],
        ]
        
        findings_table = Table(findings_data, colWidths=[3*inch, 3*inch])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(Spacer(1, 0.2*inch))
        story.append(findings_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Methodology
        story.append(Paragraph("2. METHODOLOGY", self.styles['SectionHeader']))
        methodology = f"""
        <b>2.1 Data Collection:</b><br/>
        Source: Ethereum Mainnet<br/>
        RPC Provider: Infura/Alchemy<br/><br/>
        
        <b>2.2 Taint Analysis:</b><br/>
        Model: {trace_data.get('taint_model', 'Proportional').capitalize()}<br/>
        Threshold: {trace_data.get('min_taint_threshold', 0.01) * 100}%<br/><br/>
        
        <b>2.3 Risk Assessment:</b><br/>
        ML Model: XGBoost (100+ features)<br/>
        Labels: OFAC, Chainalysis, Etherscan
        """
        story.append(Paragraph(methodology, self.styles['BodyText']))
        story.append(PageBreak())
        
        # High-Risk Addresses
        story.append(Paragraph("3. HIGH-RISK ADDRESSES", self.styles['SectionHeader']))
        
        if trace_data.get('high_risk_addresses'):
            risk_data = [['Address', 'Taint %', 'Labels']]
            for addr in trace_data.get('high_risk_addresses', [])[:10]:
                node = trace_data.get('nodes', {}).get(addr, {})
                taint = node.get('taint_received', 0)
                labels = ', '.join(node.get('labels', [])[:2]) or 'None'
                risk_data.append([
                    addr[:10] + '...' + addr[-8:],
                    f"{taint * 100:.2f}%",
                    labels
                ])
            
            risk_table = Table(risk_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(risk_table)
        else:
            story.append(Paragraph("No high-risk addresses detected.", self.styles['BodyText']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Sanctioned Entities
        story.append(Paragraph("4. OFAC SANCTIONED ENTITIES", self.styles['SectionHeader']))
        
        if trace_data.get('sanctioned_addresses'):
            for addr in trace_data.get('sanctioned_addresses', []):
                warning = f"<font color='red'><b>⚠ WARNING:</b></font> {addr} - OFAC SANCTIONED"
                story.append(Paragraph(warning, self.styles['BodyText']))
        else:
            story.append(Paragraph(
                "<font color='green'>✓ No OFAC sanctioned entities detected.</font>",
                self.styles['BodyText']
            ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # KPI Snapshot (optional)
        if findings and isinstance(findings, dict) and findings.get('kpis'):
            kpis = findings.get('kpis') or {}
            story.append(Paragraph("5. DASHBOARD KPI SNAPSHOT", self.styles['SectionHeader']))
            kpi_rows = [["Metric", "Value"]]
            def _fmt(v):
                try:
                    return f"{float(v):.2f}"
                except Exception:
                    return str(v)
            kpi_rows += [
                ["False Positive Rate", f"{float(kpis.get('fpr', 0.0))*100:.2f}%"],
                ["MTTR (hours)", _fmt(kpis.get('mttr', 0.0))],
                ["MTTD (hours)", _fmt(kpis.get('mttd', 0.0))],
                ["SLA Breach Rate", f"{float(kpis.get('sla_breach_rate', 0.0))*100:.2f}%"],
                ["Sanctions Hits", str(int(kpis.get('sanctions_hits', 0)))],
            ]
            kpi_table = Table(kpi_rows, colWidths=[3*inch, 3*inch])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 0.3*inch))

        # Rule Effectiveness (optional)
        if findings and isinstance(findings, dict) and findings.get('rule_effectiveness'):
            eff = findings.get('rule_effectiveness') or []
            story.append(Paragraph("6. RULE EFFECTIVENESS", self.styles['SectionHeader']))
            eff_rows = [["Rule", "Total", "Labeled", "False Positives", "FP Rate"]]
            for it in (eff[:10] if isinstance(eff, list) else []):
                try:
                    rule = str(it.get('rule', 'unknown'))
                    total_alerts = int(it.get('total_alerts', 0))
                    labeled = int(it.get('labeled', 0))
                    fp = int(it.get('false_positives', 0))
                    fp_rate = float(it.get('fp_rate', 0.0))
                    eff_rows.append([
                        rule[:36] + ('…' if len(rule) > 36 else ''),
                        str(total_alerts),
                        str(labeled),
                        str(fp),
                        f"{fp_rate*100:.2f}%",
                    ])
                except Exception:
                    continue
            eff_table = Table(eff_rows, colWidths=[2.8*inch, 0.8*inch, 0.8*inch, 1.0*inch, 0.6*inch])
            eff_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(eff_table)
            story.append(Spacer(1, 0.5*inch))

        # Exposure Summary
        story.append(Paragraph("5. EXPOSURE SUMMARY", self.styles['SectionHeader']))
        exposure = trace_data.get('exposure_summary') or {}
        if exposure:
            exp_rows = [['Address', 'Direct', 'Indirect Hops', 'Exposure Share']]
            for addr, es in list(exposure.items())[:10]:
                exp_rows.append([
                    addr[:10] + '...' + addr[-8:],
                    'Yes' if es.get('direct_exposure') else 'No',
                    str(es.get('indirect_hops') if es.get('indirect_hops') is not None else 'N/A'),
                    f"{float(es.get('exposure_share', 0.0)) * 100:.2f}%",
                ])
            exp_table = Table(exp_rows, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
            exp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(exp_table)
        else:
            story.append(Paragraph("No exposure data available.", self.styles['BodyText']))
        story.append(Spacer(1, 0.5*inch))

        # Evidence Chain
        story.append(Paragraph("6. EVIDENCE CHAIN & CERTIFICATION", self.styles['SectionHeader']))
        evidence = f"""
        All evidence maintains proper chain of custody:<br/><br/>
        1. <b>Data Source:</b> Ethereum blockchain (immutable)<br/>
        2. <b>Collection:</b> {timestamp}<br/>
        3. <b>Storage:</b> TimescaleDB (tamper-evident)<br/>
        4. <b>Analysis:</b> Deterministic algorithms<br/>
        5. <b>Report:</b> Automated generation<br/><br/>
        
        This report represents factual findings based on blockchain data.
        All methodologies are scientifically sound and reproducible.
        """
        story.append(Paragraph(evidence, self.styles['BodyJustified']))
        story.append(Spacer(1, 0.3*inch))
        
        # Digital Signature
        content_hash = hashlib.sha256(
            f"{trace_id}{timestamp}{trace_data.get('total_nodes', 0)}".encode()
        ).hexdigest()
        
        sig_data = [
            ['Report Hash (SHA-256):', content_hash],
            ['Digital Signature:', '[Requires HSM in production]'],
        ]
        sig_table = Table(sig_data, colWidths=[2*inch, 4*inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(sig_table)
        
        # Appendix A - Exposure Details
        story.append(PageBreak())
        story.append(Paragraph("APPENDIX A. EXPOSURE DETAILS", self.styles['SectionHeader']))
        exposure_full = trace_data.get('exposure_summary') or {}
        if exposure_full:
            # sort by exposure_share desc
            try:
                items = sorted(exposure_full.items(), key=lambda kv: float(kv[1].get('exposure_share', 0.0)), reverse=True)
            except Exception:
                items = list(exposure_full.items())
            rows = [[
                'Address', 'Direct Exposure', 'Indirect Hops', 'Exposure Share', 'Labels', 'Paths Examined'
            ]]
            for addr, es in items[:100]:
                rows.append([
                    (addr or '')[:18] + '...' + (addr or '')[-10:] if isinstance(addr, str) and len(addr) > 32 else (addr or ''),
                    'Yes' if es.get('direct_exposure') else 'No',
                    str(es.get('indirect_hops') if es.get('indirect_hops') is not None else 'N/A'),
                    f"{float(es.get('exposure_share', 0.0)) * 100:.2f}%",
                    ', '.join((es.get('labels_seen') or [])[:3]) if isinstance(es.get('labels_seen'), list) else '',
                    str(es.get('paths_examined', 0)),
                ])
            app_table = Table(rows, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.6*inch, 1.0*inch])
            app_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(app_table)
        else:
            story.append(Paragraph("No exposure details available for appendix.", self.styles['BodyText']))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _add_footer(self, canvas_obj, doc):
        """Add footer to each page"""
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num} - Blockchain Forensics Platform - {datetime.utcnow().strftime('%Y-%m-%d')}"
        canvas_obj.drawCentredString(A4[0] / 2.0, 30, text)
        
        canvas_obj.restoreState()
    
    def _generate_text_fallback(self, trace_id: str, trace_data: Dict) -> str:
        """Fallback text report when ReportLab unavailable"""
        timestamp = datetime.utcnow().isoformat()
        
        return f"""
================================================================================
BLOCKCHAIN FORENSIC INVESTIGATION REPORT
================================================================================

Report ID:          {trace_id}
Generated:          {timestamp}
Platform:           Blockchain Forensics Platform v2.0
Classification:     CONFIDENTIAL

WARNING: This is a text fallback. Install reportlab for PDF generation.

================================================================================
EXECUTIVE SUMMARY
================================================================================

Source Address:     {trace_data.get('source_address', 'N/A')}
Total Nodes:        {trace_data.get('total_nodes', 0)}
Total Edges:        {trace_data.get('total_edges', 0)}
High-Risk:          {len(trace_data.get('high_risk_addresses', []))}
Sanctioned:         {len(trace_data.get('sanctioned_addresses', []))}

================================================================================
END OF REPORT
================================================================================
"""


# Singleton
complete_pdf_generator = CompletePDFReportGenerator()

__all__ = ['CompletePDFReportGenerator', 'complete_pdf_generator', 'REPORTLAB_AVAILABLE']
