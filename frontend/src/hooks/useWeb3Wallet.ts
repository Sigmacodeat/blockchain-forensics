/**
 * Web3 Wallet Hook for One-Click Payments
 * Supports MetaMask, TronLink, WalletConnect, and more
 */
import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { Decimal } from 'decimal.js';

interface WalletState {
  connected: boolean;
  address: string | null;
  chainId: number | null;
  provider: 'metamask' | 'tronlink' | 'walletconnect' | null;
  balance: string | null;
}

interface TransactionParams {
  to: string;
  value: string; // in Wei for ETH, Sun for TRX
  currency: 'eth' | 'trx' | 'bnb' | 'matic';
  gasLimit?: string;
}

export const useWeb3Wallet = () => {
  const [wallet, setWallet] = useState<WalletState>({
    connected: false,
    address: null,
    chainId: null,
    provider: null,
    balance: null
  });
  const [loading, setLoading] = useState(false);

  // Detect available wallets
  const detectWallets = useCallback(() => {
    const detected: string[] = [];
    
    if (typeof window.ethereum !== 'undefined') {
      detected.push('MetaMask');
    }
    
    if (typeof window.tronWeb !== 'undefined') {
      detected.push('TronLink');
    }
    
    return detected;
  }, []);

  // Connect to MetaMask
  const connectMetaMask = useCallback(async () => {
    if (typeof window.ethereum === 'undefined') {
      toast.error('MetaMask not installed! Please install MetaMask.');
      window.open('https://metamask.io/download/', '_blank');
      return false;
    }

    try {
      setLoading(true);
      
      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts'
      });
      
      // Get chain ID
      const chainId = await window.ethereum.request({
        method: 'eth_chainId'
      });
      
      // Get balance
      const balance = await window.ethereum.request({
        method: 'eth_getBalance',
        params: [accounts[0], 'latest']
      });
      
      setWallet({
        connected: true,
        address: accounts[0],
        chainId: parseInt(chainId, 16),
        provider: 'metamask',
        balance: (parseInt(balance, 16) / 1e18).toFixed(6) // Convert Wei to ETH
      });
      
      toast.success(`✅ Connected to MetaMask: ${accounts[0].slice(0, 6)}...${accounts[0].slice(-4)}`);
      return true;
    } catch (error: any) {
      console.error('MetaMask connection error:', error);
      toast.error(`❌ MetaMask error: ${error.message || 'Connection failed'}`);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Connect to TronLink
  const connectTronLink = useCallback(async () => {
    if (typeof window.tronWeb === 'undefined') {
      toast.error('TronLink not installed! Please install TronLink.');
      window.open('https://www.tronlink.org/', '_blank');
      return false;
    }

    try {
      setLoading(true);
      
      // Request account access
      const tronWeb = window.tronWeb;
      
      if (!tronWeb || !tronWeb.ready) {
        toast.error('TronLink is locked. Please unlock it first.');
        return false;
      }
      
      if (!tronWeb.defaultAddress?.base58) {
        toast.error('TronLink address not available.');
        return false;
      }
      
      const address = tronWeb.defaultAddress.base58;
      
      if (!tronWeb.trx?.getBalance) {
        toast.error('TronLink API not available.');
        return false;
      }
      
      // Get balance
      const balance = await tronWeb.trx.getBalance(address);
      
      setWallet({
        connected: true,
        address,
        chainId: null, // Tron doesn't use chainId
        provider: 'tronlink',
        balance: (balance / 1e6).toFixed(6) // Convert Sun to TRX
      });
      
      toast.success(`✅ Connected to TronLink: ${address.slice(0, 6)}...${address.slice(-4)}`);
      return true;
    } catch (error: any) {
      console.error('TronLink connection error:', error);
      toast.error(`❌ TronLink error: ${error.message || 'Connection failed'}`);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Send transaction via MetaMask
  const sendTransactionMetaMask = useCallback(async (params: TransactionParams) => {
    if (!wallet.connected || wallet.provider !== 'metamask') {
      toast.error('Please connect MetaMask first!');
      return null;
    }

    try {
      setLoading(true);
      // Network guard: ensure correct chain for currency
      const desiredChain: Record<string, string> = {
        eth: '0x1',      // Ethereum Mainnet
        bnb: '0x38',     // BSC Mainnet
        matic: '0x89'    // Polygon Mainnet
      };
      const target = desiredChain[params.currency];
      if (target && window.ethereum) {
        try {
          const current = await window.ethereum.request({ method: 'eth_chainId' });
          if (current?.toLowerCase() !== target.toLowerCase()) {
            await window.ethereum.request({
              method: 'wallet_switchEthereumChain',
              params: [{ chainId: target }]
            });
            // update local state chainId
            setWallet(prev => ({ ...prev, chainId: parseInt(target, 16) }));
            toast('🔁 Switched network for this transaction');
          }
        } catch (switchErr: any) {
          // 4902 means chain not added
          if (switchErr?.code === 4902) {
            toast.error('Network not available in MetaMask. Please add the network first.');
          } else if (switchErr?.code === 4001) {
            toast.error('Network switch rejected by user');
          } else {
            toast.error('Failed to switch network');
          }
          return null;
        }
      }
      
      if (!window.ethereum) {
        toast.error('MetaMask not available');
        return null;
      }
      
      // MetaMask expects hex string for value (in Wei) - use Decimal for precision
      let hexValue = params.value;
      try {
        if (!/^0x/i.test(hexValue)) {
          const decimalValue = new Decimal(hexValue);
          hexValue = '0x' + decimalValue.toHex();
        }
      } catch {
        // Best-effort: if conversion fails, leave as-is; MetaMask may still handle
      }

      const txHash = await window.ethereum.request({
        method: 'eth_sendTransaction',
        params: [{
          from: wallet.address,
          to: params.to,
          value: hexValue,
          gas: params.gasLimit || '0x5208', // 21000 gas for simple transfer
        }]
      });
      
      toast.success(`✅ Transaction sent! Hash: ${txHash.slice(0, 10)}...`);
      return txHash;
    } catch (error: any) {
      console.error('Transaction error:', error);
      
      if (error.code === 4001) {
        toast.error('❌ Transaction rejected by user');
      } else if (error.code === -32000) {
        toast.error('❌ Insufficient funds for gas or value');
      } else {
        toast.error(`❌ Transaction failed: ${error.message || 'Unknown error'}`);
      }
      
      return null;
    } finally {
      setLoading(false);
    }
  }, [wallet]);

  // Send transaction via TronLink
  const sendTransactionTronLink = useCallback(async (params: TransactionParams) => {
    if (!wallet.connected || wallet.provider !== 'tronlink') {
      toast.error('Please connect TronLink first!');
      return null;
    }

    try {
      setLoading(true);
      
      const tronWeb = window.tronWeb;
      
      if (!tronWeb?.transactionBuilder?.sendTrx) {
        toast.error('TronLink API not available');
        return null;
      }
      
      if (!wallet.address) {
        toast.error('Wallet address not available');
        return null;
      }
      
      // Create transaction with precise decimal handling
      const decimalValue = new Decimal(params.value);
      const tx = await tronWeb.transactionBuilder.sendTrx(
        params.to,
        decimalValue.toNumber(), // Amount in Sun (converted from Decimal)
        wallet.address
      );
      
      if (!tronWeb.trx?.sign || !tronWeb.trx?.sendRawTransaction) {
        toast.error('TronLink transaction API not available');
        return null;
      }
      
      // Sign transaction
      const signedTx = await tronWeb.trx.sign(tx);
      
      // Broadcast transaction
      const result = await tronWeb.trx.sendRawTransaction(signedTx);
      
      if (result.result) {
        const txHash = result.txid || result.transaction?.txID;
        toast.success(`✅ Transaction sent! Hash: ${txHash.slice(0, 10)}...`);
        return txHash;
      } else {
        throw new Error('Transaction failed');
      }
    } catch (error: any) {
      console.error('TronLink transaction error:', error);
      toast.error(`❌ Transaction failed: ${error.message || 'Unknown error'}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [wallet]);

  // Unified send transaction
  const sendTransaction = useCallback(async (params: TransactionParams) => {
    if (wallet.provider === 'metamask') {
      return await sendTransactionMetaMask(params);
    } else if (wallet.provider === 'tronlink') {
      return await sendTransactionTronLink(params);
    } else {
      toast.error('No wallet connected!');
      return null;
    }
  }, [wallet.provider, sendTransactionMetaMask, sendTransactionTronLink]);

  // Disconnect wallet
  const disconnect = useCallback(() => {
    setWallet({
      connected: false,
      address: null,
      chainId: null,
      provider: null,
      balance: null
    });
    toast.success('👋 Wallet disconnected');
  }, []);

  // Listen for account changes (MetaMask)
  useEffect(() => {
    if (typeof window.ethereum !== 'undefined') {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          disconnect();
        } else if (wallet.connected && wallet.provider === 'metamask') {
          setWallet(prev => ({ ...prev, address: accounts[0] }));
          toast('🔄 Account changed');
        }
      };

      const handleChainChanged = (cid: string) => {
        // update chainId without reloading page, keep UX smooth
        const parsed = parseInt(cid, 16);
        setWallet(prev => ({ ...prev, chainId: parsed }));
        toast(`🔁 Network changed (${parsed})`);
      };

      if (window.ethereum?.on && window.ethereum?.removeListener) {
        window.ethereum.on('accountsChanged', handleAccountsChanged);
        window.ethereum.on('chainChanged', handleChainChanged);

        return () => {
          if (window.ethereum?.removeListener) {
            window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
            window.ethereum.removeListener('chainChanged', handleChainChanged);
          }
        };
      }
    }
  }, [wallet.connected, wallet.provider, disconnect]);

  return {
    wallet,
    loading,
    detectWallets,
    connectMetaMask,
    connectTronLink,
    sendTransaction,
    disconnect
  };
};

export default useWeb3Wallet;
