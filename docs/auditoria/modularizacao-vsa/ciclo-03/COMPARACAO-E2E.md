# Comparação E2E — `ciclo-01` × `ciclo-26`

> Gerado por `scripts/e2e_foto.py comparar` em 2026-10-08 19:15:15.

## Fluxos e métricas

| Escopo | Métrica | Base | Novo | Piorou | Obs |
|---|---|---|---|---|---|
| fluxo-01-pure | exit_code | 1 | 1 | não |  |
| fluxo-01-pure | quebrou_em | builder | builder | não |  |
| fluxo-01-pure | quarteto | 0/4 rotas | 0/4 rotas | não |  |
| fluxo-01-pure | vazamentos | 2 | 0 | não |  |
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

## Notas do Ticket 21 (fora da comparação automática)

- Base `ciclo-01`: foto de 01/10/2026 (HEAD `7b61b45`), antes da VSA. A pasta das fotos saiu de `Desktop/TESTES_E2E-ecossistema-aidd` para `Desktop/01_projetos_apps/testes-e2e-ecossistema-aidd` em 05/10/2026; `raiz_padrao()` passou a procurar lá também.
- Foto nova `ciclo-26`: 08/10/2026, main `10a41f82` (VSA ciclo-03, Blocos 1–7), `e2e_foto.py rodar --ciclo auto` com worktree isolada `worktrees_e2e-ciclo-26`, 93 s.
- Fluxo 01 quebra no mesmo ponto da base: motor pure, fase 2 (Analisador), protocolo delegado sem resposta e nenhum LLM headless configurado. O aviso de plugins mudou de `No module named 'core.logs'` para `No module named 'core'` (o pacote virou `core_pure` no Ticket 10); os plugins já não carregavam na base.
- `ciclo-25` (04/10, antes da VSA) chegou ao master no fluxo 01, com Quarteto 4/4, porque rodou com a ordem de etapas de `f1abff5a` (master antes do pure), desfeita em `e4f2a4f5` (04/10 21:20). Não é efeito da VSA.
- Continuação (etapas 4–6 na cópia do projeto do fluxo 01): 5 de 5 comandos com exit 0 e sem vazamento; na base, `ops plan` saía com exit 1 (`NICHO_NAO_RECONHECIDO`).
- Métricas de ciclo (`duplicatas`, `tempo_gate_s`, `tokens`, `orfaos_inventario`): o `rodar` não as mede, por isso ficam n/a, como na comparação do fronteiras-ferramentas ciclo-01. Fora da foto: o `audit` levou 711 s com 2352 testes na base e cerca de 1920 s com 3689 testes no audit de 08/10 (17:48–18:20). O tempo de gate subiu junto com o número de testes e gates.
