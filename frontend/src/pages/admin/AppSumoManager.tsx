import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Package, Code, TrendingUp, Users, Download, Plus } from 'lucide-react';
import api from '@/lib/api';

interface Product {
  name: string;
  tiers: Record<number, { price: number; features: any }>;
}

interface Analytics {
  total_codes: number;
  by_status: Record<string, number>;
  by_product: Record<string, number>;
  active_activations: number;
  redemption_rate: number;
}

const AppSumoManager: React.FC = () => {
  const [selectedProduct, setSelectedProduct] = useState('chatbot');
  const [selectedTier, setSelectedTier] = useState(1);
  const [codeCount, setCodeCount] = useState(10);

  // Fetch analytics
  const { data: analytics } = useQuery<Analytics>({
    queryKey: ['appsumo-analytics'],
    queryFn: async () => {
      const res = await api.get('/api/v1/admin/appsumo/analytics');
      return res.data;
    }
  });

  // Fetch products
  const { data: productsData } = useQuery({
    queryKey: ['appsumo-products'],
    queryFn: async () => {
      const res = await api.get('/api/v1/admin/appsumo/products');
      return res.data;
    }
  });

  const products: Record<string, Product> = productsData?.products || {};

  // Generate codes mutation
  const generateMutation = useMutation({
    mutationFn: async (data: { product: string; tier: number; count: number }) => {
      const res = await api.post('/api/v1/admin/appsumo/codes/generate', data);
      return res.data;
    },
    onSuccess: (data) => {
      alert(`✅ ${data.count} codes generated!`);
      // Download as CSV
      const csv = data.codes.map((c: any) => c.code).join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `appsumo-codes-${selectedProduct}-tier${selectedTier}.csv`;
      a.click();
    }
  });

  const handleGenerate = () => {
    generateMutation.mutate({
      product: selectedProduct,
      tier: selectedTier,
      count: codeCount
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            AppSumo Manager
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage AppSumo codes, redemptions, and analytics
          </p>
        </div>

        {/* Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Codes</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {analytics?.total_codes || 0}
                </p>
              </div>
              <Code className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Active Users</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {analytics?.active_activations || 0}
                </p>
              </div>
              <Users className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Redemption Rate</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {analytics?.redemption_rate || 0}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Products</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {Object.keys(products).length}
                </p>
              </div>
              <Package className="w-8 h-8 text-orange-500" />
            </div>
          </div>
        </div>

        {/* Code Generator */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            <Plus className="inline w-5 h-5 mr-2" />
            Generate Codes
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label htmlFor="product" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Product
              </label>
              <select
                id="product"
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {Object.keys(products).map((key) => (
                  <option key={key} value={key}>
                    {products[key].name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="tier" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tier
              </label>
              <select
                id="tier"
                value={selectedTier}
                onChange={(e) => setSelectedTier(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={1}>Tier 1 - ${products[selectedProduct]?.tiers[1]?.price}</option>
                <option value={2}>Tier 2 - ${products[selectedProduct]?.tiers[2]?.price}</option>
                <option value={3}>Tier 3 - ${products[selectedProduct]?.tiers[3]?.price}</option>
              </select>
            </div>

            <div>
              <label htmlFor="count" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Count
              </label>
              <input
                id="count"
                type="number"
                value={codeCount}
                onChange={(e) => setCodeCount(Number(e.target.value))}
                min={1}
                max={1000}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              {codeCount > 1000 && (
                <p className="text-sm text-red-600 mt-1">maximum 1000 codes</p>
              )}
            </div>

            <div className="flex items-end">
              <button
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
                className="w-full px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-medium hover:shadow-lg disabled:opacity-50"
              >
                {generateMutation.isPending ? 'Generating...' : 'Generate & Download'}
              </button>
            </div>
          </div>
        </div>

        {/* By Product Stats */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Codes by Product
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {analytics?.by_product && Object.entries(analytics.by_product).map(([product, count]) => (
              <div key={product} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">{product}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{count}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppSumoManager;
