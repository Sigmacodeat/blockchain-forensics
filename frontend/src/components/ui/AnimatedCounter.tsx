/**
 * AnimatedCounter - Elegant counter animation for stats
 * Counts from 0 to target value when scrolled into view
 */

import { useEffect, useRef, useState } from 'react'
import { useInView } from 'framer-motion'

interface AnimatedCounterProps {
  value: string | number
  duration?: number
  className?: string
  suffix?: string
}

export function AnimatedCounter({ 
  value, 
  duration = 2000, 
  className = '',
  suffix = ''
}: AnimatedCounterProps) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-50px' })
  const [displayValue, setDisplayValue] = useState('0')

  useEffect(() => {
    if (!isInView) return

    const valueStr = String(value)
    
    // Parse number from value string (handles formats like "$12.6B+", "100+", "99.9%")
    const numMatch = valueStr.match(/([0-9.]+)/)
    if (!numMatch) {
      setDisplayValue(valueStr)
      return
    }

    const targetNum = parseFloat(numMatch[1])
    const prefix = valueStr.substring(0, valueStr.indexOf(numMatch[1]))
    const extractedSuffix = valueStr.replace(prefix, '').replace(numMatch[1], '')
    const finalSuffix = suffix || extractedSuffix

    let startTime: number | null = null

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)
      
      // Easing function for smooth animation (easeOutQuart)
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentNum = easeOutQuart * targetNum
      
      // Format number based on original format
      const decimals = numMatch[1].includes('.') ? 1 : 0
      const formattedNum = currentNum.toFixed(decimals)
      
      setDisplayValue(prefix + formattedNum + finalSuffix)
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        setDisplayValue(valueStr)
      }
    }

    requestAnimationFrame(animate)
  }, [isInView, value, duration, suffix])

  return (
    <div ref={ref} className={className}>
      {displayValue}
    </div>
  )
}

// Convenience component for stat displays
interface StatCounterProps {
  value: string | number
  label: string
  duration?: number
  valueClassName?: string
  labelClassName?: string
}

export function StatCounter({ 
  value, 
  label, 
  duration,
  valueClassName = 'text-4xl font-bold text-primary',
  labelClassName = 'text-sm text-muted-foreground'
}: StatCounterProps) {
  return (
    <div>
      <AnimatedCounter 
        value={value} 
        duration={duration}
        className={valueClassName}
      />
      <div className={labelClassName}>{label}</div>
    </div>
  )
}
