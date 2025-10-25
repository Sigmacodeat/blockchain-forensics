"""
Erweiterte Visualisierung für Blockchain Forensics
================================================

3D-Graphen, Heatmaps und interaktive Timelines für:
- Komplexe Beziehungsanalyse
- Zeitbasierte Mustererkennung
- Räumliche Darstellung von Transaktionsmustern
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VisualizationType(str, Enum):
    """Arten von Visualisierungen"""
    GRAPH_2D = "graph_2d"
    GRAPH_3D = "graph_3d"
    HEATMAP = "heatmap"
    TIMELINE = "timeline"
    SANKEY = "sankey"
    TREEMAP = "treemap"
    SCATTER_3D = "scatter_3d"


@dataclass
class VisualizationConfig:
    """Konfiguration für Visualisierungen"""
    viz_type: VisualizationType
    title: str
    width: int = 800
    height: int = 600
    interactive: bool = True
    show_legend: bool = True
    color_scheme: str = "viridis"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.viz_type.value,
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "interactive": self.interactive,
            "show_legend": self.show_legend,
            "color_scheme": self.color_scheme
        }


class GraphVisualizer:
    """3D-Graph-Visualisierung für komplexe Beziehungen"""

    def __init__(self):
        self.node_positions = {}
        self.edge_weights = {}

    def create_3d_graph(self, nodes: List[Dict], edges: List[Dict], config: VisualizationConfig) -> Dict[str, Any]:
        """Erstellt 3D-Graph-Daten für Visualisierung"""
        # Force-directed Layout Algorithmus für 3D-Positionierung
        positions = self._calculate_3d_positions(nodes, edges)

        graph_data = {
            "type": "graph_3d",
            "config": config.to_dict(),
            "data": {
                "nodes": [
                    {
                        "id": node["id"],
                        "label": node.get("label", node["id"]),
                        "x": positions[node["id"]]["x"],
                        "y": positions[node["id"]]["y"],
                        "z": positions[node["id"]]["z"],
                        "size": self._calculate_node_size(node),
                        "color": self._get_node_color(node),
                        "metadata": node
                    }
                    for node in nodes
                ],
                "edges": [
                    {
                        "source": edge["source"],
                        "target": edge["target"],
                        "weight": edge.get("weight", 1),
                        "type": edge.get("type", "default"),
                        "color": self._get_edge_color(edge),
                        "metadata": edge
                    }
                    for edge in edges
                ]
            }
        }

        return graph_data

    def _calculate_3d_positions(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Berechnet 3D-Positionen mit Force-Directed Algorithmus"""
        positions = {}

        # Initiale zufällige Positionierung
        for node in nodes:
            positions[node["id"]] = {
                "x": np.random.uniform(-10, 10),
                "y": np.random.uniform(-10, 10),
                "z": np.random.uniform(-10, 10)
            }

        # Force-directed Iterationen
        for _ in range(100):  # 100 Iterationen
            forces = {node_id: {"x": 0, "y": 0, "z": 0} for node_id in positions}

            # Repulsive Kräfte (alle Knoten stoßen sich ab)
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes[i+1:], i+1):
                    if node1["id"] != node2["id"]:
                        dx = positions[node1["id"]]["x"] - positions[node2["id"]]["x"]
                        dy = positions[node1["id"]]["y"] - positions[node2["id"]]["y"]
                        dz = positions[node1["id"]]["z"] - positions[node2["id"]]["z"]
                        distance = np.sqrt(dx**2 + dy**2 + dz**2)

                        if distance > 0:
                            force = 1 / distance**2  # Inverse Quadrat Kraft
                            forces[node1["id"]]["x"] += force * dx / distance
                            forces[node1["id"]]["y"] += force * dy / distance
                            forces[node1["id"]]["z"] += force * dz / distance

                            forces[node2["id"]]["x"] -= force * dx / distance
                            forces[node2["id"]]["y"] -= force * dy / distance
                            forces[node2["id"]]["z"] -= force * dz / distance

            # Attractive Kräfte (verbundene Knoten ziehen sich an)
            for edge in edges:
                source, target = edge["source"], edge["target"]
                if source in positions and target in positions:
                    dx = positions[source]["x"] - positions[target]["x"]
                    dy = positions[source]["y"] - positions[target]["y"]
                    dz = positions[source]["z"] - positions[target]["z"]
                    distance = np.sqrt(dx**2 + dy**2 + dz**2)

                    if distance > 0:
                        force = distance**2 / 100  # Hooke's Law
                        forces[source]["x"] -= force * dx / distance
                        forces[source]["y"] -= force * dy / distance
                        forces[source]["z"] -= force * dz / distance

                        forces[target]["x"] += force * dx / distance
                        forces[target]["y"] += force * dy / distance
                        forces[target]["z"] += force * dz / distance

            # Positionen aktualisieren
            for node_id in positions:
                positions[node_id]["x"] += forces[node_id]["x"] * 0.01
                positions[node_id]["y"] += forces[node_id]["y"] * 0.01
                positions[node_id]["z"] += forces[node_id]["z"] * 0.01

        return positions

    def _calculate_node_size(self, node: Dict) -> float:
        """Berechnet Knotengröße basierend auf Bedeutung"""
        # Größe basierend auf Transaktionsvolumen oder Verbindungen
        tx_count = node.get("tx_count", 1)
        return min(5 + np.log(tx_count + 1), 20)

    def _get_node_color(self, node: Dict) -> str:
        """Farbe basierend auf Knotentyp und Risiko"""
        risk_score = node.get("risk_score", 0)
        node_type = node.get("type", "unknown")

        if risk_score > 0.8:
            return "#ff4444"  # Rot für hohes Risiko
        elif risk_score > 0.5:
            return "#ffaa00"  # Orange für mittleres Risiko
        else:
            return "#44aa88"  # Grün für niedriges Risiko

    def _get_edge_color(self, edge: Dict) -> str:
        """Farbe basierend auf Edge-Typ"""
        edge_type = edge.get("type", "default")
        if edge_type == "bridge":
            return "#8888ff"
        elif edge_type == "mixer":
            return "#ff8888"
        else:
            return "#88aa88"


