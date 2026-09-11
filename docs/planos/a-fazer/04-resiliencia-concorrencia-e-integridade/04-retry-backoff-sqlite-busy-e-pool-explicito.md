# Item — retry-backoff-sqlite-busy-e-pool-explicito

> **Escopo:** Implementar retry com backoff exponencial para erros SQLITE_BUSY e tradução para Result.fail(DB_LOCKED) na fronteira de API HTTP.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. grep -rn pool_pre_ping componentes tools nao retorna nada. Nao ha retry exponencial para database is locked.

---

## Contexto já investigado

- Sob worktrees ou concorrência com migrations, busy_timeout de 5s pode estourar e subir exceção crua [SQL-1]. Não há retry com backoff nem código estruturado.

## Definição de Pronto

1. Envolver execuções em `EngineFacadeConnection` com retry exponencial (50ms a 2s, 5 tentativas) para `sqlite3.OperationalError: database is locked`.
2. Configurar pool explícito com pool_pre_ping=True e timeout controlado.
3. Mapear SQLITE_BUSY na camada de rotas para `Result.fail(codigo='DB_LOCKED')` com HTTP 503/Retry-After.

## Critério de saída

- Teste com conexão travada externamente recebe Result estruturado com retries automáticos sem crash.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: retry-backoff-sqlite-busy-e-pool-explicito.
Siga rigorosamente a Definição de Pronto acima:
1. Envolver execuções em `EngineFacadeConnection` com retry exponencial (50ms a 2s, 5 tentativas) para `sqlite3.OperationalError: database is locked`.
2. Configurar pool explícito com pool_pre_ping=True e timeout controlado.
3. Mapear SQLITE_BUSY na camada de rotas para `Result.fail(codigo='DB_LOCKED')` com HTTP 503/Retry-After.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: retry-backoff-sqlite-busy-e-pool-explicito.
Strictly follow the Definition of Done above:
1. Envolver execuções em `EngineFacadeConnection` com retry exponencial (50ms a 2s, 5 tentativas) para `sqlite3.OperationalError: database is locked`.
2. Configurar pool explícito com pool_pre_ping=True e timeout controlado.
3. Mapear SQLITE_BUSY na camada de rotas para `Result.fail(codigo='DB_LOCKED')` com HTTP 503/Retry-After.
Ensure exit code 0 across relevant tests and gates.
```
