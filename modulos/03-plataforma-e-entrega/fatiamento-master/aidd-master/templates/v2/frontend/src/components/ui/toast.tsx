import React, { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id: string
  title?: string
  message: string
  type: ToastType
  duration?: number
}

interface ToastContextType {
  toast: {
    success: (message: string, title?: string) => void
    error: (message: string, title?: string) => void
    warning: (message: string, title?: string) => void
    info: (message: string, title?: string) => void
  }
}

const ToastContext = createContext<ToastContextType | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback((message: string, type: ToastType, title?: string, duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: ToastItem = { id, message, type, title, duration }
    setToasts((prev) => [...prev, newToast])

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
  }, [removeToast])

  const toast = React.useMemo(() => ({
    success: (message: string, title?: string) => addToast(message, 'success', title),
    error: (message: string, title?: string) => addToast(message, 'error', title),
    warning: (message: string, title?: string) => addToast(message, 'warning', title),
    info: (message: string, title?: string) => addToast(message, 'info', title),
  }), [addToast])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Toast Viewport (Canto superior direito) */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => {
          const config = {
            success: {
              border: 'border-emerald-200',
              bg: 'bg-white',
              icon: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />,
              titleColor: 'text-emerald-950',
            },
            error: {
              border: 'border-rose-200',
              bg: 'bg-white',
              icon: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />,
              titleColor: 'text-rose-950',
            },
            warning: {
              border: 'border-amber-200',
              bg: 'bg-white',
              icon: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
              titleColor: 'text-amber-950',
            },
            info: {
              border: 'border-sky-200',
              bg: 'bg-white',
              icon: <Info className="w-5 h-5 text-sky-600 shrink-0" />,
              titleColor: 'text-sky-950',
            },
          }[t.type]

          return (
            <div
              key={t.id}
              className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border shadow-lg ${config.border} ${config.bg} animate-in slide-in-from-top-2 fade-in duration-200`}
            >
              {config.icon}
              <div className="flex-1 min-w-0">
                {t.title && <h4 className={`text-sm font-bold ${config.titleColor}`}>{t.title}</h4>}
                <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{t.message}</p>
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-slate-400 hover:text-slate-700 p-0.5 rounded transition cursor-pointer"
                aria-label="Fechar notificação"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast deve ser utilizado dentro de um ToastProvider')
  }
  return context.toast
}
