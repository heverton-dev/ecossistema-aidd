import { useState } from 'react'
import { useTriagem, type Paciente } from '@/hooks/useTriagem'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Plus, Loader2 } from 'lucide-react'

const emptyForm = { nome: '', cpf: '', data_nascimento: '', sexo: '', queixa: '', status: 'aguardando' }

export default function TriagemPage() {
  const { pacientes, createPaciente } = useTriagem()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createPaciente.mutate(form, {
      onSuccess: () => {
        setOpen(false)
        setForm(emptyForm)
      },
    })
  }

  const statusBadge = (s: string) => {
    const map: Record<string, 'success' | 'warning' | 'secondary'> = {
      aguardando: 'warning',
      atendido: 'success',
      triagem: 'secondary',
    }
    return map[s] ?? 'secondary'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Triagem</h1>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Paciente
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pacientes</CardTitle>
        </CardHeader>
        <CardContent>
          {pacientes.isLoading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : pacientes.error ? (
            <p className="text-sm text-destructive py-4">Erro ao carregar dados.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>CPF</TableHead>
                  <TableHead>Nascimento</TableHead>
                  <TableHead>Queixa</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pacientes.data?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                      Nenhum paciente encontrado.
                    </TableCell>
                  </TableRow>
                ) : (
                  pacientes.data?.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-medium">{p.nome}</TableCell>
                      <TableCell>{p.cpf}</TableCell>
                      <TableCell>{p.data_nascimento}</TableCell>
                      <TableCell>{p.queixa}</TableCell>
                      <TableCell>
                        <Badge variant={statusBadge(p.status)}>{p.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Novo Paciente</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Nome</Label>
              <Input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>CPF</Label>
                <Input value={form.cpf} onChange={(e) => setForm({ ...form, cpf: e.target.value })} />
              </div>
              <div>
                <Label>Data de Nascimento</Label>
                <Input type="date" value={form.data_nascimento} onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })} />
              </div>
            </div>
            <div>
              <Label>Sexo</Label>
              <Input value={form.sexo} onChange={(e) => setForm({ ...form, sexo: e.target.value })} placeholder="M / F" />
            </div>
            <div>
              <Label>Queixa</Label>
              <Input value={form.queixa} onChange={(e) => setForm({ ...form, queixa: e.target.value })} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createPaciente.isPending}>
                {createPaciente.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
