import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import html2canvas from 'html2canvas';
import { useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import jsPDF from 'jspdf';

// Components
import { GraphHeader } from '@/components/investigator/GraphHeader';
import { AddressSearchPanel } from '@/components/investigator/AddressSearchPanel';
import { GraphSettingsPanel } from '@/components/investigator/GraphSettingsPanel';
import { NodeDetailsPanel } from '@/components/investigator/NodeDetailsPanel';
import { PatternFindings } from '@/components/investigator/PatternFindings';
import { NetworkMetricsPanel } from '@/components/investigator/NetworkMetricsPanel';
import { TimelinePanel } from '@/components/investigator/TimelinePanel';
import { ConnectedAddresses } from '@/components/investigator/ConnectedAddresses';
import { PathResults } from '@/components/investigator/PathResults';
import { GraphVisualization } from '@/components/investigator/GraphVisualization';
import { ActionsPanel } from '@/components/investigator/ActionsPanel';

import type {
  LocalGraph,
  GraphControls,
  TimelineEvent,
  GraphNode,
} from '@/components/investigator/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface GraphV2PathStep {
  from_address: string;
  to_address: string;
  from_chain: string;
  to_chain: string;
  amount?: number;
  tx_hash?: string;
  timestamp?: string;
  fee?: number;
  risk_score?: number;
  edge_cost?: number;
}

interface GraphV2PathResult {
  path: GraphV2PathStep[];
  total_cost?: number;
  hops?: number;
  meeting_point?: string;
}

interface GraphV2FindPathsResponse {
  source: string;
  target: string;
  paths: GraphV2PathResult[];
  execution_time_ms?: number;
  total_paths_found?: number;
  algorithm?: string;
}

interface PathSummary {
  source: string;
  target: string;
  hops: number;
  totalAmount: number;
  maxRiskPercent: number;
  bridges: string[];
  executionTimeMs?: number;
  totalPathsFound?: number;
  algorithm?: string;
}

interface GraphV2SubgraphNode {
  address: string;
  chain: string;
  risk_score: number;
  risk_level?: string;
  labels: string[];
  tx_count: number;
  balance: number;
  first_seen?: string | null;
  last_seen?: string | null;
  [key: string]: unknown;
}

interface GraphV2SubgraphLink {
  source: string;
  target: string;
  value: number;
  timestamp?: string;
  tx_hash?: string;
  event_type?: string;
  bridge?: boolean;
  risk_score?: number;
  source_chain?: string;
  target_chain?: string;
  fee?: number;
  [key: string]: unknown;
}

interface GraphV2SubgraphResponse {
  nodes: Record<string, GraphV2SubgraphNode>;
  links: GraphV2SubgraphLink[];
  summary?: Record<string, unknown>;
}

const _riskLevelFromScore = (score: number): string => {
  if (score >= 0.8) return 'CRITICAL';
  if (score >= 0.6) return 'HIGH';
  if (score >= 0.3) return 'MEDIUM';
  if (score >= 0.1) return 'LOW';
  return 'SAFE';
};

// Compute SHA-256 hash of a string (hex)
async function computeSHA256(input: string): Promise<string> {
  const enc = new TextEncoder();
  const data = enc.encode(input);
  const hashBuf = await crypto.subtle.digest('SHA-256', data);
  const bytes = Array.from(new Uint8Array(hashBuf));
  return bytes.map((b) => b.toString(16).padStart(2, '0')).join('');
}

