import React from 'react'

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>

const base = 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => {
  const classes = [base, className].filter(Boolean).join(' ')
  return <input ref={ref} className={classes} {...props} />
})
Input.displayName = 'Input'

export default Input
