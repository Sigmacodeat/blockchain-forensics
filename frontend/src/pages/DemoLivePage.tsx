/**
 * Live Demo Page (Tier 2 - 30 Minutes Test Drive)
 * 
 * Inspired by: Linear, Supabase, Framer
 * Creates temporary account, auto-login, 30-min timer
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  Zap,
  Shield,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { track } from '@/lib/analytics';

interface LiveDemoResponse {
  user_id: string;
  email: string;
  token: string;
  demo_type: string;
  plan: string;
  expires_at: string;
  duration_minutes: number;
  features: string[];
  message: string;
  limitations: {
    time_limited: boolean;
    auto_cleanup: boolean;
    data_not_saved: boolean;
  };
  cta: {
    message: string;
    action: string;
  };
}

const DemoLivePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demoData, setDemoData] = useState<LiveDemoResponse | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);

  // Track page view
  useEffect(() => {
    track('demo_live_viewed', {
      source: window.location.search.includes('ref=chat') ? 'chatbot' : 'direct'
    });
  }, []);

  const startLiveDemo = async () => {
    track('demo_live_start_clicked', {
      source: 'live_demo_page'
    });

    setLoading(true);
    setError(null);

    try {
      // Create live demo account
      const response = await axios.post<LiveDemoResponse>('/api/v1/demo/live');
      setDemoData(response.data);

      // Track successful creation
      track('demo_live_created', {
        user_id: response.data.user_id,
        plan: response.data.plan,
        duration_minutes: response.data.duration_minutes
      });

      // Auto-login with demo token
      const { token, user_id, email, plan } = response.data;
      
      // Store token and user info
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify({
        id: user_id,
        email,
        plan,
        is_demo: true
      }));

      // Calculate initial time remaining
      const expiresAt = new Date(response.data.expires_at).getTime();
      const now = Date.now();
      setTimeRemaining(Math.floor((expiresAt - now) / 1000));

      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        navigate('/dashboard');
      }, 3000);

    } catch (err: any) {
      const errorType = err.response?.status === 429 ? 'rate_limit' : 'unknown';
      
      track('demo_live_error', {
        error_type: errorType,
        status_code: err.response?.status || 0
      });

      if (err.response?.status === 429) {
        setError('Rate Limit erreicht: Max 3 Live-Demos pro IP pro Tag');
      } else {
        setError('Fehler beim Erstellen der Live-Demo. Bitte versuche es später erneut.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Countdown timer
  useEffect(() => {
    if (timeRemaining > 0) {
      const interval = setInterval(() => {
        setTimeRemaining((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [timeRemaining]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (demoData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <Card className="max-w-2xl w-full bg-slate-800/50 backdrop-blur border-slate-700 p-8">
          <div className="text-center">
            {/* Success Animation */}
            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-32 w-32 bg-green-500/20 rounded-full animate-ping"></div>
              </div>
              <CheckCircle2 className="h-32 w-32 text-green-500 mx-auto relative" />
            </div>

            <h1 className="text-3xl font-bold text-white mb-2">
              🎉 Live-Demo gestartet!
            </h1>
            <p className="text-xl text-slate-300 mb-6">
              {demoData.message}
            </p>

            {/* Timer */}
            <div className="bg-gradient-to-r from-primary to-purple-600 rounded-lg p-6 mb-6">
              <div className="flex items-center justify-center gap-3 text-white">
                <Clock className="h-6 w-6" />
                <span className="text-4xl font-bold font-mono">
                  {formatTime(timeRemaining)}
                </span>
              </div>
              <p className="text-white/80 text-sm mt-2">
                Zeit verbleibend
              </p>
            </div>

            {/* Features */}
            <div className="bg-slate-900/50 rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center justify-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Deine Pro-Features
              </h2>
              <div className="grid grid-cols-2 gap-3">
                {demoData.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm text-slate-300">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    {feature.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                ))}
              </div>
            </div>

            {/* Info Badges */}
            <div className="flex flex-wrap gap-2 justify-center mb-6">
              <Badge variant="outline" className="border-green-500 text-green-500">
                <Shield className="h-3 w-3 mr-1" />
                Keine Kreditkarte nötig
              </Badge>
              <Badge variant="outline" className="border-blue-500 text-blue-500">
                <Zap className="h-3 w-3 mr-1" />
                Voller Pro-Zugang
              </Badge>
              <Badge variant="outline" className="border-yellow-500 text-yellow-500">
                <Clock className="h-3 w-3 mr-1" />
                30 Minuten
              </Badge>
            </div>

            {/* Auto-Redirect Message */}
            <div className="flex items-center justify-center gap-2 text-primary mb-4">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm">Weiterleitung zum Dashboard in 3 Sekunden...</span>
            </div>

            {/* Manual Navigation */}
            <Button 
              onClick={() => navigate('/dashboard')}
              className="bg-gradient-to-r from-primary to-purple-600"
              size="lg"
            >
              Jetzt starten
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>

            {/* CTA Box */}
            <div className="mt-6 p-4 bg-primary/10 rounded-lg border border-primary/20">
              <p className="text-sm text-slate-300">
                💡 <strong className="text-white">{demoData.cta.message}</strong>
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full bg-slate-800/50 backdrop-blur border-slate-700 p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full mb-4">
            <Zap className="h-4 w-4" />
            <span className="text-sm font-medium">30-Minuten Live-Demo</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Teste mit echten Daten
          </h1>
          <p className="text-xl text-slate-300">
            Voller Pro-Plan Zugang - keine Registrierung nötig
          </p>
        </div>

        {/* Features List */}
        <div className="space-y-4 mb-8">
          <div className="flex items-start gap-3 p-4 bg-slate-900/50 rounded-lg">
            <CheckCircle2 className="h-6 w-6 text-green-500 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-white mb-1">Voller Pro-Zugang</h3>
              <p className="text-sm text-slate-400">
                Alle Features: Transaction Tracing, Investigator, Cases, AI-Agent, Analytics
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-slate-900/50 rounded-lg">
            <Clock className="h-6 w-6 text-blue-500 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-white mb-1">30 Minuten Zeit</h3>
              <p className="text-sm text-slate-400">
                Genug Zeit um alle Features gründlich zu testen
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-slate-900/50 rounded-lg">
            <Shield className="h-6 w-6 text-purple-500 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-white mb-1">Keine Kreditkarte</h3>
              <p className="text-sm text-slate-400">
                Account wird automatisch gelöscht - keine versteckten Kosten
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-slate-900/50 rounded-lg">
            <Sparkles className="h-6 w-6 text-yellow-500 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-white mb-1">Echte Daten</h3>
              <p className="text-sm text-slate-400">
                Teste mit deinen eigenen Blockchain-Adressen und echten Traces
              </p>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* CTA Button */}
        <Button
          onClick={startLiveDemo}
          disabled={loading}
          className="w-full bg-gradient-to-r from-primary to-purple-600 hover:opacity-90 text-white text-lg py-6"
          size="lg"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Live-Demo wird erstellt...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-5 w-5" />
              Jetzt kostenlos starten
            </>
          )}
        </Button>

        {/* Fine Print */}
        <p className="text-center text-sm text-slate-400 mt-4">
          Nach Ablauf kannst du kostenlos einen Account erstellen und deine Arbeit speichern
        </p>

        {/* Rate Limit Info */}
        <div className="mt-6 p-3 bg-slate-900/50 rounded-lg text-center">
          <p className="text-xs text-slate-500">
            Max 3 Live-Demos pro IP pro Tag • Account wird nach 30 Min automatisch gelöscht
          </p>
        </div>
      </Card>
    </div>
  );
};

export default DemoLivePage;
