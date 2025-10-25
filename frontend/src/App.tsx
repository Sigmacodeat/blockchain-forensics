import React, { Suspense } from 'react'
import { Routes, Route, Navigate, Outlet, useParams } from 'react-router-dom'
import PublicLayout from '@/components/PublicLayout'
import Layout from '@/components/Layout'
import { I18nProvider } from '@/contexts/I18nContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { ToastProvider } from '@/components/ui/toast'
import { AuthProvider } from '@/contexts/AuthContext'
import { OnboardingProvider } from '@/contexts/OnboardingContext'
import { ChatProvider } from '@/contexts/ChatContext'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { UserRole } from '@/lib/auth'
import i18n, { resolveLocale } from '@/i18n/config-optimized'
import { initAnalyticsConsentBridge } from '@/lib/analytics'
import { analyticsTracker } from '@/services/analytics-tracker'
import CookieConsent from '@/components/legal/CookieConsent'
import RichStructuredData from '@/components/seo/RichStructuredData'
import ChatWidget from '@/components/chat/ChatWidget'
import ChatErrorBoundary from '@/components/chat/ChatErrorBoundary'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { SkeletonDashboard } from '@/components/ui/SkeletonScreen'

// Hinweis: QueryClientProvider wird in src/main.tsx gesetzt

// Premium Loading Fallback with Skeleton
const LoadingFallback = () => (
  <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-6">
    <SkeletonDashboard />
  </div>
)

// Simple Spinner for quick loads
const Spinner = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
)

// Public pages
const LandingPage = React.lazy(() => import('@/pages/LandingPage.complex'))
const FeaturesPage = React.lazy(() => import('@/pages/FeaturesPage'))
const PricingPage = React.lazy(() => import('@/pages/PricingPage'))
const CheckoutPage = React.lazy(() => import('@/pages/CheckoutPage'))
const AboutPage = React.lazy(() => import('@/pages/AboutPage'))
const PrivacyPolicyPage = React.lazy(() => import('@/pages/legal/PrivacyPolicyPage'))
const TermsPage = React.lazy(() => import('@/pages/legal/TermsPage'))
const ImpressumPage = React.lazy(() => import('@/pages/legal/ImpressumPage'))
const ContactPage = React.lazy(() => import('@/pages/ContactPage'))
const LoginPage = React.lazy(() => import('@/pages/LoginPage'))
const RegisterPage = React.lazy(() => import('@/pages/RegisterPage'))
const VerificationPage = React.lazy(() => import('@/pages/VerificationPage'))
const ForgotPasswordPage = React.lazy(() => import('@/pages/ForgotPasswordPage'))
const NotFoundPage = React.lazy(() => import('@/pages/NotFoundPage'))
// ChatbotLandingPage wird über Subdomain bereitgestellt (chatbot.blocksigmakode.ai)
const NewsCasePublicPage = React.lazy(() => import('@/pages/NewsCasePublicPage'))

// Demo pages (Two-Tier Demo System)
const DemoSandboxPage = React.lazy(() => import('@/pages/DemoSandboxPage'))
const DemoLivePage = React.lazy(() => import('@/pages/DemoLivePage'))

// AppSumo Redemption
const AppSumoRedemption = React.lazy(() => import('@/pages/AppSumoRedemption'))

