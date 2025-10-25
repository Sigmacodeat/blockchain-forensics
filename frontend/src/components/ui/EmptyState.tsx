import React from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  FileText,
  Database,
  AlertCircle,
  FolderOpen,
  Users,
  Inbox,
  TrendingUp,
  FileSearch,
  Clock,
  LucideIcon,
} from 'lucide-react';

/**
 * Empty State Component
 * Beautiful placeholders for empty data states
 */

interface EmptyStateProps {
  variant?:
    | 'no-results'
    | 'no-data'
    | 'no-cases'
    | 'no-traces'
    | 'no-notifications'
    | 'no-reports'
    | 'error'
    | 'custom';
  icon?: LucideIcon;
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  illustration?: 'simple' | 'detailed';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const variantConfig = {
  'no-results': {
    icon: Search,
    title: 'Keine Ergebnisse gefunden',
    description: 'Versuchen Sie es mit anderen Suchbegriffen oder Filtern.',
    illustration: 'simple',
  },
  'no-data': {
    icon: Database,
    title: 'Keine Daten verfügbar',
    description: 'Es sind noch keine Daten vorhanden. Starten Sie Ihre erste Analyse.',
    illustration: 'simple',
  },
  'no-cases': {
    icon: FolderOpen,
    title: 'Keine Cases vorhanden',
    description: 'Erstellen Sie Ihren ersten Case um mit der Ermittlung zu beginnen.',
    illustration: 'detailed',
  },
  'no-traces': {
    icon: TrendingUp,
    title: 'Keine Traces gefunden',
    description: 'Starten Sie einen Trace um Transaktionen zu analysieren.',
    illustration: 'detailed',
  },
  'no-notifications': {
    icon: Inbox,
    title: 'Keine Benachrichtigungen',
    description: 'Sie sind auf dem neuesten Stand! Keine neuen Benachrichtigungen.',
    illustration: 'simple',
  },
  'no-reports': {
    icon: FileText,
    title: 'Keine Reports',
    description: 'Generieren Sie Ihren ersten Report aus einem Case oder Trace.',
    illustration: 'simple',
  },
  error: {
    icon: AlertCircle,
    title: 'Ein Fehler ist aufgetreten',
    description: 'Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.',
    illustration: 'simple',
  },
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  variant = 'no-data',
  icon: CustomIcon,
  title: customTitle,
  description: customDescription,
  action,
  secondaryAction,
  illustration = 'simple',
  size = 'md',
  className = '',
}) => {
  const config = variantConfig[variant as keyof typeof variantConfig] || variantConfig['no-data'];
  const Icon = CustomIcon || config.icon;
  const title = customTitle || config.title;
  const description = customDescription || config.description;

  const sizeClasses = {
    sm: {
      icon: 'w-12 h-12',
      title: 'text-lg',
      description: 'text-sm',
      padding: 'p-6',
    },
    md: {
      icon: 'w-16 h-16',
      title: 'text-xl',
      description: 'text-base',
      padding: 'p-8',
    },
    lg: {
      icon: 'w-20 h-20',
      title: 'text-2xl',
      description: 'text-lg',
      padding: 'p-12',
    },
  };

  const currentSize = sizeClasses[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`flex flex-col items-center justify-center ${currentSize.padding} ${className}`}
    >
      {/* Icon with gradient background */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        className={`
          relative mb-6
          ${illustration === 'detailed' ? 'bg-gradient-to-br from-primary-100 to-primary-50 dark:from-primary-900/20 dark:to-primary-800/10' : ''}
          ${illustration === 'detailed' ? 'p-6 rounded-2xl' : ''}
        `}
      >
        <Icon
          className={`
            ${currentSize.icon}
            text-slate-400 dark:text-slate-600
            ${illustration === 'detailed' ? 'text-primary-600 dark:text-primary-400' : ''}
          `}
        />
        
        {/* Decorative circles for detailed illustration */}
        {illustration === 'detailed' && (
          <>
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.5, 0.3],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="absolute -top-2 -right-2 w-4 h-4 bg-primary-400 rounded-full"
            />
            <motion.div
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.2, 0.4, 0.2],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 0.5,
              }}
              className="absolute -bottom-1 -left-1 w-3 h-3 bg-primary-300 rounded-full"
            />
          </>
        )}
      </motion.div>

      {/* Title */}
      <motion.h3
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className={`${currentSize.title} font-semibold text-slate-900 dark:text-white mb-2 text-center`}
      >
        {title}
      </motion.h3>

      {/* Description */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className={`${currentSize.description} text-slate-600 dark:text-slate-400 text-center max-w-md mb-6`}
      >
        {description}
      </motion.p>

      {/* Actions */}
      {(action || secondaryAction) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col sm:flex-row gap-3"
        >
          {action && (
            <button
              onClick={action.onClick}
              className={`
                px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl
                ${
                  action.variant === 'secondary'
                    ? 'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                    : 'bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-700 hover:to-primary-600 text-white'
                }
              `}
            >
              {action.label}
            </button>
          )}
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="px-6 py-3 bg-transparent border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg font-medium transition-all duration-200"
            >
              {secondaryAction.label}
            </button>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};

/**
 * Empty State variants for common use cases
 */

export const EmptySearchResults: React.FC<{ onClearFilters?: () => void }> = ({ onClearFilters }) => (
  <EmptyState
    variant="no-results"
    action={
      onClearFilters
        ? {
            label: 'Filter zurücksetzen',
            onClick: onClearFilters,
            variant: 'secondary',
          }
        : undefined
    }
  />
);

export const EmptyCases: React.FC<{ onCreateCase: () => void }> = ({ onCreateCase }) => (
  <EmptyState
    variant="no-cases"
    action={{
      label: '➕ Neuen Case erstellen',
      onClick: onCreateCase,
    }}
    illustration="detailed"
  />
);

export const EmptyTraces: React.FC<{ onStartTrace: () => void }> = ({ onStartTrace }) => (
  <EmptyState
    variant="no-traces"
    action={{
      label: '🔍 Trace starten',
      onClick: onStartTrace,
    }}
    illustration="detailed"
  />
);

export const EmptyNotifications: React.FC = () => (
  <EmptyState variant="no-notifications" size="sm" />
);

export const EmptyReports: React.FC<{ onGenerateReport?: () => void }> = ({ onGenerateReport }) => (
  <EmptyState
    variant="no-reports"
    action={
      onGenerateReport
        ? {
            label: '📄 Report generieren',
            onClick: onGenerateReport,
          }
        : undefined
    }
  />
);

/**
 * First Time User Empty State - Special onboarding variant
 */
export const FirstTimeEmptyState: React.FC<{
  feature: string;
  onGetStarted: () => void;
  onWatchDemo?: () => void;
}> = ({ feature, onGetStarted, onWatchDemo }) => (
  <EmptyState
    icon={FileSearch}
    title={`Willkommen bei ${feature}!`}
    description={`Starten Sie Ihre erste ${feature}-Analyse und entdecken Sie die leistungsstarken Features.`}
    action={{
      label: 'Jetzt starten',
      onClick: onGetStarted,
    }}
    secondaryAction={
      onWatchDemo
        ? {
            label: 'Demo ansehen',
            onClick: onWatchDemo,
          }
        : undefined
    }
    illustration="detailed"
    size="lg"
  />
);

export default EmptyState;