class HeatmapVisualizer:
    """Heatmap-Visualisierung für zeitbasierte Muster"""

    def __init__(self):
        self.time_buckets = {}

    def create_heatmap(self, data: List[Dict], config: VisualizationConfig) -> Dict[str, Any]:
        """Erstellt Heatmap für zeitbasierte Daten"""
        # Zeitachsen-Aggregation
        time_series = self._aggregate_time_series(data)

        # 2D-Grid für Heatmap
        heatmap_grid = self._create_heatmap_grid(time_series, config)

        return {
            "type": "heatmap",
            "config": config.to_dict(),
            "data": {
                "grid": heatmap_grid,
                "x_labels": list(heatmap_grid.keys()) if heatmap_grid else [],
                "y_labels": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                "color_scale": "viridis",
                "max_value": max(max(row) for row in heatmap_grid.values()) if heatmap_grid else 0
            }
        }

    def _aggregate_time_series(self, data: List[Dict]) -> Dict[str, Dict[str, int]]:
        """Aggregiert Daten in Zeitbuckets"""
        time_series = {}

        for entry in data:
            timestamp = entry.get("timestamp")
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.strftime("%Y-%m-%d-%H")

                if hour not in time_series:
                    time_series[hour] = {"count": 0, "value": 0}

                time_series[hour]["count"] += 1
                time_series[hour]["value"] += entry.get("value", 0)

        return time_series

    def _create_heatmap_grid(self, time_series: Dict, config: VisualizationConfig) -> Dict[str, List[float]]:
        """Erstellt 2D-Grid für Heatmap"""
        grid = {}

        for hour, data in time_series.items():
            date_hour = hour.split("-")[-1]  # Letzte Stunde
            if date_hour not in grid:
                grid[date_hour] = [0.0] * 6  # 6 Zeit-Slots pro Stunde

            # Bestimme Zeit-Slot (0-5)
            slot = int(hour.split("-")[-1]) // 4  # 4-Stunden-Buckets
            if slot < 6:
                grid[date_hour][slot] = max(grid[date_hour][slot], data["value"])

        return grid


