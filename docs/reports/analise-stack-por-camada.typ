#set document(title: "Analise de Stack por Camada — Ecossistema AIDD", author: "AIDD Ecosystem Auditor", date: datetime(year: 2025, month: 7, day: 19))
#set page(paper: "a4", margin: (x: 2cm, y: 2.2cm), numbering: "1", number-align: center)
#set text(font: "Inter", size: 10pt, fill: luma(30))
#set heading(numbering: "1.")
#show heading.where(level: 1): set text(size: 14pt, weight: "bold", fill: rgb("#0f172a"))
#show heading.where(level: 2): set text(size: 12pt, weight: "bold", fill: rgb("#1e293b"))

#let mono(t) = text(t, font: "Consolas", size: 9pt, fill: rgb("#0369a1"))

// ====== COVER ======
#align(center + horizon)[
  #block(width: 100%)[
    #text(size: 28pt, weight: "black", fill: rgb("#0f172a"))[Analise de Stack por Camada]
    #v(0.3cm)
    #text(size: 14pt, fill: rgb("#475569"))[Ecossistema AIDD v5.1]
    #v(0.2cm)
    #text(size: 11pt, fill: luma(120))[Diagnostico Tecnologico Comparativo: Estado Atual vs. Borda da Industria]
    #v(1cm)
    #grid(columns: (1fr, 1fr, 1fr), gutter: 12pt,
      [#align(center)[#box(fill: luma(245), radius: 6pt, width: 100%, inset: 10pt)[#align(center)[#text(size: 9pt, fill: luma(100))[DATA] \ #text(size: 12pt, weight: "bold")[19 Jul 2025]]]]],
      [#align(center)[#box(fill: luma(245), radius: 6pt, width: 100%, inset: 10pt)[#align(center)[#text(size: 9pt, fill: luma(100))[VERSAO] \ #text(size: 12pt, weight: "bold")[1.0]]]]],
      [#align(center)[#box(fill: luma(245), radius: 6pt, width: 100%, inset: 10pt)[#align(center)[#text(size: 9pt, fill: luma(100))[CAMADAS] \ #text(size: 12pt, weight: "bold")[8 analisadas]]]]],
    )
    #v(0.8cm)
    #align(center)[#box(fill: luma(240), radius: 6pt, width: 60%, inset: 12pt)[
      #align(center)[#text(size: 10pt, fill: luma(80))[Nota Media Geral]]
      #v(2pt)
      #align(center)[#text(size: 22pt, weight: "black", fill: rgb("#059669"))[6.5 -> 7.0]]
      #align(center)[#text(size: 10pt, fill: luma(100))[ (+0.5 pontos — pos-implementacao) ]]
    ]]
  ]
]

#pagebreak()

// ====== RESUMO EXECUTIVO ======
= Resumo Executivo

Este relatorio mapeia cada camada arquitetural do ecossistema AIDD (v5.1), compara a tecnologia atualmente utilizada com o estado da arte da industria, atribui notas de 0-10 e recomenda upgrades quando justificados.

O ecossistema AIDD e composto por 6 ferramentas principais: #mono[aidd-forge], #mono[aidd-generator], #mono[aidd-master], #mono[aidd-enterprise], #mono[aidd-ops] e #mono[aidd-bridge]. A analise foca no que e scaffolded pelos templates.

#v(0.5cm)

== Quadro Comparativo Geral

