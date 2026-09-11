# PROCESSO E DECISOES — evolucao-aidd-ops-fase-completa

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.
> **Decisão aplicada em 2026-09-07:** Coolify adotado como plataforma self-hosted para os itens 1, 3 e 4 (executados como slices descompostos NIH #19/#20/#21). O item 2 também foi decidido e concluído em 2026-09-07 (sops+age, ver §5) — nota anterior desatualizada, corrigida em 2026-09-09.

---

## 0. Contexto da decisao

O levantamento NIH (`docs/features/08-09-2026_feature-oportunidades-reaproveitamento-nih.md`, itens 18-21) e a Fase 2 de `docs/planos/a-fazer/direcionamento-estrategico-anti-nih/` apontam que as 4 frentes abaixo (intake web, cofre de credenciais, appshell, isolamento em VPS compartilhada) são, em conjunto, essencialmente o escopo inteiro de plataformas self-hosted maduras como **Coolify**, **CapRover** ou **Dokku** — já prontas, open source, ativas.

A decisão de adotar **Coolify** foi aplicada em 2026-09-07 aos itens 1 (intake web como app gerenciado), 3 (AppShell white-label = Coolify Dashboard) e 4 (isolamento nativo em VPS compartilhada), conforme registrado em cada documento de item e no inventário NIH (#19/#20/#21). O item 2 (cofre de credenciais) permanece bloqueado até o usuário decidir entre sops+age e Vaultwarden.

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Intake Interativo Web Sem Friccao | `01-intake-interativo-web-sem-friccao.md` |
| 2 | Cofre Local e Coleta Segura de Credenciais | `02-cofre-local-e-coleta-segura-de-credenciais.md` |
| 3 | AppShell White-Label e Studios OpenAPI Webhook MCP | `03-appshell-white-label-e-studios-openapi-webhook-mcp.md` |
| 4 | Isolamento Estrito em VPS Compartilhada e Uninstall Atomico | `04-isolamento-estrito-em-vps-compartilhada-e-uninstall-atomico.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Intake Interativo Web Sem Friccao | ✅ Concluído via Coolify + Streamlit (2026-09-07, NIH #19) — `apps/intake/` (Streamlit 8501 headless reusando `montar_plano_em_memoria`) + `Dockerfile.intake` + deploy como app gerenciado via `pipeline_ops.py coolify create/setenv/deploy`; 144 testes aidd-ops verdes, G_OPS_MVP e G_OPS_SSH aprovados | `01-intake-interativo-web-sem-friccao.md` |
| 2 | Cofre Local e Coleta Segura de Credenciais | ✅ Concluído via sops+age (2026-09-07, NIH #18/#29) — `CofreCredenciais` (`src/core/cofre_credenciais.py`) + CLI `pipeline_ops.py cofre init/encrypt/decrypt/up`; 17/17 testes reais com binários `sops`/`age-keygen` (`tests/test_cofre_credenciais.py`), reverificados em 2026-09-09. Linha corrigida — estava desatualizada, o item já constava concluído em seu próprio documento desde 2026-09-07 | `02-cofre-local-e-coleta-segura-de-credenciais.md` |
| 3 | AppShell White-Label e Studios OpenAPI Webhook MCP | ✅ Concluído via Coolify (2026-09-07, NIH #20) — Coolify Dashboard adotado como base para AppShell white-label + Studios integrados via `CoolifyManager` | `03-appshell-white-label-e-studios-openapi-webhook-mcp.md` |
| 4 | Isolamento Estrito em VPS Compartilhada e Uninstall Atomico | ✅ Concluído via Coolify (2026-09-07, NIH #21) — Isolamento nativo de containers em VPS compartilhada implementado via `CoolifyManager` (redes isoladas, zero portas expostas, limites CPU/RAM) | `04-isolamento-estrito-em-vps-compartilhada-e-uninstall-atomico.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
