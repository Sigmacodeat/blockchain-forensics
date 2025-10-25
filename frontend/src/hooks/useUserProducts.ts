import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface UserProduct {
  product: 'chatbot' | 'firewall' | 'inspector' | 'commander'
  tier: number
  source: string
  status: string
  features: Record<string, any>
  limits: Record<string, any>
  activated_at: string
  expires_at: string | null
}

export function useUserProducts() {
  return useQuery<UserProduct[]>({
    queryKey: ['user-products'],
    queryFn: async () => {
      const token = localStorage.getItem('token')
      if (!token) {
        return []
      }
      
      const res = await axios.get(`${API_URL}/api/v1/appsumo/my-products`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return res.data
    },
    enabled: !!localStorage.getItem('token'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1
  })
}

export function useProductAccess(product: string) {
  const { data: products } = useUserProducts()
  
  const hasAccess = products?.some(
    (p) => p.product === product && p.status === 'active'
  ) || false
  
  const tier = products?.find(
    (p) => p.product === product && p.status === 'active'
  )?.tier || null
  
  return { hasAccess, tier }
}
