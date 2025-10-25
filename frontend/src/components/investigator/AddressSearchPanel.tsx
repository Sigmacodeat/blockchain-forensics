import React from 'react';
import { useTranslation } from 'react-i18next';
import { Search, MapPin } from 'lucide-react';

interface AddressSearchPanelProps {
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
  onSearch: () => void;
}

export const AddressSearchPanel: React.FC<AddressSearchPanelProps> = ({
  searchQuery,
  onSearchQueryChange,
  onSearch,
}) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 transition-all hover:shadow-xl">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
        <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
          <Search className="h-4 w-4 text-primary-600 dark:text-primary-400" />
        </div>
        {t('investigator.search.title', 'Address Search')}
      </h3>
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500" />
          <input
            type="text"
            placeholder={t('investigator.search.placeholder', 'Enter address (0x... or bc1...)')}
            className="w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all text-sm"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && onSearch()}
          />
        </div>
        <button
          onClick={onSearch}
          className="w-full bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 dark:from-primary-500 dark:to-primary-600 text-white py-3 px-4 rounded-lg font-medium shadow-lg shadow-primary-500/30 transition-all hover:shadow-xl hover:shadow-primary-500/40 hover:-translate-y-0.5"
        >
          <span className="flex items-center justify-center gap-2">
            <MapPin className="h-4 w-4" />
            {t('investigator.search.explore', 'Explore Address')}
          </span>
        </button>
      </div>
    </div>
  );
};