// Protected pages
const DashboardHub = React.lazy(() => import('@/pages/DashboardHub'))
const MainDashboard = React.lazy(() => import('@/pages/MainDashboard'))
const DashboardsOverviewPage = React.lazy(() => import('@/pages/DashboardsOverviewPage'))
const CasesPage = React.lazy(() => import('@/pages/CasesPage'))
const CaseDetailPage = React.lazy(() => import('@/pages/CaseDetailPage'))
const BridgeTransfersPage = React.lazy(() => import('@/pages/BridgeTransfersPage'))
const TracePage = React.lazy(() => import('@/pages/TracePage'))
const TraceToolsPage = React.lazy(() => import('@/pages/Trace'))
const TraceResultPage = React.lazy(() => import('@/pages/TraceResultPage'))
const InvestigatorGraphPage = React.lazy(() => import('@/pages/InvestigatorGraphPage'))
const CorrelationAnalysisPage = React.lazy(() => import('@/pages/CorrelationAnalysisPage'))
const PerformanceDashboard = React.lazy(() => import('@/pages/PerformanceDashboard'))
const GraphAnalyticsPage = React.lazy(() => import('@/pages/GraphAnalyticsPage'))
const AdvancedAnalyticsPage = React.lazy(() => import('@/pages/AdvancedAnalyticsPage'))
const WebAnalyticsPage = React.lazy(() => import('@/pages/WebAnalyticsPage'))
const MonitoringAlertsPage = React.lazy(() => import('@/pages/MonitoringAlertsPage'))
const MonitoringDashboardPage = React.lazy(() => import('@/pages/MonitoringDashboardPage'))
const OrgsPage = React.lazy(() => import('@/pages/OrgsPage'))
const PolicyManager = React.lazy(() => import('@/features/alerts/PolicyManager'))
const AIAgentPage = React.lazy(() => import('@/pages/AIAgentPage'))
const AdminPage = React.lazy(() => import('@/pages/AdminPage'))
const OnboardingAnalytics = React.lazy(() => import('@/pages/admin/OnboardingAnalytics'))
const ChatAnalytics = React.lazy(() => import('@/pages/ChatAnalytics'))
const ConversationAnalytics = React.lazy(() => import('@/pages/admin/ConversationAnalytics'))
// LinkTrackingAdmin optional - falls vorhanden
let LinkTrackingAdmin: any = null;
try {
  LinkTrackingAdmin = React.lazy(() => import('@/pages/admin/LinkTrackingAdmin'));
} catch (e) {
  // Optional component
}
const AppSumoMetrics = React.lazy(() => import('@/pages/admin/AppSumoMetrics'))
const AppSumoManager = React.lazy(() => import('@/pages/admin/AppSumoManager'))
const InstitutionalVerificationAdmin = React.lazy(() => import('@/pages/admin/InstitutionalVerificationAdmin'))
const FeatureFlagsAdmin = React.lazy(() => import('@/pages/admin/FeatureFlagsAdmin'))
const AdvancedAnalyticsDashboard = React.lazy(() => import('@/pages/admin/AdvancedAnalyticsDashboard'))
const SOARPlaybooksAdmin = React.lazy(() => import('@/pages/admin/SOARPlaybooksAdmin'))
const VASPRiskAdmin = React.lazy(() => import('@/pages/admin/VASPRiskAdmin'))
const PartnerPayoutsAdmin = React.lazy(() => import('@/pages/admin/PartnerPayoutsAdmin'))
const CryptoPaymentsDashboard = React.lazy(() => import('@/pages/admin/CryptoPaymentsDashboard'))
const AddressAnalysisPage = React.lazy(() => import('@/pages/AddressAnalysisPage'))
const ChainCoverage = React.lazy(() => import('@/pages/ChainCoverage'))
const SecurityComplianceDashboard = React.lazy(() => import('@/pages/SecurityComplianceDashboard'))
const WalletTestPage = React.lazy(() => import('@/pages/WalletTestPage'))
const VASPCompliancePage = React.lazy(() => import('@/pages/VASPCompliance'))
const UniversalScreeningPage = React.lazy(() => import('@/pages/UniversalScreening'))
const CustomEntitiesManagerPage = React.lazy(() => import('@/pages/CustomEntitiesManager'))
const IntelligenceNetwork = React.lazy(() => import('@/pages/IntelligenceNetwork'))
const WalletScanner = React.lazy(() => import('@/pages/WalletScanner'))
const BitcoinInvestigation = React.lazy(() => import('@/pages/BitcoinInvestigation'))
const AdvancedIndirectRiskPage = React.lazy(() => import('@/pages/AdvancedIndirectRisk'))

