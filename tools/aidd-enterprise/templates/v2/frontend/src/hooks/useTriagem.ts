import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Paciente {
  id: number
  nome: string
  cpf: string
  data_nascimento: string
  sexo: string
  queixa: string
  status: string
  created_at: string
}

export function useTriagem() {
  const queryClient = useQueryClient()

  const pacientes = useQuery({
    queryKey: ['triagem', 'pacientes'],
    queryFn: async () => {
      const { data } = await api.get<Paciente[]>('/api/triagem/pacientes')
      return data
    },
  })

  const createPaciente = useMutation({
    mutationFn: async (novo: Partial<Paciente>) => {
      const { data } = await api.post('/api/triagem/novo', novo)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triagem', 'pacientes'] })
    },
  })

  return { pacientes, createPaciente }
}
