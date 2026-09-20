# Item 1 — Reativar G_ARQUITETURA_DELIVERABLE corrigindo 212 violacoes SQL-fora-infra nos templates

> **Escopo:** Corrigir as violações de arquitetura (SQL fora de `infrastructure/`) detectadas pelo gate `G_ARQUITETURA_DELIVERABLE.py`, e mover esse gate de "stage manual" para a bateria padrão de hooks do pre-commit e de `python ecossistema.py audit`.
> **Status:** [CONCLUIDO]
> **Nota Atual (0-10):** 3.0 — evidencia: gates/G_ARQUITETURA_DELIVERABLE.py rodado com 18 violações reais pós-regressão em `src/core/`.
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** 10.0 — evidencia: G_ARQUITETURA_DELIVERABLE.py rodado com 0 violações (334 arquivos auditados, exit 0); pre-commit sem `stages: [manual]` aprovado; ecossistema.py audit aprovado (exit 0).

---

## Reconciliação Factual: 18 medidas vs 212 previstas

**Veredicto: Regressão de backlog após fix anterior, e não cegueira do gate.**

1. As 212 violações originais foram corrigidas no commit `d7ad28f` ("fix: corrige as 212 violações SQL-fora-de-infra"), extraindo SQL inline dos templates (`server.py`, `G_SEGURANCA.py`, etc.) para a camada de persistência.
2. Posteriormente, dois commits reintroduziram SQL inline em `src/core/`:
   - Commit `ebd6b7f`: introduziu `transaction_log.py` com 7 chamadas `.execute()` inline (7 master + 7 enterprise = 14 violações).
   - Commit `154f275`: modificou `src/core/mcp_server.py` reintroduzindo `import sqlite3` e `.execute()` inline (2 master + 2 enterprise = 4 violações).
3. Total medido antes da correção: **18 violações** (todas em `src/core/`, zero nos templates).
4. Solução aplicada:
   - Funções de persistência de `transaction_log` movidas para `src/core/database.py` e consumidas via injeção/delegação em master, enterprise e componentes compartilhados.
   - `mcp_server.py` refatorado para delegar operações SQL ao `MCPRepository` (`src/core/mcp_repository.py`), eliminando `import sqlite3` e queries inline.
   - Espelhamento estrito validado com `G_DRIFT_NUCLEO_COMPARTILHADO.py` e `G_TRANSACTION_LOG_LRU.py`.

---

## Contexto ja investigado

- `gates/G_ARQUITETURA_DELIVERABLE.py` roda hoje so manualmente (fora do `audit` agregado).
- Rodando o gate agora: 212 violacoes em 15 arquivos: templates/core/server.py (46), templates/v2/server.py (46), templates/gates/G_SEGURANCA.py (6), mcp_server.py (2), src/server.py (2) e equivalentes do lado enterprise.

## Definicao de Pronto

1. As 212 violacoes SQL-fora-de-infrastructure detectadas em templates/core/server.py, templates/v2/server.py, templates/gates/G_SEGURANCA.py, mcp_server.py, src/server.py (e equivalentes enterprise) foram corrigidas — SQL movido para a camada de infrastructure correta.
2. `python gates/G_ARQUITETURA_DELIVERABLE.py` roda com exit 0 (zero violacoes).
3. O gate sai do "stage manual" e passa a fazer parte da bateria agregada de `python ecossistema.py audit`.
4. Testes executados com exit 0.

## Criterio de saida

- `python gates/G_ARQUITETURA_DELIVERABLE.py` aprovado (exit 0), rodado de verdade.
- `python ecossistema.py audit` inclui esse gate e continua passando.
- Nenhuma regressao nos testes reais ja existentes.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Reativar G_ARQUITETURA_DELIVERABLE corrigindo 212 violacoes SQL-fora-infra nos templates.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Reativar G_ARQUITETURA_DELIVERABLE corrigindo 212 violacoes SQL-fora-infra nos templates.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
