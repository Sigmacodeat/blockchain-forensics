import React from 'react';
import { motion } from 'framer-motion';
import { Network, AlertTriangle, Shield, ExternalLink } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface RelatedAddress {
  address: string;
  chain: string;
  relationship: string;
  flags: number;
  risk_score: number;
}

interface Props {
  relatedAddresses: RelatedAddress[];
  loading?: boolean;
}

export function RelatedAddressNetwork({ relatedAddresses, loading }: Props) {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
          <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded" />
        </div>
      </Card>
    );
  }

  if (!relatedAddresses || relatedAddresses.length === 0) {
    return (
      <Card className="p-6 text-center">
        <Network className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Keine verwandten Adressen gefunden
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Network className="w-5 h-5 text-primary-600" />
          Related Address Network
        </h3>
        <Badge className="text-slate-600 bg-slate-100">
          {relatedAddresses.length} connections
        </Badge>
      </div>

      <div className="space-y-3">
        {relatedAddresses.map((related, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            className={`
              p-4 rounded-lg border-l-4 transition-all
              ${related.risk_score >= 0.7 
                ? 'bg-red-50 dark:bg-red-900/20 border-red-500' 
                : related.risk_score >= 0.4
                ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
                : 'bg-slate-50 dark:bg-slate-800 border-slate-300'
              }
              hover:shadow-md
            `}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <code className="text-sm font-mono font-medium text-slate-900 dark:text-white truncate">
                    {related.address.substring(0, 12)}...{related.address.substring(related.address.length - 10)}
                  </code>
                  <Badge variant="outline" className="text-xs">
                    {related.chain}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400">
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Relationship:</span>
                    {related.relationship}
                  </span>
                  {related.flags > 0 && (
                    <span className="flex items-center gap-1 text-red-600">
                      <AlertTriangle className="w-3 h-3" />
                      {related.flags} flags
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <div className="text-right">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Risk Score</p>
                  <p className={`
                    text-lg font-bold
                    ${related.risk_score >= 0.7 ? 'text-red-600' : 
                      related.risk_score >= 0.4 ? 'text-yellow-600' : 
                      'text-green-600'}
                  `}>
                    {(related.risk_score * 100).toFixed(0)}%
                  </p>
                </div>
                <button className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg transition-colors">
                  <ExternalLink className="w-4 h-4 text-slate-400" />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}
