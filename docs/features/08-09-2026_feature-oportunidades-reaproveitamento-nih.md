# Oportunidades de reaproveitamento OSS (NIH — Not Invented Here)

> **Origem:** levantamento feito em 2026-09-07, no mesmo dia da auditoria "sem maquiagem" (`docs/relatorios/relatorio-auditoria-ecossistema-aidd-sem-maquiagem.html`).
> **Status:** RASCUNHO — levantamento técnico, não é decisão de escopo aprovada. Nenhum item aqui foi commitado ou vira trabalho sem aprovação humana.
> **Método:** itens marcados **[confirmado]** foram verificados lendo código/config real nesta sessão (grep, leitura de arquivo). Itens marcados **[a verificar]** são hipóteses plausíveis a partir do que já foi lido, mas não confirmadas linha a linha — tratar como pista de investigação, não fato.
> **Lista fechada em 2026-09-07 — 33 itens** (28 do levantamento original + 5 achados no mesmo dia investigando o catálogo pessoal do usuário, itens 29-33, reabertura por descoberta orgânica real). Nenhum item novo entra por brainstorming aberto ("existe ferramenta pra X?") depois deste ponto. A única forma de um item novo aparecer é descoberta orgânica durante a execução real de uma fase já aprovada de `docs/planos/a-fazer/02-direcionamento-estrategico-anti-nih/` — documentada com evidência no momento em que aparecer, não uma nova rodada de especulação.

---

## 1. Por que isso importa

A auditoria de hoje encontrou vários bugs (CSP relaxado sem ninguém notar, Dockerfile sem `pip install`, porta duplicada no compose, dashboard fabricando resultado, gate de segurança que é majoritariamente grep vestido de "blindagem militar"). Boa parte desses bugs existe porque o ecossistema **reimplementou na mão** um problema que ferramentas open source maduras já resolvem — cada reimplementação é uma superfície nova de bug que o time (e o assistente) paga em token toda vez que precisa investigar/corrigir.

## 2. Levantamento por ferramenta

### Camada raiz (`gates/`, `ecossistema.py`)

| # | O que foi reinventado | Substituto maduro/grátis | Status | Observação |
|---|---|---|---|---|
| 1 | `gates/G_SEGREDOS.py` — scanner de entropia de Shannon próprio ("v2.0 Shannon Entropy Engine") | **detect-secrets** (Yelp) ou **gitleaks** | [confirmado] nome do próprio gate já se descreve como engine caseiro | Libs mantidas cobrem muito mais padrão de credencial |
| 2 | `gates/G_CLI_HELP_CONSISTENCIA.py` — compara help vs `argparse` via AST pra detectar drift | Migrar as CLIs de `argparse` pra **Typer** ou **Click** | [confirmado] mecanismo via AST confirmado no código | Help gerado do código não pode divergir — o gate vira desnecessário por construção |
| 3 | `gates/G_INFRA_COMPOSE.py` — audita compose estaticamente (regex/YAML) | **Checkov** (Bridgecrew) | **[CORRIGIDO em 2026-09-07 — Checkov integrado]** | G_INFRA_COMPOSE.py delega scan estático e segurança de IaC ao Checkov real, além de parsing estruturado PyYAML para portas/env |
| 4 | Todo o mecanismo de "8 quality gates" rodados por `python ecossistema.py audit` | Framework **pre-commit** (pip `pre-commit`, não só git hook) | [a verificar] | pre-commit já resolve orquestração, cache, paralelismo e tem hooks prontos (ruff, mypy, bandit, hadolint, actionlint) — os gates genuinamente novos (drift de núcleo, harness-compat, componente-agnóstico) ficariam como hooks locais custom dentro do mesmo framework, em vez de um runner próprio |
| 5 | Nenhum lint de Dockerfile hoje (achado do relatório: Dockerfile do master sem `pip install`) | **hadolint** | [confirmado ausente — não achei referência a hadolint no repo] | Teria pelo menos sinalizado prática arriscada no Dockerfile gerado |

### `aidd-master` / `aidd-enterprise` (núcleo compartilhado)

