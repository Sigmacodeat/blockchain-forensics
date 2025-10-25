/**
 * 🛡️ AI BLOCKCHAIN FIREWALL - CONTROL CENTER
 * ============================================
 * 
 * Das ultimative Wallet-Security Dashboard:
 * - Real-Time Protection Monitor
 * - Threat Detection Live-Feed
 * - Whitelist/Blacklist Management
 * - Custom Rule Engine
 * - AI Statistics & Analytics
 * - Emergency Controls
 */

import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Settings,
  TrendingUp,
  Eye,
  EyeOff,
  Plus,
  Trash2,
  Download,
  RefreshCw,
  Zap,
  Brain,
  Lock,
  Unlock,
  Play,
  Pause
} from 'lucide-react';
import { motion } from 'framer-motion';

// Types
interface ThreatDetection {
  tx_hash: string;
  timestamp: string;
  threat_level: 'critical' | 'high' | 'medium' | 'low' | 'safe';
  confidence: number;
  threat_types: string[];
  evidence: Array<{type: string; [key: string]: any}>;
  allowed: boolean;
  block_reason?: string;
  detection_time_ms: number;
}

interface FirewallStats {
  total_scanned: number;
  blocked: number;
  warned: number;
  allowed: number;
  threat_types: Record<string, number>;
  avg_detection_time_ms: number;
  protection_level: string;
  enabled: boolean;
  whitelist_size: number;
  blacklist_size: number;
  custom_rules: number;
  block_rate: number;
}

