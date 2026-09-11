# Item 8 — Registrar ranking de limpeza por ferramenta atualizado com todas as metricas (sem acao corretiva)

> **Escopo:** Entra: só registrar, num documento de referência, a régua objetiva de limpeza de código medida via grafo/grep em 2026-09-08 por ferramenta — sem nenhuma ação corretiva associada. Não entra: corrigir qualquer coisa a partir deste ranking (isso é o que os itens 1-7 já fazem, ou achados futuros).

> **Status:** ✅ Concluído (2026-09-08 — tabela já registrada abaixo, ver nota pós-execução)

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

## Execução (2026-09-08)

- Tabela já registrada acima no momento da criação deste documento — satisfaz a Definição de Pronto sem ação adicional.
- Nota de atualização: a coluna `except: sem tipo` reflete a contagem **antes** do item 2 deste mesmo plano ser executado. Depois do item 2, essa coluna caiu para **0 em todas as 5 ferramentas** (aidd-enterprise, aidd-master e aidd-generator corrigidos; aidd-forge/aidd-ops já eram 0). As demais colunas (classe/método maior, `except Exception` genérico, linhas longas, % comentário) ainda refletem o estado real de 2026-09-08, pois os itens que as endereçam (1 e 3) ainda não haviam sido executados.
- Nota de atualização 2 (recomputado via AST em sessão posterior, depois dos itens 3 e 4): a coluna "Maior método dentro dela" também mudou.
  - `aidd-generator`: nenhum método passa de 100 linhas — `CriadorProjetoFase5._registrar_sync_manifest` (94L) é hoje o maior, contra os 198L de `_criar_arquivos_configuracao` registrados originalmente (item 3 dividiu esse e os outros métodos gigantes). A classe `ImplementadorFase8` cresceu de 894 para 942 linhas — efeito esperado de dividir um método em vários (mais assinaturas/docstrings), não uma regressão: nenhum método individual passa de 100 linhas.
  - `aidd-ops`: `OpsMvpGate._validar_estrutura` (73L) é hoje o maior método, contra os 111L de `_validar_saida` registrados originalmente (item 3 dividiu esse método).
  - `aidd-enterprise`/`aidd-master`: dentro de `SecurityGate` (`G_SEGURANCA.py`), o maior método hoje é `_camada8_cve_audit` (75L), contra os 345L de `run_all_checks` registrados originalmente (item 4 dividiu essa função). A coluna "Maior classe" da tabela original (817L) não foi recomputada nesta nota — pode se referir a outra classe do mesmo tool, não necessariamente `SecurityGate`; fica para quando o item 1 (ainda pendente) passar por essas ferramentas.
  - As colunas `except Exception` genérico, linhas >150 chars e % comentário continuam refletindo o estado real de 2026-09-08 — o item 1 (que as afeta) ainda não foi executado.
- **Veredito: Concluído.**

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
