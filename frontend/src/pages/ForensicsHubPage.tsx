import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Radar, FolderOpen, Network, Brain, Route, GitBranch, Search, Shield, Key, Users, Sparkles, TrendingUp, FileText, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { canAccessRoute } from '@/lib/features';

interface Tool {
  id: string;
  title: string;
  description: string;
  icon: any;
  path: string;
  badge?: string;
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
  minPlan: string;
}

const TOOLS: Tool[] = [
  { id: 'trace', title: 'Transaction Tracing', description: 'Verfolge Transaktionen über Chains hinweg', icon: Radar, path: '/trace', badge: 'Community+', badgeVariant: 'secondary', minPlan: 'community' },
  { id: 'cases', title: 'Case Management', description: 'Organisiere Ermittlungen strukturiert', icon: FolderOpen, path: '/cases', badge: 'Community+', badgeVariant: 'secondary', minPlan: 'community' },
  { id: 'bridge', title: 'Bridge Transfers', description: 'Erkenne Cross-Chain-Transfers', icon: GitBranch, path: '/bridge-transfers', badge: 'Community+', badgeVariant: 'secondary', minPlan: 'community' },
  { id: 'investigator', title: 'Graph Explorer', description: 'Interaktive Graph-Visualisierung', icon: Network, path: '/investigator', badge: 'Pro+', minPlan: 'pro' },
  { id: 'correlation', title: 'Korrelations-Analyse', description: 'Muster- und Verbindungsanalyse', icon: Brain, path: '/correlation', badge: 'Pro+', minPlan: 'pro' },
  { id: 'patterns', title: 'Pattern Detection', description: 'Peel Chains, Rapid Movement und mehr', icon: Route, path: '/patterns', badge: 'Pro+', minPlan: 'pro' },
  { id: 'screening', title: 'Universal Screening', description: 'Multi-Chain Screening gegen Sanktionslisten', icon: Search, path: '/universal-screening', badge: 'Pro+', minPlan: 'pro' },
  { id: 'intelligence', title: 'Intelligence Network', description: 'Teile & empfange Threat Intelligence', icon: Users, path: '/intelligence-network', badge: 'Pro+', minPlan: 'pro' },
  { id: 'scanner', title: 'Wallet Scanner', description: 'Tiefenanalyse von Wallets', icon: Key, path: '/wallet-scanner', badge: 'Pro+', minPlan: 'pro' },
  { id: 'automation', title: 'Automation Rules', description: 'Automatisiere Tracing, Cases & Alerts', icon: Sparkles, path: '/automation', badge: 'Business+', minPlan: 'business' },
  { id: 'policies', title: 'Risk Policies', description: 'Definiere Custom-Risk-Policies', icon: Shield, path: '/policies', badge: 'Business+', minPlan: 'business' },
  { id: 'vasp', title: 'VASP Compliance', description: 'Travel Rule & VASP Screening', icon: FileText, path: '/vasp-compliance', badge: 'Business+', minPlan: 'business' },
  { id: 'ai', title: 'AI-Assistent', description: 'KI-gestützte forensische Queries', icon: Sparkles, path: '/ai-agent', badge: 'Plus+', badgeVariant: 'destructive', minPlan: 'plus' },
  { id: 'indirect', title: 'Advanced Indirect Risk', description: 'Erweiterte indirekte Risiko-Analyse', icon: AlertTriangle, path: '/advanced-indirect-risk', badge: 'Plus+', badgeVariant: 'destructive', minPlan: 'plus' },
];

export default function ForensicsHubPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Forensics Hub</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Professionelle Blockchain-Forensik-Tools für jede Ermittlung</p>
        </div>
        <Button variant="outline" onClick={() => navigate('/dashboards')} className="h-10 px-4">
          <TrendingUp className="w-4 h-4 mr-2" /> Eigene Dashboards
        </Button>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {TOOLS.map((tool) => {
          const allowed = canAccessRoute(user, tool.path);
          const Icon = tool.icon;
          return (
            <button
              key={tool.id}
              onClick={() => allowed && navigate(tool.path)}
              disabled={!allowed}
              className={`group relative flex flex-col items-start p-5 rounded-xl border-2 transition-all duration-200 text-left ${
                allowed
                  ? 'bg-card border-border hover:border-primary-500 dark:hover:border-primary-400 hover:shadow-lg'
                  : 'bg-muted border-border opacity-60 cursor-not-allowed'
              }`}
              title={allowed ? tool.description : `Benötigt ${tool.badge}`}
              aria-label={tool.title}
            >
              {/* Icon & Badge */}
              <div className="flex items-start justify-between w-full mb-3">
                <div className={`p-3 rounded-lg ${allowed ? 'bg-primary-50 dark:bg-primary-900/20 group-hover:bg-primary-100 dark:group-hover:bg-primary-900/30' : 'bg-gray-100 dark:bg-gray-800'} transition-colors`}>
                  <Icon className={`w-6 h-6 ${allowed ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-600'}`} />
                </div>
                {tool.badge && (
                  <Badge variant={tool.badgeVariant || 'outline'} className="text-xs">
                    {tool.badge}
                  </Badge>
                )}
              </div>

              {/* Title & Description */}
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  {tool.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {tool.description}
                </p>
              </div>

              {/* Lock Icon für disabled */}
              {!allowed && (
                <div className="absolute top-3 right-3 text-gray-400 dark:text-gray-600">
                  <Shield className="w-5 h-5" />
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
