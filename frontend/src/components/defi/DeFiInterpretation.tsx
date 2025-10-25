import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Code, AlertTriangle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { useInterpretTransaction } from '@/hooks/useDeFiInterpreter';
import type { DeFiInterpretation as DeFiInterpretationType } from '@/hooks/useDeFiInterpreter';
import {
  getComplexityColor,
  getProtocolLogo,
  getProtocolColor,
  getActionIcon,
  formatActionDescription,
} from '@/hooks/useDeFiInterpreter';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface Props {
  txHash: string;
  chain: string;
  autoInterpret?: boolean;
}

export function DeFiInterpretation({ txHash, chain, autoInterpret = false }: Props) {
  const [expanded, setExpanded] = useState(false);
  const { mutate: interpret, data: result, isPending, error } = useInterpretTransaction();

  React.useEffect(() => {
    if (autoInterpret) {
      interpret({ tx_hash: txHash, chain, include_risk: true });
    }
  }, [autoInterpret, txHash, chain]);

  if (!result && !isPending && !error) {
    return (
      <Button
        onClick={() => interpret({ tx_hash: txHash, chain, include_risk: true })}
        variant="outline"
        size="sm"
        className="text-xs"
      >
        <Code className="w-3 h-3 mr-1" />
        Interpret DeFi
      </Button>
    );
  }

  if (isPending) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
        <div className="w-3 h-3 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
        <span>Interpreting transaction...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-600">
        <AlertTriangle className="w-4 h-4" />
        <span>Failed to interpret: {error.message}</span>
      </div>
    );
  }

  if (!result) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3"
    >
      {/* Compact View */}
      <Card className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-purple-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            <span className="text-2xl">{getProtocolLogo(result.protocol)}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Badge className={getProtocolColor(result.protocol)}>
                  {result.protocol}
                </Badge>
                <Badge className={getComplexityColor(result.complexity)}>
                  {result.complexity}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {result.type}
                </Badge>
              </div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                {result.human_readable}
              </p>
            </div>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
          >
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </Card>

      {/* Expanded Details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="space-y-4"
          >
            {/* Actions */}
            {result.actions.length > 0 && (
              <Card className="p-4">
                <h4 className="font-semibold mb-3 text-sm">Actions ({result.actions.length})</h4>
                <div className="space-y-2">
                  {result.actions.map((action, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-2 bg-slate-50 dark:bg-slate-800 rounded"
                    >
                      <span className="text-lg flex-shrink-0">{getActionIcon(action.type)}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white capitalize">
                          {action.type.replace('_', ' ')}
                        </p>
                        <p className="text-xs text-slate-600 dark:text-slate-400">
                          {action.description}
                        </p>
                        {(action.from || action.to || action.amount) && (
                          <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                            {formatActionDescription(action)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Risk Assessment */}
            {result.risk_assessment && (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <h4 className="font-semibold text-sm">Risk Assessment</h4>
                  <Badge className={getRiskLevelColor(result.risk_assessment.risk_level)}>
                    {result.risk_assessment.risk_level}
                  </Badge>
                </div>

                {result.risk_assessment.risk_factors.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Risk Factors:
                    </p>
                    <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                      {result.risk_assessment.risk_factors.map((factor, idx) => (
                        <li key={idx}>• {factor}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.risk_assessment.warnings.length > 0 && (
                  <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200">
                    <p className="text-xs font-medium text-orange-900 dark:text-orange-100 mb-1">
                      ⚠️ Warnings:
                    </p>
                    <ul className="text-xs text-orange-800 dark:text-orange-200 space-y-1">
                      {result.risk_assessment.warnings.map((warning, idx) => (
                        <li key={idx}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            )}

            {/* Technical Details */}
            {(result.function_signature || result.decoded_input) && (
              <Card className="p-4">
                <h4 className="font-semibold mb-3 text-sm flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  Technical Details
                </h4>
                {result.function_signature && (
                  <div className="mb-2">
                    <p className="text-xs text-slate-500 mb-1">Function Signature:</p>
                    <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded block overflow-x-auto">
                      {result.function_signature}
                    </code>
                  </div>
                )}
                {result.decoded_input && (
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Decoded Input:</p>
                    <pre className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded overflow-x-auto">
                      {JSON.stringify(result.decoded_input, null, 2)}
                    </pre>
                  </div>
                )}
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Helper
function getRiskLevelColor(level: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-700 bg-red-50 border-red-200',
    high: 'text-orange-700 bg-orange-50 border-orange-200',
    medium: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    low: 'text-green-700 bg-green-50 border-green-200',
  };
  return colors[level] || 'text-slate-700 bg-slate-50';
}
