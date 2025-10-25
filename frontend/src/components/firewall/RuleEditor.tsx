import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, Save, X, Shield, AlertCircle } from 'lucide-react';

interface FirewallRule {
  rule_id: string;
  rule_type: string;
  condition: Record<string, any>;
  action: string;
  priority: number;
  enabled: boolean;
  created_at: string;
  auto_generated: boolean;
  description?: string;
}

type RuleCondition = 
  | { address: string }
  | { contract: string }
  | Record<string, any>;

interface NewRuleForm {
  rule_type: string;
  condition: RuleCondition;
  action: string;
  priority: number;
  description: string;
}

const RuleEditor: React.FC = () => {
  const [rules, setRules] = useState<FirewallRule[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingRule, setEditingRule] = useState<string | null>(null);
  const [newRule, setNewRule] = useState<NewRuleForm>({
    rule_type: 'address',
    condition: { address: '' },
    action: 'block',
    priority: 100,
    description: ''
  });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await fetch('/api/v1/firewall/rules', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setRules(data.rules);
    } catch (error) {
      console.error('Failed to fetch rules:', error);
    }
  };

  const addRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/firewall/rules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newRule)
      });

      if (response.ok) {
        setShowAddForm(false);
        setNewRule({
          rule_type: 'address',
          condition: { address: '' },
          action: 'block',
          priority: 100,
          description: ''
        });
        fetchRules();
      }
    } catch (error) {
      console.error('Failed to add rule:', error);
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    
    try {
      await fetch(`/api/v1/firewall/rules/${ruleId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      fetchRules();
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'block': return 'bg-red-600 text-white';
      case 'warn': return 'bg-yellow-600 text-white';
      case 'require_2fa': return 'bg-orange-600 text-white';
      case 'allow': return 'bg-green-600 text-white';
      default: return 'bg-slate-600 text-white';
    }
  };

  const getRuleTypeIcon = (type: string) => {
    switch (type) {
      case 'address': return '🎯';
      case 'contract': return '📜';
      case 'pattern': return '🔍';
      case 'customer': return '👤';
      case 'ai': return '🤖';
      default: return '⚙️';
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-primary-400" />
          Firewall Rules
        </h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Add Rule
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <form onSubmit={addRule} className="bg-slate-700/50 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">New Firewall Rule</h3>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Rule Type
                </label>
                <select
                  value={newRule.rule_type}
                  onChange={(e) => {
                    const type = e.target.value;
                    setNewRule({
                      ...newRule,
                      rule_type: type,
                      condition: type === 'address' ? { address: '' } : 
                                type === 'contract' ? { contract: '' } : {}
                    });
                  }}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                >
                  <option value="address">Address</option>
                  <option value="contract">Contract</option>
                  <option value="pattern">Pattern</option>
                  <option value="customer">Customer</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Action
                </label>
                <select
                  value={newRule.action}
                  onChange={(e) => setNewRule({...newRule, action: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                >
                  <option value="block">Block</option>
                  <option value="warn">Warn</option>
                  <option value="require_2fa">Require 2FA</option>
                  <option value="allow">Allow</option>
                </select>
              </div>
            </div>

            {newRule.rule_type === 'address' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Address
                </label>
                <input
                  type="text"
                  value={'address' in newRule.condition ? newRule.condition.address : ''}
                  onChange={(e) => setNewRule({
                    ...newRule,
                    condition: { address: e.target.value }
                  })}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white font-mono"
                  placeholder="0x123..."
                  required
                />
              </div>
            )}

            {newRule.rule_type === 'contract' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Contract Address
                </label>
                <input
                  type="text"
                  value={'contract' in newRule.condition ? newRule.condition.contract : ''}
                  onChange={(e) => setNewRule({
                    ...newRule,
                    condition: { contract: e.target.value }
                  })}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white font-mono"
                  placeholder="0xabc..."
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Priority (0-999, higher = executes first)
              </label>
              <input
                type="number"
                value={newRule.priority}
                onChange={(e) => setNewRule({...newRule, priority: parseInt(e.target.value)})}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                min="0"
                max="999"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Description (optional)
              </label>
              <input
                type="text"
                value={newRule.description}
                onChange={(e) => setNewRule({...newRule, description: e.target.value})}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                placeholder="Block known scammer address"
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Create Rule
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

      {/* Rules List */}
      <div className="space-y-3">
        {rules.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <AlertCircle className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No custom rules configured</p>
            <p className="text-sm mt-2">Add rules to customize firewall behavior</p>
          </div>
        ) : (
          rules
            .sort((a, b) => b.priority - a.priority)
            .map((rule) => (
              <div
                key={rule.rule_id}
                className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 flex items-center justify-between"
              >
                <div className="flex items-center gap-4 flex-1">
                  <span className="text-2xl">{getRuleTypeIcon(rule.rule_type)}</span>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-mono text-white font-semibold">
                        {rule.rule_type === 'address' && rule.condition.address}
                        {rule.rule_type === 'contract' && rule.condition.contract}
                        {rule.rule_type === 'pattern' && 'Pattern Match'}
                        {rule.rule_type === 'customer' && 'Customer Rule'}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getActionColor(rule.action)}`}>
                        {rule.action}
                      </span>
                      <span className="px-2 py-1 bg-slate-600 text-slate-200 rounded text-xs">
                        Priority: {rule.priority}
                      </span>
                      {rule.auto_generated && (
                        <span className="px-2 py-1 bg-purple-600 text-white rounded text-xs">
                          AI Generated
                        </span>
                      )}
                    </div>
                    {rule.description && (
                      <p className="text-sm text-slate-400">{rule.description}</p>
                    )}
                    <p className="text-xs text-slate-500 mt-1">
                      Created: {new Date(rule.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => deleteRule(rule.rule_id)}
                    className="p-2 rounded-lg bg-red-600 hover:bg-red-700"
                    title="Delete rule"
                  >
                    <Trash2 className="w-4 h-4 text-white" />
                  </button>
                </div>
              </div>
            ))
        )}
      </div>

      {/* Info Box */}
      <div className="mt-6 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-slate-300">
            <p className="font-semibold text-white mb-1">Rule Execution Order</p>
            <p>Rules are executed by priority (highest first). If multiple rules match, the first matching rule determines the action.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RuleEditor;
