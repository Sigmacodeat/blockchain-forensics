/*
 * Erweiterte Wallet-Testseite für die Forensik-Anwendung
 *
 * Demonstriert alle neuen Features: Export/Import, Multi-Sig, erweiterte Analyse, NFT-Support und DeFi.
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { NFTPortfolio } from '../components/wallet/NFTPortfolio'
import { CrossChainDashboard } from '../components/wallet/CrossChainDashboard'
import { TourManager } from '../components/ui/tour-manager'
import {
  ResponsiveContainer,
  ResponsiveGrid,
  ResponsiveCard,
  ResponsiveButton,
} from '../components/ui/Responsive'
import { Menu, X, Wallet, TrendingUp, Shield, Download, Upload, Settings } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '../components/ui/button'

const WalletTestPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const { t } = useTranslation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const tabs = [
    { id: 'overview', label: t('wallet.test.tabs.overview', 'Übersicht'), icon: '📊' },
    { id: 'transactions', label: t('wallet.test.tabs.transactions', 'Transaktionen'), icon: '💱' },
    { id: 'analytics', label: t('wallet.test.tabs.analytics', 'Analytics'), icon: '📈' },
    { id: 'export', label: t('wallet.test.tabs.export', 'Export/Import'), icon: '📁' },
    { id: 'multisig', label: t('wallet.test.tabs.multisig', 'Multi-Signature'), icon: '🔐' },
    { id: 'nft', label: t('wallet.test.tabs.nft', 'NFT Portfolio'), icon: '🖼️' },
    { id: 'crosschain', label: t('wallet.test.tabs.crosschain', 'Cross-Chain'), icon: '🌉' },
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <ResponsiveContainer>
            <ResponsiveGrid columns="1 md:2 lg:4" gap="4" className="mb-6">
              <ResponsiveCard>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Wallet className="h-4 w-4" />
                    {t('wallet.test.overview.active_wallets', 'Aktive Wallets')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">12</div>
                  <p className="text-xs text-muted-foreground">{t('wallet.test.overview.new_this_week', '+2 neue diese Woche')}</p>
                </CardContent>
              </ResponsiveCard>

              <ResponsiveCard>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    {t('wallet.test.overview.total_volume', 'Gesamtvolumen')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">$2.4M</div>
                  <p className="text-xs text-muted-foreground">{t('wallet.test.overview.month_change', '+15% diesen Monat')}</p>
                </CardContent>
              </ResponsiveCard>

              <ResponsiveCard>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    {t('wallet.test.overview.security_score', 'Sicherheits-Score')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">98%</div>
                  <p className="text-xs text-muted-foreground">{t('wallet.test.overview.security_grade', 'Ausgezeichnet')}</p>
                </CardContent>
              </ResponsiveCard>

              <ResponsiveCard>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    {t('wallet.test.overview.multisig', 'Multi-Sig Wallets')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">3</div>
                  <p className="text-xs text-muted-foreground">Alle aktiv</p>
                </CardContent>
              </ResponsiveCard>
            </ResponsiveGrid>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>{t('wallet.test.overview.recent', 'Kürzliche Aktivitäten')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">ETH</Badge>
                        <span className="text-sm">{t('wallet.test.overview.activity.receive', 'Transfer erhalten')}</span>
                      </div>
                      <span className="text-sm font-medium">+0.5 ETH</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">UNI</Badge>
                        <span className="text-sm">{t('wallet.test.overview.activity.liquidity', 'Liquidity hinzugefügt')}</span>
                      </div>
                      <span className="text-sm font-medium">+125 UNI</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">NFT</Badge>
                        <span className="text-sm">{t('wallet.test.overview.activity.nft', 'NFT erworben')}</span>
                      </div>
                      <span className="text-sm font-medium">Bored Ape #1234</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('wallet.test.overview.status.title', 'Wallet-Status')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{t('wallet.test.overview.status.hardware', 'Hardware Wallets')}</span>
                      <Badge variant="success">{t('wallet.test.overview.status.hw_connected', '3 verbunden')}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{t('wallet.test.overview.status.2fa', '2FA Status')}</span>
                      <Badge variant="success">{t('wallet.test.overview.status.active', 'Aktiv')}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{t('wallet.test.overview.status.backup', 'Backup Codes')}</span>
                      <Badge variant="warning">{t('wallet.test.overview.status.backup_available', '3 verfügbar')}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{t('wallet.test.overview.status.recovery', 'Recovery Phrase')}</span>
                      <Badge variant="success">{t('wallet.test.overview.status.secured', 'Gesichert')}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ResponsiveContainer>
        )

      case 'transactions':
        return (
          <ResponsiveContainer>
            <Card>
              <CardHeader>
                <CardTitle>{t('wallet.test.transactions.title', 'Transaktionshistorie')}</CardTitle>
                <CardDescription>
                  {t('wallet.test.transactions.desc', 'Detaillierte Übersicht aller Wallet-Transaktionen')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-muted-foreground">
                    {t('wallet.test.transactions.wip', 'Transaktionshistorie wird hier angezeigt (in Entwicklung)')}
                  </p>
                  <ResponsiveButton className="mt-4">
                    <Download className="h-4 w-4 mr-2" />
                    {t('wallet.test.transactions.export', 'Exportieren')}
                  </ResponsiveButton>
                </div>
              </CardContent>
            </Card>
          </ResponsiveContainer>
        )

      case 'analytics':
        return (
          <ResponsiveContainer>
            <Card>
              <CardHeader>
                <CardTitle>{t('wallet.test.analytics.title', 'Erweiterte Analytics')}</CardTitle>
                <CardDescription>
                  {t('wallet.test.analytics.desc', 'KI-gestützte Analyse Ihrer Wallet-Aktivitäten')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-muted-foreground">
                    {t('wallet.test.analytics.wip', 'Erweiterte Analytics Dashboard (in Entwicklung)')}
                  </p>
                </div>
              </CardContent>
            </Card>
          </ResponsiveContainer>
        )

      case 'export':
        return (
          <ResponsiveContainer>
            <Card>
              <CardHeader>
                <CardTitle>{t('wallet.test.export.title', 'Export/Import')}</CardTitle>
                <CardDescription>
                  {t('wallet.test.export.desc', 'Sichern und Wiederherstellen Ihrer Wallet-Daten')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <ResponsiveCard>
                      <CardHeader>
                        <CardTitle className="text-lg">{t('wallet.test.export.section_export', 'Export')}</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <ResponsiveButton className="w-full justify-start">
                          <Download className="h-4 w-4 mr-2" />
                          {t('wallet.test.export.json', 'JSON Export')}
                        </ResponsiveButton>
                        <ResponsiveButton className="w-full justify-start">
                          <Download className="h-4 w-4 mr-2" />
                          {t('wallet.test.export.csv', 'CSV Export')}
                        </ResponsiveButton>
                        <ResponsiveButton className="w-full justify-start">
                          <Download className="h-4 w-4 mr-2" />
                          {t('wallet.test.export.pdf', 'PDF Bericht')}
                        </ResponsiveButton>
                      </CardContent>
                    </ResponsiveCard>

                    <ResponsiveCard>
                      <CardHeader>
                        <CardTitle className="text-lg">{t('wallet.test.export.section_import', 'Import')}</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <ResponsiveButton className="w-full justify-start">
                          <Upload className="h-4 w-4 mr-2" />
                          {t('wallet.test.import.json', 'JSON Import')}
                        </ResponsiveButton>
                        <ResponsiveButton className="w-full justify-start">
                          <Upload className="h-4 w-4 mr-2" />
                          {t('wallet.test.import.add_wallet', 'Wallet hinzufügen')}
                        </ResponsiveButton>
                        <ResponsiveButton className="w-full justify-start">
                          <Upload className="h-4 w-4 mr-2" />
                          {t('wallet.test.import.restore_backup', 'Backup wiederherstellen')}
                        </ResponsiveButton>
                      </CardContent>
                    </ResponsiveCard>
                  </div>
                </div>
              </CardContent>
            </Card>
          </ResponsiveContainer>
        )

      case 'multisig':
        return (
          <ResponsiveContainer>
            <Card>
              <CardHeader>
                <CardTitle>{t('wallet.test.multisig.title', 'Multi-Signature Wallets')}</CardTitle>
                <CardDescription>
                  {t('wallet.test.multisig.desc', 'Verwalten Sie Multi-Sig Wallets mit mehreren Unterschriften')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-muted-foreground">
                    {t('wallet.test.multisig.wip', 'Multi-Signature Wallet Management (in Entwicklung)')}
                  </p>
                </div>
              </CardContent>
            </Card>
          </ResponsiveContainer>
        )

      case 'nft':
        return <NFTPortfolio />

      case 'crosschain':
        return <CrossChainDashboard />

      default:
        return (
          <div className="text-center py-8">
            <p className="text-muted-foreground">Tab noch nicht implementiert</p>
          </div>
        )
    }
  }

  return (
    <TourManager currentPage="wallet">
      <div className="min-h-screen bg-background">
        {/* Mobile Header */}
        <div className="lg:hidden bg-card border-b p-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold">{t('wallet.test.header.title', 'Wallet Management')}</h1>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        <div className="flex">
          {/* Desktop Sidebar */}
          <div className="hidden lg:block w-64 bg-card border-r min-h-[calc(100vh-4rem)]">
            <div className="p-6">
              <h2 className="text-lg font-semibold mb-4">{t('wallet.test.sidebar.title', 'Wallet Features')}</h2>
              <nav className="space-y-2">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full text-left px-3 py-2 rounded-md transition-colors flex items-center gap-2 ${
                      activeTab === tab.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 p-6">
            {renderTabContent()}
          </div>
        </div>

        {/* Mobile Menu Overlay */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 bg-background z-50">
            <div className="p-4">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">{t('wallet.test.sidebar.title', 'Wallet Features')}</h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <nav className="space-y-2">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id)
                      setMobileMenuOpen(false)
                    }}
                    className={`w-full text-left px-3 py-2 rounded-md transition-colors flex items-center gap-2 ${
                      activeTab === tab.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>
        )}
      </div>
    </TourManager>
  )
}

export default WalletTestPage
