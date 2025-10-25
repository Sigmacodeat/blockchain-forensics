// Trace Types
export type TaintModel = 'fifo' | 'proportional' | 'haircut'
export type TraceDirection = 'forward' | 'backward' | 'both'

export interface TraceRequest {
  source_address: string
  direction?: TraceDirection
  max_depth?: number
  max_nodes?: number
  taint_model?: TaintModel
  min_taint_threshold?: number
  start_timestamp?: string
  end_timestamp?: string
  save_to_graph?: boolean
}

export interface TraceNode {
  address: string
  taint_received: number
  taint_sent: number
  hop_distance: number
  labels: string[]
}

export interface TraceEdge {
  from_address: string
  to_address: string
  tx_hash: string
  value: number
  taint_value: number
  timestamp: string
  hop: number
}

export interface TraceResult {
  trace_id: string
  source_address: string
  direction: TraceDirection
  taint_model: TaintModel
  max_depth: number
  total_nodes: number
  total_edges: number
  max_hop_reached: number
  nodes: Record<string, TraceNode>
  edges: TraceEdge[]
  high_risk_addresses: string[]
  sanctioned_addresses: string[]
  completed: boolean
  execution_time_seconds: number
  error?: string
}

export interface TraceStatusResponse {
  trace_id: string
  status: string
  completed: boolean
  total_nodes: number
  total_edges: number
  execution_time_seconds?: number
}

// AI Agent Types
export interface InvestigationRequest {
  query: string
  chat_history?: Array<{ role: string; content: string }>
}

export interface InvestigationResponse {
  response: string
  success: boolean
  intermediate_steps?: any[]
  error?: string
}

// Enrichment Types
export interface AddressLabel {
  address: string
  labels: string[]
  entity_name?: string
  category?: string
  risk_score?: number
}

export interface RiskScore {
  address: string
  risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  factors: string[]
}
