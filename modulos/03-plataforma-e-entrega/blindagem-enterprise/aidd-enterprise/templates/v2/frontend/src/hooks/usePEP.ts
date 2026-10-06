import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Prontuario {
  id: number
  paciente_id: number
  paciente_nome: string
  diagnostico: string
  observacoes: string
  created_at: string
}

export interface Prescricao {
  id: number
  prontuario_id: number
  medicamento: string
  dosagem: string
  frequencia: string
  duracao: string
  created_at: string
}

export function usePEP() {
  const queryClient = useQueryClient()

  const prontuarios = useQuery({
    queryKey: ['pep', 'prontuarios'],
    queryFn: async () => {
      const { data } = await api.get<Prontuario[]>('/api/pep/prontuarios')
      return data
    },
  })

  const prescricoes = useQuery({
    queryKey: ['pep', 'prescricoes'],
    queryFn: async () => {
      const { data } = await api.get<Prescricao[]>('/api/pep/prescricoes')
      return data
    },
  })

  const createProntuario = useMutation({
    mutationFn: async (novo: Partial<Prontuario>) => {
      const { data } = await api.post('/api/pep/prontuarios', novo)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pep', 'prontuarios'] })
    },
  })

  const createPrescricao = useMutation({
    mutationFn: async (novo: Partial<Prescricao>) => {
      const { data } = await api.post('/api/pep/prescricoes', novo)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pep', 'prescricoes'] })
    },
  })

  return { prontuarios, prescricoes, createProntuario, createPrescricao }
}
