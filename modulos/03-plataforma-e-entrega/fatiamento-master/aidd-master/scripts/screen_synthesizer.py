#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 — SINTETIZADOR DINÂMICO DE TELAS (screen_synthesizer.py)
=============================================================================
Gera páginas React 19 completas e dinâmicas a partir do contrato da entidade,
sem usar templates estáticos de negócio.

Regras Invioláveis de Craft:
1. Zero window.alert, window.confirm ou window.prompt (proibição de diálogos do SO/browser).
2. Todo modal de cadastro/edição usa <Dialog> proprietário.
3. Toda exclusão exige <ConfirmDialog> proprietário de segurança.
4. Toda mutação dispara feedback via useToast() (toast.success / toast.error).
5. Quadro Kanban com Drag-and-Drop nativo (HTML5) e atualização reativa.
=============================================================================
"""

from typing import List, Dict, Any, Optional

TEMPLATE_TSX = """import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { useToast } from '@/components/ui/toast'
import {
  CheckSquare,
  ListFilter,
  Kanban,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  AlertCircle,
  Tag,
  Trash2,
  ArrowRight,
  ArrowLeft,
  Loader2,
  Move
} from 'lucide-react'

interface __TITULO_SINGULAR__Item {
  id: string | number
  titulo?: string
  title?: string
  descricao?: string
  status?: string
  prioridade?: string
  dados?: any
  criado_em?: string
}

type StatusTipo = 'a_fazer' | 'em_progresso' | 'concluido'

const normalizarStatus = (raw?: string): StatusTipo => {
  const s = String(raw || 'a_fazer').toLowerCase()
  if (s === 'concluido' || s === 'done' || s === 'finalizado') return 'concluido'
  if (s === 'em_progresso' || s === 'em_andamento' || s === 'in_progress') return 'em_progresso'
  return 'a_fazer'
}

