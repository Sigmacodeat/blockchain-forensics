import { useState } from 'react'
import { TrendingUp, TrendingDown, DollarSign, Wallet, PieChart } from 'lucide-react'
import { motion } from 'framer-motion'

export default function PortfolioTracker() {
  const [portfolio] = useState({
    totalValue: 45782.34,
    change24h: 3.42,
    assets: [
      { symbol: 'ETH', name: 'Ethereum', balance: 12.5, price: 2456.78, value: 30709.75, change: 5.2, allocation: 67 },
      { symbol: 'BTC', name: 'Bitcoin', balance: 0.234, price: 43521.45, value: 10184.06, change: 2.1, allocation: 22 },
      { symbol: 'USDT', name: 'Tether', balance: 4888.53, price: 1.0, value: 4888.53, change: 0.01, allocation: 11 }
    ]
  })

  return (
    <div className="w-full">
      {/* Total Value Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-blue-600 via-blue-700 to-purple-700 rounded-2xl shadow-2xl p-8 mb-6 text-white"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur">
              <Wallet size={24} />
            </div>
            <div>
              <p className="text-sm font-medium opacity-90">Total Portfolio Value</p>
              <h2 className="text-4xl font-bold">${portfolio.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</h2>
            </div>
          </div>
          <div className="text-right">
            <div className={`flex items-center gap-2 text-2xl font-bold ${portfolio.change24h >= 0 ? 'text-green-300' : 'text-red-300'}`}>
              {portfolio.change24h >= 0 ? <TrendingUp size={28} /> : <TrendingDown size={28} />}
              {portfolio.change24h >= 0 ? '+' : ''}{portfolio.change24h}%
            </div>
            <p className="text-sm opacity-75 mt-1">24h Change</p>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-white/20">
          <div>
            <p className="text-xs opacity-75">Assets</p>
            <p className="text-xl font-bold">{portfolio.assets.length}</p>
          </div>
          <div>
            <p className="text-xs opacity-75">Best Performer</p>
            <p className="text-xl font-bold">ETH +5.2%</p>
          </div>
          <div>
            <p className="text-xs opacity-75">Allocation</p>
            <p className="text-xl font-bold">3 Chains</p>
          </div>
        </div>
      </motion.div>

      {/* Assets List */}
      <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-900">Your Assets</h3>
            <button className="text-sm text-blue-600 hover:text-blue-700 font-semibold">
              Add Asset +
            </button>
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          {portfolio.assets.map((asset, idx) => (
            <motion.div
              key={asset.symbol}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="p-6 hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                    {asset.symbol.charAt(0)}
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900">{asset.symbol}</h4>
                    <p className="text-sm text-gray-600">{asset.name}</p>
                  </div>
                </div>

                <div className="text-right">
                  <p className="font-bold text-gray-900">${asset.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                  <p className="text-sm text-gray-600">{asset.balance} {asset.symbol}</p>
                </div>

                <div className="text-right">
                  <div className={`flex items-center gap-1 font-semibold ${asset.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {asset.change >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                    {asset.change >= 0 ? '+' : ''}{asset.change}%
                  </div>
                  <p className="text-sm text-gray-600">${asset.price.toLocaleString()}</p>
                </div>

                <div>
                  <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-600"
                      style={{ width: `${asset.allocation}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-600 text-center mt-1">{asset.allocation}%</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Charts Preview */}
      <div className="grid md:grid-cols-2 gap-6 mt-6">
        <ChartCard
          title="Asset Allocation"
          icon={<PieChart className="text-blue-600" />}
          description="Distribution of your portfolio"
        />
        <ChartCard
          title="Performance History"
          icon={<TrendingUp className="text-green-600" />}
          description="30-day portfolio performance"
        />
      </div>
    </div>
  )
}

function ChartCard({ title, icon, description }) {
  return (
    <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl transition-all hover:border-blue-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-gray-50 rounded-lg">
          {icon}
        </div>
        <div>
          <h4 className="font-bold text-gray-900">{title}</h4>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
      <div className="h-32 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-400 text-sm">Chart Preview</p>
      </div>
    </div>
  )
}
