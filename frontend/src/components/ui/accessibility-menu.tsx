import React, { useState } from 'react'
import { Settings, Type, Contrast, Keyboard, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '@/hooks/useAccessibility'
import { LanguageSelector } from '@/contexts/I18nContext'

interface AccessibilityMenuProps {
  className?: string
}

export const AccessibilityMenu: React.FC<AccessibilityMenuProps> = ({ className }) => {
  const { t, i18n } = useTranslation()
  const { fontSize, changeFontSize, highContrast, reducedMotion } = useAccessibility()
  const [isOpen, setIsOpen] = useState(false)

  // i18n: nur übersetzen, wenn der Namespace geladen ist – sonst Fallback nutzen
  const nsReady = (typeof i18n.hasLoadedNamespace === 'function' && i18n.hasLoadedNamespace('translation'))
    || (typeof i18n.hasResourceBundle === 'function' && i18n.hasResourceBundle(i18n.language, 'translation'))
  const tr = (key: string, fallback: string) => (nsReady ? t(key) : fallback)

  const toggleMenu = () => {
    setIsOpen(!isOpen)
  }

  return (
    <div className={`fixed right-4 bottom-4 z-50 ${className}`}>
      {/* Floating Button */}
      <button
        onClick={toggleMenu}
        className="flex items-center justify-center w-12 h-12 bg-primary-600 text-white rounded-full shadow-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-all"
        aria-label={tr('accessibility.settings', 'Accessibility settings')}
        aria-expanded={isOpen}
      >
        <Settings className="h-6 w-6" aria-hidden="true" />
      </button>

      {/* Menu Panel */}
      {isOpen && (
        <div
          className="absolute bottom-16 right-0 w-80 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden"
          role="dialog"
          aria-label={tr('accessibility.settings', 'Accessibility settings')}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Settings className="h-5 w-5" aria-hidden="true" />
              {tr('accessibility.settings', 'Accessibility settings')}
            </h3>
            <button
              onClick={toggleMenu}
              className="text-gray-500 hover:text-gray-700 p-1 rounded focus:ring-2 focus:ring-primary-500"
              aria-label={tr('common.close', 'Close')}
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
            {/* Font Size */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Type className="h-4 w-4" aria-hidden="true" />
                {tr('accessibility.font_size', 'Font Size')}
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => changeFontSize('normal')}
                  className={`flex-1 px-3 py-2 text-sm rounded-md border transition-colors ${
                    fontSize === 'normal'
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  aria-pressed={fontSize === 'normal'}
                >
                  {tr('accessibility.font_size_normal', 'Normal font size')}
                </button>
                <button
                  onClick={() => changeFontSize('large')}
                  className={`flex-1 px-3 py-2 text-sm rounded-md border transition-colors ${
                    fontSize === 'large'
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  aria-pressed={fontSize === 'large'}
                >
                  {tr('accessibility.font_size_large', 'Large font size')}
                </button>
                <button
                  onClick={() => changeFontSize('xlarge')}
                  className={`flex-1 px-3 py-2 text-sm rounded-md border transition-colors ${
                    fontSize === 'xlarge'
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                  aria-pressed={fontSize === 'xlarge'}
                >
                  {tr('accessibility.font_size_xlarge', 'Extra large font size')}
                </button>
              </div>
            </div>

            {/* Language Selection */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                {tr('common.language', 'Language')}
              </label>
              <LanguageSelector variant="dropdown" showFlags={true} />
            </div>

            {/* System Preferences Info */}
            <div className="pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                {tr('accessibility.system_preferences', 'System Preferences')}
              </h4>
              <div className="space-y-2 text-xs text-gray-600">
                {highContrast && (
                  <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                    <Contrast className="h-4 w-4" aria-hidden="true" />
                    <span>{tr('accessibility.high_contrast_detected', 'High contrast detected')}</span>
                  </div>
                )}
                {reducedMotion && (
                  <div className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                    <span>{tr('accessibility.reduced_motion_detected', 'Reduced motion detected')}</span>
                  </div>
                )}
                {!highContrast && !reducedMotion && (
                  <div className="text-gray-500 italic">
                    {tr('accessibility.no_system_preferences', 'No special system preferences detected')}
                  </div>
                )}
              </div>
            </div>

            {/* Keyboard Shortcuts Info */}
            <div className="pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Keyboard className="h-4 w-4" aria-hidden="true" />
                {tr('accessibility.keyboard_shortcuts', 'Keyboard shortcuts')}
              </h4>
              <div className="space-y-1 text-xs text-gray-600">
                <div className="flex justify-between">
                  <span>Tab</span>
                  <span>{tr('accessibility.navigate_forward', 'Navigate forward')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Shift + Tab</span>
                  <span>{tr('accessibility.navigate_backward', 'Navigate backward')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Enter</span>
                  <span>{tr('accessibility.activate', 'Activate')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Esc</span>
                  <span>{tr('accessibility.close_dialog', 'Close dialog')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AccessibilityMenu
