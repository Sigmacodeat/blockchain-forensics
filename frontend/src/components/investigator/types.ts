// Shared types for Investigator components

export interface GraphNode {
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

export interface GraphEdge {
  source: string;
  target: string;
  tx_hash: string;
  value: number;
  timestamp: string;
  event_type: string;
  bridge?: string;
}

export interface ClusterData {
  cluster_id: number;
  size: number;
  members: string[];
  stats: {
    total_balance: number;
    avg_risk_score: number;
    tx_volume: number;
  };
}

export interface CrossChainData {
  chains: Record<string, number>;
  degree: { in: number; out: number };
  bridges: { outbound: number; inbound: number };
}

export interface PathResult {
  path: string[];
  hops: number;
  total_value: number;
  risk_score: number;
  bridges: string[];
}

export interface TimelineEvent {
  timestamp: string;
  address: string;
  event_type: string;
  value: number;
  tx_hash: string;
  risk_score: number;
}

export interface AdvancedTraceResult {
  trace_id: string;
  source_address: string;
  total_addresses: number;
  total_transactions: number;
  high_risk_count: number;
  sanctioned_count: number;
  clusters?: Record<string, number>;
  cross_chain?: CrossChainData;
  graph_nodes?: Array<{ id: string; type: string }>;
  graph_edges?: Array<{ source: string; target: string; type: string }>;
}

export interface GraphControls {
  zoomIn: () => void;
  zoomOut: () => void;
  zoomToFit: () => void;
  centerOn: (address?: string) => void;
}

export interface LocalGraph {
  nodes: Record<string, GraphNode>;
  links: GraphEdge[];
}
