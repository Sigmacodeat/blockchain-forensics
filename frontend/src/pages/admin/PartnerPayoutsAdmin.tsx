import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  CheckCircle2,
  DollarSign,
  Loader2,
  RefreshCcw,
  Clock,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import {
  useAdminPayouts,
  useApprovePartnerPayout,
  usePayPartnerPayout,
  PartnerPayout,
} from '@/hooks/usePartner'
import toast from 'react-hot-toast'

const STATUS_OPTIONS: Array<{ value: PartnerPayout['status'] | ''; label: string }> = [
  { value: '', label: 'Alle Status' },
  { value: 'requested', label: 'Requested' },
  { value: 'approved', label: 'Approved' },
  { value: 'paid', label: 'Paid' },
  { value: 'canceled', label: 'Canceled' },
]

const statusBadges: Record<PartnerPayout['status'], string> = {
  requested: 'bg-indigo-100 text-indigo-700',
  approved: 'bg-amber-100 text-amber-700',
  paid: 'bg-green-100 text-green-700',
  canceled: 'bg-slate-200 text-slate-600',
}

export default function PartnerPayoutsAdmin() {
  const { t } = useTranslation()
  const [statusFilter, setStatusFilter] = useState<PartnerPayout['status'] | ''>('requested')

  const {
    data,
    isPending,
    isError,
    isFetching,
    refetch,
  } = useAdminPayouts(statusFilter || undefined)

  const approveMutation = useApprovePartnerPayout()
  const payMutation = usePayPartnerPayout()

  const payouts = data?.data ?? []

  const totals = useMemo(() => {
    if (!payouts.length) {
      return { count: 0, amount: 0 }
    }
    const totalAmount = payouts.reduce((sum, item) => sum + Number(item.amount_usd ?? 0), 0)
    return {
      count: payouts.length,
      amount: totalAmount,
    }
  }, [payouts])

  const handleApprove = async (payoutId: string) => {
    try {
      await approveMutation.mutateAsync(payoutId)
      toast.success(t('partner.admin_payouts.toast_approved', 'Payout wurde freigegeben.'))
    } catch (error: any) {
      toast.error(error?.response?.data?.detail ?? t('partner.admin_payouts.toast_error', 'Aktion fehlgeschlagen.'))
    }
  }

  const handlePay = async (payoutId: string) => {
    const txRef = window.prompt(t('partner.admin_payouts.prompt_tx', 'Transaktionsreferenz (optional):')) || undefined
    try {
      await payMutation.mutateAsync({ payoutId, txRef })
      toast.success(t('partner.admin_payouts.toast_paid', 'Payout wurde ausgezahlt.'))
    } catch (error: any) {
      toast.error(error?.response?.data?.detail ?? t('partner.admin_payouts.toast_error', 'Aktion fehlgeschlagen.'))
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 py-10 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
          <div>
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-8 h-8 text-primary-600" />
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                {t('partner.admin_payouts.title', 'Partner-Auszahlungen')}
              </h1>
            </div>
            <p className="text-gray-600 dark:text-gray-300 mt-2">
              {t(
                'partner.admin_payouts.subtitle',
                'Abwicklung von Partnerauszahlungen inklusive Freigabe, Auszahlung und Nachverfolgung.'
              )}
            </p>
          </div>
          <div className="card px-5 py-4">
            <div className="flex items-center gap-3">
              <DollarSign className="w-5 h-5 text-primary-600" />
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('partner.admin_payouts.stats_count', 'Offene Einträge')}
                </p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {totals.count.toLocaleString()} &middot; {totals.amount.toFixed(2)} USD
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 mb-6 flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
              {t('partner.admin_payouts.filter_status', 'Status')}
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as PartnerPayout['status'] | '')}
              className="input text-sm w-48"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value || 'all'} value={option.value}>
                  {t(`partner.admin_payouts.status.${option.value || 'all'}`, option.label)}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={() => refetch()}
            className="btn-outline flex items-center gap-2"
            disabled={isFetching}
          >
            {isFetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
            {t('partner.admin_payouts.refresh', 'Aktualisieren')}
          </button>
        </div>

        {isPending && (
          <div className="flex justify-center py-16">
            <LoadingSpinner />
          </div>
        )}

        {isError && !isPending && (
          <div className="card p-6 text-center text-red-500">
            {t('partner.admin_payouts.error', 'Auszahlungen konnten nicht geladen werden.')}
          </div>
        )}

        {!isPending && !isError && payouts.length === 0 && (
          <div className="card p-6 text-center text-gray-500 dark:text-gray-400">
            {t('partner.admin_payouts.empty', 'Keine Einträge für die aktuelle Auswahl.')}
          </div>
        )}

        {!isPending && !isError && payouts.length > 0 && (
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-slate-700">
                <thead className="bg-gray-50 dark:bg-slate-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                      {t('partner.admin_payouts.table_partner', 'Partner')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                      {t('partner.admin_payouts.table_amount', 'Betrag (USD)')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                      {t('partner.admin_payouts.table_requested', 'Angefragt am')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                      {t('partner.admin_payouts.table_status', 'Status')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                      {t('partner.admin_payouts.table_actions', 'Aktionen')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-slate-700">
                  {payouts.map((payout) => {
                    const approveDisabled = approveMutation.isPending || payMutation.isPending
                    const payDisabled = payMutation.isPending || approveMutation.isPending
                    const isApproveVisible = payout.status === 'requested'
                    const isPayVisible = payout.status === 'approved' || payout.status === 'requested'
                    return (
                      <tr key={payout.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-200">
                            {payout.partner_user_id ?? `${payout.partner_id.slice(0, 8)}…`}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {payout.partner_id}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">
                          ${Number(payout.amount_usd).toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {new Date(payout.requested_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${statusBadges[payout.status]}`}>
                            {payout.status === 'paid' ? <CheckCircle2 className="w-3 h-3 mr-1" /> : payout.status === 'approved' ? <ShieldCheck className="w-3 h-3 mr-1" /> : payout.status === 'canceled' ? <XCircle className="w-3 h-3 mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                            {payout.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center gap-2">
                            {isApproveVisible && (
                              <button
                                type="button"
                                className="btn-outline btn-xs"
                                onClick={() => handleApprove(payout.id)}
                                disabled={approveDisabled}
                              >
                                {approveMutation.isPending ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  t('partner.admin_payouts.action_approve', 'Freigeben')
                                )}
                              </button>
                            )}
                            {isPayVisible && (
                              <button
                                type="button"
                                className="btn-primary btn-xs"
                                onClick={() => handlePay(payout.id)}
                                disabled={payDisabled}
                              >
                                {payMutation.isPending ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  t('partner.admin_payouts.action_pay', 'Auszahlen')
                                )}
                              </button>
                            )}
                          </div>
                          {payout.tx_ref && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                              TX: {payout.tx_ref}
                            </div>
                          )}
                          {payout.paid_at && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {t('partner.admin_payouts.label_paid_at', 'Ausgezahlt am')}: {new Date(payout.paid_at).toLocaleString()}
                            </div>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
