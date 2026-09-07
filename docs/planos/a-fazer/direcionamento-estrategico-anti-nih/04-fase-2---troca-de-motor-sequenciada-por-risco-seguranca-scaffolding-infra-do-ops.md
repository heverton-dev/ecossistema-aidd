# Item 4 — Fase 2 - Troca de motor sequenciada por risco (seguranca, scaffolding, infra do ops)

> **Escopo:** Entra: sequenciar (não executar ainda — cada sub-troca vira sua própria tarefa de implementação, aprovada individualmente) a ordem de migração dos 26 itens do levantamento NIH, por risco. Não entra: implementar as trocas — isso é trabalho de execução posterior, um item por vez, cada um com seu próprio critério de verificação.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (sequenciamento estratégico, avalia risco e dependência entre trocas)

---

## Contexto ja investigado

- Levantamento completo em `docs/features/oportunidades-reaproveitamento-oss-nih.md` (26 itens, marcados [confirmado] ou [a verificar]).
- Ordem proposta por risco (a validar com o usuário):
  1. **Segurança primeiro** (itens NIH #1, #9, #10): CSP/security.py → secure.py; secret scanning → detect-secrets/gitleaks; RLS via regex → sqlglot. Risco de regressão de segurança silenciosa é o mais caro (foi o que já aconteceu).
  2. **Scaffolding** (itens #6, #7, #8): add_module.py/compose_suite.py → Cookiecutter/Copier; Result Monad → lib `returns`; DB adapter → SQLAlchemy/aiosqlite. Resolve de brinde a duplicação master/enterprise.
  3. **Infra do ops** (itens #13-21): decisão prévia obrigatória — avaliar adoção de Coolify/CapRover/Dokku ANTES de aprovar qualquer uma das 4 frentes de `evolucao-aidd-ops-fase-completa/`, porque 3 das 4 podem ficar obsoletas.
  4. **Raiz/gates** (itens #2, #3, #4, #5): migrar runner de gates pra `pre-commit`; CLIs pra Typer/Click; adicionar hadolint/Checkov.
  5. **Generator** (itens #22-26): Repomix, instructor, Pandoc, SDK oficial MCP — menor risco, ganho direto de token, pode rodar em paralelo com o resto.

## Definicao de Pronto

1. Ordem de sequenciamento (1-5 acima, ou ajustada) aprovada pelo usuário.
2. Para cada sub-troca da ordem aprovada, existe (ou é criado quando chegar a vez) um item de execução próprio com Definição de Pronto checável — este item não implementa nada, só define a fila.
3. Nenhuma sub-troca começa antes da anterior na fila estar reproduzida (suíte real + app gerado rodando de novo) — ver item 5 (Fase 3) para o mecanismo de prova.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: Fase 2 - Troca de motor sequenciada por risco (seguranca, scaffolding, infra do ops).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: Fase 2 - Troca de motor sequenciada por risco (seguranca, scaffolding, infra do ops).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
