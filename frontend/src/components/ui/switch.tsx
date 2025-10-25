import React from 'react'

export type SwitchProps = {
  id?: string
  name?: string
  checked?: boolean
  defaultChecked?: boolean
  disabled?: boolean
  onCheckedChange?: (checked: boolean) => void
  className?: string
}

export const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  (
    {
      id,
      name,
      checked,
      defaultChecked,
      disabled,
      onCheckedChange,
      className,
      ...rest
    },
    ref
  ) => {
    return (
      <label className={[
        "relative inline-flex h-6 w-11 cursor-pointer select-none items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-offset-2",
        disabled ? "opacity-50 cursor-not-allowed" : "",
        className
      ]
        .filter(Boolean)
        .join(" ")}
      >
        <input
          id={id}
          name={name}
          ref={ref}
          type="checkbox"
          role="switch"
          aria-checked={checked}
          disabled={disabled}
          checked={checked}
          defaultChecked={defaultChecked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          className="peer sr-only"
          {...rest as any}
        />
        <span className="pointer-events-none h-6 w-11 rounded-full bg-gray-300 transition-colors peer-checked:bg-primary-600" />
        <span className="pointer-events-none absolute left-0.5 top-0.5 h-5 w-5 transform rounded-full bg-white shadow transition-transform peer-checked:translate-x-5" />
      </label>
    )
  }
)

Switch.displayName = 'Switch'

export default Switch
