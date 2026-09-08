# Inventário definitivo: o que fica vs o que troca, por ferramenta

> **Origem:** Item 1 de `docs/planos/a-fazer/02-direcionamento-estrategico-anti-nih/01-inventario-do-que-fica-vs-o-que-troca-por-ferramenta-o-trabalho-que-continua-de-pe.md`.
> **Fonte dos achados:** `docs/features/oportunidades-reaproveitamento-oss-nih.md` (levantamento NIH).
> **Status:** publicado para revisão do usuário — decisão de execução das Fases 1-4 depende de confirmação explícita (ver seção 6).

## Nota sobre numeração

O pedido original deste item referenciava "26 itens" do levantamento NIH. Na data desta publicação, o levantamento já está **fechado em 33 itens** (1-28 do levantamento original + 5 achados adicionais no mesmo dia, itens 29-33, por descoberta orgânica no catálogo pessoal do usuário — ver cabeçalho de `oportunidades-reaproveitamento-oss-nih.md`). Esta tabela usa a numeração atual (1-33) para manter rastreabilidade exata; nenhum item ficou de fora.

## 1. Resposta formal: "perdemos o trabalho?"

**Não.** Nenhum item do levantamento NIH pede para descartar modelagem de domínio, decisões de arquitetura vertical, ou os três diferenciais sem equivalente de mercado (materializador multi-harness, protocolo delegado, fleet discovery — seção 5 de `oportunidades-reaproveitamento-oss-nih.md`). O que troca, item por item, é o **motor por baixo** de mecanismos genéricos (parsing, templating, scanner de segredo, adapter de banco, orquestração de infra) — trabalho mecânico já resolvido por ferramenta madura, que hoje é mantido à mão e paga dívida técnica em token cada vez que quebra (CSP relaxado, Dockerfile sem `pip install`, porta duplicada). Trocar o motor não invalida a decisão de produto; states de domínio e a lógica específica de cada fatia continuam de pé.

## 2. Tabela por ferramenta

### aidd-forge

| Fica | Troca | # NIH |
|---|---|---|
| Tudo — é a ferramenta mais madura do ecossistema | Nenhum item do levantamento aponta para aidd-forge | — (0 itens aplicáveis) |

### aidd-generator

| Fica | Troca | # NIH |
|---|---|---|
| Pipeline de 8 fases (lógica de domínio de cada fase) | — | não mapeado a item NIH (não é reinvenção, é lógica própria) |
| Protocolo delegado (conversar com assistente ativo sem API key) | — | não mapeado — diferencial confirmado, ver `oportunidades-reaproveitamento-oss-nih.md` §5 |
| Fleet discovery (detectar CLIs de agente instaladas) | — | não mapeado — diferencial confirmado, ver §5 |
| — | Empacotamento de contexto de repo pra LLM → **Repomix** (**[CORRIGIDO — Fase2-Gen1]**) | #22 |
| — | Parsing/retry de saída estruturada de LLM na mão → **instructor** | #23 |
| — | MCP JSON-RPC 2.0 implementado à mão → **SDK oficial MCP** | #24 |
| — | Documentação gerada em 3 formatos separados (html/md/pdf) → **Pandoc** (1 fonte + conversão) | #25 |
| — | Orquestração de 8 fases com estado em JSON próprio → **Prefect/Dagster** para a parte genérica (retries, checkpoints); o protocolo delegado em si continua custom | #26 |

### aidd-master / aidd-enterprise (núcleo compartilhado)

| Fica | Troca | # NIH |
|---|---|---|
| Modelagem de fatias verticais, CQRS, consciência de RLS, WAL — decisão de arquitetura de domínio | — | não mapeado (decisão de produto, não código descartável) |
| — | Templating manual (`add_module.py`/`compose_suite.py`) → **Cookiecutter/Copier** | #6 |
| — | Result Monad próprio → lib **`returns`** (dry-python) | #7 |
| — | Adapter SQLite próprio (WAL manual) → **SQLAlchemy async / aiosqlite** | #8 |
| — | CSP/headers hand-rolled (causa raiz do CSP relaxado sem aviso) → **secure.py** / `starlette-csp` | #9 |
| — | RLS via regex reescrevendo SQL → **sqlglot** (parser real) | #10 |
| — | Webhooks CQRS com retry/DLQ hand-rolled → **huey** (a verificar: qual biblioteca está por trás hoje) | #11 |
| — | Portais de doc (Swagger/Webhook/MCP/Super-App) via HTML estático próprio → **Swagger UI/ReDoc** nativos do FastAPI (a verificar: se já coexistem) | #12 |
| — | Migração de schema sem ferramenta dedicada → **Alembic** | #27 |
| — | Tailwind servido via CDN (causa raiz do CSP relaxado) → **Tailwind CLI/PostCSS** auto-hospedado | #28 |

### aidd-ops

| Fica | Troca | # NIH |
|---|---|---|
| Inteligência de sizing/classificação de nicho | — | não mapeado (lógica de decisão própria) |
| — | Geração de infra por nicho do zero (Twenty/Chatwoot/Cal.com/Typebot/Evolution API) → **CapRover/Coolify/Dokku** | #13 |
| — | Dashboard de preflight que fabricou resultado hardcoded → **Uptime Kuma** | #14 |
| — | Hardening de SSH manual (`ssh_runner`) → **Ansible** + coleção `dev-sec.hardening` | #15 |
| Fix de integração, não troca de ferramenta: Traefik já está no template mas subutilizado — ligar labels de roteamento nos serviços que faltam | — | #16 |
| Healthcheck via Docker nativo — **confirmado, não é NIH**, já usado corretamente (13x no compose gerado) | — | #17 (não troca) |
| — | Cofre de credenciais (planejado, bloqueado) → **sops+age** ou **Vaultwarden** (comparar as duas antes de escolher) | #18, #29 |
| — | Intake interativo web (planejado) → **Streamlit gerenciado via Coolify** | #19 |
| — | AppShell white-label + Studios (planejado) → **Coolify Dashboard** (base para AppShell white-label + Studios integrados via CoolifyManager) | #20 |
| — | Isolamento estrito em VPS compartilhada (planejado) → resolvido nativamente por **Coolify** (redes dedicadas, zero portas host, limites CPU/RAM) | #21 |