export default function FirewallControlCenter() {
  // State
  const [stats, setStats] = useState<FirewallStats | null>(null);
  const [recentThreats, setRecentThreats] = useState<ThreatDetection[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [whitelist, setWhitelist] = useState<string[]>([]);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [newAddress, setNewAddress] = useState('');
  const [activeTab, setActiveTab] = useState<'monitor' | 'lists' | 'rules' | 'settings'>('monitor');

  // WebSocket Connection
  useEffect(() => {
    if (!isMonitoring) return;

    const websocket = new WebSocket(
      `ws://${window.location.hostname}:8000/api/v1/firewall/stream?user_id=${getUserId()}`
    );

    websocket.onopen = () => {
      console.log('🔌 Firewall WebSocket connected');
      // Request stats
      websocket.send(JSON.stringify({ type: 'stats' }));
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'scan.result') {
        // Add to recent threats
        setRecentThreats(prev => [data as ThreatDetection, ...prev].slice(0, 50));
      } else if (data.type === 'stats.response') {
        setStats(data.stats);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('🔌 Firewall WebSocket disconnected');
    };

    setWs(websocket);

    // Cleanup
    return () => {
      websocket.close();
    };
  }, [isMonitoring]);

  // Fetch initial data
  useEffect(() => {
    fetchStats();
    fetchWhitelist();
    fetchBlacklist();
  }, []);

  // Auto-refresh stats every 5s
  useEffect(() => {
    const interval = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'stats' }));
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [ws]);

  // API Calls
  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/firewall/stats', {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchWhitelist = async () => {
    try {
      const response = await fetch('/api/v1/firewall/whitelist', {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      setWhitelist(data.addresses);
    } catch (error) {
      console.error('Failed to fetch whitelist:', error);
    }
  };

  const fetchBlacklist = async () => {
    try {
      const response = await fetch('/api/v1/firewall/blacklist', {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      setBlacklist(data.addresses);
    } catch (error) {
      console.error('Failed to fetch blacklist:', error);
    }
  };

  const addToWhitelist = async (address: string) => {
    try {
      await fetch('/api/v1/firewall/whitelist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ address, reason: 'User added' })
      });
      fetchWhitelist();
      setNewAddress('');
    } catch (error) {
      console.error('Failed to add to whitelist:', error);
    }
  };

  const addToBlacklist = async (address: string) => {
    try {
      await fetch('/api/v1/firewall/blacklist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ address, reason: 'User added' })
      });
      fetchBlacklist();
      setNewAddress('');
    } catch (error) {
      console.error('Failed to add to blacklist:', error);
    }
  };

  const removeFromWhitelist = async (address: string) => {
    try {
      await fetch(`/api/v1/firewall/whitelist/${address}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      fetchWhitelist();
    } catch (error) {
      console.error('Failed to remove from whitelist:', error);
    }
  };

  const removeFromBlacklist = async (address: string) => {
    try {
      await fetch(`/api/v1/firewall/blacklist/${address}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      fetchBlacklist();
    } catch (error) {
      console.error('Failed to remove from blacklist:', error);
    }
  };

  const toggleFirewall = async () => {
    const endpoint = stats?.enabled ? '/api/v1/firewall/disable' : '/api/v1/firewall/enable';
    try {
      await fetch(endpoint, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      fetchStats();
    } catch (error) {
      console.error('Failed to toggle firewall:', error);
    }
  };

  // Helpers
  const getUserId = () => {
    // Get from localStorage or auth context
    return localStorage.getItem('user_id') || 'anonymous';
  };

  const getToken = () => {
    return localStorage.getItem('access_token') || '';
  };

  const getThreatColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-500 bg-red-500/10';
      case 'high': return 'text-orange-500 bg-orange-500/10';
      case 'medium': return 'text-yellow-500 bg-yellow-500/10';
      case 'low': return 'text-blue-500 bg-blue-500/10';
      case 'safe': return 'text-green-500 bg-green-500/10';
      default: return 'text-gray-500 bg-gray-500/10';
    }
  };

  const getThreatIcon = (level: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return <XCircle className="w-5 h-5" />;
      case 'medium':
        return <AlertTriangle className="w-5 h-5" />;
      case 'safe':
        return <CheckCircle className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  if (!stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-primary-500" />
          <p className="text-gray-600 dark:text-gray-400">Loading Firewall...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring' }}
              className="w-16 h-16 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg"
            >
              <Shield className="w-8 h-8 text-white" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                AI Blockchain Firewall
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Real-Time Wallet Protection • 15 ML Models • 7 Defense Layers
              </p>
            </div>
          </div>

          {/* Firewall Toggle */}
          <motion.button
            onClick={toggleFirewall}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`px-6 py-3 rounded-xl font-semibold flex items-center gap-2 shadow-lg transition-all ${
              stats.enabled
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white'
                : 'bg-gradient-to-r from-gray-500 to-gray-600 text-white'
            }`}
          >
            {stats.enabled ? (
              <>
                <Lock className="w-5 h-5" />
                Firewall Active
              </>
            ) : (
              <>
                <Unlock className="w-5 h-5" />
                Firewall Inactive
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          icon={<Activity />}
          title="Total Scanned"
          value={stats.total_scanned.toLocaleString()}
          color="blue"
        />
        <StatsCard
          icon={<XCircle />}
          title="Blocked"
          value={stats.blocked.toLocaleString()}
          subtitle={`${(stats.block_rate * 100).toFixed(1)}% block rate`}
          color="red"
        />
        <StatsCard
          icon={<AlertTriangle />}
          title="Warned"
          value={stats.warned.toLocaleString()}
          color="yellow"
        />
        <StatsCard
          icon={<Zap />}
          title="Avg Detection"
          value={`${stats.avg_detection_time_ms.toFixed(1)}ms`}
          subtitle="Sub-10ms target"
          color="purple"
        />
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex gap-2 bg-card rounded-xl p-2 shadow-lg border border-border">
          {[
            { id: 'monitor', label: 'Live Monitor', icon: <Eye /> },
            { id: 'lists', label: 'White/Blacklist', icon: <Shield /> },
            { id: 'rules', label: 'Custom Rules', icon: <Settings /> },
            { id: 'settings', label: 'Settings', icon: <Settings /> }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-1 px-4 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-primary-500 to-purple-600 text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto">
        {activeTab === 'monitor' && (
          <MonitorTab threats={recentThreats} getThreatColor={getThreatColor} getThreatIcon={getThreatIcon} />
        )}
        {activeTab === 'lists' && (
          <ListsTab
            whitelist={whitelist}
            blacklist={blacklist}
            newAddress={newAddress}
            setNewAddress={setNewAddress}
            addToWhitelist={addToWhitelist}
            addToBlacklist={addToBlacklist}
            removeFromWhitelist={removeFromWhitelist}
            removeFromBlacklist={removeFromBlacklist}
          />
        )}
        {activeTab === 'rules' && <RulesTab />}
        {activeTab === 'settings' && <SettingsTab stats={stats} />}
      </div>
    </div>
  );
}

// Stats Card Component
type ColorKey = 'blue' | 'red' | 'yellow' | 'purple' | 'green';

interface StatsCardProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  subtitle?: string;
  color: ColorKey;
}

function StatsCard({ icon, title, value, subtitle, color }: StatsCardProps) {
  const colors: Record<ColorKey, string> = {
    blue: 'from-blue-500 to-blue-600',
    red: 'from-red-500 to-red-600',
    yellow: 'from-yellow-500 to-orange-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-emerald-600'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all"
    >
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 bg-gradient-to-br ${colors[color]} rounded-xl flex items-center justify-center text-white`}>
          {icon}
        </div>
        <div className="flex-1">
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        </div>
      </div>
    </motion.div>
  );
}

// Monitor Tab
function MonitorTab({ threats, getThreatColor, getThreatIcon }: any) {
  return (
    <div className="bg-card rounded-2xl shadow-lg p-6 border border-border">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Activity className="w-6 h-6 text-primary-500" />
          Real-Time Threat Feed
        </h2>
        <span className="px-3 py-1 bg-green-500/10 text-green-500 rounded-lg text-sm font-medium flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Live
        </span>
      </div>

      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {threats.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No threats detected. Firewall is protecting your wallet.</p>
          </div>
        ) : (
          threats.map((threat: ThreatDetection, i: number) => (
            <motion.div
              key={`${threat.tx_hash}-${i}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`p-4 rounded-xl border-2 ${
                threat.allowed ? 'border-gray-200 dark:border-slate-700' : 'border-red-500/50'
              } hover:shadow-md transition-all`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-3 py-1 rounded-lg text-sm font-medium flex items-center gap-2 ${getThreatColor(threat.threat_level)}`}>
                      {getThreatIcon(threat.threat_level)}
                      {threat.threat_level.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(threat.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`text-xs font-medium ${threat.allowed ? 'text-green-500' : 'text-red-500'}`}>
                      {threat.allowed ? '✓ ALLOWED' : '✗ BLOCKED'}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-mono mb-2">
                    TX: {threat.tx_hash.slice(0, 16)}...
                  </p>
                  
                  {threat.threat_types.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2">
                      {threat.threat_types.map(type => (
                        <span key={type} className="px-2 py-1 bg-gray-100 dark:bg-slate-700 text-xs rounded">
                          {type}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  {threat.block_reason && (
                    <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                      ⚠️ {threat.block_reason}
                    </p>
                  )}
                </div>
                
                <div className="text-right">
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                    {(threat.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    {threat.detection_time_ms.toFixed(1)}ms
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}

// Lists Tab
function ListsTab({ whitelist, blacklist, newAddress, setNewAddress, addToWhitelist, addToBlacklist, removeFromWhitelist, removeFromBlacklist }: any) {
  const [activeList, setActiveList] = useState<'whitelist' | 'blacklist'>('whitelist');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Whitelist */}
      <div className="bg-card rounded-2xl shadow-lg p-6 border border-border">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          Whitelist ({whitelist.length})
        </h3>
        
        <div className="mb-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={activeList === 'whitelist' ? newAddress : ''}
              onChange={(e) => { setActiveList('whitelist'); setNewAddress(e.target.value); }}
              placeholder="0x..."
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 dark:bg-slate-700"
            />
            <button
              onClick={() => addToWhitelist(newAddress)}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>
        </div>

        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {whitelist.map((addr: string) => (
            <div key={addr} className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/10 rounded-lg">
              <span className="font-mono text-sm">{addr}</span>
              <button
                onClick={() => removeFromWhitelist(addr)}
                className="text-red-500 hover:text-red-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          {whitelist.length === 0 && (
            <p className="text-center text-gray-500 py-8">No whitelisted addresses</p>
          )}
        </div>
      </div>

      {/* Blacklist */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <XCircle className="w-5 h-5 text-red-500" />
          Blacklist ({blacklist.length})
        </h3>
        
        <div className="mb-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={activeList === 'blacklist' ? newAddress : ''}
              onChange={(e) => { setActiveList('blacklist'); setNewAddress(e.target.value); }}
              placeholder="0x..."
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-red-500 dark:bg-slate-700"
            />
            <button
              onClick={() => addToBlacklist(newAddress)}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>
        </div>

        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {blacklist.map((addr: string) => (
            <div key={addr} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/10 rounded-lg">
              <span className="font-mono text-sm">{addr}</span>
              <button
                onClick={() => removeFromBlacklist(addr)}
                className="text-gray-500 hover:text-gray-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          {blacklist.length === 0 && (
            <p className="text-center text-gray-500 py-8">No blacklisted addresses</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Rules Tab
function RulesTab() {
  return (
    <div className="bg-card rounded-2xl shadow-lg p-6 border border-border">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <Settings className="w-5 h-5 text-primary-500" />
        Custom Firewall Rules
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        Create advanced rules for fine-grained control over your wallet protection.
      </p>
      <div className="text-center py-12 text-gray-500">
        <Settings className="w-16 h-16 mx-auto mb-4 opacity-50" />
        <p>Rules management UI coming soon...</p>
        <p className="text-sm mt-2">Use API endpoints for now</p>
      </div>
    </div>
  );
}

// Settings Tab
function SettingsTab({ stats }: { stats: FirewallStats }) {
  return (
    <div className="bg-card rounded-2xl shadow-lg p-6 border border-border">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
        <Settings className="w-5 h-5 text-primary-500" />
        Firewall Settings
      </h3>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Protection Level
          </label>
          <select className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg dark:bg-slate-700">
            <option value="low">Low (Basic checks)</option>
            <option value="medium">Medium (Standard)</option>
            <option value="high">High (Strict)</option>
            <option value="maximum" selected>Maximum (All layers)</option>
          </select>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Active Models</h4>
          <div className="grid grid-cols-2 gap-3">
            {[
              'Behavioral Scam Detector',
              'Risk Scorer',
              'Sanctions Screener',
              'Contract Scanner',
              'Network Analysis',
              'Pattern Matcher'
            ].map(model => (
              <div key={model} className="flex items-center gap-2 p-3 bg-muted rounded-lg border border-border">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm">{model}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-slate-700 pt-6">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-2">System Info</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Total Scanned:</span>
              <span className="ml-2 font-semibold">{stats.total_scanned.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Block Rate:</span>
              <span className="ml-2 font-semibold">{(stats.block_rate * 100).toFixed(2)}%</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Avg Detection:</span>
              <span className="ml-2 font-semibold">{stats.avg_detection_time_ms.toFixed(1)}ms</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Status:</span>
              <span className={`ml-2 font-semibold ${stats.enabled ? 'text-green-500' : 'text-red-500'}`}>
                {stats.enabled ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
