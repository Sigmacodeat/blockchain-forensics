/**
 * Toast Notification System
 * Lightweight toast notifications without external dependencies
 */

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  type?: ToastType
  duration?: number
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
}

class ToastManager {
  private container: HTMLElement | null = null
  private toasts: Map<string, HTMLElement> = new Map()

  constructor() {
    if (typeof window !== 'undefined') {
      this.initContainer()
    }
  }

  private initContainer() {
    this.container = document.createElement('div')
    this.container.id = 'toast-container'
    this.container.className = 'fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none'
    document.body.appendChild(this.container)
  }

  private getIcon(type: ToastType): string {
    switch (type) {
      case 'success':
        return '✓'
      case 'error':
        return '✗'
      case 'warning':
        return '⚠'
      case 'info':
        return 'ℹ'
    }
  }

  private getColors(type: ToastType): { bg: string; border: string; text: string; icon: string } {
    switch (type) {
      case 'success':
        return {
          bg: 'bg-green-50',
          border: 'border-green-500',
          text: 'text-green-900',
          icon: 'text-green-600'
        }
      case 'error':
        return {
          bg: 'bg-red-50',
          border: 'border-red-500',
          text: 'text-red-900',
          icon: 'text-red-600'
        }
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-500',
          text: 'text-yellow-900',
          icon: 'text-yellow-600'
        }
      case 'info':
        return {
          bg: 'bg-primary-50',
          border: 'border-primary-500',
          text: 'text-primary-900',
          icon: 'text-primary-600'
        }
    }
  }

  show(message: string, options: ToastOptions = {}) {
    if (!this.container) return

    const {
      type = 'info',
      duration = 4000,
    } = options

    const id = `toast-${Date.now()}-${Math.random()}`
    const colors = this.getColors(type)
    const icon = this.getIcon(type)

    const toast = document.createElement('div')
    toast.id = id
    toast.className = `
      ${colors.bg} ${colors.border} ${colors.text}
      border-l-4 p-4 rounded-lg shadow-lg
      pointer-events-auto
      transform transition-all duration-300 ease-out
      translate-x-0 opacity-100
      max-w-md
    `
    toast.style.animation = 'slideInRight 0.3s ease-out'

    toast.innerHTML = `
      <div class="flex items-start gap-3">
        <span class="${colors.icon} text-xl font-bold">${icon}</span>
        <p class="flex-1 text-sm font-medium">${message}</p>
        <button class="text-gray-400 hover:text-gray-600 transition-colors" onclick="this.parentElement.parentElement.remove()">
          ✕
        </button>
      </div>
    `

    this.container.appendChild(toast)
    this.toasts.set(id, toast)

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        this.remove(id)
      }, duration)
    }

    return id
  }

  remove(id: string) {
    const toast = this.toasts.get(id)
    if (toast) {
      toast.style.animation = 'slideOutRight 0.3s ease-in'
      setTimeout(() => {
        toast.remove()
        this.toasts.delete(id)
      }, 300)
    }
  }

  success(message: string, duration?: number) {
    return this.show(message, { type: 'success', duration })
  }

  error(message: string, duration?: number) {
    return this.show(message, { type: 'error', duration })
  }

  warning(message: string, duration?: number) {
    return this.show(message, { type: 'warning', duration })
  }

  info(message: string, duration?: number) {
    return this.show(message, { type: 'info', duration })
  }

  clear() {
    this.toasts.forEach((_, id) => this.remove(id))
  }
}

// Singleton instance
export const toast = new ToastManager()

// Add animations to global styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style')
  style.textContent = `
    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    @keyframes slideOutRight {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `
  document.head.appendChild(style)
}
