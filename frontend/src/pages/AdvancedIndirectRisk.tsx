import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch,
  AlertTriangle,
  Shield,
  TrendingDown,
  Search,
  Loader2,
  ChevronRight,
  Network,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface RiskPath {
  from_address: string;
  to_address: string;
  hop_count: number;
  path_type: string;
  risk_categories: string[];
  risk_score: number;
  confidence: number;
  intermediate_addresses: string[];
  chains_involved: string[];
}

interface IndirectRiskResult {
  target_address: string;
  max_hops: number;
  total_paths_found: number;
  paths_analyzed: number;
  aggregate_risk_score: number;
  risk_by_category: Record<string, number>;
  high_risk_paths: RiskPath[];
  chains_analyzed: string[];
  processing_time_ms: number;
}

const AdvancedIndirectRisk: React.FC = () => {
  const [targetAddress, setTargetAddress] = useState('');
  const [maxHops, setMaxHops] = useState(3);
  const [selectedChains, setSelectedChains] = useState<string[]>(['ethereum', 'polygon', 'arbitrum']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IndirectRiskResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const chains = [
    'ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 
    'avalanche', 'bsc', 'fantom', 'bitcoin', 'solana'
  ];

  const analyzeRisk = async () => {
    if (!targetAddress) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/advanced-risk/indirect-risk`,
        {
          target_address: targetAddress,
          max_hops: maxHops,
          chains: selectedChains,
          max_paths: 1000,
        },
        {
          headers: { Authorization: token ? `Bearer ${token}` : '' },
        }
      );

      if (response.data.success) {
        setResult(response.data.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
      console.error('Risk analysis failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary via-purple-500 to-blue-500 bg-clip-text text-transparent flex items-center gap-3">
            <GitBranch className="h-8 w-8 text-primary" />
            Advanced Indirect Risk Detection
          </h1>
          <p className="text-muted-foreground mt-1">
            Path-Agnostic Multi-Hop Risk Analysis across all chains
          </p>
        </div>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Analysis Configuration
          </CardTitle>
          <CardDescription>
            Configure multi-hop risk analysis parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Target Address */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Target Address *
            </label>
            <Input
              placeholder="0xAbCDEF..."
              value={targetAddress}
              onChange={(e) => setTargetAddress(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Max Hops */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Maximum Hops: {maxHops}
            </label>
            <input
              type="range"
              min="1"
              max="5"
              value={maxHops}
              onChange={(e) => setMaxHops(parseInt(e.target.value))}
              disabled={loading}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Higher hops = more paths found, but slower analysis
            </p>
          </div>

          {/* Chain Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Chains to Analyze
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {chains.map((chain) => (
                <label
                  key={chain}
                  className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                    selectedChains.includes(chain)
                      ? 'bg-primary/10 border-primary'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedChains.includes(chain)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedChains([...selectedChains, chain]);
                      } else {
                        setSelectedChains(selectedChains.filter((c) => c !== chain));
                      }
                    }}
                    disabled={loading}
                  />
                  <span className="text-sm capitalize">{chain}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Analyze Button */}
          <Button
            onClick={analyzeRisk}
            disabled={loading || !targetAddress || selectedChains.length === 0}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <GitBranch className="mr-2 h-4 w-4" />
                Analyze Indirect Risk
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4 flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            <span>{error}</span>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Summary */}
            <Card className={`border-l-4 ${getRiskBorderColor(result.aggregate_risk_score)}`}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Risk Analysis Summary</span>
                  <Badge className={getRiskBadgeVariant(result.aggregate_risk_score)}>
                    {(result.aggregate_risk_score * 100).toFixed(1)}% Risk
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatBox
                    label="Paths Found"
                    value={result.total_paths_found.toLocaleString()}
                    icon={<GitBranch className="h-4 w-4" />}
                  />
                  <StatBox
                    label="Max Hops"
                    value={result.max_hops}
                    icon={<Network className="h-4 w-4" />}
                  />
                  <StatBox
                    label="Chains Analyzed"
                    value={result.chains_analyzed.length}
                    icon={<Shield className="h-4 w-4" />}
                  />
                  <StatBox
                    label="Processing Time"
                    value={`${(result.processing_time_ms / 1000).toFixed(2)}s`}
                    icon={<TrendingDown className="h-4 w-4" />}
                  />
                </div>

                {/* Risk by Category */}
                {Object.keys(result.risk_by_category).length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-semibold text-sm">Risk by Category</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(result.risk_by_category).map(([category, score]) => (
                        <div
                          key={category}
                          className="flex items-center justify-between p-2 bg-muted rounded"
                        >
                          <span className="text-sm capitalize">{category}</span>
                          <Badge variant="outline">{(score * 100).toFixed(1)}%</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* High Risk Paths */}
            {result.high_risk_paths.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-destructive" />
                    High Risk Paths ({result.high_risk_paths.length})
                  </CardTitle>
                  <CardDescription>
                    Paths with elevated risk scores requiring attention
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {result.high_risk_paths.map((path, idx) => (
                    <RiskPathCard key={idx} path={path} />
                  ))}
                </CardContent>
              </Card>
            )}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
};

// Helper Components
interface StatBoxProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
}

function StatBox({ label, value, icon }: StatBoxProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="text-muted-foreground">{icon}</div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="font-semibold text-lg">{value}</p>
      </div>
    </div>
  );
}

interface RiskPathCardProps {
  path: RiskPath;
}

function RiskPathCard({ path }: RiskPathCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="border-l-4 border-l-orange-500">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className="capitalize">
                {path.path_type}
              </Badge>
              <Badge variant="destructive">
                {(path.risk_score * 100).toFixed(1)}% Risk
              </Badge>
              <Badge variant="secondary">
                {path.hop_count} {path.hop_count === 1 ? 'hop' : 'hops'}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-sm font-mono">
              <code className="text-xs">{truncateAddress(path.from_address)}</code>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              <code className="text-xs">{truncateAddress(path.to_address)}</code>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Less' : 'More'}
          </Button>
        </div>

        {/* Risk Categories */}
        <div className="flex flex-wrap gap-1 mb-2">
          {path.risk_categories.map((category, idx) => (
            <Badge key={idx} variant="outline" className="text-xs">
              {category}
            </Badge>
          ))}
        </div>

        {/* Expanded Details */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 space-y-2 border-t pt-4"
            >
              {/* Intermediate Addresses */}
              {path.intermediate_addresses.length > 0 && (
                <div>
                  <p className="text-xs font-semibold mb-1">Intermediate Addresses:</p>
                  <div className="space-y-1">
                    {path.intermediate_addresses.map((addr, idx) => (
                      <code key={idx} className="block text-xs text-muted-foreground">
                        {addr}
                      </code>
                    ))}
                  </div>
                </div>
              )}

              {/* Chains Involved */}
              <div>
                <p className="text-xs font-semibold mb-1">Chains:</p>
                <div className="flex flex-wrap gap-1">
                  {path.chains_involved.map((chain, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs capitalize">
                      {chain}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Confidence */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Confidence:</span>
                <span className="font-semibold">{(path.confidence * 100).toFixed(1)}%</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}

// Helper Functions
function getRiskBorderColor(score: number): string {
  if (score >= 0.8) return 'border-l-red-500';
  if (score >= 0.6) return 'border-l-orange-500';
  if (score >= 0.4) return 'border-l-yellow-500';
  return 'border-l-green-500';
}

function getRiskBadgeVariant(score: number): 'default' | 'destructive' | 'secondary' | 'outline' {
  if (score >= 0.8) return 'destructive';
  if (score >= 0.6) return 'secondary';
  return 'outline';
}

function truncateAddress(address: string): string {
  if (address.length <= 13) return address;
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export default AdvancedIndirectRisk;
