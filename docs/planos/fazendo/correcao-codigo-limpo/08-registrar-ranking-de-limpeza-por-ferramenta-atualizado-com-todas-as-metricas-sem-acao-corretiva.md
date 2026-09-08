# Item 8 — Registrar ranking de limpeza por ferramenta atualizado com todas as metricas (sem acao corretiva)

> **Escopo:** Entra: só registrar, num documento de referência, a régua objetiva de limpeza de código medida via grafo/grep em 2026-09-08 por ferramenta — sem nenhuma ação corretiva associada. Não entra: corrigir qualquer coisa a partir deste ranking (isso é o que os itens 1-7 já fazem, ou achados futuros).

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

---

## Contexto já investigado (medido via `.code-review-graph/graph.db` e `grep`, 2026-09-08, duas rodadas)

| Ferramenta | Maior classe (L) | Maior método dentro dela (L) | `except:` sem tipo | `except Exception` genérico | Linhas >150 chars | % linhas comentário |
|---|---|---|---|---|---|---|
| aidd-forge | 151 | 66 | 0 | 7 | 0 | 1,0% |
| aidd-ops | 389 | 111 | 0 | 19 | 2 | 2,8% |
| aidd-generator | 894 | 198 | 7 | 65 | 41 | 6,6% |
| aidd-enterprise | 817 | 345 (`run_all_checks`) | 15 | 198 | 176 | 3,8% |
| aidd-master | 817 (cópia idêntica) | 345 (cópia idêntica) | 15 | 196 | 183 | 3,9% |

Ranking do mais limpo pro que mais precisa de atenção: aidd-forge → aidd-ops → aidd-generator → aidd-enterprise/aidd-master (empatados, por razões diferentes — ver itens 1-6 deste plano e a iniciativa `correcao-arquitetura-limpa`). Correção em relação à rodada de análise anterior: aidd-ops e aidd-forge não estavam tão "sem ressalva" quanto uma primeira olhada rápida sugeriu — aidd-ops tem um método de 111 linhas real; só aidd-forge se manteve limpo em toda métrica medida nas duas rodadas.

## Definição de Pronto

1. Tabela acima publicada em algum documento de referência do ecossistema (ex.: `docs/` ou anexado a este próprio arquivo como registro final).
2. Nenhuma ação corretiva tomada como parte deste item — apenas registro.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 8: Registrar ranking de limpeza por ferramenta atualizado com todas as metricas (sem acao corretiva).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 8: Registrar ranking de limpeza por ferramenta atualizado com todas as metricas (sem acao corretiva).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
