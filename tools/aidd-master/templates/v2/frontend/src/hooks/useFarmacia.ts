import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Medicamento {
  id: number
  nome: string
  principio_ativo: string
  dosagem: string
  forma_farmaceutica: string
  estoque_atual: number
  estoque_minimo: number
  laboratorio: string
  created_at: string
}

export function useFarmacia() {
  const queryClient = useQueryClient()

  const estoque = useQuery({
    queryKey: ['farmacia', 'estoque'],
    queryFn: async () => {
      const { data } = await api.get<Medicamento[]>('/api/farmacia/estoque')
      return data
    },
  })

  const createMedicamento = useMutation({
    mutationFn: async (novo: Partial<Medicamento>) => {
      const { data } = await api.post('/api/farmacia/medicamento', novo)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['farmacia', 'estoque'] })
    },
  })

  return { estoque, createMedicamento }
}
