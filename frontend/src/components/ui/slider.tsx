import React from 'react'

export type SliderProps = {
  value: number[]
  onValueChange: (value: number[]) => void
  min?: number
  max?: number
  step?: number
  disabled?: boolean
  className?: string
}

export const Slider: React.FC<SliderProps> = ({
  value,
  onValueChange,
  min = 0,
  max = 100,
  step = 1,
  disabled,
  className,
}) => {
  const current = value?.[0] ?? 0

  return (
    <div className={[
      "w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-offset-2",
      className,
    ].filter(Boolean).join(" ")}> 
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={current}
        disabled={disabled}
        onChange={(e) => onValueChange([Number(e.target.value)])}
        className="w-full appearance-none h-2 rounded bg-gray-200 accent-primary-600 disabled:opacity-50"
      />
    </div>
  )
}

export default Slider
