/**
 * Admin Dashboard for Crypto Payments
 * Shows all payments, analytics, and conversion metrics
 */
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle,
  XCircle,
  Clock,
  Bitcoin,
  Download,
  Filter,
  Calendar
} from 'lucide-react';
import api from '@/lib/api';

interface Payment {
  id: number;
  payment_id: number;
  order_id: string;
  user_id: string;
  plan_name: string;
  pay_currency: string;
  pay_amount: number;
  price_amount: number;
  payment_status: string;
  pay_in_hash?: string;
  created_at: string;
  updated_at?: string;
}

interface Analytics {
  total_payments: number;
  successful_payments: number;
  failed_payments: number;
  pending_payments: number;
  total_revenue_usd: number;
  conversion_rate: number;
  popular_currencies: Array<{ currency: string; count: number }>;
  revenue_by_plan: Array<{ plan: string; revenue: number }>;
}

export const CryptoPaymentsAdmin: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'finished' | 'pending' | 'failed'>('all');
  const [dateRange, setDateRange] = useState<'today' | 'week' | 'month' | 'all'>('month');

  useEffect(() => {
    fetchData();
  }, [filter, dateRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch payments
      const paymentsResponse = await api.get('/api/v1/admin/crypto-payments/list', {
        params: { filter, date_range: dateRange }
      });
      setPayments(paymentsResponse.data.payments || []);
      
      // Fetch analytics
      const analyticsResponse = await api.get('/api/v1/admin/crypto-payments/analytics', {
        params: { date_range: dateRange }
      });
      setAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      finished: 'text-green-600 bg-green-100 dark:bg-green-900/20',
      pending: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20',
      waiting: 'text-blue-600 bg-blue-100 dark:bg-blue-900/20',
      confirming: 'text-blue-600 bg-blue-100 dark:bg-blue-900/20',
      failed: 'text-red-600 bg-red-100 dark:bg-red-900/20',
      expired: 'text-gray-600 bg-gray-100 dark:bg-gray-900/20'
    };
    return colors[status] || 'text-gray-600 bg-gray-100';
  };

  const getStatusIcon = (status: string) => {
    if (status === 'finished') return <CheckCircle className="w-4 h-4" />;
    if (status === 'failed' || status === 'expired') return <XCircle className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  const exportToCSV = () => {
    // CSV Export logic
    const csv = [
      ['Order ID', 'User ID', 'Plan', 'Currency', 'Amount', 'Status', 'Date'].join(','),
      ...payments.map(p => [
        p.order_id,
        p.user_id,
        p.plan_name,
        p.pay_currency.toUpperCase(),
        p.pay_amount,
        p.payment_status,
        new Date(p.created_at).toLocaleString()
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crypto-payments-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Bitcoin className="w-8 h-8 text-primary-600" />
            Crypto Payments Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Übersicht aller Kryptowährungs-Zahlungen und Metriken
          </p>
        </div>

        {/* Analytics Cards */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-600 dark:text-gray-400 text-sm">Total Payments</span>
                <DollarSign className="w-5 h-5 text-primary-600" />
              </div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                {analytics.total_payments}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                ${analytics.total_revenue_usd.toLocaleString()} USD
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-600 dark:text-gray-400 text-sm">Successful</span>
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div className="text-3xl font-bold text-green-600">
                {analytics.successful_payments}
              </div>
              <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
                <TrendingUp className="w-3 h-3" />
                {analytics.conversion_rate.toFixed(1)}% conversion
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-600 dark:text-gray-400 text-sm">Pending</span>
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div className="text-3xl font-bold text-yellow-600">
                {analytics.pending_payments}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Awaiting confirmation
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-600 dark:text-gray-400 text-sm">Failed</span>
                <XCircle className="w-5 h-5 text-red-600" />
              </div>
              <div className="text-3xl font-bold text-red-600">
                {analytics.failed_payments}
              </div>
              <div className="flex items-center gap-1 text-xs text-red-600 mt-1">
                <TrendingDown className="w-3 h-3" />
                {((analytics.failed_payments / analytics.total_payments) * 100).toFixed(1)}% failure rate
              </div>
            </motion.div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-lg mb-6 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter:</span>
            {['all', 'finished', 'pending', 'failed'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f as any)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filter === f
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <Calendar className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value as any)}
              className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 border-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="all">All Time</option>
            </select>
            
            <button
              onClick={exportToCSV}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg flex items-center gap-2 hover:bg-primary-700 transition"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Payments Table */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-slate-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Order ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    TX Hash
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-slate-700">
                {payments.map((payment) => (
                  <motion.tr
                    key={payment.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="hover:bg-gray-50 dark:hover:bg-slate-700/50 transition"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {payment.order_id.slice(0, 16)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                      <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
                        {payment.plan_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {payment.pay_amount} {payment.pay_currency.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500">
                          ≈ ${payment.price_amount}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(payment.payment_status)}`}>
                        {getStatusIcon(payment.payment_status)}
                        {payment.payment_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                      {payment.pay_in_hash ? (
                        <a
                          href={`https://etherscan.io/tx/${payment.pay_in_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-700 font-mono text-xs"
                        >
                          {payment.pay_in_hash.slice(0, 10)}...
                        </a>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {new Date(payment.created_at).toLocaleString()}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Popular Currencies & Revenue by Plan */}
        {analytics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Popular Currencies
              </h3>
              <div className="space-y-3">
                {analytics.popular_currencies.map((item, index) => (
                  <div key={item.currency} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
                        {item.currency.toUpperCase().slice(0, 2)}
                      </div>
                      <span className="font-medium text-gray-700 dark:text-gray-300">
                        {item.currency.toUpperCase()}
                      </span>
                    </div>
                    <span className="text-gray-900 dark:text-white font-semibold">
                      {item.count} payments
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Revenue by Plan
              </h3>
              <div className="space-y-3">
                {analytics.revenue_by_plan.map((item) => (
                  <div key={item.plan} className="flex items-center justify-between">
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      {item.plan.charAt(0).toUpperCase() + item.plan.slice(1)}
                    </span>
                    <span className="text-gray-900 dark:text-white font-semibold">
                      ${item.revenue.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CryptoPaymentsAdmin;
