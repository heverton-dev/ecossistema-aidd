import React from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import TarefasPage from './pages/TarefasPage'
import ModulosPage from './pages/ModulosPage'
import DocsPage from './pages/DocsPage'
import ConfigPage from './pages/ConfigPage'
import { ToastProvider } from './components/ui/toast'

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/tarefas" element={<TarefasPage />} />
          <Route path="/modulos" element={<ModulosPage />} />
          <Route path="/docs" element={<DocsPage />} />
          <Route path="/config" element={<ConfigPage />} />
        </Route>
      </Routes>
    </ToastProvider>
  )
}

function LoginPage() {
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [error, setError] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { default: api } = await import('./lib/api')
      const { data } = await api.post('/api/auth/login', { email, password })
      localStorage.setItem('token', data.token ?? data.access_token ?? '')
      navigate('/dashboard')
    } catch {
      setError('Credenciais inválidas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-bold text-center text-slate-900 mb-1">Acesso Corporativo</h1>
        <p className="text-xs text-center text-slate-500 mb-6">Plataforma Empresarial Segura</p>
        {error && <p className="text-sm text-red-600 bg-red-50 p-2.5 rounded-lg border border-red-200 mb-4">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email corporativo"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600"
          />
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 transition disabled:opacity-50 cursor-pointer shadow-xs"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
