'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FileText, Download } from 'lucide-react';
import jsPDF from 'jspdf';
import QRCode from 'qrcode';
import html2canvas from 'html2canvas';

interface PDFExportProps {
  caseId: string;
  caseData: {
    title: string;
    description: string;
    addresses: string[];
    tags: string[];
    created_at: string;
    status: string;
  };
  traceData?: any;
  riskAnalysis?: any;
}

export function PDFExport({ caseId, caseData, traceData, riskAnalysis }: PDFExportProps) {
  const [isExporting, setIsExporting] = useState(false);

  const generatePDF = async () => {
    setIsExporting(true);

    try {
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      let yPosition = 20;

      // Set document properties
      pdf.setProperties({
        title: `Forensics Report ${caseId}`,
        subject: 'Blockchain Forensics Report',
        keywords: 'blockchain, forensics, trace, risk, report',
        creator: 'SIGMACODE Forensics',
        author: 'SIGMACODE',
      } as any);

      // Compute SHA-256 hash over report payload to embed provenance
      let reportHash = '';
      try {
        const payload = JSON.stringify({ caseId, caseData, traceData, riskAnalysis });
        const bytes = new TextEncoder().encode(payload);
        const digest = await crypto.subtle.digest('SHA-256', bytes);
        reportHash = Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, '0')).join('');
      } catch {}

      // Generate QR code for the report hash
      let qrDataUrl = '';
      try {
        if (reportHash) {
          qrDataUrl = await QRCode.toDataURL(reportHash, { margin: 0, scale: 2 });
        }
      } catch {}

      // Track section pages for ToC
      const sectionPages: { name: string; page: number }[] = [];

      // Header
      pdf.setFontSize(20);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Blockchain Forensics Report', pageWidth / 2, yPosition, { align: 'center' });
      
      yPosition += 10;
      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Generated: ${new Date().toLocaleString('de-DE')}`, pageWidth / 2, yPosition, {
        align: 'center',
      });

      yPosition += 15;

      // Case Information
      sectionPages.push({ name: 'Case Information', page: pdf.getNumberOfPages() });
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Case Information', 15, yPosition);
      yPosition += 8;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Title: ${caseData.title}`, 15, yPosition);
      yPosition += 6;
      pdf.text(`Case ID: ${caseId}`, 15, yPosition);
      yPosition += 6;
      pdf.text(`Status: ${caseData.status}`, 15, yPosition);
      yPosition += 6;
      pdf.text(`Created: ${new Date(caseData.created_at).toLocaleDateString('de-DE')}`, 15, yPosition);
      yPosition += 10;

      // Description
      if (caseData.description) {
        pdf.setFont('helvetica', 'bold');
        pdf.text('Description:', 15, yPosition);
        yPosition += 6;
        pdf.setFont('helvetica', 'normal');
        const descLines = pdf.splitTextToSize(caseData.description, pageWidth - 30);
        pdf.text(descLines, 15, yPosition);
        yPosition += descLines.length * 6 + 5;
      }

      // Tags
      if (caseData.tags && caseData.tags.length > 0) {
        pdf.setFont('helvetica', 'bold');
        pdf.text('Tags:', 15, yPosition);
        yPosition += 6;
        pdf.setFont('helvetica', 'normal');
        pdf.text(caseData.tags.join(', '), 15, yPosition);
        yPosition += 10;
      }

      // Addresses
      if (caseData.addresses && caseData.addresses.length > 0) {
        if (yPosition > pageHeight - 40) {
          pdf.addPage();
          yPosition = 20;
        }

        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Investigated Addresses', 15, yPosition);
        yPosition += 8;

        pdf.setFontSize(9);
        pdf.setFont('helvetica', 'normal');
        caseData.addresses.forEach((addr, idx) => {
          if (yPosition > pageHeight - 20) {
            pdf.addPage();
            yPosition = 20;
          }
          pdf.text(`${idx + 1}. ${addr}`, 15, yPosition);
          yPosition += 6;
        });
        yPosition += 5;
      }

      // Risk Analysis
      if (riskAnalysis) {
        sectionPages.push({ name: 'Risk Analysis', page: pdf.getNumberOfPages() });
        if (yPosition > pageHeight - 60) {
          pdf.addPage();
          yPosition = 20;
        }

        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Risk Analysis Summary', 15, yPosition);
        yPosition += 8;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        
        if (riskAnalysis.high_risk_count) {
          pdf.text(`High-Risk Addresses: ${riskAnalysis.high_risk_count}`, 15, yPosition);
          yPosition += 6;
        }
        
        if (riskAnalysis.sanctioned_count) {
          pdf.setTextColor(220, 38, 38); // Red
          pdf.text(`⚠ OFAC Sanctioned: ${riskAnalysis.sanctioned_count}`, 15, yPosition);
          pdf.setTextColor(0, 0, 0); // Reset to black
          yPosition += 6;
        }

        if (riskAnalysis.avg_risk_score !== undefined) {
          pdf.text(
            `Average Risk Score: ${(riskAnalysis.avg_risk_score * 100).toFixed(1)}%`,
            15,
            yPosition
          );
          yPosition += 10;
        }
      }

      // Trace Data Summary
      if (traceData) {
        sectionPages.push({ name: 'Transaction Trace Summary', page: pdf.getNumberOfPages() });
        if (yPosition > pageHeight - 60) {
          pdf.addPage();
          yPosition = 20;
        }

        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Transaction Trace Summary', 15, yPosition);
        yPosition += 8;

        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        
        if (traceData.total_nodes) {
          pdf.text(`Total Nodes: ${traceData.total_nodes}`, 15, yPosition);
          yPosition += 6;
        }
        
        if (traceData.total_edges) {
          pdf.text(`Total Transactions: ${traceData.total_edges}`, 15, yPosition);
          yPosition += 6;
        }
        
        if (traceData.max_depth_reached) {
          pdf.text(`Max Depth Reached: ${traceData.max_depth_reached}`, 15, yPosition);
          yPosition += 10;
        }
      }

      // Attempt to embed graph image if present
      try {
        const graphElement = document.querySelector('[data-graph-container]') as HTMLElement | null;
        if (graphElement) {
          sectionPages.push({ name: 'Graph Snapshot', page: pdf.getNumberOfPages() });
          const canvas = await html2canvas(graphElement, { backgroundColor: '#ffffff', scale: 2 });
          const imgData = canvas.toDataURL('image/png');
          const imgWidth = pageWidth - 30;
          const imgHeight = (canvas.height * imgWidth) / canvas.width;
          if (yPosition + imgHeight > pageHeight - 20) {
            pdf.addPage();
            yPosition = 20;
          }
          pdf.setFont('helvetica', 'bold');
          pdf.setFontSize(14);
          pdf.text('Graph Snapshot', 15, yPosition);
          yPosition += 6;
          pdf.addImage(imgData, 'PNG', 15, yPosition, imgWidth, imgHeight, undefined, 'FAST');
          yPosition += imgHeight + 8;
        }
      } catch (e) {
        // Fallback: continue without image
        console.warn('Graph snapshot embedding skipped:', e);
      }

      // Footer
      const footerY = pageHeight - 15;
      pdf.setFontSize(8);
      pdf.setTextColor(128, 128, 128);
      const footerText = 'Confidential - For Law Enforcement & Legal Use Only';
      pdf.text(footerText, pageWidth / 2, footerY, {
        align: 'center',
      });
      if (reportHash) {
        pdf.text(`Report Hash (SHA-256): ${reportHash.slice(0, 16)}…`, pageWidth / 2, footerY - 4, { align: 'center' });
        // Draw QR code on the left side of the footer
        if (qrDataUrl) {
          const qrSize = 14; // mm
          pdf.addImage(qrDataUrl, 'PNG', 15, footerY - qrSize - 2, qrSize, qrSize, undefined, 'FAST');
        }
      }

      // Add header, page numbers & watermark on each page
      const pageCount = pdf.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        pdf.setPage(i);
        // Header: Case ID (left), Title (center), Date (right)
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(9);
        pdf.setTextColor(80, 80, 80);
        const headerY = 12;
        pdf.text(`Case ID: ${caseId}`, 15, headerY);
        pdf.text('Blockchain Forensics Report', pageWidth / 2, headerY, { align: 'center' });
        pdf.text(new Date().toLocaleDateString('de-DE'), pageWidth - 15, headerY, { align: 'right' });

        // Page number
        pdf.setFontSize(8);
        pdf.setTextColor(120, 120, 120);
        pdf.text(`Seite ${i} / ${pageCount}`, pageWidth - 20, pageHeight - 10, { align: 'right' });

        // Watermark (light gray, rotated)
        pdf.setTextColor(200, 200, 200);
        pdf.setFontSize(36);
        // Save current state by adding a temporary rotation via addImage/text transformation
        // jsPDF supports text rotation via options parameter
        pdf.text('SIGMACODE', pageWidth / 2, pageHeight / 2, {
          align: 'center',
          angle: 35,
        } as any);
      }

      // Insert Table of Contents on page 1
      try {
        pdf.insertPage(1);
        pdf.setPage(1);
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(18);
        pdf.text('Inhaltsverzeichnis', pageWidth / 2, 20, { align: 'center' });
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(11);
        let tocY = 35;
        const uniq = new Map<string, number>();
        sectionPages.forEach((s) => {
          if (!uniq.has(s.name)) uniq.set(s.name, s.page + 1); // +1 because we inserted a new first page
        });
        Array.from(uniq.entries()).forEach(([name, page]) => {
          if (tocY > pageHeight - 20) {
            pdf.addPage();
            tocY = 20;
          }
          pdf.text(`${name}`, 20, tocY);
          pdf.text(`${page}`, pageWidth - 20, tocY, { align: 'right' });
          tocY += 8;
        });
      } catch {}

      // Save PDF
      pdf.save(`forensics_report_${caseId}_${Date.now()}.pdf`);
    } catch (error) {
      console.error('PDF generation failed:', error);
      alert('PDF-Export fehlgeschlagen. Bitte versuchen Sie es erneut.');
    } finally {
      setIsExporting(false);
    }
  };

  const exportGraphAsPNG = async () => {
    setIsExporting(true);

    try {
      // Find graph container
      const graphElement = document.querySelector('[data-graph-container]') as HTMLElement;
      
      if (!graphElement) {
        alert('Kein Graph gefunden zum Exportieren');
        return;
      }

      const canvas = await html2canvas(graphElement, {
        backgroundColor: '#ffffff',
        scale: 2, // Higher quality
      });

      // Convert to blob and download
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `trace_graph_${caseId}_${Date.now()}.png`;
          a.click();
          URL.revokeObjectURL(url);
        }
      });
    } catch (error) {
      console.error('PNG export failed:', error);
      alert('PNG-Export fehlgeschlagen');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        onClick={generatePDF}
        disabled={isExporting}
        variant="outline"
        className="flex items-center gap-2"
      >
        {isExporting ? (
          <>
            <span className="animate-spin">⏳</span>
            Exportiere...
          </>
        ) : (
          <>
            <FileText className="w-4 h-4" />
            PDF Export
          </>
        )}
      </Button>

      <Button
        onClick={exportGraphAsPNG}
        disabled={isExporting}
        variant="outline"
        className="flex items-center gap-2"
      >
        <Download className="w-4 h-4" />
        Graph PNG
      </Button>
    </div>
  );
}
