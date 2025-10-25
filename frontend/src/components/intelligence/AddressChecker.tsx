import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Shield, AlertTriangle, CheckCircle, Info, ExternalLink } from 'lucide-react';
import { useCheckAddress } from '@/hooks/useIntelligenceNetwork';
import type { IntelligenceCheckResult } from '@/hooks/useIntelligenceNetwork';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function AddressChecker() {
  const [address, setAddress] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [checkRelated, setCheckRelated] = useState(true);
  const { mutate: checkAddress, data: result, isPending, error } = useCheckAddress();

  const handleCheck = () => {
    if (!address) return;
    checkAddress({ address, chain, check_related: checkRelated });
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Search className="w-5 h-5 text-primary-600" />
          Check Address Against Network
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Address
            </label>
            <Input
              type="text"
              placeholder="0x1234567890abcdef..."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Chain
            </label>
            <Select value={chain} onValueChange={setChain}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ethereum">Ethereum</SelectItem>
                <SelectItem value="bitcoin">Bitcoin</SelectItem>
                <SelectItem value="polygon">Polygon</SelectItem>
                <SelectItem value="arbitrum">Arbitrum</SelectItem>
                <SelectItem value="optimism">Optimism</SelectItem>
                <SelectItem value="base">Base</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="check-related"
              checked={checkRelated}
              onChange={(e) => setCheckRelated(e.target.checked)}
              className="rounded border-slate-300"
            />
            <label htmlFor="check-related" className="text-sm text-slate-700 dark:text-slate-300">
              Check related addresses (depth 1)
            </label>
          </div>
          <Button
            onClick={handleCheck}
            disabled={isPending || !address}
            className="w-full"
          >
            {isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Checking...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Check Address
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Error: {error.message}</span>
          </div>
        </Card>
      )}

      {/* Results */}
      {result && <CheckResults result={result} />}
    </div>
  );
}

// Results Component
interface CheckResultsProps {
  result: IntelligenceCheckResult;
}

