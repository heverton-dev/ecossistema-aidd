# Item 3 — templates-servidores-core-master-enterprise

> **Escopo:** Ajustar servidores templates e modulos core para servir Swagger em /api, Webhooks em /webhook, MCP em /mcp e Guia em /docs.
> **Status:** [EM EXECUCAO]

---

## Arquivos Alvo

- `componentes/compartilhado/src-core/server.py`
- `componentes/compartilhado/src-core/openapi.py`
- `tools/aidd-master/src/server.py`
- `tools/aidd-master/src/core/server.py`
- `tools/aidd-master/src/core/openapi.py`
- `tools/aidd-enterprise/src/server.py`
- `tools/aidd-enterprise/src/core/server.py`
- `tools/aidd-enterprise/src/core/openapi.py`

## Metadados do Ticket

- **Blocked By:** TICKET-02
- **Comando de Validação:**
  ```bash
  python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py
  ```

## Contexto e Definição de Pronto

1. No `server.py` e `openapi.py`, adicionar a rota `/api` para a documentação interativa Swagger.
2. Adicionar redirect `/docs` para o Guia do Utilizador (ou `/api` para Swagger se não houver guia separado).
3. Adicionar `/webhook` além de `/webhooks`.
4. Garantir paridade e ausência de drift entre `aidd-master` e `aidd-enterprise`.
