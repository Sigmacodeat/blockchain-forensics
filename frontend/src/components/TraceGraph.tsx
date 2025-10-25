import { useEffect, useRef } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { TraceResult } from '@/lib/types'
import { formatAddress } from '@/lib/utils'

interface TraceGraphProps {
  trace: TraceResult
}

export default function TraceGraph({ trace }: TraceGraphProps) {
  const graphRef = useRef<any>()

  const isDarkRef = useRef(false as boolean)
  useEffect(() => {
    const update = () => { isDarkRef.current = document.documentElement.classList.contains('dark') }
    update()
    const obs = new MutationObserver(update)
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => obs.disconnect()
  }, [])

  // Convert trace data to graph format
  const graphData = {
    nodes: Object.entries(trace.nodes).map(([address, node]) => ({
      id: address,
      name: formatAddress(address, 6),
      taint: node.taint_received,
      hop: node.hop_distance,
      labels: node.labels,
      isSource: address === trace.source_address,
      isHighRisk: trace.high_risk_addresses.includes(address),
      isSanctioned: trace.sanctioned_addresses.includes(address),
    })),
    links: trace.edges.map((edge) => ({
      source: edge.from_address,
      target: edge.to_address,
      value: edge.taint_value,
      txHash: edge.tx_hash,
      event_type: (edge as any).event_type,
      bridge: (edge as any).bridge,
      chain_from: (edge as any).chain_from,
      chain_to: (edge as any).chain_to,
      hop: (edge as any).hop,
    })),
  }

  useEffect(() => {
    // Auto-zoom to fit
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50)
    }
  }, [trace])

  const getNodeColor = (node: any) => {
    if (node.isSanctioned) return '#dc2626' // red-600
    if (node.isHighRisk) return '#ea580c' // orange-600
    if (node.isSource) return '#0ea5e9' // primary-600
    return '#6b7280' // gray-500
  }

  const getNodeSize = (node: any) => {
    if (node.isSource) return 8
    if (node.isSanctioned || node.isHighRisk) return 6
    return 4
  }

  return (
    <div className="relative w-full h-[600px] bg-card rounded-lg overflow-hidden border border-border">
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        linkLabel={(link: any) => {
          const isBridge = String(link.event_type || '').toLowerCase() === 'bridge'
          const parts = [
            `Tx: ${link.txHash || 'n/a'}`,
            `Hop: ${link.hop ?? 'n/a'}`,
          ]
          if (isBridge) {
            parts.unshift(`Bridge: ${link.bridge || 'unknown'}`)
            parts.push(`From: ${link.chain_from || 'n/a'}`)
            parts.push(`To: ${link.chain_to || 'n/a'}`)
          }
          return parts.join(' | ')
        }}
        nodeLabel={(node: any) => {
          const dark = isDarkRef.current
          const bg = dark ? '#0f172a' : '#ffffff' // slate-900 vs white
          const fg = dark ? '#e2e8f0' : '#111827' // slate-200 vs gray-900
          const sub = dark ? '#94a3b8' : '#666666' // slate-400 vs gray-600
          const shadow = dark ? 'rgba(0,0,0,0.45)' : 'rgba(0,0,0,0.15)'
          const border = dark ? 'rgba(148,163,184,0.25)' : 'rgba(100,116,139,0.25)'
          return `
          <div style="background:${bg}; color:${fg}; padding: 8px; border-radius: 6px; box-shadow: 0 2px 8px ${shadow}; border: 1px solid ${border};">
            <div style="font-weight: 600; margin-bottom: 4px;">${node.name}</div>
            <div style="font-size: 12px; color:${sub}; line-height:1.5;">
              Taint: ${(node.taint * 100).toFixed(2)}%<br/>
              Hop: ${node.hop}<br/>
              ${node.labels.length > 0 ? `Labels: ${node.labels.join(', ')}` : ''}
            </div>
          </div>
        `
        }}
        nodeColor={getNodeColor}
        nodeVal={getNodeSize}
        linkColor={(link: any) =>
          String(link.event_type || '').toLowerCase() === 'bridge' ? '#06b6d4' /* cyan-500 */ : '#cbd5e1' /* gray-300 */
        }
        linkWidth={(link: any) => {
          const base = Math.max(1, link.value * 3)
          return String(link.event_type || '').toLowerCase() === 'bridge' ? base + 1 : base
        }}
        linkLineDash={(link: any) =>
          String(link.event_type || '').toLowerCase() === 'bridge' ? [6, 4] : null
        }
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkCurvature={0.2}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        cooldownTicks={100}
        onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
      />
      
      {/* Legend */}
      <div className="absolute top-4 right-4 bg-card text-foreground p-4 rounded-lg shadow-md text-sm border border-border">
        <h3 className="font-semibold mb-2">Legend</h3>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-primary-600" />
            <span>Source</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-600" />
            <span>Sanctioned</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-600" />
            <span>High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-500" />
            <span>Normal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-cyan-500" style={{ borderBottom: '2px dashed #06b6d4', width: '1.25rem' }} />
            <span>Bridge Edge</span>
          </div>
        </div>
      </div>

      {/* Controls Hint */}
      <div className="absolute bottom-4 left-4 bg-card text-foreground p-3 rounded-lg shadow-md text-xs border border-border">
        <p className="text-muted-foreground">🖱️ Drag nodes | Scroll to zoom | Click & drag to pan</p>
      </div>
    </div>
  )
}
