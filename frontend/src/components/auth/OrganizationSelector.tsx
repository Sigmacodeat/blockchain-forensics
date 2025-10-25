/**
 * Organization Selector Component
 * Für Registration-Form: User wählt Organization-Type für 10% Rabatt
 */

import React from 'react'
import { motion } from 'framer-motion'
import { Shield, Search, Scale, Building2, Globe, User, Sparkles, CheckCircle2 } from 'lucide-react'

export interface OrganizationSelectorProps {
  value?: string
  organizationName?: string
  wantsDiscount?: boolean
  onChange: (type: string | undefined, name: string | undefined, wantsDiscount: boolean) => void
  className?: string
}

const ORGANIZATION_TYPES = [
  {
    value: 'police',
    label: 'Polizei & Ermittlungsbehörden',
    icon: Shield,
    color: 'from-blue-500 to-blue-600',
    description: 'LKA, BKA, Polizei, Interpol, FBI, etc.'
  },
  {
    value: 'detective',
    label: 'Privatdetektiv & Agentur',
    icon: Search,
    color: 'from-purple-500 to-purple-600',
    description: 'Investigation Agencies, Private Investigators'
  },
  {
    value: 'lawyer',
    label: 'Anwalt & Staatsanwalt',
    icon: Scale,
    color: 'from-green-500 to-green-600',
    description: 'Lawyers, Prosecutors, Legal Professionals'
  },
  {
    value: 'government',
    label: 'Regierung & Behörden',
    icon: Globe,
    color: 'from-orange-500 to-orange-600',
    description: 'Government Agencies, Public Sector'
  },
  {
    value: 'exchange',
    label: 'Exchange & Bank',
    icon: Building2,
    color: 'from-pink-500 to-pink-600',
    description: 'Crypto Exchanges, Financial Institutions'
  },
  {
    value: 'other',
    label: 'Andere',
    icon: User,
    color: 'from-slate-500 to-slate-600',
    description: 'Other organizations or individuals'
  }
]

export default function OrganizationSelector({
  value,
  organizationName,
  wantsDiscount = false,
  onChange,
  className = ''
}: OrganizationSelectorProps) {
  const [isExpanded, setIsExpanded] = React.useState(false)
  const [localName, setLocalName] = React.useState(organizationName || '')

  const handleTypeSelect = (type: string) => {
    onChange(type, localName, type !== 'other')
    setIsExpanded(true)
  }

  const handleNameChange = (name: string) => {
    setLocalName(name)
    onChange(value, name, wantsDiscount)
  }

  const handleDiscountChange = (checked: boolean) => {
    onChange(value, localName, checked)
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Info Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg p-4 text-white"
      >
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 flex-shrink-0 mt-0.5 animate-pulse" />
          <div className="flex-1">
            <div className="font-bold text-lg mb-1">
              💡 Institutioneller Rabatt verfügbar!
            </div>
            <div className="text-sm opacity-90">
              Polizei, Detektive, Anwälte & Regierungen erhalten <strong>10% zusätzlichen Rabatt</strong>.
              Zusammen mit Jahresrabatt: <strong>30% Gesamt-Ersparnis!</strong>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Organization Type Selection */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
          Gehören Sie zu einer Institution? (Optional)
        </label>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {ORGANIZATION_TYPES.map((org) => {
            const Icon = org.icon
            const isSelected = value === org.value
            
            return (
              <motion.button
                key={org.value}
                type="button"
                onClick={() => handleTypeSelect(org.value)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`
                  relative p-4 rounded-xl border-2 transition-all text-left
                  ${isSelected 
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-600'
                  }
                `}
              >
                {isSelected && (
                  <div className="absolute top-2 right-2">
                    <CheckCircle2 className="w-5 h-5 text-blue-500" />
                  </div>
                )}
                
                <div className={`inline-flex p-2 bg-gradient-to-br ${org.color} rounded-lg mb-2`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                
                <div className="font-semibold text-sm mb-1 text-slate-900 dark:text-white">
                  {org.label}
                </div>
                
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  {org.description}
                </div>
              </motion.button>
            )
          })}
        </div>
      </div>

      {/* Organization Name (if type selected) */}
      {value && value !== 'other' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Name Ihrer Organisation (Optional)
          </label>
          <input
            type="text"
            value={localName}
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="z.B. LKA Berlin, Smith Investigation Agency, etc."
            className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg 
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
          />
        </motion.div>
      )}

      {/* Discount Request Checkbox (if type selected and not 'other') */}
      {value && value !== 'other' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800"
        >
          <label className="flex items-start gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={wantsDiscount}
              onChange={(e) => handleDiscountChange(e.target.checked)}
              className="mt-1 w-5 h-5 text-green-600 border-green-300 rounded 
                       focus:ring-green-500 focus:ring-2 cursor-pointer"
            />
            <div className="flex-1">
              <div className="font-semibold text-sm text-green-700 dark:text-green-300 mb-1 group-hover:text-green-600 dark:group-hover:text-green-200 transition">
                ✅ Ich möchte 10% institutionellen Rabatt beantragen
              </div>
              <div className="text-xs text-green-600 dark:text-green-400">
                Nach Registration: Nachweis hochladen (Dienstausweis, Lizenz, etc.)
                <br />
                Bearbeitung: 24-48 Stunden | Bei @gov/@polizei-Email: Sofort-Aktivierung möglich
              </div>
            </div>
          </label>
        </motion.div>
      )}

      {/* Savings Preview (if discount requested) */}
      {wantsDiscount && value !== 'other' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg p-4 text-white"
        >
          <div className="text-sm font-semibold mb-2">
            💰 Ihre potenzielle Ersparnis:
          </div>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <div className="opacity-80">Jahresrabatt</div>
              <div className="text-lg font-bold">20%</div>
            </div>
            <div>
              <div className="opacity-80">Institutionell</div>
              <div className="text-lg font-bold">+10%</div>
            </div>
            <div>
              <div className="opacity-80">Gesamt</div>
              <div className="text-lg font-bold">30%</div>
            </div>
          </div>
          <div className="mt-2 text-xs opacity-90">
            Pro Plan: $855/Jahr (statt $1,188) → Sie sparen $333!
          </div>
        </motion.div>
      )}
    </div>
  )
}
