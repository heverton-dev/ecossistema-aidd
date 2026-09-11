# Item 1 — Reativar G_ARQUITETURA_DELIVERABLE corrigindo 212 violacoes SQL-fora-infra nos templates

> **Escopo:** Corrigir as 212 violacoes de arquitetura (SQL fora de `infrastructure/`) ja detectadas pelo gate `G_ARQUITETURA_DELIVERABLE.py` nos 15 arquivos listados, e mover esse gate de "stage manual" para a bateria agregada de `python ecossistema.py audit`. Nao inclui reescrever a arquitetura Clean/DDD alem do necessario pra zerar essas violacoes.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** 3.0 — evidencia: gates/G_ARQUITETURA_DELIVERABLE.py rodado: 212 violacoes em 15 arquivos (templates/core/server.py 46, templates/v2/server.py 46, templates/gates/G_SEGURANCA.py 6, mcp_server.py 2, src/server.py 2 e equivalentes enterprise)
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

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
