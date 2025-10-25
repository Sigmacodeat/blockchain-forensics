import { motion } from 'framer-motion'
import { ArrowRight, Check } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero */}
      <div className="max-w-7xl mx-auto px-4 pt-20 pb-16">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI ChatBot Pro
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Professional tool for blockchain analysis
          </p>
          <button className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 flex items-center gap-2 mx-auto">
            Get Started <ArrowRight size={20} />
          </button>
        </motion.div>
      </div>

      {/* Pricing */}
      <div className="max-w-7xl mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Pricing</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { name: 'Tier 1', price: 59, features: ['Feature 1', 'Feature 2'] },
            { name: 'Tier 2', price: 119, features: ['All Tier 1', 'Feature 3', 'Feature 4'] },
            { name: 'Tier 3', price: 199, features: ['All Tier 2', 'Feature 5', 'Unlimited'] }
          ].map(tier => (
            <div key={tier.name} className="border rounded-lg p-6 bg-white shadow-sm">
              <h3 className="text-xl font-bold mb-2">{tier.name}</h3>
              <div className="text-4xl font-bold mb-4">${tier.price}</div>
              <ul className="space-y-2">
                {tier.features.map(f => (
                  <li key={f} className="flex items-center gap-2">
                    <Check size={16} className="text-green-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
