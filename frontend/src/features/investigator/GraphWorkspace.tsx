/**
 * Investigator Graph Workspace Component
 * =====================================
 *
 * Interactive graph visualization for blockchain forensics investigations.
 * Uses Cytoscape.js for graph rendering with live WebSocket updates.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape from 'cytoscape';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Play, Pause, RotateCcw, ZoomIn, ZoomOut, Maximize } from 'lucide-react';

interface GraphNode {
  id: string;
  address: string;
  type: string;
  risk_level: string;
  taint_received: number;
  taint_sent: number;
  labels: string[];
  metadata: Record<string, any>;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  value: number;
  taint: number;
  timestamp?: string;
  tx_hash?: string;
  metadata: Record<string, any>;
}

interface SubgraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
  query_depth: number;
  execution_time_ms: number;
}

interface TraceStatus {
  trace_id: string;
  status: string;
  progress: number;
  nodes_found: number;
  current_hop: number;
  estimated_completion?: string;
}

const RISK_COLORS = {
  LOW: '#10b981',     // Green
  MEDIUM: '#f59e0b',  // Yellow
  HIGH: '#ef4444',    // Red
  CRITICAL: '#7c2d12' // Dark red
};

const NODE_TYPES = {
  address: '#0284c7',    // Primary
  transaction: '#8b5cf6', // Purple
  entity: '#06b6d4'      // Cyan
};

export function GraphWorkspace() {
  const cyRef = useRef<HTMLDivElement>(null);
  const cyInstance = useRef<cytoscape.Core | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // State
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentAddress, setCurrentAddress] = useState('');
  const [subgraphData, setSubgraphData] = useState<SubgraphResponse | null>(null);
  const [traceStatus, setTraceStatus] = useState<TraceStatus | null>(null);

  // UI Controls
  const [depth, setDepth] = useState([3]);
  const [includeTransactions, setIncludeTransactions] = useState(true);
  const [includeLabels, setIncludeLabels] = useState(true);
  const [riskThreshold, setRiskThreshold] = useState([0.0]);
  const [defiOnly, setDefiOnly] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(false);

  // WebSocket for real-time updates
  const wsRef = useRef<WebSocket | null>(null);

  // API base helper
  const apiBase = (import.meta as any)?.env?.VITE_API_URL || '';
  const apiUrl = useCallback((path: string) => {
    if (!apiBase) return path; // relative fetch (proxy/dev)
    return `${String(apiBase).replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
  }, [apiBase]);

  const initializeCytoscape = useCallback(() => {
    if (!cyRef.current || cyInstance.current) return;

    cyInstance.current = cytoscape({
      container: cyRef.current,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele: any) => {
              const risk = ele.data('risk_level');
              return RISK_COLORS[risk as keyof typeof RISK_COLORS] || '#6b7280';
            },
            'border-width': 2,
            'border-color': (ele: any) => {
              const type = ele.data('type');
              return NODE_TYPES[type as keyof typeof NODE_TYPES] || '#6b7280';
            },
            'label': (ele: any) => {
              const address = ele.data('address');
              return address.length > 10 ? `${address.slice(0, 6)}...${address.slice(-4)}` : address;
            },
            'font-size': 10,
            'text-valign': 'center',
            'text-halign': 'center',
            'width': (ele: any) => {
              const taint = ele.data('taint_received') || 0;
              return Math.max(20, Math.min(60, 20 + taint * 40));
            },
            'height': (ele: any) => {
              const taint = ele.data('taint_received') || 0;
              return Math.max(20, Math.min(60, 20 + taint * 40));
            }
          }
        },
        {
          selector: 'node[is_defi = 1]',
          style: {
            'border-width': 4,
            'border-color': '#7c3aed' // violet highlight for DeFi-labeled nodes
          }
        },
        {
          selector: 'edge',
          style: {
            'width': (ele: any) => {
              const value = ele.data('value') || 0;
              return Math.max(1, Math.min(5, 1 + Math.log10(value + 1)));
            },
            'line-color': (ele: any) => {
              const taint = ele.data('taint') || 0;
              return taint > 0.5 ? '#ef4444' : taint > 0.2 ? '#f59e0b' : '#10b981';
            },
            'target-arrow-color': '#6b7280',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': (ele: any) => {
              const value = ele.data('value');
              return value > 0.001 ? `${value.toFixed(4)} ETH` : '';
            },
            'font-size': 8,
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.8
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#1f2937'
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#1f2937',
            'target-arrow-color': '#1f2937'
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 1000,
        nodeOverlap: 20,
        idealEdgeLength: 100,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: true,
      autounselectify: false
    });

    // Event listeners
    cyInstance.current.on('tap', 'node', (event: any) => {
      const node = event.target;
      const data = node.data();
      console.log('Node selected:', data);
      // Could open detail panel here
    });

    cyInstance.current.on('tap', 'edge', (event: any) => {
      const edge = event.target;
      const data = edge.data();
      console.log('Edge selected:', data);
      // Could show transaction details
    });

  }, []);

  const loadSubgraph = useCallback(async () => {
    if (!currentAddress) return;

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        address: currentAddress,
        depth: depth[0].toString(),
        include_transactions: includeTransactions.toString(),
        include_labels: includeLabels.toString(),
        risk_threshold: riskThreshold[0].toString()
      });

      const response = await fetch(apiUrl(`/api/v1/graph/subgraph?${params}`));

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: SubgraphResponse = await response.json();
      setSubgraphData(data);

      // Update graph visualization
      updateGraphVisualization(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subgraph');
    } finally {
      setIsLoading(false);
    }
  }, [currentAddress, depth, includeTransactions, includeLabels, riskThreshold]);

  const updateGraphVisualization = useCallback((data: SubgraphResponse) => {
    if (!cyInstance.current) return;

    const cy = cyInstance.current;

    // Clear existing elements
    cy.elements().remove();

    // Add nodes
    const nodes = data.nodes.map(node => ({
      data: {
        id: node.id,
        address: node.address,
        type: node.type,
        risk_level: node.risk_level,
        taint_received: node.taint_received,
        taint_sent: node.taint_sent,
        labels: node.labels,
        is_defi: Array.isArray(node.labels) && node.labels.some((l: any) => typeof l === 'string' && l.toLowerCase().startsWith('defi:')) ? 1 : 0,
        metadata: node.metadata
      }
    }));

    // Add edges
    const edges = data.edges.map(edge => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        value: edge.value,
        taint: edge.taint,
        timestamp: edge.timestamp,
        tx_hash: edge.tx_hash,
        metadata: edge.metadata
      }
    }));

    cy.add([...nodes, ...edges]);

    // Re-run layout
    cy.layout({
      name: 'cose',
      animate: true,
      animationDuration: 800
    }).run();

    // Fit to viewport
    cy.fit(undefined, 50);

    // Apply DeFi filter visibility
    if (defiOnly) {
      cy.$('node[is_defi != 1]').style('display', 'none');
      cy.$('node[is_defi = 1]').style('display', 'element');
      // Hide edges not connected to visible nodes
      cy.$('edge').forEach(e => {
        const srcVisible = e.source().style('display') !== 'none';
        const tgtVisible = e.target().style('display') !== 'none';
        e.style('display', srcVisible && tgtVisible ? 'element' : 'none');
      });
    } else {
      // Reset visibility
      cy.$('node').style('display', 'element');
      cy.$('edge').style('display', 'element');
    }

  }, []);

  const startTrace = useCallback(async () => {
    if (!currentAddress) return;

    try {
      const response = await fetch(apiUrl('/api/v1/trace/start'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_address: currentAddress,
          direction: 'both',
          taint_model: 'proportional',
          max_depth: depth[0],
          min_taint_threshold: riskThreshold[0],
          save_to_graph: true,
          enable_native: true,
          enable_token: true,
          enable_bridge: true,
          enable_utxo: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Start polling for trace result completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(apiUrl(`/api/v1/trace/id/${data.trace_id}`));
          if (statusResponse.ok) {
            const resultData = await statusResponse.json();
            // Map to local TraceStatus shape (best-effort)
            const completed = Boolean(resultData?.completed);
            setTraceStatus({
              trace_id: data.trace_id,
              status: completed ? 'completed' : 'running',
              progress: completed ? 1 : 0.5,
              nodes_found: Number(resultData?.total_nodes ?? 0),
              current_hop: Number(resultData?.max_hop_reached ?? 0),
              estimated_completion: undefined,
            });

            if (completed) {
              clearInterval(pollInterval);
              // Reload subgraph with new data
              loadSubgraph();
            }
          }
        } catch (err) {
          console.error('Error polling trace status:', err);
        }
      }, 2000); // Poll every 2 seconds

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start trace');
    }
  }, [currentAddress, depth, riskThreshold, loadSubgraph]);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const apiBase = (import.meta as any)?.env?.VITE_API_URL || window.location.origin;
      const wsBase = apiBase.replace(/^http(s?):\/\//, (m: string, s: string) => (s ? 'wss://' : 'ws://'));
      const wsUrl = `${wsBase.replace(/\/$/, '')}/api/v1/ws`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected for live updates');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'trace_progress') {
            setTraceStatus(message.data);
          } else if (message.type === 'completed') {
            // Trace completed event: refresh graph
            loadSubgraph();
          } else if (message.type === 'enrichment_completed') {
            // Reload graph if relevant address was enriched
            if (message.data.address === currentAddress) {
              loadSubgraph();
            }
          }

        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
      };

    } catch (err) {
      console.error('Error connecting WebSocket:', err);
    }
  }, [currentAddress, loadSubgraph]);

  useEffect(() => {
    initializeCytoscape();

    return () => {
      if (cyInstance.current) {
        cyInstance.current.destroy();
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [initializeCytoscape]);

  // Re-apply DeFi visibility filter when toggled without requiring a reload
  useEffect(() => {
    const cy = cyInstance.current;
    if (!cy) return;
    if (defiOnly) {
      cy.$('node[is_defi != 1]').style('display', 'none');
      cy.$('node[is_defi = 1]').style('display', 'element');
      cy.$('edge').forEach(e => {
        const srcVisible = e.source().style('display') !== 'none';
        const tgtVisible = e.target().style('display') !== 'none';
        e.style('display', srcVisible && tgtVisible ? 'element' : 'none');
      });
    } else {
      cy.$('node').style('display', 'element');
      cy.$('edge').style('display', 'element');
    }
  }, [defiOnly, subgraphData]);

  useEffect(() => {
    if (isLiveMode) {
      connectWebSocket();
    }
  }, [isLiveMode, connectWebSocket]);

  return (
    <div className="h-full flex flex-col space-y-4">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Graph Investigation Controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="address">Starting Address</Label>
              <Input
                id="address"
                value={currentAddress}
                onChange={(e) => setCurrentAddress(e.target.value)}
                placeholder="0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
              />
            </div>

            <div className="space-y-2">
              <Label>Traversal Depth</Label>
              <Slider
                value={depth}
                onValueChange={setDepth}
                min={1}
                max={10}
                step={1}
                className="w-full"
              />
              <div className="text-sm text-muted-foreground">Current: {depth[0]}</div>
            </div>

            <div className="space-y-2">
              <Label>Risk Threshold</Label>
              <Slider
                value={riskThreshold}
                onValueChange={setRiskThreshold}
                min={0.0}
                max={1.0}
                step={0.1}
                className="w-full"
              />
              <div className="text-sm text-muted-foreground">Current: {riskThreshold[0]}</div>
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="transactions"
                checked={includeTransactions}
                onCheckedChange={setIncludeTransactions}
              />
              <Label htmlFor="transactions">Include Transactions</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="labels"
                checked={includeLabels}
                onCheckedChange={setIncludeLabels}
              />
              <Label htmlFor="labels">Include Labels</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="defiOnly"
                checked={defiOnly}
                onCheckedChange={setDefiOnly}
              />
              <Label htmlFor="defiOnly">DeFi only</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="live"
                checked={isLiveMode}
                onCheckedChange={setIsLiveMode}
              />
              <Label htmlFor="live">Live Mode</Label>
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={loadSubgraph} disabled={isLoading || !currentAddress}>
              {isLoading ? 'Loading...' : 'Load Subgraph'}
            </Button>

            <Button onClick={startTrace} disabled={!currentAddress} variant="outline">
              <Play className="w-4 h-4 mr-2" />
              Start Trace
            </Button>

            <Button onClick={() => cyInstance.current?.fit()} variant="outline">
              <Maximize className="w-4 h-4 mr-2" />
              Fit to View
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Graph Visualization */}
      <Card className="flex-1">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Graph Visualization
            {subgraphData && (
              <Badge variant="secondary">
                {subgraphData.total_nodes} nodes, {subgraphData.total_edges} edges
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="h-full">
          {error && (
            <div className="flex items-center space-x-2 text-destructive mb-4">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}

          <div
            ref={cyRef}
            className="w-full h-full border rounded-lg bg-gray-50"
            style={{ minHeight: '400px' }}
          />

          {/* Legend */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
              <span>Low Risk</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
              <span>Medium Risk</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded-full bg-red-500"></div>
              <span>High Risk</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded-full bg-red-800"></div>
              <span>Critical Risk</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded-full border-4 border-violet-600"></div>
              <span>DeFi Highlight</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trace Status */}
      {traceStatus && (
        <Card>
          <CardHeader>
            <CardTitle>Trace Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Status: {traceStatus.status}</span>
                <span>{Math.round(traceStatus.progress * 100)}%</span>
              </div>

              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${traceStatus.progress * 100}%` }}
                ></div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>Nodes Found: {traceStatus.nodes_found}</div>
                <div>Current Hop: {traceStatus.current_hop}</div>
                <div>Est. Completion: {traceStatus.estimated_completion || 'N/A'}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
