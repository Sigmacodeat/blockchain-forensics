import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User,
  Building2,
  Globe,
  Github,
  Twitter,
  AlertTriangle,
  TrendingUp,
  Users,
  Activity,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Shield,
} from 'lucide-react';
import { useEntityProfile } from '@/hooks/useEntityProfiler';
import {
  getEntityTypeIcon,
  getEntityTypeColor,
  getConfidenceColor,
  getActivityPatternColor,
  formatVolume,
  formatTransactionCount,
} from '@/hooks/useEntityProfiler';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface Props {
  address: string;
  chain: string;
  includeOsint?: boolean;
  includeRelationships?: boolean;
  autoLoad?: boolean;
}

export function EntityProfileCard({
  address,
  chain,
  includeOsint = true,
  includeRelationships = true,
  autoLoad = false,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const { data: profile, isPending, error, refetch } = useEntityProfile(
    address,
    chain,
    {
      include_osint: includeOsint,
      include_relationships: includeRelationships,
      depth: 2,
    }
  );

  const [manualLoad, setManualLoad] = React.useState(!autoLoad);

  if (manualLoad && !isPending) {
    return (
      <Button
        onClick={() => {
          setManualLoad(false);
          refetch();
        }}
        variant="outline"
        size="sm"
        className="text-xs"
      >
        <User className="w-3 h-3 mr-1" />
        Load Entity Profile
      </Button>
    );
  }

  if (isPending) {
    return (
      <Card className="p-4 animate-pulse">
        <div className="space-y-3">
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
          <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
          <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200">
        <div className="flex items-center gap-2 text-sm text-red-600">
          <AlertTriangle className="w-4 h-4" />
          <span>Failed to load profile: {error.message}</span>
        </div>
      </Card>
    );
  }

  if (!profile) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3"
    >
      {/* Compact View */}
      <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">{getEntityTypeIcon(profile.entity_type)}</span>
              <Badge className={getEntityTypeColor(profile.entity_type)}>
                {profile.entity_type.replace('_', ' ')}
              </Badge>
              {profile.attribution.attributed_name && (
                <Badge className={getConfidenceColor(profile.attribution.confidence)}>
                  {profile.attribution.confidence}
                </Badge>
              )}
            </div>

            {profile.attribution.attributed_name && (
              <h4 className="font-semibold text-lg text-slate-900 dark:text-white mb-1">
                {profile.attribution.attributed_name}
              </h4>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <p className="text-xs text-slate-500">Volume</p>
                <p className="font-semibold text-slate-900 dark:text-white">
                  {formatVolume(profile.blockchain_data.total_volume_usd)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Transactions</p>
                <p className="font-semibold text-slate-900 dark:text-white">
                  {formatTransactionCount(profile.blockchain_data.total_transactions)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Counterparties</p>
                <p className="font-semibold text-slate-900 dark:text-white">
                  {formatTransactionCount(profile.blockchain_data.unique_counterparties)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Risk</p>
                <Badge className={getRiskColor(profile.risk_assessment.risk_level)}>
                  {profile.risk_assessment.risk_level}
                </Badge>
              </div>
            </div>
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white ml-4"
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
            {/* Attribution Details */}
            {profile.attribution.signals.length > 0 && (
              <Card className="p-4">
                <h4 className="font-semibold mb-3 text-sm flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-600" />
                  Attribution Signals ({profile.attribution.signals.length})
                </h4>
                <div className="space-y-2">
                  {profile.attribution.signals.slice(0, 5).map((signal, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-xs p-2 bg-slate-50 dark:bg-slate-800 rounded"
                    >
                      <div className="flex-1">
                        <span className="font-medium">{signal.type}:</span>{' '}
                        <span className="text-slate-600 dark:text-slate-400">{signal.value}</span>
                      </div>
                      <Badge className={getConfidenceColor(signal.confidence)} variant="outline">
                        {signal.confidence}
                      </Badge>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Behavior Analysis */}
            <Card className="p-4">
              <h4 className="font-semibold mb-3 text-sm flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-600" />
                Behavioral Pattern
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="text-slate-500 mb-1">Activity Pattern</p>
                  <Badge className={getActivityPatternColor(profile.behavior_analysis.activity_pattern)}>
                    {profile.behavior_analysis.activity_pattern}
                  </Badge>
                </div>
                <div>
                  <p className="text-slate-500 mb-1">Transaction Frequency</p>
                  <Badge variant="outline">
                    {profile.behavior_analysis.transaction_frequency}
                  </Badge>
                </div>
                <div>
                  <p className="text-slate-500 mb-1">Typical TX Size</p>
                  <p className="font-semibold">
                    {formatVolume(profile.behavior_analysis.typical_transaction_size_usd)}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 mb-1">Counterparty Diversity</p>
                  <Badge variant="outline">
                    {profile.behavior_analysis.counterparty_diversity}
                  </Badge>
                </div>
              </div>

              {profile.behavior_analysis.anomalies.length > 0 && (
                <div className="mt-3 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200">
                  <p className="text-xs font-medium text-orange-900 dark:text-orange-100 mb-1">
                    ⚠️ Anomalies Detected:
                  </p>
                  <ul className="text-xs text-orange-800 dark:text-orange-200 space-y-1">
                    {profile.behavior_analysis.anomalies.map((anomaly, idx) => (
                      <li key={idx}>
                        • [{anomaly.severity}] {anomaly.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>

            {/* OSINT Data */}
            {profile.osint_data && profile.osint_data.findings.length > 0 && (
              <Card className="p-4">
                <h4 className="font-semibold mb-3 text-sm flex items-center gap-2">
                  <Globe className="w-4 h-4 text-green-600" />
                  OSINT Findings ({profile.osint_data.findings.length})
                </h4>
                <div className="space-y-2">
                  {/* Social Profiles */}
                  {profile.osint_data.social_profiles.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Social Media:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {profile.osint_data.social_profiles.map((social, idx) => (
                          <a
                            key={idx}
                            href={social.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30"
                          >
                            {getSocialIcon(social.platform)}
                            <span>{social.username}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Websites */}
                  {profile.osint_data.websites.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Websites:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {profile.osint_data.websites.map((website, idx) => (
                          <a
                            key={idx}
                            href={website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded hover:bg-green-100 dark:hover:bg-green-900/30"
                          >
                            <Globe className="w-3 h-3" />
                            <span className="truncate max-w-[200px]">{website}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Related Entities */}
            {profile.related_entities.length > 0 && (
              <Card className="p-4">
                <h4 className="font-semibold mb-3 text-sm flex items-center gap-2">
                  <Users className="w-4 h-4 text-indigo-600" />
                  Related Entities ({profile.related_entities.length})
                </h4>
                <div className="space-y-2">
                  {profile.related_entities.slice(0, 5).map((related, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-xs p-2 bg-slate-50 dark:bg-slate-800 rounded"
                    >
                      <div className="flex-1 min-w-0">
                        <code className="text-xs truncate block">
                          {related.address.substring(0, 10)}...
                          {related.address.substring(related.address.length - 8)}
                        </code>
                        <span className="text-slate-500">
                          {related.relationship_type} ({related.chain})
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">{(related.confidence * 100).toFixed(0)}%</p>
                        {related.entity_type && (
                          <Badge variant="outline" className="text-xs mt-1">
                            {related.entity_type}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Risk Assessment */}
            {profile.risk_assessment.risk_factors.length > 0 && (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <h4 className="font-semibold text-sm">Risk Assessment</h4>
                  <Badge className={getRiskColor(profile.risk_assessment.risk_level)}>
                    {profile.risk_assessment.risk_level} • {(profile.risk_assessment.risk_score * 100).toFixed(0)}%
                  </Badge>
                </div>

                <div className="space-y-2">
                  {profile.risk_assessment.risk_factors.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Risk Factors:
                      </p>
                      <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                        {profile.risk_assessment.risk_factors.map((factor, idx) => (
                          <li key={idx}>• {factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {profile.risk_assessment.recommendations.length > 0 && (
                    <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200">
                      <p className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-1">
                        💡 Recommendations:
                      </p>
                      <ul className="text-xs text-blue-800 dark:text-blue-200 space-y-1">
                        {profile.risk_assessment.recommendations.map((rec, idx) => (
                          <li key={idx}>• {rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Labels & Tags */}
            {(profile.labels.length > 0 || profile.tags.length > 0) && (
              <Card className="p-4">
                <h4 className="font-semibold mb-2 text-sm">Labels & Tags</h4>
                <div className="flex flex-wrap gap-2">
                  {profile.labels.map((label, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {label}
                    </Badge>
                  ))}
                  {profile.tags.map((tag, idx) => (
                    <Badge key={idx} className="text-xs bg-purple-100 text-purple-700">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Helpers
function getRiskColor(level: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-700 bg-red-50 border-red-200',
    high: 'text-orange-700 bg-orange-50 border-orange-200',
    medium: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    low: 'text-green-700 bg-green-50 border-green-200',
  };
  return colors[level] || 'text-slate-700 bg-slate-50';
}

function getSocialIcon(platform: string) {
  const icons: Record<string, React.ReactNode> = {
    twitter: <Twitter className="w-3 h-3" />,
    github: <Github className="w-3 h-3" />,
    linkedin: <Building2 className="w-3 h-3" />,
  };
  return icons[platform.toLowerCase()] || <Globe className="w-3 h-3" />;
}
