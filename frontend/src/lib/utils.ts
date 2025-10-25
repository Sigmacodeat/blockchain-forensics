import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format Ethereum address (0x1234...5678)
 */
export function formatAddress(address: string, length = 4): string {
  if (!address) return ''
  if (address.length <= length * 2 + 2) return address
  return `${address.slice(0, length + 2)}...${address.slice(-length)}`
}

/**
 * Format large numbers (1000000 -> 1M)
 */
export function formatNumber(num: number): string {
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`
  if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`
  return num.toString()
}

/**
 * Format Wei to Ether
 */
export function formatEther(wei: string | number): string {
  const weiNum = typeof wei === 'string' ? parseFloat(wei) : wei
  const ether = weiNum / 1e18
  
  if (ether >= 1000) return formatNumber(ether) + ' ETH'
  if (ether >= 1) return ether.toFixed(4) + ' ETH'
  if (ether >= 0.001) return ether.toFixed(6) + ' ETH'
  return ether.toExponential(2) + ' ETH'
}

/**
 * Format date relative to now (2 hours ago, 3 days ago, etc.)
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date()
  const then = typeof date === 'string' ? new Date(date) : date
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000)
  
  if (seconds < 60) return 'gerade eben'
  if (seconds < 3600) return `vor ${Math.floor(seconds / 60)} Min.`
  if (seconds < 86400) return `vor ${Math.floor(seconds / 3600)} Std.`
  if (seconds < 604800) return `vor ${Math.floor(seconds / 86400)} Tagen`
  if (seconds < 2592000) return `vor ${Math.floor(seconds / 604800)} Wochen`
  
  return then.toLocaleDateString('de-DE')
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('Failed to copy:', err)
    return false
  }
}

/**
 * Get risk color based on score
 */
export function getRiskColor(score: number): string {
  if (score >= 0.9) return 'text-red-600 bg-red-50'
  if (score >= 0.6) return 'text-orange-600 bg-orange-50'
  if (score >= 0.3) return 'text-yellow-600 bg-yellow-50'
  return 'text-green-600 bg-green-50'
}

/**
 * Validate Ethereum address
 */
export function isValidAddress(address: string): boolean {
  return /^0x[a-fA-F0-9]{40}$/.test(address)
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}