const InvestigatorGraphPage: React.FC = () => {
  const location = useLocation();
  const queryClient = useQueryClient();

  // State
  const [selectedAddress, setSelectedAddress] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [maxHops, setMaxHops] = useState<number>(3);
  const [includeBridges, setIncludeBridges] = useState<boolean>(true);
  const [minTaint, setMinTaint] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [timeRange, setTimeRange] = useState<{ from: string; to: string }>({ from: '', to: '' });
  const [localGraph, setLocalGraph] = useState<LocalGraph | null>(null);
  const [graphControls, setGraphControls] = useState<GraphControls | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<string[]>([]);
  const [highlightedPath, setHighlightedPath] = useState<string[] | undefined>(undefined);
  const [freezeLayout, setFreezeLayout] = useState<boolean>(false);
  const [hiddenRiskLevels] = useState<Set<string>>(new Set());
  const [lastSnapshotHash, setLastSnapshotHash] = useState<string | null>(null);
  const [pathRiskThreshold, setPathRiskThreshold] = useState<number>(() => {
    const stored = localStorage.getItem('investigator:pathRiskThreshold');
    return stored ? Math.max(0, Math.min(100, parseInt(stored) || 70)) : 70;
  });
  const [pathMinAmount, setPathMinAmount] = useState<number>(() => {
    const stored = localStorage.getItem('investigator:pathMinAmount');
    return stored ? Math.max(0, parseFloat(stored) || 0) : 0;
  });
  const [pathTimeWindowDays, setPathTimeWindowDays] = useState<number>(() => {
    const stored = localStorage.getItem('investigator:pathTimeWindowDays');
    return stored ? Math.max(1, Math.min(3650, parseInt(stored) || 365)) : 365;
  });
  const [pathAlgorithm, setPathAlgorithm] = useState<'astar' | 'bidirectional'>(() => {
    const stored = localStorage.getItem('investigator:pathAlgorithm');
    return stored === 'bidirectional' ? 'bidirectional' : 'astar';
  });
  const lastActionApplied = useRef<string>('');
  const graphContainerRef = useRef<HTMLDivElement>(null);

  // Restore persisted settings
  useEffect(() => {
    try {
      const sMaxHops = localStorage.getItem('investigator:maxHops');
      if (sMaxHops) setMaxHops(Math.max(1, Math.min(10, parseInt(sMaxHops) || 3)));
      const sInclude = localStorage.getItem('investigator:includeBridges');
      if (sInclude !== null) setIncludeBridges(sInclude === '1');
      const sMinTaint = localStorage.getItem('investigator:minTaint');
      if (sMinTaint) setMinTaint(Math.max(0, Math.min(100, parseInt(sMinTaint) || 0)));
    } catch {}
  }, []);

  // Persist settings
  useEffect(() => {
    try {
      localStorage.setItem('investigator:maxHops', String(maxHops));
    } catch {}
  }, [maxHops]);
  useEffect(() => {
    try {
      localStorage.setItem('investigator:includeBridges', includeBridges ? '1' : '0');
    } catch {}
  }, [includeBridges]);
  useEffect(() => {
    try {
      localStorage.setItem('investigator:minTaint', String(minTaint));
    } catch {}
  }, [minTaint]);
  useEffect(() => {
    try {
      localStorage.setItem('investigator:pathRiskThreshold', String(pathRiskThreshold));
    } catch {}
  }, [pathRiskThreshold]);
  useEffect(() => {
    try {
      localStorage.setItem('investigator:pathMinAmount', String(pathMinAmount));
    } catch {}
  }, [pathMinAmount]);
  useEffect(() => {
    try {
      localStorage.setItem('investigator:pathTimeWindowDays', String(pathTimeWindowDays));
    } catch {}
  }, [pathTimeWindowDays]);
  useEffect(() => {
    try {
      localStorage.setItem('investigator:pathAlgorithm', pathAlgorithm);
    } catch {}
  }, [pathAlgorithm]);

  // Read address from query param for deep-linking
  useEffect(() => {
    const sp = new URLSearchParams(location.search);
    const qAddr = (sp.get('address') || '').trim();
    const autoTrace = sp.get('auto_trace') === 'true';

    if (qAddr && qAddr !== selectedAddress) {
      setSelectedAddress(qAddr);
      if (autoTrace) {
        console.log(`🚀 Auto-Trace aktiviert für ${qAddr}`);
      }
    }
  }, [location.search, selectedAddress]);

  // Fetch graph data
  const { data: graphData, isLoading: graphLoading } = useQuery({
    queryKey: ['investigatorGraph', selectedAddress, maxHops, includeBridges, timeRange, minTaint],
    queryFn: async () => {
      if (!selectedAddress) return null;

      const riskThreshold = Math.max(0, Math.min(1, (minTaint || 0) / 100));
      const timeWindowDays = (() => {
        const fromTs = timeRange.from ? Date.parse(timeRange.from) : undefined;
        const toTs = timeRange.to ? Date.parse(timeRange.to) : undefined;
        if (Number.isFinite(fromTs) && Number.isFinite(toTs) && fromTs! < toTs!) {
          const diffMs = toTs! - fromTs!;
          return Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
        }
        if (Number.isFinite(fromTs) && !Number.isFinite(toTs)) {
          const diffMs = Date.now() - (fromTs as number);
          return Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
        }
        return 365;
      })();

      const params = new URLSearchParams({
        address: selectedAddress,
        max_hops: String(maxHops),
        risk_threshold: String(riskThreshold),
        min_amount: '0',
        time_window_days: String(timeWindowDays),
        include_bridges: includeBridges ? 'true' : 'false',
        max_nodes: '500',
        max_edges: '1000',
      });

      const response = await axios.get<GraphV2SubgraphResponse>(`${API_BASE_URL}/api/v1/graph-v2/subgraph?${params.toString()}`);
      const data = response.data;

      const nodesRecord = Object.entries(data.nodes || {}).reduce((acc: Record<string, any>, [key, node]) => {
        const id = key || node.address;
        if (!id) return acc;
        acc[id] = {
          id,
          address: node.address || id,
          chain: node.chain || 'unknown',
          risk_score: node.risk_score ?? 0,
          risk_level: node.risk_level || _riskLevelFromScore(node.risk_score ?? 0),
          labels: node.labels || [],
          tx_count: node.tx_count ?? 0,
          balance: node.balance ?? 0,
          first_seen: node.first_seen || '',
          last_seen: node.last_seen || '',
        };
        return acc;
      }, {} as Record<string, any>);

      const links = (data.links || []).map((link) => ({
        source: link.source,
        target: link.target,
        tx_hash: link.tx_hash || '',
        value: link.value ?? 0,
        timestamp: link.timestamp || '',
        event_type: link.event_type || (link.bridge ? 'BRIDGE_LINK' : 'TRANSACTION'),
        bridge: link.bridge ?? (link.source_chain && link.target_chain && link.source_chain !== link.target_chain),
        risk_score: link.risk_score ?? 0,
      }));

      return { nodes: nodesRecord, links };
    },
    enabled: !!selectedAddress,
  });

  // Sync localGraph with fetched data
  useEffect(() => {
    if (graphData && (graphData as any).nodes && (graphData as any).links) {
      setLocalGraph(graphData as any);
    } else if (!selectedAddress) {
      setLocalGraph(null);
    }
  }, [graphData, selectedAddress]);

  // Update breadcrumbs
  useEffect(() => {
    if (!selectedAddress) {
      setBreadcrumbs([]);
      return;
    }
    setBreadcrumbs((prev: string[]) => {
      if (prev.length === 0) return [selectedAddress];
      if (prev[prev.length - 1] === selectedAddress) return prev;
      return [...prev, selectedAddress];
    });
  }, [selectedAddress]);

  // Fetch timeline
  const { data: timelineData } = useQuery({
    queryKey: ['timeline', selectedAddress, timeRange],
    queryFn: async () => {
      if (!selectedAddress) return [];
      const params = new URLSearchParams({ address: selectedAddress });
      if (timeRange.from) params.set('from_timestamp', timeRange.from);
      if (timeRange.to) params.set('to_timestamp', timeRange.to);
      const response = await axios.get(`${API_BASE_URL}/api/v1/graph/timeline?${params}`);
      return response.data.events || [];
    },
    enabled: !!selectedAddress,
  });

  const timelineEvents = useMemo(() => {
    if (!timelineData) return [];
    return timelineData.map((event: any) => ({
      timestamp: event.timestamp,
      address: event.address,
      event_type: event.event_type,
      value: event.value || 0,
      tx_hash: event.tx_hash,
      risk_score: event.risk_score || 0,
    }));
  }, [timelineData]);

  // Pattern detection mutation
  const patternsMutation = useMutation({
    mutationFn: async () => {
      if (!selectedAddress) return null;
      const params = new URLSearchParams({
        address: selectedAddress,
        max_depth: String(maxHops),
        min_value: '0',
        lookback_hours: '168',
      });
      const res = await axios.get(`${API_BASE_URL}/api/v1/patterns/detect?${params}`);
      return res.data;
    },
  });

  // Find path mutation
  const findPathMutation = useMutation<GraphV2FindPathsResponse, unknown, { source: string; target: string }>({
    mutationFn: async ({ source, target }) => {
      const response = await axios.post(`${API_BASE_URL}/api/v1/graph-v2/find-paths`, {
        source,
        target,
        constraints: {
          max_hops: maxHops,
          min_amount: pathMinAmount,
          risk_threshold: Math.max(0, Math.min(1, pathRiskThreshold / 100)),
          time_window_days: pathTimeWindowDays,
        },
        cost_function: {},
        algorithm: pathAlgorithm,
        max_paths: 3,
      });
      return response.data;
    },
  });

  // Cluster mutation
  const clusterMutation = useMutation({
    mutationFn: async (addresses: string[]) => {
      const response = await axios.post(`${API_BASE_URL}/api/v1/graph/cluster/build`, {
        addresses,
        depth: 3,
      });
      return response.data;
    },
  });

  // Expand neighbors mutation
  const expandNeighborsMutation = useMutation({
    mutationFn: async (address: string) => {
      setFreezeLayout(true);
      const params = new URLSearchParams({
        address,
        depth: '1',
        include_transactions: 'true',
        include_labels: 'true',
        risk_threshold: String(Math.max(0, Math.min(1, (minTaint || 0) / 100))),
      });
      const response = await axios.get(`${API_BASE_URL}/api/v1/graph/subgraph?${params}`);
      const raw = response.data || {};
      const nodesArr: any[] = Array.isArray(raw.nodes) ? raw.nodes : [];
      const linksArr: any[] = Array.isArray(raw.edges || raw.links) ? raw.edges || raw.links : [];
      const nodesRecord = nodesArr.reduce((acc: Record<string, any>, n: any) => {
        const key = n.address || n.id;
        if (key)
          acc[key] = {
            id: n.id || key,
            address: n.address || key,
            chain: n.chain || n.network || 'evm',
            taint_score: n.taint_received ?? n.taint ?? 0,
            risk_level: n.risk_level || 'LOW',
            labels: n.labels || [],
            tx_count: n.tx_count || 0,
            balance: n.balance || 0,
            first_seen: n.first_seen || '',
            last_seen: n.last_seen || '',
          };
        return acc;
      }, {} as Record<string, any>);
      const links = linksArr.map((e: any) => ({
        source: e.source || e.from || e.src || e.id?.split('_')?.[0],
        target: e.target || e.to || e.dst || e.id?.split('_')?.[1],
        tx_hash: e.tx_hash || e.txid || '',
        value: e.value ?? 0,
        timestamp: e.timestamp || '',
        event_type: e.type || 'transaction',
        bridge: e.type === 'BRIDGE_LINK' ? e.bridge || 'bridge' : undefined,
      }));
      return { nodes: nodesRecord, links };
    },
    onSuccess: (subgraph) => {
      setLocalGraph((prev) => {
        const base = prev || { nodes: {}, links: [] };
        return {
          nodes: { ...base.nodes, ...(subgraph as any).nodes },
          links: [...base.links, ...(subgraph as any).links],
        };
      });
      try {
        graphControls?.centerOn(selectedAddress);
      } catch {}
    },
    onSettled: () => {
      setFreezeLayout(false);
    },
  });

  // Update highlighted path when mutation returns
  useEffect(() => {
    const first = findPathMutation.data?.paths?.[0];
    if (first?.path && first.path.length > 0) {
      const sequence = [first.path[0].from_address, ...first.path.map((step) => step.to_address)];
      setHighlightedPath(sequence);
    } else {
      setHighlightedPath(undefined);
    }
  }, [findPathMutation.data]);

  const pathSummary = useMemo<PathSummary | null>(() => {
    if (!findPathMutation.data?.paths || findPathMutation.data.paths.length === 0) {
      return null;
    }
    const first = findPathMutation.data.paths[0];
    const steps = first.path || [];
    const hops = first.hops ?? steps.length;
    const totalAmount = steps.reduce((acc, step) => acc + (step.amount ?? 0), 0);
    const maxRisk = steps.reduce((acc, step) => Math.max(acc, step.risk_score ?? 0), 0);
    const bridges = Array.from(
      new Set(
        steps
          .filter((step) => step.from_chain && step.to_chain && step.from_chain !== step.to_chain)
          .map((step) => `${step.from_chain.toUpperCase()} → ${step.to_chain.toUpperCase()}`)
      )
    );

    return {
      source: findPathMutation.data.source,
      target: findPathMutation.data.target,
      hops,
      totalAmount,
      maxRiskPercent: Math.round(maxRisk * 100),
      bridges,
      executionTimeMs: findPathMutation.data.execution_time_ms,
      totalPathsFound: findPathMutation.data.total_paths_found,
      algorithm: findPathMutation.data.algorithm,
    };
  }, [findPathMutation.data]);

  // Network Metrics
  const networkMetrics = useMemo(() => {
    if (!localGraph || !localGraph.nodes) return null;
    const nodeCount = Object.keys(localGraph.nodes).length;
    const linkCount = localGraph.links?.length || 0;
    const maxPossibleLinks = (nodeCount * (nodeCount - 1)) / 2;
    const density = maxPossibleLinks > 0 ? (linkCount / maxPossibleLinks) * 100 : 0;

    const highRiskNodes = Object.entries(localGraph.nodes)
      .filter(([_, node]: [string, any]) => node.risk_level === 'HIGH' || node.risk_level === 'CRITICAL')
      .slice(0, 5)
      .map(([addr, node]: [string, any]) => ({ address: addr, risk: node.risk_level, taint: node.taint_score }));

    return { density, nodeCount, linkCount, highRiskNodes };
  }, [localGraph]);

  // Filtered graph
  const filteredGraph = useMemo(() => {
    if (!localGraph) return null;
    const nodes: Record<string, any> = {};

    for (const [addr, n] of Object.entries(localGraph.nodes)) {
      const pct = (n as any).taint_score ? ((n as any).taint_score as number) * 100 : 0;
      const riskLevel = (n as any).risk_level || 'LOW';

      if (minTaint && pct < minTaint) continue;
      if (hiddenRiskLevels.has(riskLevel)) continue;

      nodes[addr] = n;
    }

    const allowed = new Set(Object.keys(nodes));
    const links = (localGraph.links || []).filter((l: any) => allowed.has(l.source) && allowed.has(l.target));
    return { nodes, links };
  }, [localGraph, minTaint, hiddenRiskLevels]);

  // Handlers
  const handleAddressSearch = useCallback(() => {
    if (searchQuery.trim()) {
      setSelectedAddress(searchQuery.trim());
    }
  }, [searchQuery]);

  const handleClusterAddresses = useCallback(() => {
    if (localGraph?.nodes) {
      const addresses = Object.keys(localGraph.nodes);
      if (addresses.length > 0) {
        clusterMutation.mutate(addresses);
      }
    }
  }, [localGraph, clusterMutation]);

  const handleFindPath = useCallback(
    (targetAddress: string) => {
      if (selectedAddress && targetAddress) {
        findPathMutation.mutate({ source: selectedAddress, target: targetAddress });
      }
    },
    [selectedAddress, findPathMutation]
  );

  const handleAskAssistant = useCallback(() => {
    const subject = selectedAddress || breadcrumbs[breadcrumbs.length - 1] || '';
    const prompt = subject
      ? `Analysiere bitte die Adresse ${subject}: Risk Score, auffällige Muster (Peel Chain, Rapid Movement), Bridges und empfohlene Maßnahmen.`
      : 'Ich brauche Hilfe bei der Graph-Analyse: Bitte erkläre mir Risk Scores und mögliche Muster.';
    try {
      window.dispatchEvent(new CustomEvent('assistant.ask', { detail: { text: prompt } }));
    } catch {}
  }, [selectedAddress, breadcrumbs]);

  const handleAiTracePath = useCallback(() => {
    if (!selectedAddress) return;
    const prompt = `Führe eine Pfadsuche ab ${selectedAddress} durch (Richtung beide Richtungen, max_depth=${maxHops}). Falls es sich um eine Bitcoin-Adresse (bc1/1/3) handelt, berücksichtige UTXO-Flows. Aggregiere die wichtigsten Pfade (Top 3), nenne Hops, Gesamtwert, wesentliche Knoten (z. B. Börsen/Mixer) und markiere eventuelle Cross-Chain-Bridges. Gib eine kurze Handlungsempfehlung.`;
    try {
      window.dispatchEvent(new CustomEvent('assistant.ask', { detail: { text: prompt } }));
    } catch {}
  }, [selectedAddress, maxHops]);

  const handleAiMonitorAddress = useCallback(() => {
    if (!selectedAddress) return;
    const prompt = `Richte für ${selectedAddress} eine Monitoring-Strategie ein: liste aktive Alert-Regeln auf, schlage passende Regeln vor (z. B. high_risk ab 0.7, large_transfer > $50k, sanctioned/mixer Labels) und simuliere Alerts (mit Beispiel-Event). Erkläre, wie Webhooks/Benachrichtigungen angebunden werden.`;
    try {
      window.dispatchEvent(new CustomEvent('assistant.ask', { detail: { text: prompt } }));
    } catch {}
  }, [selectedAddress]);

  const handleBreadcrumbClick = useCallback(
    (index: number) => {
      setBreadcrumbs((prev) => prev.slice(0, index + 1));
      const addr = breadcrumbs[index];
      if (addr) {
        setSelectedAddress(addr);
        graphControls?.centerOn(addr);
      }
    },
    [breadcrumbs, graphControls]
  );

  const exportTimelineCSV = () => {
    if (!timelineEvents || timelineEvents.length === 0) return;
    const headers = ['timestamp', 'address', 'event_type', 'value', 'tx_hash', 'risk_score'];
    const rows = timelineEvents.map((e: TimelineEvent) => [
      e.timestamp,
      e.address,
      e.event_type,
      String(e.value ?? ''),
      e.tx_hash ?? '',
      String(e.risk_score ?? ''),
    ]);
    const csv = [headers, ...rows]
      .map((r: (string | number)[]) => r.map((v: string | number) => String(v).replace(/"/g, '""')).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `timeline_${selectedAddress || 'address'}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSaveSnapshot = useCallback(() => {
    const base = {
      timestamp: new Date().toISOString(),
      selectedAddress,
      maxHops,
      includeBridges,
      timeRange,
      highlightedPath,
      nodes: localGraph?.nodes,
      links: localGraph?.links,
    };
    const blob = new Blob([JSON.stringify(base, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `snapshot_${selectedAddress?.slice(0, 8) || 'graph'}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [selectedAddress, maxHops, includeBridges, timeRange, highlightedPath, localGraph]);

  const handleExportPDF = useCallback(async () => {
    const container = graphContainerRef.current;
    if (!container) return;
    const canvas = container.querySelector('canvas') as HTMLCanvasElement | null;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/png');

    const pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();

    const img = new Image();
    await new Promise((res) => {
      img.onload = res as any;
      img.src = dataUrl;
    });
    const ratio = Math.min(pageWidth / img.width, (pageHeight - 120) / img.height);
    const imgW = img.width * ratio;
    const imgH = img.height * ratio;
    const x = (pageWidth - imgW) / 2;
    const y = 80;

    pdf.setFontSize(16);
    pdf.text('Investigation Graph Snapshot', 40, 30);
    pdf.setFontSize(10);
    pdf.text(`Address: ${selectedAddress || '-'}`, 40, 48);
    pdf.text(`Time: ${new Date().toISOString()}`, 40, 62);

    pdf.addImage(dataUrl, 'PNG', x, y, imgW, imgH);

    pdf.setFontSize(9);
    const meta = `Hops=${maxHops}  Bridges=${includeBridges ? 'on' : 'off'}  PathLen=${highlightedPath?.length || 0}`;
    pdf.text(meta, 40, pageHeight - 24);
    let hash = lastSnapshotHash;
    if (!hash) {
      const base = {
        timestamp: new Date().toISOString(),
        selectedAddress,
        maxHops,
        includeBridges,
        timeRange,
        highlightedPath,
        graph: localGraph,
      };
      const json = JSON.stringify(base);
      hash = await computeSHA256(json);
      setLastSnapshotHash(hash);
    }
    pdf.text(`SHA-256: ${hash}`, 40, pageHeight - 10);

    pdf.save(`investigation_${selectedAddress?.slice(0, 8) || 'graph'}_${Date.now()}.pdf`);
  }, [selectedAddress, maxHops, includeBridges, highlightedPath, localGraph, lastSnapshotHash]);

  const handleExportPNG = useCallback(async () => {
    const el = graphContainerRef.current;
    if (!el) return;
    const canvas = await html2canvas(el, { backgroundColor: '#ffffff', scale: 2 });
    const dataUrl = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = `investigation_${selectedAddress?.slice(0, 8) || 'graph'}_${Date.now()}.png`;
    a.click();
  }, [graphContainerRef, selectedAddress]);

  const openTxExplorer = (tx: string, chain: string = 'ethereum') => {
    const explorers: Record<string, string> = {
      ethereum: `https://etherscan.io/tx/${tx}`,
      polygon: `https://polygonscan.com/tx/${tx}`,
      arbitrum: `https://arbiscan.io/tx/${tx}`,
      optimism: `https://optimistic.etherscan.io/tx/${tx}`,
      base: `https://basescan.org/tx/${tx}`,
    };
    window.open(explorers[chain] || explorers.ethereum, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <GraphHeader localGraph={localGraph} timelineEvents={timelineEvents} />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Controls Panel (Sidebar) */}
          <div className="lg:col-span-1 space-y-5">
            <AddressSearchPanel
              searchQuery={searchQuery}
              onSearchQueryChange={setSearchQuery}
              onSearch={handleAddressSearch}
            />

            {selectedAddress && localGraph?.nodes?.[selectedAddress] && (
              <NodeDetailsPanel
                selectedAddress={selectedAddress}
                node={localGraph.nodes[selectedAddress] as GraphNode}
                graphControls={graphControls}
                onPatternDetect={() => patternsMutation.mutate()}
                onAiTracePath={handleAiTracePath}
                onAiMonitor={handleAiMonitorAddress}
                onFindPath={handleFindPath}
                patternsPending={patternsMutation.isPending}
              />
            )}

            {patternsMutation.data?.findings?.length > 0 && (
              <PatternFindings findings={patternsMutation.data.findings} onOpenTx={openTxExplorer} />
            )}

            {networkMetrics && (
              <NetworkMetricsPanel
                density={networkMetrics.density}
                nodeCount={networkMetrics.nodeCount}
                linkCount={networkMetrics.linkCount}
                highRiskNodes={networkMetrics.highRiskNodes}
                onSelectAddress={setSelectedAddress}
                graphControls={graphControls}
              />
            )}

            <GraphSettingsPanel
              maxHops={maxHops}
              onMaxHopsChange={setMaxHops}
              includeBridges={includeBridges}
              onIncludeBridgesChange={setIncludeBridges}
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
              minTaint={minTaint}
              onMinTaintChange={setMinTaint}
              pathRiskThreshold={pathRiskThreshold}
              onPathRiskThresholdChange={setPathRiskThreshold}
              pathMinAmount={pathMinAmount}
              onPathMinAmountChange={setPathMinAmount}
              pathTimeWindowDays={pathTimeWindowDays}
              onPathTimeWindowDaysChange={setPathTimeWindowDays}
              pathAlgorithm={pathAlgorithm}
              onPathAlgorithmChange={setPathAlgorithm}
            />

            <ActionsPanel
              localGraph={localGraph}
              isPlaying={isPlaying}
              clusterPending={clusterMutation.isPending}
              onCluster={handleClusterAddresses}
              onTogglePlay={() => setIsPlaying(!isPlaying)}
            />

            {pathSummary && (
              <PathResults
                summary={pathSummary}
                rawPaths={findPathMutation.data?.paths}
                isLoading={findPathMutation.isPending}
              />
            )}
          </div>

          {/* Main Graph Area */}
          <div className="lg:col-span-3 space-y-5">
            <div ref={graphContainerRef}>
              <GraphVisualization
                localGraph={localGraph}
                graphLoading={graphLoading}
                selectedAddress={selectedAddress}
                highlightedPath={highlightedPath}
                freezeLayout={freezeLayout}
                lastSnapshotHash={lastSnapshotHash}
                breadcrumbs={breadcrumbs}
                onNodeClick={(node: any) => {
                  setSelectedAddress(node.address);
                  graphControls?.centerOn(node.address);
                }}
                onReady={setGraphControls}
                onZoomIn={() => graphControls?.zoomIn()}
                onZoomOut={() => graphControls?.zoomOut()}
                onZoomToFit={() => graphControls?.zoomToFit()}
                onClearPath={() => setHighlightedPath(undefined)}
                onExportPNG={handleExportPNG}
                onExportPDF={handleExportPDF}
                onSaveSnapshot={handleSaveSnapshot}
                onOpenVerify={() => {}}
                onAskAssistant={handleAskAssistant}
                onBreadcrumbClick={handleBreadcrumbClick}
                graphControls={graphControls}
              />
            </div>

            <TimelinePanel events={timelineEvents} onExportCSV={exportTimelineCSV} />

            {filteredGraph && (
              <ConnectedAddresses
                filteredGraph={filteredGraph}
                selectedAddress={selectedAddress}
                highlightedPath={highlightedPath}
                onSelectAddress={setSelectedAddress}
                onFindPath={handleFindPath}
                onExpandNeighbors={(addr) => expandNeighborsMutation.mutate(addr)}
                graphControls={graphControls}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvestigatorGraphPage;
