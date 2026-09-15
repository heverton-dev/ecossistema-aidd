import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Agendamento {
  id: number
  paciente_nome: string
  cirurgia: string
  data: string
  horario: string
  medico: string
  sala: string
  status: string
  created_at: string
}

export function useCirurgico() {
  const queryClient = useQueryClient()

  const agendamentos = useQuery({
    queryKey: ['cirurgico', 'agendamentos'],
    queryFn: async () => {
      const { data } = await api.get<Agendamento[]>('/api/cirurgico/agendamentos')
      return data
    },
  })

  const createAgendamento = useMutation({
    mutationFn: async (novo: Partial<Agendamento>) => {
      const { data } = await api.post('/api/cirurgico/novo', novo)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cirurgico', 'agendamentos'] })
    },
  })

  return { agendamentos, createAgendamento }
}
