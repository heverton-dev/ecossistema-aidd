import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Users,
  Stethoscope,
  Scissors,
  Pill,
  Receipt,
  Activity,
  Loader2,
} from 'lucide-react'

interface KPIs {
  total_pacientes?: number
  triagem_hoje?: number
  cirurgias_agendadas?: number
  medicamentos_estoque?: number
  guas_pendentes?: number
  consultas_hoje?: number
}

const fallbackKPIs = [
  { title: 'Pacientes Cadastrados', value: '—', icon: Users, color: 'text-blue-400' },
  { title: 'Triagens Hoje', value: '—', icon: Stethoscope, color: 'text-emerald-400' },
  { title: 'Cirurgias Agendadas', value: '—', icon: Scissors, color: 'text-amber-400' },
  { title: 'Medicamentos', value: '—', icon: Pill, color: 'text-purple-400' },
  { title: 'Guias Pendentes', value: '—', icon: Receipt, color: 'text-rose-400' },
  { title: 'Consultas Hoje', value: '—', icon: Activity, color: 'text-cyan-400' },
]

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery<KPIs>({
    queryKey: ['dashboard', 'kpis'],
    queryFn: async () => {
      const { data } = await api.get('/api/dashboard/kpis')
      return data
    },
  })

  const kpis = data
    ? [
        { title: 'Pacientes Cadastrados', value: data.total_pacientes ?? 0, icon: Users, color: 'text-blue-400' },
        { title: 'Triagens Hoje', value: data.triagem_hoje ?? 0, icon: Stethoscope, color: 'text-emerald-400' },
        { title: 'Cirurgias Agendadas', value: data.cirurgias_agendadas ?? 0, icon: Scissors, color: 'text-amber-400' },
        { title: 'Medicamentos', value: data.medicamentos_estoque ?? 0, icon: Pill, color: 'text-purple-400' },
        { title: 'Guias Pendentes', value: data.guas_pendentes ?? 0, icon: Receipt, color: 'text-rose-400' },
        { title: 'Consultas Hoje', value: data.consultas_hoje ?? 0, icon: Activity, color: 'text-cyan-400' },
      ]
    : fallbackKPIs

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-amber-800 bg-amber-950/30 p-4 text-amber-300 text-sm mb-6">
          Não foi possível carregar os KPIs. Exibindo dados de exemplo.
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {kpis.map((kpi) => (
          <Card key={kpi.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {kpi.title}
              </CardTitle>
              <kpi.icon className={`h-5 w-5 ${kpi.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{kpi.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