// Use Case Pages
const UseCasesOverview = React.lazy(() => import('@/pages/UseCasesOverview'))
const UseCaseLawEnforcement = React.lazy(() => import('@/pages/UseCaseLawEnforcement'))
const UseCaseCompliance = React.lazy(() => import('@/pages/UseCaseCompliance'))
const UseCasePolice = React.lazy(() => import('@/pages/UseCasePolice'))
const UseCasePrivateInvestigators = React.lazy(() => import('@/pages/UseCasePrivateInvestigators'))
const UseCaseFinancialInstitutions = React.lazy(() => import('@/pages/UseCaseFinancialInstitutions'))
const AutomationPage = React.lazy(() => import('@/pages/AutomationPage'))
const PatternsPage = React.lazy(() => import('@/pages/PatternsPage'))
const BillingPage = React.lazy(() => import('@/pages/BillingPage'))
const APIKeysPage = React.lazy(() => import('@/pages/APIKeysPage'))
const WebhooksPage = React.lazy(() => import('@/pages/WebhooksPage'))
const ForensicsHubPage = React.lazy(() => import('@/pages/ForensicsHubPage'))
const PrivacyDemixingPage = React.lazy(() => import('@/pages/PrivacyDemixingPage'))
const SettingsPage = React.lazy(() => import('@/pages/SettingsPage'))
const FirewallControlCenter = React.lazy(() => import('@/pages/FirewallControlCenter'))
const PartnerDashboard = React.lazy(() => import('@/pages/PartnerDashboard'))
const NewsCasesManager = React.lazy(() => import('@/pages/NewsCasesManager'))
const OptimizationDashboard = React.lazy(() => import('@/pages/OptimizationDashboard'))

// Bank System Pages
const CaseManagement = React.lazy(() => import('@/pages/bank/CaseManagement'))
const CaseDetail = React.lazy(() => import('@/pages/bank/CaseDetail'))

// Helper: Wrap route in Suspense
const withSuspense = (Component: React.LazyExoticComponent<any>) => (
  <Suspense fallback={<LoadingFallback />}>
    <Component />
  </Suspense>
)

function LangLayout() {
  const { lang } = useParams()
  const requested = lang || 'en'
  const resolved = resolveLocale(requested)

  // Sprache außerhalb der Render-Phase synchronisieren und HTML lang setzen
  React.useEffect(() => {
    if (resolved) {
      if (i18n.language !== resolved) {
        void i18n.changeLanguage(resolved)
      }
      try { document.documentElement.setAttribute('lang', resolved) } catch {}
    }
  }, [resolved])

  // Redirect only if die gewünschte Sprache ungültig ist
  if (!resolved) {
    return <Navigate to={`/${i18n.language || 'en'}`} replace />
  }

  return <Outlet />
}

