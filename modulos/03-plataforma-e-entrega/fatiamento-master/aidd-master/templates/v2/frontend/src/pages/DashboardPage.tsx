import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Layers,
  Activity,
  CheckCircle2,
  Server,
  Zap,
  Globe,
  Loader2,
} from 'lucide-react'

interface KPIs {
  total_modulos?: number
  total_registros?: number
  taxa_sucesso?: string
  requisicoes_hoje?: number
  latencia_ms?: number
  webhooks_disparados?: number
}

const fallbackKPIs = [
  { title: 'Fatias VSA Ativas', value: '1', icon: Layers, color: 'text-blue-400' },
  { title: 'Registros Totais', value: '0', icon: Server, color: 'text-emerald-400' },
  { title: 'Taxa de Sucesso', value: '100%', icon: CheckCircle2, color: 'text-amber-400' },
  { title: 'Requisições Hoje', value: '0', icon: Activity, color: 'text-purple-400' },
  { title: 'Latência Média', value: '4ms', icon: Zap, color: 'text-rose-400' },
  { title: 'Webhooks Ativos', value: '0', icon: Globe, color: 'text-cyan-400' },
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
        { title: 'Fatias VSA Ativas', value: data.total_modulos ?? 1, icon: Layers, color: 'text-blue-400' },
        { title: 'Registros Totais', value: data.total_registros ?? 0, icon: Server, color: 'text-emerald-400' },
        { title: 'Taxa de Sucesso', value: data.taxa_sucesso ?? '100%', icon: CheckCircle2, color: 'text-amber-400' },
        { title: 'Requisições Hoje', value: data.requisicoes_hoje ?? 0, icon: Activity, color: 'text-purple-400' },
        { title: 'Latência Média', value: `${data.latencia_ms ?? 4}ms`, icon: Zap, color: 'text-rose-400' },
        { title: 'Webhooks Ativos', value: data.webhooks_disparados ?? 0, icon: Globe, color: 'text-cyan-400' },
      ]
    : fallbackKPIs

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard do Sistema</h1>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-amber-800 bg-amber-950/30 p-4 text-amber-300 text-sm mb-6">
          Exibindo métricas locais da aplicação.
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
