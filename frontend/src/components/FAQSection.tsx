/**
 * FAQ Section Component - Ausklappbare FAQs mit SEO-Optimierung
 * Features: 
 * - Accordion-Style mit Framer Motion
 * - Schema.org FAQPage structured data
 * - i18n-ready mit Translation Keys
 * - SEO-optimiert für besseres Ranking
 */

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, HelpCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface FAQ {
  question: string
  answer: string
}

interface FAQSectionProps {
  title?: string
  description?: string
  faqs: FAQ[]
  categoryColor?: 'blue' | 'purple' | 'green' | 'orange'
  structuredData?: boolean // Add Schema.org structured data
}

export default function FAQSection({ 
  title = 'Häufig gestellte Fragen',
  description,
  faqs, 
  categoryColor = 'blue',
  structuredData = true 
}: FAQSectionProps) {
  const { t } = useTranslation()
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  const colorMap = {
    blue: {
      gradient: 'from-blue-500 to-purple-500',
      text: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      hover: 'hover:bg-blue-50 dark:hover:bg-blue-900/10'
    },
    purple: {
      gradient: 'from-purple-500 to-pink-500',
      text: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-50 dark:bg-purple-900/20',
      border: 'border-purple-200 dark:border-purple-800',
      hover: 'hover:bg-purple-50 dark:hover:bg-purple-900/10'
    },
    green: {
      gradient: 'from-green-500 to-blue-500',
      text: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      hover: 'hover:bg-green-50 dark:hover:bg-green-900/10'
    },
    orange: {
      gradient: 'from-orange-500 to-red-500',
      text: 'text-orange-600 dark:text-orange-400',
      bg: 'bg-orange-50 dark:bg-orange-900/20',
      border: 'border-orange-200 dark:border-orange-800',
      hover: 'hover:bg-orange-50 dark:hover:bg-orange-900/10'
    }
  }

  const colors = colorMap[categoryColor]

  // Generate Schema.org structured data
  const generateStructuredData = () => {
    if (!structuredData) return null

    const schemaData = {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": faqs.map(faq => ({
        "@type": "Question",
        "name": faq.question,
        "acceptedAnswer": {
          "@type": "Answer",
          "text": faq.answer
        }
      }))
    }

    return (
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaData) }}
      />
    )
  }

  return (
    <section className="py-12 px-6 bg-white/50 dark:bg-slate-900/50">
      {generateStructuredData()}
      
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-10"
        >
          <div className={`inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r ${colors.gradient} rounded-full mb-4`}>
            <HelpCircle className="w-4 h-4 text-white" />
            <span className="text-sm font-bold text-white">FAQ</span>
          </div>
          
          <h2 className="text-3xl md:text-4xl font-bold mb-3">{title}</h2>
          
          {description && (
            <p className="text-base text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              {description}
            </p>
          )}
        </motion.div>

        {/* FAQ Accordion */}
        <div className="space-y-3">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.05 }}
              className={`bg-white dark:bg-slate-800 rounded-lg border-2 ${colors.border} overflow-hidden`}
            >
              {/* Question Button */}
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className={`w-full px-5 py-4 flex items-center justify-between gap-4 text-left transition-colors ${colors.hover}`}
                aria-expanded={openIndex === index}
                aria-controls={`faq-answer-${index}`}
              >
                <span className={`font-bold text-base ${colors.text}`}>
                  {faq.question}
                </span>
                <motion.div
                  animate={{ rotate: openIndex === index ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex-shrink-0"
                >
                  <ChevronDown className={`w-5 h-5 ${colors.text}`} />
                </motion.div>
              </button>

              {/* Answer Content */}
              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    id={`faq-answer-${index}`}
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className={`px-5 py-4 ${colors.bg} border-t-2 ${colors.border}`}>
                      <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                        {faq.answer}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        {/* CTA am Ende */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="mt-10 text-center"
        >
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            Noch Fragen? Unser Team hilft Ihnen gerne weiter!
          </p>
          <a
            href={`/${t('lang')}/contact`}
            className={`inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r ${colors.gradient} text-white rounded-lg font-bold text-sm hover:shadow-xl transition-all`}
          >
            Kontakt aufnehmen
            <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
          </a>
        </motion.div>
      </div>
    </section>
  )
}