function App() {
  React.useEffect(() => {
    initAnalyticsConsentBridge()
    analyticsTracker.initialize()
    return () => {
      analyticsTracker.shutdown()
    }
  }, [])
  return (
    <ErrorBoundary showDetails={import.meta.env.DEV}>
      <I18nProvider>
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <ChatProvider>
                <OnboardingProvider>
                    <Routes>
                {/* Redirect root to current language */}
                <Route path="/" element={<Navigate to={`/${i18n.language || 'en'}`} replace />} />

                {/* Language scoped routes */}
                <Route path=":lang" element={<LangLayout />}>
                  {/* Public */}
                  <Route index element={<PublicLayout><React.Suspense fallback={<div />}> <LandingPage /> </React.Suspense></PublicLayout>} />
                  <Route path="features" element={<PublicLayout><React.Suspense fallback={<div />}> <FeaturesPage /> </React.Suspense></PublicLayout>} />
                  <Route path="optimization" element={<PublicLayout><React.Suspense fallback={<div />}> <OptimizationDashboard /> </React.Suspense></PublicLayout>} />
                  <Route path="pricing" element={<PublicLayout><React.Suspense fallback={<div />}> <PricingPage /> </React.Suspense></PublicLayout>} />
                  <Route path="checkout/:orderId" element={<PublicLayout><React.Suspense fallback={<div />}> <CheckoutPage /> </React.Suspense></PublicLayout>} />
                  <Route path="news/:slug" element={<PublicLayout><React.Suspense fallback={<div />}> <NewsCasePublicPage /> </React.Suspense></PublicLayout>} />
                  {/* Chatbot-Route entfernt - wird über chatbot.blocksigmakode.ai bereitgestellt */}
                  <Route path="about" element={<PublicLayout><React.Suspense fallback={<div />}> <AboutPage /> </React.Suspense></PublicLayout>} />
                  <Route path="contact" element={<PublicLayout><React.Suspense fallback={<div />}> <ContactPage /> </React.Suspense></PublicLayout>} />
                  <Route path="legal/privacy" element={<PublicLayout><React.Suspense fallback={<div />}> <PrivacyPolicyPage /> </React.Suspense></PublicLayout>} />
                  <Route path="legal/terms" element={<PublicLayout><React.Suspense fallback={<div />}> <TermsPage /> </React.Suspense></PublicLayout>} />
                  <Route path="legal/impressum" element={<PublicLayout><React.Suspense fallback={<div />}> <ImpressumPage /> </React.Suspense></PublicLayout>} />
                  
                  {/* Use Case Pages (Marketing/SEO) - AI-AGENT FOKUS */}
                  <Route path="use-cases" element={<PublicLayout><React.Suspense fallback={<div />}> <UseCasesOverview /> </React.Suspense></PublicLayout>} />
                  <Route path="use-cases/law-enforcement" element={<PublicLayout><React.Suspense fallback={<div />}> <UseCaseLawEnforcement /> </React.Suspense></PublicLayout>} />
                  <Route path="use-cases/compliance" element={<PublicLayout><React.Suspense fallback={<div />}> <UseCaseCompliance /> </React.Suspense></PublicLayout>} />
                  <Route path="use-cases/police" element={<PublicLayout><React.Suspense fallback={<div />}> <UseCasePolice /> </React.Suspense></PublicLayout>} />
                  <Route path="use-cases/private-investigators" element={<PublicLayout><React.Suspense fallback={<div />}> <UseCasePrivateInvestigators /> </React.Suspense></PublicLayout>} />
                  <Route path="use-cases/financial-institutions" element={<PublicLayout><React.Suspense fallback={<div />}> <UseCaseFinancialInstitutions /> </React.Suspense></PublicLayout>} />
                  
                  <Route path="login" element={<React.Suspense fallback={<div />}> <LoginPage /> </React.Suspense>} />
                  <Route path="register" element={<React.Suspense fallback={<div />}> <RegisterPage /> </React.Suspense>} />
                  <Route path="verify" element={<React.Suspense fallback={<div />}> <VerificationPage /> </React.Suspense>} />
                  <Route path="verify/:user_id" element={<React.Suspense fallback={<div />}> <VerificationPage /> </React.Suspense>} />
                  <Route path="forgot-password" element={<React.Suspense fallback={<div />}> <ForgotPasswordPage /> </React.Suspense>} />

                  {/* Demo System (Two-Tier: Sandbox + Live) - NO AUTH REQUIRED */}
                  <Route path="demo/sandbox" element={<React.Suspense fallback={<div />}> <DemoSandboxPage /> </React.Suspense>} />
                  <Route path="demo/live" element={<React.Suspense fallback={<div />}> <DemoLivePage /> </React.Suspense>} />

                  {/* AppSumo Redemption - NO AUTH REQUIRED */}
                  <Route path="redeem/appsumo" element={<React.Suspense fallback={<div />}> <AppSumoRedemption /> </React.Suspense>} />

                  {/* Protected (Dashboard workspace) */}
                  <Route path="dashboard" element={<ProtectedRoute routePath="/dashboard"><Layout><React.Suspense fallback={<div />}> <MainDashboard /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="dashboard-hub" element={<ProtectedRoute routePath="/dashboard"><Layout><React.Suspense fallback={<div />}> <DashboardHub /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="dashboards" element={<ProtectedRoute requiredPlan="pro" routePath="/dashboards"><Layout><React.Suspense fallback={<div />}> <DashboardsOverviewPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="cases" element={<ProtectedRoute routePath="/cases"><Layout><React.Suspense fallback={<div />}> <CasesPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="cases/:caseId" element={<ProtectedRoute routePath="/cases"><Layout><React.Suspense fallback={<div />}> <CaseDetailPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="trace" element={<ProtectedRoute routePath="/trace"><Layout><React.Suspense fallback={<div />}> <TracePage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="trace/tools" element={<ProtectedRoute requiredPlan="starter" routePath="/trace/tools"><Layout><React.Suspense fallback={<div />}> <TraceToolsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="trace/result/:txHash" element={<ProtectedRoute><Layout><React.Suspense fallback={<div />}> <TraceResultPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="address/:address" element={<ProtectedRoute><Layout><React.Suspense fallback={<div />}> <AddressAnalysisPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="coverage" element={<ProtectedRoute><Layout><React.Suspense fallback={<div />}> <ChainCoverage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="analytics" element={<ProtectedRoute requiredPlan="pro" routePath="/analytics"><Layout><React.Suspense fallback={<div />}> <GraphAnalyticsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="analytics/advanced" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]} routePath="/analytics/advanced"><Layout><React.Suspense fallback={<LoadingFallback />}> <AdvancedAnalyticsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="web-analytics" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <WebAnalyticsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="monitoring" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <MonitoringAlertsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="monitoring/dashboard" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <MonitoringDashboardPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="investigator" element={<ProtectedRoute requiredPlan="pro" routePath="/investigator"><Layout><React.Suspense fallback={<div />}> <InvestigatorGraphPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="correlation" element={<ProtectedRoute requiredPlan="pro" routePath="/correlation"><Layout><React.Suspense fallback={<div />}> <CorrelationAnalysisPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="performance" element={<ProtectedRoute requiredPlan="business" routePath="/performance"><Layout><React.Suspense fallback={<div />}> <PerformanceDashboard /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="news-cases" element={<ProtectedRoute requiredPlan="pro" routePath="/news-cases"><Layout><React.Suspense fallback={<div />}> <NewsCasesManager /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="security" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN, UserRole.AUDITOR]}><Layout><React.Suspense fallback={<div />}> <SecurityComplianceDashboard /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="bridge-transfers" element={<ProtectedRoute routePath="/bridge-transfers"><Layout><React.Suspense fallback={<div />}> <BridgeTransfersPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="wallet" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN, UserRole.ANALYST]}><Layout><React.Suspense fallback={<div />}> <WalletTestPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="orgs" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <OrgsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="ai-agent" element={<ProtectedRoute requiredPlan="plus" routePath="/ai-agent"><Layout><React.Suspense fallback={<div />}> <AIAgentPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="intelligence-network" element={<ProtectedRoute requiredPlan="pro" routePath="/intelligence-network"><Layout><React.Suspense fallback={<div />}> <IntelligenceNetwork /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="wallet-scanner" element={<ProtectedRoute requiredPlan="pro" routePath="/wallet-scanner"><Layout><React.Suspense fallback={<div />}> <WalletScanner /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="bitcoin-investigation" element={<ProtectedRoute requiredPlan="plus" routePath="/bitcoin-investigation"><Layout><React.Suspense fallback={<div />}> <BitcoinInvestigation /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="policies" element={<ProtectedRoute requiredPlan="business" routePath="/policies"><Layout><React.Suspense fallback={<div />}> <PolicyManager /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="vasp-compliance" element={<ProtectedRoute requiredPlan="business" routePath="/vasp-compliance"><Layout><React.Suspense fallback={<div />}> <VASPCompliancePage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="universal-screening" element={<ProtectedRoute requiredPlan="pro" routePath="/universal-screening"><Layout><React.Suspense fallback={<div />}> <UniversalScreeningPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="custom-entities" element={<ProtectedRoute requiredPlan="pro" routePath="/custom-entities"><Layout><React.Suspense fallback={<div />}> <CustomEntitiesManagerPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="advanced-indirect-risk" element={<ProtectedRoute requiredPlan="plus" routePath="/advanced-indirect-risk"><Layout><React.Suspense fallback={<div />}> <AdvancedIndirectRiskPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="automation" element={<ProtectedRoute requiredPlan="business" routePath="/automation"><Layout><React.Suspense fallback={<div />}> <AutomationPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="patterns" element={<ProtectedRoute requiredPlan="pro" routePath="/patterns"><Layout><React.Suspense fallback={<div />}> <PatternsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="privacy-demixing" element={<ProtectedRoute requiredPlan="pro" routePath="/privacy-demixing"><Layout><React.Suspense fallback={<div />}> <PrivacyDemixingPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="firewall" element={<ProtectedRoute requiredPlan="pro" routePath="/firewall"><Layout><React.Suspense fallback={<div />}> <FirewallControlCenter /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="partner" element={<ProtectedRoute requiredRoles={[UserRole.PARTNER, UserRole.ADMIN]} routePath="/partner"><Layout><React.Suspense fallback={<div />}> <PartnerDashboard /> </React.Suspense></Layout></ProtectedRoute>} />
                  
                  {/* Bank System - Case Management */}
                  <Route path="bank/cases" element={<ProtectedRoute requiredPlan="enterprise" routePath="/bank/cases"><Layout><React.Suspense fallback={<div />}> <CaseManagement /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="bank/cases/:caseId" element={<ProtectedRoute requiredPlan="enterprise" routePath="/bank/cases"><Layout><React.Suspense fallback={<div />}> <CaseDetail /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="settings" element={<ProtectedRoute routePath="/settings"><Layout><React.Suspense fallback={<div />}> <SettingsPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="billing" element={<ProtectedRoute routePath="/billing"><Layout><React.Suspense fallback={<div />}> <BillingPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="api-keys" element={<ProtectedRoute requiredPlan="pro" routePath="/api-keys"><Layout><React.Suspense fallback={<div />}> <APIKeysPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="webhooks" element={<ProtectedRoute requiredPlan="starter" routePath="/webhooks"><Layout><React.Suspense fallback={<div />}> <WebhooksPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="forensics" element={<ProtectedRoute routePath="/forensics"><Layout><React.Suspense fallback={<div />}> <ForensicsHubPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <AdminPage /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/onboarding-analytics" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <OnboardingAnalytics /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/chat-analytics" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <ChatAnalytics /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/conversation-analytics" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <ConversationAnalytics /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/feature-flags" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<LoadingFallback />}> <FeatureFlagsAdmin /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/analytics-premium" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<LoadingFallback />}> <AdvancedAnalyticsDashboard /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/soar-playbooks" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <SOARPlaybooksAdmin /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/vasp-risk" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <VASPRiskAdmin /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/partner-payouts" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <PartnerPayoutsAdmin /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/link-tracking" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <LinkTrackingAdmin /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/appsumo" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <AppSumoMetrics /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/appsumo/manager" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<div />}> <AppSumoManager /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/institutional-verifications" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN, UserRole.AUDITOR]}><Layout><React.Suspense fallback={<div />}> <InstitutionalVerificationAdmin /> </React.Suspense></Layout></ProtectedRoute>} />
                  <Route path="admin/crypto-payments-dashboard" element={<ProtectedRoute requiredRoles={[UserRole.ADMIN]}><Layout><React.Suspense fallback={<LoadingFallback />}> <CryptoPaymentsDashboard /> </React.Suspense></Layout></ProtectedRoute>} />

                  {/* Language scoped 404 */}
                  <Route path="*" element={<PublicLayout><React.Suspense fallback={<div />}> <NotFoundPage /> </React.Suspense></PublicLayout>} />
                </Route>

                {/* Fallback: any non-matching route -> language root */}
                <Route path="*" element={<Navigate to={`/${i18n.language || 'en'}`} replace />} />
              </Routes>

            {/* Global Components */}
            <RichStructuredData />
            <CookieConsent />
            
            {/* Chatbot Widget */}
            <ChatErrorBoundary>
              <ChatWidget />
            </ChatErrorBoundary>
          </OnboardingProvider>
        </ChatProvider>
      </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  </I18nProvider>
</ErrorBoundary>
  )
}

export default App
