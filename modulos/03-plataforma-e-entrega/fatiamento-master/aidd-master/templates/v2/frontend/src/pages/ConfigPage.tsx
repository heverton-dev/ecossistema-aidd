import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Settings, ShieldCheck, Database } from 'lucide-react'

export default function ConfigPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Configurações do Ambiente</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold">Persistência & Armazenamento</CardTitle>
            <Database className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Modo SQLite WAL com garantia ACID local e isolamento por fatia.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold">Segurança & Governança</CardTitle>
            <ShieldCheck className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Blindagem SHA-256 ativa, zero stubs e validação contínua de contratos.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