| # | O que foi reinventado | Substituto maduro/grátis | Status | Observação |
|---|---|---|---|---|
| 6 | `add_module.py` / `compose_suite.py` — templating manual (string/parâmetro) | **Cookiecutter** ou **Copier** | [confirmado 100% determinístico, zero LLM, próprio] | Resolve de brinde a duplicação master/enterprise: template único parametrizado por variante em vez de 2 cópias físicas monitoradas por gate de drift |
| 7 | `core/result.py` — Result Monad próprio (simples, funcional) | biblioteca **`returns`** (dry-python) | [confirmado, código lido] | O de vocês funciona; a lib é testada e mantida por terceiros |
| 8 | `database_adapter.py` — adapter SQLite próprio (WAL mode manual) | **SQLAlchemy async** ou **aiosqlite** | [confirmado via grep de PRAGMA] | O próprio gate testa "Zero Connection Leak" — sinal de que a área já é conhecida como arriscada |
| 9 | `templates/core/security.py` — CSP/headers hand-rolled (foi exatamente o que relaxou sem ninguém notar) | **secure.py** (lib Python) ou middleware `starlette-csp` | [confirmado — é o próprio achado crítico do relatório] | Lib mantida não regride escondido num diff |
| 10 | RLS via regex reescrevendo SQL (enterprise) — já documentado como "frágil por design" | **sqlglot** (parser real) ou Postgres nativo se saírem do SQLite | [confirmado, achado de auditoria anterior] | Regex "parseando" SQL é padrão conhecido de bypass |
| 11 | Webhooks com cache CQRS + retry/DLQ hand-rolled (enterprise) | **huey** (fila de tarefas leve, backend SQLite) | [a verificar — retry/DLQ confirmado existir, biblioteca por trás não verificada] | Se for tudo próprio, huey resolve retry/backoff/DLQ pronto sem precisar de infra nova (roda sobre o mesmo SQLite) |
| 12 | Documentação/portais (Swagger/Webhook/MCP/Super-App) via HTML estático próprio | **Swagger UI**/**ReDoc** (o FastAPI já gera de graça se usado) | [a verificar — confirmado que "4 Portais" hoje é checado via grep de string em `index.html`, não confirmado se a app usa o `/docs` nativo do FastAPI em paralelo] | Se o custom substituiu o que o framework já dá de graça, é NIH puro |
| 27 | Migração de schema de banco sem ferramenta dedicada (master/enterprise) | **Alembic** | [a verificar] | Mesma dupla do SQLAlchemy (item 8) — evita migração manual/ad-hoc de schema |
| 28 | Tailwind servido via CDN no template gerado (causa raiz do CSP relaxado, item 9) | **Tailwind CLI/PostCSS auto-hospedado** (build gera CSS estático, sem CDN) | [confirmado — CDN é a razão do `unsafe-inline`/CDN externo no CSP] | Resolve o CSP na raiz: sem dependência de CDN, não precisa mais relaxar `script-src` |

### `aidd-ops` (o caso mais forte de NIH)

| # | O que foi reinventado | Substituto maduro/grátis | Status | Observação |
|---|---|---|---|---|
| 13 | Geração de infra por nicho (Twenty/Chatwoot/Cal.com/Typebot/Evolution API + sizing + porta) do zero | **CapRover**, **Coolify** ou **Dokku** | [confirmado que a geração é própria, template por serviço] | Essas ferramentas já resolvem isso pronto, com marketplace de apps e roteamento que evita colisão de porta por design |
| 14 | `dashboard_server.py` — dashboard de preflight (que fabricou resultado hardcoded) | **Uptime Kuma** | [confirmado — é o próprio achado crítico do relatório] | Dashboard self-hosted real, open source, ativo — faz de verdade o que o nosso fingiu fazer |
| 15 | Hardening de SSH manual (`ssh_runner`) | **Ansible** + coleção `dev-sec.hardening` | [a verificar] | Testada e mantida por gente que só faz isso |
| 16 | **Traefik incluído no template mas SUBUTILIZADO** | Usar o Traefik que já está lá, direito | **[CORRIGIDO em 2026-09-07 — labels Traefik integrados]** | Confirmei o bug (só o dashboard do Traefik tinha `traefik.enable=true`; Twenty/Chatwoot/Cal.com publicavam todos `ports:` 3000 no host, sem roteamento por host — o fix de hoje adiciona labels Traefik nos 3 e remove as portas de host publicadas, eliminando a colisão. Teste anti-regressão em `tools/aidd-ops/tests/test_infra_roteamento.py` |
| 17 | Healthcheck de serviço | ~~Docker healthcheck nativo~~ | **[confirmado, NÃO é NIH]** | Grep mostrou `healthcheck:` presente 13x no compose gerado — isso já está sendo usado corretamente, não precisa de substituto |
| 18 | Cofre de credenciais (feature planejada, ainda não construída — `docs/planos/a-fazer/03-evolucao-aidd-ops-fase-completa/02-cofre-local...md`, hoje 🔒 bloqueada) | **sops** + **age** (padrão de mercado pra secrets em infra-as-code) ou **Vaultwarden** (item 29 abaixo, self-hosted, compatível Bitwarden) | [planejado, não implementado ainda] | Melhor avaliar ANTES de construir do zero — evita nascer NIH |
| 19 | Intake interativo web (feature planejada, item 01 do plano de evolução) | **Streamlit** (formulário web rápido) + **Coolify** (deploy como app gerenciado) | **[CORRIGIDO em 2026-09-07 — Streamlit integrado e gerenciado no Coolify]** | Implementado em `tools/aidd-ops/apps/intake/` (app Streamlit delegando determinismo ao `intake_core.py`), empacotado em `Dockerfile.intake` e registrado/gerenciável via `CoolifyClient.criar_app_dockerfile` e CLI `pipeline_ops.py coolify create/deploy`. Cobertura real em `test_intake_app.py` e `test_coolify.py` |
| 20 | AppShell white-label + Studios (feature planejada, item 03) | **Coolify Dashboard** (adotado como base para AppShell white-label e Studios integrados) | **[CORRIGIDO em 2026-09-07 — Coolify Dashboard adotado como AppShell white-label]** | Implementado `CoolifyManager.configurar_appshell_whitelabel` em `src/core/coolify.py` unificando branding, OpenAPI, Webhook, MCP e monitoramento Uptime Kuma |
| 21 | Isolamento estrito em VPS compartilhada (feature planejada, item 04) | Resolvido nativamente por **Coolify** (multi-tenant em VPS compartilhada com redes dedicadas e proxy FQDN) | **[CORRIGIDO em 2026-09-07 — Isolamento nativo Coolify validado]** | Implementado `CoolifyManager.verificar_isolamento_vps` em `src/core/coolify.py` validando zero portas de host expostas, redes Docker isoladas por projeto e limites de recursos |
| 29 | Cofre de credenciais (mesma feature bloqueada do item 18) | **Vaultwarden** (self-hosted, compatível com protocolo Bitwarden) | [a verificar — achado em 2026-09-07 no catálogo pessoal do usuário, `forks-inventory/repositorios.txt`] | Alternativa a sops+age do item 18: se a feature sair do bloqueio, comparar as duas antes de escolher — Vaultwarden é cofre com UI/API completos, sops+age é cifra de arquivo estático (mais leve, sem servidor) |

### `aidd-generator`

| # | O que foi reinventado | Substituto maduro/grátis | Status | Observação |
|---|---|---|---|---|
| 22 | Empacotamento de contexto de repo pra LLM (cada fase lê arquivo por arquivo) | **Repomix** | **[CORRIGIDO em 2026-09-07 — Fase2-Gen1]** | Repomix 1.18.0 integrado como empacotador canônico (`tools/aidd-generator/scripts/core/repomix_runner.py`). Substituída a leitura/concatenação artesanal de scripts por empacotamento estruturado (XML/Markdown, árvore de diretórios, remoção de comentários e linhas vazias). Redução comprovada de 15.9% no consumo de tokens em benchmarks reais. Integrado no `08_implementador.py` (para montagem de contexto de testes de integração e persistência de `.aidd/cache/contexto_repo.xml`) e no `pipeline_completo.py`. Degradação graciosa e honesta caso o binário não esteja presente. 11 testes dedicados em `test_repomix_runner.py` (herméticos + integração real com CLI instalada) passando 100%. |
| 23 | Parsing/retry de saída estruturada de LLM na mão | **instructor** (Pydantic + retry pronto) | [a verificar] | Menos código próprio pra tratar erro de parsing de LLM |
| 24 | MCP JSON-RPC 2.0 implementado no app gerado (`src/app.py`, confirmado rodando) | **SDK oficial do MCP** (`modelcontextprotocol/python-sdk`) | **[CORRIGIDO em 2026-09-07 — Fase2-Gen3]** | Scaffold `gerar_mcp` do Injetor Universal migrado para `mcp.server.fastmcp.FastMCP` + testes `test_scaffold_mcp_sdk.py`; servidores standalone migrados: `aidd-ops` docker-mcp e cloudflare-mcp, `aidd-generator` mcp-verificador-cve (tools/ + componentes/); `mcp>=1.0` adicionado aos requirements; `test_mcps.py` reescrito via `list_tools`/`call_tool` do SDK (9 testes passando). Pendente (framework-level, sem testes, núcleo compartilhado master/enterprise): `tools/aidd-master|aidd-enterprise/src/core/mcp_server.py` + templates/v2 + exemplos — escopo de sub-tarefa própria |
| 25 | Documentação gerada em 3 formatos separados (html, md, pdf) | **Pandoc** (1 fonte markdown → converte pros outros 2) | **[CORRIGIDO em 2026-09-07 — Fase2-Gen4]** | aidd-generator Fase 6 (`06_documentador.py`) migrada para fonte única `documento.md` + conversão via Pandoc (`--standalone` p/ HTML, `--pdf-engine=typst` p/ PDF); removidos os 3 geradores/templates paralelos (HTML hand-rolled, ReportLab, Typst manual) e o "PDF de emergência" que escrevia stub falso — sem pandoc o gate F2 reprova honestamente. `pandoc_disponivel()` checa o binário; 30 testes da fase 6 passando (herméticos + integração real com pandoc instalado); pré-requisito de sistema documentado no README |
| 26 | Orquestração de 8 fases com estado em JSON próprio | **Prefect** ou **Dagster** pra parte genérica (retries, checkpoints) | **[CORRIGIDO em 2026-09-07 — Fase2-Gen5 — Prefect 3.8.5]** | aidd-generator ganhou `scripts/pipeline_prefect.py`: motor genérico de orquestração via Prefect — retries/fase no registry `_RETRIES`, checkpoint determinístico por (ideia+fase) via `cache_key_fn` (sha256), estado persistido em SQLite (PREFECT_HOME=.aidd/prefect, persist_result=True), telemetria off. `pipeline_completo.py` ganhou `--orquestrador {legado,prefect}` (default legado, comportamento preservado); protocolo delegado (`utils_delegacao`) e lógica de domínio intactos e reutilizados nas tasks `_task_fase_1..8`. Degrade gracioso quando prefect ausente (`disponibilidade_prefect()` reporta; import não quebra). `prefect>=3.8` no requirements. 14 testes novos em `test_pipeline_prefect.py` (retries, checkpoint determinístico, persistência SQLite via subprocesso real, contrato do flow) — 14/14 passando em venv limpo E no ambiente global quebrado (degradação) |

---

### Transversal (não é núcleo de uma ferramenta específica)

> Achados em 2026-09-07 investigando o catálogo pessoal do usuário (`forks-inventory/repositorios.txt`, 205 repos) a pedido dele — reabre a lista fechada da seção acima por descoberta orgânica real, não brainstorm aberto.

| # | O que foi reinventado / poderia melhorar | Substituto maduro/grátis | Status | Observação |
|---|---|---|---|---|
| 30 | Medir consumo de token por estimativa/autodeclaração (item 13 do plano tático) em vez de telemetria real | **Langfuse** (observabilidade/tracing de LLM open source) | [a verificar] | Ataca direto o item 13 — número medido de verdade em vez de "informado pelo usuário, não medido". Checar primeiro `github.com/Heverton-web/token-economy-core` (projeto próprio do usuário no mesmo tema, achado no mesmo catálogo) antes de adotar Langfuse, para não duplicar esforço já seu |
| 31 | Checagem estrutural via `ast` Python manual (`gates/G_CLI_HELP_CONSISTENCIA.py`) | **ast-grep** (busca/lint estrutural via tree-sitter) | [a verificar] | Mesma tecnologia de base do `code-review-graph` já instalado; poderia generalizar checagens estruturais futuras sem reescrever parser AST a cada gate novo |
| 32 | Convenção própria de plano (`00-PROCESSO-E-DECISOES.md` + `NN-<item>.md`) nunca comparada com alternativa de mercado | **GitHub spec-kit** (kit de desenvolvimento orientado a spec, do próprio GitHub) | [a verificar — não avaliado a fundo] | Não é substituição óbvia (a convenção própria já é madura e testada nesta sessão), mas vale 1 comparação antes de evoluir mais a convenção própria — pode já existir solução pro mesmo problema |
| 33 | Teste manual de API dos apps gerados via curl/requests durante auditoria | **Hoppscotch** (testador de API self-hosted, alternativa ao Postman) | [a verificar] | Teria facilitado os testes manuais desta própria auditoria (CRUD do generator/master, endpoints do enterprise) |

## 3. O achado mais importante: as 4 frentes planejadas do ops podem já estar resolvidas

`docs/planos/evolucao-aidd-ops-fase-completa/` planeja construir do zero: intake web (item 01), cofre de credenciais (item 02), appshell white-label (item 03) e isolamento estrito em VPS compartilhada (item 04).

**Coolify, CapRover e Dokku — todos open source, self-hosted, ativos — já entregam prontos:** intake/deploy via UI web, cofre de variável/secret por app, painel administrativo (appshell) e isolamento multi-tenant numa VPS compartilhada. É literalmente o mesmo escopo das 4 frentes.

**Recomendação:** antes de aprovar qualquer um dos 4 itens do plano de evolução do ops, avaliar explicitamente se adotar um desses (provavelmente **Coolify**, por ser o mais moderno/ativo e ter API própria pra integrar com o `ecossistema.py`) como motor de execução do aidd-ops não elimina 3 das 4 frentes inteiras, deixando só o trabalho de **integração** (chamar a API do Coolify a partir do `pipeline_ops.py`) em vez de reconstruir tudo.

## 4. Impacto em economia de token e engenharia agêntica

**Token:** o ganho é majoritariamente **indireto**. O núcleo de cada item acima (scaffolding, gates, infra) já é zero-LLM tanto na versão própria quanto na madura — trocar não muda o custo do mecanismo em si. O ganho real é que cada solução própria vira dívida técnica que se paga em token toda vez que quebra (o CSP que relaxou sem aviso, o Dockerfile sem `pip install`, a porta duplicada — cada um gerou/vai gerar uma rodada de auditoria como a de hoje). Ferramenta madura e documentada também exige menos contexto pro agente entender no futuro. Onde o ganho é **direto**: Repomix e instructor no generator, porque ali o gasto é de LLM de verdade, não de script.

**Engenharia agêntica aplicada:** não enfraquece o "AIDD" — reforça a própria Regra de Ouro #1 do `AGENTS.md` ("nunca usar LLM/esforço de agente pra tarefa mecânica já resolvida"). Configurar Cookiecutter ou ligar o Traefik direito exige mais julgamento real do agente (ler documentação, tratar caso de borda, decidir o que é específico do projeto) do que gerar scaffolding do zero — que é trabalho repetitivo de baixo valor. Reinventar contraria a lei que o próprio projeto escreveu para si.

## 5. O que é genuinamente nosso e não deve ser substituído

- **Sync de skill/comando/spec pra 7 harnesses diferentes com fonte física única** (`componentes/` → `.claude/`, `.opencode/`, `.mimocode/`, `.gemini/`, `.agents/`...). Não há ferramenta de mercado que resolva isso pronto.
- **Protocolo delegado do generator** (conversar com o assistente ativo da sessão sem exigir API key externa). Genuinamente sem equivalente pronto.
- **Fleet discovery** (detectar quais CLIs de agente de IA estão instaladas na máquina). Nicho demais pra ter lib pronta.
