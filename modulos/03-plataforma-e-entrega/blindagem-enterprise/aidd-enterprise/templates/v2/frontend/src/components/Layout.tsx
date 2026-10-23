import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Stethoscope,
  FileText,
  Scissors,
  Pill,
  Receipt,
  LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/triagem', label: 'Triagem', icon: Stethoscope },
  { to: '/pep', label: 'PEP', icon: FileText },
  { to: '/cirurgico', label: 'Cirúrgico', icon: Scissors },
  { to: '/farmacia', label: 'Farmácia', icon: Pill },
  { to: '/faturamento', label: 'Faturamento', icon: Receipt },
]

export default function Layout() {
  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-slate-200 bg-white flex flex-col shadow-xs">
        <div className="px-5 py-5 border-b border-slate-200">
          <h1 className="text-base font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-600"></span>
            AIDD Enterprise
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">Gestão Corporativa</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-slate-800 hover:text-foreground',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-slate-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-slate-800 hover:text-foreground w-full transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
