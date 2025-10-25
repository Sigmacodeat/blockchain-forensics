import React, { useState, useEffect } from 'react';
import { Plus, Trash2, ToggleLeft, ToggleRight, Mail, Webhook, Shield } from 'lucide-react';

interface CustomerMonitor {
  monitor_id: string;
  customer_name: string;
  wallet_addresses: string[];
  alert_on: string[];
  notify_email?: string;
  notify_webhook?: string;
  enabled: boolean;
  created_at: string;
  last_alert?: string;
  total_scans: number;
  total_blocks: number;
}

const CustomerMonitorManager: React.FC = () => {
  const [monitors, setMonitors] = useState<CustomerMonitor[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMonitor, setNewMonitor] = useState({
    customer_name: '',
    wallet_addresses: '',
    alert_on: ['critical', 'high'],
    notify_email: '',
    notify_webhook: ''
  });

  useEffect(() => {
    fetchMonitors();
  }, []);

  const fetchMonitors = async () => {
    try {
      const response = await fetch('/api/v1/firewall/customers', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setMonitors(data.monitors);
    } catch (error) {
      console.error('Failed to fetch monitors:', error);
    }
  };

  const addMonitor = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/firewall/customers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...newMonitor,
          wallet_addresses: newMonitor.wallet_addresses.split('\n').filter(a => a.trim())
        })
      });

      if (response.ok) {
        setShowAddForm(false);
        setNewMonitor({
          customer_name: '',
          wallet_addresses: '',
          alert_on: ['critical', 'high'],
          notify_email: '',
          notify_webhook: ''
        });
        fetchMonitors();
      }
    } catch (error) {
      console.error('Failed to add monitor:', error);
    }
  };

  const deleteMonitor = async (monitorId: string) => {
    if (!confirm('Are you sure you want to delete this customer monitor?')) return;
    
    try {
      await fetch(`/api/v1/firewall/customers/${monitorId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      fetchMonitors();
    } catch (error) {
      console.error('Failed to delete monitor:', error);
    }
  };

  const toggleMonitor = async (monitorId: string, enabled: boolean) => {
    try {
      await fetch(`/api/v1/firewall/customers/${monitorId}/toggle?enabled=${!enabled}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      fetchMonitors();
    } catch (error) {
      console.error('Failed to toggle monitor:', error);
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-primary-400" />
          Customer Monitoring
        </h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Add Customer
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <form onSubmit={addMonitor} className="bg-slate-700/50 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">New Customer Monitor</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Customer Name
              </label>
              <input
                type="text"
                value={newMonitor.customer_name}
                onChange={(e) => setNewMonitor({...newMonitor, customer_name: e.target.value})}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                placeholder="Bank-Kunde ABC123"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Wallet Addresses (one per line)
              </label>
              <textarea
                value={newMonitor.wallet_addresses}
                onChange={(e) => setNewMonitor({...newMonitor, wallet_addresses: e.target.value})}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white h-32"
                placeholder="0x123...&#10;0x456..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Alert On
              </label>
              <div className="flex gap-4">
                {['critical', 'high', 'medium', 'low'].map(level => (
                  <label key={level} className="flex items-center gap-2 text-slate-300">
                    <input
                      type="checkbox"
                      checked={newMonitor.alert_on.includes(level)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewMonitor({...newMonitor, alert_on: [...newMonitor.alert_on, level]});
                        } else {
                          setNewMonitor({...newMonitor, alert_on: newMonitor.alert_on.filter(l => l !== level)});
                        }
                      }}
                      className="rounded"
                    />
                    {level}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <Mail className="w-4 h-4 inline mr-2" />
                Notification Email (optional)
              </label>
              <input
                type="email"
                value={newMonitor.notify_email}
                onChange={(e) => setNewMonitor({...newMonitor, notify_email: e.target.value})}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                placeholder="compliance@bank.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <Webhook className="w-4 h-4 inline mr-2" />
                Webhook URL (optional)
              </label>
              <input
                type="url"
                value={newMonitor.notify_webhook}
                onChange={(e) => setNewMonitor({...newMonitor, notify_webhook: e.target.value})}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                placeholder="https://your-system.com/webhooks/firewall"
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Create Monitor
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-6 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Monitors List */}
      <div className="space-y-4">
        {monitors.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No customer monitors configured yet</p>
            <p className="text-sm mt-2">Click "Add Customer" to start monitoring</p>
          </div>
        ) : (
          monitors.map((monitor) => (
            <div
              key={monitor.monitor_id}
              className="bg-slate-700/50 rounded-lg p-6 border border-slate-600"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">
                    {monitor.customer_name}
                  </h3>
                  <p className="text-sm text-slate-400">
                    {monitor.wallet_addresses.length} wallet(s) monitored
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleMonitor(monitor.monitor_id, monitor.enabled)}
                    className={`p-2 rounded-lg ${
                      monitor.enabled ? 'bg-green-600 hover:bg-green-700' : 'bg-slate-600 hover:bg-slate-700'
                    }`}
                    title={monitor.enabled ? 'Enabled' : 'Disabled'}
                  >
                    {monitor.enabled ? (
                      <ToggleRight className="w-5 h-5 text-white" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-white" />
                    )}
                  </button>
                  <button
                    onClick={() => deleteMonitor(monitor.monitor_id)}
                    className="p-2 rounded-lg bg-red-600 hover:bg-red-700"
                  >
                    <Trash2 className="w-5 h-5 text-white" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Total Scans:</span>
                  <p className="text-white font-semibold mt-1">{monitor.total_scans}</p>
                </div>
                <div>
                  <span className="text-slate-400">Blocks:</span>
                  <p className="text-white font-semibold mt-1">{monitor.total_blocks}</p>
                </div>
                <div>
                  <span className="text-slate-400">Block Rate:</span>
                  <p className="text-white font-semibold mt-1">
                    {monitor.total_scans > 0 
                      ? ((monitor.total_blocks / monitor.total_scans) * 100).toFixed(1)
                      : 0}%
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Last Alert:</span>
                  <p className="text-white font-semibold mt-1">
                    {monitor.last_alert 
                      ? new Date(monitor.last_alert).toLocaleString() 
                      : 'Never'}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-600">
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs text-slate-400">Alert on:</span>
                  {monitor.alert_on.map(level => (
                    <span
                      key={level}
                      className="px-2 py-1 bg-slate-600 text-slate-200 rounded text-xs"
                    >
                      {level}
                    </span>
                  ))}
                </div>
                {monitor.notify_email && (
                  <p className="text-xs text-slate-400 mt-2">
                    <Mail className="w-3 h-3 inline mr-1" />
                    {monitor.notify_email}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CustomerMonitorManager;
