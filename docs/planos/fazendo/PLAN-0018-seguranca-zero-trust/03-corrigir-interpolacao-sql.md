# Item — corrigir-interpolacao-sql-set-tenant-pg

> **Escopo:** Corrigir a interpolação direta com f-string em SET app.current_tenant_id na policy de PostgreSQL, eliminando vulnerabilidade de SQL Injection.
> **Status:** [CONCLUIDO]
> **Auditoria por reproducao real (12-09-2026):** CONCLUÍDO. Validação estrita por regex _UUID_RE (36 caracteres hexadecimais com hífens) implementada em set_tenant, query parametrizada via %s no Postgres e testes automatizados cobrindo payload de injeção e formatos inválidos. 1954 testes passando (0 falhas em todas as suítes).

---

## Contexto já investigado

- database.py:390 usa SET app.current_tenant_id = '{tenant_id}' com f-string [SEC-10], permitindo quebra de isolamento multi-tenant se tenant_id contiver aspas.

## Definição de Pronto

1. Substituir a f-string por validação estrita de UUID via regex (`^[0-9a-fA-F-]{36}$`).
2. Aplicar parametrização segura na query de sessão PostgreSQL.
3. Adicionar teste automatizado com payload de injeção (`x'; DROP TABLE`) garantindo rejeição.

## Critério de saída

- Injeção SQL em tenant_id bloqueada com validação e parametrização.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: corrigir-interpolacao-sql-set-tenant-pg.
Siga rigorosamente a Definição de Pronto acima:
1. Substituir a f-string por validação estrita de UUID via regex (`^[0-9a-fA-F-]{36}$`).
2. Aplicar parametrização segura na query de sessão PostgreSQL.
3. Adicionar teste automatizado com payload de injeção (`x'; DROP TABLE`) garantindo rejeição.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: corrigir-interpolacao-sql-set-tenant-pg.
Strictly follow the Definition of Done above:
1. Substituir a f-string por validação estrita de UUID via regex (`^[0-9a-fA-F-]{36}$`).
2. Aplicar parametrização segura na query de sessão PostgreSQL.
3. Adicionar teste automatizado com payload de injeção (`x'; DROP TABLE`) garantindo rejeição.
Ensure exit code 0 across relevant tests and gates.
```