> Achado mais importante desta ferramenta (ver `oportunidades-reaproveitamento-oss-nih.md` §3): 3 das 4 frentes planejadas em `evolucao-aidd-ops-fase-completa/` (itens #18/#29, #19, #20, #21) podem já estar resolvidas adotando Coolify/CapRover/Dokku como motor — restando só o trabalho de integração via API, não construção do zero. Decisão formal de qual adotar fica para a Fase 2 (item 4 deste plano).

### Camada raiz (`gates/`, `ecossistema.py`)

| Fica | Troca | # NIH |
|---|---|---|
| Materializador multi-harness (`componentes/` → `.claude/`, `.opencode/`, `.mimocode/`, `.gemini/`, `.agents/`...) | — | não mapeado — diferencial sem equivalente de mercado, ver §5 |
| As regras que cada gate checa (o que é validado continua igual) | — | não mapeado |
| — | `G_SEGREDOS.py` — scanner de entropia próprio → **detect-secrets** ou **gitleaks** | #1 |
| — | `G_CLI_HELP_CONSISTENCIA.py` — comparação via AST → migrar CLIs de `argparse` pra **Typer/Click** (concluído para `ecossistema.py` e `pipeline_ops.py` via Click; elimina necessidade do gate por construção nessas CLIs) | #2 |
| — | `G_INFRA_COMPOSE.py` — auditoria de compose via regex/YAML → **Checkov** (concluído) | #3 |
| — | Runner próprio dos "8 quality gates" (`python ecossistema.py audit`) → framework **pre-commit** (gates genuinamente novos viram hooks locais custom dentro dele) | #4 |
| — | Nenhum lint de Dockerfile hoje → **hadolint** | #5 |

### Transversal (não é núcleo de uma ferramenta específica)

| Fica | Troca | # NIH |
|---|---|---|
| — | Medir consumo de token por estimativa/autodeclaração → **Langfuse** (checar primeiro `token-economy-core`, projeto próprio do usuário no mesmo tema, antes de adotar) | #30 |
| — | Checagem estrutural via `ast` Python manual → **ast-grep** (mesma base tecnológica do `code-review-graph` já instalado) | #31 |
| Convenção própria de plano (`00-PROCESSO-E-DECISOES.md` + `NN-<item>.md`) — já madura e testada nesta sessão, não é substituição óbvia | Vale 1 comparação com **GitHub spec-kit** antes de evoluir mais | #32 |
| — | Teste manual de API via curl/requests durante auditoria → **Hoppscotch** | #33 |

## 3. O que de fato não valeu (não é "motor troca", é esforço que não deveria ter existido)

- Scanner de entropia caseiro do `G_SEGREDOS` (#1).
- Dashboard do aidd-ops que fabricou resultado hardcoded (#14).
- Gate de segurança (`G_SEGURANCA` do enterprise) inflado de linguagem de marketing ("blindagem militar") — achado de auditoria anterior, fora da numeração do levantamento NIH atual; tratar como achado independente, não item #.

Esses três são esforço específico e pequeno — não o projeto inteiro, nem a ferramenta inteira onde apareceram.

## 4. Cobertura de rastreabilidade

Todos os 33 itens do levantamento NIH aparecem na tabela acima exatamente uma vez:

- Camada raiz: #1–#5 (5 itens)
- aidd-master/aidd-enterprise: #6–#12, #27, #28 (9 itens)
- aidd-ops: #13–#21, #29 (10 itens)
- aidd-generator: #22–#26 (5 itens)
- Transversal: #30–#33 (4 itens)

5 + 9 + 10 + 5 + 4 = 33. Nenhum item órfão.

## 5. Itens com status "[a verificar]" no levantamento original

Os itens #11, #12, #15, #18 (feature planejada), #19 (planejada), #20 (planejada), #21 (planejada), #23, #29–#33 permanecem com status `[a verificar]` ou `[planejado]` na fonte (`oportunidades-reaproveitamento-oss-nih.md`). Esta tabela herda esse status — não eleva nenhum deles a "confirmado" por conta própria. A confirmação linha a linha é trabalho das Fases 1-4, não deste inventário.

> Atualização 2026-09-07: **#26 foi CORRIGIDO pela Fase2-Gen5** (Prefect 3.8.5 como motor genérico de orquestração — retries, checkpoints, persistência SQLite; protocolo delegado preservado), ver evidência na fonte. Os demais itens desta lista permanecem `[a verificar]`/`[planejado]`.

## 6. Confirmação necessária antes das Fases 1-4

Este documento cumpre os itens 1 e 2 da Definição de Pronto do Item 1 (tabela publicada, cada linha citando o # do achado NIH). O item 3 — usuário confirma que a leitura "o trabalho não foi perdido, o motor por baixo troca" está correta — é um gate humano explícito, registrado separadamente na comunicação com o usuário/coordenador desta tarefa antes de qualquer execução das Fases 1-4 (`03-fase-1...md` em diante).
