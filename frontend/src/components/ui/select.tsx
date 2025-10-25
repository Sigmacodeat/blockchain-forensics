import React, { createContext, useContext, useMemo, useRef, useState, useId, useEffect } from 'react'

// Minimalistischer Select, API-kompatibel zur Nutzung im Code
// Usage: <Select value={...} onValueChange={...}><SelectTrigger>...<SelectValue /></SelectTrigger><SelectContent><SelectItem value="x">X</SelectItem></SelectContent></Select>

type SelectContextType = {
  value?: string
  setValue?: (v: string) => void
  open?: boolean
  setOpen?: (o: boolean) => void
  contentId?: string
  containerRef?: React.RefObject<HTMLDivElement>
  itemsRef?: React.MutableRefObject<HTMLDivElement[]>
  disabled?: boolean
}

const SelectContext = createContext<SelectContextType>({})

export type SelectRootProps = {
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
  disabled?: boolean
  children: React.ReactNode
}

export const Select: React.FC<SelectRootProps> = ({ value, defaultValue, onValueChange, disabled, children }) => {
  const [internal, setInternal] = useState<string | undefined>(defaultValue)
  const [open, setOpen] = useState(false)
  const contentId = useId()
  const containerRef = useRef<HTMLDivElement>(null)
  const itemsRef = useRef<HTMLDivElement[]>([])
  const current = value !== undefined ? value : internal
  const setValue = (v: string) => {
    if (onValueChange) onValueChange(v)
    if (value === undefined) setInternal(v)
  }
  useEffect(() => {
    function onDocMouseDown(e: MouseEvent) {
      if (!open) return
      const el = containerRef.current
      if (el && !el.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    function onDocKeyDown(e: KeyboardEvent) {
      if (!open) return
      if (e.key === 'Escape') {
        e.stopPropagation()
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDocMouseDown)
    document.addEventListener('keydown', onDocKeyDown)
    if (open && itemsRef.current.length > 0) {
      // Focus first item when opening
      setTimeout(() => itemsRef.current[0]?.focus(), 0)
    }
    return () => {
      document.removeEventListener('mousedown', onDocMouseDown)
      document.removeEventListener('keydown', onDocKeyDown)
    }
  }, [open])
  const ctx = useMemo(() => ({ value: current, setValue, open, setOpen, contentId, containerRef, itemsRef, disabled }), [current, open, disabled])
  return <SelectContext.Provider value={ctx}><div ref={containerRef}>{children}</div></SelectContext.Provider>
}

export const SelectTrigger: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ className, children, disabled, onClick, ...props }) => {
  const { open, setOpen, contentId, disabled: rootDisabled } = useContext(SelectContext)
  const isDisabled = disabled ?? rootDisabled
  const base = "flex h-10 w-full items-center justify-between rounded-md border px-3 py-2 text-sm";
  const disabledCls = isDisabled ? "opacity-50 cursor-not-allowed" : "";
  const cls = [base, disabledCls, className].filter(Boolean).join(' ');
  const handleClick: React.MouseEventHandler<HTMLButtonElement> = (e) => {
    if (isDisabled) { e.preventDefault(); e.stopPropagation(); return; }
    setOpen && setOpen(!open)
    onClick?.(e);
  };
  return (
    <button
      type="button"
      className={cls}
      aria-haspopup="listbox"
      aria-controls={contentId}
      aria-expanded={open || false}
      aria-disabled={isDisabled || undefined}
      tabIndex={isDisabled ? -1 : props.tabIndex}
      onClick={handleClick}
      disabled={isDisabled}
      {...props}
    >
      {children}
    </button>
  )
}

export const SelectValue: React.FC<{ placeholder?: string; className?: string }> = ({ placeholder = '', className }) => {
  const { value } = useContext(SelectContext)
  return <span className={["truncate text-sm", className].filter(Boolean).join(' ')}>{value ?? placeholder}</span>
}

export const SelectContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => {
  const { open, contentId } = useContext(SelectContext)
  if (!open) return null
  return (
    <div id={contentId} role="listbox" className={["mt-2 w-full rounded-md border bg-popover p-1 text-popover-foreground shadow max-h-60 overflow-auto", className].filter(Boolean).join(' ')} {...props}>
      {children}
    </div>
  )
}

export const SelectItem: React.FC<{ value: string } & React.HTMLAttributes<HTMLDivElement>> = ({ value, className, children, ...props }) => {
  const { value: selected, setValue, setOpen, itemsRef } = useContext(SelectContext)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = ref.current
    if (!itemsRef || !el) return
    const list = itemsRef.current
    if (!list.includes(el)) list.push(el)
    return () => {
      const idx = list.indexOf(el)
      if (idx >= 0) list.splice(idx, 1)
    }
  }, [itemsRef])
  return (
    <div
      role="option"
      aria-selected={selected === value}
      tabIndex={0}
      ref={ref}
      onClick={() => { setValue && setValue(value); setOpen && setOpen(false) }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          setValue && setValue(value)
          setOpen && setOpen(false)
          return
        }
        const list = itemsRef?.current || []
        const idx = ref.current ? list.indexOf(ref.current) : -1
        if (e.key === 'ArrowDown') {
          e.preventDefault()
          const next = idx >= 0 ? list[Math.min(idx + 1, list.length - 1)] : list[0]
          next?.focus()
        } else if (e.key === 'ArrowUp') {
          e.preventDefault()
          const prev = idx >= 0 ? list[Math.max(idx - 1, 0)] : list[0]
          prev?.focus()
        } else if (e.key === 'Home') {
          e.preventDefault()
          list[0]?.focus()
        } else if (e.key === 'End') {
          e.preventDefault()
          list[list.length - 1]?.focus()
        }
      }}
      className={["cursor-pointer select-none rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground", className]
        .filter(Boolean)
        .join(' ')}
      {...props}
      >
      {children}
    </div>
  )
}

export default Select
