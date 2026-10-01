# Diagnóstico (Fase 1) — fronteiras-ferramentas ciclo-01

> Data: 01/10/2026 · HEAD `7b61b45` · Tudo abaixo foi medido nesta sessão com script próprio.
> Evidências brutas: `C:\Users\trcnologia\Desktop\TESTES_E2E-ecossistema-aidd\ciclo-01\_evidencias\`
> Foto "antes" dos 3 fluxos: [BASELINE-E2E.md](file:///C:/Users/trcnologia/Desktop/TESTES_E2E-ecossistema-aidd/ciclo-01/BASELINE-E2E.md)

## Como foi medido

| Script (em `_evidencias/`) | O que faz |
|---|---|
| `medir_ferramentas.py` | Conta arquivos por ferramenta (HEAD versionado e disco), pares de conteúdo idêntico, cópias de gates |
| `matriz_donos.py` | Classifica cada arquivo versionado de `tools/` por responsabilidade (nome + conteúdo) |
| `rodar_fluxo.py` | Roda `run-fluxo` no worktree isolado e compara `git status --ignored` e mtime antes/depois (main, worktree, export de origem, Desktop) |
| `rodar_continuacao.py` | Roda as etapas 4–6 com os mesmos comandos do orquestrador numa cópia do projeto do fluxo 01 |
| `checar_quarteto.py` | Sobe `src/server.py` gerado e faz GET real nas rotas do Quarteto |

Exclusões: `node_modules`, `__pycache__`, `.git`, `.pytest_cache`, pastas de harness (`.claude`, `.agents`, `.gemini`, `.opencode`, `.mimocode`, `.cursor`, `.codebuddy`, `.skills`).

## Etapa 1 — Remedição das 8 ferramentas (diferenças contra o baseline recebido)

| Ferramenta | Baseline recebido | HEAD (versionado) | Disco | Por que difere |
|---|---|---|---|---|
| generator | 1685 | **173** | 1730 | 1557 arquivos são `scripts/.aidd/cache/_llm_request_*.json` (cache de execução, ignorado pelo git, **dentro da pasta da ferramenta**) |
| enterprise | 1011 | 1000 | 1012 | `.mimocode/` local e lixo ignorado |
| master | 383 | 377 | 385 | idem |
| forge | 167 | 152 | 158 | idem |
| ops | 94 | 94 | 94 | igual |
| factory | 70 | 70 | 70 | igual |
| bridge | 26 | 26 | 26 | igual |
| planner | 19 | 19 | 19 | igual |

Pares com conteúdo idêntico (HEAD, hashes distintos em comum, sem arquivo vazio):

| Par | Baseline | Medido |
|---|---|---|
| master–enterprise | 255 | **244** (311 arquivos em master, 367 em enterprise) |
| factory–enterprise | 23 | 23 |
| factory–master | 21 | 21 |
| generator–enterprise | 4 | **3** |
| forge–enterprise / forge–generator / forge–master / generator–master | — | 2 / 1 / 1 / 1 (não estavam no baseline) |

Total: **249 conteúdos** repetidos em 2+ ferramentas, envolvendo **727 arquivos**.

master × enterprise (`diff -rq`): **26** arquivos de mesmo nome divergentes (baseline dizia 27). Exclusivos de master: 31 entradas; de enterprise: 13 (lista em `_evidencias/diff_master_enterprise.txt`).

Cópias de gates (repo inteiro, HEAD):

| Gate | Baseline (cópias/versões) | Medido | Onde |
|---|---|---|---|
| G_HARNESS_COMPAT | 19/5 | **20/6** | raiz `gates/`, 12 exemplos em enterprise, master+enterprise `scripts/gates` e `templates/gates`, forge `templates/gates` + `sandbox-forge-teste`, generator |
| G_SEGREDOS | 16/2 | **17/3** | raiz + 12 exemplos + 4 em master/enterprise |
| G_QUALIDADE | 16/2 | 16/2 | 12 exemplos + 4 em master/enterprise |
| G_INJECT | 5/4 | 5/4 | enterprise, master, generator, forge (template + sandbox) |
| Outros com mais de 1 cópia | — | G_auditoria_15D 15/1, G_SEGURANCA 6/2, G_CONTRACTS 6/2, G_PERFORMANCE 6/2, G_TESTES_REAIS 3/2, G_BLOQUEAR_SEGREDOS 3/2, G_CYBERSECURITY_OWASP 3/2 … | 20 nomes de gate com cópia, **126 cópias** no total |

## Etapa 2 — Matriz real de responsabilidade (quem faz hoje × dono alvo)

Contagem de arquivos versionados que implementam cada responsabilidade (`(+Nex)` = cópias em pastas de exemplo).

| Responsabilidade | Dono alvo | forge | planner | generator | factory | bridge | master | enterprise | ops |
|---|---|---|---|---|---|---|---|---|---|
| Gates `G_*.py` | forge | 12 (+8ex) | 3 | 9 | 6 | 4 | 22 | 21 (+38ex) | 2 |
| Spec → `PLANNER.json` | planner | – | 2 | – | – | – | 1 (`dispatch_pipeline.py`) | – | – |
| Injetor de componentes | enterprise | 6 | – | **11** | – | – | 3 | 5 | – |
| Selo SHA-256 / COMPONENT-REGISTRY | enterprise | – | – | – | – | – | – | 1 | – |
| Merge em monólito (`compose_suite`, `attach_vsa`) | master | – | – | – | – | – | 3 | **1** | – |
| Quarteto `/mcp` | master | – | – | – | **2** | – | 6 | **6 (+2ex)** | – |
| Quarteto `/webhook` | master | – | – | – | **2** | – | 6 | **6 (+11ex)** | – |
| Quarteto OpenAPI/`/docs` | master | – | – | – | **4** | – | 9 | **9 (+19ex)** | – |
| Dockerfile | ops | – | – | – | **1** | – | **2** | **2 (+11ex)** | 1 |
| docker-compose | ops | – | – | – | **1** | – | **2** | **2 (+11ex)** | 9 |
| deploy.sh | ops | – | – | – | **1** | – | **2** | **2 (+9ex)** | 0 |
| nginx | ops | – | – | – | – | – | **4** | **4 (+4ex)** | 0 |
| sops+age | ops | – | – | – | – | – | – | – | 3 |
| Uptime Kuma | ops | – | – | – | – | – | – | – | 5 |
| Sincronizador de harness | compartilhado | 1 | – | 1 | – | – | 1 | 1 | – |

Refinamentos do mapa alvo (confirmados por execução, ver BASELINE-E2E):
1. **master também viola a fronteira de infra**: `master init` gerou `Dockerfile`, `docker-compose.yml`, `deploy.sh` e `nginx/` no projeto (o baseline só apontava enterprise).
2. **master faz trabalho de construtor**: `master add-module` cria a fatia de domínio `src/modules/principal` sozinho. Decisão aberta D1 (ver PLANO).
3. **O despacho de fatias (`dispatch`, código do master) roda dentro da etapa 3 (construtor)** e quebrou o fluxo 03.
4. **O orquestrador escreve os contratos no lugar das ferramentas**: os 4 JSON de hand-off são montados com valores fixos (`servidor_fastapi_ok: true`, `testes passaram = 2×fatias`). Prova: `run-fluxo --dry-run` aprovou os 4 contratos e imprimiu "100% DE APROVAÇÃO" sem rodar nenhuma ferramenta.
5. **aidd-ops nem é dono de infra genérica hoje**: `ops plan` só aceita 5 nichos fixos (clínicas, delivery, farmácias, b2b_industrial, energia_solar) e reprovou "Gestao Tarefas" (`NICHO_NAO_RECONHECIDO`).
6. **Quarteto**: o doc de papéis diz que ops "entrega" o Quarteto; o alvo diz que master o implementa. Proposta: master **implementa** as 4 rotas, ops só **publica**.
7. **Gate tem dois tipos com o mesmo nome**: gates do monorepo (`gates/`, ex.: G_HARNESS_COMPAT com 147 linhas) e gates entregues ao projeto gerado (ex.: `templates/gates/G_HARNESS_COMPAT.py` com 40 linhas). Não são versões do mesmo arquivo — são ferramentas diferentes com nome igual. Decisão aberta D2.

## Etapa 3 — Violações de fronteira (arquivo, quem usa, destino, risco)

| # | Arquivos | Quem usa de verdade (grep) | Destino | Risco ao mover |
|---|---|---|---|---|
| V1 | factory `templates/vsa/`: `Dockerfile`, `docker-compose.yml`, `deploy.sh` | `src/core/vsa_generator.py:25` (`_TEMPLATES_VSA_DIR`) | ops | Médio: caminho relativo fixo no gerador VSA |
| V2 | factory `templates/vsa/`: `mcp_server.py`, `mcp_studio.html`, `webhooks.py`, `webhook_studio.html`, `openapi.py`, `swagger.html`, `docs.html`, `templates/docs/openapi.json.j2` | mesmo `vsa_generator.py` | master | Médio: versões diferentes da fonte única (`mcp_server` 73612b ≠ src-core 800b23) |
| V3 | generator `scripts/core/injector/` (9 arquivos) + `scripts/aidd_inject.py` + `scripts/gates/G_INJECT.py` | só a própria CLI do generator; `gates/G_CLI_HELP_CONSISTENCIA.py:59`; `gates/manifesto_harnesses.json`; 5 testes em `tools/aidd-generator/tests/` | enterprise (injetor) / compartilhado (`sincronizador_harness`, `materializador`) | Baixo: a CLI raiz já usa `enterprise inject`; ninguém do fluxo chama o injetor do generator |
| V4 | enterprise `templates/core` e `templates/v2`: Dockerfile, compose, deploy.sh, nginx (10) + 35 em `materiais-extras/examples` | `application/commands/bench.py:26-27`, `scripts/compose_suite.py:503` (`_copy_shared_kernel`) | ops (infra) / remover (exemplos) | Médio: `tests/test_mapa_visual.py` cita `aidd-enterprise/templates/core` |
| V5 | master `templates/core` e `templates/v2`: Dockerfile, compose, deploy.sh, nginx (10) | `scripts/attach_vsa_infra.py:27-29`, `application/commands/bench.py`, `compose_suite._copy_shared_kernel` | ops | **Alto**: é o caminho que hoje faz o app subir; ops ainda não gera infra genérica |
| V6 | enterprise `scripts/compose_suite.py` (cópia antiga do merge) | `bench.py`, testes de enterprise | master | Baixo |
| V7 | Quarteto em enterprise (`src/core` e `templates/*`: mcp/webhooks/openapi/swagger/docs) | `G_DRIFT_NUCLEO_COMPARTILHADO` exige a cópia | master (implementa) | Médio: o gate de drift depende das duas cópias |
| V8 | master `scripts/dispatch_pipeline.py` lê/compila `PLANNER.json` | `orquestrador_sincrono.etapa_03_engine` | planner compila; master só consome | Médio |
| V9 | injetor também em forge (`aidd_forge/core/injector*.py`, `universal_injector.py`) e master (`application/commands/inject.py`) | `forge init`/`forge inject` | enterprise ou compartilhado (decisão D3) | Alto: forge usa para instalar skills/commands no projeto |
| V10 | bridge grava `bridge-manifest.json` **dentro do export do usuário** | `bridge scan` (fluxo 03) | pasta do projeto | Baixo; vazamento confirmado por execução |
| V11 | generator grava cache LLM em `tools/aidd-generator/scripts/.aidd/cache/` (1557 arquivos no main) | protocolo delegado | pasta do projeto (`.aidd/cache`) | Baixo |

## Etapa 4 — Duplicações: versão correta e destino

| Família | Versões | Versão recomendada (por `git log` + conteúdo) | Destino |
|---|---|---|---|
| G_HARNESS_COMPAT | 6 | Monorepo: `gates/` (2c8a58f, 23/09). Projeto: master/enterprise `templates/gates` (9fcab5e, 09/09). Forge template (cc21520, 03/09) e generator (4dadce0, 03/09) estão **mais velhos** | forge (`templates/gates`) como fonte única dos gates de projeto, distribuído por sync |
| G_SEGREDOS | 3 | Monorepo `gates/` (4cde1c8, 30/09). Projeto: 09ad11b (28/09) | idem |
| G_QUALIDADE | 2 | 1f37de0 (16/09); as 12 cópias de exemplo (24 linhas, 04/09) são velhas | idem |
| G_INJECT | 4 | enterprise 3745108 (233 linhas, 09/09) | enterprise (dono do injetor) |
| G_SEGURANCA / G_CONTRACTS / G_PERFORMANCE | 2 cada | master/enterprise (24/09, 18/09, 09/09); forge template é de 03/09 | forge `templates/gates` |
| G_TESTES_REAIS | 2 | `gates/` (30/09) | forge |
| G_BLOQUEAR_SEGREDOS / G_CYBERSECURITY_OWASP | 2 cada | generator OWASP 0e07d9e (583 linhas, 12/09) > forge (111 linhas) | forge |
| Núcleo `src/core` master+enterprise | 28 arquivos byte-idênticos | já tem fonte única (`componentes/compartilhado/src-core`) | manter |
| Quarteto em `templates/core` e `templates/v2` | 4 cópias, **divergem da fonte única** (mcp_server 326a90 × 800b23; webhooks b7bcaa × 21bbcd; openapi 1bb19e × d56743; database d584bf/bb9161 × 33f315) | src-core | ligar ao sync (ver Etapa 6) |
| `materiais-extras/examples` (12 projetos) | gates de 04/09 | — | remover do enterprise (fase d), guardar fora se o usuário quiser |
| `sandbox-forge-teste` | cópias de gates | — | remover (fase d) |

Achado: os gates que `forge init` instala hoje no projeto gerado vêm de `aidd_forge/templates/gates` — os mais antigos de todos (03/09).

## Etapa 5 — master × enterprise: os 26 divergentes

`+E/-M` = linhas que só existem em enterprise / só em master.

| Arquivo | Diferença | Último commit M / E | Versão correta | Destino |
|---|---|---|---|---|
| AGENTS.md | +16/-18 | 16/09 / 16/09 | cada um o seu | ferramenta (fase g) |
| application/commands/\_\_init\_\_.py | +5/-3 | 10/09 / 17/09 | enterprise (registra drift) | cada CLI registra só o que é seu |
| application/commands/inject.py | +138/-123 | 10/09 / 10/09 | enterprise (tem conteúdo padrão) — revisar diff | enterprise; sai do master |
| application/commands/plan.py | +8/-1 | 10/09 / 10/09 | enterprise | ops (é plano de infra) |
| application/commands/verificar_drift.py | +1/-1 | 10/09 / 17/09 | enterprise | enterprise |
| README.md | +10/-9 | 10/09 / 10/09 | cada um o seu | fase g |
| requirements.txt | +0/-5 | 14/09 / 12/09 | master (asyncpg, pyjwt, argon2) | cada ferramenta, a partir do lock raiz |
| scripts/aidd.py | +19/-27 | 18/09 / 17/09 | cada CLI a sua | ferramenta |
| scripts/compose_suite.py | +31/-103 | 20/09 / 20/09 | **master** (tem `CORE_KERNEL_FILES`, conserto de 17/09) | master; sai do enterprise |
| scripts/gates/G_INJECT.py | +61/-50 | 09/09 / 09/09 | enterprise | enterprise |
| scripts/openapi_to_ts.py | +1/-1 | 03/09 / 04/09 | enterprise (mais novo) | master (Quarteto/front) |
| scripts/provision_project.py | +23/-218 | 22/09 / 22/09 | **master** (render real do `docs.html`) | master |
| scripts/run_all.py | +0/-1 | 09/09 / 09/09 | master | ferramenta |
| src/core/detector_camada.py | +1/-1 | 05/09 / 05/09 | divergência documentada (`_PROJETO_PADRAO`) | compartilhado, parametrizado |
| src/core/profiles_registry.py | +60/-4 | 10/09 / 05/09 | revisar diff (master mais novo, enterprise com mais linhas) | compartilhado, perfil por ferramenta |
| src/core/schema_injector_request.json | +2/-2 | 05/09 / 05/09 | enterprise | enterprise |
| suite.db | binário | não versionado | nenhuma (arquivo de execução local) | apagar localmente |
| templates/cookiecutter-scaffold/suite/cookiecutter.json | +1/-1 | 18/09 / 18/09 | master | master |
| templates/core/deploy.sh | +0/-1 | 17/09 / 04/09 | master | ops |
| templates/core/Dockerfile | +0/-4 | 17/09 / 08/09 | **master** (tem `pip install`, conserto de 17/09) | ops |
| templates/v2/deploy.sh | +0/-1 | 17/09 / 04/09 | master | ops |
| tests/conftest.py | +15/-8 | 12/09 / 12/09 | cada um o seu | ferramenta |
| tests/unit/test_cli_commands.py | +21/-21 | 05/09 / 05/09 | cada um o seu | ferramenta |
| tests/unit/test_compose_suite.py | +0/-140 | 18/09 / 09/09 | master | master |
| tests/unit/test_g_seguranca_gate.py | +0/-69 | 17/09 / 09/09 | master | junto do G_SEGURANCA (forge) |
| tests/unit/test_mcp_server_sdk.py | +2/-2 | 12/09 / 12/09 | master | master |

Regra que sai da tabela: onde a responsabilidade é de integração/Quarteto/infra, **master tem a versão consertada**; onde é injetor/drift, **enterprise tem a versão consertada**. As cópias velhas são exatamente as que estão no lugar errado.

## Etapa 6 — Sincronização existente

| Mecanismo | Cobre | Resultado agora | Não cobre |
|---|---|---|---|
| `componentes/compartilhado/src-core/sync.py` (`verify`) | 28 arquivos → `tools/aidd-master/src/core` e `tools/aidd-enterprise/src/core` | exit 0, byte-idêntico | `templates/core`, `templates/v2`, factory `templates/vsa`, generator `scripts/core/injector`, `tests/`, `scripts/gates/` |
| `python ecossistema.py components verify` | 81 componentes (skills/commands/hooks) nos espelhos de harness | exit 0 | código de ferramenta, gates, templates |

Conclusão: **não existe sync para gates nem para templates**. É por isso que os templates do Quarteto envelheceram em relação à fonte única e os gates de projeto do forge ficaram em 03/09.

## Achados já conhecidos, rechecados nesta sessão

| Achado antigo | Hoje |
|---|---|
| Fluxos 02/03 quebram na etapa 3 | **Confirmado**, e o fluxo 01 também (motivos diferentes) |
| inject grava no repo real em vez do projeto | **Não reproduziu**: `enterprise inject` gravou só em `projeto/templates/rules/`; main e worktree intactos |
| 2 comandos de auditoria diferentes | **Confirmado**: `ecossistema.py audit` (monorepo inteiro) × `forge audit <pasta>` (projeto). A etapa 7 do `run-fluxo` chama o primeiro — audita a ferramenta, não o app gerado (leitura de código; nenhum fluxo chegou na etapa 7) |
| CLI do forge só roda de dentro de `tools/aidd-forge` | **Confirmado**: `python -m aidd_forge.cli` fora dá `ModuleNotFoundError` (exit 1); `python ecossistema.py forge` funciona (usado nos 3 fluxos) |
| Novo | `Failed to initialize plugins: No module named 'core.logs'` no início do generator |