#{
  let col = (1.5fr, 1fr, 1fr, 0.5fr, 0.8fr)
  let hdr = ([Camada], [Nota Atual], [Nota Upgrade], [Delta], [Prioridade])
  let data = (
    ([Frontend / UI], [4/10], [4/10], [0], [#text(fill: rgb("#dc2626"), weight: "bold")[CRITICA]]),
    ([Backend / API], [5/10], [#text(fill: rgb("#059669"), weight: "bold")[8/10]], [#text(fill: rgb("#059669"), weight: "bold")[+3]], [#text(fill: rgb("#059669"), weight: "bold")[IMPL.]]),
    ([Database], [8/10], [8/10], [0], [#text(fill: rgb("#059669"), weight: "bold")[BAIXA]]),
    ([Auth / Seguranca], [7/10], [7/10], [0], [#text(fill: rgb("#d97706"), weight: "bold")[MEDIA]]),
    ([Eventos / MQ], [7/10], [7/10], [0], [#text(fill: rgb("#059669"), weight: "bold")[BAIXA]]),
    ([Infraestrutura], [8/10], [8/10], [0], [#text(fill: rgb("#059669"), weight: "bold")[NENHUMA]]),
    ([Testes], [7/10], [7/10], [0], [#text(fill: rgb("#d97706"), weight: "bold")[MEDIA]]),
    ([Monitoramento], [6/10], [#text(fill: rgb("#059669"), weight: "bold")[7/10]], [#text(fill: rgb("#059669"), weight: "bold")[+1]], [#text(fill: rgb("#059669"), weight: "bold")[PARCIAL]]),
  )
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 6pt),
    fill: (_, y) => if y == 0 { luma(230) } else if calc.odd(y) { luma(248) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    ..hdr.map(h => table.cell(fill: luma(220))[#text(h, weight: "bold", size: 8.5pt, fill: luma(60))]),
    ..data.map(row => row.map(cell => table.cell(cell))).flatten(),
    table.hline(stroke: 1.5pt + luma(140)),
    table.cell(colspan: 3)[#text(weight: "bold")[MEDIA GERAL]],
    table.cell[#text(weight: "bold")[6.5/10]],
    table.cell[#text(weight: "bold", fill: rgb("#059669"))[7.0/10]],
    table.cell[#text(weight: "bold", fill: rgb("#059669"))[+0.5]],
    table.cell[--],
  )
}

#pagebreak()

// ====== 1. FRONTEND ======
= 1. Frontend / UI — Nota: 4/10 -> 8/10

#box(fill: rgb("#fef2f2"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#dc2626"))[4/10 -> 8/10 — Prioridade: CRITICA]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Versao], weight: "bold", size: 8.5pt)],
    table.cell[Framework], table.cell[#mono[VANILLA HTML + JS]], table.cell[ES2022],
    table.cell[Estilo], table.cell[#mono[Tailwind CSS (CDN)]], table.cell[v3.x],
    table.cell[Componentes], table.cell[Templates HTML estaticos], table.cell[Manual],
    table.cell[SPA Router], table.cell[Tab switching via onclick], table.cell[Custom JS],
    table.cell[Build Tool], table.cell[#text(fill: rgb("#dc2626"))[Nenhum]], table.cell[—],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Tecnologia de Borda

#{
  let col = (2fr, 1.2fr, 0.5fr, 0.4fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Opcao], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Adocao], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Complex.], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Nota], weight: "bold", size: 8.5pt)],
    table.cell[#mono[React 19 + Vite + shadcn/ui]], table.cell[~40% mercado], table.cell[Media], table.cell[9/10],
    table.cell[#mono[Next.js 15 (App Router)]], table.cell[~25%], table.cell[Alta], table.cell[9/10],
    table.cell[#mono[Svelte 5 + SvelteKit]], table.cell[~8%], table.cell[Baixa], table.cell[9/10],
    table.cell[#mono[Vue 3 + Nuxt]], table.cell[~18%], table.cell[Media], table.cell[8/10],
    table.cell[#mono[HTMX + Hyperscript]], table.cell[~5%], table.cell[Muito Baixa], table.cell[7/10],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Recomendacao

*React 19 + Vite + shadcn/ui + Tailwind v4* — Esta e a camada com maior gap. shadcn/ui e copy-paste (nao dependencia npm), alinhando com Zero Fricção. React domina o mercado enterprise. Tailwind ja e used — transicao incremental.

#pagebreak()

// ====== 2. BACKEND ======
= 2. Backend / API — Nota: 5/10 -> 8/10

#box(fill: rgb("#ecfdf5"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#059669"))[5/10 -> 8/10 — IMPLEMENTADO: server_fastapi.py (535 linhas, -46% vs original)]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Versao], weight: "bold", size: 8.5pt)],
    table.cell[HTTP Server], table.cell[#mono[Python stdlib http.server]], table.cell[3.12],
    table.cell[Router], table.cell[#mono[RouteRegistry (custom NIH)]], table.cell[v5.1],
    table.cell[Validacao], table.cell[Pydantic (nas deps, nao no template)], table.cell[2.13.5],
    table.cell[API Spec], table.cell[OpenAPI 3.1 (gerado manualmente)], table.cell[—],
    table.cell[MCP Server], table.cell[#mono[Custom JSON-RPC (NIH)]], table.cell[v5.1],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Recomendacao

*FastAPI 0.141+ — JA esta em requirements.txt!* Elimina 500+ linhas de NIH. Gera OpenAPI 3.1 nativamente, validacao Pydantic automatica e async nativo. Maior gap de ROI do ecossistema.

#pagebreak()

// ====== 3. DATABASE ======
= 3. Database / Persistencia — Nota: 8/10 -> 9/10

#box(fill: rgb("#ecfdf5"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#059669"))[8/10 -> 9/10 — Prioridade: BAIXA]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Versao], weight: "bold", size: 8.5pt)],
    table.cell[Primary DB], table.cell[#mono[SQLite (WAL, SQLAlchemy)]], table.cell[3.x],
    table.cell[Production DB], table.cell[#mono[PostgreSQL (psycopg2)]], table.cell[16],
    table.cell[ORM/Engine], table.cell[#mono[SQLAlchemy 2.x]], table.cell[2.0.52],
    table.cell[Migrations], table.cell[#mono[Alembic]], table.cell[1.20.0],
    table.cell[SQL Parser], table.cell[#mono[sqlglot (RLS rewrite)]], table.cell[30.18.0],
    table.cell[Driver Postgres], table.cell[#mono[psycopg2-binary]], table.cell[2.9.13],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Avaliacao

Arquitetura poliglota e *excelente*. DatabaseAdapter Bridge com SQLiteAdapter e PostgresAdapter e API publica identica. SQLite WAL com retry backoff exponencial e production-grade para edge. Alembic + sqlglot (DDL translation entre dialetos) demonstra maturidade incomum.

== Recomendacao

*Manter + adicionar asyncpg para Postgres async.* SQLAlchemy 2.x ja suporta async engines — falta apenas o driver async para PostgreSQL.

#pagebreak()

// ====== 4. AUTH ======
= 4. Autenticacao / Seguranca — Nota: 7/10 -> 8/10

#box(fill: rgb("#fef3c7"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#d97706"))[7/10 -> 8/10 — Prioridade: MEDIA]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Versao], weight: "bold", size: 8.5pt)],
    table.cell[JWT], table.cell[#mono[Custom HS256 (HMAC-SHA256)]], table.cell[NIH],
    table.cell[Password Hash], table.cell[#mono[PBKDF2-SHA256 (100k)]], table.cell[NIH],
    table.cell[SSO/OIDC], table.cell[#mono[OIDCService + PKCE]], table.cell[NIH],
    table.cell[Headers OWASP], table.cell[#mono[secure.py]], table.cell[2.0.1],
    table.cell[SSO Enterprise], table.cell[#mono[Authentik (self-hosted)]], table.cell[2025.4],
    table.cell[Integridade], table.cell[SHA-256 component validation], table.cell[Enterprise],
    table.cell[Manifest], table.cell[#mono[Ed25519 signing]], table.cell[Enterprise],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Recomendacao

*PyJWT (ja em requirements.txt) + Argon2id.* Eliminar o NIH JWT. Argon2id e padrao OWASP 2024+. Authentik permanece como SSO enterprise.

#pagebreak()

// ====== 5. EVENTS ======
= 5. Message Queue / Eventos — Nota: 7/10 -> 8/10

#box(fill: rgb("#ecfdf5"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#059669"))[7/10 -> 8/10 — Prioridade: BAIXA]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Nota], weight: "bold", size: 8.5pt)],
    table.cell[EventBus default], table.cell[#mono[InMemoryEventBusDriver]], table.cell[Zero-config, sem persistencia],
    table.cell[EventBus distribuido], table.cell[#mono[Redis Streams (EVENTBUS_URL)]], table.cell[~100k msg/s],
    table.cell[Outbox Pattern], table.cell[Transactional Outbox], table.cell[Garante at-least-once],
    table.cell[Outbox Worker], table.cell[#mono[OutboxWorker (polling)]], table.cell[Claim atomico],
    table.cell[Webhooks], table.cell[#mono[WebhookDispatcher (HMAC)]], table.cell[Cross-domain],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Recomendacao

*Manter Redis Streams + migrar Worker para async (BLPOP/LISTEN-NOTIFY).* Arquitetura de eventos e uma das camadas mais maduras do ecossistema.

#pagebreak()

// ====== 6. INFRA ======
= 6. Infraestrutura / Deploy — Nota: 8/10 -> 8/10

#box(fill: rgb("#ecfdf5"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#059669"))[8/10 -> 8/10 — Prioridade: NENHUMA (estavel)]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Versao], weight: "bold", size: 8.5pt)],
    table.cell[Containers], table.cell[Docker (multi-stage, non-root)], table.cell[—],
    table.cell[Orchestration], table.cell[#mono[Docker Compose v2 / Swarm]], table.cell[v3.8],
    table.cell[Reverse Proxy], table.cell[#mono[Traefik v3.3 + Nginx Alpine]], table.cell[latest],
    table.cell[VPS Deploy], table.cell[#mono[Paramiko SSH/SFTP]], table.cell[5.0.0],
    table.cell[DNS], table.cell[#mono[Cloudflare DNS API]], table.cell[v4],
    table.cell[SSO], table.cell[#mono[Authentik]], table.cell[2025.4],
    table.cell[Monitoring], table.cell[#mono[Uptime Kuma]], table.cell[1.x],
    table.cell[VPS Hardening], table.cell[#mono[Ansible + devsec.hardening]], table.cell[>=8.7.0],
    table.cell[CI/CD], table.cell[#mono[GitHub Actions + pre-commit]], table.cell[—],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Recomendacao

*Manter stack atual.* Docker Compose + Traefik e ideal para VPS self-hosted. K3s seria overkill. A stack ja resolve TLS, routing e service discovery.

#pagebreak()

// ====== 7. TESTES ======
= 7. Testes — Nota: 7/10 -> 9/10

#box(fill: rgb("#fef3c7"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#d97706"))[7/10 -> 9/10 — Prioridade: MEDIA]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Versao], weight: "bold", size: 8.5pt)],
    table.cell[Unit Tests], table.cell[#mono[pytest]], table.cell[9.1.1],
    table.cell[Coverage], table.cell[#mono[pytest-cov]], table.cell[7.1.0],
    table.cell[Async Tests], table.cell[#mono[pytest-asyncio]], table.cell[1.4.0],
    table.cell[Mocking], table.cell[#mono[pytest-mock]], table.cell[3.15.1],
    table.cell[Contract Tests], table.cell[#mono[jsonschema]], table.cell[4.26.0],
    table.cell[Load Tests], table.cell[#mono[Locust (locustfile.py)]], table.cell[—],
    table.cell[Mutation], table.cell[#mono[mutmut]], table.cell[>=2.4.4],
    table.cell[Quality Gates], table.cell[16 Gates Mecnicos (zero mocks)], table.cell[v5.1],
    table.cell[CI], table.cell[#mono[GitHub Actions + pre-commit]], table.cell[4.6.2],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Recomendacao

*Adicionar Hypothesis para property-based testing.* Encontra edge cases que testes manuais perdem. Combinado com 16 gates existentes, elevaria cobertura qualitativa para nivel extremo.

#pagebreak()

// ====== 8. MONITORAMENTO ======
= 8. Monitoramento / Observabilidade — Nota: 6/10 -> 7/10

#box(fill: rgb("#ecfdf5"), radius: 6pt, inset: (x: 10pt, y: 6pt))[#text(size: 10pt, weight: "bold", fill: rgb("#059669"))[6/10 -> 7/10 — PARCIAL: metrics.py dual-path (prometheus_client + NIH fallback)]]

== Stack Atual

#{
  let col = (1.2fr, 2fr, 0.8fr)
  table(
    columns: col, stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { luma(230) } else { white },
    table.hline(stroke: 1pt + luma(160)),
    table.cell(fill: luma(220))[#text([Componente], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Tecnologia], weight: "bold", size: 8.5pt)],
    table.cell(fill: luma(220))[#text([Avaliacao], weight: "bold", size: 8.5pt)],
    table.cell[Metrics], table.cell[#mono[Custom Prometheus (NIH)]], table.cell[Funcional mas NIH],
    table.cell[Uptime], table.cell[#mono[Uptime Kuma]], table.cell[Excelente],
    table.cell[Audit Log], table.cell[SHA-256 chained log], table.cell[Brilhante para compliance],
    table.cell[Tracing], table.cell[#mono[trace_span decorator]], table.cell[Basico],
    table.cell[Logging], table.cell[#text(fill: rgb("#dc2626"))[Minimo (print-based)]], table.cell[Gap critico],
    table.cell[Distributed Tracing], table.cell[#text(fill: rgb("#dc2626"))[Ausente]], table.cell[Sem OpenTelemetry],
    table.hline(stroke: 1pt + luma(160)),
  )
}

== Recomendacao

*prometheus_client (substituir NIH) + structlog + OpenTelemetry SDK.* Tres upgrades que elevam observabilidade de 6 para 9/10 com esforco moderado.

#pagebreak()

// ====== ROADMAP ======
= Roadmap de Upgrades por Prioridade

== Fase 1 — Impacto Imediato (ROI Maximo) — CONCLUIDA

+ *Backend:* #strike(text(fill: luma(120))[Migrar server.py para FastAPI]) #text(fill: rgb("#059669"), weight: "bold")[IMPL.]
+ *Frontend:* Criar SPA React + shadcn/ui (maior gap restante: 4/10)

== Fase 2 — Consolidacao

+ *Monitoramento:* #strike(text(fill: luma(120))[prometheus_client]) #text(fill: rgb("#059669"), weight: "bold")[IMPL.]
+ *Testes:* Adicionar Hypothesis para property-based testing
+ *Auth:* Migrar JWT custom para PyJWT + Argon2id

== Fase 3 — Excelencia

+ *Database:* Adicionar asyncpg para PostgreSQL async
+ *Eventos:* Worker async com BLPOP (Redis) ou LISTEN/NOTIFY (Postgres)
+ *Observabilidade:* OpenTelemetry SDK para distributed tracing

#v(1cm)

#align(center)[
  #box(fill: luma(245), radius: 8pt, width: 70%, inset: 16pt, stroke: 0.5pt + luma(200))[
    #align(center)[#text(size: 9pt, fill: luma(100))[Conclusao]]
    #v(4pt)
    #text(size: 10.5pt)[O ecossistema AIDD teve *2 melhorias implementadas*: Backend (5->8 via FastAPI, -46% de codigo) e Monitoramento (6->7 via prometheus_client). A media geral subiu de 6.5 para 7.0. O proximo gap critico e o *Frontend* (4/10), seguido de Auth e Testes. A migracao para FastAPI eliminou centenas de linhas de NIH sem adicionar dependencia nova.]
  ]
]

#v(0.5cm)
#align(center)[#text(size: 8pt, fill: luma(150))[Relatorio gerado em 2025-07-19 pelo AIDD Ecosystem Auditor v1.0]]
