# Oportunidades de reaproveitamento OSS (NIH — Not Invented Here)

> **Origem:** levantamento feito em 2026-09-07, no mesmo dia da auditoria "sem maquiagem" (`docs/relatorios/relatorio-auditoria-ecossistema-aidd-sem-maquiagem.html`).
> **Status:** RASCUNHO — levantamento técnico, não é decisão de escopo aprovada. Nenhum item aqui foi commitado ou vira trabalho sem aprovação humana.
> **Método:** itens marcados **[confirmado]** foram verificados lendo código/config real nesta sessão (grep, leitura de arquivo). Itens marcados **[a verificar]** são hipóteses plausíveis a partir do que já foi lido, mas não confirmadas linha a linha — tratar como pista de investigação, não fato.
> **Lista fechada em 2026-09-07 — 28 itens.** Nenhum item novo entra por brainstorming aberto ("existe ferramenta pra X?") depois deste ponto. A única forma de um item novo aparecer é descoberta orgânica durante a execução real de uma fase já aprovada de `docs/planos/a-fazer/02-direcionamento-estrategico-anti-nih/` — documentada com evidência no momento em que aparecer, não uma nova rodada de especulação.

---

## 1. Por que isso importa

A auditoria de hoje encontrou vários bugs (CSP relaxado sem ninguém notar, Dockerfile sem `pip install`, porta duplicada no compose, dashboard fabricando resultado, gate de segurança que é majoritariamente grep vestido de "blindagem militar"). Boa parte desses bugs existe porque o ecossistema **reimplementou na mão** um problema que ferramentas open source maduras já resolvem — cada reimplementação é uma superfície nova de bug que o time (e o assistente) paga em token toda vez que precisa investigar/corrigir.

## 2. Levantamento por ferramenta

### Camada raiz (`gates/`, `ecossistema.py`)

| # | O que foi reinventado | Substituto maduro/grátis | Status | Observação |
|---|---|---|---|---|
| 1 | `gates/G_SEGREDOS.py` — scanner de entropia de Shannon próprio ("v2.0 Shannon Entropy Engine") | **detect-secrets** (Yelp) ou **gitleaks** | [confirmado] nome do próprio gate já se descreve como engine caseiro | Libs mantidas cobrem muito mais padrão de credencial |
| 2 | `gates/G_CLI_HELP_CONSISTENCIA.py` — compara help vs `argparse` via AST pra detectar drift | Migrar as CLIs de `argparse` pra **Typer** ou **Click** | [confirmado] mecanismo via AST confirmado no código | Help gerado do código não pode divergir — o gate vira desnecessário por construção |
| 3 | `gates/G_INFRA_COMPOSE.py` — audita compose estaticamente (regex/YAML) | **Checkov** (Bridgecrew) | [confirmado] | Detectaria porta duplicada, env faltando — exatamente o que passou batido no ops |
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
| 16 | **Traefik incluído no template mas SUBUTILIZADO** | Usar o Traefik que já está lá, direito | **[confirmado agora, 2026-09-07]** | `templates/infra/traefik/docker-compose.yml` existe e sobe um Traefik real — mas grep em `docker-compose.yml` do projeto gerado mostra que só o **dashboard do próprio Traefik** tem `traefik.enable=true`/labels de roteamento (linhas 30-34). Twenty, Chatwoot e Cal.com (os 3 que colidem na porta 3000) usam `ports:` diretos, sem nenhuma label de roteamento por host via Traefik. **O bug de porta duplicada existe porque a ferramenta que evitaria o problema está no compose mas não está fazendo o trabalho** — não é falta de ferramenta, é integração incompleta |
| 17 | Healthcheck de serviço | ~~Docker healthcheck nativo~~ | **[confirmado, NÃO é NIH]** | Grep mostrou `healthcheck:` presente 13x no compose gerado — isso já está sendo usado corretamente, não precisa de substituto |
| 18 | Cofre de credenciais (feature planejada, ainda não construída — `docs/planos/evolucao-aidd-ops-fase-completa/02-cofre-local...md`) | **sops** + **age** (padrão de mercado pra secrets em infra-as-code) | [planejado, não implementado ainda] | Melhor avaliar ANTES de construir do zero — evita nascer NIH |
| 19 | Intake interativo web (feature planejada, item 01 do plano de evolução) | **Streamlit** ou **Gradio** pra formulário rápido interno | [planejado, não implementado ainda] | Ambos resolvem "formulário web sem fricção" sem frontend custom |
| 20 | AppShell white-label + Studios (feature planejada, item 03) | **Backstage** (Spotify, developer portal open source, plugin-based) | [planejado, não implementado ainda] | Tem catálogo de API/docs pronto — avaliar antes de construir um appshell do zero |
| 21 | Isolamento estrito em VPS compartilhada (feature planejada, item 04) | Resolvido nativamente por **Coolify/CapRover/Dokku** (multi-tenant em VPS compartilhada é o caso de uso principal deles) | [planejado, não implementado ainda] | **Ver seção 3 abaixo — este é o achado mais importante** |

### `aidd-generator`

| # | O que foi reinventado | Substituto maduro/grátis | Status | Observação |
|---|---|---|---|---|
| 22 | Empacotamento de contexto de repo pra LLM (cada fase lê arquivo por arquivo) | **Repomix** | [a verificar — não confirmado como o contexto é montado hoje] | Ganho direto de token, é fase que já gasta LLM de verdade |
| 23 | Parsing/retry de saída estruturada de LLM na mão | **instructor** (Pydantic + retry pronto) | [a verificar] | Menos código próprio pra tratar erro de parsing de LLM |
| 24 | MCP JSON-RPC 2.0 implementado no app gerado (`src/app.py`, confirmado rodando) | **SDK oficial do MCP** (`modelcontextprotocol/python-sdk`) | **[confirmado — grep por import do SDK oficial não encontrou nada no app gerado]** | Provável dispatcher JSON-RPC próprio; SDK oficial trata negociação de capacidade e códigos de erro corretamente |
| 25 | Documentação gerada em 3 formatos separados (html, md, pdf) | **Pandoc** (1 fonte markdown → converte pros outros 2) | [confirmado que os 3 formatos existem, via AVALIACAO-AUTO-CRITICA.md] | Hoje provavelmente 3 geradores/templates a manter em vez de 1 fonte + conversão |
| 26 | Orquestração de 8 fases com estado em JSON próprio | **Prefect** ou **Dagster** pra parte genérica (retries, checkpoints) | [a verificar] | O "protocolo delegado" (falar com o assistente sem API key) continua genuinamente custom — isso não tem equivalente pronto |

---

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
