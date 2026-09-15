import { useState } from 'react'
import { usePEP } from '@/hooks/usePEP'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Plus, Loader2 } from 'lucide-react'

const emptyPront = { paciente_nome: '', diagnostico: '', observacoes: '' }
const emptyPresc = { medicamento: '', dosagem: '', frequencia: '', duracao: '' }

export default function PEPPage() {
  const { prontuarios, prescricoes, createProntuario, createPrescricao } = usePEP()
  const [tab, setTab] = useState('prontuarios')
  const [openPront, setOpenPront] = useState(false)
  const [openPresc, setOpenPresc] = useState(false)
  const [formPront, setFormPront] = useState(emptyPront)
  const [formPresc, setFormPresc] = useState(emptyPresc)

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Prontuário Eletrônico (PEP)</h1>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="prontuarios">Prontuários</TabsTrigger>
          <TabsTrigger value="prescricoes">Prescrições</TabsTrigger>
        </TabsList>

        <TabsContent value="prontuarios">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Prontuários</CardTitle>
              <Button onClick={() => setOpenPront(true)}>
                <Plus className="h-4 w-4 mr-2" /> Novo
              </Button>
            </CardHeader>
            <CardContent>
              {prontuarios.isLoading ? (
                <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Paciente</TableHead>
                      <TableHead>Diagnóstico</TableHead>
                      <TableHead>Observações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {prontuarios.data?.length === 0 ? (
                      <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">Nenhum registro.</TableCell></TableRow>
                    ) : prontuarios.data?.map((p) => (
                      <TableRow key={p.id}>
                        <TableCell className="font-medium">{p.paciente_nome}</TableCell>
                        <TableCell>{p.diagnostico}</TableCell>
                        <TableCell>{p.observacoes}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="prescricoes">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Prescrições</CardTitle>
              <Button onClick={() => setOpenPresc(true)}>
                <Plus className="h-4 w-4 mr-2" /> Nova
              </Button>
            </CardHeader>
            <CardContent>
              {prescricoes.isLoading ? (
                <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Medicamento</TableHead>
                      <TableHead>Dosagem</TableHead>
                      <TableHead>Frequência</TableHead>
                      <TableHead>Duração</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {prescricoes.data?.length === 0 ? (
                      <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">Nenhuma prescrição.</TableCell></TableRow>
                    ) : prescricoes.data?.map((p) => (
                      <TableRow key={p.id}>
                        <TableCell className="font-medium">{p.medicamento}</TableCell>
                        <TableCell>{p.dosagem}</TableCell>
                        <TableCell>{p.frequencia}</TableCell>
                        <TableCell>{p.duracao}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialog Prontuário */}
      <Dialog open={openPront} onOpenChange={setOpenPront}>
        <DialogContent>
          <DialogHeader><DialogTitle>Novo Prontuário</DialogTitle></DialogHeader>
          <form onSubmit={(e) => { e.preventDefault(); createProntuario.mutate(formPront, { onSuccess: () => { setOpenPront(false); setFormPront(emptyPront) } }) }} className="space-y-4">
            <div><Label>Paciente</Label><Input value={formPront.paciente_nome} onChange={(e) => setFormPront({ ...formPront, paciente_nome: e.target.value })} required /></div>
            <div><Label>Diagnóstico</Label><Input value={formPront.diagnostico} onChange={(e) => setFormPront({ ...formPront, diagnostico: e.target.value })} required /></div>
            <div><Label>Observações</Label><Input value={formPront.observacoes} onChange={(e) => setFormPront({ ...formPront, observacoes: e.target.value })} /></div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpenPront(false)}>Cancelar</Button>
              <Button type="submit" disabled={createProntuario.isPending}>
                {createProntuario.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog Prescrição */}
      <Dialog open={openPresc} onOpenChange={setOpenPresc}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nova Prescrição</DialogTitle></DialogHeader>
          <form onSubmit={(e) => { e.preventDefault(); createPrescricao.mutate(formPresc, { onSuccess: () => { setOpenPresc(false); setFormPresc(emptyPresc) } }) }} className="space-y-4">
            <div><Label>Medicamento</Label><Input value={formPresc.medicamento} onChange={(e) => setFormPresc({ ...formPresc, medicamento: e.target.value })} required /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Dosagem</Label><Input value={formPresc.dosagem} onChange={(e) => setFormPresc({ ...formPresc, dosagem: e.target.value })} /></div>
              <div><Label>Frequência</Label><Input value={formPresc.frequencia} onChange={(e) => setFormPresc({ ...formPresc, frequencia: e.target.value })} /></div>
            </div>
            <div><Label>Duração</Label><Input value={formPresc.duracao} onChange={(e) => setFormPresc({ ...formPresc, duracao: e.target.value })} /></div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpenPresc(false)}>Cancelar</Button>
              <Button type="submit" disabled={createPrescricao.isPending}>
                {createPrescricao.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
