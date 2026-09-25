# Apêndice A — Referência da CLI unificada

Todos os comandos abaixo são despachados por `ecossistema.py` e existem também na forma
de slash command, conforme a dupla camada descrita no capítulo 2.

## A.1 Fluxos da Tríade Canônica

| Comando                            | Alias        | O que faz                                                      |
| :--------------------------------- | :----------- | :--------------------------------------------------------------- |
| `python ecossistema.py pure`       | `aidd-pure`  | Fluxo 01 — do zero puro, motor `aidd-generator`                 |
| `python ecossistema.py open`       | `aidd-open`  | Fluxo 02 — motores open-source, motor `aidd-factory`            |
| `python ecossistema.py freedom`    | `aidd-freedom` | Fluxo 03 — libertação de low-code, motor `aidd-bridge`        |
| `python ecossistema.py run-fluxo --fluxo <pure\|open\|freedom>` | — | Forma longa, aceita `--dry-run`             |

Parâmetros comuns aos fluxos: `--nome`, `--slug`, `--dominio`, `--pasta`,
`--origem` (Fluxo 03), `--dry-run`.

## A.2 Ferramentas

| Comando                                                | Ferramenta        |
| :----------------------------------------------------- | :---------------- |
| `forge init [caminho] [--force]`                       | `aidd-forge`      |
| `forge inject <tipo> <nome>`                           | `aidd-forge`      |
| `forge audit <caminho> [--fmt] [--output]`             | `aidd-forge`      |
| `forge conform <caminho> [--dry-run] [--items N]`      | `aidd-forge`      |
| `planner init --fluxo <1\|2\|3> --nome --slug --dominio --pasta` | `aidd-planner` |
| `planner validate <caminho>`                           | `aidd-planner`    |
| `planner export <caminho> --formato factory`           | `aidd-planner`    |
| `planner audit <pasta>`                                | `aidd-planner`    |
| `generate "<ideia>" --pasta <p> [--implementar-codigo] [--resume]` | `aidd-generator` |
| `factory --plano <arquivo> --pasta <destino>`          | `aidd-factory`    |
| `factory curate --dominio <d> --output <pasta>`        | `aidd-factory`    |
| `bridge scan\|convert-db\|merge\|pack\|migrate-auth\|destroy\|unpack` | `aidd-bridge` |
| `master init\|add-module\|compose\|compose-orca\|audit\|test\|bench\|heal\|status\|deploy\|apply\|setup\|inject\|attach-vsa\|refine-module\|export-frontend\|scaffold-infra` | `aidd-master` |
| `enterprise inject <tipo> <nome> [--dir]`              | `aidd-enterprise` |
| `enterprise verificar-drift [--dir]`                   | `aidd-enterprise` |
| `ops plan "<requisito>" [--pasta]`                     | `aidd-ops`        |
| `ops plan --ferramentas-json <arquivo>`                | `aidd-ops`        |
| `ops bootstrap --host <ip>`                            | `aidd-ops`        |
| `ops deploy`                                           | `aidd-ops`        |
| `ops preflight`                                        | `aidd-ops`        |

## A.3 Evolução e governança

| Comando                                          | O que faz                                                    |
| :----------------------------------------------- | :-------------------------------------------------------------- |
| `melhoria init --pedido "<texto>" --nome "<n>"`  | Etapa 1: análise com nota e evidência em `docs/melhorias/`     |
| `plan init <nome>`                               | Etapa 2: estrutura o plano em `docs/planos/<nome>/`            |
| `orchestrate <plano> [--dry-run]`                | Etapa 3: roteia ambiente, monta Plano de Voo e executa         |
| `audit-4f --manifest <json>`                     | Pipeline Linear de Auditoria 4F de uma ferramenta (capítulo 12) |
| `evolucao <ferramenta>` ou `evolucao --manifest <json>` | Executa os tickets do `PLANO-EVOLUCAO` do ciclo vigente (capítulo 12) |
| `livro <pasta-do-projeto> [--compilar]`          | Gera o livro-texto de um projeto a partir dos artefatos reais  |
| `sessao registrar\|listar\|buscar`               | Registro de sessões de IA em `secoes/` (capítulo 5, §5.6)      |
| `audit`                                          | Delega a `pre-commit run --all-files`                          |
| `status`                                         | Painel de ferramentas, habilidades e slash commands            |
| `status --testes [--write]`                      | Telemetria de testes                                           |
| `harness`                                        | Diagnóstico de compatibilidade multi-harness                   |
| `preflight-host`                                 | Diagnóstico do host                                            |

