import type { TraceResult } from './types'

/**
 * Export-Utilities für Trace-Ergebnisse
 */

// CSV Export
export function exportTraceToCSV(trace: TraceResult): void {
  const rows: string[][] = [
    ['Type', 'From', 'To', 'TX Hash', 'Value', 'Taint Value', 'Timestamp', 'Hop'],
  ]

  // Edges als CSV Rows
  trace.edges.forEach((edge) => {
    rows.push([
      'Transaction',
      edge.from_address,
      edge.to_address,
      edge.tx_hash,
      edge.value.toString(),
      edge.taint_value.toString(),
      edge.timestamp,
      edge.hop.toString(),
    ])
  })

  // High-Risk Addresses
  trace.high_risk_addresses.forEach((addr) => {
    const node = trace.nodes[addr]
    rows.push([
      'High-Risk Address',
      addr,
      node?.labels.join(', ') || '',
      '',
      '',
      node?.taint_received.toString() || '0',
      '',
      node?.hop_distance.toString() || '0',
    ])
  })

  // Sanctioned Addresses
  trace.sanctioned_addresses.forEach((addr) => {
    rows.push([
      'OFAC Sanctioned',
      addr,
      '',
      '',
      '',
      '',
      '',
      '',
    ])
  })

  const csvContent = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n')
  downloadFile(csvContent, `trace_${trace.trace_id}.csv`, 'text/csv')
}

// JSON Export
export function exportTraceToJSON(trace: TraceResult): void {
  const jsonContent = JSON.stringify(trace, null, 2)
  downloadFile(jsonContent, `trace_${trace.trace_id}.json`, 'application/json')
}

// Nodes CSV Export
export function exportNodesToCSV(trace: TraceResult): void {
  const rows: string[][] = [
    ['Address', 'Taint Received', 'Taint Sent', 'Hop Distance', 'Labels', 'Risk Level'],
  ]

  Object.entries(trace.nodes).forEach(([address, node]) => {
    const isHighRisk = trace.high_risk_addresses.includes(address)
    const isSanctioned = trace.sanctioned_addresses.includes(address)
    let riskLevel = 'Low'
    if (isSanctioned) riskLevel = 'Critical (Sanctioned)'
    else if (isHighRisk) riskLevel = 'High'
    else if (node.taint_received > 0.5) riskLevel = 'Medium'

    rows.push([
      address,
      node.taint_received.toFixed(4),
      node.taint_sent.toFixed(4),
      node.hop_distance.toString(),
      node.labels.join('; '),
      riskLevel,
    ])
  })

  const csvContent = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n')
  downloadFile(csvContent, `trace_nodes_${trace.trace_id}.csv`, 'text/csv')
}

// Helper: Download File
function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// GraphML Export (für Gephi, Cytoscape etc.)
export function exportTraceToGraphML(trace: TraceResult): void {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
  xml += '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'
  xml += '  <key id="d0" for="node" attr.name="label" attr.type="string"/>\n'
  xml += '  <key id="d1" for="node" attr.name="taint_received" attr.type="double"/>\n'
  xml += '  <key id="d2" for="edge" attr.name="value" attr.type="double"/>\n'
  xml += '  <key id="d3" for="edge" attr.name="taint_value" attr.type="double"/>\n'
  xml += '  <key id="d4" for="edge" attr.name="tx_hash" attr.type="string"/>\n'
  xml += '  <graph id="G" edgedefault="directed">\n'

  // Nodes
  Object.entries(trace.nodes).forEach(([address, node]) => {
    xml += `    <node id="${address}">\n`
    xml += `      <data key="d0">${node.labels.join(', ')}</data>\n`
    xml += `      <data key="d1">${node.taint_received}</data>\n`
    xml += `    </node>\n`
  })

  // Edges
  trace.edges.forEach((edge, idx) => {
    xml += `    <edge id="e${idx}" source="${edge.from_address}" target="${edge.to_address}">\n`
    xml += `      <data key="d2">${edge.value}</data>\n`
    xml += `      <data key="d3">${edge.taint_value}</data>\n`
    xml += `      <data key="d4">${edge.tx_hash}</data>\n`
    xml += `    </edge>\n`
  })

  xml += '  </graph>\n'
  xml += '</graphml>'

  downloadFile(xml, `trace_${trace.trace_id}.graphml`, 'application/xml')
}