class TimelineVisualizer:
    """Interaktive Timeline-Visualisierung"""

    def __init__(self):
        self.event_types = set()

    def create_timeline(self, events: List[Dict], config: VisualizationConfig) -> Dict[str, Any]:
        """Erstellt interaktive Timeline"""
        # Events nach Zeit sortieren
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))

        # Events in Zeitgruppen aufteilen
        time_groups = self._group_events_by_time(sorted_events)

        timeline_data = {
            "type": "timeline",
            "config": config.to_dict(),
            "data": {
                "events": [
                    {
                        "id": event.get("id", f"event_{i}"),
                        "title": event.get("title", "Event"),
                        "description": event.get("description", ""),
                        "timestamp": event.get("timestamp"),
                        "type": event.get("type", "unknown"),
                        "severity": event.get("severity", "info"),
                        "group": self._get_time_group(event.get("timestamp")),
                        "metadata": event
                    }
                    for i, event in enumerate(sorted_events)
                ],
                "groups": [
                    {"id": group_id, "content": group_label}
                    for group_id, group_label in time_groups.items()
                ]
            }
        }

        return timeline_data

    def _group_events_by_time(self, events: List[Dict]) -> Dict[str, str]:
        """Gruppiert Events nach Zeitperioden"""
        groups = {}
        current_group = None

        for event in events:
            timestamp = event.get("timestamp")
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

                # Neue Gruppe pro Tag
                group_id = dt.strftime("%Y-%m-%d")
                if group_id != current_group:
                    groups[group_id] = dt.strftime("%A, %B %d, %Y")
                    current_group = group_id

        return groups

    def _get_time_group(self, timestamp: str) -> str:
        """Bestimmt Zeitgruppe für Event"""
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d")
        return "unknown"


