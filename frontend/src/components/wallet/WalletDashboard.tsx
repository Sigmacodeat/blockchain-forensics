/*
 * Wallet Dashboard - Haupt-UI für Wallet-Management
 */

import React, { useState } from 'react'
import { useWallet } from '@/contexts/WalletContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/error-message'

export const WalletDashboard: React.FC = () => {
  const { state, createWallet, sendTransaction } = useWallet()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showSendForm, setShowSendForm] = useState(false)
  const [sendChain, setSendChain] = useState('ethereum')
  const [sendTo, setSendTo] = useState('')
  const [sendAmount, setSendAmount] = useState('')
  const [sendPk, setSendPk] = useState('')
  const [sendStatus, setSendStatus] = useState<string | null>(null)

  if (state.isLoading) {
    return <LoadingSpinner />
  }

  if (state.error) {
    return <ErrorMessage message={state.error} />
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Wallet Management</h1>
          <p className="text-muted-foreground">
            Verwalte deine Multi-Chain-Wallets mit KI-gestützter Analyse
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
        >
          Neue Wallet
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-6 p-4 border rounded">
          <h3 className="text-lg font-semibold mb-2">Neue Wallet erstellen</h3>
          <div className="flex gap-2">
            <select className="border p-2 rounded">
              <option>Ethereum</option>
              <option>Bitcoin</option>
              <option>Solana</option>
            </select>
            <button
              onClick={() => createWallet('ethereum')}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              Erstellen
            </button>
          </div>
        </div>
      )}

      <div className="mb-6 p-4 border rounded">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Transaktion senden (einfach)</h3>
          <button
            className="text-sm text-primary-600 hover:underline"
            onClick={() => setShowSendForm((s) => !s)}
          >
            {showSendForm ? 'Schließen' : 'Öffnen'}
          </button>
        </div>
        {showSendForm && (
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            <div className="flex gap-2 items-center">
              <label className="w-24 text-sm text-muted-foreground">Chain</label>
              <select className="border p-2 rounded w-full" value={sendChain} onChange={(e)=>setSendChain(e.target.value)}>
                <option value="ethereum">Ethereum</option>
                <option value="bitcoin">Bitcoin</option>
                <option value="solana">Solana</option>
              </select>
            </div>
            <div className="flex gap-2 items-center">
              <label className="w-24 text-sm text-muted-foreground">To</label>
              <input className="border p-2 rounded w-full" value={sendTo} onChange={(e)=>setSendTo(e.target.value)} placeholder="Empfänger-Adresse" />
            </div>
            <div className="flex gap-2 items-center">
              <label className="w-24 text-sm text-muted-foreground">Amount</label>
              <input className="border p-2 rounded w-full" value={sendAmount} onChange={(e)=>setSendAmount(e.target.value)} placeholder="Betrag (Native)" />
            </div>
            <div className="flex gap-2 items-center">
              <label className="w-24 text-sm text-muted-foreground">PrivKey</label>
              <input className="border p-2 rounded w-full" value={sendPk} onChange={(e)=>setSendPk(e.target.value)} placeholder="Private Key (hex)" type="password" />
            </div>
            <div className="md:col-span-2 flex items-center gap-2">
              <button
                className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
                onClick={async ()=>{
                  setSendStatus(null)
                  try {
                    const tx = await sendTransaction({ chain: sendChain, to: sendTo, amount: sendAmount, privateKey: sendPk })
                    setSendStatus(`Gesendet: ${tx.hash}`)
                  } catch (e:any) {
                    setSendStatus(`Fehler: ${e?.message || String(e)}`)
                  }
                }}
                disabled={!sendTo || !sendAmount || !sendPk}
              >
                Senden
              </button>
              {sendStatus && <span className="text-sm text-muted-foreground">{sendStatus}</span>}
            </div>
            <p className="md:col-span-2 text-xs text-yellow-700">Nur für Tests. Private Keys niemals in Produktion im Browser eingeben.</p>
          </div>
        )}
      </div>

      <div className="grid gap-4">
        {state.wallets.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">Keine Wallets vorhanden</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-2 bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              Erste Wallet erstellen
            </button>
          </div>
        ) : (
          state.wallets.map(wallet => (
            <div key={wallet.id} className="p-4 border rounded">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-semibold">{wallet.chain}</h3>
                  <p className="text-sm text-muted-foreground">{wallet.address}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">
                    {wallet.balance?.balance || '0'} {wallet.chain.toUpperCase()}
                  </p>
                  {wallet.riskScore && (
                    <span className={`text-xs px-2 py-1 rounded ${
                      wallet.riskScore < 0.3 ? 'bg-green-100 text-green-800' :
                      wallet.riskScore < 0.7 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {wallet.riskScore < 0.3 ? 'Sicher' :
                       wallet.riskScore < 0.7 ? 'Mittel' : 'Hoch'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
