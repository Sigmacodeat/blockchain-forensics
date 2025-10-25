import React, { useState, useEffect } from 'react';
import { Shield, Activity, Users, AlertTriangle, Clock, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DashboardAnalytics {
  overview: {
    total_scanned_24h: number;
    blocked_24h: number;
    critical_24h: number;
    block_rate_24h: number;
  };
  threat_distribution: Record<string, number>;
  top_threats: [string, number][];
  hourly_stats: Array<{
    hour: string;
    total: number;
    blocked: number;
    critical: number;
    high: number;
  }>;
  customer_stats: Array<{
    customer_name: string;
    total_scans: number;
    total_blocks: number;
    block_rate: number;
    last_alert: string | null;
  }>;
  active_monitors: number;
}

interface Activity {
  activity_id: string;
  timestamp: string;
  tx_hash: string;
  chain: string;
  from_address: string;
  to_address: string;
  value_usd: number;
  threat_level: string;
  action_taken: string;
  threat_types: string[];
  customer_monitor_id?: string;
  confidence: number;
}

const FirewallDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Fetch initial data
  useEffect(() => {
    fetchDashboardData();
    fetchActivities();
    connectWebSocket();

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/firewall/dashboard', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setAnalytics(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  const fetchActivities = async () => {
    try {
      const response = await fetch('/api/v1/firewall/activities?limit=50', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setActivities(data.activities);
    } catch (error) {
      console.error('Failed to fetch activities:', error);
    }
  };

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    const wsUrl = `ws://localhost:8000/api/v1/firewall/stream?user_id=${token}`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => console.log('🔌 Firewall WebSocket connected');
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'scan.result') {
        // Update activities with new scan
        fetchActivities();
      } else if (data.type === 'dashboard.response') {
        setAnalytics(data.analytics);
      }
    };

    websocket.onerror = (error) => console.error('WebSocket error:', error);
    setWs(websocket);

    // Request updates every 10 seconds
    const interval = setInterval(() => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: 'dashboard' }));
      }
    }, 10000);

    return () => clearInterval(interval);
  };

  const getThreatColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-blue-600 bg-blue-100';
      default: return 'text-green-600 bg-green-100';
    }
  };

  if (loading || !analytics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Chart data
  const hourlyChartData = {
    labels: analytics.hourly_stats.map(s => s.hour),
    datasets: [
      {
        label: 'Total Scans',
        data: analytics.hourly_stats.map(s => s.total),
        borderColor: 'rgb(99, 102, 241)',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true,
      },
      {
        label: 'Blocked',
        data: analytics.hourly_stats.map(s => s.blocked),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
      }
    ]
  };

  const threatDistributionData = {
    labels: Object.keys(analytics.threat_distribution),
    datasets: [{
      data: Object.values(analytics.threat_distribution),
      backgroundColor: [
        'rgba(239, 68, 68, 0.8)',
        'rgba(249, 115, 22, 0.8)',
        'rgba(234, 179, 8, 0.8)',
        'rgba(59, 130, 246, 0.8)',
        'rgba(34, 197, 94, 0.8)'
      ],
    }]
  };

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Shield className="w-8 h-8 text-primary-400" />
          AI Firewall Dashboard
        </h1>
        <p className="text-slate-400 mt-2">Real-time threat monitoring & customer protection</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-slate-400 text-sm">Total Scanned (24h)</h3>
            <Activity className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white">{analytics.overview.total_scanned_24h}</p>
          <div className="mt-2 flex items-center gap-2 text-xs text-green-400">
            <TrendingUp className="w-4 h-4" />
            <span>Live monitoring</span>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-slate-400 text-sm">Blocked (24h)</h3>
            <XCircle className="w-5 h-5 text-red-400" />
          </div>
          <p className="text-3xl font-bold text-white">{analytics.overview.blocked_24h}</p>
          <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
            <span>{(analytics.overview.block_rate_24h * 100).toFixed(1)}% block rate</span>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-slate-400 text-sm">Critical Threats</h3>
            <AlertTriangle className="w-5 h-5 text-orange-400" />
          </div>
          <p className="text-3xl font-bold text-white">{analytics.overview.critical_24h}</p>
          <div className="mt-2 flex items-center gap-2 text-xs text-orange-400">
            <span>Requires immediate action</span>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-slate-400 text-sm">Active Monitors</h3>
            <Users className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-3xl font-bold text-white">{analytics.active_monitors}</p>
          <div className="mt-2 flex items-center gap-2 text-xs text-green-400">
            <CheckCircle className="w-4 h-4" />
            <span>Customers monitored</span>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4">Activity Timeline (24h)</h2>
          <Line 
            data={hourlyChartData} 
            options={{
              responsive: true,
              plugins: { legend: { labels: { color: '#fff' } } },
              scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
              }
            }}
          />
        </div>

        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4">Threat Distribution</h2>
          <Doughnut 
            data={threatDistributionData}
            options={{
              responsive: true,
              plugins: { legend: { labels: { color: '#fff' } } }
            }}
          />
        </div>
      </div>

      {/* Recent Activities */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Recent Activities
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Time</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">From</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">To</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Value</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Threat</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {activities.slice(0, 10).map((activity) => (
                <tr key={activity.activity_id} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="py-3 px-4 text-slate-300 text-sm">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-4 text-slate-300 text-sm font-mono">
                    {activity.from_address.slice(0, 10)}...
                  </td>
                  <td className="py-3 px-4 text-slate-300 text-sm font-mono">
                    {activity.to_address.slice(0, 10)}...
                  </td>
                  <td className="py-3 px-4 text-slate-300 text-sm">
                    ${activity.value_usd.toFixed(2)}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getThreatColor(activity.threat_level)}`}>
                      {activity.threat_level}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      activity.action_taken === 'block' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                    }`}>
                      {activity.action_taken}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FirewallDashboard;
