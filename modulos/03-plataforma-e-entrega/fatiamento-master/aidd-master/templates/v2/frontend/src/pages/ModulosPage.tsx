import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Layers, CheckCircle2 } from 'lucide-react'

export default function ModulosPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Módulos & Fatias Verticais (VSA)</h1>
        <p className="text-sm text-slate-500 mt-1">
          Arquitetura desacoplada onde cada domínio possui seus próprios contratos de API, models, regras de negócio e persistência isolada.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-base font-bold text-slate-900">Módulo Items</CardTitle>
              <CardDescription className="text-xs text-slate-500">src/modules/items</CardDescription>
            </div>
            <div className="w-9 h-9 rounded-lg bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-700">
              <Layers className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-slate-600">
              Gestão de entidades de dados com suporte a CRUD completo, isolamento de inquilinos (RLS) e eventos de domínio.
            </p>
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="inline-flex items-center gap-1.5 font-medium text-emerald-700">
                <CheckCircle2 className="h-3.5 w-3.5" /> Ativo & Conectado
              </span>
              <a href="/tarefas" className="font-semibold text-teal-700 hover:text-teal-800">
                Acessar Telas →
              </a>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-base font-bold text-slate-900">Módulo de Domínio Específico</CardTitle>
              <CardDescription className="text-xs text-slate-500">src/modules/mini_app_pure</CardDescription>
            </div>
            <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-700">
              <Layers className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-slate-600">
              Fatia vertical gerada automaticamente pelo motor especialista conforme a especificação de negócio formal.
            </p>
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="inline-flex items-center gap-1.5 font-medium text-emerald-700">
                <CheckCircle2 className="h-3.5 w-3.5" /> Contrato C4 Validado
              </span>
              <a href="http://localhost:3000/docs" target="_blank" rel="noreferrer" className="font-semibold text-teal-700 hover:text-teal-800">
                Swagger API →
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
