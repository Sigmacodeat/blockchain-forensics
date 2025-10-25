import React, { createContext, useContext, useMemo, useState } from 'react'

// Minimal Tabs-Implementierung kompatibel zur verwendeten API
// <Tabs defaultValue="swap"><TabsList><TabsTrigger value="swap" /></TabsList><TabsContent value="swap"/></Tabs>

type TabsCtx = {
  value: string
  setValue: (v: string) => void
}

const TabsContext = createContext<TabsCtx | null>(null)

export type TabsProps = {
  value?: string
  defaultValue?: string
  onValueChange?: (v: string) => void
  className?: string
  children: React.ReactNode
}

export const Tabs: React.FC<TabsProps> = ({ value, defaultValue, onValueChange, className, children }) => {
  const [internal, setInternal] = useState<string>(defaultValue ?? '')
  const current = value ?? internal
  const setValue = (v: string) => {
    onValueChange?.(v)
    if (value === undefined) setInternal(v)
  }
  const ctx = useMemo(() => ({ value: current, setValue }), [current])
  return (
    <TabsContext.Provider value={ctx}>
      <div className={[className].filter(Boolean).join(' ')}>{children}</div>
    </TabsContext.Provider>
  )
}

export const TabsList: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={["inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground", className].filter(Boolean).join(' ')} {...props} />
)

export const TabsTrigger: React.FC<{ value: string } & React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ value, className, ...props }) => {
  const ctx = useContext(TabsContext)
  if (!ctx) return null
  const selected = ctx.value === value
  const base = 'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'
  const styles = selected ? 'bg-background text-foreground shadow' : 'text-muted-foreground hover:text-foreground'
  return (
    <button
      type="button"
      onClick={() => ctx.setValue(value)}
      className={[base, styles, className].filter(Boolean).join(' ')}
      {...props}
    />
  )
}

export const TabsContent: React.FC<{ value: string } & React.HTMLAttributes<HTMLDivElement>> = ({ value, className, children, ...props }) => {
  const ctx = useContext(TabsContext)
  if (!ctx) return null
  if (ctx.value !== value) return null
  return (
    <div className={["ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2", className].filter(Boolean).join(' ')} {...props}>
      {children}
    </div>
  )
}

export default Tabs
