import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, FileText, User, Calendar, AlertCircle, 
  CheckCircle, Clock, MessageSquare, Send, History,
  ExternalLink, Tag, Edit2, Save, X
} from 'lucide-react';

interface CaseDetail {
  case_id: string;
  case_type: string;
  title: string;
  description: string;
  customer_id: string;
  customer_name: string;
  customer_tier: string;
  status: string;
  priority: string;
  assigned_to?: string;
  assigned_to_name?: string;
  created_by: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  due_date?: string;
  closed_at?: string;
  decision?: string;
  decision_reason?: string;
  decision_by?: string;
  decision_at?: string;
  related_transactions: string[];
  related_addresses: string[];
  related_alerts: string[];
  tags: string[];
  actions: Array<{
    action_id: string;
    action_type: string;
    user_name: string;
    details: any;
    timestamp: string;
  }>;
  comments: Array<{
    comment_id: string;
    user_name: string;
    comment: string;
    is_internal: boolean;
    timestamp: string;
  }>;
}

const CaseDetail: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({ status: '', priority: '' });

  useEffect(() => {
    fetchCaseDetail();
  }, [caseId]);

  const fetchCaseDetail = async () => {
    try {
      const response = await fetch(`/api/v1/bank/cases/${caseId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setCaseData(data);
      setEditData({ status: data.status, priority: data.priority });
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch case:', error);
      setLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    try {
      await fetch(`/api/v1/bank/cases/${caseId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ comment: newComment, is_internal: true })
      });
      
      setNewComment('');
      fetchCaseDetail();
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
  };

  const handleUpdateStatus = async () => {
    try {
      await fetch(`/api/v1/bank/cases/${caseId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ new_status: editData.status })
      });
      
      setEditMode(false);
      fetchCaseDetail();
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const handleUpdatePriority = async () => {
    try {
      await fetch(`/api/v1/bank/cases/${caseId}/priority`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ new_priority: editData.priority })
      });
      
      setEditMode(false);
      fetchCaseDetail();
    } catch (error) {
      console.error('Failed to update priority:', error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-700';
      case 'in_progress': return 'bg-purple-100 text-purple-700';
      case 'awaiting_customer': return 'bg-yellow-100 text-yellow-700';
      case 'awaiting_approval': return 'bg-orange-100 text-orange-700';
      case 'resolved': return 'bg-green-100 text-green-700';
      case 'closed': return 'bg-gray-100 text-gray-700';
      case 'escalated': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="bg-slate-800 rounded-xl p-12 border border-slate-700 text-center">
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
          <h3 className="text-xl font-semibold text-white mb-2">Case Not Found</h3>
          <button
            onClick={() => navigate('/bank/cases')}
            className="mt-4 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Back to Cases
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/bank/cases')}
          className="flex items-center gap-2 text-slate-400 hover:text-white mb-4"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Cases
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{caseData.title}</h1>
            <p className="text-slate-400">Case ID: {caseData.case_id}</p>
          </div>
          <button
            onClick={() => setEditMode(!editMode)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600"
          >
            {editMode ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
            {editMode ? 'Cancel' : 'Edit'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Main Content - Left 2/3 */}
        <div className="col-span-2 space-y-6">
          {/* Case Details */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-4">Case Details</h2>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-400">Description</label>
                <p className="text-white mt-1">{caseData.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">Type</label>
                  <p className="text-white mt-1">
                    {caseData.case_type.replace(/_/g, ' ').toUpperCase()}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Customer</label>
                  <p className="text-white mt-1">{caseData.customer_name}</p>
                  <p className="text-xs text-slate-400">
                    {caseData.customer_tier.replace('_', ' ').toUpperCase()}
                  </p>
                </div>
              </div>

              {/* Status & Priority */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">Status</label>
                  {editMode ? (
                    <div className="flex gap-2">
                      <select
                        value={editData.status}
                        onChange={(e) => setEditData({ ...editData, status: e.target.value })}
                        className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
                      >
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="awaiting_customer">Awaiting Customer</option>
                        <option value="awaiting_approval">Awaiting Approval</option>
                        <option value="resolved">Resolved</option>
                        <option value="closed">Closed</option>
                        <option value="escalated">Escalated</option>
                      </select>
                      <button
                        onClick={handleUpdateStatus}
                        className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                      >
                        <Save className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <span className={`inline-block px-3 py-1 rounded-lg text-sm font-medium ${getStatusColor(caseData.status)}`}>
                      {caseData.status.replace('_', ' ').toUpperCase()}
                    </span>
                  )}
                </div>

                <div>
                  <label className="text-sm text-slate-400 mb-2 block">Priority</label>
                  {editMode ? (
                    <div className="flex gap-2">
                      <select
                        value={editData.priority}
                        onChange={(e) => setEditData({ ...editData, priority: e.target.value })}
                        className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                      <button
                        onClick={handleUpdatePriority}
                        className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                      >
                        <Save className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(caseData.priority)}`}>
                      {caseData.priority.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>

              {/* Tags */}
              {caseData.tags.length > 0 && (
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">Tags</label>
                  <div className="flex flex-wrap gap-2">
                    {caseData.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-slate-700 text-slate-300 rounded-full text-sm flex items-center gap-1"
                      >
                        <Tag className="w-3 h-3" />
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Related Data */}
          {(caseData.related_transactions.length > 0 || caseData.related_addresses.length > 0) && (
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
              <h2 className="text-xl font-semibold text-white mb-4">Related Data</h2>
              
              {caseData.related_transactions.length > 0 && (
                <div className="mb-4">
                  <label className="text-sm text-slate-400 mb-2 block">Transactions</label>
                  <div className="space-y-2">
                    {caseData.related_transactions.map((tx) => (
                      <div key={tx} className="flex items-center gap-2 text-sm">
                        <code className="flex-1 px-3 py-2 bg-slate-900 rounded text-primary-400 font-mono">
                          {tx}
                        </code>
                        <button className="p-2 text-slate-400 hover:text-white">
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {caseData.related_addresses.length > 0 && (
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">Addresses</label>
                  <div className="space-y-2">
                    {caseData.related_addresses.map((addr) => (
                      <div key={addr} className="flex items-center gap-2 text-sm">
                        <code className="flex-1 px-3 py-2 bg-slate-900 rounded text-primary-400 font-mono">
                          {addr}
                        </code>
                        <button className="p-2 text-slate-400 hover:text-white">
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Timeline */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <History className="w-5 h-5" />
              Timeline
            </h2>

            <div className="space-y-4">
              {/* Combine actions and comments, sort by timestamp */}
              {[
                ...caseData.actions.map(a => ({ ...a, type: 'action' })),
                ...caseData.comments.map(c => ({ ...c, type: 'comment' }))
              ]
                .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                .map((item: any, idx) => (
                  <div key={idx} className="flex gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                      {item.type === 'comment' ? (
                        <MessageSquare className="w-4 h-4 text-white" />
                      ) : (
                        <History className="w-4 h-4 text-white" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-1">
                        <p className="text-white font-medium">{item.user_name}</p>
                        <span className="text-xs text-slate-400">{formatDate(item.timestamp)}</span>
                      </div>
                      {item.type === 'comment' ? (
                        <p className="text-slate-300">{item.comment}</p>
                      ) : (
                        <p className="text-slate-400 text-sm">
                          {item.action_type.replace('_', ' ').toUpperCase()}
                          {item.details && Object.keys(item.details).length > 0 && (
                            <span className="ml-2 text-slate-500">
                              {JSON.stringify(item.details)}
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Add Comment */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Add Comment
            </h2>
            <div className="flex gap-3">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a comment..."
                className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white resize-none h-24"
              />
              <button
                onClick={handleAddComment}
                disabled={!newComment.trim()}
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar - Right 1/3 */}
        <div className="space-y-6">
          {/* Meta Info */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">Information</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-slate-500">Created By</label>
                <p className="text-white mt-1">{caseData.created_by_name}</p>
                <p className="text-xs text-slate-400">{formatDate(caseData.created_at)}</p>
              </div>

              <div>
                <label className="text-xs text-slate-500">Assigned To</label>
                <p className="text-white mt-1">
                  {caseData.assigned_to_name || (
                    <span className="text-slate-500 italic">Unassigned</span>
                  )}
                </p>
              </div>

              {caseData.due_date && (
                <div>
                  <label className="text-xs text-slate-500">Due Date</label>
                  <p className={`mt-1 ${new Date(caseData.due_date) < new Date() ? 'text-red-400' : 'text-white'}`}>
                    {formatDate(caseData.due_date)}
                  </p>
                </div>
              )}

              <div>
                <label className="text-xs text-slate-500">Last Updated</label>
                <p className="text-white mt-1">{formatDate(caseData.updated_at)}</p>
              </div>

              {caseData.closed_at && (
                <div>
                  <label className="text-xs text-slate-500">Closed At</label>
                  <p className="text-white mt-1">{formatDate(caseData.closed_at)}</p>
                </div>
              )}
            </div>
          </div>

          {/* Decision */}
          {caseData.decision && (
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Decision</h3>
              <div className="space-y-3">
                <div>
                  <span className="inline-block px-3 py-1 bg-green-600 text-white rounded-lg text-sm font-medium">
                    {caseData.decision.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                {caseData.decision_reason && (
                  <p className="text-slate-300 text-sm">{caseData.decision_reason}</p>
                )}
                {caseData.decision_by && (
                  <p className="text-xs text-slate-500">
                    By {caseData.decision_by} at {formatDate(caseData.decision_at!)}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CaseDetail;
