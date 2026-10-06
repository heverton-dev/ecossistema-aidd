import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import TriagemPage from './pages/TriagemPage'
import PEPPage from './pages/PEPPage'
import CirurgicoPage from './pages/CirurgicoPage'
import FarmaciaPage from './pages/FarmaciaPage'
import FaturamentoPage from './pages/FaturamentoPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/triagem" element={<TriagemPage />} />
        <Route path="/pep" element={<PEPPage />} />
        <Route path="/cirurgico" element={<CirurgicoPage />} />
        <Route path="/farmacia" element={<FarmaciaPage />} />
        <Route path="/faturamento" element={<FaturamentoPage />} />
      </Route>
    </Routes>
  )
}

function LoginPage() {
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [error, setError] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const navigate = React.useNavigate()

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
    <div className="min-h-screen flex items-center justify-center bg-[#0b0f19]">
      <div className="w-full max-w-sm rounded-lg border border-slate-800 bg-card p-8">
        <h1 className="text-2xl font-bold text-center mb-6">AIDD Enterprise</h1>
        {error && <p className="text-sm text-destructive mb-4">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
