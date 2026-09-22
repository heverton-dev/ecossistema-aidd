# Item 2 — quality-gates-quarteto-contract-rot

> **Escopo:** Atualizar G_QUARTETO_SINE_QUA_NON.py e sua suite de testes com prova que morde (test_g_quarteto_sine_qua_non.py) para auditar [/api, /webhook, /mcp, /docs].
> **Status:** [EM EXECUCAO]

---

## Arquivos Alvo

- `gates/G_QUARTETO_SINE_QUA_NON.py`
- `gates/test_g_quarteto_sine_qua_non.py`
- `tests/test_gate_quarteto_sine_qua_non.py`

## Metadados do Ticket

- **Blocked By:** TICKET-01
- **Comando de Validação:**
  ```bash
  python gates/test_g_quarteto_sine_qua_non.py
  ```

## Contexto e Definição de Pronto

1. Atualizar `G_QUARTETO_SINE_QUA_NON.py` para verificar:
   - API Studio: rota `/api` (ou `/docs` legado como fallback aceito).
   - Webhook Studio: rota `/webhook` (ou `/webhooks` legado como fallback aceito).
   - MCP Studio: rota `/mcp`.
   - Guia do Utilizador: rota `/docs` (ou `/docs/guia` legado).
2. Atualizar o teste unitário de prova que morde para validar que a ausência de qualquer um dos 4 pilares novos causa exit code 1.
