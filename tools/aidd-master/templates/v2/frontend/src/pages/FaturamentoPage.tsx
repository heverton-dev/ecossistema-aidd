import { useState } from 'react'
import { useFaturamento } from '@/hooks/useFaturamento'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Plus, Loader2 } from 'lucide-react'

const emptyForm = { paciente_nome: '', convenio: '', numero_guia: '', valor_total: 0, status: 'pendente', data_emissao: '' }

export default function FaturamentoPage() {
  const { guias, createGuia } = useFaturamento()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createGuia.mutate(form, {
      onSuccess: () => { setOpen(false); setForm(emptyForm) },
    })
  }

  const statusBadge = (s: string) => {
    const map: Record<string, 'success' | 'warning' | 'secondary' | 'destructive'> = {
      pendente: 'warning',
      faturada: 'success',
      cancelada: 'destructive',
      paga: 'success',
    }
    return map[s] ?? 'secondary'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Faturamento</h1>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> Nova Guia
        </Button>
      </div>

      <Card>
        <CardHeader><CardTitle>Guias</CardTitle></CardHeader>
        <CardContent>
          {guias.isLoading ? (
            <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Paciente</TableHead>
                  <TableHead>Convênio</TableHead>
                  <TableHead>Nº Guia</TableHead>
                  <TableHead>Valor</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Emissão</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {guias.data?.length === 0 ? (
                  <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">Nenhuma guia encontrada.</TableCell></TableRow>
                ) : guias.data?.map((g) => (
                  <TableRow key={g.id}>
                    <TableCell className="font-medium">{g.paciente_nome}</TableCell>
                    <TableCell>{g.convenio}</TableCell>
                    <TableCell>{g.numero_guia}</TableCell>
                    <TableCell>R$ {g.valor_total?.toFixed(2)}</TableCell>
                    <TableCell><Badge variant={statusBadge(g.status)}>{g.status}</Badge></TableCell>
                    <TableCell>{g.data_emissao}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nova Guia</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><Label>Paciente</Label><Input value={form.paciente_nome} onChange={(e) => setForm({ ...form, paciente_nome: e.target.value })} required /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Convênio</Label><Input value={form.convenio} onChange={(e) => setForm({ ...form, convenio: e.target.value })} /></div>
              <div><Label>Nº Guia</Label><Input value={form.numero_guia} onChange={(e) => setForm({ ...form, numero_guia: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Valor Total (R$)</Label><Input type="number" step="0.01" value={form.valor_total} onChange={(e) => setForm({ ...form, valor_total: Number(e.target.value) })} /></div>
              <div><Label>Data Emissão</Label><Input type="date" value={form.data_emissao} onChange={(e) => setForm({ ...form, data_emissao: e.target.value })} /></div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={createGuia.isPending}>
                {createGuia.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
