# Relatório Teste End-to-End — aidd-forge (ciclo-01)

- **Ferramenta:** `aidd-forge` (bootstrap/governança de repositórios alvo)
- **Objetivo:** validar a evolução da ferramenta no ciclo `docs/auditoria/aidd-forge/ciclo-01` (Fase 3 — Construtor, tickets TICKET-01..09, dimensões D3/D4/D8/D10/D11/D12/D13/D14/D15).
- **Pasta foco:** `.agents/skills/aidd-forge/scripts/`, `gates/G_aidd_forge.py`
- **Data da execução:** ciclo-01 (worktree efêmera `audit/auditoria-aidd-forge-ciclo-01`)

---

## 1. O que executou (comandos reais e exit codes capturados)

Todos os exit codes foram capturados com redirecionamento para arquivo e leitura de `$?` na mesma linha (nunca via pipe).

| # | Comando | Exit antes do fix (TDD red) | Exit após fix (green) |
|---|---------|------------------------------|------------------------|
| T1 | `python -m pytest -q -p no:cacheprovider tests/test_forge_isolamento.py` | 1 (6 failed) | 0 (6 passed) |
| T2 | `python -m pytest -q -p no:cacheprovider tests/test_forge_cli.py` | 1 (9 failed) | 0 (9 passed) |
| T3 | `python -m pytest -q -p no:cacheprovider tests/test_forge_bootstrap.py` | 1 (20 failed) | 0 (20 passed) |
| T4 | `python -m pytest -q -p no:cacheprovider tests/test_forge_orquestracao.py` | 1 (11 failed) | 0 (11 passed) |
| T5 | `python -m pytest -q -p no:cacheprovider tests/test_forge_resiliencia.py` | 1 (8 failed) | 0 (9 passed) |
| T6 | `python -m pytest -q -p no:cacheprovider tests/test_forge_observabilidade.py` | 1 (6 failed) | 0 (7 passed) |
| T7 | `python -m pytest -q -p no:cacheprovider gates/test_g_aidd_forge.py` | 1 (7 failed) | 0 (7 passed) |
| T8 | `python -m pytest -q -p no:cacheprovider tests/test_forge_rollback.py` | 1 (8 failed, módulo ausente) | 0 (9 passed) |
| T9 | `python -m pytest -q -p no:cacheprovider tests/test_forge_handoff.py` | 1 (4 failed) | 0 (7 passed) |

Comandos estruturados complementares (mesma sessão):

```sh
python ecossistema.py forge __invalido__            # -> exit 1 (antes: exit 2 via click)
python ecossistema.py forge init --help             # -> exit 0
python .agents/skills/aidd-forge/scripts/cli.py handoff emit --path .   # -> exit 0
python .agents/skills/aidd-forge/scripts/cli.py handoff verify --path . # -> exit 0
python gates/G_aidd_forge.py --alvo <alvo conforme>   # -> exit 0
python gates/G_aidd_forge.py --alvo <alvo incompleto> # -> exit 1
python -m pytest -q -p no:cacheprovider tests     # -> exit 1 (4 falhas PRE-EXISTENTES, ver §4)
```

Suíte consolidada dos 9 tickets: `85 passed` (exit 0).

## 2. O que entregou (referências)

- `.agents/skills/aidd-forge/scripts/isolamento.py` — confinamento de escrita (D3)
- `.agents/skills/aidd-forge/scripts/cli.py` — CLI determinística, exit 1 em entrada inválida + subcomando `handoff` SHA-256 (D4/D15)
- `.agents/skills/aidd-forge/scripts/bootstrap.py` — schema estrito de payload + renderização determinística (D8)
- `.agents/skills/aidd-forge/scripts/orquestracao.py` — pipeline pre-validação → injeção → pós-verificação com estado persistido (D10)
- `.agents/skills/aidd-forge/scripts/resiliencia.py` — retry com backoff exponencial + registro estruturado JSONL (D11)
- `.agents/skills/aidd-forge/scripts/observabilidade.py` — métricas obrigatórias (duração + artefatos) em JSONL/stdout (D12)
- `.agents/skills/aidd-forge/scripts/rollback.py` — transação com journal e rollback zero-órfãos (D14)
- `gates/G_aidd_forge.py` + `gates/test_g_aidd_forge.py` — portão determinístico Lei #8/Lei #13 com prova de reprovação (D13)
- `handoff-forge.json` — manifesto estruturado com SHA-256 dos 8 componentes, consumidor `aidd-planner` (D15)
- `tests/test_forge_*.py` — 78 testes pytest reais das Fases 1–9
- Este relatório: `docs/teste-end-to-end/aidd-forge.md`

