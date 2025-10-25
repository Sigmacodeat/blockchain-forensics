import React, { useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  Legend,
  AreaChart,
  Area,
} from 'recharts'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface RiskPoint { date: string; risk_max: number; risk_avg: number }
interface ExposurePoint { date: string; direct_mixer: number; direct_sanctions: number; indirect_scam: number; indirect_darkweb: number }
interface HistoryResponse {
  success: boolean
  range: string
  risk_series: RiskPoint[]
  exposure_series: ExposurePoint[]
}

interface Props {
  address: string
}

const UniversalScreeningHistoryCharts: React.FC<Props> = ({ address }) => {
  const [range, setRange] = useState<'7d' | '30d' | '90d'>('30d')
  const [data, setData] = useState<HistoryResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      if (!address) return
      setLoading(true)
      try {
        const resp = await axios.get(`${API_BASE_URL}/api/v1/kyt/history`, { params: { address, range } })
        setData(resp.data)
      } catch (e) {
        // swallow
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [address, range])

  const riskSeries = useMemo(() => data?.risk_series || [], [data])
  const exposureSeries = useMemo(() => data?.exposure_series || [], [data])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">History</h3>
        <Select value={range} onValueChange={(v) => setRange(v as any)}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="30d" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">7d</SelectItem>
            <SelectItem value="30d">30d</SelectItem>
            <SelectItem value="90d">90d</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Risk Trends</CardTitle>
        </CardHeader>
        <CardContent style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={riskSeries}>
              <XAxis dataKey="date" hide={riskSeries.length > 60} />
              <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round((v as number) * 100)}%`} />
              <RechartsTooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
              <Legend />
              <Line type="monotone" dataKey="risk_max" stroke="#ef4444" strokeWidth={2} dot={false} name="Max" />
              <Line type="monotone" dataKey="risk_avg" stroke="#3b82f6" strokeWidth={2} dot={false} name="Avg" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Exposure Over Time</CardTitle>
        </CardHeader>
        <CardContent style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={exposureSeries}>
              <XAxis dataKey="date" hide={exposureSeries.length > 60} />
              <YAxis domain={[0, 'auto']} tickFormatter={(v) => `${Math.round((v as number) * 100)}%`} />
              <RechartsTooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
              <Legend />
              <Area type="monotone" dataKey="direct_mixer" stackId="1" stroke="#f59e0b" fill="#f59e0b33" name="Direct Mixer" />
              <Area type="monotone" dataKey="direct_sanctions" stackId="1" stroke="#ef4444" fill="#ef444433" name="Direct Sanctions" />
              <Area type="monotone" dataKey="indirect_scam" stackId="1" stroke="#eab308" fill="#eab30833" name="Indirect Scam" />
              <Area type="monotone" dataKey="indirect_darkweb" stackId="1" stroke="#8b5cf6" fill="#8b5cf633" name="Indirect Darkweb" />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default UniversalScreeningHistoryCharts
