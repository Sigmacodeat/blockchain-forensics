import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HelpCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Blockchain Tooltip Component
 * Shows explanations for blockchain terms on hover/click
 */

interface BlockchainTooltipProps {
  term: string;
  children: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  triggerMode?: 'hover' | 'click';
}

const glossaryTerms: Record<string, { definition: string; example?: string }> = {
  blockchain: {
    definition: 'Eine unveränderliche, dezentrale Datenbank. Wie ein Kassenbuch, das jeder lesen kann, aber niemand ändern kann.',
    example: 'Bitcoin ist die bekannteste Blockchain.',
  },
  transaction: {
    definition: 'Eine Überweisung von Adresse A zu Adresse B. Alle Transaktionen sind öffentlich sichtbar.',
    example: 'Alice sendet 0.5 BTC an Bob',
  },
  address: {
    definition: 'Wie eine IBAN, aber für Kryptowährungen. Eine eindeutige ID zum Empfangen von Geld.',
    example: '0x1234...abcd oder bc1q...',
  },
  wallet: {
    definition: 'Wie ein Online-Banking-Login. Enthält deine Private Keys für deine Adressen.',
    example: 'MetaMask, Ledger, Trust Wallet',
  },
  gas: {
    definition: 'Gebühr für Transaktionen. Variabel je nach Netzwerk-Auslastung.',
    example: 'Ethereum: $1-$50 pro Transaktion',
  },
  mixer: {
    definition: 'Service zum Verschleiern von Transaktionen. Wie Geldwäsche auf der Blockchain.',
    example: 'Tornado Cash (von USA sanctions)',
  },
  'smart-contract': {
    definition: 'Selbstausführender Code auf der Blockchain. Wie ein Vertrag, der sich automatisch erfüllt.',
    example: 'Uniswap (dezentrale Börse)',
  },
  defi: {
    definition: 'Decentralized Finance - Finanzdienstleistungen ohne Bank.',
    example: 'Aave (Kredite), Uniswap (Börse)',
  },
  bridge: {
    definition: 'Verbindung zwischen zwei Blockchains. Wie eine Wechselstube.',
    example: 'Polygon Bridge: ETH → Polygon',
  },
  tracing: {
    definition: 'Verfolgen von Geldflüssen über mehrere Transaktionen. Wie Detektivarbeit für Krypto.',
    example: 'Hacker → Exchange → Cash-Out',
  },
  taint: {
    definition: 'Berechnung, wieviel "schmutziges" Geld in einer Adresse ist.',
    example: '45% stammen aus einem Hack',
  },
};

export const BlockchainTooltip: React.FC<BlockchainTooltipProps> = ({
  term,
  children,
  placement = 'top',
  triggerMode = 'hover',
}) => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  
  const termKey = term.toLowerCase().replace(/\s+/g, '-');
  const termData = glossaryTerms[termKey];
  
  if (!termData) {
    // If term not found, just render children without tooltip
    return <>{children}</>;
  }
  
  const placementClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };
  
  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent',
  };
  
  const handleInteraction = () => {
    if (triggerMode === 'click') {
      setIsOpen(!isOpen);
    }
  };
  
  return (
    <span className="relative inline-block group">
      <span
        className="border-b border-dashed border-primary-400 dark:border-primary-500 cursor-help inline-flex items-center gap-1"
        onMouseEnter={() => triggerMode === 'hover' && setIsOpen(true)}
        onMouseLeave={() => triggerMode === 'hover' && setIsOpen(false)}
        onClick={handleInteraction}
        onKeyPress={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleInteraction();
          }
        }}
        tabIndex={0}
        role="button"
        aria-label={t('glossary.showDefinition', `Show definition for ${term}`)}
        aria-expanded={isOpen}
      >
        {children}
        <HelpCircle className="w-3 h-3 text-primary-500 dark:text-primary-400 opacity-70" />
      </span>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className={`absolute z-50 ${placementClasses[placement]} w-64 pointer-events-none`}
          >
            <div className="bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-2xl p-3 border border-slate-700">
              {/* Arrow */}
              <div
                className={`absolute w-0 h-0 border-8 ${arrowClasses[placement]}`}
                style={{
                  borderColor: placement === 'top' ? 'rgb(15 23 42) transparent transparent transparent' :
                               placement === 'bottom' ? 'transparent transparent rgb(15 23 42) transparent' :
                               placement === 'left' ? 'transparent transparent transparent rgb(15 23 42)' :
                               'transparent rgb(15 23 42) transparent transparent'
                }}
              />
              
              {/* Term */}
              <div className="font-bold text-sm mb-1 text-primary-400">
                {term}
              </div>
              
              {/* Definition */}
              <div className="text-xs text-slate-200 mb-2">
                {termData.definition}
              </div>
              
              {/* Example */}
              {termData.example && (
                <div className="text-xs text-slate-400 italic border-t border-slate-700 pt-2">
                  <strong className="text-slate-300">Beispiel:</strong> {termData.example}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
};

export default BlockchainTooltip;