## A.4 Gestão de componentes e dependências

| Comando                                                               | O que faz                                        |
| :--------------------------------------------------------------------- | :------------------------------------------------- |
| `components sync --tipo <tipo\|todos> [--ferramenta] [--dry-run] [--force]` | Distribui componentes aos assistentes         |
| `components verify --tipo <tipo\|todos> [--ferramenta]`               | Audita a distribuição sem escrever                |
| `dependencia bootstrap [--tipo skills\|mcps\|todos] [--dry-run]`      | Instala o que falta                               |
| `dependencia add-skill --nome --pacote --instalar --verificar`        | Registra habilidade de terceiro                   |
| `dependencia add-mcp --nome --pacote --tipo stdio\|remote [...]`      | Registra servidor MCP                             |
| `dependencia list`                                                    | Lista o registro                                  |
| `dependencia verify`                                                  | Verifica a instalação (roda no início da sessão)  |

## A.5 Flags globais

`--auto-bootstrap` instala `requirements.txt` automaticamente quando falta dependência,
em vez de apenas exibir o banner educativo e sair com 1.

# Apêndice B — Os contratos formais de handoff

Os oito esquemas em `componentes/compartilhado/specs/` são a espinha dorsal da
integração entre ferramentas. Todos seguem JSON Schema e são validados por
`jsonschema` no orquestrador síncrono e nos Quality Gates.

## B.1 `handoff-planner-to-engine.schema.json`

Campos obrigatórios: `versao_schema`, `fluxo_alvo` (inteiro: 1 = do zero puro,
2 = open-source, 3 = ponte low-code), `metadados_projeto`, `quarteto_sine_qua_non`,
`arquitetura_alvo`, `modulos_funcionais`.

O `arquitetura_alvo` carrega o Padrão-Ouro: `padrao_frontend:
nextjs_typescript_tailwind`, `padrao_backend: fastapi_modular_vsa`, e `persistencia`
que varia por fluxo (`sqlite_wal` nos Fluxos 01 e 02, `postgresql` no Fluxo 03).

## B.2 `handoff-engine-to-master.schema.json`

Campos obrigatórios: `versao_schema`, `origem_engine` (qual motor produziu),
`projeto_slug`, `slices_geradas` (com `slice_nome`, `caminho_src`, `endpoints`,
`tabelas_sql`), `artefatos_frontend` (com `tecnologia`, `paginas_geradas`,
`origem_design`), `testes_executados` (com `total`, `passaram`, `falharam`,
`zero_stubs`).

O campo `origem_design` registra a procedência visual: `custom_tdd` no Fluxo 01,
`tailwind_standard` no Fluxo 02, `lovable_preserved` no Fluxo 03.

## B.3 `handoff-master-to-enterprise.schema.json`

Campos obrigatórios: `versao_schema`, `diretorio_projeto`, `servidor_fastapi_ok`,
`quarteto_sine_qua_non_rotas`, `componentes_para_blindagem`.

## B.4 `handoff-enterprise-to-ops.schema.json`

Campos obrigatórios: `versao_schema`, `diretorio_projeto`, `sha256_audit_ok`,
`drift_verificado`, `manifesto_deploy` (com `tipo_runtime`, `dockerfile_presente`,
`compose_presente`, `portas_expostas`).

## B.5 `plano-infraestrutura.schema.json`

