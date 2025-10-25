import { useMemo } from 'react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface MetricSparklineProps {
  value: number
  prevValue?: number
  gradient: string
  history?: number[]
}

export default function MetricSparkline({ value, prevValue, gradient, history }: MetricSparklineProps) {
  // Generate sparkline data
  const data = useMemo(() => {
    if (history && history.length > 0) {
      return history.map((val, idx) => ({ value: val, index: idx }))
    }
    
    // Generate synthetic data based on current and previous values
    const points = 12
    if (prevValue !== undefined && prevValue > 0) {
      const diff = value - prevValue
      const step = diff / points
      return Array.from({ length: points }, (_, i) => ({
        value: prevValue + (step * i) + (Math.random() * step * 0.3),
        index: i
      }))
    }
    
    // Random walk if no previous value
    const baseValue = value
    const volatility = baseValue * 0.15
    let current = baseValue
    
    return Array.from({ length: points }, (_, i) => {
      current += (Math.random() - 0.5) * volatility
      current = Math.max(0, current) // Prevent negative
      return { value: current, index: i }
    })
  }, [value, prevValue, history])

  // Get gradient color
  const gradientClass = gradient.replace('from-', '').replace('to-', '').split(' ')
  const startColor = gradientClass[0]
  const endColor = gradientClass[1] || startColor

  const getColor = (colorName: string) => {
    const colors: Record<string, string> = {
      'primary-500': '#6366f1',
      'primary-700': '#4338ca',
      'green-500': '#22c55e',
      'emerald-700': '#047857',
      'red-500': '#ef4444',
      'orange-700': '#c2410c',
      'orange-500': '#f97316',
      'amber-700': '#b45309',
      'purple-500': '#a855f7',
      'violet-700': '#6d28d9',
      'indigo-500': '#6366f1',
      'blue-700': '#1d4ed8',
    }
    return colors[colorName] || '#6366f1'
  }

  return (
    <ResponsiveContainer width="100%" height={32}>
      <LineChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
        <defs>
          <linearGradient id={`gradient-${startColor}`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={getColor(startColor)} stopOpacity={0.8} />
            <stop offset="100%" stopColor={getColor(endColor)} stopOpacity={0.8} />
          </linearGradient>
        </defs>
        <Line
          type="monotone"
          dataKey="value"
          stroke={`url(#gradient-${startColor})`}
          strokeWidth={2}
          dot={false}
          isAnimationActive={true}
          animationDuration={800}
          animationEasing="ease-in-out"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
