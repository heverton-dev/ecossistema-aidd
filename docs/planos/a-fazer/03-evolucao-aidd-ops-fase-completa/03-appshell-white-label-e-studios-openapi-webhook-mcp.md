# Item 3 — AppShell White-Label e Studios OpenAPI Webhook MCP (NIH #20)

> **Escopo:** Substituir o desenvolvimento do zero de um frontend AppShell customizado utilizando o Coolify Dashboard como base nativa e integrando os Studios de OpenAPI, Webhook, MCP e monitoramento Uptime Kuma.
> **Status:** [CONCLUÍDO em 2026-09-07 — Coolify adotado como base para AppShell white-label via `CoolifyManager`]

---

## Contexto ja investigado

- O levantamento NIH #20 e a Fase 2 de infraestrutura apontaram que construir um frontend AppShell do zero seria redundante frente a plataformas consolidadas.
- O Coolify entrega nativamente uma UI administrativa completa, autenticação centralizada, proxy reverso e gerenciamento de recursos.
- Foi implementado o método `configurar_appshell_whitelabel` em `tools/aidd-ops/src/core/coolify.py` para mapear o branding corporativo (nome, marca, logo, cores) e agregar os Studios unificados (OpenAPI/Swagger, Webhook Events, MCP Agents e Uptime Kuma Dashboard).

## Definicao de Pronto

1. ✅ Coolify Dashboard configurado como base de AppShell white-label sem construção de frontend paralelo.
2. ✅ Studios unificados (OpenAPI, Webhooks, MCP, Uptime Kuma) integrados e mapeados no portal.
3. ✅ Testes determinísticos cobrindo validação e integridade em `tools/aidd-ops/tests/test_coolify.py`.
4. ✅ Gates de qualidade e integridade do ecossistema mantidos com exit 0.

## Criterio de saida

- `tools/aidd-ops/src/core/coolify.py` com `CoolifyManager.configurar_appshell_whitelabel`.
- Testes reais passando em `tools/aidd-ops/tests/test_coolify.py`.
- Documentação sincronizada no inventário NIH.
