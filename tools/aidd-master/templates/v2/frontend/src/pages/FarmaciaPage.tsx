import { useState } from 'react'
import { useFarmacia } from '@/hooks/useFarmacia'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Plus, Loader2 } from 'lucide-react'

const emptyForm = { nome: '', principio_ativo: '', dosagem: '', forma_farmaceutica: '', estoque_atual: 0, estoque_minimo: 0, laboratorio: '' }

export default function FarmaciaPage() {
  const { estoque, createMedicamento } = useFarmacia()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMedicamento.mutate(form, {
      onSuccess: () => { setOpen(false); setForm(emptyForm) },
    })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Farmácia</h1>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> Novo Medicamento
        </Button>
      </div>

      <Card>
        <CardHeader><CardTitle>Estoque de Medicamentos</CardTitle></CardHeader>
        <CardContent>
          {estoque.isLoading ? (
            <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Princípio Ativo</TableHead>
                  <TableHead>Dosagem</TableHead>
                  <TableHead>Forma</TableHead>
                  <TableHead>Estoque</TableHead>
                  <TableHead>Mínimo</TableHead>
                  <TableHead>Laboratório</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {estoque.data?.length === 0 ? (
                  <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">Nenhum medicamento.</TableCell></TableRow>
                ) : estoque.data?.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="font-medium">{m.nome}</TableCell>
                    <TableCell>{m.principio_ativo}</TableCell>
                    <TableCell>{m.dosagem}</TableCell>
                    <TableCell>{m.forma_farmaceutica}</TableCell>
                    <TableCell>
                      <Badge variant={m.estoque_atual <= m.estoque_minimo ? 'destructive' : 'success'}>
                        {m.estoque_atual}
                      </Badge>
                    </TableCell>
                    <TableCell>{m.estoque_minimo}</TableCell>
                    <TableCell>{m.laboratorio}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Novo Medicamento</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><Label>Nome</Label><Input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required /></div>
            <div><Label>Princípio Ativo</Label><Input value={form.principio_ativo} onChange={(e) => setForm({ ...form, principio_ativo: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Dosagem</Label><Input value={form.dosagem} onChange={(e) => setForm({ ...form, dosagem: e.target.value })} /></div>
              <div><Label>Forma Farmacêutica</Label><Input value={form.forma_farmaceutica} onChange={(e) => setForm({ ...form, forma_farmaceutica: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Estoque Atual</Label><Input type="number" value={form.estoque_atual} onChange={(e) => setForm({ ...form, estoque_atual: Number(e.target.value) })} /></div>
              <div><Label>Estoque Mínimo</Label><Input type="number" value={form.estoque_minimo} onChange={(e) => setForm({ ...form, estoque_minimo: Number(e.target.value) })} /></div>
            </div>
            <div><Label>Laboratório</Label><Input value={form.laboratorio} onChange={(e) => setForm({ ...form, laboratorio: e.target.value })} /></div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={createMedicamento.isPending}>
                {createMedicamento.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
