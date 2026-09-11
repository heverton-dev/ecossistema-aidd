# Item — testes-contrato-rls-e-wal-pragmas

> **Escopo:** Criar testes de contrato para RLS (afirmando isolamento entre múltiplos tenants) e para configuração obrigatória de WAL/PRAGMAs na conexão SQLite.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. grep -rn busy_timeout tools/*/tests nao retorna nada. Nao ha teste de RLS com 2 tenants nem de PRAGMA journal_mode=wal / busy_timeout.

---

## Contexto já investigado

- Filtros RLS não possuem teste com 2 tenants concorrentes verificando ausência de vazamento cruzado. PRAGMAs de conexão não são checados.

## Definição de Pronto

1. Criar teste RLS com 2 tenants confirmando zero vazamento de dados.
2. Criar teste validando PRAGMA journal_mode=wal e busy_timeout=5000.
3. Garantir falha de mutantes.

## Critério de saída

- Testes de contrato RLS e WAL passando 100%.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: testes-contrato-rls-e-wal-pragmas.
Siga rigorosamente a Definição de Pronto acima:
1. Criar teste RLS com 2 tenants confirmando zero vazamento de dados.
2. Criar teste validando PRAGMA journal_mode=wal e busy_timeout=5000.
3. Garantir falha de mutantes.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: testes-contrato-rls-e-wal-pragmas.
Strictly follow the Definition of Done above:
1. Criar teste RLS com 2 tenants confirmando zero vazamento de dados.
2. Criar teste validando PRAGMA journal_mode=wal e busy_timeout=5000.
3. Garantir falha de mutantes.
Ensure exit code 0 across relevant tests and gates.
```