class SankeyVisualizer:
    """Sankey-Diagramm für Flow-Analyse"""

    def __init__(self):
        self.flow_data = {}

    def create_sankey(self, flows: List[Dict], config: VisualizationConfig) -> Dict[str, Any]:
        """Erstellt Sankey-Diagramm für Geldflüsse"""
        # Aggregiere Flüsse
        aggregated_flows = self._aggregate_flows(flows)

        # Erstelle Nodes und Links
        nodes, links = self._create_sankey_elements(aggregated_flows)

        sankey_data = {
            "type": "sankey",
            "config": config.to_dict(),
            "data": {
                "nodes": nodes,
                "links": links
            }
        }

        return sankey_data

    def _aggregate_flows(self, flows: List[Dict]) -> Dict[Tuple[str, str], float]:
        """Aggregiert Flüsse zwischen Entitäten"""
        aggregated = {}

        for flow in flows:
            source = flow.get("source", "unknown")
            target = flow.get("target", "unknown")
            value = flow.get("value", 0)

            key = (source, target)
            aggregated[key] = aggregated.get(key, 0) + value

        return aggregated

    def _create_sankey_elements(self, aggregated_flows: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Erstellt Sankey Nodes und Links"""
        nodes = []
        links = []
        node_index = {}

        for (source, target), value in aggregated_flows.items():
            # Nodes hinzufügen
            for entity in [source, target]:
                if entity not in node_index:
                    node_index[entity] = len(nodes)
                    nodes.append({
                        "id": entity,
                        "label": entity,
                        "color": self._get_node_color(entity)
                    })

            # Link hinzufügen
            links.append({
                "source": node_index[source],
                "target": node_index[target],
                "value": value,
                "color": self._get_link_color(value)
            })

        return nodes, links

    def _get_node_color(self, entity: str) -> str:
        """Farbe basierend auf Entitätstyp"""
        if "exchange" in entity.lower():
            return "#ffaa00"
        elif "bridge" in entity.lower():
            return "#8888ff"
        else:
            return "#44aa88"

    def _get_link_color(self, value: float) -> str:
        """Farbe basierend auf Wert"""
        if value > 1000000:
            return "rgba(255, 68, 68, 0.6)"  # Rot für große Werte
        elif value > 100000:
            return "rgba(255, 170, 0, 0.6)"  # Orange für mittlere Werte
        else:
            return "rgba(68, 170, 136, 0.6)"  # Grün für kleine Werte


class ForensicVisualizer:
    """Haupt-Engine für erweiterte Visualisierungen"""

    def __init__(self):
        self.graph_viz = GraphVisualizer()
        self.heatmap_viz = HeatmapVisualizer()
        self.timeline_viz = TimelineVisualizer()
        self.sankey_viz = SankeyVisualizer()

    def create_visualization(self, viz_type: VisualizationType, data: Any, config: VisualizationConfig) -> Dict[str, Any]:
        """Erstellt Visualisierung basierend auf Typ"""
        if viz_type == VisualizationType.GRAPH_3D:
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            return self.graph_viz.create_3d_graph(nodes, edges, config)

        elif viz_type == VisualizationType.HEATMAP:
            return self.heatmap_viz.create_heatmap(data, config)

        elif viz_type == VisualizationType.TIMELINE:
            events = data.get("events", [])
            return self.timeline_viz.create_timeline(events, config)

        elif viz_type == VisualizationType.SANKEY:
            flows = data.get("flows", [])
            return self.sankey_viz.create_sankey(flows, config)

        else:
            raise ValueError(f"Unsupported visualization type: {viz_type}")

    def create_dashboard_visualizations(self, forensic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Erstellt mehrere Visualisierungen für Dashboard"""
        visualizations = []

        # 3D-Graph für Adress-Beziehungen
        if "graph_data" in forensic_data:
            config = VisualizationConfig(
                viz_type=VisualizationType.GRAPH_3D,
                title="Address Relationship Graph",
                width=1000,
                height=800
            )
            viz = self.create_visualization(VisualizationType.GRAPH_3D, forensic_data["graph_data"], config)
            visualizations.append(viz)

        # Heatmap für zeitbasierte Aktivität
        if "time_series_data" in forensic_data:
            config = VisualizationConfig(
                viz_type=VisualizationType.HEATMAP,
                title="Activity Heatmap",
                width=800,
                height=600
            )
            viz = self.create_visualization(VisualizationType.HEATMAP, forensic_data["time_series_data"], config)
            visualizations.append(viz)

        # Timeline für Events
        if "events" in forensic_data:
            config = VisualizationConfig(
                viz_type=VisualizationType.TIMELINE,
                title="Event Timeline",
                width=1200,
                height=400
            )
            viz = self.create_visualization(VisualizationType.TIMELINE, {"events": forensic_data["events"]}, config)
            visualizations.append(viz)

        # Sankey für Geldflüsse
        if "flows" in forensic_data:
            config = VisualizationConfig(
                viz_type=VisualizationType.SANKEY,
                title="Money Flow Analysis",
                width=1000,
                height=600
            )
            viz = self.create_visualization(VisualizationType.SANKEY, {"flows": forensic_data["flows"]}, config)
            visualizations.append(viz)

        return visualizations

    def export_visualization(self, visualization: Dict[str, Any], format: str = "json") -> str:
        """Exportiert Visualisierung in verschiedenen Formaten"""
        if format == "json":
            return json.dumps(visualization, indent=2, ensure_ascii=False)
        elif format == "html":
            # HTML-Export mit eingebetteten Visualisierungen
            return self._create_html_export(visualization)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _create_html_export(self, visualization: Dict[str, Any]) -> str:
        """Erstellt HTML-Export mit eingebetteten Charts"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .chart-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="chart-container">
                <div id="visualization"></div>
            </div>
            <script>
                const data = {data};
                const layout = {layout};
                Plotly.newPlot('visualization', data, layout);
            </script>
        </body>
        </html>
        """

        # Vereinfachte Daten-Extraktion für Plotly
        plotly_data = self._convert_to_plotly(visualization)

        return html_template.format(
            title=visualization.get("config", {}).get("title", "Visualization"),
            data=json.dumps(plotly_data.get("data", [])),
            layout=json.dumps(plotly_data.get("layout", {}))
        )

    def _convert_to_plotly(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Konvertiert Visualisierung zu Plotly-Format"""
        viz_type = visualization.get("type")
        data = visualization.get("data", {})

        if viz_type == "graph_3d":
            # 3D Scatter für Nodes
            nodes = data.get("nodes", [])
            return {
                "data": [{
                    "type": "scatter3d",
                    "x": [n["x"] for n in nodes],
                    "y": [n["y"] for n in nodes],
                    "z": [n["z"] for n in nodes],
                    "mode": "markers+text",
                    "text": [n["label"] for n in nodes],
                    "marker": {
                        "size": [n["size"] for n in nodes],
                        "color": [n["color"] for n in nodes],
                        "opacity": 0.8
                    }
                }],
                "layout": {
                    "title": visualization.get("config", {}).get("title"),
                    "scene": {
                        "xaxis": {"title": "X"},
                        "yaxis": {"title": "Y"},
                        "zaxis": {"title": "Z"}
                    }
                }
            }
        else:
            return {"data": [], "layout": {}}


# Singleton Instance
forensic_visualizer = ForensicVisualizer()
