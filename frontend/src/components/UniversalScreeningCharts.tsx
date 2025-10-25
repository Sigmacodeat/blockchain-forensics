import React, { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

interface ChainEntry {
  id: string
  risk_score: number
  is_sanctioned: boolean
}

interface UniversalScreeningChartsProps {
  entries: Array<[string, any]>
}

const COLORS = ['#22c55e', '#f97316', '#ef4444', '#3b82f6', '#a855f7']

const UniversalScreeningCharts: React.FC<UniversalScreeningChartsProps> = ({ entries }) => {
  const data = useMemo<ChainEntry[]>(() => {
    return entries.map(([id, chain]) => ({
      id,
      risk_score: Number(chain?.risk_score || 0),
      is_sanctioned: Boolean(chain?.is_sanctioned),
    }))
  }, [entries])

  const sanctionedStats = useMemo(() => {
    const sanctioned = data.filter(d => d.is_sanctioned).length
    const clean = data.length - sanctioned
    return [
      { name: 'Clean', value: clean },
      { name: 'Sanctioned', value: sanctioned },
    ]
  }, [data])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Risk by Chain</CardTitle>
        </CardHeader>
        <CardContent style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <XAxis dataKey="id" tick={{ fontSize: 12 }} hide={data.length > 12} />
              <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round((v as number) * 100)}%`} />
              <RechartsTooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
              <Bar dataKey="risk_score" radius={[4, 4, 0, 0]} fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Sanctions Split</CardTitle>
        </CardHeader>
        <CardContent style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={sanctionedStats} dataKey="value" nameKey="name" outerRadius={80} label>
                {sanctionedStats.map((_, idx) => (
                  <Cell key={`c-${idx}`} fill={idx === 1 ? '#ef4444' : '#22c55e'} />
                ))}
              </Pie>
              <RechartsTooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default UniversalScreeningCharts
