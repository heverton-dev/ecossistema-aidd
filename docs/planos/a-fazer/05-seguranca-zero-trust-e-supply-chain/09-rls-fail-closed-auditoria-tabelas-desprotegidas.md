# Item — rls-fail-closed-auditoria-tabelas-desprotegidas

> **Escopo:** Implementar política fail-closed para RLS no SQLite: alertar ou bloquear tabelas não registradas no RLS_TABLE_REGISTRY durante a inicialização.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. Nao ha comparacao, no boot do schema, entre tabelas criadas e a lista esperada de tabelas RLS.

---

## Contexto já investigado

- RLS opera em modo fail-open [SEC-13]: se um desenvolvedor esquecer de chamar enable_rls_tenant, a tabela fica desprotegida silenciosamente.

## Definição de Pronto

1. No boot do schema, comparar todas as tabelas criadas contra a lista esperada de tabelas RLS.
2. Emitir erro estruturado ou warning crítico se houver tabela de tenant não registrada.
3. Adicionar teste automatizado de fail-closed.

## Critério de saída

- Tabelas de dados multi-tenant protegidas por padrão.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: rls-fail-closed-auditoria-tabelas-desprotegidas.
Siga rigorosamente a Definição de Pronto acima:
1. No boot do schema, comparar todas as tabelas criadas contra a lista esperada de tabelas RLS.
2. Emitir erro estruturado ou warning crítico se houver tabela de tenant não registrada.
3. Adicionar teste automatizado de fail-closed.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: rls-fail-closed-auditoria-tabelas-desprotegidas.
Strictly follow the Definition of Done above:
1. No boot do schema, comparar todas as tabelas criadas contra a lista esperada de tabelas RLS.
2. Emitir erro estruturado ou warning crítico se houver tabela de tenant não registrada.
3. Adicionar teste automatizado de fail-closed.
Ensure exit code 0 across relevant tests and gates.
```
