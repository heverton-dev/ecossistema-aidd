import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Layers, CheckCircle2 } from 'lucide-react'

export default function ModulosPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Módulos e Fatias Verticais</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold">Fatia de Negócio</CardTitle>
            <Layers className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Módulo desacoplado com contratos de API, models e serviços de domínio.
            </p>
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <CheckCircle2 className="h-4 w-4" /> Ativo e integrado ao monólito modular
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
