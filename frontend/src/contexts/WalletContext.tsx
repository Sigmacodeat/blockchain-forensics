/*
 * Wallet Provider für React Context
 *
 * Bietet zentrale Wallet-Verwaltung mit Trust Wallet Core Integration.
 */

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { Wallet, Transaction, WalletBalance, HardwareWalletDevice } from '../types/wallet'

interface WalletState {
  wallets: Wallet[]
  activeWallet: Wallet | null
  hardwareDevices: HardwareWalletDevice[]
  isLoading: boolean
  error: string | null
}

type WalletAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_WALLETS'; payload: Wallet[] }
  | { type: 'ADD_WALLET'; payload: Wallet }
  | { type: 'SET_ACTIVE_WALLET'; payload: Wallet | null }
  | { type: 'UPDATE_WALLET_BALANCE'; payload: { walletId: string; balance: WalletBalance } }
  | { type: 'SET_HARDWARE_DEVICES'; payload: HardwareWalletDevice[] }

interface WalletContextType {
  state: WalletState
  // Wallet Management
  createWallet: (chain: string, mnemonic?: string) => Promise<Wallet>
  loadWallets: () => Promise<void>
  setActiveWallet: (wallet: Wallet | null) => void
  refreshWalletBalance: (walletId: string) => Promise<void>

  // Transaction Operations
  signTransaction: (chain: string, txData: any, privateKey: string) => Promise<string>
  broadcastTransaction: (chain: string, signedTx: string) => Promise<Transaction>
  sendTransaction: (args: { chain: string; to: string; amount: string; privateKey: string; gasPrice?: string; gasLimit?: number }) => Promise<Transaction>

  // Hardware Wallet Support
  detectHardwareWallets: () => Promise<HardwareWalletDevice[]>
  signWithHardwareWallet: (device: HardwareWalletDevice, chain: string, txData: any) => Promise<string>

  // Analytics
  getWalletHistory: (walletId: string) => Promise<Transaction[]>
  analyzeWallet: (walletId: string) => Promise<any>
}

const initialState: WalletState = {
  wallets: [],
  activeWallet: null,
  hardwareDevices: [],
  isLoading: false,
  error: null,
}

const WalletContext = createContext<WalletContextType | undefined>(undefined)

export const useWallet = () => {
  const context = useContext(WalletContext)
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider')
  }
  return context
}

interface WalletProviderProps {
  children: ReactNode
}

// Reducer auf Modulebene definiert
const walletReducer = (state: WalletState, action: WalletAction): WalletState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    case 'SET_WALLETS':
      return { ...state, wallets: action.payload }
    case 'ADD_WALLET':
      return { ...state, wallets: [...state.wallets, action.payload] }
    case 'SET_ACTIVE_WALLET':
      return { ...state, activeWallet: action.payload }
    case 'UPDATE_WALLET_BALANCE':
      return {
        ...state,
        wallets: state.wallets.map(wallet =>
          wallet.id === action.payload.walletId
            ? { ...wallet, balance: action.payload.balance }
            : wallet
        ),
        activeWallet: state.activeWallet?.id === action.payload.walletId
          ? { ...state.activeWallet, balance: action.payload.balance }
          : state.activeWallet
      }
    case 'SET_HARDWARE_DEVICES':
      return { ...state, hardwareDevices: action.payload }
    default:
      return state
  }
}

