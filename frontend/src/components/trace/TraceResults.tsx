'use client';

import React, { useCallback, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ExternalLink, Search, AlertTriangle } from 'lucide-react';
import { FixedSizeList as List } from 'react-window';

interface Node {
  address: string;
  risk_score?: number;
  labels?: string[];
  taint?: number;
}

interface Edge {
  from: string;
  to: string;
  value: number;
  tx_hash: string;
}

interface TraceData {
  nodes: Node[];
  edges: Edge[];
  sanctioned_addresses: string[];
}

interface TraceResultsProps {
  data: TraceData;
}

export function TraceResults({ data }: TraceResultsProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'risk' | 'taint' | 'address'>('risk');
  const [visibleCount, setVisibleCount] = useState(100);

  // Filter and sort nodes
  const filteredNodes = data.nodes
    .filter((node) =>
      node.address.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'risk') {
        return (b.risk_score || 0) - (a.risk_score || 0);
      } else if (sortBy === 'taint') {
        return (b.taint || 0) - (a.taint || 0);
      } else {
        return a.address.localeCompare(b.address);
      }
    });

  const visibleNodes = filteredNodes.slice(0, visibleCount);
  const useVirtualization = filteredNodes.length > 300;

  const rowHeight = 48;
  const itemKey = useCallback((index: number) => filteredNodes[index]?.address ?? index, [filteredNodes]);

  const Row = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const node = filteredNodes[index];
    const isSanctioned = data.sanctioned_addresses.includes(node.address);
    return (
      <div
        style={style}
        role="row"
        aria-rowindex={index + 1}
        className={`flex items-center border-b px-3 ${isSanctioned ? 'bg-red-50 dark:bg-red-950' : 'bg-card'}`}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openBlockExplorer(node.address);
          }
        }}
        tabIndex={0}
        aria-label={`Adresse ${node.address} öffnen`}
      >
        <div className="w-2/5 font-mono text-xs truncate flex items-center gap-2" title={node.address}>
          {isSanctioned && <AlertTriangle className="w-4 h-4 text-red-600" />}
          {node.address}
        </div>
        <div className="w-1/5">{getRiskBadge(node.risk_score)}</div>
        <div className="w-1/5">
          {node.taint ? (
            <span className="font-semibold">{(node.taint * 100).toFixed(2)}%</span>
          ) : (
            <span className="text-muted-foreground">N/A</span>
          )}
        </div>
        <div className="w-1/5 flex justify-end">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => openBlockExplorer(node.address)}
            aria-label={`Adresse im Blockexplorer öffnen: ${node.address}`}
            title="Im Blockexplorer öffnen"
          >
            <ExternalLink className="w-4 h-4" aria-hidden />
          </Button>
        </div>
      </div>
    );
  }, [filteredNodes, data.sanctioned_addresses]);

  const exportToCSV = () => {
    const headers = ['address', 'risk_score', 'taint', 'labels'];
    const rows = filteredNodes.map((n) => [
      n.address,
      n.risk_score ?? '',
      n.taint ?? '',
      (n.labels || []).join('|'),
    ]);
    const csv = [headers, ...rows]
      .map((r) => r.map((v) => `${String(v).replace(/"/g, '""')}`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trace_results_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getRiskBadge = (score?: number) => {
    if (!score) return <Badge variant="secondary">Unknown</Badge>;
    
    if (score >= 0.9)
      return <Badge className="bg-red-100 text-red-800 border-red-200">Critical</Badge>;
    if (score >= 0.6)
      return <Badge className="bg-orange-100 text-orange-800 border-orange-200">High</Badge>;
    if (score >= 0.3)
      return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Medium</Badge>;
    return <Badge className="bg-green-100 text-green-800 border-green-200">Low</Badge>;
  };

  const openBlockExplorer = (address: string, chain: string = 'ethereum') => {
    const explorers: Record<string, string> = {
      ethereum: `https://etherscan.io/address/${address}`,
      bitcoin: `https://blockchair.com/bitcoin/address/${address}`,
      polygon: `https://polygonscan.com/address/${address}`,
      arbitrum: `https://arbiscan.io/address/${address}`,
      optimism: `https://optimistic.etherscan.io/address/${address}`,
    };
    
    window.open(explorers[chain] || explorers.ethereum, '_blank');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trace Results</CardTitle>
        <CardDescription>
          {filteredNodes.length} Adressen gefunden
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search and Sort */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Suche nach Adresse..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2 items-center">
            <Button
              size="sm"
              variant={sortBy === 'risk' ? 'default' : 'outline'}
              onClick={() => setSortBy('risk')}
            >
              Risk
            </Button>
            <Button
              size="sm"
              variant={sortBy === 'taint' ? 'default' : 'outline'}
              onClick={() => setSortBy('taint')}
            >
              Taint
            </Button>
            <Button
              size="sm"
              variant={sortBy === 'address' ? 'default' : 'outline'}
              onClick={() => setSortBy('address')}
            >
              Address
            </Button>
            <Button size="sm" variant="outline" onClick={exportToCSV} aria-label="Ergebnisse als CSV exportieren" title="CSV Export">
              CSV Export
            </Button>
          </div>
        </div>

        {/* Results Table or Virtualized List */}
        {useVirtualization ? (
          <div className="border rounded-lg overflow-hidden" role="table" aria-label="Trace Results">
            <div className="flex items-center px-3 py-2 bg-muted text-sm font-medium" role="row">
              <div className="w-2/5">Address</div>
              <div className="w-1/5">Risk</div>
              <div className="w-1/5">Taint</div>
              <div className="w-1/5 text-right">Actions</div>
            </div>
            <List
              height={Math.min(12, Math.ceil(filteredNodes.length / 2)) * rowHeight}
              itemCount={filteredNodes.length}
              itemSize={rowHeight}
              width={'100%'}
              itemKey={itemKey}
            >
              {Row}
            </List>
          </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <Table id="trace-results-table">
              <caption className="sr-only">Ergebnisliste der Trace-Analyse mit Adressen, Risiko, Taint und Labels</caption>
              <TableHeader>
                <TableRow>
                  <TableHead>Address</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Taint</TableHead>
                  <TableHead>Labels</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visibleNodes.map((node) => {
                  const isSanctioned = data.sanctioned_addresses.includes(node.address);
                  return (
                    <TableRow
                      key={node.address}
                      className={isSanctioned ? 'bg-red-50 dark:bg-red-950' : ''}
                      role="button"
                      tabIndex={0}
                      aria-label={`Adresse ${node.address} öffnen`}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          openBlockExplorer(node.address);
                        }
                      }}
                    >
                      <TableCell className="font-mono text-xs">
                        <div className="flex items-center gap-2">
                          {isSanctioned && (
                            <AlertTriangle className="w-4 h-4 text-red-600" />
                          )}
                          <span className="truncate max-w-[200px]" title={node.address}>
                            {node.address}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getRiskBadge(node.risk_score)}
                      </TableCell>
                      <TableCell>
                        {node.taint ? (
                          <span className="font-semibold">
                            {(node.taint * 100).toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                          {node.labels && node.labels.length > 0 ? (
                            node.labels.slice(0, 2).map((label, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {label}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-xs text-muted-foreground">None</span>
                          )}
                          {node.labels && node.labels.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{node.labels.length - 2}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openBlockExplorer(node.address)}
                          aria-label={`Adresse im Blockexplorer öffnen: ${node.address}`}
                          title="Im Blockexplorer öffnen"
                        >
                          <ExternalLink className="w-4 h-4" aria-hidden />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Load More */}
        {filteredNodes.length > visibleNodes.length && (
          <div className="flex items-center justify-center pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setVisibleCount((c) => c + 100)}
              aria-label="Mehr Ergebnisse laden"
            >
              Mehr laden ({visibleNodes.length}/{filteredNodes.length})
            </Button>
          </div>
        )}

        {filteredNodes.length === 0 && (
          <div className="text-center py-10">
            <p className="text-sm text-muted-foreground">Keine Ergebnisse gefunden.</p>
            <p className="text-xs text-muted-foreground">Prüfen Sie den Suchbegriff oder reduzieren Sie die Filter.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
