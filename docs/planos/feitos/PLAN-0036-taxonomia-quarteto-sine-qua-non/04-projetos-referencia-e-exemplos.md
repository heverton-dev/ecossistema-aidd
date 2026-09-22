# Item 4 — projetos-referencia-e-exemplos

> **Escopo:** Atualizar rotas nos exemplos canonicos (enterprise-suite-v4) para entregar nativamente /api, /webhook, /mcp e /docs.
> **Status:** [EM EXECUCAO]

---

## Arquivos Alvo

- `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/server.py`
- `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/openapi.json`

## Metadados do Ticket

- **Blocked By:** TICKET-03
- **Comando de Validação:**
  ```bash
  python gates/G_QUARTETO_SINE_QUA_NON.py
  ```

## Contexto e Definição de Pronto

1. Configurar o projeto canônico `enterprise-suite-v4` para expor `/api` como Swagger Studio, `/webhook` como Webhook Studio, `/mcp` como MCP Studio e `/docs` como Guia do Utilizador.
2. Executar `G_QUARTETO_SINE_QUA_NON.py` comprovando 100% de conformidade.
