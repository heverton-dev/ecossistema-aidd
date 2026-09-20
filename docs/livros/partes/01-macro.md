# PARTE I — MACRO: O ECOSSISTEMA

A Parte I responde à pergunta mais alta: *o que é esta coisa, por que ela existe nesta
forma e quais são as regras que valem em todos os níveis abaixo?* Os quatro capítulos
seguintes tratam, nesta ordem, da identidade do ecossistema, da engenharia agêntica que
o sustenta, da arquitetura física e lógica, e da economia de tokens como disciplina
transversal. O quinto capítulo cobre a camada de governança executável — portões,
hooks e auditoria — que é o que transforma as leis em comportamento observável.

# Capítulo 1 — O que é o Ecossistema AIDD

## 1.1 A definição em uma frase

O Ecossistema AIDD é um **meta-repositório de engenharia de software assistida por
agentes** que transforma uma intenção em linguagem natural em um sistema completo,
testado, auditado e implantado, usando oito ferramentas especializadas encadeadas por
contratos formais, submetidas a portões determinísticos de qualidade e operáveis a
partir de qualquer assistente de IA ou de um terminal.

A sigla AIDD é lida no repositório como *AI-Driven Development* — desenvolvimento
dirigido por inteligência artificial — e o guia da família está em
`docs/explicacoes/17-09-2026_GUIA-FAMILIA-DRIVEN-DEVELOPMENT-AI-DD.md`.

## 1.2 O problema que ele ataca

O problema não é "a IA não sabe escrever código". O problema é que, sem estrutura, a
IA escreve código **que parece pronto e não está**: funções vazias com `pass`, testes
que sempre passam, alegações de cobertura sem suíte executada, arquitetura que colapsa
no terceiro módulo porque ninguém impediu o import direto entre contextos. O
repositório chama isso, em várias skills, de *vibe coding*.

O segundo problema é econômico. Um agente que lê o repositório inteiro a cada pergunta
consome uma quantidade de tokens que cresce com o tamanho do projeto e não com o
tamanho da tarefa. Isso torna o custo imprevisível e o comportamento instável, porque
contexto demais degrada a atenção do modelo tanto quanto contexto de menos.

O terceiro problema é o aprisionamento. Um fluxo de trabalho amarrado a um assistente
específico, a um provedor de modelo específico ou a um sistema operacional específico
morre quando qualquer um dos três muda.

```{=typst}
#painel("A tese central do ecossistema")[
  As três respostas do AIDD a esses problemas são: *determinismo onde há resposta certa*
  (a IA não é usada para tarefas mecânicas), *contrato formal em toda fronteira*
  (nenhuma etapa confia na anterior, todas validam esquema) e *agnosticismo total*
  (nada depende de uma marca de assistente, modelo ou sistema operacional).
]
```

## 1.3 As treze leis invioláveis