O envelope de três fases — `fase_1_intake`, `fase_2_curadoria`, `fase_3_sizing` —
compartilhado por `aidd-ops`, `aidd-factory` e `aidd-planner`. É o contrato que permite
ao planner exportar diretamente para a fábrica sem tradução intermediária.

## B.6 `handoff-execucao.schema.json`

Governa a execução determinística de tarefas paralelas e fases síncronas em Git Worktrees
efêmeras (`orchestrator_pipeline.py`). Campos obrigatórios: `versao_schema`, `id_plano`,
`fase_paralela` (com `tasks_worktrees`, comandos isolados e quality gates locais) e
`fase_sequencial` (execuções ordenadas pós Join Barrier).

## B.7 `vsa-topological-dispatch.schema.json`

Governa o despacho topológico de fatias verticais VSA (`dispatch_pipeline.py`). Define o
Grafo Acíclico Dirigido (DAG) compilado pelo `aidd-planner` com ordenação por algoritmo
de Kahn, particionamento em lotes paralelos (`lotes_execucao`), fronteiras rígidas de
arquivos por fatia (`arquivos_permitidos`) e barreira de validação e convergência master.

## B.8 `handoff-melhoria.schema.json`

Saída consolidada do `aidd-melhoria` (etapa 1 do fluxo de evolução) que o orquestrador
lê para passar a `/plan`. Campos obrigatórios: `versao_schema`, `ferramenta`, `status`,
`codigo_saida`, `emitido_em`, `transicao`, `artefatos` e `assinatura`. A assinatura HMAC
cobre o conteúdo com as chaves ordenadas, sem o próprio campo `assinatura`; quem confere é
o `G_HANDOFF_MELHORIA`.


# Apêndice C — Glossário

**AIDD** — *AI-Driven Development*. O nome do ecossistema e da família de práticas.

**Agnosticidade (Supremacia Agnóstica)** — Lei #6. Ausência de dependência de
fornecedor em quatro dimensões: sistema operacional, assistente, modelo e protocolo.

**Anti-NIH** — Política de preferir integrar software consolidado a reimplementá-lo.
*NIH* é *not invented here*.

**Caveman (Protocolo Caveman Ultra)** — Motor de compressão tri-fase que reduz a
entrada em inglês telegráfico, raciocina em inglês comprimido e entrega em PT-BR de
padrão alto.

**Context-Purge** — Descarte imediato do contexto de um subagente após a validação da
sua tarefa.

**Contexto delimitado (*bounded context*)** — Fronteira de um módulo de negócio.
Import direto entre contextos é proibido.

