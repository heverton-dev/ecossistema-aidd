# Épico de Engenharia: Nova Taxonomia do Quarteto Sine Qua Non

> **Identificador:** `EPICO-QUARTETO-TAXONOMIA-001`  
> **Data:** 21-09-2026  
> **Status:** Concluído (100% Executado e Validado)  
> **Governança:** Lei #1 (Determinismo), Lei #2 (Qualidade Binária), Lei #10 (Quarteto Sine Qua Non Dinâmico), Lei #13 (Todo Portão Prova que Morde)

---

## 1. Contexto e Motivação

O **Quarteto Sine Qua Non** (Lei Inviolável #10) exige que toda aplicação gerada ou evoluída no ecossistema entregue nativamente 4 pilares autônomos.  
A taxonomia histórica utilizava:
- `/docs` para a documentação técnica interativa da API (Swagger UI).
- `/webhooks` para o painel e simulação de eventos externos.
- `/mcp` para o servidor de integração com modelos de IA.
- `/docs/guia` ou `/guia` para o manual do utilizador humano.

### A Nova Taxonomia Canônica
A convenção adotada agora promove uma separação semântica natural e elegante:

| Pilar | Nova Rota Canônica | Rota Legada (Compat) | Finalidade |
|---|---|---|---|
| **1. API Studio** | `/api` | `/docs` (redirect) | Documentação interativa OpenAPI 3.1 / Swagger Studio de todos os endpoints REST. |
| **2. Webhook Studio** | `/webhook` | `/webhooks` | Gestão, subscrição e simulação de webhooks e eventos do sistema. |
| **3. MCP Studio** | `/mcp` | `/mcp` | Servidor Model Context Protocol nativo para conexão direta de agentes e LLMs. |
| **4. Central de Docs**| `/docs` | `/docs/guia` | Guia do Utilizador humano, manuais de operação e documentação conceitual. |

---

## 2. Grafo Topológico de Execução (Kahn DAG)

```
[01: Governança & Leis]
         │
         ▼
[02: Quality Gates & Testes]
         │
         ▼
[03: Núcleo & Servidores Templates]
         │
         ▼
[04: Deliverables & Exemplos]
         │
         ▼
[05: Livros & Sincronismo Multi-Harness]
```

---

## 3. Tabela de Tickets Atômicos

| Ticket | Arquivo | Responsabilidade | Status |
|---|---|---|---|
| `TICK-001` | [01-governanca-leis-agents-memory.md](01-governanca-leis-agents-memory.md) | Atualizar Lei #10 em `AGENTS.md`, `MEMORY.md` e referências canônicas. | `todo` |
| `TICK-002` | [02-quality-gates-quarteto-contract-rot.md](02-quality-gates-quarteto-contract-rot.md) | Atualizar `G_QUARTETO_SINE_QUA_NON.py`, `G_CONTRACT_ROT.py` e testes prova que morde. | `todo` |
| `TICK-003` | [03-templates-servidores-core-master-enterprise.md](03-templates-servidores-core-master-enterprise.md) | Atualizar rotas em `src/server.py`, `componentes/` e templates das ferramentas. | `todo` |
| `TICK-004` | [04-projetos-referencia-e-exemplos.md](04-projetos-referencia-e-exemplos.md) | Atualizar rotas nos exemplos canônicos (`enterprise-suite-v4`, etc.). | `todo` |
| `TICK-005` | [05-livros-documentacao-e-sincronismo.md](05-livros-documentacao-e-sincronismo.md) | Recompilar livros corporativos e sincronizar componentes multi-harness. | `todo` |