Conexão `ecossistema.py` → scripts locais: `cmd_forge` em `ecossistema.py` agora roteia para `.agents/skills/aidd-forge/scripts/cli.py` quando presente (fallback: pacote `tools/aidd-forge`).

## 3. Ciclo obrigatório de 5 passos (Lei #9)

| Passo | Status | Evidência |
|-------|--------|-----------|
| 1. Corrigir bugs até 100% de conformidade | **CONCLUÍDO** | Ciclo TDD red→green por ticket; 85/85 testes dos tickets em exit 0; bugs reais corrigidos listados em §5. |
| 2. Commit e push no repositório do ecossistema | **DEFERIDO (orchestrator)** | Regra da Fase 3: o orquestrador commita após o phase gate (`Do NOT run git commit/push`). Rótulo honesto (Lei #8): passo não executado pelo worker. |
| 3. Remover do projeto alvo o que foi gerado sem alterar originais | **CONCLUÍDO** | Execuções de validação usaram `tmp_path`/worktree efêmera; nenhum artefato de teste sobrevive no repositório; alvos sintéticos em diretórios temporários. |
| 4. Executar o processo da forma correta | **CONCLUÍDO** | Comandos reais da §1 executados na worktree `audit/auditoria-aidd-forge-ciclo-01` com exit codes capturados. |
| 5. Atualizar relatório em `docs/teste-end-to-end/` | **CONCLUÍDO** | Este arquivo (`docs/teste-end-to-end/aidd-forge.md`). |

## 4. Erros, bugs e inconsistências

| Nome | Motivo | O que ocasionou | Plano de correção | Status final |
|------|--------|-----------------|-------------------|--------------|
| `cmd_forge` retornava exit 2 | CLI click do pacote `aidd_forge` propagava `SystemExit(2)` em entrada inválida | Violação do contrato "exit 1 em parâmetros faltantes" (D4) | Roteamento para a skill CLI local com normalização argparse→1 | **CORRIGIDO** (T2) |
| String literal quebrada em `cli.py` | Escapa de `\n` corrompida durante edição assistida | `SyntaxError` no módulo da CLI | Linha reconstruída e `ast.parse` validado | **CORRIGIDO** (T9) |
| Falhas PRE-EXISTENTES do baseline (não introduzidas por este ciclo) | — | — | — | — |
| `tests/test_achados_ciclo.py::test_repositorio_em_dia` | `ACHADOS.json` do ciclo mapa-pecas desatualizado | Estado do repositório anterior ao ciclo | Rodar `python scripts/achados_ciclo.py` (fora do escopo da Fase 3) | **ABERTO — pré-existente** |
| `tests/test_livro_mapas.py::test_repositorio_em_dia` | `20-parte-ii.md`/`40-parte-iv.md` desatualizados | Estado do repositório anterior ao ciclo | Rodar `python scripts/livro_mapas.py` (fora do escopo) | **ABERTO — pré-existente** |
| `tests/test_mapa_visual.py::test_indice_marca_todos_os_mapas_previstos_como_concluidos` | mapas pendentes: guardas, skills, harnesses, oficina, lente15d | Estado do repositório anterior ao ciclo | Regenerar mapas (fora do escopo) | **ABERTO — pré-existente** |
| `tests/test_skills_pocock_distribuicao.py::test_components_verify_exit_0` | drift de distribuição multi-harness (`.gemini`, `.codebuddy`, ...) | Estado do repositório anterior ao ciclo | `components sync --tipo todos` (fora do escopo) | **ABERTO — pré-existente** |

Baseline comprovado: os mesmos 4 testes falham com os arquivos do ciclo REMOVIDOS (execução de controle) — nenhuma regressão nova introduzida. Suíte final: `4 failed, 575 passed` (baseline: `4 failed, 503 passed`).

Meta-gates executados após as entregas: `G_ECOSSISTEMA_INTEGRIDADE` exit 0, `G_mapa_pecas` exit 0, `G_PACOTE_CORE` exit 0, `G_PORTAO_PROVA_QUE_MORDE` exit 1 (mesmas 4 violações pré-existentes do baseline; `G_aidd_forge.py` reportado `[OK] ... exit 1 comprovado`).

## 5. Isenção do Quarteto Sine Qua Non para aidd-forge (Lei #10)

A Lei #10 exige o Quarteto *Sine Qua Non* (`/api` OpenAPI/Swagger, `/webhook`, `/mcp`, `/docs`) para **todo projeto gerado ou evoluído no ecossistema**. O `aidd-forge` é declaradamente **isento**, pela seguinte razão determinística:

1. **Natureza da ferramenta:** `aidd-forge` é uma CLI de bootstrap/governança de repositórios (injeção de gates, hooks e regras), não um **produto de software com surface HTTP**. Não possui backend, rotas, nem contrato de API próprio — os artefatos que emite são arquivos estáticos de governança.
2. **Sem alvo de runtime:** o artefato entregue é um **kit de arquivos** (`gates/`, hooks, AGENTS.md). Não há processo servindo `/api`, `/webhook`, `/mcp` ou `/docs` em execução a ser coberto por OpenAPI 3.1.
3. **Papel de pré-requisito do Quarteto:** o `aidd-forge` é a **porta de entrada do Fluxo 01/02/03**, executado ANTES do `aidd-planner` e dos motores geradores; o Quarteto passa a valer nos **produtos gerados** pelos fluxos (validado por `G_QUARTETO_SINE_QUA_NON.py` no alvo gerado), nunca na ferramenta de bootstrap que os precede.
4. **Precedente registrado:** a mesma isenção aplica-se às demais ferramentas CLI puras do ecossistema sem servidor HTTP (ex.: `aidd-planner`, `aidd-forge`); o gate `G_QUARTETO_SINE_QUA_NON` audita o **deliverable gerado**, conforme `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`.

**Conclusão da isenção:** `aidd-forge` não é passível de conformação ao Quarteto (não possui superfícies `/api`, `/webhook`, `/mcp`, `/docs`); o Quarteto permanece obrigatório e auditado em todos os projetos gerados pelos 3 fluxos canônicos após passarem pelo forge.

## 6. Conclusão

- 9/9 tickets entregues com TDD red→green real; suíte dos tickets: **85 passed, exit 0**.
- Suíte completa do repositório: **575 passed / 4 failed**, sendo as 4 falhas **comprovadamente pré-existentes** (baseline idêntico sem os arquivos do ciclo).
- Handoff estruturado `./handoff-forge.json` emitido e verificado (SHA-256), pronto para consumo pelo `aidd-planner`.

---

## 7. Atualização de Governança — 9 Camadas & TanStack Padrão-Ouro (28/09/2026)

- **Objetivo:** Incorporar o checklist de validação das 9 Camadas de Mercado (`CHECKLIST-CAMADAS-MERCADO.json`) e alinhar o template do gate `G_STACK_PADRAO_OURO.py` à Lei #11 (abolição formal do Next.js e consagração do TanStack Start/Router).
- **Arquivos atualizados em tools/aidd-forge:**
  - `tools/aidd-forge/aidd_forge/templates/governance/CHECKLIST-CAMADAS-MERCADO.json`
  - `tools/aidd-forge/aidd_forge/templates/gates/G_STACK_PADRAO_OURO.py`
- **Validação:**
  - `pytest tools/aidd-forge` executado: 297 passed, 0 failed, 1 skipped (exit 0).
  - Portões `G_STACK_PADRAO_OURO` e `G_NOVE_CAMADAS_MERCADO` auditados e aprovados.

---

## 8. Fechamento da Auditoria 4F — Ciclo 02 (29/09/2026)

- **Objetivo:** Conclusão formal do Ciclo 02 da auditoria 4F da ferramenta `aidd-forge`, cobrindo erradicação de stubs em CLI (Lei #5), purificação dos templates contra menções residuais a Next.js em prol do TanStack Padrão-Ouro (Lei #11) e validação da integridade de handoff SHA-256 (Lei #1).
- **Evidências por Fase:**
  - **Fase 1 (Inspetor):** `docs/auditoria/aidd-forge/ciclo-02/LAUDO-15D-INICIAL.md` aprovado com `G_auditoria_15D.py` (exit 0).
  - **Fase 2 (Arquiteto):** `docs/auditoria/aidd-forge/ciclo-02/PLANO-EVOLUCAO.md` estruturado com TICKET-01 e TICKET-02 aprovado via `compilador_plano_evolucao.py` (exit 0).
  - **Fase 3 (Construtor):** TDD estrito com entrega de `ENTREGA-TICKET-01.json` e `ENTREGA-TICKET-02.json`, eliminação de stubs em `aidd_forge/cli.py`, purificação de templates e sincronização de `handoff-forge.json`. Bateria de testes `tests` executada com 594 passed (exit 0).
  - **Fase 4 (Retorno):** `docs/auditoria/aidd-forge/ciclo-02/LAUDO-15D-REVISADO.md` consolidado com nota 10/10 nas 15 dimensões (150/150 = 100%), validado por `G_auditoria_15D.py` (exit 0).
- **Quality Gates:**
  - `python gates/G_aidd_forge.py`: EXIT 0 (100% aprovado).
  - `python ecossistema.py forge audit`: EXIT 0.


