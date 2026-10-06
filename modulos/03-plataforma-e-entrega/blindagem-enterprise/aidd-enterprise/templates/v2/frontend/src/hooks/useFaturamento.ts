import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Guia {
  id: number
  paciente_nome: string
  convenio: string
  numero_guia: string
  valor_total: number
  status: string
  data_emissao: string
  created_at: string
}

export function useFaturamento() {
  const queryClient = useQueryClient()

  const guias = useQuery({
    queryKey: ['faturamento', 'guias'],
    queryFn: async () => {
      const { data } = await api.get<Guia[]>('/api/faturamento/guias')
      return data
    },
  })

  const createGuia = useMutation({
    mutationFn: async (novo: Partial<Guia>) => {
      const { data } = await api.post('/api/faturamento/nova-guia', novo)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['faturamento', 'guias'] })
    },
  })

  return { guias, createGuia }
}
