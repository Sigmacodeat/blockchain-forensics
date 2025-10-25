"""
CSV Export Functions
Export trace data and analysis results
"""

import logging
import csv
from io import StringIO
from typing import Dict, List

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export data to CSV format"""
    
    async def export_trace(self, trace_data: Dict) -> str:
        """
        Export trace results to CSV
        
        Args:
            trace_data: Trace result data
        
        Returns:
            CSV string
        """
        output = StringIO()
        
        # Write nodes
        nodes_csv = StringIO()
        nodes_writer = csv.writer(nodes_csv)
        nodes_writer.writerow(['Address', 'Taint Received', 'Taint Sent', 'Hop Distance', 'Labels'])
        
        for address, node in trace_data.get('nodes', {}).items():
            nodes_writer.writerow([
                address,
                node.get('taint_received', 0),
                node.get('taint_sent', 0),
                node.get('hop_distance', 0),
                ', '.join(node.get('labels', []))
            ])
        
        # Write edges
        edges_csv = StringIO()
        edges_writer = csv.writer(edges_csv)
        edges_writer.writerow(['From', 'To', 'TX Hash', 'Value', 'Taint Value', 'Timestamp', 'Hop'])
        
        for edge in trace_data.get('edges', []):
            edges_writer.writerow([
                edge.get('from_address'),
                edge.get('to_address'),
                edge.get('tx_hash'),
                edge.get('value'),
                edge.get('taint_value'),
                edge.get('timestamp'),
                edge.get('hop')
            ])
        
        # Combine
        output.write("# NODES\n")
        output.write(nodes_csv.getvalue())
        output.write("\n# EDGES\n")
        output.write(edges_csv.getvalue())
        
        return output.getvalue()
    
    async def export_addresses(self, addresses: List[Dict]) -> str:
        """Export addresses to CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Address', 'Risk Score', 'Risk Level', 'Labels', 'Entity'])
        
        for addr in addresses:
            writer.writerow([
                addr.get('address'),
                addr.get('risk_score', 0),
                addr.get('risk_level', 'unknown'),
                ', '.join(addr.get('labels', [])),
                addr.get('entity_name', '')
            ])
        
        return output.getvalue()


csv_exporter = CSVExporter()
