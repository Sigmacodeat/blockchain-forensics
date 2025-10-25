import { useState } from 'react'
import { ChevronDown, Check, Lock, ExternalLink } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useUserProducts } from '@/hooks/useUserProducts'

const ALL_PRODUCTS = [
  { 
    id: 'chatbot', 
    name: 'AI ChatBot Pro', 
    icon: '💬', 
    color: 'purple',
    appsumoUrl: 'https://appsumo.com/products/your-chatbot' 
  },
  { 
    id: 'firewall', 
    name: 'Web3 Wallet Guardian', 
    icon: '🛡️', 
    color: 'green',
    appsumoUrl: 'https://appsumo.com/products/your-firewall'
  },
  { 
    id: 'inspector', 
    name: 'Crypto Inspector', 
    icon: '🔍', 
    color: 'blue',
    appsumoUrl: 'https://appsumo.com/products/your-inspector'
  },
  { 
    id: 'commander', 
    name: 'AI Commander', 
    icon: '🎯', 
    color: 'orange',
    appsumoUrl: 'https://appsumo.com/products/your-commander'
  }
]

export default function ProductSwitcher() {
  const [open, setOpen] = useState(false)
  const { data: userProducts, isLoading } = useUserProducts()
  
  // Get first active product as current
  const currentProduct = userProducts && userProducts.length > 0 
    ? ALL_PRODUCTS.find(p => p.id === userProducts[0].product)
    : null

  const hasAccess = (productId: string) => {
    return userProducts?.some(p => p.product === productId && p.status === 'active')
  }

  if (isLoading) {
    return (
      <div className="animate-pulse h-10 w-48 bg-slate-700 rounded-lg"></div>
    )
  }

  if (!currentProduct) {
    // User hat keine Produkte → zeige nichts oder "Get Started"
    return null
  }

  return (
    <div className="relative z-50">
      {/* Trigger Button */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg border border-white/20 transition-colors"
      >
        <span className="text-xl">{currentProduct.icon}</span>
        <span className="font-medium text-white hidden sm:inline">
          {currentProduct.name}
        </span>
        <ChevronDown 
          className={`w-4 h-4 text-white transition-transform ${
            open ? 'rotate-180' : ''
          }`} 
        />
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <div 
              className="fixed inset-0 z-40"
              onClick={() => setOpen(false)}
            />
            
            {/* Menu */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full left-0 mt-2 w-72 bg-slate-800 rounded-lg border border-slate-700 shadow-xl z-50"
            >
              <div className="p-2">
                {ALL_PRODUCTS.map((product) => {
                  const active = hasAccess(product.id)
                  const isCurrent = product.id === currentProduct?.id

                  return (
                    <div
                      key={product.id}
                      className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                        active
                          ? isCurrent
                            ? 'bg-purple-600 text-white'
                            : 'hover:bg-slate-700 text-white cursor-default'
                          : 'text-slate-400 hover:bg-slate-700/50'
                      }`}
                    >
                      <span className="text-2xl flex-shrink-0">{product.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{product.name}</div>
                        {!active && (
                          <div className="text-xs text-slate-400 flex items-center gap-1">
                            Not activated
                          </div>
                        )}
                        {active && !isCurrent && (
                          <div className="text-xs text-green-400">
                            Active
                          </div>
                        )}
                      </div>
                      {active && isCurrent && (
                        <Check className="w-4 h-4 flex-shrink-0" />
                      )}
                      {!active && (
                        <a
                          href={product.appsumoUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 flex-shrink-0"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Get
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Footer */}
              <div className="border-t border-slate-700 p-3 bg-slate-800/50">
                <p className="text-xs text-slate-400 text-center">
                  Get all 4 products on{' '}
                  <a
                    href="https://appsumo.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-400 hover:underline"
                  >
                    AppSumo
                  </a>
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
