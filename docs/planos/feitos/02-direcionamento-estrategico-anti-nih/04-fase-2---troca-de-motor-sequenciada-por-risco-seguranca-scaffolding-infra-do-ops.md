# Item 4 — Fase 2 - Troca de motor sequenciada por risco (seguranca, scaffolding, infra do ops)

> **Escopo:** Entra: sequenciar (não executar ainda — cada sub-troca vira sua própria tarefa de implementação, aprovada individualmente) a ordem de migração de 26 dos itens do levantamento NIH, por risco. Não entra: implementar as trocas — isso é trabalho de execução posterior, um item por vez, cada um com seu próprio critério de verificação.
> **Status:** [APROVADO em 2026-09-07 — ordem de sequenciamento travada; execução de cada sub-troca é item futuro próprio, criado quando chegar a vez]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (sequenciamento estratégico, avalia risco e dependência entre trocas)

---

## Contexto ja investigado

- Levantamento completo em `docs/features/08-09-2026_feature-oportunidades-reaproveitamento-nih.md` (33 itens no total: 28 originais + 5 transversais #29-33; esta fila cobre 26 dos 28 originais — ver nota abaixo sobre #11/#12 e os transversais).
- Ordem aprovada por risco:
  1. **Segurança primeiro** (itens NIH #1, #9, #10, #28): CSP/security.py → secure.py; secret scanning → detect-secrets/gitleaks; RLS via regex → sqlglot; Tailwind servido via CDN → Tailwind CLI/PostCSS auto-hospedado (resolve o CSP na raiz — sem CDN, não precisa mais relaxar `script-src`). Risco de regressão de segurança silenciosa é o mais caro (foi o que já aconteceu).
  2. **Scaffolding** (itens #6, #7, #8, #27): add_module.py/compose_suite.py → Cookiecutter/Copier; Result Monad → lib `returns`; DB adapter → SQLAlchemy/aiosqlite; migração de schema sem ferramenta → Alembic. Resolve de brinde a duplicação master/enterprise.
  3. **Infra do ops** (itens #13-21): decisão prévia obrigatória — avaliar adoção de Coolify/CapRover/Dokku ANTES de aprovar qualquer uma das 4 frentes de `evolucao-aidd-ops-fase-completa/`, porque 3 das 4 podem ficar obsoletas.
  4. **Raiz/gates** (itens #2, #3, #4, #5): migrar runner de gates pra `pre-commit`; CLIs pra Typer/Click; adicionar hadolint/Checkov.
  5. **Generator** (itens #22-26): Repomix, instructor, Pandoc, SDK oficial MCP — menor risco, ganho direto de token, pode rodar em paralelo com o resto.

- **Itens fora do escopo desta fila (decisão explícita do usuário em 2026-09-07):** #11 (webhooks retry/DLQ hand-rolled → `huey`) e #12 (documentação custom → Swagger UI/ReDoc) ficam de fora desta iniciativa — ambos marcados `[a verificar]` no levantamento original, sem confirmação linha a linha. Podem ser retomados em outro ciclo, com seu próprio diagnóstico, se e quando forem priorizados.
- A soma 26 = 28 itens originais do levantamento (`docs/features/08-09-2026_feature-oportunidades-reaproveitamento-nih.md`) menos #11 e #12. Os 5 itens transversais (#29-33) do mesmo levantamento não fazem parte desta fila de sequenciamento — são achados cross-cutting sem dono de ferramenta único.
- Item #17 (healthcheck) está dentro do range #13-21 da Fase 3 só por proximidade de área (infra do ops), mas já é `[confirmado, NÃO é NIH]` — não precisa de troca, não gera sub-item de execução.

## Decisão de sequenciamento

**Ordem de 5 fases aprovada pelo usuário em 2026-09-07, sem ajustes.**

### Decisão de Motor de Infra do Ops (NIH #13 — Fase 2-Infra1)

- **Decisão:** **Coolify** escolhido como motor de infraestrutura do `aidd-ops` (avaliado contra CapRover e Dokku).
- **Justificativa Técnica:**
  - **API-First:** Permite integração determinística direta a partir do `ecossistema.py` e `pipeline_ops.py`, sem raspagem ou automação frágil de CLI.
  - **Substituição Nativa de 3 Frentes NIH (#19, #20, #21):**
    - Substitui **#19** (*Intake interativo web*): Coolify entrega UI web self-hosted madura e estável para intake e criação de serviços.
    - Substitui **#20** (*AppShell white-label + Studios*): Dashboard administrativo e portal de controle já built-in e ativamente mantido.
    - Substitui **#21** (*Isolamento estrito em VPS compartilhada*): Multi-tenancy, isolamento de rede Docker, gestão de portas e proxy reverso automático (Traefik integrado) são o core nativo da ferramenta, eliminando colisões de porta na raiz.
  - **Webhook Deploy:** Gatilhos automáticos de deploy e rollback desacoplados via webhooks prontos.
  - **Dashboard Built-in:** Monitoramento, logs, variáveis de ambiente e métricas de container sem necessidade de painéis paralelos.
  - **Impacto no Roadmap:** Torna obsoletas 3 das 4 frentes planejadas de `docs/planos/a-fazer/03-evolucao-aidd-ops-fase-completa/`, reduzindo o escopo a apenas **integração com a API do Coolify**.

## Definicao de Pronto

1. ✅ Ordem de sequenciamento (1-5 acima) aprovada pelo usuário em 2026-09-07.
2. Para cada sub-troca da ordem aprovada, existe (ou é criado quando chegar a vez) um item de execução próprio com Definição de Pronto checável — este item não implementa nada, só define a fila.
3. Nenhuma sub-troca começa antes da anterior na fila estar reproduzida (suíte real + app gerado rodando de novo) — ver item 5 (Fase 3) para o mecanismo de prova.
4. ✅ **Decisão de motor de infra (NIH #13) concluída em 2026-09-07:** Coolify escolhido contra CapRover e Dokku. Justificativa registrada: API-first, substitui #19/#20/#21, webhook deploy e dashboard built-in. Demais sub-trocas de infra destravadas para planejamento de integração.

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