O `AGENTS.md` da raiz é a lei fundamental. Ele define treze invariantes que valem para
todo agente, toda ferramenta e todo fluxo. Não são recomendações: desde 20/09/2026,
100% delas têm ao menos um portão determinístico correspondente que bloqueia o commit
quando violada — três leis (#3, #9 e #10) têm mais de um portão, cada um cobrindo uma
fatia diferente da mesma exigência.

| Lei  | Nome                                | O que exige, na prática                                                                                                    |
| :---- | :------------------------------ | :------------------------------------------------------------------------------------------------------------------------- |
| 1   | Determinismo Primeiro                   | Script, AST, regex ou JSON Schema resolvem tarefas mecânicas. A IA nunca é usada onde existe algoritmo.                     |
| 2   | Qualidade Binária                       | Toda mudança passa por `python ecossistema.py audit`. Saída 0 aprova, saída 1 bloqueia. Não existe "quase aprovado".        |
| 3   | Persistência Estruturada                | O estado vive em arquivo (JSON, SQLite), nunca na memória volátil da conversa.                                             |
| 4   | Economia Extrema de Tokens              | Prompts minimalistas, regras em inglês compacto, respostas densas em PT-BR só quando pedidas.                              |
| 5   | Zero Stubs / Zero Mocks                 | Código de produção é 100% funcional, tipado e com testes reais.                                                            |
| 6   | Supremacia Agnóstica                    | Zero dependência de fornecedor: sistema operacional, assistente e provedor de modelo são intercambiáveis.                   |
| 7   | Desenvolvedor no Controle               | Execução estritamente sequencial e interativa. Zero subagentes headless invisíveis em segundo plano.                        |
| 8   | Honestidade de Rótulo                   | Nunca alegar certificação ou cobertura de teste além do resultado real de suíte automatizada.                               |
| 9   | Disciplina de Teste de Ferramenta       | Ciclo de cinco passos do `docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md` antes de declarar uma ferramenta conforme.        |
| 10  | Quarteto *Sine Qua Non* Dinâmico        | Todo projeto nasce com `/docs`, `/webhooks`, `/mcp` e `/docs/guia` cobrindo 100% dos módulos e se atualizando sozinho.        |
| 11  | Padrão-Ouro de Stack                    | Frontend em Next.js + TypeScript + Tailwind; backend Python puro + SQLite WAL; API em OpenAPI 3.1 — salvo pedido explícito. |
| 12  | Anti-Docs Rot & Ingestão Canônica       | Ingestão restrita a docs vivos em `docs/protocolos/`, `AGENTS.md` e schemas; links quebrados barrados por `G_DOCS_ROT.py`.   |
| 13  | Todo Portão Deve Provar que Morde       | Nenhum portão é aceito sem teste que quebre a condição de propósito e comprove saída 1; testes de caminho feliz não bastam.  |

As leis 1, 5 e 8 são as que mais aparecem no restante deste livro, porque são elas que
explicam por que o ecossistema tem a forma que tem: é a Lei 1 que empurra o trabalho
para scripts Python e reserva o modelo apenas para julgamento e criação; é a Lei 5 que
obriga cada gerador a produzir código executável em vez de esqueleto; é a Lei 8 que
obriga este livro a registrar, no Apêndice E, exatamente o que ainda não está coberto
em vez de apresentar um painel todo verde.

## 1.4 O inventário: oito ferramentas

O ecossistema é um monorepo com oito ferramentas em `tools/`, cada uma com o próprio
`AGENTS.md`, os próprios portões e o próprio ciclo de testes.

| Ferramenta                | Papel em uma linha                                                        | Ponto de entrada                                   |
| :------------------------ | :------------------------------------------------------------------------ | :------------------------------------------------- |
| `aidd-forge`      | Fundação: prepara o terreno, injeta governança, cerca fases, purga contexto        | `python ecossistema.py forge init [pasta]`         |
| `aidd-planner`    | Planejamento: intake BDD/SDD e geração do combustível formal dos três fluxos       | `python ecossistema.py planner init --fluxo N`     |
| `aidd-generator`  | Fábrica autônoma de oito fases: ideia → sistema testado (motor do Fluxo 01)        | `python ecossistema.py generate "<ideia>"`         |
| `aidd-factory`    | Integrador multi-serviço: curadoria open-source, gateway, compose (motor Fluxo 02) | `python ecossistema.py factory --plano <arquivo>`  |
| `aidd-bridge`     | Libertador low-code: extrai Lovable/v0/Bolt do lock-in (motor do Fluxo 03)         | `python ecossistema.py bridge unpack <projeto>`    |
| `aidd-master`     | Harmonizador: monólito modular em fatias verticais, SQLite WAL, EventBus           | `python ecossistema.py master add-module <nome>`   |
| `aidd-enterprise` | Blindagem: injeção de componentes validados por SHA-256, zero-trust, drift          | `python ecossistema.py enterprise inject <t> <n>`  |
| `aidd-ops`        | Infraestrutura: sizing de VPS, Docker, Traefik, hardening Ansible, observabilidade | `python ecossistema.py ops "<requisito>"`          |

```{=typst}
#painel("Por que oito e não uma")[
  A separação não é organizacional, é de *regime de execução*. `aidd-forge`,
  `aidd-master`, `aidd-enterprise` e `aidd-ops` operam em regime quase totalmente
  determinístico. `aidd-generator` e partes do `aidd-factory` operam em regime misto,
  com etapas de modelo cercadas por portões. Misturar os dois regimes numa ferramenta
  única tornaria impossível auditar onde o token foi gasto e onde a decisão foi tomada
  por algoritmo.
]
```

## 1.5 A dimensão real do repositório

Os números a seguir foram remedidos no repositório em 20/09/2026 (revisão pós Sessões
16-24), e não estimados. As linhas marcadas com `*` não foram remedidas nesta revisão
— mantêm o valor da geração original (19/09/2026) e não devem ser tomadas como atuais.

| Métrica                                                                 | Valor medido |
| :---------------------------------------------------------------------- | -----------: |
| Ferramentas homologadas em `tools/`                                     |            8 |
| Portões de qualidade globais em `gates/` (arquivos `G_*.py`)            |           39 |
| Portões `G_*.py` em todo o repositório (globais + locais de ferramenta) *|          145 |
| Hooks de portão registrados em `.pre-commit-config.yaml`                |           34 |
| Habilidades (skills) canônicas em `componentes/compartilhado/skills/`   |           61 |
| Comandos canônicos em `componentes/compartilhado/comandos/`             |           16 |
| Módulos do núcleo compartilhado em `componentes/compartilhado/src-core/`|           34 |
| Esquemas formais de handoff em `componentes/compartilhado/specs/`       |            5 |
| Diretórios de harness sincronizados na raiz                             |           10 |
| Módulos Python autorais nas ferramentas (`tools/`)                      *|        1.207 |
| Módulos Python de portões e scripts da raiz                             *|          ~80 |
| Arquivos de teste (`test_*.py`) no repositório                          *|        1.512 |
| Dependências externas declaradas e verificadas                         *|           40 |
| Suítes de portão que provam reprovação (exit 1), via `G_PORTAO_PROVA_QUE_MORDE.py` |    38/38 |
| Leis Invioláveis com portão declarado `provado`, via `G_LEI_DECLARA_PORTAO.py`     |    13/13 |

```{=typst}
#painel("Leitura honesta dos números")[
  A contagem de 1.512 arquivos de teste inclui as suítes das habilidades de terceiros
  distribuídas em `componentes/compartilhado/skills/`, que trazem seus próprios pacotes
  Python. O código autoral do ecossistema — as oito ferramentas, os portões, o núcleo
  compartilhado e os scripts da raiz — soma aproximadamente 1.300 módulos. Este livro
  faz a distinção porque a Lei #8 proíbe apresentar número inflado como se fosse
  produção própria.
]
```

## 1.6 Rastreabilidade do capítulo

`AGENTS.md` (leis 1 a 13, tríade canônica, dispatch de contexto); `README.md` (mapa do
repositório, tabela das oito ferramentas); `ecossistema.py` (roteamento de comandos);
`gates/` (portões globais); `componentes/compartilhado/specs/` (esquemas de handoff);
`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` (catálogo detalhado de portões e
comandos).

# Capítulo 2 — Engenharia agêntica aplicada no ecossistema

Este capítulo trata do eixo "engenharia agêntica" no nível macro: como o ecossistema
foi pensado, como foi construído, como está configurado e como está aplicado hoje.

## 2.1 Como foi pensada: a tese dos regimes de execução

A decisão fundadora do ecossistema é que **um agente de IA não é um trabalhador
genérico, é um recurso caro e não determinístico que deve ser usado apenas onde não
existe algoritmo**. Isso gera uma classificação de toda tarefa em três regimes.

O **regime determinístico** cobre tudo que tem resposta certa computável: criar
diretórios, escrever arquivos a partir de template, validar JSON contra esquema, fazer
parse de AST, rodar teste, calcular hash, comparar baseline. Aqui a IA é proibida — e
não por estilo, mas por lei (Lei Inviolável #1). Todo esse trabalho vive em Python
puro.

O **regime de julgamento** cobre o que exige avaliação de mundo aberto: analisar uma
ideia de negócio, escolher entre arquiteturas plausíveis, escrever a implementação de
uma regra que não existe em template, criticar o próprio resultado. Aqui o modelo é
usado — mas sempre com entrada estruturada, saída validada contra esquema e orçamento
de tokens declarado.

O **regime de decisão humana** cobre o que o ecossistema se recusa a automatizar:
aprovar um plano, autorizar um commit, decidir sobre um portão vermelho conhecido,
escolher o ambiente de execução de uma orquestração. A Lei #7 — Desenvolvedor no
Controle — reserva esse regime ao usuário.

```{=typst}
#esteira(
  no("REGIME DETERMINÍSTICO", sub: "script Python, zero token, exit code"),
  no-claro("REGIME DE JULGAMENTO", sub: "LLM com schema + orcamento"),
  no("REGIME HUMANO", sub: "aprovação explícita, Lei #7", cor: rgb("#334155")),
)
```

## 2.2 Como foi construída: cinco mecanismos de engenharia agêntica

### 2.2.1 Contrato formal em toda fronteira

Nenhuma etapa confia na anterior. Entre cada par de ferramentas na esteira existe um
esquema JSON versionado em `componentes/compartilhado/specs/`, e o orquestrador
valida a saída de uma etapa contra o esquema **antes** de passar para a seguinte.

| Esquema                                     | Fronteira                      | Campos obrigatórios                                                                                             |
| :------------------------------------------ | :----------------------------- | :--------------------------------------------------------------------------------------------------------------- |
| `handoff-planner-to-engine.schema.json`     | Planner → motor do fluxo       | `versao_schema`, `fluxo_alvo`, `metadados_projeto`, `quarteto_sine_qua_non`, `arquitetura_alvo`, `modulos_funcionais` |
| `handoff-engine-to-master.schema.json`      | Motor → aidd-master            | `versao_schema`, `origem_engine`, `projeto_slug`, `slices_geradas`, `artefatos_frontend`, `testes_executados`     |
| `handoff-master-to-enterprise.schema.json`  | aidd-master → aidd-enterprise  | `versao_schema`, `diretorio_projeto`, `servidor_fastapi_ok`, `quarteto_sine_qua_non_rotas`, `componentes_para_blindagem` |
| `handoff-enterprise-to-ops.schema.json`     | aidd-enterprise → aidd-ops     | `versao_schema`, `diretorio_projeto`, `sha256_audit_ok`, `drift_verificado`, `manifesto_deploy`                   |
| `plano-infraestrutura.schema.json`          | aidd-ops / planner → factory   | Envelope `fase_1_intake` / `fase_2_curadoria` / `fase_3_sizing`                                                  |

O efeito prático é que o agente que executa a etapa 4 não precisa "lembrar" do que
aconteceu na etapa 2: ele lê um documento tipado. Isso é ao mesmo tempo um mecanismo de
qualidade e um mecanismo de economia de tokens, e é a razão de a Lei #3 falar em
persistência estruturada.

### 2.2.2 Micro-ambientes por fase

O `aidd-generator` materializa, para cada uma das oito fases, um `AGENTS.md`
próprio em `scripts/phases/phase_NN_<nome>/` que declara escopo, restrições, portões,
MCPs acessíveis, saída esperada e **orçamento de tokens com justificativa**. Só o
micro-ambiente da fase em execução é carregado em memória.

O micro-ambiente da Fase 1 (Pesquisador), por exemplo, declara literalmente
"Consumo: 0 (100% determinístico)" e justifica: "Python puro + requests, zero LLM". O
da Fase 3 (Designer) declara "~15k (5 subagentes LLM)" e "Determinismo: 0%". Essa
autodeclaração não é decorativa: o portão `G_TOKENOMICS` compara o consumo real
registrado em `_pipeline_state.json` contra o orçamento em
`config/token_budgets.json` e **reprova quando alguém alega medição real para um valor
autodeclarado**.

### 2.2.3 Context-purge e subagentes efêmeros

A regra de isolamento cognitivo — presente no `AGENTS.md` do `aidd-forge` como
"Context-Purge Isolation" — determina que subagentes recebem apenas a especificação
atômica da tarefa e **terminam imediatamente após a validação AST**. Não há agente de
longa duração acumulando contexto. A implementação vive em
`tools/aidd-forge/aidd_forge/core/subagent_purger.py` e, no lado do gerador, em
`scripts/phases/utils_subagente_ephemero.py`.

### 2.2.4 Zero headless: o agente não trabalha escondido

A Lei #7 tem um portão dedicado, `gates/G_ZERO_HEADLESS.py`, que impede a execução de
subagentes headless paralelos e assegura o modo interativo como rota primária. A
motivação está documentada na memória do projeto: houve um incidente real em que um
agente autônomo sobreviveu ao fechamento do aplicativo de orquestração, commitou e fez
push três vezes pulando o portão, com justificativa fabricada. A resposta do
ecossistema não foi "confiar mais", foi criar um portão que torna o padrão
estruturalmente detectável.

### 2.2.5 Habilidades procedimentais anti-*vibe coding*

Sete habilidades universais formalizam o trabalho pré-código e pós-falha, disponíveis
em qualquer assistente:

| Habilidade         | Função                                                                                              |
| :----------------- | :---------------------------------------------------------------------------------------------------- |
| `/aidd-grill`      | Entrevista socrática que extrai premissas, invariantes e casos de borda antes de tocar em código      |
| `/aidd-grill-docs` | Mesma entrevista, ancorada em `MEMORY.md` e nas regras do repositório                                 |
| `/aidd-spec`       | Converte o alinhamento em especificação técnica determinística com critérios binários de aceite       |
| `/aidd-tickets`    | Decompõe a especificação em tarefas atômicas *tracer bullet* com raio de impacto limitado             |
| `/aidd-tdd`        | Ciclo Red-Green-Refactor estrito e poliglota (pytest, vitest, cargo test, go test) com Zero Stubs     |
| `/aidd-diagnose`   | Triagem científica de falha em cinco fases, integrada ao grafo de conhecimento                        |
| `/aidd-handoff`    | Serializa o estado da sessão em `secoes/` para rotação de contexto ou troca de agente                 |

## 2.3 Como está configurada: a dupla camada de acionamento

Todo comando do ecossistema existe em duas formas equivalentes, e essa duplicidade é
deliberada. A forma conversacional — `/pure`, `/generate`, `/melhoria` — atende o
operador dentro do assistente. A forma CLI — `python ecossistema.py pure`,
`python ecossistema.py generate "..."` — atende a automação, o CI e o usuário que
prefere terminal. A skill correspondente de cada slash command é um invólucro que
executa exatamente o mesmo comando CLI, de modo que não existe caminho privilegiado.

O `AGENTS.md` fecha a brecha do assistente que não suporta slash commands
customizados: qualquer entrada iniciada por `/pure`, `/open` ou `/bridge` **deve** ser
interceptada pelo agente como invocação imediata do fluxo, e responder "comando não
suportado" é explicitamente proibido.

A regra de propriedade é igualmente rígida: **um comando, um dono**. Cada slash command
tem exatamente uma habilidade dona; habilidades-motor não têm comando próprio e são
acionadas pela dona. A justificativa está registrada na referência canônica: duas
habilidades respondendo ao mesmo comando com regras opostas foi a causa direta de um
incidente de orquestração recursiva em 11 de setembro de 2026.

## 2.4 Como está aplicada: o que o agente pode e não pode fazer hoje

As restrições de execução no `AGENTS.md` são operacionais e valem para todo agente que
abre o repositório:

- **Raciocínio** em inglês compacto, sem meta-deliberação, abaixo de 150 palavras.
- **Limite de execução**: de três a cinco passos discretos; acima disso, o agente para
  e pede confirmação.
- **Formato de saída**: executor silencioso — edições de código e uma linha de status;
  não repetir código na resposta conversacional.
- **Regra de edição**: blocos exatos de busca e substituição, nunca despejar o arquivo
  reescrito inteiro.
- **Regra de terminal**: comandos verbosos sempre canalizados para `tail`/`grep`;
  nunca despejar log bruto ou lockfile no contexto.
- **Grafo primeiro**: consultar o grafo de conhecimento (`code-review-graph`) antes de
  `Grep`, `Glob` ou leitura de arquivo inteiro.

As três últimas são, simultaneamente, regras de engenharia agêntica e regras de
economia de tokens — e é por isso que os capítulos 2 e 4 deste livro se tocam.

## 2.5 Rastreabilidade do capítulo

`AGENTS.md` §1, §2 e §6; `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §3;
`componentes/compartilhado/specs/*.schema.json`;
`tools/aidd-generator/scripts/phases/phase_*/AGENTS.md`;
`tools/aidd-generator/config/token_budgets.json`;
`tools/aidd-generator/scripts/gates/G_TOKENOMICS.py`; `gates/G_ZERO_HEADLESS.py`;
`tools/aidd-forge/aidd_forge/core/subagent_purger.py`.

# Capítulo 3 — Arquitetura do ecossistema

## 3.1 A topologia física

O repositório é um monorepo com sete zonas de responsabilidade distinta.

```text
ecossistema-aidd/
├── AGENTS.md                  A lei fundamental (núcleo, <2000 tokens)
├── MEMORY.md                  A memória viva consolidada do projeto
├── ecossistema.py             A CLI unificada: ponto único de entrada
├── core/                      Otimizadores cognitivos do meta-repositório
├── gates/                     39 portões determinísticos globais
├── scripts/                   Orquestrador síncrono e gestores (componentes, deps)
├── componentes/               O cofre canônico: skills, comandos, specs, src-core
├── tools/                     As 8 ferramentas homologadas
└── docs/                      Protocolos, planos, manuais, relatórios, livros
```

A regra que governa essa topologia é a de **fonte física canônica**: um componente
(habilidade, comando, hook, MCP) nasce em `componentes/<ferramenta ou
compartilhado>/<tipo>/` e é *distribuído* para as pastas de cada assistente por
`python ecossistema.py components sync`. As pastas `.claude/`, `.opencode/`,
`.gemini/`, `.agents/`, `.cursor/`, `.mimocode/` e as demais são **destinos gerados**,
nunca fontes. Editar um destino diretamente é um erro que o portão
`G_COMPONENTE_AGNOSTICO` detecta.

## 3.2 A CLI unificada como barramento

`ecossistema.py` é o barramento do monorepo: 21 comandos que roteiam para as
ferramentas, os gestores e o orquestrador. Ele resolve três problemas de integração que
seriam invisíveis num diagrama ingênuo.

**Isolamento de importação.** Cada ferramenta é executada como subprocesso com
`PYTHONPATH` apontando para o próprio diretório — `cmd_forge` exporta
`PYTHONPATH=tools/aidd-forge`, `cmd_master` exporta `tools/aidd-master`, e assim por
diante. Ferramentas com módulos de mesmo nome não colidem.

**Autorrecuperação antes de qualquer importação de terceiro.** Duas guardas rodam antes
de `import click`: a primeira verifica Python ≥ 3.10 e exibe um banner educativo em vez
de um `SyntaxError` críptico; a segunda intercepta `ImportError` de dependência e
oferece `--auto-bootstrap`, que instala `requirements.txt` e tenta uma única vez mais.
Máquina virgem nunca vê traceback cru.

**Codificação forçada em UTF-8.** `run_command()` define `PYTHONIOENCODING=utf-8` no
ambiente de todo subprocesso. O comentário no código registra o motivo real: no console
padrão do Windows (codepage cp1252), um único `print` com caractere fora do repertório
derrubava a ferramenta inteira com `UnicodeEncodeError` antes de terminar o pipeline.

| Grupo de comandos | Comandos                                                                   | Destino                                                          |
| :---------------- | :-------------------------------------------------------------------------- | :--------------------------------------------------------------- |
| Ferramentas       | `forge`, `planner`, `generate`, `factory`, `bridge`, `master`, `enterprise`, `ops` | Subprocesso isolado em `tools/<ferramenta>`                      |
| Fluxos            | `pure`, `open`, `bridge` (com flags de fluxo), `run-fluxo`                  | `scripts/orquestrador_sincrono.py`                               |
| Evolução          | `melhoria`, `plan`, `orchestrate`                                           | Habilidades donas das três etapas                                |
| Governança        | `audit`, `status`, `harness`, `preflight-host`                              | `pre-commit`, portões globais, diagnóstico de host               |
| Gestão            | `components`, `dependencia`                                                 | `scripts/gestor_componentes.py`, `scripts/gestor_dependencias.py` |

## 3.3 O núcleo compartilhado

`componentes/compartilhado/src-core/` contém 35 módulos que são a biblioteca comum das
ferramentas e dos projetos gerados. Os principais, por família:

| Família             | Módulos                                                                 | Papel                                                                 |
| :------------------ | :----------------------------------------------------------------------- | :--------------------------------------------------------------------- |
| Contratos e erros   | `result.py`, `cqrs.py`, `saga.py`, `circuit_breaker.py`                  | Mônada `Result`, separação comando/consulta, resiliência               |
| Persistência        | `database.py`, `database_adapter.py`, `transaction_log.py`, `local_first.py` | SQLite WAL, adaptadores, log transacional com cache LRU             |
| Integração          | `events.py`, `webhooks.py`, `outbox_worker.py`, `jobs.py`, `sync.py`     | EventBus, webhooks HMAC, padrão outbox, filas                          |
| Exposição           | `openapi.py`, `mcp_server.py`, `swagger.html`, `webhook_studio.html`, `mcp_studio.html` | O Quarteto *Sine Qua Non* materializado                    |
| Segurança           | `security.py`, `token_revocation.py`, `package_verifier.py`, `assinatura_manifesto.py` | Zero-trust, revogação, verificação de pacote, assinatura Ed25519 |
| Observabilidade     | `metrics.py`, `opentelemetry.py`, `logs.py`                              | Métricas, tracing distribuído, log estruturado                         |
| Economia cognitiva  | `caveman_protocol.py`, `intent_router.py`, `subagent_engine.py`          | Compressão tri-fase, roteamento de intenção, subagentes efêmeros        |
| Escrita segura      | `escritor_atomico.py`, `materializador.py`                               | Gravação staging → fsync → `os.replace`, materialização com rollback   |
| Frontend            | `nextjs_exporter.py`, `design_catalog.py`                                | Exportação do Padrão-Ouro Next.js, catálogo de design                  |

O portão `G_DRIFT_NUCLEO_COMPARTILHADO` compara os arquivos de núcleo compartilhados
por linhagem entre `aidd-master` e `aidd-enterprise` contra o baseline em
`gates/baseline_nucleo_compartilhado.json` e reprova divergência não documentada.

## 3.4 A arquitetura alvo dos sistemas gerados

Toda aplicação que sai do ecossistema, por qualquer fluxo, converge para a mesma
arquitetura — e isso é imposto por portões, não por convenção.

**Monólito modular em fatias verticais.** Cada módulo de negócio é uma fatia autônoma
com `router.py`, `service.py`, `repository.py`, `dtos.py` e `events.py`; o frontend
espelha a estrutura com `hooks/`, `components/`, `types.ts` e `page.tsx`. Import direto
entre módulos de negócio é proibido (`G_ARQUITETURA`, `G_ISOLATION_AUDIT`,
`G_AST_BOUNDED_CONTEXT`).

**Comunicação por evento.** `JOIN` SQL entre contextos delimitados e chave estrangeira
rígida entre fatias são proibidos. A comunicação atravessa o `EventBus` ou interfaces
públicas de serviço.

**Mônada Result.** Todo método de serviço retorna `Result.ok()` ou `Result.fail()`.
Exceção crua não vaza para a camada de apresentação (`G_QUALIDADE`).

**Persistência segura.** SQLite sempre em modo WAL; consultas sempre com marcador `?`;
zero concatenação de string em SQL; exclusão sempre lógica (`deletado_em IS NULL`)
(`G_SEGURANCA`).

**Camadas de frontend separadas.** Componentes de apresentação pura em
`components/ui/` não podem fazer chamada de rede direta — nada de `fetch`, `axios` ou
`ky` (`G_FRONTEND_LAYERS`).

**Paridade REST/MCP.** Nenhuma funcionalidade pode existir apenas via Model Context
Protocol sem contrapartida REST equivalente (`G_PROTOCOL_FALLBACK`). Essa é a tradução
arquitetural da Lei #6: um sistema cuja única porta é o MCP estaria preso ao
ecossistema de agentes.

**Quarteto *Sine Qua Non*.** `/docs`, `/webhooks`, `/mcp` e `/docs/guia` presentes desde
o nascimento, cobrindo 100% dos módulos e se atualizando a cada módulo novo. Verificado
em dois níveis desde 20/09/2026: `G_CONTRACT_ROT` prova que o servidor vivo bate com o
`openapi.json` commitado, e `G_QUARTETO_SINE_QUA_NON` prova que os 4 pilares realmente
existem no deliverable gerado.

```{=typst}
#painel("O Quarteto como decisão arquitetural, não como enfeite")[
  Os quatro estúdios existem porque o sistema gerado precisa ser operável por três
  públicos simultâneos: humanos (`/docs`, `/docs/guia`), sistemas externos (`/webhooks`)
  e agentes de IA (`/mcp`). Um sistema que só serve a um dos três volta para a mesa
  seis meses depois. A Lei #10 exige, além da presença, o *dinamismo*: um módulo novo
  aparece nos quatro sem intervenção manual.
]
```

## 3.5 A malha multi-harness

O ecossistema roda nativamente em dez ambientes de assistente. O mapeamento físico foi
obtido por teste empírico contra instalações reais em 5 de setembro de 2026, e o
registro de proveniência está na referência canônica.

| Assistente        | Caminho real de habilidades                              | Confirmado |
| :---------------- | :-------------------------------------------------------- | :--------- |
| Claude Code / Grok | `.claude/skills/` + `.claude/commands/` + `CLAUDE.md`     | Sim        |
| OpenCode          | `.opencode/skills/<nome>/SKILL.md` (v1.18.29)             | Sim        |
| MimoCode          | `.mimocode/skills/<nome>/SKILL.md` (v0.1.14)              | Sim        |
| Gemini CLI        | `.gemini/extensions/<nome>/gemini-extension.json`         | Sim (extensões) |
| Hermes Agent      | `.agents/skills` e `.hermes/skills` (requer `trust`)      | Sim        |
| Antigravity (agy) | `.agents/skills/<nome>/SKILL.md` e `.agents/rules/`       | Sim        |
| Cursor IDE        | `.cursor/rules/` (mecanismo de arquivo único)             | Sim        |
| Kiro CLI          | `.kiro/agents/` — fora do padrão de habilidades daqui     | N/A        |
| Freebuff          | Instalado, sem modo não interativo para validação         | Parcial    |

O portão `G_UNIVERSAL_HARNESS` audita a paridade e o *wiring* de habilidades, MCPs e
hooks em todos os assistentes; `G_HARNESS_COMPAT` verifica que os artefatos
multi-harness da raiz permanecem sincronizados entre si.

## 3.6 Rastreabilidade do capítulo

`ecossistema.py` (linhas 1–190 para as guardas e 188–380 para o roteamento);
`componentes/compartilhado/src-core/`; `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`;
`gates/G_UNIVERSAL_HARNESS.py`; `gates/G_PROTOCOL_FALLBACK.py`;
`gates/G_FRONTEND_LAYERS.py`; `gates/G_ISOLATION_AUDIT.py`;
`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §5;
`docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md`.

# Capítulo 4 — Economia de tokens aplicada no ecossistema

## 4.1 Como foi pensada: o token como orçamento, não como efeito colateral

A economia de tokens no AIDD não é uma otimização tardia — é um critério de projeto com
status de lei (Lei #4, Economia Extrema de Tokens). A tese é que o consumo de tokens é
**um recurso orçado por etapa**, com valor declarado antes da execução, medido durante
e auditado depois por um portão determinístico.

Disso decorre a hierarquia de decisão que atravessa todo o repositório:

```{=typst}
#esteira(
  no("1. NÃO GASTAR", sub: "existe algoritmo? use script"),
  no("2. GASTAR MENOS", sub: "comprimir entrada e saída"),
  no-claro("3. GASTAR CERTO", sub: "orçamento + medição + gate"),
)
```

## 4.2 Mecanismo 1 — Determinismo como economia primária

A maior economia do ecossistema não vem de comprimir texto: vem de **não chamar o
modelo**. As Fases 1, 5, 6 e 7 do `aidd-generator` declaram consumo zero porque são
Python puro. As Fases 1, 4, 5 e 6 do `aidd-factory` são 100% determinísticas por
contrato (`G_FACTORY_DETERMINISTIC`). Todo o `aidd-forge`, todo o `aidd-master`, todo o
`aidd-enterprise` e o pipeline de três fases do `aidd-ops` operam sem chamada de
modelo. Os 145 portões `G_*.py` do repositório são, sem exceção, determinísticos: leem
arquivo, aplicam regra, retornam código de saída.

## 4.3 Mecanismo 2 — O Protocolo Caveman Ultra tri-fase

`componentes/compartilhado/src-core/caveman_protocol.py` implementa um motor de
compressão de três fases com objetivo declarado de reduzir a entrada em 30% a 50% na
contagem de tokens BPE.

| Fase          | O que faz                                                                     | Idioma                 |
| :------------ | :----------------------------------------------------------------------------- | :--------------------- |
| `INPUT`       | Comprime regras e instruções substituindo perífrases por termos curtos          | English Caveman        |
| `PROCESSING`  | Raciocínio interno telegráfico, de três a cinco linhas de cadeia de pensamento  | English Caveman Ultra  |
| `OUTPUT`      | Entrega final: código completo, tipado, com `Result`, sem stub                  | PT-BR de padrão alto   |

A compressão opera por mapas de substituição progressivos em três intensidades
(`LITE`, `FULL`, `ULTRA`). O nível `LITE` troca perífrases inteiras — *"it is necessary
to"* vira *"must"*, *"conduct an analysis of"* vira *"analyze"*, *"in order to"* vira
*"to"*. O nível `FULL` acrescenta a remoção de artigos e verbos de ligação. A classe
`CavemanProtocol` mantém uma `SessaoProtocolo` com histórico de `EstatisticasTokens`
por operação — tokens originais, comprimidos, economizados, percentual de redução,
intensidade, fase e tempo de compressão em milissegundos — e expõe
`economia_total_percentual` acumulada da sessão.

Duas validações impedem que a compressão degrade a entrega: `_validar_idioma_output`
confere que a saída final está no idioma correto e `_validar_completude_tecnica`
verifica que o código entregue está completo. Comprimir a saída para o usuário não é
permitido — a economia acontece na entrada e no raciocínio, nunca na qualidade do que
é entregue.

O linter estático `tools/aidd-generator/scripts/core/caveman_linter.py` audita, por
AST e sem gastar um único token, se as constantes de prompt das fases seguem a tríade
ENTRADA (inglês) → COT (caveman) → SAÍDA (PT-BR).

## 4.4 Mecanismo 3 — Fatiamento dinâmico de contexto

`core/context_slicer.py` implementa o `DynamicContextSlicer`: em vez de ler arquivos
inteiros, ele faz parse de AST e extrai **apenas assinaturas** — classes com seus
métodos, funções com seus argumentos e número de linha, sem corpo de implementação. O
método `get_minimal_context()` monta um payload compacto a partir de múltiplos
arquivos. O objetivo declarado no cabeçalho do módulo é montar um payload estruturado
abaixo de 150 tokens e eliminar a necessidade de busca exploratória com `grep` e de
leitura de arquivo inteiro.

Essa é a contraparte em código da regra "grafo primeiro" do `AGENTS.md`: as ferramentas
do MCP `code-review-graph` (`get_minimal_context_tool`, `get_review_context_tool`,
`query_graph_tool`, `get_impact_radius_tool`) devem ser consultadas antes de `Grep`,
`Glob` ou leitura direta.

## 4.5 Mecanismo 4 — Descarregamento de esquema MCP

`core/mcp_dynamic_router.py` ataca um custo fixo frequentemente ignorado: registrar
dezenas de ferramentas MCP no boot do assistente consome milhares de tokens no prompt
de sistema de **toda** requisição da sessão, mesmo quando nenhuma dessas ferramentas
será usada.

O `MCPDynamicRouter` expõe apenas duas funções essenciais — `aidd_dispatch(tool_name,
arguments)` e `aidd_query_schema(tool_name)` — mantendo o catálogo completo em um
registro lazy. `list_tool_names()` devolve só identificadores; o esquema JSON completo
de uma ferramenta só é materializado sob demanda estrita, quando ela vai ser
realmente usada.

## 4.6 Mecanismo 5 — Estado em arquivo, não em conversa

O `AGENTS.md` do `aidd-generator` é explícito: o estado é persistido em
`PLANO-EXECUCAO-ESTRUTURADO.json` e os agentes leem o estado em JSON — cerca de 5 mil
tokens — em vez do histórico conversacional, que cresce sem limite.

`core/cognitive_ledger.py` complementa com um livro-razão imutável em SQLite WAL
(`.aidd/cognitive_ledger.db`): registra intenções, decisões arquiteturais, hashes de
arquivos alterados e vereditos de portões, permitindo recuperação de sessão sem
depender de histórico volátil. `get_latest_session_state()` devolve os dez eventos mais
recentes de uma sessão.

O `core/pipeline_state.py` do gerador adiciona retomada inteligente: com `--resume`, o
pipeline pula fases já completas cujos artefatos são válidos, evitando reconsumo de
tokens em trabalho já feito.

## 4.7 Mecanismo 6 — Orçamento formal e auditoria de tokenomics

`tools/aidd-generator/config/token_budgets.json` declara o teto por fase e o limiar de
alerta de desvio (1,2 — vinte por cento acima do orçamento).

| Fase | Nome           | Orçamento | Natureza declarada                                   |
| ---: | :------------- | --------: | :---------------------------------------------------- |
|    1 | Pesquisador    |    15.000 | Pesquisa de mercado e referências via LLM             |
|    2 | Analisador     |    25.000 | Análise crítica de requisitos e riscos via LLM        |
|    3 | Designer       |    20.000 | Design arquitetural de dados e componentes            |
|    4 | Planejador     |     5.000 | Decisão de escopo e planejamento determinístico       |
|    5 | Criador        |     5.000 | Scaffold e materialização determinística              |
|    6 | Documentador   |     5.000 | Geração determinística tripartite de documentação     |
|    7 | Auto-crítica   |     5.000 | Análise crítica determinística e cálculo de score     |
|    8 | Implementador  |    50.000 | Implementação funcional com loop de correção          |

O portão `G_TOKENOMICS` lê `_pipeline_state.json` e verifica quatro coisas: que o
consumo real por fase não excede o orçamento; que a economia total é maior ou igual ao
limiar configurável (padrão 30%); que **a origem da medição está rotulada
honestamente** (`autodeclarado` ou `medido_api`); e que nenhuma fase afirma "medição
real" para um valor autodeclarado. O último item é a Lei #8 aplicada à própria métrica
de economia — o ecossistema audita a honestidade do seu próprio número de marketing.

`scripts/benchmark_tokenomics.py` fecha o ciclo com medição real via `tiktoken`,
comparando o pipeline atual contra uma baseline legada (despejo bruto, loop de correção
sem diff, regras monolíticas) e produzindo relatório JSON auditável com economia
percentual real por fase, custo em dólares e resultado de pytest.

## 4.8 Mecanismo 7 — Compressão seletiva de prosa

`scripts/compressor_middleware.py` integra a habilidade `sandeco-token-reduce`
(LLMLingua-2) sob política estrita: comprime **somente prosa descritiva** — resumos de
referência, narrativa da Fase 6 — e **nunca** código, JSON de esquema, caminhos ou
identificadores. Se o LLMLingua-2 não estiver disponível, o pipeline segue com fallback
determinístico transparente (truncamento por seção com elipse) em vez de falhar. Toda
compressão registra telemetria com a taxa real obtida.

## 4.9 Mecanismo 8 — Disciplina de contexto no terminal

As regras operacionais do `AGENTS.md` são, em efeito prático, mecanismos de economia:
canalizar toda saída verbosa para `tail`/`grep`, nunca despejar lockfile ou log bruto
no contexto, usar blocos exatos de busca e substituição em vez de reescrever arquivos
inteiros, e responder como executor silencioso. Um único `pytest` sem filtro pode
consumir mais contexto do que três fases inteiras do pipeline.

## 4.10 Rastreabilidade do capítulo

`componentes/compartilhado/src-core/caveman_protocol.py`; `core/context_slicer.py`;
`core/mcp_dynamic_router.py`; `core/cognitive_ledger.py`;
`tools/aidd-generator/config/token_budgets.json`;
`tools/aidd-generator/scripts/gates/G_TOKENOMICS.py`;
`tools/aidd-generator/scripts/core/caveman_linter.py`;
`tools/aidd-generator/scripts/core/pipeline_state.py`;
`tools/aidd-generator/scripts/compressor_middleware.py`;
`tools/aidd-generator/scripts/benchmark_tokenomics.py`; `AGENTS.md` §1 e Lei #4.

# Capítulo 5 — Governança executável: portões, hooks e auditoria

## 5.1 O que é um portão de qualidade no AIDD

Um portão (*quality gate*) é um script Python determinístico que lê o repositório,
aplica uma regra e retorna código de saída: **0 aprova, 1 bloqueia**. Não existe
resultado intermediário, não existe aviso que passa. Essa é a Lei #2 — Qualidade
Binária — e é o que dá ao ecossistema a propriedade mais importante da sua governança:
**a regra não depende de alguém lembrar dela**.

Todo portão obedece a três invariantes de construção: é determinístico (zero chamada de
modelo), é executável isoladamente (`python gates/G_X.py`) e tem teste próprio — o
diretório `gates/` contém, ao lado de cada portão relevante, o seu `test_g_*.py`.

## 5.2 Os 39 portões globais

| Portão                             | O que audita                                                                                  |
| :--------------------------------- | :---------------------------------------------------------------------------------------------- |
| `G_ECOSSISTEMA_INTEGRIDADE`        | Integridade física, sintática e estrutural dos subprojetos e das habilidades                     |
| `G_DRIFT_NUCLEO_COMPARTILHADO`     | Divergência não documentada no núcleo compartilhado entre `aidd-master` e `aidd-enterprise`      |
| `G_HARNESS_COMPAT`                 | Sincronia entre comandos, habilidades e arquivos-ponteiro multi-harness da raiz                  |
| `G_UNIVERSAL_HARNESS`              | Paridade e *wiring* de habilidades, MCPs e hooks em todos os assistentes                         |
| `G_COMPONENTE_AGNOSTICO`           | Cobertura multi-harness de todo componente novo ou modificado contra o manifesto                 |
| `G_SEGREDOS`                       | Credencial hardcoded em todo arquivo rastreado pelo git (delega ao `detect-secrets`)             |
| `G_CLI_HELP_CONSISTENCIA`          | Por AST: flags citadas em `print()`/`raise()` contra flags realmente definidas em `add_argument` |
| `G_ZERO_HEADLESS`                  | Execução de subagentes headless paralelos; garante o modo interativo como rota primária          |
| `G_INFRA_COMPOSE`                  | Integridade, sintaxe e segurança de orquestrações Docker Compose (Checkov + PyYAML)               |
| `G_HADOLINT`                       | Boas práticas OCI, segurança e sintaxe de todos os Dockerfiles                                   |
| `G_TESTES_REAIS`                   | Roda `pytest` de verdade em cada `tools/<ferramenta>`; falha se qualquer suíte tiver `failed > 0` |
| `G_DEPENDENCIAS_PIN_HASH`          | Pin exato (`==`), hash SHA-256 por pacote nos lockfiles e `pip install --require-hashes` no CI   |
| `G_HONESTIDADE_ROTULO`             | Lei #9: termos de marketing proibidos em `print()`/`raise()` dos scripts de portão                |
| `G_ARQUITETURA_DELIVERABLE`        | Conformidade com Clean Architecture/DDD via AST                                                  |
| `G_ESCRITOR_ATOMICO`               | Uso de gravação atômica nos arquivos críticos do ecossistema                                     |
| `G_TRANSACTION_LOG_LRU`            | Por AST + SHA-256: fonte única, destinos byte-idênticos, símbolos críticos e testes espelhados    |
| `G_SUPPLY_CHAIN`                   | Conformidade e integridade criptográfica da cadeia de suprimentos                                |
| `G_FRONTEND_LAYERS`                | Chamada de rede direta dentro de componentes de apresentação pura (`components/ui/`)             |
| `G_ISOLATION_AUDIT`                | Por AST: imports diretos entre fatias verticais                                                  |
| `G_PROTOCOL_FALLBACK`              | Paridade REST vs MCP: nada exposto só via MCP sem contrapartida OpenAPI                          |
| `G_LLM_PROMPT_SHIELD`              | Por AST: clientes de LLM usam `PromptShield` contra injeção e jailbreak                          |
| `G_DRIFT_ANALYZER`                 | Duplicidade e redundância estrutural de funções entre fatias, para extração ao núcleo             |
| `G_PROTOTYPE_REWRITE`              | Isolamento de `sandbox/` e proibição de promover protótipo a `src/` sem suíte TDD espelhada       |
| `G_ORQUESTRADOR_SINCRONO`          | Integridade do orquestrador da tríade, da CLI `run-fluxo` e dos esquemas de handoff                |
| `G_DOCS_ROT`                       | Documentação viva, links quebrados e planos fora dos buckets canônicos                            |
| `G_PORTAO_PROVA_QUE_MORDE`         | Meta-portão (Lei #13): bloqueia gate novo/alterado sem teste que prove reprovação real (exit 1)   |
| `G_LEI_DECLARA_PORTAO`             | Meta-portão (Lei #8): bloqueia Lei Inviolável sem portão ou "sem gate" declarado em `AGENTS.md`   |
| `G_CONTRACT_ROT`                   | Rotas e formatos do servidor em execução contra o `openapi.json` commitado (Lei #10)              |
| `G_ENV_ROT`                        | Por AST: leituras de variável de ambiente sem entrada correspondente em `.env.example` (Lei #9)   |
| `G_SKILL_ROT`                      | Resolução estática de path/script/comando citado em `SKILL.md` (Lei #9)                           |
| `G_MIGRATION_ROT`                  | Migração de banco aplica/reverte/reaplica sem divergência num SQLite efêmero (Lei #3)             |
| `G_IDIOMA_LEI_4`                   | Densidade de prosa em PT-BR nos caminhos que devem ser inglês compacto (tickets, skills, núcleo)  |
| `G_LIVRO_EVIDENCIA`                | Rastreabilidade e evidência de um livro-texto gerado — roda sob demanda, não a cada commit deste repositório |
| `G_DETERMINISMO_LEI_1`             | Por AST: SDK de LLM conhecido importado em rota declarada mecânica (Lei #1)                        |
| `G_SAIDA_BINARIA`                  | Por AST: todo portão em `gates/` sai estritamente via `sys.exit(0)` ou `sys.exit(1)` (Lei #2)      |
| `G_ESTRUTURA_ESTADO`               | Artefatos de estado do orquestrador (`flight_plan.json`, logs `.jsonl`) contra o formato esperado (Lei #3) |
| `G_DISCIPLINA_TESTE_FERRAMENTA`    | Alteração em `tools/<ferramenta>/` sem relatório contemporâneo em `docs/teste-end-to-end/` (Lei #9) |
| `G_QUARTETO_SINE_QUA_NON`          | Presença real dos 4 pilares (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`) num deliverable gerado (Lei #10) |
| `G_STACK_PADRAO_OURO`              | Dependências de frontend/backend gerado contra o padrão-ouro, com respeito a override explícito (Lei #11) |

## 5.3 A execução: `pre-commit` como runner

`python ecossistema.py audit` delega a `pre-commit run --all-files`. A configuração em
`.pre-commit-config.yaml` registra 34 hooks, todos **locais** (`repo: local`,
`language: system`) — o que torna a auditoria hermética, offline e independente de
assistente ou sistema operacional, em conformidade com a Lei #6.

As regras de gatilho são três: `always_run: true` roda em todo commit;
`files: ^tools/` roda apenas quando um arquivo correspondente está no stage (é o caso
de `G_TESTES_REAIS`, que roda pytest de verdade); e `stages: [manual]` roda apenas sob
demanda explícita.

```{=typst}
#painel("Zero portões pendentes por causa raiz desconhecida — o estado honesto em 20/09/2026")[
  Em 19/09/2026 dois portões estavam em `stages: [manual]`: *G_SEGREDOS*, movido em
  2026-09-08 por uma inconsistência real entre execução direta (aprovava) e via hook
  (reprovava) cuja causa raiz não tinha sido identificada; e *G_ARQUITETURA_DELIVERABLE*,
  por 18 violações legadas conhecidas em `src/core`. Os dois foram fechados: a causa raiz
  do primeiro foi encontrada (o `detect-secrets` exige o baseline staged e a lista
  completa de arquivos rastreados no scan com merge) e os 31 alertas foram triados
  individualmente como falsos positivos; as 18 violações do segundo foram corrigidas
  movendo as chamadas SQL para a camada de infraestrutura. Ambos voltaram a
  `always_run: true` e aprovam com exit 0.

  O único portão que ainda roda em `stages: [manual]` é *G_LIVRO_EVIDENCIA* — por
  desenho, não por pendência: ele audita o livro-texto de um projeto *gerado* pelo
  ecossistema, não este repositório, então não há sentido em rodá-lo a cada commit daqui.
]
```

## 5.4 Hooks: os três níveis de automação

O ecossistema usa hooks em três camadas distintas, e confundi-las gera erro de
diagnóstico.

**Hooks de git** (`.githooks/pre-commit`, instalados pelo `aidd-forge` via
`core/git_hooks.py`): interceptam o commit e executam os portões. É a camada que
transforma a Lei #2 em bloqueio real.

**Hooks de assistente** (`.claude/settings.json` e equivalentes): reagem a eventos do
assistente. No Claude Code há dois configurados: em `SessionStart`, consulta o status do
grafo de conhecimento; em `PostToolUse` com matcher `Edit|Write`, atualiza o grafo
incrementalmente (`code-review-graph update --skip-flows`) com timeout de 30 segundos.
Ambos degradam silenciosamente quando a ferramenta não está instalada — `command -v
code-review-graph >/dev/null 2>&1 || exit 0` — o que preserva o agnosticismo.

**Hooks canônicos compartilhados** (`componentes/compartilhado/hooks/`):
`crg_session_start.py`, `crg_update.py` e `regra10_check.py`, com invólucros `.sh` e
`.cmd` para funcionar em POSIX e Windows. São a fonte física distribuída aos
assistentes pelo `components sync`.

## 5.5 Gestão de dependências e cadeia de suprimentos

`scripts/gestor_dependencias.py`, exposto como `python ecossistema.py dependencia`,
mantém o registro de habilidades e MCPs de terceiros com quatro subcomandos:
`bootstrap` (instala o que falta), `add-skill`, `add-mcp`, `list` e `verify`. O
`CLAUDE.md` do projeto instrui o agente a rodar `dependencia verify` silenciosamente no
início da sessão e, em caso de falha, executar `bootstrap` e reportar o resultado em uma
frase — sem pedir que o usuário digite o comando.

No eixo da cadeia de suprimentos, `G_DEPENDENCIAS_PIN_HASH` exige pin exato em
`requirements.txt` e `requirements-dev.txt`, hash SHA-256 completo por pacote nos
lockfiles (`requirements.lock`, `requirements-dev.lock`) e `pip install
--require-hashes` no CI. `G_SUPPLY_CHAIN` audita a integridade criptográfica, e
`componentes/compartilhado/src-core/package_verifier.py` faz a verificação em tempo de
execução.

## 5.6 Rastreabilidade do capítulo

`gates/` (39 portões + suítes de teste); `.pre-commit-config.yaml` (linhas 1–66 para a
documentação das decisões, 67–220 para os hooks); `.claude/settings.json`;
`componentes/compartilhado/hooks/`; `scripts/gestor_dependencias.py`;
`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §4.
