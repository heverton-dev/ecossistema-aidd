import { useState } from 'react'
import { useCirurgico } from '@/hooks/useCirurgico'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Plus, Loader2 } from 'lucide-react'

const emptyForm = { paciente_nome: '', cirurgia: '', data: '', horario: '', medico: '', sala: '', status: 'agendada' }

export default function CirurgicoPage() {
  const { agendamentos, createAgendamento } = useCirurgico()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createAgendamento.mutate(form, {
      onSuccess: () => { setOpen(false); setForm(emptyForm) },
    })
  }

  const statusBadge = (s: string) => {
    const map: Record<string, 'success' | 'warning' | 'secondary' | 'destructive'> = {
      agendada: 'warning',
      concluida: 'success',
      cancelada: 'destructive',
      em_andamento: 'secondary',
    }
    return map[s] ?? 'secondary'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Cirúrgico</h1>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> Novo Agendamento
        </Button>
      </div>

      <Card>
        <CardHeader><CardTitle>Agendamentos</CardTitle></CardHeader>
        <CardContent>
          {agendamentos.isLoading ? (
            <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Paciente</TableHead>
                  <TableHead>Cirurgia</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead>Horário</TableHead>
                  <TableHead>Médico</TableHead>
                  <TableHead>Sala</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agendamentos.data?.length === 0 ? (
                  <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">Nenhum agendamento.</TableCell></TableRow>
                ) : agendamentos.data?.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">{a.paciente_nome}</TableCell>
                    <TableCell>{a.cirurgia}</TableCell>
                    <TableCell>{a.data}</TableCell>
                    <TableCell>{a.horario}</TableCell>
                    <TableCell>{a.medico}</TableCell>
                    <TableCell>{a.sala}</TableCell>
                    <TableCell><Badge variant={statusBadge(a.status)}>{a.status}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Novo Agendamento</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><Label>Paciente</Label><Input value={form.paciente_nome} onChange={(e) => setForm({ ...form, paciente_nome: e.target.value })} required /></div>
            <div><Label>Cirurgia</Label><Input value={form.cirurgia} onChange={(e) => setForm({ ...form, cirurgia: e.target.value })} required /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Data</Label><Input type="date" value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} required /></div>
              <div><Label>Horário</Label><Input type="time" value={form.horario} onChange={(e) => setForm({ ...form, horario: e.target.value })} required /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Médico</Label><Input value={form.medico} onChange={(e) => setForm({ ...form, medico: e.target.value })} /></div>
              <div><Label>Sala</Label><Input value={form.sala} onChange={(e) => setForm({ ...form, sala: e.target.value })} /></div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={createAgendamento.isPending}>
                {createAgendamento.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
