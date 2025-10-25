import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Flag, Plus, Trash2, Edit2, CheckCircle, XCircle,
  TrendingUp, Users, TestTube2, Activity, Save, X
} from 'lucide-react';
import api from '@/lib/api';
import { useTranslation } from 'react-i18next';

interface FeatureFlag {
  key: string;
  name: string;
  description: string;
  status: 'enabled' | 'disabled' | 'rollout' | 'ab_test';
  rollout_percentage: number;
  rollout_user_ids: string[];
  environment: string;
  created_at: string;
  updated_at: string;
}

export default function FeatureFlagsAdmin() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingFlag, setEditingFlag] = useState<FeatureFlag | null>(null);
  const [formData, setFormData] = useState({
    key: '',
    name: '',
    description: '',
    status: 'disabled' as const
  });

  // Fetch all flags
  const { data: flags, isLoading } = useQuery({
    queryKey: ['feature-flags'],
    queryFn: async () => {
      const response = await api.get('/api/v1/feature-flags/');
      return response.data as FeatureFlag[];
    }
  });

  // Create flag mutation
  const createFlagMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.post('/api/v1/feature-flags/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
      setShowCreateModal(false);
      setFormData({ key: '', name: '', description: '', status: 'disabled' });
    }
  });

  // Update flag mutation
  const updateFlagMutation = useMutation({
    mutationFn: async ({ key, data }: { key: string; data: any }) => {
      const response = await api.patch(`/api/v1/feature-flags/${key}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    }
  });

  // Delete flag mutation
  const deleteFlagMutation = useMutation({
    mutationFn: async (key: string) => {
      await api.delete(`/api/v1/feature-flags/${key}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    }
  });

  // Quick toggle enabled/disabled
  const toggleFlag = async (key: string, currentStatus: string) => {
    const newStatus = currentStatus === 'enabled' ? 'disabled' : 'enabled';
    await updateFlagMutation.mutateAsync({
      key,
      data: { status: newStatus }
    });
  };

  // Update rollout percentage
  const updateRollout = async (key: string, percentage: number) => {
    await updateFlagMutation.mutateAsync({
      key,
      data: { rollout_percentage: percentage }
    });
  };

  // Change status to rollout/ab_test
  const changeStatus = async (key: string, status: string) => {
    await updateFlagMutation.mutateAsync({
      key,
      data: { status }
    });
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      enabled: 'bg-green-500/20 text-green-400 border-green-500/30',
      disabled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
      rollout: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      ab_test: 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    };

    const icons = {
      enabled: <CheckCircle className="w-3 h-3" />,
      disabled: <XCircle className="w-3 h-3" />,
      rollout: <TrendingUp className="w-3 h-3" />,
      ab_test: <TestTube2 className="w-3 h-3" />
    };

    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${variants[status as keyof typeof variants]}`}>
        {icons[status as keyof typeof icons]}
        <span className="capitalize">{status.replace('_', ' ')}</span>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500">
              <Flag className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Feature Flags</h1>
              <p className="text-slate-400 mt-1">
                Manage feature rollouts and A/B tests
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl"
          >
            <Plus className="w-4 h-4" />
            Create Flag
          </button>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="p-4 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Flags</p>
              <p className="text-2xl font-bold text-white">{flags?.length || 0}</p>
            </div>
            <Flag className="w-8 h-8 text-purple-400" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="p-4 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Enabled</p>
              <p className="text-2xl font-bold text-green-400">
                {flags?.filter(f => f.status === 'enabled').length || 0}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="p-4 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Rollout</p>
              <p className="text-2xl font-bold text-yellow-400">
                {flags?.filter(f => f.status === 'rollout').length || 0}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-yellow-400" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="p-4 rounded-xl bg-slate-800/50 backdrop-blur-sm border border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">A/B Tests</p>
              <p className="text-2xl font-bold text-purple-400">
                {flags?.filter(f => f.status === 'ab_test').length || 0}
              </p>
            </div>
            <TestTube2 className="w-8 h-8 text-purple-400" />
          </div>
        </motion.div>
      </div>

      {/* Flags Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Flag
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Rollout
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-4 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {flags?.map((flag, index) => (
                <motion.tr
                  key={flag.key}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-slate-700/30 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-white">{flag.name}</div>
                      <div className="text-xs text-slate-400 mt-1">{flag.key}</div>
                      <div className="text-xs text-slate-500 mt-1">{flag.description}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getStatusBadge(flag.status)}
                      <select
                        value={flag.status}
                        onChange={(e) => changeStatus(flag.key, e.target.value)}
                        className="text-xs bg-slate-700 text-slate-300 rounded px-2 py-1 border border-slate-600"
                      >
                        <option value="enabled">Enabled</option>
                        <option value="disabled">Disabled</option>
                        <option value="rollout">Rollout</option>
                        <option value="ab_test">A/B Test</option>
                      </select>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {flag.status === 'rollout' ? (
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={flag.rollout_percentage}
                          onChange={(e) => updateRollout(flag.key, parseInt(e.target.value))}
                          className="w-32 accent-purple-500"
                        />
                        <span className="text-sm text-white font-medium min-w-[40px]">
                          {flag.rollout_percentage}%
                        </span>
                      </div>
                    ) : flag.status === 'ab_test' ? (
                      <span className="text-sm text-purple-400">50/50 Split</span>
                    ) : (
                      <span className="text-sm text-slate-500">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-400">
                    {new Date(flag.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => toggleFlag(flag.key, flag.status)}
                        className={`p-2 rounded-lg transition-colors ${
                          flag.status === 'enabled'
                            ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                            : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                        }`}
                        title={flag.status === 'enabled' ? 'Disable' : 'Enable'}
                      >
                        {flag.status === 'enabled' ? (
                          <XCircle className="w-4 h-4" />
                        ) : (
                          <CheckCircle className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Delete flag "${flag.name}"?`)) {
                            deleteFlagMutation.mutate(flag.key);
                          }
                        }}
                        className="p-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-700"
          >
            <h2 className="text-xl font-bold text-white mb-4">Create Feature Flag</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Key (unique identifier)
                </label>
                <input
                  type="text"
                  value={formData.key}
                  onChange={(e) => setFormData({ ...formData, key: e.target.value })}
                  placeholder="new_dashboard_ui"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="New Dashboard UI"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enable redesigned dashboard interface"
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createFlagMutation.mutate(formData)}
                  disabled={!formData.key || !formData.name || createFlagMutation.isPending}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createFlagMutation.isPending ? 'Creating...' : 'Create Flag'}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
