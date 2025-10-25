import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Save, RefreshCw, Eye, EyeOff, Settings, 
  BarChart3, TestTube, Download, Upload, 
  CheckCircle2, XCircle, AlertTriangle
} from 'lucide-react'
import { toast } from 'react-hot-toast'

interface ChatbotConfig {
  // Core Features
  enabled: boolean
  showRobotIcon: boolean
  showUnreadBadge: boolean
  showQuickReplies: boolean
  showProactiveMessages: boolean
  showVoiceInput: boolean
  
  // Advanced Features
  enableCryptoPayments: boolean
  enableIntentDetection: boolean
  enableSentimentAnalysis: boolean
  enableOfflineMode: boolean
  enableDragDrop: boolean
  enableKeyboardShortcuts: boolean
  
  // UI/UX
  enableDarkMode: boolean
  enableMinimize: boolean
  enableExport: boolean
  enableShare: boolean
  showWelcomeTeaser: boolean
  
  // Timing
  proactiveMessageDelay: number // seconds
  welcomeTeaserDelay: number // seconds
  autoScrollEnabled: boolean
  
  // Limits
  maxMessages: number
  maxFileSize: number // MB
  rateLimitPerMinute: number
  
  // Appearance
  primaryColor: string
  position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  buttonSize: 'small' | 'medium' | 'large'
}

const DEFAULT_CONFIG: ChatbotConfig = {
  enabled: true,
  showRobotIcon: true,
  showUnreadBadge: true,
  showQuickReplies: true,
  showProactiveMessages: true,
  showVoiceInput: true,
  enableCryptoPayments: true,
  enableIntentDetection: true,
  enableSentimentAnalysis: true,
  enableOfflineMode: true,
  enableDragDrop: true,
  enableKeyboardShortcuts: true,
  enableDarkMode: true,
  enableMinimize: true,
  enableExport: true,
  enableShare: true,
  showWelcomeTeaser: true,
  proactiveMessageDelay: 5,
  welcomeTeaserDelay: 10,
  autoScrollEnabled: true,
  maxMessages: 50,
  maxFileSize: 10,
  rateLimitPerMinute: 20,
  primaryColor: '#6366f1',
  position: 'bottom-right',
  buttonSize: 'medium'
}

