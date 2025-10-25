import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Book, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Blockchain Glossary for Beginners
 * Comprehensive dictionary of blockchain forensics terms
 */

interface GlossaryTerm {
  id: string;
  term: string;
  category: 'basic' | 'forensics' | 'advanced' | 'technical';
  definition: string;
  example?: string;
  relatedTerms?: string[];
}

const glossaryTerms: GlossaryTerm[] = [
  // BASIC TERMS
  {
    id: 'blockchain',
    term: 'Blockchain',
    category: 'basic',
    definition: 'Eine unveränderliche, dezentrale Datenbank. Wie ein Kassenbuch, das jeder lesen kann, aber niemand ändern kann.',
    example: 'Bitcoin ist die bekannteste Blockchain. Jede Transaktion wird dort für immer gespeichert.',
    relatedTerms: ['transaction', 'address', 'block']
  },
  {
    id: 'address',
    term: 'Address (Adresse)',
    category: 'basic',
    definition: 'Wie eine IBAN, aber für Kryptowährungen. Eine eindeutige ID zum Empfangen von Geld.',
    example: '0x1234...abcd oder bc1q... sind typische Adressen',
    relatedTerms: ['wallet', 'transaction']
  },
  {
    id: 'transaction',
    term: 'Transaction (Transaktion)',
    category: 'basic',
    definition: 'Eine Überweisung von Adresse A zu Adresse B. Alle Transaktionen sind öffentlich sichtbar.',
    example: 'Alice sendet 0.5 BTC an Bob - diese Transaktion sieht jeder auf der Blockchain',
    relatedTerms: ['address', 'gas']
  },
  {
    id: 'wallet',
    term: 'Wallet',
    category: 'basic',
    definition: 'Wie ein Online-Banking-Login. Enthält deine Private Keys (Passwörter) für deine Adressen.',
    example: 'MetaMask, Ledger, oder Trust Wallet sind beliebte Wallets',
    relatedTerms: ['private-key', 'address']
  },
  {
    id: 'gas',
    term: 'Gas Fee (Gebühr)',
    category: 'basic',
    definition: 'Gebühr für Transaktionen. Wie Porto beim Brief, aber variabel je nach Netzwerk-Auslastung.',
    example: 'Eine Ethereum-Transaktion kostet zwischen $1-$50 Gas Fee',
    relatedTerms: ['transaction']
  },
  
  // FORENSICS TERMS
  {
    id: 'tracing',
    term: 'Transaction Tracing',
    category: 'forensics',
    definition: 'Verfolgen von Geldflüssen über mehrere Transaktionen hinweg. Wie Detektivarbeit für Krypto.',
    example: 'Von Hacker-Wallet zu Exchange zu Auszahlung - wir folgen dem Geld',
    relatedTerms: ['taint-analysis', 'hop']
  },
  {
    id: 'taint-analysis',
    term: 'Taint Analysis',
    category: 'forensics',
    definition: 'Berechnung, wieviel "schmutziges" Geld in einer Adresse ist. Wichtig für Geldwäsche-Ermittlungen.',
    example: '45% der Coins stammen aus einem Hack - Taint Score = 45%',
    relatedTerms: ['tracing', 'mixer']
  },
  {
    id: 'mixer',
    term: 'Mixer (Tumbler)',
    category: 'forensics',
    definition: 'Service zum Verschleiern von Transaktionen. Wie Geldwäsche, aber auf der Blockchain.',
    example: 'Tornado Cash ist der bekannteste Mixer - von USA sanctions',
    relatedTerms: ['tornado-cash', 'privacy']
  },
  {
    id: 'hop',
    term: 'Hop (Sprung)',
    category: 'forensics',
    definition: 'Eine Transaction im Trace. "3-Hop" bedeutet 3 Transaktionen zurückverfolgen.',
    example: 'Hacker-Wallet → Exchange → Cash-Out = 2 Hops',
    relatedTerms: ['tracing']
  },
  
  // ADVANCED TERMS
  {
    id: 'smart-contract',
    term: 'Smart Contract',
    category: 'advanced',
    definition: 'Selbstausführender Code auf der Blockchain. Wie ein Vertrag, der sich automatisch erfüllt.',
    example: 'Uniswap ist ein Smart Contract für dezentralen Token-Tausch',
    relatedTerms: ['defi', 'dapp']
  },
  {
    id: 'defi',
    term: 'DeFi (Decentralized Finance)',
    category: 'advanced',
    definition: 'Finanzdienstleistungen ohne Bank. Kredite, Börsen, alles auf der Blockchain.',
    example: 'Aave (Kredite), Uniswap (Börse), Curve (Stablecoins)',
    relatedTerms: ['smart-contract']
  },
  {
    id: 'bridge',
    term: 'Bridge (Brücke)',
    category: 'advanced',
    definition: 'Verbindung zwischen zwei Blockchains. Wie eine Wechselstube zwischen Währungen.',
    example: 'Polygon Bridge: Ethereum → Polygon in ~7 Minuten',
    relatedTerms: ['cross-chain']
  },
  
  // TECHNICAL TERMS
  {
    id: 'utxo',
    term: 'UTXO',
    category: 'technical',
    definition: 'Unspent Transaction Output - Bitcoin\'s Art, Guthaben zu speichern (wie Münzen in der Tasche).',
    example: 'Du hast 3 UTXOs: 0.5 BTC, 0.3 BTC, 0.2 BTC = 1 BTC total',
    relatedTerms: ['transaction']
  },
  {
    id: 'private-key',
    term: 'Private Key',
    category: 'technical',
    definition: 'Dein geheimer Schlüssel (Passwort). Wer den Private Key hat, besitzt die Coins.',
    example: 'Niemals teilen! Verlust = Coins für immer weg',
    relatedTerms: ['wallet']
  },
  {
    id: 'hash',
    term: 'Hash',
    category: 'technical',
    definition: 'Eindeutige Fingerabdruck einer Transaktion. Wie eine Tracking-Nummer.',
    example: '0xabc123... ist der Hash einer Ethereum-Transaktion',
    relatedTerms: ['transaction']
  },
];

