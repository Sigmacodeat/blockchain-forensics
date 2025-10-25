import api from '@/lib/api'

export const traceApi = {
  async startTrace(payload: {
    chain: string
    address: string
    depth: number
    threshold: number
    model: string
    include_risk?: boolean
    max_hops?: number
  }): Promise<any> {
    const res = await api.post('/api/v1/trace/start', payload)
    return res.data
  },
  async getStatus(trace_id: string): Promise<any> {
    const res = await api.get('/api/v1/trace/status', { params: { trace_id } })
    return res.data
  },
  async getResults(trace_id: string): Promise<any> {
    const res = await api.get('/api/v1/trace/results', { params: { trace_id } })
    return res.data
  }
}
