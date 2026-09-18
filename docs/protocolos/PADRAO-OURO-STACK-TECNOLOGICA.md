# Padrão-Ouro de Stack Tecnológica (Lei Inviolável #11)

> **Origem:** definido durante a validação end-to-end real em
> `C:\Users\trcnologia\Desktop\proj_ctt\planos-ctt-app` (Sistema de Gestão
> Logística CTT). Esse projeto é a referência viva do padrão — em caso de
> dúvida sobre uma camada não coberta aqui, inspecionar o código real lá,
> nunca supor.
>
> **Escopo:** vale para TODOS os fluxos e ferramentas do ecossistema
> (`aidd-generator`, `aidd-master`, `aidd-factory`, `aidd-bridge`, e
> qualquer nova ferramenta futura) e para TODAS as camadas de todo projeto
> gerado ou evoluído.
>
> **Regra de exceção (única):** a stack abaixo só é substituída se o
> **plano estruturado** (`PLANNER.json`/`PLANO-EXECUCAO-ESTRUTURADO.json`)
> ou o **prompt do usuário** especificar outra stack de forma explícita
> para aquela camada. Silêncio do usuário nunca é licença para usar outra
> coisa — o padrão-ouro é sempre o default.

## Stack por camada

| Camada | Tecnologia obrigatória (default) | Evidência em `proj_ctt` |
|---|---|---|
| **Frontend** | Next.js (App Router) + TypeScript + Tailwind CSS | `frontend/` — `next.config.js`, `tailwind.config.ts`, `tsconfig.json`, `app/` |
| **Backend** | Python puro, 100% determinístico onde possível | `src/core/server.py` |
| **Database** | SQLite em modo WAL (alta concorrência) | `src/core/database.py`, `app.db` |
| **API** | OpenAPI 3.1 nativo — Swagger Studio em `/swagger` | `src/core/openapi.py`, `src/core/swagger.html` |
| **Webhook** | Webhook Studio nativo em `/webhooks` | `src/core/webhooks.py`, `src/core/webhook_studio.html` |
| **MCP** | MCP Studio nativo em `/mcp` | `src/core/mcp_server.py`, `src/core/mcp_studio.html` |
| **Documentação** | Guia/Documentação do Utilizador nativo em `/docs` | Quarteto Sine Qua Non (ver Lei #10 do `AGENTS.md` raiz) |

O Frontend (Next.js/TS/Tailwind) é gerado a partir do OpenAPI da própria
API (tipagem derivada dos contratos, zero divergência manual) — mecanismo
real já implementado como `nextjs_exporter.py` (`proj_ctt`) e
`tools/aidd-master/scripts/openapi_to_ts.py` + comando
`aidd-master export-frontend --stack nextjs`.

## Versões de referência (`frontend/package.json` em `proj_ctt`)

```json
{
  "dependencies": { "next": "^14.2.5", "react": "^18.3.1", "react-dom": "^18.3.1" },
  "devDependencies": {
    "typescript": "^5.4.5",
    "tailwindcss": "^3.4.4",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19"
  }
}
```

## O que isso substitui

O "Super-App" HTML gerado dinamicamente em Python puro
(`generate_superapp_index_html()` em `compose_suite.py`, e o
`templates/core/index.html` estático usado por `provision_project.py`)
**não é o padrão-ouro** e não deve ser o frontend final entregue por
nenhum fluxo. Ele só é aceitável como:

- fallback interno enquanto uma camada de frontend real não foi gerada, ou
- resultado final **apenas se o usuário pedir expressamente** um frontend
  simples/embutido em vez de Next.js.

## Achado real (17/09/2026 — validação E2E do Fluxo 01)

Hoje, `aidd-generator` (Fase 5/6) e `aidd-master`
(`provision_project.py`, `compose_suite.py`, `add_module.py`) geram o
Super-App em Python como frontend **padrão** de todo projeto novo, e
`export-frontend`/`nextjs_exporter.py` existem mas são um passo **manual
separado**, nunca disparado automaticamente por `init`/`add-module`/
`compose`. Isso viola esta lei. Pendência registrada para correção nos
pipelines geradores (fora do escopo da sessão que documentou esta regra —
ver `docs/teste-end-to-end/17-09-2026_relatorio-testes-triade-fluxos-1-2-3.md`).
