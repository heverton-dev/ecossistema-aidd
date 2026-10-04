# Comparação E2E — `ciclo-01` × `ciclo-24`

> Gerado por `scripts/e2e_foto.py comparar` em 2026-10-04 11:42:49.

## Fluxos e métricas

| Escopo | Métrica | Base | Novo | Piorou | Obs |
|---|---|---|---|---|---|
| fluxo-01-pure | exit_code | 1 | 1 | não |  |
| fluxo-01-pure | quebrou_em | builder | builder | não |  |
| fluxo-01-pure | quarteto | 0/4 rotas | 0/4 rotas | não |  |
| fluxo-01-pure | vazamentos | 2 | 1 | não | pre_commit_output.txt |
| fluxo-01-pure | tokens | não mensurável: nenhuma chamada LLM concluída (protocolo delegado sem resposta / sem chave headless) | não mensurável: nenhuma chamada LLM concluída (protocolo delegado sem resposta / sem chave headless) | n/a | não mensurável |
| fluxo-02-open | exit_code | 1 | 1 | não |  |
| fluxo-02-open | quebrou_em | builder | master | não |  |
| fluxo-02-open | quarteto | 0/4 rotas | 0/4 rotas | não |  |
| fluxo-02-open | vazamentos | 0 | 0 | não |  |
| fluxo-02-open | tokens | não mensurável: nenhuma chamada LLM concluída (protocolo delegado sem resposta / sem chave headless) | não mensurável: nenhuma chamada LLM concluída (protocolo delegado sem resposta / sem chave headless) | n/a | não mensurável |
| fluxo-03-freedom | exit_code | 1 | 1 | não |  |
| fluxo-03-freedom | quebrou_em | builder | master | não |  |
| fluxo-03-freedom | quarteto | 0/4 rotas | 0/4 rotas | não |  |
| fluxo-03-freedom | vazamentos | 2 | 0 | não |  |
| fluxo-03-freedom | tokens | não mensurável: nenhuma chamada LLM concluída (protocolo delegado sem resposta / sem chave headless) | não mensurável: nenhuma chamada LLM concluída (protocolo delegado sem resposta / sem chave headless) | n/a | não mensurável |
| ciclo | duplicatas | 249 | — | n/a | métrica ausente em um dos ciclos |
| ciclo | tempo_gate_s | 711 | — | n/a | métrica ausente em um dos ciclos |
| ciclo | tokens | — | — | n/a | métrica ausente em um dos ciclos |
| ciclo | orfaos_inventario | — | — | n/a | métrica ausente em um dos ciclos |

## Veredito

- ✅ nenhuma métrica piorou vs a base
- Exit 0