export const WalletProvider: React.FC<WalletProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(walletReducer, initialState)

  // API Calls
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`/api/v1/wallet${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    return response.json()
  }

  // Wallet Management Functions
  const createWallet = async (chain: string, mnemonic?: string): Promise<Wallet> => {
    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'SET_ERROR', payload: null })

    try {
      const response = await apiCall('/create', {
        method: 'POST',
        body: JSON.stringify({ chain, mnemonic }),
      })

      const wallet: Wallet = {
        id: response.id,
        chain: response.chain,
        address: response.address,
        publicKey: response.public_key,
        balance: response.balance,
        createdAt: response.created_at,
        riskScore: response.risk_score,
        riskFactors: response.risk_factors,
      }

      dispatch({ type: 'ADD_WALLET', payload: wallet })
      return wallet
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      dispatch({ type: 'SET_ERROR', payload: errorMessage })
      throw error
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  const loadWallets = async (): Promise<void> => {
    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'SET_ERROR', payload: null })

    try {
      // Serverseitige Wallet-Persistenz abrufen und mit LocalStorage mergen
      let serverWallets: Wallet[] = []
      try {
        const res = await apiCall('/list')
        serverWallets = Array.isArray(res) ? res : []
      } catch (e) {
        // Fallback auf LocalStorage, wenn Serverliste nicht verfügbar ist
      }

      const storedWallets = localStorage.getItem('forensics_wallets')
      let localWallets: Wallet[] = []
      if (storedWallets) {
        localWallets = JSON.parse(storedWallets)
      }

      // Merge nach ID (Server gewinnt)
      const byId = new Map<string, Wallet>()
      for (const w of localWallets) byId.set(w.id, w)
      for (const w of serverWallets) byId.set(w.id, w)
      const merged = Array.from(byId.values())

      if (merged.length > 0) {
        dispatch({ type: 'SET_WALLETS', payload: merged })
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      dispatch({ type: 'SET_ERROR', payload: errorMessage })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  const setActiveWallet = (wallet: Wallet | null): void => {
    dispatch({ type: 'SET_ACTIVE_WALLET', payload: wallet })
  }

  const refreshWalletBalance = async (walletId: string): Promise<void> => {
    try {
      const response = await apiCall(`/${walletId}/balance`)
      dispatch({
        type: 'UPDATE_WALLET_BALANCE',
        payload: { walletId, balance: response }
      })
    } catch (error) {
      console.error('Failed to refresh balance:', error)
    }
  }

  // Transaction Functions
  const signTransaction = async (chain: string, txData: any, privateKey: string): Promise<string> => {
    try {
      const response = await apiCall('/sign', {
        method: 'POST',
        body: JSON.stringify({ chain, ...txData, private_key: privateKey }),
      })
      return response.signed_tx
    } catch (error) {
      throw new Error(`Signing failed: ${error}`)
    }
  }

  const broadcastTransaction = async (chain: string, signedTx: string): Promise<Transaction> => {
    try {
      const response = await apiCall('/broadcast', {
        method: 'POST',
        body: JSON.stringify({ chain, signed_tx: signedTx }),
      })

      return {
        hash: response.tx_hash,
        status: response.status,
        analysis: response.analysis,
        timestamp: response.timestamp,
      }
    } catch (error) {
      throw new Error(`Broadcast failed: ${error}`)
    }
  }

  const sendTransaction = async (args: { chain: string; to: string; amount: string; privateKey: string; gasPrice?: string; gasLimit?: number }): Promise<Transaction> => {
    const { chain, to, amount, privateKey, gasPrice, gasLimit } = args
    const txData: any = { to_address: to, amount, gas_price: gasPrice, gas_limit: gasLimit }
    const signed = await signTransaction(chain, txData, privateKey)
    const tx = await broadcastTransaction(chain, signed)
    return tx
  }

  // Hardware Wallet Functions
  const detectHardwareWallets = async (): Promise<HardwareWalletDevice[]> => {
    try {
      // In einer echten Implementierung würde hier eine API aufgerufen
      // die Hardware-Wallets erkennt
      dispatch({ type: 'SET_HARDWARE_DEVICES', payload: [] })
      return []
    } catch (error) {
      console.error('Hardware wallet detection failed:', error)
      return []
    }
  }

  const signWithHardwareWallet = async (
    device: HardwareWalletDevice,
    chain: string,
    txData: any
  ): Promise<string> => {
    try {
      // Hardware-Wallet-Signing implementieren
      // Dies würde eine WebUSB oder ähnliche API verwenden
      throw new Error('Hardware wallet signing not yet implemented')
    } catch (error) {
      throw new Error(`Hardware wallet signing failed: ${error}`)
    }
  }

  // Analytics Functions
  const getWalletHistory = async (walletId: string): Promise<Transaction[]> => {
    try {
      const response = await apiCall(`/${walletId}/history`)
      return response.transactions.map((tx: any) => ({
        hash: tx.hash,
        status: tx.status,
        analysis: tx.analysis,
        timestamp: tx.timestamp,
      }))
    } catch (error) {
      throw new Error(`Failed to load wallet history: ${error}`)
    }
  }

  const analyzeWallet = async (walletId: string): Promise<any> => {
    try {
      const response = await apiCall(`/${walletId}/analyze`, {
        method: 'POST',
      })
      return response.analysis
    } catch (error) {
      throw new Error(`Wallet analysis failed: ${error}`)
    }
  }

  // Load wallets on mount
  useEffect(() => {
    loadWallets()
    detectHardwareWallets()
  }, [])

  // Persist wallets to localStorage
  useEffect(() => {
    if (state.wallets.length > 0) {
      localStorage.setItem('forensics_wallets', JSON.stringify(state.wallets))
    }
  }, [state.wallets])

  const value: WalletContextType = {
    state,
    createWallet,
    loadWallets,
    setActiveWallet,
    refreshWalletBalance,
    signTransaction,
    broadcastTransaction,
    sendTransaction,
    detectHardwareWallets,
    signWithHardwareWallet,
    getWalletHistory,
    analyzeWallet,
  }

  return (
    <WalletContext.Provider value={value}>
      {children}
    </WalletContext.Provider>
  )
}