export default function ChatbotSettings() {
  const [config, setConfig] = useState<ChatbotConfig>(DEFAULT_CONFIG)
  const [originalConfig, setOriginalConfig] = useState<ChatbotConfig>(DEFAULT_CONFIG)
  const [saving, setSaving] = useState(false)
  const [previewMode, setPreviewMode] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  // Load config from backend/localStorage
  useEffect(() => {
    loadConfig()
  }, [])

  // Detect changes
  useEffect(() => {
    setHasChanges(JSON.stringify(config) !== JSON.stringify(originalConfig))
  }, [config, originalConfig])

  const loadConfig = async () => {
    try {
      // Try backend first
      const response = await fetch('/api/v1/admin/chatbot-config')
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
        setOriginalConfig(data)
      } else {
        // Fallback to localStorage
        const stored = localStorage.getItem('chatbot_config')
        if (stored) {
          const parsed = JSON.parse(stored)
          setConfig(parsed)
          setOriginalConfig(parsed)
        }
      }
    } catch (error) {
      console.error('Failed to load config:', error)
      toast.error('Fehler beim Laden der Konfiguration')
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      // Save to backend
      const response = await fetch('/api/v1/admin/chatbot-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })

      if (response.ok) {
        // Also save to localStorage as backup
        localStorage.setItem('chatbot_config', JSON.stringify(config))
        setOriginalConfig(config)
        toast.success('✅ Konfiguration gespeichert!')
        
        // Broadcast change to all open tabs
        window.dispatchEvent(new CustomEvent('chatbot-config-updated', { detail: config }))
      } else {
        throw new Error('Save failed')
      }
    } catch (error) {
      console.error('Failed to save config:', error)
      toast.error('Fehler beim Speichern')
    } finally {
      setSaving(false)
    }
  }

  const resetToDefault = () => {
    if (window.confirm('Alle Einstellungen auf Standard zurücksetzen?')) {
      setConfig(DEFAULT_CONFIG)
      toast.success('Auf Standard zurückgesetzt')
    }
  }

  const exportConfig = () => {
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chatbot-config-${Date.now()}.json`
    a.click()
    toast.success('Konfiguration exportiert!')
  }

  const importConfig = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const imported = JSON.parse(event.target?.result as string)
        setConfig(imported)
        toast.success('Konfiguration importiert!')
      } catch (error) {
        toast.error('Ungültige Konfigurationsdatei')
      }
    }
    reader.readAsText(file)
  }

  const updateConfig = (key: keyof ChatbotConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                <Settings className="w-8 h-8 text-primary-600" />
                Chatbot-Einstellungen
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                Konfiguriere alle Features und Optionen für den Chatbot
              </p>
            </div>

            {/* Status */}
            <div className="flex items-center gap-3">
              {config.enabled ? (
                <div className="flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg">
                  <CheckCircle2 className="w-4 h-4" />
                  <span className="text-sm font-medium">Aktiv</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 px-3 py-2 bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg">
                  <XCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Deaktiviert</span>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={saveConfig}
              disabled={!hasChanges || saving}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Speichere...' : 'Speichern'}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={resetToDefault}
              className="flex items-center gap-2 px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Zurücksetzen
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setPreviewMode(!previewMode)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg transition-colors"
            >
              {previewMode ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {previewMode ? 'Preview Aus' : 'Preview'}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={exportConfig}
              className="flex items-center gap-2 px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Export
            </motion.button>

            <label className="flex items-center gap-2 px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg cursor-pointer transition-colors">
              <Upload className="w-4 h-4" />
              Import
              <input type="file" accept=".json" onChange={importConfig} className="hidden" />
            </label>
          </div>

          {/* Changes Warning */}
          {hasChanges && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 bg-yellow-100 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700 rounded-lg flex items-start gap-3"
            >
              <AlertTriangle className="w-5 h-5 text-yellow-700 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                  Ungespeicherte Änderungen
                </p>
                <p className="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
                  Vergiss nicht zu speichern, bevor du die Seite verlässt!
                </p>
              </div>
            </motion.div>
          )}
        </div>

        {/* Settings Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Core Features */}
          <SettingsSection title="Kern-Features">
            <ToggleOption
              label="Chatbot aktiviert"
              description="Master-Switch für den gesamten Chatbot"
              checked={config.enabled}
              onChange={(checked: any) => updateConfig('enabled', checked)}
            />
            <ToggleOption
              label="3D-Roboter-Icon"
              description="Animierter Roboter statt Sprechblase"
              checked={config.showRobotIcon}
              onChange={(checked: any) => updateConfig('showRobotIcon', checked)}
            />
            <ToggleOption
              label="Unread-Badge"
              description="Roter Zähler für neue Nachrichten"
              checked={config.showUnreadBadge}
              onChange={(checked: any) => updateConfig('showUnreadBadge', checked)}
            />
            <ToggleOption
              label="Quick-Replies"
              description="4 Beispiel-Fragen anzeigen"
              checked={config.showQuickReplies}
              onChange={(checked: any) => updateConfig('showQuickReplies', checked)}
            />
            <ToggleOption
              label="Proaktive Nachrichten"
              description="AI meldet sich automatisch"
              checked={config.showProactiveMessages}
              onChange={(checked: any) => updateConfig('showProactiveMessages', checked)}
            />
            <ToggleOption
              label="Voice-Input"
              description="Speech-to-Text Button"
              checked={config.showVoiceInput}
              onChange={(checked: any) => updateConfig('showVoiceInput', checked)}
            />
          </SettingsSection>

          {/* Advanced Features */}
          <SettingsSection title="Erweiterte Features">
            <ToggleOption
              label="Crypto-Payments"
              description="30+ Kryptowährungen im Chat"
              checked={config.enableCryptoPayments}
              onChange={(checked: any) => updateConfig('enableCryptoPayments', checked)}
            />
            <ToggleOption
              label="Intent-Detection"
              description="Auto-Navigation zu Tools"
              checked={config.enableIntentDetection}
              onChange={(checked: any) => updateConfig('enableIntentDetection', checked)}
            />
            <ToggleOption
              label="Sentiment-Analyse"
              description="Erkennt User-Stimmung"
              checked={config.enableSentimentAnalysis}
              onChange={(checked: any) => updateConfig('enableSentimentAnalysis', checked)}
            />
            <ToggleOption
              label="Offline-Modus"
              description="Funktioniert ohne Internet"
              checked={config.enableOfflineMode}
              onChange={(checked: any) => updateConfig('enableOfflineMode', checked)}
            />
            <ToggleOption
              label="Drag & Drop"
              description="Files per Drag & Drop"
              checked={config.enableDragDrop}
              onChange={(checked: any) => updateConfig('enableDragDrop', checked)}
            />
            <ToggleOption
              label="Keyboard-Shortcuts"
              description="ESC, Ctrl+K, etc."
              checked={config.enableKeyboardShortcuts}
              onChange={(checked: any) => updateConfig('enableKeyboardShortcuts', checked)}
            />
          </SettingsSection>

          {/* UI/UX Options */}
          <SettingsSection title="UI/UX Optionen">
            <ToggleOption
              label="Dark-Mode-Toggle"
              description="User kann Theme wechseln"
              checked={config.enableDarkMode}
              onChange={(checked: any) => updateConfig('enableDarkMode', checked)}
            />
            <ToggleOption
              label="Minimize-Button"
              description="Chat klein halten"
              checked={config.enableMinimize}
              onChange={(checked: any) => updateConfig('enableMinimize', checked)}
            />
            <ToggleOption
              label="Export-Funktion"
              description="Chat als PDF speichern"
              checked={config.enableExport}
              onChange={(checked: any) => updateConfig('enableExport', checked)}
            />
            <ToggleOption
              label="Share-Funktion"
              description="Chat-Link teilen"
              checked={config.enableShare}
              onChange={(checked: any) => updateConfig('enableShare', checked)}
            />
            <ToggleOption
              label="Welcome-Teaser"
              description="Zeigt sich nach 10s"
              checked={config.showWelcomeTeaser}
              onChange={(checked: any) => updateConfig('showWelcomeTeaser', checked)}
            />
            <ToggleOption
              label="Auto-Scroll"
              description="Scrollt zu neuester Message"
              checked={config.autoScrollEnabled}
              onChange={(checked: any) => updateConfig('autoScrollEnabled', checked)}
            />
          </SettingsSection>

          {/* Timing & Limits */}
          <SettingsSection title="Timing & Limits">
            <NumberOption
              label="Proactive Message Delay"
              description="Sekunden bis erste Nachricht"
              value={config.proactiveMessageDelay}
              onChange={(value: any) => updateConfig('proactiveMessageDelay', value)}
              min={3}
              max={30}
              unit="s"
            />
            <NumberOption
              label="Welcome Teaser Delay"
              description="Sekunden bis Teaser erscheint"
              value={config.welcomeTeaserDelay}
              onChange={(value: any) => updateConfig('welcomeTeaserDelay', value)}
              min={5}
              max={60}
              unit="s"
            />
            <NumberOption
              label="Max Messages (History)"
              description="Maximale Anzahl gespeicherter Messages"
              value={config.maxMessages}
              onChange={(value: any) => updateConfig('maxMessages', value)}
              min={10}
              max={100}
            />
            <NumberOption
              label="Max File Size"
              description="Maximale Dateigröße für Uploads"
              value={config.maxFileSize}
              onChange={(value: any) => updateConfig('maxFileSize', value)}
              min={1}
              max={50}
              unit="MB"
            />
            <NumberOption
              label="Rate Limit"
              description="Max Nachrichten pro Minute"
              value={config.rateLimitPerMinute}
              onChange={(value: any) => updateConfig('rateLimitPerMinute', value)}
              min={5}
              max={60}
              unit="/min"
            />
          </SettingsSection>

          {/* Appearance */}
          <SettingsSection title="Aussehen">
            <ColorOption
              label="Primary Color"
              description="Haupt-Akzentfarbe"
              value={config.primaryColor}
              onChange={(value: any) => updateConfig('primaryColor', value)}
            />
            <SelectOption
              label="Position"
              description="Wo soll der Chat-Button sein?"
              value={config.position}
              onChange={(value: any) => updateConfig('position', value)}
              options={[
                { value: 'bottom-right', label: 'Unten Rechts' },
                { value: 'bottom-left', label: 'Unten Links' },
                { value: 'top-right', label: 'Oben Rechts' },
                { value: 'top-left', label: 'Oben Links' }
              ]}
            />
            <SelectOption
              label="Button-Größe"
              description="Größe des Chat-Buttons"
              value={config.buttonSize}
              onChange={(value: any) => updateConfig('buttonSize', value)}
              options={[
                { value: 'small', label: 'Klein (40px)' },
                { value: 'medium', label: 'Mittel (48px)' },
                { value: 'large', label: 'Groß (56px)' }
              ]}
            />
          </SettingsSection>

          {/* Analytics */}
          <SettingsSection title="Analytics & Testing">
            <div className="space-y-3">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => window.open('/admin/chatbot-analytics', '_blank')}
                className="w-full flex items-center justify-between p-4 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <div className="flex items-center gap-3">
                  <BarChart3 className="w-5 h-5 text-primary-600" />
                  <div className="text-left">
                    <p className="font-medium text-sm">Analytics Dashboard</p>
                    <p className="text-xs text-muted-foreground">Metriken & Insights</p>
                  </div>
                </div>
                <span className="text-xs text-primary-600">Öffnen →</span>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => window.open('/admin/chatbot-testing', '_blank')}
                className="w-full flex items-center justify-between p-4 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <div className="flex items-center gap-3">
                  <TestTube className="w-5 h-5 text-purple-600" />
                  <div className="text-left">
                    <p className="font-medium text-sm">A/B-Testing</p>
                    <p className="text-xs text-muted-foreground">Teste Varianten</p>
                  </div>
                </div>
                <span className="text-xs text-purple-600">Öffnen →</span>
              </motion.button>
            </div>
          </SettingsSection>
        </div>

        {/* Live Preview */}
        {previewMode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 p-6 bg-white dark:bg-slate-800 rounded-lg border-2 border-primary-500 shadow-xl"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Live Preview
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              So sieht der Chatbot mit den aktuellen Einstellungen aus (speichere, um Änderungen zu übernehmen):
            </p>
            <div className="relative bg-slate-100 dark:bg-slate-900 rounded-lg h-96 flex items-center justify-center">
              <p className="text-slate-500">Preview wird geladen...</p>
              {/* Hier würde der tatsächliche Chat-Widget als Preview erscheinen */}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

// Helper Components
function SettingsSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
      <h2 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">{title}</h2>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  )
}

function ToggleOption({ label, description, checked, onChange }: any) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <p className="font-medium text-sm text-slate-900 dark:text-white">{label}</p>
        <p className="text-xs text-slate-600 dark:text-slate-400">{description}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-primary-600' : 'bg-slate-300 dark:bg-slate-600'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  )
}

function NumberOption({ label, description, value, onChange, min, max, unit }: any) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex-1">
          <p className="font-medium text-sm text-slate-900 dark:text-white">{label}</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">{description}</p>
        </div>
        <span className="text-sm font-mono text-primary-600">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
      />
    </div>
  )
}

function ColorOption({ label, description, value, onChange }: any) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <p className="font-medium text-sm text-slate-900 dark:text-white">{label}</p>
        <p className="text-xs text-slate-600 dark:text-slate-400">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-12 h-8 rounded border-2 border-slate-300 dark:border-slate-600 cursor-pointer"
        />
        <span className="text-xs font-mono text-slate-600 dark:text-slate-400">{value}</span>
      </div>
    </div>
  )
}

function SelectOption({ label, description, value, onChange, options }: any) {
  return (
    <div>
      <p className="font-medium text-sm text-slate-900 dark:text-white mb-1">{label}</p>
      <p className="text-xs text-slate-600 dark:text-slate-400 mb-2">{description}</p>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 bg-slate-100 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        {options.map((opt: any) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}
