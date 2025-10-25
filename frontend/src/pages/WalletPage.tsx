/*
 * Wallet-Seite für die Forensik-Anwendung
 */

import React from 'react'
import { WalletProvider } from '@/contexts/WalletContext'
import { WalletDashboard } from '@/components/wallet/WalletDashboard'

const WalletPage: React.FC = () => {
  return (
    <WalletProvider>
      <WalletDashboard />
    </WalletProvider>
  )
}

export default WalletPage