function CheckResults({ result }: CheckResultsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Summary Card */}
      <Card className={`p-6 border-l-4 ${getActionBorderColor(result.recommended_action)}`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              {result.is_flagged ? (
                <AlertTriangle className="w-6 h-6 text-red-600" />
              ) : (
                <CheckCircle className="w-6 h-6 text-green-600" />
              )}
              <h3 className="text-xl font-bold">
                {result.is_flagged ? '⚠️ Address Flagged' : '✅ Address Clean'}
              </h3>
            </div>
            <p className="font-mono text-sm text-slate-600 dark:text-slate-400 mb-4">
              {result.address}
            </p>
          </div>
          <Badge className={getActionColor(result.recommended_action)}>
            {result.recommended_action.toUpperCase()}
          </Badge>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <StatBox
            label="Risk Score"
            value={`${(result.risk_score * 100).toFixed(0)}%`}
            color={getRiskColor(result.risk_score)}
          />
          <StatBox
            label="Direct Flags"
            value={result.direct_flags}
            color={result.direct_flags > 0 ? 'text-red-600' : 'text-green-600'}
          />
          <StatBox
            label="Related Flags"
            value={result.related_flags}
            color={result.related_flags > 0 ? 'text-orange-600' : 'text-green-600'}
          />
          <StatBox
            label="Chain"
            value={result.chain}
            color="text-blue-600"
          />
        </div>

        {/* Recommendation */}
        <div className={`p-4 rounded-lg ${getActionBgColor(result.recommended_action)}`}>
          <h4 className="font-semibold mb-2 flex items-center gap-2">
            <Info className="w-4 h-4" />
            Recommended Action
          </h4>
          <p className="text-sm">{getActionDescription(result.recommended_action)}</p>
        </div>
      </Card>

      {/* Flags Details */}
      {result.flags.length > 0 && (
        <Card className="p-6">
          <h4 className="font-semibold mb-4">🚩 Direct Flags ({result.flags.length})</h4>
          <div className="space-y-3">
            {result.flags.map((flag, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className={getReasonColor(flag.reason)}>{flag.reason}</Badge>
                    <Badge className={getStatusColor(flag.status)}>{flag.status}</Badge>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">{flag.description}</p>
                </div>
                <div className="text-right text-xs text-slate-500">
                  <div>{flag.confirmation_count} confirmations</div>
                  <div className="font-mono">{flag.flagged_by}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Related Addresses */}
      {result.related_addresses.length > 0 && (
        <Card className="p-6">
          <h4 className="font-semibold mb-4">
            🔗 Related Addresses ({result.related_addresses.length})
          </h4>
          <div className="space-y-2">
            {result.related_addresses.map((related, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"
              >
                <div className="flex-1">
                  <code className="text-sm">
                    {related.address.substring(0, 10)}...
                    {related.address.substring(related.address.length - 8)}
                  </code>
                  <span className="text-xs text-slate-500 ml-2">({related.chain})</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {related.relationship}
                  </Badge>
                  {related.flags > 0 && (
                    <Badge className="text-red-600 bg-red-50 text-xs">
                      {related.flags} flags
                    </Badge>
                  )}
                  <ExternalLink className="w-4 h-4 text-slate-400" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </motion.div>
  );
}

// Helper Components
interface StatBoxProps {
  label: string;
  value: string | number;
  color: string;
}

function StatBox({ label, value, color }: StatBoxProps) {
  return (
    <div className="text-center">
      <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

// Helper Functions
function getActionBorderColor(action: string): string {
  const colors: Record<string, string> = {
    freeze: 'border-red-500',
    review: 'border-orange-500',
    monitor: 'border-yellow-500',
    allow: 'border-green-500',
  };
  return colors[action] || 'border-slate-300';
}

function getActionColor(action: string): string {
  const colors: Record<string, string> = {
    freeze: 'text-red-700 bg-red-50 border-red-200',
    review: 'text-orange-700 bg-orange-50 border-orange-200',
    monitor: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    allow: 'text-green-700 bg-green-50 border-green-200',
  };
  return colors[action] || 'text-slate-700 bg-slate-50';
}

function getActionBgColor(action: string): string {
  const colors: Record<string, string> = {
    freeze: 'bg-red-50 dark:bg-red-900/20 border border-red-200',
    review: 'bg-orange-50 dark:bg-orange-900/20 border border-orange-200',
    monitor: 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200',
    allow: 'bg-green-50 dark:bg-green-900/20 border border-green-200',
  };
  return colors[action] || 'bg-slate-50 dark:bg-slate-800';
}

function getActionDescription(action: string): string {
  const descriptions: Record<string, string> = {
    freeze: '🚨 IMMEDIATE ACTION REQUIRED: Freeze all transactions and escalate to law enforcement.',
    review: '⚠️ CAUTION: Manual review required before proceeding with transaction.',
    monitor: '👁️ WATCHLIST: Monitor future activity but allow current transactions.',
    allow: '✅ SAFE: No flags detected. Transaction can proceed normally.',
  };
  return descriptions[action] || 'Unknown action';
}

function getRiskColor(score: number): string {
  if (score >= 0.8) return 'text-red-600';
  if (score >= 0.6) return 'text-orange-600';
  if (score >= 0.3) return 'text-yellow-600';
  return 'text-green-600';
}

function getReasonColor(reason: string): string {
  const colors: Record<string, string> = {
    ransomware: 'text-red-700 bg-red-50 border-red-200',
    scam: 'text-orange-700 bg-orange-50 border-orange-200',
    fraud: 'text-amber-700 bg-amber-50 border-amber-200',
    sanctions: 'text-purple-700 bg-purple-50 border-purple-200',
    darknet: 'text-slate-700 bg-slate-50 border-slate-200',
    terrorism: 'text-red-800 bg-red-100 border-red-300',
  };
  return colors[reason] || 'text-slate-700 bg-slate-50';
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    confirmed: 'text-green-700 bg-green-50 border-green-200',
    disputed: 'text-red-700 bg-red-50 border-red-200',
    resolved: 'text-blue-700 bg-blue-50 border-blue-200',
  };
  return colors[status] || 'text-slate-700 bg-slate-50';
}