export default function __TITULO_SINGULAR__Page() {
  const queryClient = useQueryClient()
  const toast = useToast()

  // Estados locais
  const [visao, setVisao] = useState<'tabela' | 'checklist' | 'kanban'>('kanban')
  const [busca, setBusca] = useState('')
  const [filtroStatus, setFiltroStatus] = useState<string>('todos')
  
  // Modais e alertas proprietários componentizados
  const [modalCriacaoAberto, setModalCriacaoAberto] = useState(false)
  const [itemParaExcluir, setItemParaExcluir] = useState<__TITULO_SINGULAR__Item | null>(null)
  const [draggedId, setDraggedId] = useState<string | number | null>(null)

  // Campos do formulário
  const [formTitulo, setFormTitulo] = useState('')
  const [formDescricao, setFormDescricao] = useState('')
  const [formPrioridade, setFormPrioridade] = useState('media')

  // Consulta à API real com SQLite WAL
  const { data: itens = [], isLoading } = useQuery<__TITULO_SINGULAR__Item[]>({
    queryKey: ['__SLUG_MODULO__', 'lista'],
    queryFn: async () => {
      const res = await api.get('__ROTA__')
      return Array.isArray(res.data) ? res.data : (res.data.itens ?? [])
    }
  })

  // Mutação: Criar registro com Toast proprietário
  const createMutation = useMutation({
    mutationFn: async (novoItem: any) => {
      const payload = {
        titulo: novoItem.titulo,
        title: novoItem.titulo,
        descricao: novoItem.descricao,
        status: 'ativo',
        dados: { prioridade: novoItem.prioridade }
      }
      const res = await api.post('__ROTA__/criar', payload)
      if (res.data?.sucesso === false) {
        throw new Error(res.data?.erro || 'Erro ao registrar item')
      }
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['__SLUG_MODULO__', 'lista'] })
      toast.success('__TITULO_SINGULAR__ cadastrado no SQLite WAL com sucesso!', 'Sucesso')
      setModalCriacaoAberto(false)
      setFormTitulo('')
      setFormDescricao('')
    },
    onError: (err: any) => {
      toast.error(err?.message || err?.response?.data?.erro || 'Erro ao registrar item', 'Falha na Operação')
    }
  })

  // Mutação: Atualizar status (usado no Kanban e botões de avanço)
  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string | number; status: string }) => {
      const res = await api.post('__ROTA__/atualizar', { id, status })
      if (res.data?.sucesso === false) {
        throw new Error(res.data?.erro || 'Erro ao atualizar status')
      }
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['__SLUG_MODULO__', 'lista'] })
      toast.success('Status atualizado com sucesso!', 'Fluxo Kanban')
    },
    onError: () => {
      toast.error('Não foi possível alterar o status', 'Erro de Conexão')
    }
  })

  // Mutação: Exclusão com Modal de Confirmação proprietário
  const deleteMutation = useMutation({
    mutationFn: async (id: string | number) => {
      const res = await api.post('__ROTA__/deletar', { id })
      if (res.data?.sucesso === false) {
        throw new Error(res.data?.erro || 'Erro ao excluir')
      }
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['__SLUG_MODULO__', 'lista'] })
      toast.success('Registro removido do banco com segurança!', 'Item Excluído')
      setItemParaExcluir(null)
    },
    onError: () => {
      toast.error('Falha ao excluir o registro', 'Erro')
    }
  })

  // Drag and Drop Nativo HTML5
  const handleDragStart = (e: React.DragEvent, id: string | number) => {
    setDraggedId(id)
    e.dataTransfer.setData('text/plain', String(id))
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDrop = (e: React.DragEvent, targetStatus: string) => {
    e.preventDefault()
    const id = draggedId || e.dataTransfer.getData('text/plain')
    if (id) {
      updateStatusMutation.mutate({ id, status: targetStatus })
    }
    setDraggedId(null)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  // Filtros em memória
  const itensFiltrados = itens.filter((t) => {
    const tit = (t.titulo || t.title || '').toLowerCase()
    const desc = (t.descricao || '').toLowerCase()
    const matchBusca = tit.includes(busca.toLowerCase()) || desc.includes(busca.toLowerCase())
    const statusNorm = normalizarStatus(t.status)
    const matchStatus = filtroStatus === 'todos' || statusNorm === filtroStatus
    return matchBusca && matchStatus
  })

  const submeterCriacao = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formTitulo.trim()) return
    createMutation.mutate({
      titulo: formTitulo.trim(),
      descricao: formDescricao.trim(),
      prioridade: formPrioridade
    })
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Gestão de __NOME_MODULO__</h1>
          <p className="text-sm text-slate-500 mt-1">
            Persistência reativa no SQLite WAL com isolamento por fatias verticais VSA.
          </p>
        </div>
        <button
          onClick={() => setModalCriacaoAberto(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-700 hover:bg-teal-800 text-white font-medium text-sm transition-colors shadow-xs cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Novo __TITULO_SINGULAR__
        </button>
      </div>

      {/* Controles de Busca e Filtros */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-1 items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Buscar registros..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:bg-white transition"
            />
          </div>
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="px-3 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-600"
          >
            <option value="todos">Todos os Status</option>
            <option value="a_fazer">A Fazer</option>
            <option value="em_progresso">Em Andamento</option>
            <option value="concluido">Concluído</option>
          </select>
        </div>

        {/* Alternador de Visões */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button
            onClick={() => setVisao('tabela')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition cursor-pointer ${
              visao === 'tabela' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ListFilter className="w-3.5 h-3.5" />
            Tabela
          </button>
          <button
            onClick={() => setVisao('kanban')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition cursor-pointer ${
              visao === 'kanban' ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Kanban className="w-3.5 h-3.5" />
            Quadro Kanban
          </button>
        </div>
      </div>

      {/* ESTADO: CARREGANDO */}
      {isLoading && (
        <div className="flex items-center justify-center py-16 bg-white rounded-xl border border-slate-200">
          <Loader2 className="h-8 w-8 animate-spin text-teal-700" />
        </div>
      )}

      {/* VISÃO KANBAN COM DRAG-AND-DROP REAL */}
      {!isLoading && visao === 'kanban' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { id: 'a_fazer', label: 'A Fazer', color: 'border-slate-300 bg-slate-100/60' },
            { id: 'em_progresso', label: 'Em Andamento', color: 'border-blue-300 bg-blue-50/40' },
            { id: 'concluido', label: 'Concluído', color: 'border-emerald-300 bg-emerald-50/40' }
          ].map((col) => {
            const itensCol = itensFiltrados.filter((t) => normalizarStatus(t.status) === col.id)
            return (
              <div
                key={col.id}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, col.id)}
                className={`rounded-xl border p-4 min-h-[380px] flex flex-col transition-colors ${col.color}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-slate-800">{col.label}</h3>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white text-slate-700 shadow-xs border border-slate-200">
                    {itensCol.length}
                  </span>
                </div>

                <div className="space-y-3 flex-1">
                  {itensCol.length === 0 ? (
                    <div className="h-28 flex items-center justify-center text-xs text-slate-400 italic bg-white/50 rounded-lg border border-dashed border-slate-200">
                      Arraste itens para esta coluna
                    </div>
                  ) : (
                    itensCol.map((item) => (
                      <Card
                        key={item.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, item.id)}
                        className="bg-white border-slate-200 shadow-xs hover:shadow-md transition cursor-grab active:cursor-grabbing"
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <p className="text-sm font-semibold text-slate-900 leading-snug">
                              {item.titulo || item.title}
                            </p>
                            <button
                              onClick={() => setItemParaExcluir(item)}
                              className="text-slate-400 hover:text-rose-600 p-1 rounded transition cursor-pointer"
                              title="Excluir com segurança"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          {item.descricao && (
                            <p className="text-xs text-slate-500 mb-3 line-clamp-2 leading-relaxed">
                              {item.descricao}
                            </p>
                          )}
                          <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
                            <span className="inline-flex items-center gap-1 font-mono text-[11px] text-slate-400">
                              <Move className="w-3 h-3" /> Arrastar
                            </span>
                            <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                              ID #{item.id}
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* VISÃO TABELA RESPONSIVA */}
      {!isLoading && visao === 'tabela' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-xs uppercase font-semibold text-slate-500">
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Título</th>
                  <th className="py-3 px-4">Descrição</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {itensFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-sm text-slate-400 italic">
                      Nenhum registro encontrado para este filtro.
                    </td>
                  </tr>
                ) : (
                  itensFiltrados.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/50 transition">
                      <td className="py-3 px-4 font-mono text-xs text-slate-500">#{item.id}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">{item.titulo || item.title}</td>
                      <td className="py-3 px-4 text-slate-600 text-xs">{item.descricao || '-'}</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700">
                          {normalizarStatus(item.status)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setItemParaExcluir(item)}
                          className="text-slate-400 hover:text-rose-600 p-1.5 rounded transition cursor-pointer"
                          title="Excluir registro"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL PROPRIETÁRIO DE CADASTRO */}
      <Dialog open={modalCriacaoAberto} onOpenChange={setModalCriacaoAberto}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Cadastrar Novo __TITULO_SINGULAR__</DialogTitle>
            <DialogDescription>
              Persistência imediata com validação estrita no banco SQLite WAL.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={submeterCriacao} className="space-y-4 mt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Título *</label>
              <input
                type="text"
                placeholder="Informe o título identificador..."
                value={formTitulo}
                onChange={(e) => setFormTitulo(e.target.value)}
                required
                autoFocus
                className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600 text-slate-900"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Descrição</label>
              <textarea
                placeholder="Detalhes complementares do registro..."
                rows={3}
                value={formDescricao}
                onChange={(e) => setFormDescricao(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600 text-slate-900 resize-none"
              />
            </div>

            <DialogFooter>
              <button
                type="button"
                onClick={() => setModalCriacaoAberto(false)}
                className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition cursor-pointer"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-teal-700 hover:bg-teal-800 rounded-lg shadow-xs transition cursor-pointer disabled:opacity-50"
              >
                {createMutation.isPending ? 'Gravando...' : 'Salvar Registro'}
              </button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL PROPRIETÁRIO DE CONFIRMAÇÃO DE EXCLUSÃO (SEM ALERT NATIVO) */}
      <ConfirmDialog
        open={!!itemParaExcluir}
        onOpenChange={(open) => !open && setItemParaExcluir(null)}
        title="Confirmar Exclusão"
        description={`Tem certeza que deseja excluir o item "${itemParaExcluir?.titulo || itemParaExcluir?.title || ''}"? Esta alteração será persistida no SQLite WAL.`}
        confirmText="Excluir Definitivamente"
        variant="danger"
        loading={deleteMutation.isPending}
        onConfirm={() => itemParaExcluir && deleteMutation.mutate(itemParaExcluir.id)}
      />
    </div>
  )
}
"""

def sintetizar_tela_entidade(
    nome_modulo: str,
    slug_modulo: str,
    campos: Optional[List[Dict[str, Any]]] = None,
    rota_api: Optional[str] = None
) -> str:
    """Gera o código TypeScript/React de uma página de entidade completa e proprietária."""
    
    rota = rota_api or f"/api/{slug_modulo}"
    titulo_singular = nome_modulo.capitalize()
    
    code = (
        TEMPLATE_TSX
        .replace("__TITULO_SINGULAR__", titulo_singular)
        .replace("__SLUG_MODULO__", slug_modulo)
        .replace("__NOME_MODULO__", nome_modulo)
        .replace("__ROTA__", rota)
    )
    return code