**Determinismo** — Regime de execução em que o resultado é computado por algoritmo, sem
chamada de modelo. É o regime padrão do ecossistema (Lei #1).

**Drift** — Divergência entre o estado atual de um componente e o seu estado
registrado/assinado. Detectado por `verificar-drift` e por
`G_DRIFT_NUCLEO_COMPARTILHADO`.

**Fatia vertical (VSA, *vertical slice architecture*)** — Módulo autônomo contendo
todas as camadas de uma funcionalidade, do roteamento à persistência.

**Handoff** — Passagem de bastão entre duas etapas da esteira, sempre mediada por um
documento JSON validado contra esquema.

**Harness** — O assistente de IA que hospeda a sessão (Claude Code, OpenCode, Cursor,
Antigravity, entre outros).

**Honestidade de Rótulo** — Lei #8. Proibição de alegar certificação, cobertura ou
medição além do resultado real.

**Micro-ambiente** — O `AGENTS.md` isolado de uma fase, contendo apenas as regras
daquela fase.

**Mônada `Result`** — Tipo de retorno que encapsula sucesso (`Result.ok`) ou falha
(`Result.fail`), impedindo que exceção crua vaze para a apresentação.

**Portão (*quality gate*)** — Script determinístico que retorna 0 (aprova) ou 1
(bloqueia). Lei #2.

**PRÉ-PLANO** — O intake interativo conduzido pelo `aidd-planner` antes de gerar o
`PLANNER.json`.

**Protocolo delegado** — Mecanismo pelo qual o pipeline usa o modelo do próprio
assistente da sessão, sem abrir conexão própria com provedor.

**Quarteto *Sine Qua Non*** — Lei #10. Os quatro estúdios obrigatórios em todo projeto:
`/docs`, `/webhooks`, `/mcp` e `/docs/guia`.

**Tríade Canônica** — Os três fluxos de criação: `aidd-pure`, `aidd-open` e
`aidd-bridge`.

**Tokenomics** — A disciplina de orçar, medir e auditar o consumo de tokens por fase.

**Zero Stubs** — Lei #5. Proibição de função vazia, `TODO`, marcador de espaço ou
retorno simulado em código de produção.

**WAL (*write-ahead logging*)** — Modo de operação do SQLite exigido pelo ecossistema
para permitir leitura concorrente durante escrita.

# Apêndice D — Mapa de arquivos-chave

Para quem quiser verificar as afirmações deste livro diretamente no repositório, esta é
a rota mais curta para cada assunto.

| Assunto                                  | Arquivo                                                         |
| :--------------------------------------- | :---------------------------------------------------------------- |
| As treze leis invioláveis                | `AGENTS.md` §2                                                   |
| A Tríade Canônica                        | `AGENTS.md` §3                                                   |
| Catálogo detalhado de portões e comandos | `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`                  |
| Padrão-Ouro de stack                     | `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md`               |
| Ciclo de teste de ferramenta             | `docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`                |
| Agnosticidade de componentes             | `docs/protocolos/05-09-2026_protocolo-agnosticidade-componentes.md` |
| Validação de testes reais                | `docs/protocolos/06-09-2026_protocolo-validacao-testes-reais.md` |
| A CLI unificada                          | `ecossistema.py`                                                 |
| O orquestrador da tríade                 | `scripts/orquestrador_sincrono.py`                               |
| Contratos de handoff                     | `componentes/compartilhado/specs/`                               |
| Protocolo Caveman                        | `componentes/compartilhado/src-core/caveman_protocol.py`         |
| Fatiamento de contexto                   | `core/context_slicer.py`                                         |
| Roteador MCP dinâmico                    | `core/mcp_dynamic_router.py`                                     |
| Livro-razão cognitivo                    | `core/cognitive_ledger.py`                                       |
| Orçamento de tokens por fase             | `tools/aidd-generator/config/token_budgets.json`                 |
| Auditoria de tokenomics                  | `tools/aidd-generator/scripts/gates/G_TOKENOMICS.py`             |
| Micro-ambientes das 8 fases              | `tools/aidd-generator/scripts/phases/phase_*/AGENTS.md`          |
| Configuração dos portões no commit       | `.pre-commit-config.yaml`                                        |
| Hooks de assistente                      | `.claude/settings.json`                                          |
| Hooks canônicos compartilhados           | `componentes/compartilhado/hooks/`                               |
| Manifesto multi-harness                  | `gates/manifesto_harnesses.json`                                 |
| Baseline do núcleo compartilhado         | `gates/baseline_nucleo_compartilhado.json`                       |
| Despacho topológico VSA em worktrees     | `tools/aidd-master/scripts/dispatch_pipeline.py`                 |
| Pipeline de auditoria 4F e de evolução   | `scripts/orquestrador_4f.py`, `docs/protocolos/PIPELINE-AUDITORIA-4F.md` |
| Commit do usuário (`faz-commit`)         | `scripts/faz_commit.py`                                          |
| Registro de sessões de IA                | `scripts/gestor_sessoes.py`, `secoes/historico_sessoes.json`     |
| Guia de entrada para quem chega          | `ONBOARDING.md`                                                  |
| Assistente e modelo de cada fase         | `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`                    |
| Contrato de despacho DAG VSA             | `componentes/compartilhado/specs/vsa-topological-dispatch.schema.json` |
| Memória viva do projeto                  | `MEMORY.md`                                                      |
| Índice de planos                         | `docs/planos/INDEX.md`                                           |

# Apêndice E — Estado honesto na data de geração

A Lei #8 exige que este livro registre não apenas o que funciona, mas o que está
pendente. Esta é a lista consolidada de tudo que o texto sinalizou como incompleto,
vermelho ou aguardando decisão.

| Item                                                          | Estado                                                                    | Onde está registrado                                                        |
| :------------------------------------------------------------ | :-------------------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| `G_QUARTETO_SINE_QUA_NON` auto-descoberta                     | Cobre 2 de 3 fluxos canônicos com exemplo real (falta saída real do Fluxo 02/03) | `gates/G_QUARTETO_SINE_QUA_NON.py`, saída do próprio portão                 |
| Campos de telemetria do orquestrador síncrono                 | **RESOLVIDO** (21/09/2026): payloads de handoff e fatias são derivados dinamicamente de `PLANNER.json` e `dispatch_pipeline.py` | `scripts/orquestrador_sincrono.py`, `ISSUE-MESO-0007`                        |
| Discovery Engine completo do `aidd-factory`                   | Só o subconjunto determinístico (nicho dinâmico) está implementado         | `docs/features/v2_arquitetura-aidd-ops-factory.md` §7.1 e §9.1              |
| `.gemini/skills/` como mecanismo                              | Sincronizado, mas `confirmado: false` — o mecanismo real são as extensões  | `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §5                          |
| Freebuff                                                      | Instalado, sem modo não interativo para validação automatizada             | `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §5                          |
| 10 portões globais fora do `.pre-commit-config.yaml`           | Rodam só sob demanda; `audit` verde não cobre esses dez (lista no capítulo 5, §5.3). O décimo, `G_GESTOR_SESSOES`, entrou em 24/09/2026 | `.pre-commit-config.yaml`, `gates/`                                          |
| Pipeline de auditoria 4F                                      | Em uso real; ciclo `aidd-diagnose/ciclo-01` com a Fase 3 pronta numa branch fora da `main`, sem `gate_final` aprovado nem Fase 4 | `docs/auditoria/aidd-diagnose/ciclo-01/`, branch `audit/evolucao-aidd-diagnose-ciclo-01` |
| Plano `skills-pocock/ciclo-01`                                | Rascunho com 13 tickets; não executado; depende do merge do `aidd-diagnose` | `docs/auditoria/skills-pocock/ciclo-01/`                                     |
| `faz-commit` com mais de uma sessão aberta                    | `git add -A` leva o trabalho de outra sessão junto (caso real: commit `a1ea899`) | `scripts/faz_commit.py`                                                      |
| Commit por fase com `--no-verify` e merge pelo orquestrador   | Escolha deliberada no código, ainda em revisão                             | `scripts/orquestrador_4f.py`                                                 |
| Compressor de prosa (`sandeco-token-reduce`)                  | **REMOVIDO** (20/09/2026) — nunca esteve ligado ao pipeline                | `docs/issues/saneamento-governanca/` (ISSUE-0008)                            |
| Portões `G_FACTORY_INPUT/OUTPUT/DETERMINISTIC`                 | São rótulos de invariante no `AGENTS.md` da factory, não arquivos; a cobrança real está nos 6 portões de `tools/aidd-factory/gates/` | `tools/aidd-factory/AGENTS.md`, `tools/aidd-factory/gates/`                  |

```{=typst}
#painel("Por que este apêndice existe")[
  Um documento corporativo que só mostra o que funciona é um documento de vendas. A Lei
  #8 do ecossistema — Honestidade de Rótulo — proíbe alegar certificação ou cobertura
  além do resultado real, e essa proibição não faz exceção para a documentação sobre o
  próprio ecossistema.

  Cada linha da tabela acima tem um arquivo do repositório que a sustenta, e cada uma
  delas foi encontrada lendo o código e a configuração, não interpretando intenções. É
  assim que se verifica se um livro sobre um sistema descreve o sistema ou descreve o
  que alguém gostaria que ele fosse.
]
```
