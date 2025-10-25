/**
 * Sandbox Demo Page (Tier 1 - No Signup)
 * 
 * Inspired by: Flagsmith, SEMrush, Notion
 * Shows instant preview with mock data, zero friction
 */

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { 
  Play, 
  Eye, 
  AlertTriangle, 
  TrendingUp, 
  Activity,
  ArrowRight,
  Sparkles,
  Lock,
  Zap
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import axios from 'axios';
import { track } from '@/lib/analytics';

interface SandboxDemoData {
  type: string;
  message: string;
  features: string[];
  mock_data: {
    recent_cases: Array<{
      id: string;
      title: string;
      status: string;
      risk_score: number;
      created_at: string;
      addresses_count: number;
    }>;
    sample_addresses: Array<{
      address: string;
      chain: string;
      risk_score: number;
      labels: string[];
      balance: string;
    }>;
    analytics: {
      total_traces: number;
      high_risk_detected: number;
      active_cases: number;
      chains_monitored: number;
    };
  };
  limitations: {
    read_only: boolean;
    no_data_persistence: boolean;
    limited_to_samples: boolean;
  };
  cta: {
    message: string;
    action: string;
  };
}

const DemoSandboxPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [demoData, setDemoData] = useState<SandboxDemoData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Track page view
    track('demo_sandbox_viewed', {
      source: window.location.search.includes('ref=chat') ? 'chatbot' : 'direct'
    });

    // Load sandbox demo data
    const loadSandboxData = async () => {
      try {
        const response = await axios.get<SandboxDemoData>('/api/v1/demo/sandbox');
        setDemoData(response.data);
        
        // Track successful load
        track('demo_sandbox_loaded', {
          cases_count: response.data.mock_data.recent_cases.length,
          addresses_count: response.data.mock_data.sample_addresses.length
        });
      } catch (error) {
        console.error('Failed to load sandbox demo:', error);
        track('demo_sandbox_error', {
          error: String(error)
        });
      } finally {
        setLoading(false);
      }
    };

    loadSandboxData();
  }, []);

  const handleStartLiveDemo = () => {
    track('demo_sandbox_cta_clicked', {
      action: 'start_live_demo',
      source: 'sandbox_page'
    });
    navigate('/demo/live');
  };

  const handleSignup = () => {
    track('demo_sandbox_cta_clicked', {
      action: 'signup',
      source: 'sandbox_page'
    });
    navigate('/register');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Demo...</p>
        </div>
      </div>
    );
  }

  if (!demoData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center text-white">
          <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-yellow-500" />
          <h2 className="text-2xl font-bold mb-2">Demo nicht verfügbar</h2>
          <p className="text-slate-300 mb-4">Bitte versuche es später erneut.</p>
          <Button onClick={() => navigate('/')}>Zurück zur Startseite</Button>
        </div>
      </div>
    );
  }

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'text-red-500';
    if (score >= 60) return 'text-orange-500';
    if (score >= 40) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Banner: This is a Demo */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-3 px-4 text-center">
        <div className="flex items-center justify-center gap-2 text-white">
          <Eye className="h-5 w-5" />
          <span className="font-semibold">{demoData.message}</span>
          <Badge variant="outline" className="bg-white/20 text-white border-white/30">
            Read-Only
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full mb-4">
            <Sparkles className="h-4 w-4" />
            <span className="text-sm font-medium">Sandbox Demo - Sofort testen!</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Blockchain Forensics Platform
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Erkunde alle Features mit Beispieldaten - keine Registrierung nötig
          </p>
        </div>

        {/* Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-slate-800/50 backdrop-blur border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Total Traces</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {demoData.mock_data.analytics.total_traces.toLocaleString()}
                </p>
              </div>
              <Activity className="h-12 w-12 text-blue-500 opacity-80" />
            </div>
          </Card>

          <Card className="bg-slate-800/50 backdrop-blur border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">High Risk Detected</p>
                <p className="text-3xl font-bold text-red-500 mt-1">
                  {demoData.mock_data.analytics.high_risk_detected}
                </p>
              </div>
              <AlertTriangle className="h-12 w-12 text-red-500 opacity-80" />
            </div>
          </Card>

          <Card className="bg-slate-800/50 backdrop-blur border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Active Cases</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {demoData.mock_data.analytics.active_cases}
                </p>
              </div>
              <TrendingUp className="h-12 w-12 text-green-500 opacity-80" />
            </div>
          </Card>

          <Card className="bg-slate-800/50 backdrop-blur border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Chains Monitored</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {demoData.mock_data.analytics.chains_monitored}+
                </p>
              </div>
              <Activity className="h-12 w-12 text-purple-500 opacity-80" />
            </div>
          </Card>
        </div>

        {/* Recent Cases */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
            <Play className="h-6 w-6 text-primary" />
            Beispiel-Cases
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {demoData.mock_data.recent_cases.map((case_item) => (
              <Card key={case_item.id} className="bg-slate-800/50 backdrop-blur border-slate-700 p-6 hover:border-primary/50 transition-colors cursor-pointer">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">{case_item.title}</h3>
                  <Badge variant={case_item.status === 'active' ? 'default' : 'outline'}>
                    {case_item.status}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Risk Score:</span>
                    <span className={`font-bold ${getRiskColor(case_item.risk_score)}`}>
                      {case_item.risk_score}/100
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Addresses:</span>
                    <span className="text-white">{case_item.addresses_count}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Created:</span>
                    <span className="text-white">
                      {new Date(case_item.created_at).toLocaleDateString('de-DE')}
                    </span>
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-end gap-2 text-primary text-sm font-medium">
                  View Details
                  <ArrowRight className="h-4 w-4" />
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Sample Addresses */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
            <Lock className="h-6 w-6 text-primary" />
            Beispiel-Adressen
          </h2>
          <div className="grid grid-cols-1 gap-4">
            {demoData.mock_data.sample_addresses.map((addr, idx) => (
              <Card key={idx} className="bg-slate-800/50 backdrop-blur border-slate-700 p-6 hover:border-primary/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <code className="text-sm text-primary font-mono bg-primary/10 px-3 py-1 rounded">
                        {addr.address}
                      </code>
                      <Badge variant="outline" className="text-xs">
                        {addr.chain}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-slate-400">
                        Risk: <span className={`font-bold ${getRiskColor(addr.risk_score)}`}>
                          {addr.risk_score}/100
                        </span>
                      </span>
                      <span className="text-slate-400">
                        Balance: <span className="text-white font-medium">{addr.balance}</span>
                      </span>
                      <div className="flex gap-2">
                        {addr.labels.map((label, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {label}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <Card className="bg-gradient-to-r from-primary to-purple-600 border-0 p-8 text-center">
          <Zap className="h-16 w-16 text-white mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-2">
            {demoData.cta.message}
          </h2>
          <p className="text-white/90 mb-6 max-w-2xl mx-auto">
            Voller Pro-Plan Zugang für 30 Minuten - teste mit echten Daten, 
            keine Kreditkarte nötig!
          </p>
          <div className="flex gap-4 justify-center">
            <Button 
              size="lg" 
              variant="secondary"
              onClick={handleStartLiveDemo}
              className="bg-white text-primary hover:bg-white/90"
            >
              <Play className="mr-2 h-5 w-5" />
              30-Min Live-Demo starten
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              onClick={handleSignup}
              className="border-white text-white hover:bg-white/10"
            >
              Kostenlosen Account erstellen
            </Button>
          </div>
          <p className="text-white/70 text-sm mt-4">
            Nach der Live-Demo kannst du deine Arbeit mit einem kostenlosen Account speichern
          </p>
        </Card>
      </div>
    </div>
  );
};

export default DemoSandboxPage;
