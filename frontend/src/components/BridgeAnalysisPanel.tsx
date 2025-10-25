import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Network, AlertTriangle, TrendingUp } from 'lucide-react';
import { useAIOrchestrator } from '@/hooks/useAIOrchestrator';

interface BridgeTransfer {
  type: 'incoming' | 'outgoing';
  timestamp: string;
  from_chain: string;
  to_chain: string;
  value_usd: number;
  bridge_name: string;
  tx_hash: string;
  risk_score: number;
}

interface BridgeAnalysisResult {
  address: string;
  primary_chain: string;
  total_bridge_transfers: number;
  total_volume_usd: number;
  chains_involved: string[];
  bridges_used: string[];
  high_risk_count: number;
  risk_factors: string[];
  recent_transfers: BridgeTransfer[];
  analysis_period: {
    from_timestamp?: string;
    to_timestamp?: string;
    min_value_usd?: number;
  };
}

export const BridgeAnalysisPanel: React.FC = () => {
  const [address, setAddress] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [maxDepth, setMaxDepth] = useState(3);
  const [includeIncoming, setIncludeIncoming] = useState(true);
  const [includeOutgoing, setIncludeOutgoing] = useState(true);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [minValue, setMinValue] = useState('');

  const { forensicAction, isExecutingAction, forensicError } = useAIOrchestrator();

  const [result, setResult] = useState<BridgeAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!address.trim()) {
      alert('Bitte geben Sie eine Adresse ein.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await forensicAction('analyze_cross_chain_bridge' as any, {
        address,
        chain,
        max_depth: maxDepth,
        include_incoming: includeIncoming,
        include_outgoing: includeOutgoing,
        from_timestamp: fromDate || undefined,
        to_timestamp: toDate || undefined,
        min_value_usd: minValue ? parseFloat(minValue) : undefined,
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Fehler bei der Analyse');
    } finally {
      setIsLoading(false);
    }
  };

  const formatUSD = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const getRiskColor = (score: number) => {
    if (score > 0.7) return 'destructive';
    if (score > 0.4) return 'default';
    return 'secondary';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Cross-Chain Bridge Analyse
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Input Form */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Adresse</label>
              <Input
                placeholder="0x..."
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Primäre Chain</label>
              <Select value={chain} onValueChange={setChain}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ethereum">Ethereum</SelectItem>
                  <SelectItem value="polygon">Polygon</SelectItem>
                  <SelectItem value="bsc">BSC</SelectItem>
                  <SelectItem value="arbitrum">Arbitrum</SelectItem>
                  <SelectItem value="optimism">Optimism</SelectItem>
                  <SelectItem value="avalanche">Avalanche</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Max Depth</label>
              <Select value={maxDepth.toString()} onValueChange={(v) => setMaxDepth(parseInt(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1</SelectItem>
                  <SelectItem value="2">2</SelectItem>
                  <SelectItem value="3">3</SelectItem>
                  <SelectItem value="5">5</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Filter Options */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Von Datum</label>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Bis Datum</label>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Min. Wert (USD)</label>
              <Input
                type="number"
                placeholder="1000"
                value={minValue}
                onChange={(e) => setMinValue(e.target.value)}
              />
            </div>
          </div>

          {/* Direction Toggles */}
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeIncoming}
                onChange={(e) => setIncludeIncoming(e.target.checked)}
              />
              Eingehende Transfers
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeOutgoing}
                onChange={(e) => setIncludeOutgoing(e.target.checked)}
              />
              Ausgehende Transfers
            </label>
          </div>

          <Button onClick={handleAnalyze} disabled={isLoading} className="w-full">
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analysiere...
              </>
            ) : (
              <>
                <Network className="mr-2 h-4 w-4" />
                Bridge-Aktivitäten analysieren
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Fehler bei der Analyse: {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Results Display */}
      {result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold">{result.total_bridge_transfers}</div>
                <div className="text-sm text-muted-foreground">Bridge-Transfers</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold">{formatUSD(result.total_volume_usd)}</div>
                <div className="text-sm text-muted-foreground">Gesamtvolumen</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold">{result.chains_involved.length}</div>
                <div className="text-sm text-muted-foreground">Chains beteiligt</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-red-600">{result.high_risk_count}</div>
                <div className="text-sm text-muted-foreground">Hochrisiko</div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Factors */}
          {result.risk_factors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                  Risk-Faktoren
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.risk_factors.map((factor: string, idx: number) => (
                    <li key={idx} className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Chains and Bridges */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Beteiligte Chains</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {result.chains_involved.map((chain: string) => (
                    <Badge key={chain} variant="outline">{chain}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Verwendete Bridges</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {result.bridges_used.map((bridge: string) => (
                    <Badge key={bridge} variant="secondary">{bridge}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Transfers */}
          <Card>
            <CardHeader>
              <CardTitle>Letzte Bridge-Transfers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {result.recent_transfers.slice(0, 10).map((transfer: BridgeTransfer, idx: number) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <TrendingUp className={`h-4 w-4 ${
                          transfer.type === 'incoming' ? 'text-green-500' : 'text-blue-500'
                        }`} />
                        <span className="font-medium">
                          {transfer.type === 'incoming' ? 'Eingehend' : 'Ausgehend'}
                        </span>
                        <Badge variant={getRiskColor(transfer.risk_score)}>
                          Risk: {(transfer.risk_score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {new Date(transfer.timestamp).toLocaleString()}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Von:</span> {transfer.from_chain}
                      </div>
                      <div>
                        <span className="text-muted-foreground">Nach:</span> {transfer.to_chain}
                      </div>
                      <div>
                        <span className="text-muted-foreground">Wert:</span> {formatUSD(transfer.value_usd)}
                      </div>
                      <div>
                        <span className="text-muted-foreground">Bridge:</span> {transfer.bridge_name}
                      </div>
                    </div>

                    <div className="mt-2 text-xs text-muted-foreground">
                      TX: {transfer.tx_hash.substring(0, 10)}...
                    </div>
                  </div>
                ))}

                {result.recent_transfers.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    Keine Bridge-Transfers gefunden
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
