'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ZoomIn, ZoomOut, Maximize2, Download } from 'lucide-react';
import html2canvas from 'html2canvas';

interface Node {
  address: string;
  risk_score?: number;
  labels?: string[];
  taint?: number;
}

interface Edge {
  from: string;
  to: string;
  value: number;
  tx_hash: string;
}

interface TraceData {
  nodes: Node[];
  edges: Edge[];
  sanctioned_addresses: string[];
}

interface TransactionGraphProps {
  data: TraceData;
  onReady?: (api: { exportPNG: () => void; fit: () => void }) => void;
}

export function TransactionGraph({ data, onReady }: TransactionGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const liveRef = useRef<HTMLDivElement>(null);

  // Precompute transformed nodes/edges (avoids repeated heavy mapping)
  const visNodeItems = useMemo(() => {
    return data.nodes.map((node) => {
        const isSanctioned = data.sanctioned_addresses.includes(node.address);
        const riskLevel = node.risk_score
          ? node.risk_score >= 0.9
            ? 'critical'
            : node.risk_score >= 0.6
            ? 'high'
            : node.risk_score >= 0.3
            ? 'medium'
            : 'low'
          : 'unknown';

        const colors = {
          critical: { background: '#ef4444', border: '#dc2626' },
          high: { background: '#f97316', border: '#ea580c' },
          medium: { background: '#eab308', border: '#ca8a04' },
          low: { background: '#22c55e', border: '#16a34a' },
          unknown: { background: '#94a3b8', border: '#64748b' },
        };

        return {
          id: node.address,
          label: `${node.address.substring(0, 8)}...`,
          title: `${node.address}\nRisk: ${
            node.risk_score ? (node.risk_score * 100).toFixed(1) : 'N/A'
          }%\nTaint: ${node.taint ? (node.taint * 100).toFixed(2) : 'N/A'}%`,
          color: isSanctioned
            ? { background: '#7f1d1d', border: '#991b1b' }
            : colors[riskLevel],
          font: { color: '#ffffff', size: 12, face: 'monospace' },
          shape: isSanctioned ? 'diamond' : 'dot',
          size: isSanctioned ? 30 : 20 + (node.taint || 0) * 20,
          borderWidth: 2,
          borderWidthSelected: 4,
        };
      });
  }, [data.nodes, data.sanctioned_addresses]);

  const visEdgeItems = useMemo(() => {
    return data.edges.map((edge, idx) => ({
      id: `${edge.from}-${edge.to}-${idx}`,
      from: edge.from,
      to: edge.to,
      label: `${edge.value.toFixed(4)}`,
      title: `TX: ${edge.tx_hash}\nValue: ${edge.value}`,
      arrows: 'to',
      color: { color: '#64748b', highlight: '#3b82f6' },
      width: Math.max(1, Math.log10(edge.value + 1)),
      font: { size: 10, align: 'middle' },
    }));
  }, [data.edges]);

  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Prepare nodes/edges for vis.js
    const visNodes = new DataSet(visNodeItems);
    const visEdges = new DataSet(visEdgeItems);

    // Network options
    const options = {
      nodes: {
        font: {
          color: '#ffffff',
        },
      },
      edges: {
        smooth: {
          enabled: true,
          type: 'cubicBezier',
          forceDirection: 'horizontal',
          roundness: 0.4,
        },
      },
      physics: {
        enabled: true,
        hierarchicalRepulsion: {
          nodeDistance: 150,
          centralGravity: 0.3,
          springLength: 200,
          springConstant: 0.05,
        },
        solver: 'hierarchicalRepulsion',
        stabilization: {
          iterations: 200,
        },
      },
      layout: {
        hierarchical: {
          enabled: true,
          direction: 'LR',
          sortMethod: 'directed',
          levelSeparation: 200,
          nodeSpacing: 150,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true,
      },
    };

    // Create network
    const network = new Network(
      containerRef.current,
      { nodes: visNodes, edges: visEdges },
      options
    );

    networkRef.current = network;

    // Expose minimal API to parent
    if (typeof onReady === 'function') {
      onReady({ exportPNG: handleExportPNG, fit: handleFit });
    }

    // Event listeners
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = data.nodes.find((n) => n.address === nodeId);
        setSelectedNode(node || null);
      } else {
        setSelectedNode(null);
      }
    });

    return () => {
      network.destroy();
    };
  }, [data]);

  // Keyboard controls for accessibility
  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!networkRef.current) return;
    if (e.key === '+') {
      e.preventDefault();
      handleZoomIn();
    } else if (e.key === '-') {
      e.preventDefault();
      handleZoomOut();
    } else if (e.key.toLowerCase() === 'f') {
      e.preventDefault();
      handleFit();
    } else if (e.key === 'Enter' && selectedNode) {
      // Announce selected node details
      if (liveRef.current) {
        liveRef.current.textContent = `Adresse ${selectedNode.address}. Risiko ${selectedNode.risk_score ? (selectedNode.risk_score * 100).toFixed(1) + ' Prozent' : 'unbekannt'}.`;
      }
    }
  };

  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 0.8 });
    }
  };

  const handleFit = () => {
    if (networkRef.current) {
      networkRef.current.fit({ animation: true });
    }
  };

  const handleExportPNG = async () => {
    if (!containerRef.current) return;
    try {
      const canvas = await html2canvas(containerRef.current, { backgroundColor: null, scale: 2 });
      const dataUrl = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = `transaction_graph_${Date.now()}.png`;
      a.click();
    } catch (e) {
      console.error('PNG Export fehlgeschlagen', e);
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={handleZoomIn} aria-label="Hineinzoomen" title="Hineinzoomen (Strg +)">
            <ZoomIn className="w-4 h-4" aria-hidden />
          </Button>
          <Button size="sm" variant="outline" onClick={handleZoomOut} aria-label="Herauszoomen" title="Herauszoomen (Strg -)">
            <ZoomOut className="w-4 h-4" aria-hidden />
          </Button>
          <Button size="sm" variant="outline" onClick={handleFit} aria-label="Ansicht einpassen" title="Ansicht einpassen">
            <Maximize2 className="w-4 h-4" aria-hidden />
          </Button>
          <Button size="sm" variant="outline" onClick={handleExportPNG} aria-label="Graph als PNG exportieren" title="PNG Export">
            <Download className="w-4 h-4 mr-2" aria-hidden />
            Export PNG
          </Button>
        </div>

        {/* Legend */}
        <div className="flex gap-3 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-red-600 border-2 border-red-700" />
            <span>Critical</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-orange-500 border-2 border-orange-600" />
            <span>High</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-yellow-500 border-2 border-yellow-600" />
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500 border-2 border-green-600" />
            <span>Low</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-900 border-2 border-red-950 rotate-45" />
            <span>Sanctioned</span>
          </div>
        </div>
      </div>

      {/* Graph Container */}
      <div
        ref={containerRef}
        className="w-full h-[600px] border rounded-lg bg-slate-50 dark:bg-slate-900"
        tabIndex={0}
        role="application"
        aria-label="Interaktiver Transaktionsgraph. Verwenden Sie Plus/Minus zum Zoomen und F zum Einpassen."
        onKeyDown={onKeyDown}
        data-graph-container
      />

      {/* Live region for announcements */}
      <div ref={liveRef} className="sr-only" aria-live="polite" />

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
          <h4 className="font-semibold mb-2">Selected Address:</h4>
          <code className="text-xs block mb-3 font-mono">{selectedNode.address}</code>
          
          <div className="grid grid-cols-3 gap-4 mb-3">
            <div>
              <p className="text-xs text-muted-foreground">Risk Score</p>
              <p className="text-lg font-bold">
                {selectedNode.risk_score
                  ? `${(selectedNode.risk_score * 100).toFixed(1)}%`
                  : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Taint</p>
              <p className="text-lg font-bold">
                {selectedNode.taint ? `${(selectedNode.taint * 100).toFixed(2)}%` : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Labels</p>
              <p className="text-lg font-bold">{selectedNode.labels?.length || 0}</p>
            </div>
          </div>

          {selectedNode.labels && selectedNode.labels.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedNode.labels.map((label, idx) => (
                <Badge key={idx} variant="secondary">
                  {label}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
