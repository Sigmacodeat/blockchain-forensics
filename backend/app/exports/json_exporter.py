"""
JSON Export Functions
Standard format exports
"""

import logging
import json
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export data to JSON format"""
    
    async def export_trace(self, trace_data: Dict) -> str:
        """
        Export trace to JSON
        
        Args:
            trace_data: Trace result data
        
        Returns:
            JSON string
        """
        # Add metadata
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'export_format': 'json',
            'version': '1.0',
            'trace_data': trace_data
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    async def export_graph(self, trace_data: Dict) -> str:
        """
        Export as graph format (nodes + edges)
        
        Compatible with:
        - D3.js
        - Cytoscape
        - Gephi
        """
        nodes = []
        edges = []
        
        # Convert nodes
        for address, node in trace_data.get('nodes', {}).items():
            nodes.append({
                'id': address,
                'taint': node.get('taint_received', 0),
                'hop': node.get('hop_distance', 0),
                'labels': node.get('labels', [])
            })
        
        # Convert edges
        for edge in trace_data.get('edges', []):
            edges.append({
                'source': edge.get('from_address'),
                'target': edge.get('to_address'),
                'value': edge.get('taint_value'),
                'tx_hash': edge.get('tx_hash')
            })
        
        return json.dumps({'nodes': nodes, 'links': edges}, indent=2)


json_exporter = JSONExporter()