const BlockchainGlossary: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  // Filter terms
  const filteredTerms = glossaryTerms.filter(term => {
    const matchesSearch = term.term.toLowerCase().includes(search.toLowerCase()) ||
                         term.definition.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || term.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });
  
  const categoryColors = {
    basic: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700',
    forensics: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700',
    advanced: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-300 dark:border-orange-700',
    technical: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700',
  };
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50"
            onClick={onClose}
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-primary-600 to-purple-600 p-6 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Book className="w-8 h-8" />
                    <div>
                      <h2 className="text-2xl font-bold">{t('glossary.title', 'Blockchain Glossar')}</h2>
                      <p className="text-sm text-white/80">{t('glossary.subtitle', 'Alle Begriffe einfach erklärt')}</p>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                    aria-label={t('common.close', 'Close')}
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
                
                {/* Search */}
                <div className="mt-4 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/60" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder={t('glossary.search', 'Begriff suchen...')}
                    className="w-full pl-10 pr-4 py-2 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50"
                  />
                </div>
                
                {/* Category Filter */}
                <div className="mt-3 flex flex-wrap gap-2">
                  {['all', 'basic', 'forensics', 'advanced', 'technical'].map(cat => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`px-3 py-1 rounded-full text-sm transition-colors ${
                        selectedCategory === cat
                          ? 'bg-white text-primary-600'
                          : 'bg-white/20 text-white hover:bg-white/30'
                      }`}
                    >
                      {t(`glossary.category.${cat}`, cat === 'all' ? 'Alle' : cat.charAt(0).toUpperCase() + cat.slice(1))}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="space-y-4">
                  {filteredTerms.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>{t('glossary.noResults', 'Keine Begriffe gefunden')}</p>
                    </div>
                  ) : (
                    filteredTerms.map((term) => (
                      <motion.div
                        key={term.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white">{term.term}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs border ${categoryColors[term.category]}`}>
                            {t(`glossary.category.${term.category}`, term.category)}
                          </span>
                        </div>
                        <p className="text-sm text-slate-700 dark:text-slate-300 mb-2">
                          {term.definition}
                        </p>
                        {term.example && (
                          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded p-2 text-xs text-slate-600 dark:text-slate-400">
                            <strong>Beispiel:</strong> {term.example}
                          </div>
                        )}
                      </motion.div>
                    ))
                  )}
                </div>
              </div>
              
              {/* Footer */}
              <div className="border-t border-slate-200 dark:border-slate-800 p-4 text-center text-sm text-slate-500">
                {filteredTerms.length} {t('glossary.terms', 'Begriffe')} • {t('glossary.beginner', 'Für Anfänger optimiert')}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default BlockchainGlossary;
