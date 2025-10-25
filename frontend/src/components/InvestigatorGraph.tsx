import React, { useRef, useState, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d';
import { formatAddress } from '@/lib/utils';

interface GraphNode {
  id: string;
  address: string;
  chain: string;
  taint_score: number;
  risk_level: string;
  labels: string[];
  tx_count: number;
  balance: number;
  first_seen: string;
  last_seen: string;
}

interface GraphEdge {
  source: string;
  target: string;
  tx_hash: string;
  value: number;
  timestamp: string;
  event_type: string;
  bridge?: string;
}

interface InvestigatorGraphProps {
  nodes: Record<string, GraphNode>;
  links: GraphEdge[];
  selectedAddress?: string;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  onReady?: (api: {
    zoomIn: () => void;
    zoomOut: () => void;
    zoomToFit: () => void;
    centerOn: (address?: string) => void;
  }) => void;
  highlightPath?: string[];
  disableAutoFit?: boolean;
}

export default function InvestigatorGraph({
  nodes,
  links,
  selectedAddress,
  onNodeClick,
  onEdgeClick,
  onReady,
  highlightPath,
  disableAutoFit
}: InvestigatorGraphProps) {
  const graphRef = useRef<any>();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const isDarkRef = useRef(false);
  useEffect(() => {
    const update = () => {
      isDarkRef.current = document.documentElement.classList.contains('dark');
    };
    update();
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // Convert data to graph format
  const graphData = {
    nodes: Object.values(nodes).map(node => ({
      id: node.address,
      address: node.address,
      chain: node.chain,
      taint: node.taint_score,
      risk_level: node.risk_level,
      labels: node.labels,
      tx_count: node.tx_count,
      balance: node.balance,
      isSelected: node.address === selectedAddress,
      isSource: node.address === selectedAddress,
    })),
    links: links.map(link => ({
      source: link.source,
      target: link.target,
      value: link.value,
      tx_hash: link.tx_hash,
      timestamp: link.timestamp,
      event_type: link.event_type,
      bridge: link.bridge,
    }))
  };

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      const container = graphRef.current?.container;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: container.clientHeight
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Expose control API and auto-zoom to fit when data changes
  useEffect(() => {
    if (!graphRef.current) return;
    const api = {
      zoomIn: () => {
        const curZoom = graphRef.current.zoom();
        graphRef.current.zoom(curZoom * 1.2, 300);
      },
      zoomOut: () => {
        const curZoom = graphRef.current.zoom();
        graphRef.current.zoom(curZoom / 1.2, 300);
      },
      zoomToFit: () => graphRef.current.zoomToFit(500, 60),
      centerOn: (address?: string) => {
        if (!address) {
          graphRef.current.zoomToFit(500, 60);
          return;
        }
        const g = graphRef.current.graphData();
        const n = g?.nodes?.find((nd: any) => nd.id === address);
        if (n && typeof n.x === 'number' && typeof n.y === 'number') {
          graphRef.current.centerAt(n.x, n.y, 400);
          graphRef.current.zoom(1.2, 300);
        } else {
          graphRef.current.zoomToFit(500, 60);
        }
      }
    };
    onReady?.(api);

    if (!disableAutoFit && graphData.nodes.length > 0) {
      setTimeout(() => {
        graphRef.current.zoomToFit(400, 50);
      }, 120);
    }
  }, [graphData.nodes.length, onReady, disableAutoFit]);

  const getNodeColor = (node: any) => {
    if (highlightPath && highlightPath.includes(node.address)) return '#2563eb'; // blue-600 for path
    if (node.isSelected || node.isSource) return '#0284c7'; // primary-600
    if (node.risk_level === 'CRITICAL') return '#dc2626'; // red-600
    if (node.risk_level === 'HIGH') return '#ea580c'; // orange-600
    if (node.risk_level === 'MEDIUM') return '#f59e0b'; // yellow-600
    return '#6b7280'; // gray-500
  };

  const getNodeSize = (node: any) => {
    const baseSize = 4;
    if (node.isSelected || node.isSource) return baseSize + 4;
    if (node.risk_level === 'CRITICAL' || node.risk_level === 'HIGH') return baseSize + 2;
    return baseSize;
  };

  const getLinkColor = (link: any) => {
    if (highlightPath && Array.isArray(highlightPath)) {
      for (let i = 0; i < highlightPath.length - 1; i++) {
        const a = highlightPath[i];
        const b = highlightPath[i + 1];
        if (
          (link.source?.id === a && link.target?.id === b) ||
          (link.source === a && link.target === b)
        ) {
          return '#2563eb'; // blue for highlighted path edges
        }
      }
    }
    if (link.bridge) return '#06b6d4'; // cyan-500 for bridges
    if (link.event_type === 'large_transfer') return '#f59e0b'; // yellow for large transfers
    return '#cbd5e1'; // gray-300 for normal
  };

  const getLinkWidth = (link: any) => {
    const base = Math.max(1, Math.log(link.value + 1));
    return link.bridge ? base + 2 : base;
  };

  return (
    <div className="relative w-full h-full bg-card rounded-lg overflow-hidden border border-border">
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        nodeLabel={(node: any) => {
          const dark = isDarkRef.current;
          const bg = dark ? '#0f172a' : '#ffffff';
          const fg = dark ? '#e2e8f0' : '#111827';
          const sub = dark ? '#94a3b8' : '#666666';
          const shadow = dark ? 'rgba(0,0,0,0.5)' : 'rgba(0,0,0,0.15)';
          const border = dark ? 'rgba(148,163,184,0.25)' : 'rgba(100,116,139,0.25)';
          return `
          <div style="background: ${bg}; color:${fg}; padding: 12px; border-radius: 6px; box-shadow: 0 4px 12px ${shadow}; max-width: 260px; border: 1px solid ${border};">
            <div style="font-weight: 600; margin-bottom: 6px; color: ${getNodeColor(node)};">
              ${formatAddress(node.address, 8)}
            </div>
            <div style="font-size: 12px; color: ${sub}; line-height: 1.5;">
              <div>Risk: ${node.risk_level} (${(node.taint * 100).toFixed(1)}% taint)</div>
              <div>Chain: ${node.chain}</div>
              <div>Tx Count: ${node.tx_count}</div>
              ${node.labels?.length > 0 ? `<div>Labels: ${node.labels.join(', ')}</div>` : ''}
            </div>
          </div>
        `;
        }}
        linkLabel={(link: any) => {
          const dark = isDarkRef.current;
          const bg = dark ? '#0f172a' : '#ffffff';
          const fg = dark ? '#e2e8f0' : '#111827';
          const shadow = dark ? 'rgba(0,0,0,0.45)' : 'rgba(0,0,0,0.15)';
          const border = dark ? 'rgba(148,163,184,0.25)' : 'rgba(100,116,139,0.25)';
          return `
          <div style="background: ${bg}; color:${fg}; padding: 8px; border-radius: 4px; box-shadow: 0 2px 8px ${shadow}; border: 1px solid ${border};">
            <div style="font-size: 12px;">
              <div>Tx: ${link.tx_hash ? formatAddress(link.tx_hash, 8) : 'N/A'}</div>
              <div>Value: ${link.value?.toFixed(4)} ETH</div>
              <div>Type: ${link.event_type?.replace('_', ' ') || 'unknown'}</div>
              ${link.bridge ? `<div>Bridge: ${link.bridge}</div>` : ''}
            </div>
          </div>
        `;
        }}
        nodeColor={getNodeColor}
        nodeVal={getNodeSize}
        linkColor={getLinkColor}
        linkWidth={getLinkWidth}
        linkLineDash={(link: any) => link.bridge ? [8, 4] : null}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.25}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        cooldownTicks={100}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        onNodeClick={(node: any) => onNodeClick?.(node)}
        onLinkClick={(link: any) => onEdgeClick?.(link)}
        nodeRelSize={4}
        minZoom={0.1}
        maxZoom={10}
      />

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-card text-foreground p-4 rounded-lg shadow-lg border border-border dark:bg-slate-800 dark:text-slate-100">
        <h4 className="font-semibold text-sm mb-3">Legend</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-primary-600"></div>
            <span>Selected/Source</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-600"></div>
            <span>Critical Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-600"></div>
            <span>High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-600"></div>
            <span>Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-500"></div>
            <span>Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-cyan-500" style={{borderBottom: '2px dashed #06b6d4', width: '1rem'}}></div>
            <span>Bridge Connection</span>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="absolute bottom-4 left-4 bg-card text-foreground p-3 rounded-lg shadow-lg border border-border dark:bg-slate-800 dark:text-slate-100">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>🖱️ Drag nodes</span>
          <span>•</span>
          <span>Scroll to zoom</span>
          <span>•</span>
          <span>Click nodes for details</span>
        </div>
      </div>

      {/* Node Count */}
      <div className="absolute top-4 left-4 bg-card text-foreground px-3 py-2 rounded-lg shadow-lg border border-border dark:bg-slate-800 dark:text-slate-100">
        <div className="text-sm font-semibold">
          {graphData.nodes.length} nodes • {graphData.links.length} connections
        </div>
      </div>
    </div>
  );
}
