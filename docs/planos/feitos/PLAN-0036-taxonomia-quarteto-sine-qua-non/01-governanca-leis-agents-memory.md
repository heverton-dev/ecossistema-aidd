# Item 1 — governanca-leis-agents-memory

> **Escopo:** Atualizar a Lei Inviolável #10 nos documentos de governança central (AGENTS.md, MEMORY.md, GEMINI.md) formalizando a nova taxonomia [/api, /webhook, /mcp, /docs].
> **Status:** [EM EXECUCAO]

---

## Arquivos Alvo

- `AGENTS.md`
- `MEMORY.md`
- `GEMINI.md`

## Metadados do Ticket

- **Blocked By:** nenhum
- **Comando de Validação:**
  ```bash
  python gates/G_HARNESS_COMPAT.py
  ```

## Contexto e Definição de Pronto

1. Atualizar o texto da Lei #10 em `AGENTS.md` para consagrar explicitamente:
   - Swagger / OpenAPI Studio: `/api`
   - Webhook Studio: `/webhook`
   - MCP Studio: `/mcp`
   - Guia do Utilizador: `/docs`
2. Registrar a decisão no `MEMORY.md` com data de 21/09/2026.
3. Sincronizar os ponteiros de governança.
