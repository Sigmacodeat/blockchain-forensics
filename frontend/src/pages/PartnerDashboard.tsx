import { useMemo, useState } from 'react'
import { Clipboard, ClipboardCheck, DollarSign, Link as LinkIcon, Users, BarChart3, Download } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/error-message'
import {
  usePartnerAccount,
  usePartnerCommissions,
  usePartnerReferrals,
  useRequestPartnerPayout,
  useTriggerPartnerExport
} from '@/hooks/usePartner'
import toast from 'react-hot-toast'

export default function PartnerDashboard() {
  const { t, i18n } = useTranslation()
  const [copied, setCopied] = useState(false)
  const [commissionStatus, setCommissionStatus] = useState<string | undefined>(undefined)
  const [payoutAmount, setPayoutAmount] = useState('')

  const { data: accountData, isPending: accountPending, isError: accountError } = usePartnerAccount()
  const {
    data: commissionsData,
    isPending: commissionsPending,
    isError: commissionsError
  } = usePartnerCommissions(commissionStatus)
  const {
    data: referralsData,
    isPending: referralsPending,
    isError: referralsError
  } = usePartnerReferrals()
  const requestPayout = useRequestPartnerPayout()
  const triggerExport = useTriggerPartnerExport()

  const account = accountData?.account
  const stats = useMemo(() => accountData?.stats ?? {}, [accountData])

  const referralCode = account?.referral_code
  const referralLink = referralCode
    ? `${window.location.origin}/${i18n.language || 'en'}/register?ref=${referralCode}`
    : ''

  const handleCopy = async () => {
    if (!referralLink) return
    try {
      await navigator.clipboard.writeText(referralLink)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch (err) {
      console.error('Failed to copy referral link', err)
    }
  }

  const availableStats = stats

  const isLoading = accountPending || commissionsPending || referralsPending

  const commissionRows = commissionsData?.data ?? []
  const referralRows = referralsData?.data ?? []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <BarChart3 className="w-8 h-8 text-indigo-500" />
          <h1 className="text-3xl font-bold text-slate-900">{t('partner.dashboard.title', 'Partner Dashboard')}</h1>
        </div>
        <p className="text-slate-600">
          {t('partner.dashboard.subtitle', 'Verwalte deine Empfehlungen, Kommissionen und Auszahlungen.')}
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      )}

      {accountError && !accountPending && (
        <ErrorMessage message={t('partner.dashboard.account_error', 'Account konnte nicht geladen werden.')} />
      )}

      {account && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <LinkIcon className="w-5 h-5 text-indigo-500" />
              {t('partner.dashboard.ref_link', 'Referral-Link')}
            </h2>
            <div className="bg-slate-100 rounded-md px-3 py-2 text-sm break-all">
              {referralLink || t('partner.dashboard.no_link', 'Kein Link verfügbar')}
            </div>
            <div className="flex items-center gap-2 mt-4">
              <button
                type="button"
                className="btn-outline flex items-center gap-2"
                onClick={handleCopy}
                disabled={!referralLink}
              >
                {copied ? <ClipboardCheck className="w-4 h-4" /> : <Clipboard className="w-4 h-4" />}
                {copied ? t('partner.dashboard.copied', 'Kopiert!') : t('partner.dashboard.copy', 'Link kopieren')}
              </button>
              <span className="text-xs text-slate-500">
                {t('partner.dashboard.cookie', 'Tracking-Dauer')}: {account.cookie_duration_days} {t('partner.dashboard.days', 'Tage')}
              </span>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-indigo-500" />
              {t('partner.dashboard.payout', 'Auszahlung beantragen')}
            </h2>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault()
                const amount = parseFloat(payoutAmount)
                if (!amount || amount <= 0) return
                requestPayout.mutate(amount, {
                  onSuccess: () => {
                    setPayoutAmount('')
                    toast.success(t('partner.dashboard.payout_success', 'Auszahlung erfolgreich angefordert.'))
                  },
                  onError: (error: any) => {
                    toast.error(error?.response?.data?.detail ?? t('partner.dashboard.payout_error', 'Auszahlung konnte nicht angefordert werden.'))
                  }
                })
              }}
            >
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">
                  {t('partner.dashboard.amount', 'Betrag (USD)')}
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  className="input w-full"
                  value={payoutAmount}
                  onChange={(e) => setPayoutAmount(e.target.value)}
                  placeholder={t('partner.dashboard.min_payout', 'Mindestbetrag')} 
                />
              </div>
              <button
                type="submit"
                className="btn-primary w-full"
                disabled={requestPayout.isPending}
              >
                {requestPayout.isPending
                  ? t('partner.dashboard.payout_pending', 'Anfrage wird gesendet...')
                  : t('partner.dashboard.payout_request', 'Auszahlung anfordern')}
              </button>
              <p className="text-xs text-slate-500">
                {t('partner.dashboard.payout_minimum', 'Mindestbetrag')}: {account.min_payout_usd} USD
              </p>
            </form>
            <button
              type="button"
              className="btn-outline w-full mt-3 flex items-center justify-center gap-2"
              onClick={async () => {
                try {
                  await triggerExport({ status: commissionStatus })
                  toast.success(t('partner.dashboard.export_success', 'CSV-Export gestartet.'))
                } catch (error: any) {
                  toast.error(error?.response?.data?.detail ?? t('partner.dashboard.export_error', 'Export fehlgeschlagen.'))
                }
              }}
              disabled={requestPayout.isPending}
            >
              <Download className="w-4 h-4" />
              {t('partner.dashboard.export_csv', 'Kommissionen exportieren')}
            </button>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-500" />
              {t('partner.dashboard.account_info', 'Account-Details')}
            </h2>
            <dl className="text-sm space-y-3">
              <div className="flex justify-between">
                <dt className="text-slate-600">{t('partner.dashboard.commission_rate', 'Provision')}</dt>
                <dd className="font-medium text-slate-900">{account.commission_rate}%</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">{t('partner.dashboard.recurring_rate', 'Wiederkehrend')}</dt>
                <dd className="font-medium text-slate-900">{account.recurring_rate}%</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">{t('partner.dashboard.status', 'Status')}</dt>
                <dd className="font-medium text-slate-900">{account.is_active ? t('partner.dashboard.active', 'Aktiv') : t('partner.dashboard.inactive', 'Inaktiv')}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">{t('partner.dashboard.since', 'Seit')}</dt>
                <dd className="font-medium text-slate-900">{new Date(account.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </div>
        </div>
      )}

      {account && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-10">
          {Object.entries(availableStats).map(([key, value]) => (
            <div key={key} className="bg-indigo-50 border border-indigo-100 rounded-lg p-4">
              <p className="text-xs uppercase tracking-wide text-indigo-600 mb-1">{key}</p>
              <p className="text-2xl font-semibold text-indigo-900">{value?.toLocaleString?.() ?? value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">{t('partner.dashboard.commissions', 'Kommissionen')}</h2>
            <select
              className="input text-sm w-40"
              value={commissionStatus ?? ''}
              onChange={(e) => setCommissionStatus(e.target.value || undefined)}
            >
              <option value="">{t('partner.dashboard.all_status', 'Alle Status')}</option>
              <option value="pending">{t('partner.dashboard.status_pending', 'Ausstehend')}</option>
              <option value="approved">{t('partner.dashboard.status_approved', 'Freigegeben')}</option>
              <option value="paid">{t('partner.dashboard.status_paid', 'Ausgezahlt')}</option>
              <option value="canceled">{t('partner.dashboard.status_canceled', 'Storniert')}</option>
            </select>
          </div>
          {commissionsPending && <LoadingSpinner />}
          {commissionsError && !commissionsPending && (
            <ErrorMessage message={t('partner.dashboard.commissions_error', 'Kommissionen konnten nicht geladen werden.')} />
          )}
          {!commissionsPending && !commissionsError && commissionRows.length === 0 && (
            <p className="text-sm text-slate-500">{t('partner.dashboard.no_commissions', 'Noch keine Kommissionen vorhanden.')}</p>
          )}
          {!commissionsPending && commissionRows.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 uppercase text-xs">
                    <th className="py-2 pr-4">{t('partner.dashboard.date', 'Datum')}</th>
                    <th className="py-2 pr-4">{t('partner.dashboard.plan', 'Plan')}</th>
                    <th className="py-2 pr-4">{t('partner.dashboard.amount', 'Betrag')}</th>
                    <th className="py-2 pr-4">{t('partner.dashboard.commission', 'Provision')}</th>
                    <th className="py-2 pr-4">{t('partner.dashboard.status', 'Status')}</th>
                  </tr>
                </thead>
                <tbody>
                  {commissionRows.map((item) => (
                    <tr key={item.id} className="border-t border-slate-200">
                      <td className="py-2 pr-4 text-slate-700 whitespace-nowrap">{new Date(item.event_time).toLocaleString()}</td>
                      <td className="py-2 pr-4 text-slate-700">{item.plan_name || '—'}</td>
                      <td className="py-2 pr-4 text-slate-700">${item.amount_usd.toFixed(2)}</td>
                      <td className="py-2 pr-4 text-slate-700">
                        ${item.commission_usd.toFixed(2)}
                        <span className="text-xs text-slate-500 ml-2">({item.commission_rate}%)</span>
                      </td>
                      <td className="py-2 pr-4">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold
                            ${
                              item.status === 'paid'
                                ? 'bg-green-100 text-green-700'
                                : item.status === 'approved'
                                  ? 'bg-amber-100 text-amber-700'
                                  : item.status === 'canceled'
                                    ? 'bg-slate-200 text-slate-600'
                                    : 'bg-indigo-100 text-indigo-700'
                            }
                          `}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">{t('partner.dashboard.referrals', 'Referrals')}</h2>
          {referralsPending && <LoadingSpinner />}
          {referralsError && !referralsPending && (
            <ErrorMessage message={t('partner.dashboard.referrals_error', 'Referrals konnten nicht geladen werden.')} />
          )}
          {!referralsPending && !referralsError && referralRows.length === 0 && (
            <p className="text-sm text-slate-500">{t('partner.dashboard.no_referrals', 'Noch keine Referrals vorhanden.')}</p>
          )}
          {!referralsPending && referralRows.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 uppercase text-xs">
                    <th className="py-2 pr-4">{t('partner.dashboard.email', 'Email')}</th>
                    <th className="py-2 pr-4">{t('partner.dashboard.source', 'Quelle')}</th>
                    <th className="py-2 pr-4">{t('partner.dashboard.first_touch', 'Erstkontakt')}</th>
                    <th className="py-2 pr-4">{t('partner.dashboard.last_touch', 'Letzter Kontakt')}</th>
                  </tr>
                </thead>
                <tbody>
                  {referralRows.map((item) => (
                    <tr key={item.id} className="border-t border-slate-200">
                      <td className="py-2 pr-4 text-slate-700">{item.user_email || '—'}</td>
                      <td className="py-2 pr-4 text-slate-700">{item.source || '—'}</td>
                      <td className="py-2 pr-4 text-slate-700 whitespace-nowrap">{new Date(item.first_touch_at).toLocaleString()}</td>
                      <td className="py-2 pr-4 text-slate-700 whitespace-nowrap">{new Date(item.last_touch_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
