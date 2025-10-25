import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  ExternalLink,
  Filter,
  MapPin,
  Shield,
  TrendingUp,
  Users,
  XCircle,
} from 'lucide-react';
import { useConfirmFlag } from '@/hooks/useIntelligenceNetwork';
import type { IntelligenceFlag } from '@/hooks/useIntelligenceNetwork';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface Props {
  flags: IntelligenceFlag[];
  loading: boolean;
}

export function ActiveFlags({ flags, loading }: Props) {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterReason, setFilterReason] = useState<string>('all');
  const { mutate: confirmFlag, isPending: isConfirming } = useConfirmFlag();

  const filteredFlags = flags.filter((flag) => {
    if (filterStatus !== 'all' && flag.status !== filterStatus) return false;
    if (filterReason !== 'all' && flag.reason !== filterReason) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <Filter className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="confirmed">Confirmed</SelectItem>
                <SelectItem value="disputed">Disputed</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterReason} onValueChange={setFilterReason}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by reason" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Reasons</SelectItem>
                <SelectItem value="ransomware">Ransomware</SelectItem>
                <SelectItem value="scam">Scam</SelectItem>
                <SelectItem value="fraud">Fraud</SelectItem>
                <SelectItem value="sanctions">Sanctions</SelectItem>
                <SelectItem value="darknet">Darknet</SelectItem>
                <SelectItem value="terrorism">Terrorism</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Flags List */}
      <AnimatePresence>
        {filteredFlags.length === 0 ? (
          <Card className="p-12 text-center">
            <Shield className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400">
              Keine Flags gefunden für ausgewählte Filter
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredFlags.map((flag) => (
              <FlagCard
                key={flag.id}
                flag={flag}
                onConfirm={() => confirmFlag({ flag_id: flag.id })}
                isConfirming={isConfirming}
              />
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Flag Card Component
interface FlagCardProps {
  flag: IntelligenceFlag;
  onConfirm: () => void;
  isConfirming: boolean;
}

function FlagCard({ flag, onConfirm, isConfirming }: FlagCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      layout
    >
      <Card className={`p-6 border-l-4 ${getStatusBorderColor(flag.status)}`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              {getReasonIcon(flag.reason)}
              <h3 className="font-mono text-lg font-semibold text-slate-900 dark:text-white">
                {flag.address.substring(0, 10)}...{flag.address.substring(flag.address.length - 8)}
              </h3>
              <Badge className={getStatusColor(flag.status)}>{flag.status}</Badge>
              <Badge className={getReasonColor(flag.reason)}>{flag.reason}</Badge>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">{flag.description}</p>
            <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {flag.chain}
              </span>
              {flag.amount_usd && (
                <span className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  ${flag.amount_usd.toLocaleString()}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatDate(flag.flagged_at)}
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                {flag.confirmation_count} confirmations
              </span>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            {flag.auto_traced && (
              <Badge className="text-purple-600 bg-purple-50 border-purple-200">
                🔍 Auto-traced
              </Badge>
            )}
            {flag.status === 'pending' && (
              <Button
                size="sm"
                onClick={onConfirm}
                disabled={isConfirming}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Confirm
              </Button>
            )}
          </div>
        </div>

        {/* Evidence & Details */}
        {flag.evidence.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              {expanded ? '▼' : '▶'} Evidence ({flag.evidence.length})
            </button>
            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-3 space-y-2"
                >
                  {flag.evidence.map((evidence, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2 bg-slate-50 dark:bg-slate-800 rounded text-xs"
                    >
                      <Badge variant="outline">{evidence.type}</Badge>
                      <code className="flex-1 text-slate-700 dark:text-slate-300 truncate">
                        {evidence.value}
                      </code>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Confirmed By */}
        {flag.confirmed_by.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span>Confirmed by:</span>
              <div className="flex flex-wrap gap-2">
                {flag.confirmed_by.map((investigator, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {investigator}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  );
}

// Helper Functions
function getStatusBorderColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'border-yellow-500',
    confirmed: 'border-green-500',
    disputed: 'border-red-500',
    resolved: 'border-blue-500',
  };
  return colors[status] || 'border-slate-300';
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

function getReasonIcon(reason: string) {
  const icons: Record<string, React.ReactNode> = {
    ransomware: <Shield className="w-5 h-5 text-red-600" />,
    scam: <AlertTriangle className="w-5 h-5 text-orange-600" />,
    fraud: <XCircle className="w-5 h-5 text-amber-600" />,
    sanctions: <Shield className="w-5 h-5 text-purple-600" />,
    darknet: <Shield className="w-5 h-5 text-slate-600" />,
    terrorism: <AlertTriangle className="w-5 h-5 text-red-700" />,
  };
  return icons[reason] || <AlertTriangle className="w-5 h-5 text-slate-600" />;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}
