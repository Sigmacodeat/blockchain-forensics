import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Flag, Plus, X, AlertTriangle, CheckCircle } from 'lucide-react';
import { useFlagAddress } from '@/hooks/useIntelligenceNetwork';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface Evidence {
  type: string;
  value: string;
}

export function FlagSubmission() {
  const [address, setAddress] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [reason, setReason] = useState<string>('');
  const [description, setDescription] = useState('');
  const [amountUsd, setAmountUsd] = useState('');
  const [autoTrace, setAutoTrace] = useState(true);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [newEvidenceType, setNewEvidenceType] = useState('transaction_hash');
  const [newEvidenceValue, setNewEvidenceValue] = useState('');

  const { mutate: flagAddress, isPending, isSuccess, error } = useFlagAddress();

  const handleSubmit = () => {
    if (!address || !reason || !description) return;

    flagAddress({
      address,
      chain,
      reason,
      description,
      amount_usd: amountUsd ? parseFloat(amountUsd) : undefined,
      evidence: evidence.length > 0 ? evidence : undefined,
      auto_trace: autoTrace,
    }, {
      onSuccess: () => {
        // Reset form
        setAddress('');
        setDescription('');
        setAmountUsd('');
        setEvidence([]);
      },
    });
  };

  const addEvidence = () => {
    if (!newEvidenceValue) return;
    setEvidence([...evidence, { type: newEvidenceType, value: newEvidenceValue }]);
    setNewEvidenceValue('');
  };

  const removeEvidence = (index: number) => {
    setEvidence(evidence.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Info Card */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-1">
              ℹ️ Flag Submission Guidelines
            </h4>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <li>• Ensure address is verified before flagging</li>
              <li>• Provide detailed description and evidence</li>
              <li>• Flags are shared with all network investigators</li>
              <li>• False flags may impact your trust score</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Form */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Flag className="w-5 h-5 text-primary-600" />
          Submit Intelligence Flag
        </h3>

        <div className="space-y-4">
          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Address *
            </label>
            <Input
              type="text"
              placeholder="0x1234567890abcdef..."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="font-mono"
            />
          </div>

          {/* Chain */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Chain *
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

          {/* Reason */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Reason *
            </label>
            <Select value={reason} onValueChange={setReason}>
              <SelectTrigger>
                <SelectValue placeholder="Select reason..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ransomware">🔒 Ransomware</SelectItem>
                <SelectItem value="scam">⚠️ Scam</SelectItem>
                <SelectItem value="fraud">💸 Fraud</SelectItem>
                <SelectItem value="sanctions">🚫 Sanctions</SelectItem>
                <SelectItem value="darknet">🕷️ Darknet</SelectItem>
                <SelectItem value="terrorism">☠️ Terrorism</SelectItem>
                <SelectItem value="other">📋 Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Description *
            </label>
            <Textarea
              placeholder="Provide detailed description of the illicit activity..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
            />
            <p className="text-xs text-slate-500 mt-1">
              {description.length}/500 characters
            </p>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Estimated Amount (USD)
            </label>
            <Input
              type="number"
              placeholder="0.00"
              value={amountUsd}
              onChange={(e) => setAmountUsd(e.target.value)}
            />
          </div>

          {/* Evidence */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Evidence
            </label>
            <div className="flex gap-2 mb-2">
              <Select value={newEvidenceType} onValueChange={setNewEvidenceType}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="transaction_hash">Transaction Hash</SelectItem>
                  <SelectItem value="blockchain_explorer">Explorer Link</SelectItem>
                  <SelectItem value="report">Report Link</SelectItem>
                  <SelectItem value="article">Article URL</SelectItem>
                  <SelectItem value="screenshot">Screenshot URL</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
              <Input
                type="text"
                placeholder="Evidence value..."
                value={newEvidenceValue}
                onChange={(e) => setNewEvidenceValue(e.target.value)}
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                onClick={addEvidence}
                disabled={!newEvidenceValue}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            {/* Evidence List */}
            {evidence.length > 0 && (
              <div className="space-y-2 mt-3">
                {evidence.map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-2 p-2 bg-slate-50 dark:bg-slate-800 rounded"
                  >
                    <Badge variant="outline" className="text-xs">
                      {item.type}
                    </Badge>
                    <code className="flex-1 text-xs truncate text-slate-700 dark:text-slate-300">
                      {item.value}
                    </code>
                    <button
                      onClick={() => removeEvidence(idx)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* Auto-Trace */}
          <div className="flex items-center gap-2 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200">
            <input
              type="checkbox"
              id="auto-trace"
              checked={autoTrace}
              onChange={(e) => setAutoTrace(e.target.checked)}
              className="rounded border-slate-300"
            />
            <label htmlFor="auto-trace" className="text-sm text-slate-700 dark:text-slate-300">
              <span className="font-medium">🔍 Auto-Trace:</span> Automatically trace fund flow after
              flagging
            </label>
          </div>

          {/* Submit Button */}
          <Button
            onClick={handleSubmit}
            disabled={isPending || !address || !reason || !description}
            className="w-full"
          >
            {isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Submitting...
              </>
            ) : (
              <>
                <Flag className="w-4 h-4 mr-2" />
                Submit Flag
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Success Message */}
      {isSuccess && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="p-4 bg-green-50 dark:bg-green-900/20 border-green-200">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
              <CheckCircle className="w-5 h-5" />
              <div>
                <p className="font-semibold">✅ Flag submitted successfully!</p>
                <p className="text-sm">
                  {autoTrace
                    ? 'Auto-trace has been initiated. Results will be available shortly.'
                    : 'Flag has been broadcast to all network investigators.'}
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Error Message */}
      {error && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Error: {error.message}</span>
          </div>
        </Card>
      )}
    </div>
  );
}
