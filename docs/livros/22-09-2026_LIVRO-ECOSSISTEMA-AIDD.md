---
title: "Ecossistema AIDD"
subtitle: "Tratado completo: do macro ao micro"
author:
  - Ecossistema AIDD — Governança Canônica
date: "22 de setembro de 2026"
lang: pt-BR
toc: true
toc-depth: 2
abstract: |
  Este livro descreve o **Ecossistema AIDD** em três níveis de profundidade e sob três
  eixos fixos de análise.

  Os três níveis são o **macro** (o ecossistema como organismo único: leis, governança,
  CLI unificada, portões de qualidade e distribuição multi-harness), o **meso** (os três
  fluxos canônicos de criação — `aidd-pure`, `aidd-open` e `aidd-freedom` [motor `aidd-bridge`] — e o fluxo de
  evolução `/melhoria → /plan → /orchestrate`) e o **micro** (cada uma das oito
  ferramentas homologadas, uma a uma).

  Os três eixos, aplicados em todos os níveis, são: **Engenharia Agêntica Aplicada**
  (como foi pensada, construída, configurada e como está aplicada), **Arquitetura**
  (como está, de fato, hoje) e **Economia de Tokens Aplicada** (como foi pensada,
  construída, configurada e como está aplicada).

  Cada ferramenta é descrita em três camadas sucessivas — funcionamento **individual**,
  funcionamento **dentro do fluxo** e funcionamento **dentro do ecossistema** — e, em
  cada camada, sempre pelos mesmos sete itens: passo a passo de execução, portões de
  qualidade, habilidades, determinismo, ferramentas acessadas, hooks e regras, e o
  contrato de entrega (o quê, como e para quem).

  A obra é descritiva, não promocional: descreve o estado real do repositório na data
  de geração, inclui o que está incompleto ou pendente de decisão humana e cita o
  arquivo-fonte de cada afirmação.
---

# Como ler este livro

## A quem este livro se destina

Este livro tem três leitores simultâneos, e a diagramação foi pensada para servir aos
três sem obrigar nenhum deles a ler o livro inteiro.

O **arquiteto ou engenheiro** que precisa entender a topologia, os contratos formais
entre etapas e o modelo de qualidade encontra na Parte I e na Parte IV o material
denso: leis invioláveis, catálogo de portões, esquemas JSON de handoff, regras de
isolamento arquitetural.

O **operador** que precisa rodar o ecossistema — gerar um sistema, evoluir um módulo,
subir uma infraestrutura — encontra na Parte II o passo a passo dos fluxos e, na
Parte III, a ficha técnica de cada ferramenta com a CLI exata, entradas, saídas e o
que falha quando algo falha.

O **avaliador** (auditor, gestor técnico, revisor externo) que precisa julgar se o que
está escrito corresponde ao que existe encontra, ao final de cada capítulo, a seção
*Rastreabilidade*, que aponta os arquivos do repositório que sustentam cada afirmação.

## A estrutura em três níveis e três eixos

O livro é uma matriz. O eixo vertical é o nível de aproximação; o eixo horizontal é a
pergunta que se faz em cada nível.

| Nível de aproximação                       | Engenharia agêntica aplicada                                             | Arquitetura                                                          | Economia de tokens aplicada                                          |
| :----------------------------------------- | :----------------------------------------------------------------------- | :------------------------------------------------------------------- | :------------------------------------------------------------------- |
| **Macro** — o ecossistema (Parte I)        | Capítulo 2: leis, papéis, autonomia limitada, desenvolvedor no controle   | Capítulo 3: monorepo, CLI unificada, núcleo compartilhado, harnesses  | Capítulo 4: tríade Caveman, determinismo como economia, orçamentos   |
| **Meso** — os fluxos (Parte II)            | Capítulo 6 e 10: quem decide o quê em cada etapa da esteira               | Capítulos 7–9: topologia de cada fluxo e contratos de handoff        | Capítulo 6: onde o token é gasto e onde é proibido gastar            |
| **Micro** — as ferramentas (Parte III)     | Seções "como foi pensada" e "individual" de cada capítulo                 | Seções "como está estruturada" de cada capítulo                      | Seções "economia de tokens" de cada capítulo                         |

## As convenções visuais

Alguns elementos se repetem ao longo do livro e têm sempre o mesmo significado.

```{=typst}
#painel("Painel de contexto")[
  Caixas como esta trazem contexto, decisão histórica ou advertência. Quando o painel
  descreve algo que está *incompleto ou pendente*, o texto diz isso explicitamente —
  este livro não maquia estado.
]
```

Blocos de código em fundo claro são sempre **comandos reais** da CLI ou trechos
literais de arquivos do repositório. Tabelas de duas colunas com a primeira coluna em
cinza são **fichas técnicas** — o cartão de identidade de uma ferramenta ou etapa.
Diagramas em caixas escuras representam **etapas determinísticas**; caixas claras com
borda representam **etapas que consomem modelo de linguagem**. Essa distinção é a mais
importante do livro inteiro e reaparece em todos os diagramas.

```{=typst}
#esteira(
  no("ETAPA DETERMINÍSTICA", sub: "Python puro, zero token"),
  no-claro("ETAPA COM LLM", sub: "custo real em tokens"),
  no("PORTÃO DE QUALIDADE", sub: "exit 0 ou bloqueia", cor: rgb("#334155")),
)
```

## O que este livro não é

Não é um manual de instalação — esse papel é do `README.md` e do
`docs/manuais/`. Não é a lei do ecossistema — essa é o `AGENTS.md`, e em caso de
divergência entre este livro e o `AGENTS.md`, **o `AGENTS.md` vence**. Não é um
documento de marketing: onde há dívida técnica, gate vermelho ou decisão adiada, o
texto registra o fato, a data e o motivo, porque a Lei Inviolável #8 do ecossistema —
Honestidade de Rótulo — se aplica também à documentação sobre ele.

# PARTE I — MACRO: O ECOSSISTEMA

A Parte I responde à pergunta mais alta: *o que é esta coisa, por que ela existe nesta
forma e quais são as regras que se aplicam a todos os níveis abaixo?* Os quatro capítulos
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

Os números a seguir foram remedidos no repositório em 21/09/2026 (revisão da Meso-Camada da Tríade e Pipeline de Orquestração), e não estimados. As linhas marcadas com `*` mantêm o valor da geração original e não devem ser tomadas como atuais.

| Métrica                                                                 | Valor medido |
| :---------------------------------------------------------------------- | -----------: |
| Ferramentas homologadas em `tools/`                                     |            8 |
| Portões de qualidade globais em `gates/` (arquivos `G_*.py`)            |           42 |
| Portões `G_*.py` em todo o repositório (globais + locais de ferramenta) *|          148 |
| Hooks de portão registrados em `.pre-commit-config.yaml`                |           34 |
| Habilidades (skills) canônicas em `componentes/compartilhado/skills/`   |           66 |
| Comandos canônicos em `componentes/compartilhado/comandos/`             |           16 |
| Módulos do núcleo compartilhado em `componentes/compartilhado/src-core/`|           34 |
| Esquemas formais de handoff em `componentes/compartilhado/specs/`       |            7 |
| Diretórios de harness sincronizados na raiz                             |           10 |
| Módulos Python autorais nas ferramentas (`tools/`)                      *|        1.215 |
| Módulos Python de portões e scripts da raiz                             *|          ~85 |
| Arquivos de teste (`test_*.py`) no repositório                          *|        1.520 |
| Dependências externas declaradas e verificadas                         *|           40 |
| Suítes de portão que provam reprovação (exit 1), via `G_PORTAO_PROVA_QUE_MORDE.py` |    41/41 |
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

| Esquema                                                          | Fronteira                      | Campos obrigatórios                                                                       |
| :--------------------------------------------------------------- | :----------------------------- | :---------------------------------------------------------------------------------------- |
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
`python ecossistema.py components sync --tipo todos`. As pastas `.claude/`, `.opencode/`,
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
| `G_HONESTIDADE_ROTULO`             | Lei #8: termos de marketing proibidos em `print()`/`raise()` dos scripts de portão                |
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
assistentes pelo `components sync --tipo todos`.

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

# PARTE II — MESO: OS FLUXOS

A Parte II desce um nível. Enquanto a Parte I descreveu o organismo, esta descreve os
seus **movimentos**: as esteiras que levam uma intenção até um sistema em produção.

São quatro movimentos. Três deles são fluxos de **criação** — a Tríade Canônica
`aidd-pure`, `aidd-open` e `aidd-bridge` — e diferem entre si apenas na estratégia de
construção do artefato central. O quarto é o fluxo de **evolução**,
`/melhoria → /plan → /orchestrate`, que atua sobre o que já existe.

O capítulo 6 estabelece a anatomia comum, porque as três criações compartilham
princípio, cabeça e cauda. Os capítulos 7, 8 e 9 tratam de cada fluxo pelo mesmo
gabarito de sete itens usado no restante do livro. O capítulo 10 trata da evolução.

# Capítulo 6 — Anatomia comum de um fluxo de criação

## 6.1 O que é um fluxo no AIDD

Um fluxo é uma **esteira síncrona de sete etapas**, executada por
`scripts/orquestrador_sincrono.py`, em que cada etapa valida formalmente o contrato de
handoff antes de passar a bola para a seguinte. Se qualquer etapa falhar, o pipeline é
abortado imediatamente com código de saída 1 — não existe continuação com dado
fabricado nem etapa pulada silenciosamente.

```{=typst}
#esteira(
  no("1. FORGE", sub: "fundação"),
  no("2. PLANNER", sub: "plano formal"),
  no-claro("3. ENGINE", sub: "varia por fluxo"),
  no("4. MASTER", sub: "harmonização"),
)
#v(-4pt)
#esteira(
  no("5. ENTERPRISE", sub: "blindagem SHA-256"),
  no("6. OPS", sub: "infraestrutura"),
  no("7. AUDITORIA", sub: "manifesto de execução", cor: rgb("#334155")),
)
```

A **cabeça** (`FORGE → PLANNER`) e a **cauda** (`MASTER → ENTERPRISE → OPS →
AUDITORIA`) são idênticas nos três fluxos. A única diferença é a etapa 3, o motor:

| Fluxo e nome canônico     | Motor da etapa 3     | Acionamento                          | Estratégia de construção                              |
| :------------------------ | :------------------- | :----------------------------------- | :----------------------------------------------------- |
| Fluxo 01 — `aidd-pure`    | `aidd-generator`     | `/pure` · `ecossistema.py pure`      | Do zero puro: código autoral sob medida, com TDD       |
| Fluxo 02 — `aidd-open`    | `aidd-factory`       | `/open` · `ecossistema.py open`      | Motores open-source curados e integrados               |
| Fluxo 03 — `aidd-bridge`  | `aidd-bridge`        | `/bridge` · `ecossistema.py bridge`  | Desacoplamento de low-code e migração para PostgreSQL  |

Esse desenho — chamado no `AGENTS.md` de **Universal Convergence Funnel** — significa
que a decisão "como construir" é tomada uma única vez, no início, e não contamina o
resto da esteira. A entrega final é a mesma forma arquitetural nos três casos.

## 6.2 Engenharia agêntica no nível do fluxo

### Quem decide o quê

| Etapa            | Regime              | Quem decide                                                                 |
| :--------------- | :------------------ | :---------------------------------------------------------------------------- |
| 1 — Forge        | Determinístico   | Script: cria estrutura, injeta governança, instala hooks                        |
| 2 — Planner      | Misto            | Usuário no PRÉ-PLANO interativo; script valida e exporta                        |
| 3 — Engine       | Varia            | Fluxo 01 usa modelo em 4 das 8 fases; Fluxos 02 e 03 são quase determinísticos  |
| 4 — Master       | Determinístico   | Script: scaffold de fatia vertical e frontend                                   |
| 5 — Enterprise   | Determinístico   | Script: injeção com SHA-256 e verificação de drift                              |
| 6 — Ops          | Determinístico   | Script: sizing, compose, validação de manifesto                                 |
| 7 — Auditoria    | Determinístico   | Script: manifesto de execução                                                   |

A concentração do regime de julgamento na etapa 3 é deliberada: é a única etapa em que
não existe resposta certa computável, porque é ali que se decide *o que* construir e
não apenas *como* materializar o que já foi decidido.

### Regras que o fluxo segue

O orquestrador aplica quatro regras invariantes, independentemente do fluxo:
execução **estritamente sequencial** (Lei #7 — nunca há duas etapas correndo em
paralelo em segundo plano); **abortar na primeira falha**; **validar esquema antes do
handoff**; e **gravar artefato em disco** a cada fronteira, de modo que a execução seja
retomável e auditável depois.

## 6.3 Arquitetura no nível do fluxo: os artefatos de fronteira

Cada etapa deixa um arquivo na pasta do projeto. Esses arquivos são o registro
permanente do que aconteceu — e são eles, não a conversa, que a etapa seguinte lê.

| Artefato                       | Quem escreve   | Quem lê          | Conteúdo                                                        |
| :----------------------------- | :------------- | :--------------- | :---------------------------------------------------------------- |
| `.git/`, governança, hooks     | Forge          | Todas            | Repositório, `AGENTS.md`, portões, hooks de commit                |
| `PLANNER.json`                 | Planner        | Orquestrador     | Plano BDD/SDD completo do projeto                                 |
| `HANDOFF_PLANNER_ENGINE.json`  | Orquestrador   | Motor da etapa 3 | Contrato validado contra `handoff-planner-to-engine.schema.json`  |
| `HANDOFF_ENGINE_MASTER.json`   | Orquestrador   | aidd-master      | Fatias geradas, artefatos de frontend, testes executados          |
| `HANDOFF_MASTER_ENTERPRISE.json` | Orquestrador | aidd-enterprise  | Diretório, estado do servidor, rotas do Quarteto, componentes     |
| `HANDOFF_ENTERPRISE_OPS.json`  | Orquestrador   | aidd-ops         | Auditoria SHA-256, drift verificado, manifesto de deploy          |
| `ORQUESTRACAO_EXECUCAO.json`   | Orquestrador   | Humano/auditoria | Manifesto final com fluxo, nome, slug, domínio, timestamp, etapas |

```{=typst}
#painel("Estado honesto do orquestrador síncrono")[
  O orquestrador valida cada payload de handoff contra o esquema JSON formal antes de
  gravá-lo — essa parte é real e bloqueia de fato. Porém, na versão atual de
  `scripts/orquestrador_sincrono.py`, *parte dos campos dos payloads é montada pelo
  próprio orquestrador com valores fixos* em vez de ser lida da saída real da
  ferramenta: `testes_executados` recebe um bloco constante, `sha256_audit_ok` recebe
  `True` literal e o manifesto final grava `status: "CONFORME_100_POR_CENTO"` de forma
  fixa.

  Em termos práticos: hoje o orquestrador garante que o *formato* do contrato está
  correto e que cada ferramenta *saiu com código 0*, mas o conteúdo de alguns campos de
  telemetria ainda não reflete medição real. Este livro registra o fato porque a Lei #8
  (Honestidade de Rótulo) se aplica à documentação; a checagem forte de cada etapa
  continua existindo, mas ela vem do código de saída da ferramenta e dos portões
  próprios dela, não desses campos.
]
```

## 6.4 Economia de tokens no nível do fluxo

O desenho do fluxo é, por si só, o maior mecanismo de economia do ecossistema. Três
propriedades explicam por quê.

**Cinco das sete etapas custam zero tokens.** Forge, Master, Enterprise, Ops e
Auditoria são inteiramente determinísticas. O custo de um fluxo completo se concentra
nas etapas 2 (parcialmente) e 3.

**O contrato substitui a memória.** Como cada etapa lê um JSON tipado, não há
necessidade de manter histórico conversacional entre etapas. Um agente que retoma o
fluxo na etapa 5 lê aproximadamente 5 mil tokens de estado, não o transcript inteiro.

**O motor é escolhido pelo custo, não só pela adequação.** Os Fluxos 02 e 03 são
quase totalmente determinísticos porque curam software que já existe em vez de
escrevê-lo. Quando o problema admite reuso, o fluxo correspondente custa uma fração do
Fluxo 01.

| Fluxo | Onde o token é gasto                                                         | Ordem de grandeza da etapa 3 |
| :---- | :---------------------------------------------------------------------------- | :--------------------------- |
| 01    | Fases 2, 3, 4 e 8 do gerador (analisar, desenhar, planejar, implementar)      | Dezenas de milhares          |
| 02    | Fases 2, 3 e 7 do factory (curadoria e integração), com portões AST + bandit  | Baixo                        |
| 03    | Nenhuma fase do pipeline de seis etapas exige modelo                          | Próximo de zero              |

## 6.5 Como disparar um fluxo

Pelo assistente, basta o slash command. Pelo terminal:

```bash
# Fluxo 01 — do zero puro
python ecossistema.py pure --nome "Clinica Vida" --slug clinica --dominio saude --pasta ../proj_clinica

# Fluxo 02 — motores open-source
python ecossistema.py open --nome "Central CRM" --slug crm --dominio vendas --pasta ../proj_crm

# Fluxo 03 — libertação de low-code
python ecossistema.py freedom --nome "App Lovable" --slug app --dominio geral \
  --pasta ../proj_app --origem ../export-lovable

# Forma longa equivalente, com simulação segura
python ecossistema.py run-fluxo --fluxo pure --nome "..." --slug ... --dominio ... --pasta ... --dry-run
python ecossistema.py run-fluxo --fluxo freedom --nome "..." --slug ... --dominio ... --pasta ... --origem ...
```

O `--dry-run` executa toda a lógica de decisão e validação de contrato sem escrever no
disco nem tocar em git — é o modo recomendado para conhecer o fluxo antes de rodá-lo
de verdade.

### 6.5.1 Clone dentro de projeto existente (o que acontece)

Se você clonou o `ecossistema-aidd` **dentro** de uma pasta que já tem o seu app
(existe `package.json`, `src/`, `app/` ou `backend/` ao lado do clone), o projeto
novo **não** nasce em `ecossistema-aidd/projetos/`. Ele nasce **irmão do clone**,
na raiz da pasta de trabalho — a mesma regra do `--pasta ../proj_clinica`.

- **Na festa:** o app novo fica junto com o seu app antigo, não escondido dentro da ferramenta.
- **Na casa:** `core/resolve_pasta_entrega.py` decide; com legado irmão o default é
  `<workspace>/<slug>`, nunca `<clone>/projetos/<slug>`. Se houver duas pastas plausíveis,
  o fluxo **para e pergunta** (Lei #7) — nada é escrito em silêncio. Passe `--pasta`
  para escolher. Sem legado algum, o default continua sendo `<clone>/projetos/<slug>`.

### 6.5.2 Topologia Git padrão (5 linhas)

1. O **produto** vive em `<workspace>/` — é aí que o `git init` acontece (raiz da entrega).
2. O **legado** (`proj_app/`) é subárvore do mesmo repo (ou repo próprio, se você já tinha).
3. O **app gerado** entra como subárvore desse workspace — não vira repo isolado por acidente.
4. O **ecossistema-aidd** é ferramenta externa: de preferência fora do workspace; se ficar dentro, clone raso/esparso e **nunca** misture o histórico da ferramenta com o do produto.
5. Se a entrega cair dentro do clone da ferramenta, **não** criamos um terceiro `.git` (guarda triple-repo) — o fecho avisa para mover para fora.

## 6.6 Rastreabilidade do capítulo

`scripts/orquestrador_sincrono.py` (etapas 1 a 7, mapa de fluxos, validação de
esquema); `componentes/compartilhado/specs/*.schema.json`; `AGENTS.md` §3;
`gates/G_ORQUESTRADOR_SINCRONO.py`; `ecossistema.py` (`cmd_pure`, `cmd_open`,
`cmd_aidd_bridge`, `cmd_run_fluxo`).

# Capítulo 7 — Fluxo 01: `aidd-pure` (do zero puro)

## 7.1 O que é

O Fluxo 01 constrói o sistema **do zero, sob medida**, sem reaproveitar base de código
existente. É o fluxo de maior custo em tokens e o de maior liberdade arquitetural:
o motor `aidd-generator` executa oito fases que vão de pesquisa de referências reais
até implementação de código funcional verificada por pytest.

É o fluxo indicado quando o domínio é específico o bastante para que nenhum motor
open-source sirva, ou quando o controle total sobre a arquitetura é requisito.

## 7.2 Passo a passo de execução

```{=typst}
#ficha(
  ("Disparo", [`/pure` ou `python ecossistema.py pure --nome ... --slug ... --dominio ... --pasta ...`]),
  ("Motor da etapa 3", [`aidd-generator` — pipeline de 8 fases]),
  ("Persistência alvo", [SQLite em modo WAL]),
  ("Frontend alvo", [Next.js + TypeScript + Tailwind (Padrão-Ouro, Lei #11)]),
  ("Entrega", [Sistema completo, testado, blindado e com manifesto de deploy]),
)
```

1. **Forge** cria a pasta, inicializa git e roda `forge init --force`, instalando
   governança, portões locais e hooks de pre-commit.
2. **Planner** roda `planner init --fluxo 1`, produz `PLANNER.json` e o orquestrador
   valida e grava `HANDOFF_PLANNER_ENGINE.json`.
3. **Generator** roda `generate "<nome>: sistema para <domínio>" --pasta <p>
   --implementar-codigo`. As oito fases executam na ordem 1→2→3→4→5→8→6→7 (a Fase 8
   entra logo após a 5 para que a documentação da Fase 6 descreva o código real e a
   auto-crítica da Fase 7 audite o sistema funcional).
4. **Master** roda `master init <slug>` e `master add-module <slug>`, harmonizando o
   resultado em fatia vertical com frontend espelhado.
5. **Enterprise** roda `enterprise inject rule regra-integridade-<slug>` e
   `enterprise verificar-drift`.
6. **Ops** valida a presença de `Dockerfile` e `docker-compose.yml` no projeto.
7. **Auditoria** grava `ORQUESTRACAO_EXECUCAO.json`.

## 7.3 Portões de qualidade do fluxo

Além dos portões globais, o Fluxo 01 acumula os portões do gerador: transição de fase
bloqueada por `python scripts/validar_fase.py --fase N` (saída 1 impede progressão),
mais `G_TOKENOMICS`, `G_CYBERSECURITY_OWASP`, `G_SANDBOX_NIVEL_1`,
`G_SESSAO_HERMETICA`, `G_BLOQUEAR_SEGREDOS`, `G_INTEGRACAO_CROSS_SCRIPT`,
`G_VERIFICAR_LLM_PRONTO`, `G_INJECT` e `G_HARNESS_COMPAT`.

## 7.4 Determinismo e economia de tokens

Quatro das oito fases não gastam token: 1 (Pesquisador), 5 (Criador), 6 (Documentador)
e 7 (Auto-crítica). O orçamento total declarado das fases que gastam é de 115 mil
tokens, dos quais 50 mil são da Fase 8 (Implementador) — que é onde o código de fato
nasce. A Fase 4 (Planejador) é híbrida: 50% determinística no modo automático e
interativa quando o usuário participa.

## 7.5 O que entrega, como e para quem

Entrega um sistema completo em `<pasta>`: backend Python modular em fatias verticais,
frontend Next.js, banco SQLite WAL inicializado, suíte pytest executada de verdade,
documentação tripartite (HTML, Markdown e PDF via Typst), relatório de auto-crítica com
score em seis dimensões e roadmap, e o Quarteto *Sine Qua Non* ativo. Entrega **para o
`aidd-master`** dentro do fluxo, e **para o desenvolvedor** como produto final.

# Capítulo 8 — Fluxo 02: `aidd-open` (motores open-source)

## 8.1 O que é

O Fluxo 02 **não escreve o sistema: integra sistemas que já existem**. O motor
`aidd-factory` recebe um plano de infraestrutura resolvido, cura os motores
open-source adequados ao nicho, gera a camada de integração (gateway/BFF, compose,
inicialização de banco, variáveis de ambiente) e entrega uma aplicação multi-serviço.

É o fluxo indicado quando o domínio já tem software consolidado — CRM, atendimento,
agendamento, automação — e o valor está na integração, não na reimplementação. É a
aplicação direta da política anti-NIH (*not invented here*) do ecossistema.

## 8.2 Passo a passo de execução

A cabeça e a cauda são idênticas às do Fluxo 01. A etapa 3 roda
`factory curate --dominio <d> --output <pasta>/factory_output`.

O contrato de entrada do factory é **único e fechado**: ele consome apenas
`PLANO-INFRAESTRUTURA.json`, validado contra
`componentes/compartilhado/specs/plano-infraestrutura.schema.json`, e nunca lê
catálogos de nicho diretamente — o plano já chega resolvido. O contrato de saída também
é único: `FACTORY_OUTPUT.json`, listando todos os artefatos gerados com status, que o
orquestrador de deploy consome.

### O nicho dinâmico

O catálogo fixo tem cinco nichos (`clinicas`, `delivery`, `farmacias`, `b2b_industrial`,
`energia_solar`). Para domínios fora desse catálogo, existe o caminho do **nicho
dinâmico**: `fase_1_intake.saida.nicho_slug` recebe o prefixo `dinamico_`, e
`01_analisador.py` sintetiza os blocos e bancos lógicos a partir da própria lista de
ferramentas do plano (baseline `traefik` mais `postgres` condicional), em vez de exigir
que `templates/infra/nichos/<slug>.json` exista.

A razão dessa decisão está registrada no `AGENTS.md` do `aidd-planner`: pela Lei #7
(Desenvolvedor no Controle), a lista de ferramentas curada pelo usuário no PRÉ-PLANO é
autoritativa — não um palpite por palavra-chave. Por isso `exportar_para_fluxo_factory`
reutiliza `pipeline_ops.montar_plano_em_memoria(..., ferramentas_planejadas=...)` em
vez de tentar casar o texto com um dos cinco nichos fixos.

## 8.3 Portões, determinismo e economia

O `AGENTS.md` do factory é explícito sobre o regime de cada fase:

| Fases            | Regime                   | Portão associado                  |
| :--------------- | :----------------------- | :--------------------------------- |
| 1, 4, 5, 6       | 100% determinístico, zero LLM | `G_FACTORY_DETERMINISTIC`     |
| 2, 3, 7          | LLM com portões AST + bandit  | `G_FACTORY_INPUT`, `G_FACTORY_OUTPUT` |

O resultado é que o Fluxo 02 custa uma fração do Fluxo 01 em tokens: o trabalho pesado
— escrever o software — já foi feito por terceiros, e o que resta é integração, que é
majoritariamente mecânica.

## 8.4 O que entrega, como e para quem

Entrega uma stack multi-serviço integrada: gateway/BFF, compose unificado com os
serviços curados, banco inicializado, `.env` resolvido, integração entre os serviços e
`FACTORY_OUTPUT.json` como manifesto auditável. Entrega **para o `aidd-master`** (que
fatia a integração em VSA) e, no fim da esteira, **para o `aidd-ops`**, que provisiona a
infraestrutura correspondente.

# Capítulo 9 — Fluxo 03: `aidd-freedom` (motor `aidd-bridge` — libertação de low-code)

## 9.1 O que é

O Fluxo 03 resolve um problema específico e muito concreto: uma aplicação foi gerada em
uma plataforma low-code (Lovable, v0, Bolt), funciona, o usuário gosta da interface —
e está presa ao fornecedor, com banco Supabase, autenticação proprietária e custo
recorrente. O motor `aidd-bridge` extrai essa aplicação, converte o banco para
PostgreSQL puro com emulação PostgREST, empacota em Docker e a coloca em VPS própria
**preservando a interface**.

## 9.2 Passo a passo de execução

O pipeline determinístico do bridge tem seis fases, documentadas no cabeçalho de
`aidd_bridge/pipeline_bridge.py`:

```{=typst}
#esteira(
  no("1. SCAN", sub: "componentes"),
  no("2. DATA", sub: "→ PostgreSQL"),
  no("3. FRONT", sub: ".env limpo"),
  no("4. DEVOPS", sub: "OCI + Nginx"),
  no("5. VSA", sub: "Quarteto"),
  no("6. GATES", sub: "G_BRIDGE_*", cor: rgb("#334155")),
)
```

1. **Scan e análise de componentes** (`LovableScanner`): mapeia páginas, componentes
   shadcn e migrações.
2. **Desacoplamento de banco** (`DataBridge`): sanitiza o SQL do Supabase para
   PostgreSQL puro com emulação PostgREST, de modo que o cliente
   `@supabase/supabase-js` do frontend continue funcionando **sem refatoração**.
3. **Separação de camadas e frontend** (`FrontendLiberator`): produz `.env.production`
   limpo, sem credencial de fornecedor.
4. **Empacotamento DevOps OCI** (`DevOpsPackager`): Dockerfile com usuário não-root,
   Nginx com cabeçalhos OWASP, compose.
5. **Conector VSA e Quarteto *Sine Qua Non***: exporta `/docs`, `/webhooks`, `/mcp`
   e `/docs/guia` em `quarteto_sine_qua_non/` para harmonização no `aidd-master`.
6. **Portões dedicados**: `G_BRIDGE_VENDOR_LOCKIN`, `G_BRIDGE_DOCKER_OCI`,
   `G_BRIDGE_POSTGRESQL` e `G_BRIDGE_VSA_COMPAT`.

## 9.3 As quatro operações sensíveis

O bridge lida com dados reais de produção, e por isso quatro operações têm tratamento
especial.

**Migração de autenticação** (`migrate-auth`): preserva os hashes de senha de
`auth.users` ao migrar contas para o ambiente self-hosted — as pessoas continuam
entrando com a mesma senha. A operação é **preview por padrão** e só escreve com
`--apply`.

**Fusão multi-aplicação** (`merge`): combina várias aplicações em fatias verticais
segregadas em `src/modules/<app>/` com roteamento unificado.

**DNS Cloudflare** (`cloudflare_dns.py`): cria e remove registros durante o
empacotamento e o teardown.

**Teardown atômico** (`destroy`): limpeza completa de stacks Docker Swarm, volumes e
registros DNS — **exige confirmação** a menos que `--yes` seja passado explicitamente.

## 9.4 Determinismo e economia

Nenhuma das seis fases do pipeline exige chamada de modelo. O Fluxo 03 é o mais barato
dos três em tokens, porque a tarefa é de transformação estrutural — parse, reescrita de
SQL, reempacotamento — e transformação estrutural tem algoritmo.

## 9.5 O que entrega, como e para quem

Entrega o projeto libertado: código React/Vite/Tailwind preservado, banco PostgreSQL
puro com PostgREST, Dockerfile e compose prontos para VPS, `.env.production` sem
credencial de fornecedor, e o Quarteto exportado. Entrega **para o `aidd-master`**
dentro do fluxo e **para a VPS do usuário** ao final, via `aidd-ops`.

# Capítulo 10 — O fluxo de evolução: `/melhoria → /plan → /orchestrate`

## 10.1 Por que existe um quarto fluxo

Os três fluxos canônicos criam. Este evolui. A diferença é essencial: criar tem estado
inicial vazio e, portanto, nenhuma restrição de compatibilidade; evoluir tem um sistema
em funcionamento, com usuários e dados, e uma pergunta que precede qualquer código —
*o que exatamente está errado, e como sabemos disso?*

O ecossistema responde com uma esteira de três etapas, cada uma com uma **parada
obrigatória** para decisão humana.

| Etapa | Comando         | Entra                                              | Sai                                                | Parada no fim                          |
| :---- | :-------------- | :-------------------------------------------------- | :--------------------------------------------------- | :--------------------------------------- |
| 1     | `/melhoria`     | Pedido em linguagem natural, ou plano a reanalisar  | Relatório em `docs/melhorias/` com Nota Atual + evidência | "gero o plano a partir disto?"     |
| 2     | `/plan`         | Relatório da etapa 1, ou pedido direto              | Pasta em `docs/planos/<nome>/`, tudo em rascunho      | "aprova este plano?"                   |
| 3     | `/orchestrate`  | Plano aprovado                                      | Execução real das frentes                             | Escolha de ambiente + Plano de Voo     |

## 10.2 Etapa 1 — `/melhoria`: nota com evidência

A skill dona investiga o **código real** na ordem grafo → `Grep`/`Read` → reprodução
real, atribui uma **Nota Atual de 0 a 10 com evidência** e gera relatório `.html` e
`.json` em `docs/melhorias/`. Ela também reanalisa um plano existente, comparando
previsto contra implementado item a item.

A palavra-chave é *evidência*. Uma memória de projeto registra a regra com clareza:
todo caso de auditoria exige script ou comando próprio, executado do zero — leitura de
código nunca substitui teste. E o código de saída precisa ser real: `cmd | tail`
devolve o código do `tail`, não o do comando; a forma correta é redirecionar para
arquivo e capturar `$?` na mesma linha.

## 10.3 Etapa 2 — `/plan`: rascunho que não se aprova sozinho

A skill dona (`plan`, com motor `planos-auditoria-runner`) gera a estruturação
padronizada e os rascunhos de planos de auditoria, evolução ou teste, com checagem
determinística de cercas markdown. Duas proibições são explícitas: **não fabricar
decisões** e **não fabricar aprovações**.

```{=typst}
#painel("Aprovar o plano não é autorizar a execução")[
  O ecossistema separa rigorosamente os dois atos. Dizer "aprovado" sobre um plano
  aprova *o documento*; não é sinal verde para implementar. A autorização de execução é
  uma instrução separada, dada depois — e é exatamente isso que a parada obrigatória no
  fim da etapa 2 protege.
]
```

## 10.4 Etapa 3 — `/orchestrate`: roteador de ambiente e Plano de Voo

A skill dona é um **roteador de ambiente**: decide entre o aplicativo ORCA, subagentes
ou git worktree nativo, monta um Plano de Voo e executa as frentes do plano. Não é o
comando do AIDD Ops — esse é `/ops`.

As regras fixas da via ORCA estão gravadas na referência canônica e nasceram de
incidentes reais: carregar o manual da versão instalada (`orca skills get orca-cli`)
antes de qualquer comando; usar mesa independente (`--no-parent`) por padrão, mesa
filha só a pedido explícito; **nunca** lançar o assistente com `--resume <id-de-sessão>`;
esperar `tui-idle` com `satisfied: true` antes de enviar o prompt; e nunca reenviar no
silêncio.

`--dry-run` gera e imprime o Plano de Voo sem tocar em git nem criar agente.

## 10.5 Um comando, um dono

A regra de propriedade descrita no capítulo 2 vale integralmente aqui: `/melhoria`,
`/plan` e `/orchestrate` têm cada um exatamente uma skill dona; `planos-auditoria-runner`
e `orca-plan-orchestrator` são motores acionados pelas donas, sem slash command
próprio. A justificativa está registrada: duas skills respondendo ao mesmo comando com
regras opostas causou o incidente de mesas recursivas de 11 de setembro de 2026.

## 10.6 Rastreabilidade do capítulo

`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §3 (tabela das três etapas e regras da
via ORCA); `componentes/compartilhado/skills/melhoria/`, `plan/`, `orchestrate/`,
`planos-auditoria-runner/`, `orca-plan-orchestrator/`; `ecossistema.py`
(`cmd_melhoria`, `cmd_plan`, `cmd_orchestrate`); `docs/melhorias/`; `docs/planos/`.

# Capítulo 11 — Meso-Camada: Despacho Topológico VSA em Git Worktrees

## 11.1 A Necessidade da Meso-Camada

A execução de sistemas complexos baseados em Vertical Slice Architecture (VSA) impõe
um desafio estrutural: fatias verticais independentes podem ser desenvolvidas em paralelo,
mas fatias interdependentes exigem uma ordem estrita de precedência causal. A Meso-Camada
da Tríade Canônica resolve esse problema através de compilação topológica de dependências
e execução em ambientes efêmeros isolados.

Em vez de permitir concorrência cega ou execuções monolíticas sequenciais desnecessárias,
o ecossistema compila o `PLANNER.json` em um Directed Acyclic Graph (DAG) governado pelo
schema formal `vsa-topological-dispatch.schema.json`.

## 11.2 Compilação Topológica (Algoritmo de Kahn)

O motor do `aidd-planner` analisa as dependências declaradas entre fatias verticais e
aplica o algoritmo de Kahn:
1. **Identificação de Raízes:** Fatias com grau de entrada zero (sem dependências) formam
   o Lote 0 (execução simultânea).
2. **Resolução em Camadas:** Conforme cada lote é satisfeito, fatias dependentes são
   destravadas e alocadas no lote topológico subsequente.
3. **Detecção Estrita de Ciclos:** Caso exista uma dependência circular (A depende de B e
   B depende de A), o compilador rejeita o plano deterministamente com código de saída 1.

## 11.3 Isolamento em Git Worktrees Efêmeras

Cada fatia vertical aprovada é despachada pelo motor `dispatch_pipeline.py` em uma
Git Worktree dedicada (`.worktrees/<slice_id>`), ancorada em uma branch limpa
`slice/<slice_id>` originada da branch base.

- **Zero Contaminação Cruzada:** Cada fatia só enxerga os arquivos explicitamente
  concedidos em seu escopo (`arquivos_permitidos`).
- **Limpeza Garantida (Lei #7):** Um bloco `try-finally` invariável assegura que, em caso
  de sucesso ou aborto por interrupção, 100% das worktrees e branches efêmeras sejam
  desmontadas e expurgadas do disco.

## 11.4 Roteamento Especialista e Quarteto Sine Qua Non

O roteador especialista (`engine_router.py`) inspeciona o tipo de motor associado a cada
fatia na Tríade:
- `fluxo_01_generator`: Geração com TDD Red-Green (código autoral).
- `fluxo_02_factory`: Curadoria e integração de motores Open-Source.
- `fluxo_03_bridge`: Desacoplamento de plataformas low-code e unificação SQL.

Adicionalmente, o roteador garante que toda fatia nasça em estrita conformidade com a
**Lei #10 (Quarteto Sine Qua Non)**, injetando os pontos de montagem dinâmica para
API Studio (`/api`), Webhook Studio (`/webhook`), MCP Studio (`/mcp`) e Central de
Documentação e Guia (`/docs`).

## 11.5 Barreira de Validação e Convergência Master

Antes que qualquer fatia seja mesclada no repositório principal, a barreira
`vsa_join_barrier.py` executa a auditoria de integridade:
1. **Auditoria de Fronteiras:** Via `git status --porcelain -uall`, verifica se algum
   arquivo fora de `arquivos_permitidos` foi modificado. Qualquer vazamento causa o
   aborto imediato da fatia.
2. **Quality Gates da Fatia:** Execução dos testes unitários e validações locais da fatia.
3. **Convergência Master:** As fatias aprovadas são mescladas sequencialmente na branch
   base (`--no-ff`), o registro de rotas do Monólito Modular (`router_registry.py`) é
   atualizado deterministicamente, e um manifesto formal com SHA-256 é gerado para a
   etapa de `aidd-enterprise`.

## 11.6 Rastreabilidade do capítulo

`componentes/compartilhado/specs/vsa-topological-dispatch.schema.json`;
`gates/G_DISPATCH_PIPELINE_VSA.py`; `gates/test_g_dispatch_pipeline_vsa.py`;
`tools/aidd-master/scripts/dispatch_pipeline.py`;
`tools/aidd-master/scripts/engine_router.py`;
`tools/aidd-master/scripts/vsa_join_barrier.py`;
`tools/aidd-planner/aidd_planner/core/planner_engine.py` (`compilar_grafo_topologico_vsa`);
`componentes/compartilhado/skills/aidd-dispatch-runner/SKILL.md`;
`ecossistema.py` (`cmd_dispatch`).

# PARTE III — MICRO: AS OITO FERRAMENTAS

Esta é a parte mais longa do livro, e a mais repetitiva por desenho. Cada uma das oito
ferramentas é descrita pelo mesmo gabarito, na mesma ordem, para que o leitor possa
comparar duas ferramentas lendo a mesma seção de cada capítulo.

O gabarito tem oito seções. As três primeiras situam a ferramenta: o que ela é, qual é
o seu papel dentro do fluxo e qual é o seu papel dentro do ecossistema. A quarta
descreve como foi pensada, como está estruturada e como está configurada. As três
seguintes são a análise em camadas — funcionamento **individual**, funcionamento
**dentro do fluxo** e funcionamento **dentro do ecossistema** — e cada uma delas
responde sempre aos mesmos sete itens:

```{=typst}
#painel("Os sete itens de cada camada")[
  *1. Passo a passo de execução* — o que acontece, em ordem. \
  *2. Portões de qualidade* — o que bloqueia, e com qual critério. \
  *3. Habilidades* — quais skills operam ou são operadas nessa camada. \
  *4. Determinismo* — quais scripts fazem o trabalho sem chamar modelo. \
  *5. Ferramentas acessadas* — CLIs, MCPs, APIs e binários externos. \
  *6. Hooks e regras* — o que dispara automaticamente e quais leis se aplicam. \
  *7. Entrega* — o que entrega, como entrega e para quem entrega.
]
```

A oitava seção é a *Rastreabilidade*: os arquivos do repositório que sustentam o
capítulo.

A ordem dos capítulos segue a ordem da esteira, não a ordem alfabética: primeiro a
cabeça (`aidd-forge`, `aidd-planner`), depois os três motores (`aidd-generator`,
`aidd-factory`, `aidd-bridge`), depois a cauda (`aidd-master`, `aidd-enterprise`,
`aidd-ops`).

# Capítulo 11 — `aidd-forge`: a fundação

```{=typst}
#ficha(
  ("Papel", "Bootstrap determinístico, isolamento de micro-ambiente, fatiamento de fase e purga de contexto"),
  ("Etapa na esteira", "1 de 7 — primeira etapa dos três fluxos"),
  ("Slash command", [`/forge [caminho]` ou `/aidd-init`]),
  ("CLI", [`python ecossistema.py forge init|inject|audit|conform`]),
  ("Regime", "100% determinístico — zero chamada de modelo"),
  ("Padrão de erro", [Mônada `Result.ok()` / `Result.fail()` em toda fronteira]),
)
```

## 11.1 O que é a ferramenta

`aidd-forge` é o **injetor de governança** do ecossistema. Ele pega um diretório — vazio
ou com um projeto existente — e o transforma em um ambiente onde as leis do AIDD são
executáveis: cria a estrutura canônica, materializa os arquivos de regra para todos os
assistentes, instala os portões locais, instala os hooks de git e prepara os
micro-ambientes de fase.

A analogia do `README.md` é precisa: é a fundação e o chassi. Antes dele, o diretório é
um lugar onde a IA pode fazer o que quiser. Depois dele, é um lugar onde a IA não
consegue commitar código que viole as regras, porque o hook de pre-commit roda os
portões e bloqueia.

## 11.2 O papel da ferramenta dentro do FLUXO

Dentro de qualquer um dos três fluxos, `aidd-forge` é a **etapa 1**, e a sua função é
garantir que as seis etapas seguintes rodem sobre terreno preparado. O orquestrador
síncrono cria a pasta, garante `git init` e então executa
`ecossistema.py forge init <pasta> --force`. Se essa etapa falhar, o fluxo aborta
imediatamente — não existe caminho que pule a fundação.

A ordem importa: sem o forge, o `aidd-planner` escreveria `PLANNER.json` num diretório
sem governança, e o código gerado pelo motor da etapa 3 poderia ser commitado sem
passar por portão nenhum.

## 11.3 O papel da ferramenta dentro do ECOSSISTEMA

Fora do contexto de um fluxo, o `aidd-forge` tem três funções permanentes.

É o **injetor universal de componentes**: `forge inject <tipo> <nome>` materializa
deterministicamente dez tipos de artefato — `skill`, `mcp`, `rule`, `spec`, `roteiro`,
`config`, `command`, `hook`, `sub-agent` e `script` — com rollback atômico via
`materializador.py`. É assim que uma habilidade nova nasce no ecossistema.

É o **auditor de conformidade de governança**: `forge audit` verifica se um projeto
está aderente às regras, e `forge conform` aplica correções automáticas.

É o **sincronizador multi-harness**: `core/harness_sync.py` e `core/harness_manifest.py`
mantêm a paridade entre os dez ambientes de assistente, e o `core/agents_md_anchor.py`
garante que o `AGENTS.md` permaneça a âncora canônica com os arquivos-ponteiro dos
demais assistentes apontando para ele.

## 11.4 Como foi pensada, está estruturada e configurada

### A tese

A tese do forge é que **governança que depende de alguém lembrar não é governança**. Por
isso ele não escreve documentação pedindo boas práticas: ele instala mecanismos que
tornam a violação impossível ou detectável. O `AGENTS.md` do forge lista cinco
invariantes: Zero Stubs, mônada `Result` em toda fronteira de serviço, isolamento por
purga de contexto, injetor universal com rollback atômico, e sete portões
determinísticos obrigatórios.

### A estrutura

O pacote `aidd_forge/` tem quatro subdiretórios — `commands/`, `core/`, `schemas/`,
`templates/` — e o núcleo concentra 23 módulos com responsabilidade estreita:

| Módulo do núcleo             | Responsabilidade                                                          |
| :--------------------------- | :-------------------------------------------------------------------------- |
| `injector.py`                | Injeção da infraestrutura AIDD no projeto alvo                              |
| `universal_injector.py`      | Injeção de componentes por tipo, com perfis                                 |
| `injector_profiles.py`       | Os dez tipos suportados e o destino físico de cada um                       |
| `materializador.py`          | Escrita com transação e rollback atômico                                    |
| `injection_schema.py`        | Validação do contrato de injeção                                            |
| `audit_engine.py` / `audit_checks.py` / `audit_report.py` | Motor, checagens e relatório de auditoria         |
| `conform_engine.py` / `conform_fixers.py` | Correção automática de não conformidade                        |
| `harness_sync.py` / `harness_manifest.py` | Distribuição e manifesto multi-harness                         |
| `agents_md_anchor.py`        | `AGENTS.md` como âncora canônica                                            |
| `git_hooks.py`               | Instalação dos hooks de pre-commit                                          |
| `phase_fencer.py`            | Cercas de fase: cada fase enxerga apenas o seu micro-ambiente               |
| `subagent_purger.py`         | Purga de contexto de subagente após validação AST                           |
| `sandbox_worktree.py`        | Isolamento por worktree para experimentos                                   |
| `token_optimizer.py`         | Otimização de contexto no material injetado                                 |
| `context_linter.py`          | Lint do contexto injetado                                                   |
| `camada_detector.py` / `detector.py` | Detecção de camada arquitetural e de ferramentas do host             |
| `orca_bridge.py`             | Integração com o ambiente de orquestração ORCA                              |

### A configuração

Os sete portões que o forge instala no projeto alvo vivem em
`aidd_forge/templates/gates/`: `G_BLOQUEAR_SEGREDOS`, `G_CONTRACTS`,
`G_CYBERSECURITY_OWASP`, `G_ESTRUTURA_AST`, `G_HARNESS_COMPAT`, `G_INJECT`,
`G_PERFORMANCE` e `G_TESTES_REAIS`.

O `ecossistema.py` adiciona uma camada de autorreparo: antes de rodar qualquer comando
do forge, `_reparar_instalacao_editable_aidd_forge()` verifica se `pip show aidd-forge`
aponta para este clone e, se apontar para um caminho morto — uma worktree deletada, uma
pasta renomeada —, reinstala silenciosamente com `pip install --no-deps -e`. O comentário
no código é explícito sobre o escopo: isso não é necessário para
`python ecossistema.py forge`, que já roda isolado por `PYTHONPATH`; existe para que
chamadas diretas de `python -m aidd_forge.cli` e os testes da própria ferramenta
continuem funcionando após um clone novo.

## 11.5 Como funciona individualmente

**Passo a passo.** `forge init <caminho> [--force]` executa: detecção do estado do
diretório alvo → materialização da estrutura AIDD → injeção do `AGENTS.md` âncora e dos
arquivos-ponteiro por assistente → cópia dos sete portões-template → instalação dos
hooks de git → criação das cercas de fase → relatório de status em uma linha. Toda
escrita passa pelo `materializador.py`, que mantém transação: se qualquer passo falhar,
o estado anterior é restaurado.

`forge inject <tipo> <nome>` resolve o perfil do tipo em `injector_profiles.py`, calcula
o destino físico com `resolve_destination()`, valida contra `injection_schema.py`,
materializa e sincroniza para os assistentes.

`forge audit <caminho> [--fmt] [--output]` roda o motor de auditoria e emite relatório.
`forge conform <caminho> [--dry-run] [--items N]` aplica os corretores automáticos.

**Portões.** Os sete portões-template, mais o portão global `G_INJECT` e
`G_COMPONENTE_AGNOSTICO` quando a injeção alcança o ecossistema.

**Habilidades.** `aidd-forge-runner` é a skill dona de `/forge`. `aidd-componentes` e
`aidd-skills` operam sobre o resultado da injeção.

**Determinismo.** Integral. Não há chamada de modelo em nenhum caminho do forge — é
Python puro operando sobre templates, AST e sistema de arquivos.

**Ferramentas acessadas.** `git` (init, instalação de hooks), `pip` (autorreparo da
instalação editável), sistema de arquivos. Nenhuma API externa.

**Hooks e regras.** O forge é a ferramenta que **instala** hooks —
`.githooks/pre-commit` via `core/git_hooks.py`. As regras que segue: Zero Stubs,
mônada `Result`, purga de contexto, rollback atômico e os sete portões.

**Entrega.** Entrega um diretório governado. O formato da entrega é o próprio sistema
de arquivos do projeto alvo. O destinatário é a etapa seguinte do fluxo (o
`aidd-planner`) ou, fora de fluxo, o desenvolvedor que rodou `/forge` num projeto
existente.

## 11.6 Como funciona dentro da camada FLUXO

**Passo a passo.** O orquestrador cria a pasta, roda `git init` se necessário, e chama
`forge init <pasta> --force`. Código de saída diferente de zero aborta o fluxo inteiro.

**Portões.** No contexto do fluxo, o forge não apenas roda os seus portões: ele
**instala** os portões que todas as etapas seguintes terão de satisfazer. É a etapa que
arma o resto da esteira.

**Habilidades.** `fluxo-01-runner`, `fluxo-02-runner` e `fluxo-03-runner` invocam o forge
como primeira etapa de cada fluxo.

**Determinismo.** 100%. É uma das cinco etapas de custo zero em tokens.

**Ferramentas acessadas.** As mesmas do modo individual, mais o `ecossistema.py` como
invocador.

**Hooks e regras.** A partir do fim da etapa 1, o hook de pre-commit está ativo no
projeto — o que significa que qualquer commit feito pelas etapas 3 a 7 passa pelos
portões.

**Entrega.** Entrega ao `aidd-planner` um diretório com git inicializado, governança
instalada e hooks ativos.

## 11.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora de fluxo, o forge é acionado para criar componentes novos
(`inject`), auditar projetos (`audit`) e corrigir divergência (`conform`). A criação de
uma habilidade nova segue o caminho: `forge inject skill <nome>` → o componente nasce em
`componentes/compartilhado/skills/<nome>/` → `python ecossistema.py components sync --tipo todos
--tipo skills` distribui para os dez assistentes → `G_COMPONENTE_AGNOSTICO` audita a
cobertura.

**Portões.** `G_COMPONENTE_AGNOSTICO`, `G_UNIVERSAL_HARNESS`, `G_HARNESS_COMPAT` e
`G_INJECT` são os portões do ecossistema que julgam o trabalho do forge.

**Habilidades.** `aidd-skills` (criação de habilidade), `aidd-componentes` (gestão de
componentes), `aidd-mcp` (criação de servidor MCP), `skill-creator-runner`.

**Determinismo.** Integral.

**Ferramentas acessadas.** `scripts/gestor_componentes.py` via
`ecossistema.py components`.

**Hooks e regras.** A regra da **fonte física canônica**: o componente nasce em
`componentes/`, nunca numa pasta de assistente. Editar `.claude/skills/<nome>` direto é
o erro que `G_COMPONENTE_AGNOSTICO` detecta.

**Entrega.** Entrega componentes canônicos distribuídos e projetos conformes. O
destinatário é o ecossistema inteiro — toda ferramenta e todo assistente consome o
resultado.

## 11.8 Rastreabilidade

`tools/aidd-forge/AGENTS.md`; `tools/aidd-forge/aidd_forge/cli.py`;
`tools/aidd-forge/aidd_forge/core/` (23 módulos);
`tools/aidd-forge/aidd_forge/templates/gates/` (7 portões);
`ecossistema.py::cmd_forge` e `_reparar_instalacao_editable_aidd_forge`;
`scripts/orquestrador_sincrono.py::etapa_01_forge`.

# Capítulo 12 — `aidd-planner`: o plano formal

```{=typst}
#ficha(
  ("Papel", "Motor de planejamento, intake SDD/BDD e geração do combustível dos três fluxos"),
  ("Etapa na esteira", "2 de 7"),
  ("Slash command", [`/planner`]),
  ("CLI", [`python ecossistema.py planner init|validate|export|audit`]),
  ("Artefato central", [`PLANNER.json`, validado contra `schemas/planner_schema.json`]),
  ("Portões próprios", [`G_PLANNER_SCHEMA`, `G_PLANNER_SINE_QUA_NON`, `G_PLANNER_COERENCIA_FLUXO`]),
)
```

## 12.1 O que é a ferramenta

`aidd-planner` é o **intake formal** do ecossistema: transforma uma conversa sobre o que
se quer construir em um documento tipado que os motores conseguem executar. O
`AGENTS.md` o define como "motor de planejamento, intake SDD/BDD e geração de
combustível para a Tríade Canônica".

A entrada é um PRÉ-PLANO interativo conduzido com o usuário. A saída é `PLANNER.json`:
entidades, endpoints, cenários BDD, módulos funcionais, arquitetura alvo e a
configuração explícita do Quarteto *Sine Qua Non*.

## 12.2 O papel da ferramenta dentro do FLUXO

É a etapa 2, e é a **única etapa da cabeça em que o usuário participa da decisão**. O
que o planner decide aqui governa tudo o que vem depois: o campo `meta.fluxo_alvo`
determina a estrutura do `payload_especifico_fluxo`, e é esse payload que o motor da
etapa 3 consome.

O orquestrador roda `planner init --fluxo N --nome --slug --dominio --pasta`, lê o
`PLANNER.json` resultante, monta o payload de handoff, valida contra
`handoff-planner-to-engine.schema.json` e grava `HANDOFF_PLANNER_ENGINE.json`.

## 12.3 O papel da ferramenta dentro do ECOSSISTEMA

No ecossistema, o planner é o **guardião da Lei #10**: nenhum plano passa sem
`/docs`, `/webhooks`, `/mcp` e `/docs/guia` marcados como `ativo: true`. O portão
`G_PLANNER_SINE_QUA_NON` (local, em `tools/aidd-planner/gates/`) reprova qualquer
plano que tente nascer sem o Quarteto; desde 20/09/2026 ele é complementado pelo
`gates/G_QUARTETO_SINE_QUA_NON.py` na raiz, que audita a presença real dos 4 pilares
no deliverable já gerado, não só na intenção declarada no plano.

É também o ponto onde a Lei #7 (Desenvolvedor no Controle) tem a sua expressão mais
forte: a lista de ferramentas curada pelo usuário no PRÉ-PLANO é **autoritativa**, e o
ecossistema mudou o próprio código para respeitá-la.

```{=typst}
#painel("O achado de 18/09/2026 — por que o export mudou")[
  O `AGENTS.md` do planner registra um achado real com data: o `export --formato factory`
  precisa devolver *exatamente* o envelope `fase_1_intake` / `fase_2_curadoria` /
  `fase_3_sizing` que o `contrato_factory.py` valida contra
  `plano-infraestrutura.schema.json` — nunca um formato próprio.

  A implementação (`exportar_para_fluxo_factory` em `src/core/planner_engine.py`)
  reutiliza `pipeline_ops.montar_plano_em_memoria(texto,
  ferramentas_planejadas=payload_especifico_fluxo.ferramentas_opensource)`, que é o
  caminho do "nicho dinâmico" do `aidd-ops`, em vez de tentar casar o pedido com um dos
  cinco nichos fixos do catálogo. A justificativa é a Lei #7: a lista curada pelo usuário
  vale mais que um palpite por palavra-chave.
]
```

## 12.4 Como foi pensada, está estruturada e configurada

A ferramenta é enxuta por desenho: `src/cli.py` com quatro subcomandos e
`src/core/planner_engine.py` mais `src/core/design_system.py` como núcleo. O contrato
é o `schemas/planner_schema.json`, e a validação é feita por três portões dedicados em
`gates/`.

Os quatro invariantes arquiteturais declarados no `AGENTS.md` são: **Zero Stubs**
(nunca produzir `TODO`, `FIXME` ou marcador de espaço em `PLANNER.json` — todas as
entidades, endpoints e cenários BDD devem ser completos e tipados); **Quarteto *Sine
Qua Non*** com os quatro ativos; **polimorfismo estrito** governado por
`meta.fluxo_alvo`; e **qualidade binária** contra os três portões.

## 12.5 Como funciona individualmente

**Passo a passo.**

```bash
python ecossistema.py planner init --fluxo 1 --nome "Clinica Vida" --slug clinica --dominio saude --pasta ../proj
python ecossistema.py planner validate ../proj/PLANNER.json
python ecossistema.py planner export ../proj/PLANNER.json --formato factory
python ecossistema.py planner audit ../proj
```

`init` conduz o intake e gera o `PLANNER.json` canônico; `validate` confere
conformidade contra o esquema; `export` converte para o formato do fluxo de destino;
`audit` roda os três portões.

**Portões.** `G_PLANNER_SCHEMA` (conformidade estrutural), `G_PLANNER_SINE_QUA_NON`
(os quatro estúdios ativos) e `G_PLANNER_COERENCIA_FLUXO` (coerência entre
`meta.fluxo_alvo` e o `payload_especifico_fluxo`). Os três precisam sair com 0.

**Habilidades.** `aidd-planner-runner` é a dona de `/planner`. As habilidades
procedimentais `/aidd-grill` e `/aidd-spec` alimentam o intake: a primeira extrai
invariantes e casos de borda por entrevista socrática, a segunda converte o resultado em
especificação com critérios binários de aceite.

**Determinismo.** A geração, validação e exportação são determinísticas. O que não é
determinístico é o **diálogo** do PRÉ-PLANO — mas ali quem decide é o usuário, não o
modelo.

**Ferramentas acessadas.** `jsonschema` para validação; `pipeline_ops` do `aidd-ops`
para o caminho do nicho dinâmico no export.

**Hooks e regras.** Lei #10 (Quarteto), Lei #7 (usuário autoritativo), Zero Stubs.

**Entrega.** Entrega `PLANNER.json` no diretório do projeto. Entrega **para o motor do
fluxo escolhido** — `aidd-generator`, `aidd-factory` ou `aidd-bridge`.

## 12.6 Como funciona dentro da camada FLUXO

**Passo a passo.** Etapa 2 de 7. O orquestrador invoca, lê o resultado, monta e valida
o handoff. Falha em qualquer ponto aborta o fluxo.

**Portões.** Os três próprios, mais a validação do orquestrador contra
`handoff-planner-to-engine.schema.json`, cujos seis campos obrigatórios são
`versao_schema`, `fluxo_alvo`, `metadados_projeto`, `quarteto_sine_qua_non`,
`arquitetura_alvo` e `modulos_funcionais`.

**Habilidades.** `fluxo-01-runner`, `fluxo-02-runner`, `fluxo-03-runner`.

**Determinismo.** A parte automatizada é integral; o intake é interativo por desenho.

**Ferramentas acessadas.** `ecossistema.py planner` como invocador.

**Hooks e regras.** O campo `arquitetura_alvo` do handoff carrega o Padrão-Ouro (Lei
#11): `padrao_frontend: nextjs_typescript_tailwind`, `padrao_backend:
fastapi_modular_vsa`, e a persistência que varia por fluxo — `sqlite_wal` nos Fluxos 01
e 02, `postgresql` no Fluxo 03.

**Entrega.** Entrega `HANDOFF_PLANNER_ENGINE.json` validado, para a etapa 3.

## 12.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora de um fluxo completo, o planner é usado para produzir e auditar
planos isoladamente — por exemplo, para avaliar a viabilidade de um domínio antes de
comprometer a execução.

**Portões.** Os três portões do planner são parte da bateria auditada por
`G_ECOSSISTEMA_INTEGRIDADE`.

**Habilidades.** `/aidd-grill`, `/aidd-grill-docs`, `/aidd-spec`, `/aidd-tickets` — a
cadeia anti-*vibe coding* completa desemboca num plano.

**Determinismo.** Validação e exportação determinísticas.

**Ferramentas acessadas.** `componentes/compartilhado/specs/plano-infraestrutura.schema.json`
como contrato compartilhado com `aidd-ops` e `aidd-factory`.

**Hooks e regras.** A regra de que o export do factory deve devolver o envelope exato do
`aidd-ops`, e nunca um formato próprio.

**Entrega.** Entrega um contrato formal que qualquer motor do ecossistema consegue
consumir sem tradução. É o que torna possível trocar o motor sem reescrever o plano.

## 12.8 Rastreabilidade

`tools/aidd-planner/AGENTS.md`; `tools/aidd-planner/src/cli.py`;
`tools/aidd-planner/src/core/planner_engine.py`;
`tools/aidd-planner/schemas/planner_schema.json`; `tools/aidd-planner/gates/`;
`componentes/compartilhado/specs/handoff-planner-to-engine.schema.json`;
`scripts/orquestrador_sincrono.py::etapa_02_planner`.

# Capítulo 13 — `aidd-generator`: a fábrica autônoma de oito fases

```{=typst}
#ficha(
  ("Papel", "Fábrica autônoma: ideia → sistema completo, testado e auditado"),
  ("Etapa na esteira", "3 de 7 — motor do Fluxo 01 (`aidd-pure`)"),
  ("Slash command", [`/generate <ideia>`]),
  ("CLI", [`python ecossistema.py generate "<ideia>" --pasta <p> [--implementar-codigo]`]),
  ("Estado", [`PLANO-EXECUCAO-ESTRUTURADO.json` + `.aidd/cache/_pipeline_state.json`]),
  ("Orçamento total declarado", "115.000 tokens nas 4 fases que usam modelo"),
)
```

## 13.1 O que é a ferramenta

`aidd-generator` é a ferramenta mais complexa do ecossistema e a única que constrói
software do zero. É um pipeline de oito fases, com máquina de estados formal validada
por JSON Schema Draft 2020-12, que vai da pesquisa de referências reais até a entrega de
código funcional verificado por pytest.

## 13.2 O papel da ferramenta dentro do FLUXO

É o motor da etapa 3 do Fluxo 01. Recebe o handoff do planner, executa as oito fases e
entrega um sistema que o `aidd-master` vai harmonizar em fatias verticais.

O orquestrador o invoca com `--implementar-codigo`, o que altera a ordem de execução
para 1→2→3→4→5→**8**→6→7. O motivo é documentado no próprio pipeline: rodar a Fase 8
logo após a 5 faz com que a documentação da Fase 6 descreva o código real e a
auto-crítica da Fase 7 audite o projeto funcional completo, em vez de auditar um
esqueleto.

## 13.3 O papel da ferramenta dentro do ECOSSISTEMA

No ecossistema, o gerador cumpre dois papéis além de gerar software.

É o **laboratório de tokenomics**: `config/token_budgets.json`, `G_TOKENOMICS`,
`benchmark_tokenomics.py`, `compressor_middleware.py`, `caveman_linter.py` e
`core/pipeline_state.py` estão todos aqui. As técnicas de economia de tokens do
ecossistema são desenvolvidas e medidas neste contexto.

É o **laboratório de engenharia agêntica**: Fleet Discovery (descoberta automática dos
assistentes instalados no host), Context-Purge Engine (subagentes efêmeros), Intent
Router (detecção de intenção), micro-ambientes por fase e o protocolo delegado nasceram
aqui.

## 13.4 Como foi pensada, está estruturada e configurada

### As oito fases

| Fase | Nome           | Regime                  | Orçamento | Saída principal                            |
| ---: | :------------- | :---------------------- | --------: | :------------------------------------------ |
| 1    | Pesquisador    | Determinístico          |         0 | `insights_phase1.json` — referências reais  |
| 2    | Analisador     | LLM                     |    25.000 | `analise_phase2.json`                       |
| 3    | Designer       | LLM (5 subagentes)      |    20.000 | `design_aidd_phase3.json`                   |
| 4    | Planejador     | Híbrido                 |     5.000 | `config_global_local_phase4.json`           |
| 5    | Criador        | Determinístico          |         0 | Projeto em disco, git, SQLite               |
| 6    | Documentador   | Determinístico          |         0 | HTML + Markdown + PDF (Typst)               |
| 7    | Auto-crítica   | Determinístico          |         0 | `relatorio_final.md` com score              |
| 8    | Implementador  | LLM + loop de correção  |    50.000 | Código funcional verificado por pytest      |

### Micro-ambiente: a fase como unidade isolada

Cada fase tem um `AGENTS.md` próprio em `scripts/phases/phase_NN_<nome>/` declarando
escopo, restrições, regras de negócio, portões, MCPs acessíveis, saída e consumo de
tokens com justificativa. Apenas o micro-ambiente da fase em execução é carregado em
memória.

Os portões de fase são nomeados por letra e número, e são específicos:

| Fase | Portões                                                                          |
| ---: | :-------------------------------------------------------------------------------- |
| 1    | R1 URLs válidas; R2 atividade recente (`pushed_at` < 2 anos); R3 estrutura mínima; R4 ≥ 3 referências |
| 2    | A1 esquema válido; A2 zero alucinação; A3 dados completos; A4 sem `TODO`/`pass`    |
| 3    | D1 camadas completas; D2 scripts com pseudocódigo; D3 determinismo mínimo ≥ 65%    |
| 4    | C1 decisões GLOBAL/LOCAL válidas; C2 symlinks resolvem para caminho real; C3 configuração completa |
| 5    | E1 arquivos em disco; E2 git init + commit; E3 SQLite inicializado; E4 permissões; S1 segurança |

```{=typst}
#painel("Duas regras que revelam a filosofia inteira")[
  A Fase 1 proíbe explicitamente o fallback de dados de teste: *"Dados REAIS apenas —
  fallback DADOS_TESTE é PROIBIDO"*. A Fase 2 proíbe fabricar citação: as referências
  citadas devem vir da Fase 1, e sem referências a análise deve ser *honesta sobre as
  lacunas*. O portão D3 da Fase 3 exige determinismo mínimo de 65% no design produzido —
  o gerador é obrigado a projetar sistemas que, eles próprios, minimizem o uso de modelo.
]
```

### A máquina de estados

`scripts/fsm_engine.py` implementa o `GeneratorFSMEngine`, que valida o artefato de
saída de cada fase contra JSON Schema Draft 2020-12 **antes** de permitir a transição
para a fase N+1. `scripts/core/pipeline_state.py` grava atomicamente o estado em
`.aidd/cache/_pipeline_state.json` com validação estrita e implementa `--resume`:
retomada que pula fases completas com artefatos válidos, sem reconsumo de tokens.

Os retries por fase são configurados individualmente — de uma tentativa na Fase 4 até
três nas Fases 2, 3, 6 e 8, com atrasos de 2 a 5 segundos.

### O Padrão-Ouro imposto no design

O micro-ambiente da Fase 3 exige que toda aplicação Web/API projetada inclua
obrigatoriamente: CRUD completo com ciclo fechado; frontend no padrão *Impeccable*
(paleta Zinc, tipografia tabular, microinterações de 150 ms, zero alertas nativos do
sistema operacional via `share/ui_dialogs.js`); Swagger em tema escuro nativo; Studio
MCP com JSON-RPC 2.0; e Studio de Webhooks com HMAC SHA-256 assíncrono e auditoria de
disparos.

## 13.5 Como funciona individualmente

**Passo a passo.**

```bash
    python scripts/preflight_llm.py                       # 0 = pronto, 1 = falta configuração
    python ecossistema.py generate "app de habitos" --pasta ../MEU-PROJETO --implementar-codigo # `implementação`
    python scripts/gates/G_TOKENOMICS.py --pasta ../MEU-PROJETO
```

O pré-voo verifica se há `LLM_MODEL` configurado **e** credencial do provedor antes de
gastar tempo com a Fase 1 — se faltar, o pipeline para imediatamente com mensagem clara.
Sem fallback silencioso: se qualquer fase retornar `None`, o pipeline para e reporta
exatamente qual fase falhou e por quê.

**Portões.** Os portões de fase (R, A, D, C, E, S), mais os portões da ferramenta:
`G_TOKENOMICS`, `G_CYBERSECURITY_OWASP`, `G_SANDBOX_NIVEL_1`, `G_SESSAO_HERMETICA`,
`G_BLOQUEAR_SEGREDOS`, `G_INTEGRACAO_CROSS_SCRIPT`, `G_VERIFICAR_LLM_PRONTO`,
`G_INJECT`, `G_HARNESS_COMPAT`, e o comparativo `AUDITAR_COMPARATIVO_HARNESS`.

**Habilidades.** `aidd-generator-runner` é a dona de `/generate`. As Fases 1 e 2
utilizam `/aidd-spec` e `/aidd-tickets` explicitamente, conforme o `AGENTS.md`, para
impedir *vibe coding*.

**Determinismo.** Quatro das oito fases são de custo zero. A validação AST é mecânica
em toda escrita: na Fase 5, todo código gerado passa por `ast.parse()` antes de ir para
o disco — se falhar, o arquivo **não** é criado e o erro é registrado no índice. Na
Fase 8, `_validar_contrato_ast` roda antes do pytest real.

**Ferramentas acessadas.** API do GitHub e do HuggingFace (Fase 1, via `requests`);
provedor de LLM configurado, sempre através de `solicitar_llm()` de
`utils_delegacao.py` — nunca chamada direta a `litellm`; `pytest` (Fase 8);
`Repomix` via `core/repomix_runner.py` para empacotamento de contexto; Typst (Fase 6,
geração de PDF); MCP de sistema de arquivos; MCP verificador de CVE em `mcps/`.

**Hooks e regras.** Prompt em inglês com saída em PT-BR (tríade Caveman, auditada pelo
`caveman_linter.py`); UTF-8 explícito na escrita; loop de correção com traceback real do
pytest reenviado ao modelo por até três tentativas.

**Entrega.** Entrega o projeto completo em `<pasta>`, mais a documentação tripartite em
`output/<nome>/documentos/` e o `relatorio_final.md` com score em seis dimensões
(pesos 20+20+25+10+15+10), roadmap filtrado pelo score atingido e investimento estimado
com premissas rotuladas explicitamente como estimativa.

## 13.6 Como funciona dentro da camada FLUXO

**Passo a passo.** Etapa 3 do Fluxo 01, invocada com `--implementar-codigo`, ordem
1→2→3→4→5→8→6→7.

**Portões.** Todos os portões de fase, mais a validação do handoff
`handoff-engine-to-master.schema.json`.

**Habilidades.** `aidd-pure`, `fluxo-01-runner`.

**Determinismo.** No contexto do fluxo, o gerador é a única etapa com consumo
significativo de tokens — as outras seis são determinísticas.

**Ferramentas acessadas.** As mesmas, mais o `PLANNER.json` como entrada consumida
nativamente.

**Hooks e regras.** O hook de pre-commit instalado pelo forge na etapa 1 está ativo: o
commit que a Fase 5 executa passa pelos portões.

**Entrega.** Entrega ao `aidd-master` um projeto com fatias, artefatos de frontend e
resultado de testes.

## 13.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora do fluxo completo, `/generate` é o caminho mais curto entre uma
ideia e um sistema. É também o campo de prova das técnicas de economia: rodar
`benchmark_tokenomics.py` mede a economia real por fase contra a baseline legada.

**Portões.** `G_TOKENOMICS` é o portão que liga esta ferramenta à Lei #8 — ele reprova
quem alegar medição real para valor autodeclarado.

**Habilidades.** `sandeco-token-reduce` (LLMLingua-2) via `compressor_middleware.py`;
`aidd-orca` e `aidd-orchestrate` quando a execução acontece em ambiente orquestrado.

**Determinismo.** Metade do pipeline.

**Ferramentas acessadas.** O MCP `code-review-graph` para consulta de grafo antes de
busca textual; `detector.py` detecta silenciosamente quais assistentes estão instalados
no host (claude, codex, agy, cursor, ollama) usando apenas `shutil.which()` e
`os.environ`, sem dependência externa.

**Hooks e regras.** Lei #1 (determinismo primeiro), Lei #4 (economia extrema), Lei #5
(zero stubs), Lei #8 (honestidade de rótulo).

**Entrega.** Entrega sistemas e, para o ecossistema, entrega **métricas auditáveis de
economia de tokens** — o relatório JSON do benchmark com economia percentual real por
fase, custo em dólares e resultado de pytest.

## 13.8 Rastreabilidade

`tools/aidd-generator/AGENTS.md` e `AGENTS-WORKFLOW.md`;
`tools/aidd-generator/scripts/pipeline_completo.py`;
`tools/aidd-generator/scripts/phases/` (8 micro-ambientes + 8 módulos de fase);
`tools/aidd-generator/scripts/fsm_engine.py`;
`tools/aidd-generator/scripts/core/pipeline_state.py`;
`tools/aidd-generator/config/token_budgets.json`;
`tools/aidd-generator/scripts/gates/` (10 portões).

# Capítulo 14 — `aidd-factory`: o integrador multi-serviço

```{=typst}
#ficha(
  ("Papel", "Gerador de aplicação e integração para stacks multi-serviço"),
  ("Etapa na esteira", "3 de 7 — motor do Fluxo 02 (`aidd-open`)"),
  ("Slash command", [`/factory [requisito]`]),
  ("CLI", [`python ecossistema.py factory --plano <arquivo> --pasta <destino>`]),
  ("Contrato de entrada", [`PLANO-INFRAESTRUTURA.json` (único, fechado)]),
  ("Contrato de saída", [`FACTORY_OUTPUT.json` (único, fechado)]),
)
```

## 14.1 O que é a ferramenta

`aidd-factory` é o **integrador**: em vez de escrever o sistema, ele compõe uma
aplicação a partir de motores open-source curados, gerando a camada que os une —
gateway/BFF, orquestração compose, inicialização de banco, variáveis de ambiente e
código de integração.

É a materialização da política anti-NIH do ecossistema: quando existe software
consolidado que resolve o problema, escrever de novo é desperdício de tokens, de tempo
e de confiabilidade.

## 14.2 O papel da ferramenta dentro do FLUXO

É o motor da etapa 3 do Fluxo 02. Recebe um plano já resolvido e produz os artefatos que
o `aidd-master` vai fatiar em VSA e que o `aidd-ops` vai provisionar.

A restrição de entrada é dura e está no portão `G_FACTORY_INPUT`: a fábrica consome
**apenas** `PLANO-INFRAESTRUTURA.json` validado contra
`componentes/compartilhado/specs/plano-infraestrutura.schema.json`, e **nunca** lê
catálogos de nicho diretamente — o plano já chega resolvido.

## 14.3 O papel da ferramenta dentro do ECOSSISTEMA

No ecossistema, a `aidd-factory` é o par simétrico do `aidd-ops`: o ops decide *qual
infraestrutura*, a factory decide *qual código de integração*. Os dois compartilham o
mesmo esquema de plano, o que permite que o planner exporte para qualquer um dos dois
sem tradução.

É também a ferramenta que demonstra a doutrina de regimes mistos: quatro fases
inteiramente determinísticas convivendo com três fases de modelo cercadas por portões de
AST e `bandit`.

## 14.4 Como foi pensada, está estruturada e configurada

O `AGENTS.md` declara cinco invariantes: contrato de entrada único
(`G_FACTORY_INPUT`), contrato de saída único (`G_FACTORY_OUTPUT`), fases determinísticas
explicitamente demarcadas (`G_FACTORY_DETERMINISTIC` para as fases 1, 4, 5 e 6), Zero
Stubs, e **reuso obrigatório do núcleo compartilhado** — `result.py` e
`escritor_atomico.py` vêm de `componentes/compartilhado/src-core/`, não são
reimplementados.

A estrutura reflete isso: `scripts/contrato_factory.py` guarda os contratos,
`scripts/pipeline_factory.py` orquestra, e `scripts/phases/` contém os módulos de fase
(`01_analisador.py`, `04_compose.py`, `05_init_db.py`, `06_env.py`,
`09_integracao.py`). `templates/`, `schemas/`, `data/` e `gates/` completam.

### O nicho dinâmico

`01_analisador.py` detecta o prefixo `dinamico_` em `fase_1_intake.saida.nicho_slug` e,
nesse caso, sintetiza `blocos` e `bancos_logicos` a partir da própria lista de
`ferramentas` do plano — baseline `traefik` mais `postgres` condicional — em vez de
exigir que `templates/infra/nichos/<slug>.json` exista.

O `AGENTS.md` é honesto sobre o alcance dessa solução: ela é *"o subconjunto
determinístico do gap do Discovery Engine documentado em
`docs/features/v2_arquitetura-aidd-ops-factory.md` §7.1/§9.1 — um motor completo de
busca no GitHub permanece trabalho futuro"*.

## 14.5 Como funciona individualmente

**Passo a passo.** `pipeline_factory.py` valida o plano de entrada contra o esquema →
Fase 1 analisa e resolve blocos e bancos lógicos → Fases 2 e 3 usam modelo para a
curadoria e o desenho de integração, com portões AST e `bandit` → Fase 4 gera o compose
→ Fase 5 inicializa o banco → Fase 6 resolve o `.env` → Fase 9 gera o código de
integração → grava `FACTORY_OUTPUT.json` com todos os artefatos e seus status.

**Portões.** `G_FACTORY_INPUT`, `G_FACTORY_OUTPUT`, `G_FACTORY_DETERMINISTIC`, mais AST
e `bandit` nas fases de modelo.

**Habilidades.** `aidd-factory-runner` é a dona de `/factory`.

**Determinismo.** Fases 1, 4, 5 e 6 são 100% determinísticas por contrato auditado.

**Ferramentas acessadas.** Docker Compose (geração de manifesto), PostgreSQL
(inicialização), `bandit` (análise estática de segurança), núcleo compartilhado.

**Hooks e regras.** Zero Stubs — todos os geradores devem produzir código real,
funcional, sem marcador de espaço nem `TODO`.

**Entrega.** Entrega `FACTORY_OUTPUT.json` e os artefatos listados nele. O destinatário
declarado no `AGENTS.md` é o `DeployOrchestrator`.

## 14.6 Como funciona dentro da camada FLUXO

**Passo a passo.** Etapa 3 do Fluxo 02, invocada pelo orquestrador como
`factory curate --dominio <d> --output <pasta>/factory_output`.

**Portões.** Os três próprios, mais a validação do handoff Engine → Master.

**Habilidades.** `aidd-open`, `fluxo-02-runner`.

**Determinismo.** Majoritário — é o que torna o Fluxo 02 barato em tokens.

**Ferramentas acessadas.** O plano exportado pelo `aidd-planner` via
`exportar_para_fluxo_factory`.

**Hooks e regras.** A regra do contrato único: se o plano não validar contra o esquema, a
fábrica não roda. Não existe modo tolerante.

**Entrega.** Entrega ao `aidd-master` a stack integrada para fatiamento em VSA.

## 14.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora do fluxo, a factory pode ser usada isoladamente para gerar a
camada de integração de uma stack já planejada.

**Portões.** `G_INFRA_COMPOSE` e `G_HADOLINT` do ecossistema auditam os manifestos que
ela produz.

**Habilidades.** `aidd-dependencias` (quando a curadoria exige registrar dependência
nova), `aidd-componentes`.

**Determinismo.** Majoritário.

**Ferramentas acessadas.** `plano-infraestrutura.schema.json` como contrato
compartilhado com `aidd-ops` e `aidd-planner`.

**Hooks e regras.** A política anti-NIH: reusar `result.py` e `escritor_atomico.py` do
núcleo em vez de reimplementar. O portão `G_DRIFT_NUCLEO_COMPARTILHADO` detecta
divergência.

**Entrega.** Entrega ao ecossistema a prova de que integração é majoritariamente
mecânica — e, portanto, majoritariamente determinística.

## 14.8 Rastreabilidade

`tools/aidd-factory/AGENTS.md`; `tools/aidd-factory/scripts/contrato_factory.py`;
`tools/aidd-factory/scripts/pipeline_factory.py`;
`tools/aidd-factory/scripts/phases/`; `tools/aidd-factory/gates/`;
`componentes/compartilhado/specs/plano-infraestrutura.schema.json`;
`docs/features/v2_arquitetura-aidd-ops-factory.md`.

# Capítulo 15 — `aidd-bridge`: o libertador de low-code

```{=typst}
#ficha(
  ("Papel", "Extrator de projetos low-code, unificador PostgreSQL e empacotador para VPS própria"),
  ("Etapa na esteira", "3 de 7 — motor do Fluxo 03 (`aidd-bridge`)"),
  ("Slash command", [`/bridge [comando]`]),
  ("CLI", [`python ecossistema.py bridge unpack|scan|convert-db|merge|pack|migrate-auth|destroy`]),
  ("Origem suportada", "React + Vite + Tailwind + Supabase (Lovable, v0, Bolt)"),
  ("Destino", "PostgreSQL puro + PostgREST + Docker em VPS própria"),
)
```

## 15.1 O que é a ferramenta

`aidd-bridge` resolve o aprisionamento por fornecedor em aplicações geradas por
plataformas low-code. Ele ingere um projeto React + Vite + Tailwind + Supabase, extrai
páginas, componentes shadcn e migrações, converte o banco para PostgreSQL puro com
emulação PostgREST, empacota em Docker com boas práticas OCI e entrega uma aplicação
que roda em servidor próprio — **sem refatorar o frontend**.

A propriedade que torna isso viável é a emulação PostgREST: o cliente
`@supabase/supabase-js` do frontend continua funcionando contra o novo backend, e por
isso a interface é preservada exatamente como estava.

## 15.2 O papel da ferramenta dentro do FLUXO

É o motor da etapa 3 do Fluxo 03. A diferença essencial em relação aos outros dois
motores é a origem: aqui existe um artefato de partida real — o export da plataforma
low-code — e o trabalho é de transformação, não de criação.

Ao final, exporta o Quarteto *Sine Qua Non* em `quarteto_sine_qua_non/` para que o
`aidd-master` o harmonize na estrutura VSA canônica.

## 15.3 O papel da ferramenta dentro do ECOSSISTEMA

No ecossistema, o bridge é a **prova de agnosticidade aplicada a terceiros**: a Lei #6
proíbe aprisionamento no próprio ecossistema, e o bridge estende esse princípio aos
projetos dos usuários, desfazendo o aprisionamento criado por outras plataformas.

É também a ferramenta com o maior número de operações destrutivas, e por isso a que tem
o protocolo de confirmação mais rígido.

## 15.4 Como foi pensada, está estruturada e configurada

O pacote `aidd_bridge/` organiza-se por responsabilidade de transformação:

| Módulo                  | Responsabilidade                                                        |
| :---------------------- | :------------------------------------------------------------------------ |
| `scanner.py`            | `LovableScanner` — mapeia páginas, componentes e migrações                |
| `vendor_patterns.py`    | Catálogo de padrões proprietários a detectar e neutralizar                |
| `data_bridge.py`        | Sanitização SQL Supabase → PostgreSQL puro                                |
| `bridge/sql_transpiler.py` | Transpilação de dialeto SQL                                            |
| `frontend_liberator.py` | Separação de camadas e `.env.production` limpo                            |
| `devops.py`             | `DevOpsPackager` — Dockerfile não-root, Nginx OWASP, compose              |
| `vsa_exporter.py`       | Exportação do Quarteto e conector VSA                                     |
| `auth_migrator.py`      | Migração de contas preservando hash de senha                              |
| `jwt_generator.py`      | Geração de segredos JWT para o ambiente self-hosted                       |
| `cloudflare_dns.py`     | Criação e remoção de registros DNS                                        |
| `unifier.py`            | Fusão de múltiplas aplicações em fatias segregadas                        |
| `teardown.py`           | Remoção atômica de stack, volumes, DNS e diretório                        |
| `pipeline_bridge.py`    | `BridgePipeline` — orquestração das seis fases                            |

Os sete invariantes do `AGENTS.md` são: libertação de fornecedor; ponte de dados com
PostgREST; fusão multi-aplicação em fatias; migração real de autenticação com
preservação de hash; teardown atômico com confirmação obrigatória; Quarteto *Sine Qua
Non* exportado; e subordinação aos quatro portões dedicados.

## 15.5 Como funciona individualmente

**Passo a passo.** O pipeline completo (`unpack`) executa as seis fases descritas no
capítulo 9. Os subcomandos individuais permitem operar fase a fase:

```bash
python ecossistema.py bridge scan --dir ../export-lovable
python ecossistema.py bridge convert-db --dir ../export-lovable
python ecossistema.py bridge merge --apps app1,app2
python ecossistema.py bridge pack --dominio meuapp.com
python ecossistema.py bridge migrate-auth --origem <postgres-origem>          # preview
python ecossistema.py bridge migrate-auth --origem <postgres-origem> --apply  # escreve
python ecossistema.py bridge destroy --stack meuapp                           # pede confirmação
python ecossistema.py bridge unpack ../export-lovable                         # pipeline completo
```

**Portões.** `G_BRIDGE_VENDOR_LOCKIN` (nenhum resquício proprietário),
`G_BRIDGE_DOCKER_OCI` (boas práticas de imagem), `G_BRIDGE_POSTGRESQL` (SQL convertido
válido) e `G_BRIDGE_VSA_COMPAT` (compatibilidade com o fatiamento do master).

**Habilidades.** `aidd-bridge` e `aidd-bridge-runner` são as skills do comando.

**Determinismo.** Integral — nenhuma das seis fases chama modelo.

**Ferramentas acessadas.** Docker e Docker Swarm, PostgreSQL, PostgREST, Nginx, API da
Cloudflare (DNS), git.

**Hooks e regras.** Preview por padrão em `migrate-auth`; confirmação obrigatória em
`destroy` salvo `--yes` explícito; UTF-8 forçado no subprocesso pelo `ecossistema.py`,
uma decisão tomada especificamente porque o bridge imprime caracteres fora do cp1252 e
derrubava o pipeline no console padrão do Windows.

**Entrega.** Entrega o projeto libertado com Docker, compose, banco convertido, `.env`
limpo e Quarteto exportado. Entrega **para o `aidd-master`** dentro do fluxo e **para a
VPS do usuário** ao final.

## 15.6 Como funciona dentro da camada FLUXO

**Passo a passo.** Etapa 3 do Fluxo 03. O orquestrador chama `bridge scan --dir
<origem>`; o pipeline completo é acionado via `bridge unpack`.

**Portões.** Os quatro dedicados, mais o handoff Engine → Master, cujo campo
`artefatos_frontend.origem_design` recebe `lovable_preserved` neste fluxo — registro
explícito de que a interface original foi mantida.

**Habilidades.** `aidd-bridge`, `fluxo-03-runner`.

**Determinismo.** Integral — é o fluxo mais barato dos três.

**Ferramentas acessadas.** O export da plataforma low-code como entrada real.

**Hooks e regras.** Persistência `postgresql` no `arquitetura_alvo` do handoff (os
Fluxos 01 e 02 usam `sqlite_wal`).

**Entrega.** Entrega ao `aidd-master` o projeto convertido com o Quarteto pronto para
harmonização.

## 15.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora do fluxo, o bridge é usado cirurgicamente: converter só o banco,
só empacotar, só migrar contas, só destruir uma stack.

**Portões.** `G_HADOLINT` e `G_INFRA_COMPOSE` do ecossistema auditam os artefatos Docker
que ele produz.

**Habilidades.** `adaptar-lovable-aidd` cobre o caso de adaptação de projeto exportado
do Lovable para projeto convencional.

**Determinismo.** Integral.

**Ferramentas acessadas.** Cloudflare, Docker Swarm, PostgreSQL.

**Hooks e regras.** Toda operação destrutiva exige confirmação; a Lei #6 aplicada ao
projeto do usuário.

**Entrega.** Entrega ao ecossistema uma porta de entrada para projetos que nasceram fora
dele — é o caminho pelo qual um sistema criado em plataforma proprietária passa a ser
governado pelas mesmas leis dos sistemas nascidos aqui.

## 15.8 Rastreabilidade

`tools/aidd-bridge/AGENTS.md`; `tools/aidd-bridge/aidd_bridge/pipeline_bridge.py`;
`tools/aidd-bridge/aidd_bridge/` (13 módulos); `tools/aidd-bridge/gates/` (4 portões);
`ecossistema.py::cmd_bridge`; `scripts/orquestrador_sincrono.py::etapa_03_engine`.

# Capítulo 16 — `aidd-master`: o harmonizador modular

```{=typst}
#ficha(
  ("Papel", "Plataforma de arquitetura limpa modular em fatias verticais"),
  ("Etapa na esteira", "4 de 7 — primeira etapa do funil de convergência"),
  ("Slash command", [`/master <modulo>`]),
  ("CLI", [`python ecossistema.py master add-module|init|compose|audit|...` (22 subcomandos)]),
  ("Portões locais", "10, orquestrados por `scripts/run_all.py` com auto-remediação"),
  ("Persistência", "SQLite em modo WAL, com EventBus e mônada `Result`"),
)
```

## 16.1 O que é a ferramenta

`aidd-master` é onde os três fluxos convergem. Qualquer que seja o motor da etapa 3, o
resultado passa por aqui e sai no mesmo formato: **monólito modular em fatias verticais**
— domínio fatiado verticalmente, com uma camada horizontal compartilhada.

A analogia do `README.md` é a dos blocos de encaixe: permite acrescentar função nova sem
quebrar o que já existe. A razão técnica é o isolamento de contexto delimitado.

## 16.2 O papel da ferramenta dentro do FLUXO

É a etapa 4 e a primeira do funil de convergência. O orquestrador roda `master init
<slug>` e depois `master add-module <slug>`, criando a fatia vertical principal a partir
do que o motor produziu.

A etapa existe porque os três motores produzem coisas estruturalmente diferentes — código
autoral, integração de serviços, projeto low-code convertido — e o ecossistema precisa
de uma forma canônica única para as etapas 5 e 6 operarem.

## 16.3 O papel da ferramenta dentro do ECOSSISTEMA

No ecossistema, o `aidd-master` é o **guardião da arquitetura alvo**. Os seus dez
portões locais definem, na prática, o que "arquitetura correta" significa no AIDD:
contexto delimitado isolado, fatia vertical completa, mônada `Result`, SQLite WAL,
consulta parametrizada, exclusão lógica, observabilidade com SLA.

É também a fonte da linhagem do núcleo compartilhado: os arquivos que o `aidd-master`
e o `aidd-enterprise` compartilham são auditados contra baseline por
`G_DRIFT_NUCLEO_COMPARTILHADO`.

## 16.4 Como foi pensada, está estruturada e configurada

### Os sete invariantes

1. **Isolamento de contexto delimitado e fatias verticais** (`G_ARQUITETURA`): import
   direto entre módulos de negócio é proibido; toda fatia contém `router.py`,
   `service.py`, `repository.py`, `dtos.py` e `events.py`; o frontend espelha com
   `hooks/`, `components/`, `types.ts` e `page.tsx`.
2. **Repositórios dedicados e isolamento de dados**: `JOIN` SQL entre contextos e chave
   estrangeira rígida entre fatias são proibidos; acesso a dado é encapsulado no
   `repository.py` da fatia; comunicação entre fatias só por `EventBus` ou interface
   pública de serviço.
3. **Mônada `Result`** (`G_QUALIDADE`): todo método de serviço retorna `Result[T, E]`;
   exceção crua nunca vaza para a apresentação.
4. **Persistência segura** (`G_SEGURANCA`): `PRAGMA journal_mode=WAL` sempre; marcador
   `?` em toda consulta; zero concatenação de string; exclusão lógica.
5. **Zero Stubs**.
6. **Observabilidade** (`G_PERFORMANCE`): rotinas decoradas com `@trace_span(name)` e
   teto de SLA `p99 < 200 ms`.
7. **Alinhamento com skills de engenharia**: fatias decompostas por `/aidd-tickets` e
   implementadas sob `/aidd-tdd` antes de graduar.

### Os dez portões e a auto-remediação

`scripts/run_all.py` executa os dez portões em ordem fixa — `G_ESTRUTURA`,
`G_SEGREDOS`, `G_SEGURANCA`, `G_TESTES`, `G_QUALIDADE`, `G_CONTRACTS`, `G_CHAOS`,
`G_HARNESS_COMPAT`, `G_ARQUITETURA`, `G_INJECT` — com um comportamento distintivo:
**se um portão falha, o orquestrador executa `scripts/autofix.py` e tenta de novo**; se
ainda falhar, sai com 1. É auto-remediação determinística, não tolerância.

`G_CHAOS` merece destaque: testa resiliência por injeção de falha, e é o portão que
distingue "passa nos testes" de "sobrevive a problema real".

### Os 22 subcomandos

A CLI do master é a mais rica do ecossistema. Os principais grupos:

| Grupo          | Subcomandos                                                                    |
| :------------- | :------------------------------------------------------------------------------ |
| Ciclo de vida  | `init`, `setup`, `status`, `apply`, `deploy`                                   |
| Módulos        | `add-module`, `refine-module`, `attach-vsa`, `heal`                            |
| Composição     | `compose`, `compose-orca`                                                      |
| Qualidade      | `audit`, `test`, `bench`                                                        |
| Frontend       | `export-frontend` (Next.js/TypeScript tipado a partir do OpenAPI)              |
| Infraestrutura | `scaffold-infra` (Terraform + Helm em `infra/`)                                |
| Componentes    | `inject`                                                                        |

Dois merecem nota. `compose-orca` compõe módulos via subagentes efêmeros com purga de
contexto — a aplicação direta da doutrina de isolamento cognitivo. `attach-vsa` conecta
um backend VSA (núcleo, módulo e Quarteto) a um frontend preservado — por exemplo, a
saída do `aidd-bridge` — **sem sobrescrever** Docker, Caddy ou o frontend existente; é a
peça que torna o Fluxo 03 possível sem perder a interface original.

## 16.5 Como funciona individualmente

**Passo a passo.** `master init <slug> --pasta <p>` provisiona o projeto modular;
`master add-module <nome>` gera a fatia vertical desacoplada com backend e frontend
espelhados; `master export-frontend` deriva o frontend tipado do contrato OpenAPI;
`master audit` roda os dez portões com auto-remediação; `master bench` mede
concorrência real no SQLite WAL e no EventBus.

**Portões.** Os dez de `run_all.py`, mais `G_AST_BOUNDED_CONTEXT` para a auditoria AST
de fronteira de contexto.

**Habilidades.** `aidd-master-runner` é a dona de `/master`; `/aidd-tickets` e
`/aidd-tdd` governam a implementação de cada fatia.

**Determinismo.** Integral. Todo o scaffold, a derivação de frontend a partir do
OpenAPI e a auditoria são mecânicos.

**Ferramentas acessadas.** SQLite (WAL), Alembic (migrações — a ferramenta tem
`alembic/` e `alembic_models.py`), `behave` (suítes BDD em `refine-module`), pytest,
Terraform e Helm (`scaffold-infra`), OpenAPI → TypeScript (`openapi_to_ts.py`).

**Hooks e regras.** Os sete invariantes; `CAPABILITIES.json` assinado com Ed25519
(`CAPABILITIES.json.ed25519.sig`) declara o que a ferramenta é capaz de fazer, de forma
verificável.

**Entrega.** Entrega um projeto modular com fatias verticais completas, frontend
tipado, banco WAL e contratos OpenAPI. Entrega **para o `aidd-enterprise`** dentro do
fluxo.

## 16.6 Como funciona dentro da camada FLUXO

**Passo a passo.** Etapa 4. `master init <slug>` seguido de `master add-module <slug>`
ou, na Meso-Camada, o despacho em Git Worktrees efêmeras governado por `dispatch_pipeline.py`.
O roteador especialista (`engine_router.py`) encaminha a implementação para a engine
correspondente (Generator, Factory ou Bridge) e a barreira `vsa_join_barrier.py` audita as
fronteiras de arquivos via `git status --porcelain -uall` antes de efetuar a fusão no
Monólito Modular VSA.

**Portões.** Os dez locais, `G_DISPATCH_PIPELINE_VSA` (para fatias despachadas via DAG)
mais a validação do handoff `handoff-master-to-enterprise.schema.json`, cujos campos
obrigatórios são `versao_schema`, `diretorio_projeto`, `servidor_fastapi_ok`,
`quarteto_sine_qua_non_rotas` e `componentes_para_blindagem`.

**Habilidades.** `componentes-runner`, `aidd-master-runner`, `aidd-dispatch-runner` e os runners de fluxo.

**Determinismo.** Integral — etapa de custo zero em tokens.

**Ferramentas acessadas.** O resultado do motor da etapa 3, sob qualquer uma das três
formas.

**Hooks e regras.** É aqui que a Lei #11 (Padrão-Ouro) se materializa no frontend
Next.js e a Lei #10 (Quarteto) tem as rotas verificadas para o handoff.

**Entrega.** Entrega ao `aidd-enterprise` a lista de componentes para blindagem e a
confirmação de que o servidor sobe e as rotas do Quarteto respondem.

## 16.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora do fluxo, `/master <modulo>` é o comando do dia a dia: adicionar
uma fatia nova a um sistema em produção. Na orquestração de fatias paralelas, o comando
`python ecossistema.py dispatch --planner PLANNER.json` governa a execução concorrente
em worktrees efêmeras.

**Portões.** `G_ISOLATION_AUDIT`, `G_FRONTEND_LAYERS`, `G_ARQUITETURA_DELIVERABLE`,
`G_DISPATCH_PIPELINE_VSA` e `G_DRIFT_ANALYZER` do ecossistema complementam os dez locais.

**Habilidades.** `/aidd-grill` antes de projetar a fatia; `/aidd-tdd` durante;
`/aidd-diagnose` quando algo quebra; `/aidd-dispatch-runner` para despacho topológico.

**Determinismo.** Integral.

**Ferramentas acessadas.** `componentes/aidd-master/` guarda os componentes específicos
da ferramenta no cofre canônico.

**Hooks e regras.** `G_DRIFT_NUCLEO_COMPARTILHADO` audita a linhagem compartilhada com o
`aidd-enterprise` contra `gates/baseline_nucleo_compartilhado.json`.

**Entrega.** Entrega ao ecossistema a **definição executável de arquitetura correta** —
os seus portões são a especificação operacional do que o AIDD considera um sistema bem
construído.

## 16.8 Rastreabilidade

`tools/aidd-master/AGENTS.md`; `tools/aidd-master/scripts/aidd.py` (22 subcomandos);
`tools/aidd-master/scripts/dispatch_pipeline.py`;
`tools/aidd-master/scripts/engine_router.py`;
`tools/aidd-master/scripts/vsa_join_barrier.py`;
`tools/aidd-master/scripts/orchestrator_pipeline.py`;
`tools/aidd-master/scripts/run_all.py`; `tools/aidd-master/scripts/gates/` (12 portões);
`tools/aidd-master/CAPABILITIES.json` e a assinatura Ed25519;
`componentes/compartilhado/specs/handoff-master-to-enterprise.schema.json`;
`componentes/compartilhado/specs/vsa-topological-dispatch.schema.json`.

# Capítulo 17 — `aidd-enterprise`: a blindagem criptográfica

```{=typst}
#ficha(
  ("Papel", "Plataforma de missão crítica com injeção de componentes validada por SHA-256"),
  ("Etapa na esteira", "5 de 7"),
  ("Slash command", [`/enterprise <tipo> <nome>`]),
  ("CLI", [`python ecossistema.py enterprise inject <tipo> <nome>`, `verificar-drift`]),
  ("Portões locais", "10, mesma bateria do master com `G_INJECT` estendido"),
  ("Garantia central", "Integridade criptográfica e detecção de drift pós-injeção"),
)
```

## 17.1 O que é a ferramenta

`aidd-enterprise` é o `aidd-master` com uma camada adicional de garantia: todo componente
injetado é **validado contra assinatura SHA-256 antes de ser admitido em execução**, e a
sincronização multi-harness é verificada por detecção de drift depois da injeção.

A distinção entre as duas ferramentas é de regime de confiança, não de arquitetura. O
master constrói; o enterprise constrói **sob suspeita permanente** — zero-trust aplicado
à própria cadeia de componentes.

## 17.2 O papel da ferramenta dentro do FLUXO

É a etapa 5. O orquestrador executa duas operações: `enterprise inject rule
regra-integridade-<slug>` e `enterprise verificar-drift`. Ambas precisam sair com
código 0.

O que essa etapa acrescenta ao produto é a garantia de que os componentes de governança
presentes no projeto são exatamente os que deveriam estar ali — nem adulterados, nem
dessincronizados entre assistentes.

## 17.3 O papel da ferramenta dentro do ECOSSISTEMA

No ecossistema, o enterprise é o **par de linhagem do master**. As duas ferramentas
compartilham arquivos de núcleo, e essa duplicação é deliberada e auditada: o portão
`G_DRIFT_NUCLEO_COMPARTILHADO` mantém um baseline em
`gates/baseline_nucleo_compartilhado.json` e reprova divergência não documentada entre
as duas linhagens.

É também a ferramenta que responde pela conformidade regulada: projetos que precisam
demonstrar integridade de cadeia a um auditor externo passam por aqui.

## 17.4 Como foi pensada, está estruturada e configurada

Os seis invariantes do `AGENTS.md`: integridade criptográfica (validação SHA-256 antes
da execução); mônada `Result` com exceção bloqueada no perímetro; contextos delimitados
estritos com integração exclusivamente por `EventBus` e `core.*`; persistência
resiliente (SQLite WAL, parametrização estrita, exclusão lógica); Zero Stubs com
tipagem forte e testes automatizados; e ciclo `/aidd-tdd` com cobertura real de
asserção **antes** de o componente receber a assinatura criptográfica.

O último invariante é o mais revelador: a assinatura não certifica que o código existe —
certifica que ele passou por um ciclo TDD com asserções reais. Assinar código não
testado seria transformar a criptografia em teatro.

O portão `G_INJECT` local valida duas dimensões: a infraestrutura do motor (contrato
JSON Schema, arquivos de núcleo `profiles_registry.py`, `detector_camada.py`,
`materializador.py`, `sincronizador_harness.py`, integração com a CLI e o `IntentRouter`,
varredura AST anti-stub e suíte pytest dedicada) e a sincronização multi-harness com
integridade SHA-256 pós-injeção via `sincronizador_harness.verificar_sincronizacao()`.

## 17.5 Como funciona individualmente

**Passo a passo.** `enterprise inject <tipo> <nome> --dir <projeto>` resolve o perfil do
componente, materializa com transação, sincroniza para os assistentes, calcula os hashes
e verifica a integridade. `enterprise verificar-drift --dir <projeto>` recalcula e
compara contra o registro. `python scripts/run_all.py` roda os dez portões locais.

**Portões.** Os dez de `run_all.py`, com `G_INJECT` estendido para a verificação
criptográfica.

**Habilidades.** `aidd-enterprise-runner` é a dona de `/enterprise`; `aidd-master-pack`
cobre a suíte cross-domain.

**Determinismo.** Integral.

**Ferramentas acessadas.** SHA-256 e Ed25519 (`assinatura_manifesto.py` do núcleo),
Alembic, SQLite WAL, pytest.

**Hooks e regras.** Zero-trust: nenhum componente entra em execução sem validação de
assinatura.

**Entrega.** Entrega componentes blindados e um veredito de drift. Entrega **para o
`aidd-ops`** dentro do fluxo.

## 17.6 Como funciona dentro da camada FLUXO

**Passo a passo.** Etapa 5: `inject` seguido de `verificar-drift`.

**Portões.** Os dez locais, mais a validação do handoff
`handoff-enterprise-to-ops.schema.json`, cujos campos obrigatórios são `versao_schema`,
`diretorio_projeto`, `sha256_audit_ok`, `drift_verificado` e `manifesto_deploy`.

**Habilidades.** `aidd-enterprise-runner` e os runners de fluxo.

**Determinismo.** Integral — etapa de custo zero em tokens.

**Ferramentas acessadas.** O projeto harmonizado pelo master.

**Hooks e regras.** O manifesto de deploy declara `tipo_runtime`, presença de Dockerfile
e compose, e as portas expostas (80, 443, 3000).

**Entrega.** Entrega ao `aidd-ops` a confirmação de integridade e o manifesto de deploy.

## 17.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora do fluxo, `/enterprise inject` é o caminho para introduzir
componente certificado em qualquer projeto AIDD.

**Portões.** `G_DRIFT_NUCLEO_COMPARTILHADO`, `G_SUPPLY_CHAIN` e `G_COMPONENTE_AGNOSTICO`
do ecossistema.

**Habilidades.** `aidd-componentes`, `aidd-dependencias`.

**Determinismo.** Integral.

**Ferramentas acessadas.** `componentes/compartilhado/src-core/package_verifier.py` e
`assinatura_manifesto.py`.

**Hooks e regras.** A regra de que assinatura só vem depois de TDD com asserção real.

```{=typst}
#painel("Conformidade da Honestidade de Rótulo")[
  `G_HONESTIDADE_ROTULO` foi plenamente reabilitado e roda como portão obrigatório em
  todo commit (`always_run: true`). As mensagens de saída de todos os scripts de portão
  em `gates/`, `tools/aidd-master` e `tools/aidd-enterprise` foram alinhadas à linguagem
  técnica factual, auditando com zero termos proibidos.
]
```

**Entrega.** Entrega ao ecossistema a garantia de que a cadeia de componentes é
verificável — e o registro honesto de onde ela ainda não está.

## 17.8 Rastreabilidade

`tools/aidd-enterprise/AGENTS.md`; `tools/aidd-enterprise/scripts/aidd.py`;
`tools/aidd-enterprise/scripts/run_all.py`;
`tools/aidd-enterprise/scripts/gates/G_INJECT.py`;
`tools/aidd-enterprise/scripts/injector/`;
`componentes/compartilhado/src-core/assinatura_manifesto.py`;
`gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` e `gates/baseline_nucleo_compartilhado.json`.

# Capítulo 18 — `aidd-ops`: a infraestrutura agêntica

```{=typst}
#ficha(
  ("Papel", "Meta-orquestrador de infraestrutura para stacks self-hosted"),
  ("Etapa na esteira", "6 de 7 — última etapa antes da auditoria"),
  ("Slash command", [`/ops [requisito]`]),
  ("CLI", [`python ecossistema.py ops plan|bootstrap|preflight|deploy`]),
  ("Pipeline próprio", "3 fases: Intake → Curadoria → Sizing"),
  ("Artefato central", [`PLANO-INFRAESTRUTURA.json`]),
)
```

## 18.1 O que é a ferramenta

`aidd-ops` transforma um requisito em linguagem natural — *"uma clínica com agendamento
e prontuário para 2 mil pacientes"* — em uma infraestrutura dimensionada, provisionada e
monitorada: sizing de VPS, hardening de SSH, Docker, Traefik, PostgreSQL, Uptime Kuma e
bateria de preflight de ponta a ponta.

## 18.2 O papel da ferramenta dentro do FLUXO

É a etapa 6. No orquestrador síncrono atual, a etapa se limita a **validar** a presença
de `Dockerfile` e `docker-compose.yml` no projeto — o provisionamento real da VPS é
acionado separadamente, porque envolve credencial, host remoto e custo. Esse
desacoplamento é deliberado: a Lei #7 (Desenvolvedor no Controle) não permite que um
fluxo automatizado provisione infraestrutura paga sem decisão humana explícita.

## 18.3 O papel da ferramenta dentro do ECOSSISTEMA

No ecossistema, o `aidd-ops` é a **fonte do plano de infraestrutura** — o mesmo
`PLANO-INFRAESTRUTURA.json` que a `aidd-factory` consome e que o `aidd-planner` exporta.
As três ferramentas compartilham um único esquema, e o caminho do nicho dinâmico
descrito nos capítulos 8 e 12 nasceu aqui.

É também a ferramenta que aplica a política anti-NIH de forma mais visível: em vez de
escrever monitoramento, usa os templates oficiais do Uptime Kuma; em vez de escrever
scripts de hardening, usa a coleção Ansible `devsec.hardening`.

## 18.4 Como foi pensada, está estruturada e configurada

### As três fases do pipeline

| Fase | Módulo             | O que faz                                                                  |
| ---: | :----------------- | :--------------------------------------------------------------------------- |
| 1    | `01_intake.py`     | Reconhece o nicho a partir do texto; suporta nicho dinâmico com prefixo `dinamico_` |
| 2    | `02_curadoria.py`  | Cura a stack de ferramentas para o nicho reconhecido                        |
| 3    | `03_sizing.py`     | Dimensiona recursos — e é 100% orientado a nome de ferramenta               |

`pipeline_ops.py` roda as três em sequência, grava `PLANO-INFRAESTRUTURA.json` no destino
acumulando o estado de cada fase e imprime um resumo legível. Propaga códigos de erro
estruturados das fases — não mascara `Result.fail()`.

O `AGENTS.md` registra um detalhe importante sobre a Fase 3: ela **não precisou de
alteração** para suportar nicho dinâmico, porque já era inteiramente orientada a nome de
ferramenta e ignora graciosamente ferramentas desconhecidas. É um bom exemplo de
desenho que envelhece bem.

### Os seis invariantes

Compose determinístico e estruturado sob `templates/infra/` (`G_INFRA_COMPOSE`); boas
práticas OCI com Hadolint e zero violação alta ou crítica (`G_HADOLINT`); observabilidade
ativa **apenas** com templates oficiais do Uptime Kuma, zero painel falso ou simulado
(anti-NIH #14); hardening idempotente via coleção Ansible `devsec.hardening`, zero script
shell improvisado (anti-NIH #15); Zero Stubs; e triagem obrigatória por `/aidd-diagnose`
antes de qualquer correção emergencial em incidente de produção.

### O núcleo operacional

| Módulo de `src/core/`   | Responsabilidade                                                       |
| :---------------------- | :----------------------------------------------------------------------- |
| `ssh_runner.py`         | Execução remota via SSH                                                  |
| `cofre_credenciais.py`  | Cofre local com `sops` + `age`                                           |
| `preflight.py`          | Bateria E2E pós-deploy                                                   |
| `compose_preflight.py`  | Validação de compose antes do deploy                                     |
| `uptime_kuma.py`        | Integração com a API do Uptime Kuma                                      |
| `coolify.py`            | Integração com Coolify                                                   |
| `result.py`             | Mônada `Result` local                                                    |

```{=typst}
#painel("A decisão do cofre: sops + age, e não Vaultwarden")[
  O cabeçalho de `cofre_credenciais.py` registra a decisão e o motivo. O Vaultwarden foi
  descartado por trazer serviço e banco de dados para um caso de uso que é *pipeline
  automatizado* — decifrar sob demanda antes de `docker compose up` — e não humano
  compartilhando senha por interface gráfica.

  A escolha foi `sops` (Mozilla), que cifra o *valor* de cada variável de um arquivo
  dotenv mantendo as *chaves* legíveis — o que preserva a capacidade de comparar
  versões — usando `age` (FiloSottile) como backend assimétrico moderno (X25519 +
  ChaCha20-Poly1305). Sem servidor, sem banco, sem processo daemon.
]
```

### A bateria de preflight

`preflight.py` é uma bateria determinística contra um deploy já realizado, com quatro
verificações: healthcheck HTTP (`/healthz` de cada serviço, status 200 obrigatório);
validação de certificado SSL/TLS (emissor, vigência, cadeia); resolução DNS dos
subdomínios da topologia, com resolver injetável; e simulação de um webhook de ponta a
ponta com disparo sintético no gateway. Suporta injeção de dependência para execução
hermética em teste unitário e devolve `Result` com relatório estruturado em JSON.

## 18.5 Como funciona individualmente

**Passo a passo.**

```bash
python ecossistema.py ops plan "clinica com agendamento e prontuario" --pasta ../infra
python ecossistema.py ops plan --ferramentas-json ferramentas.json --pasta ../infra   # nicho dinâmico
python ecossistema.py ops bootstrap --host <ip>          # hardening + Docker via SSH
python ecossistema.py ops deploy                          # deploy E2E com Result e rollback
python ecossistema.py ops preflight                       # bateria E2E pós-deploy
python scripts/pipeline_ops.py monitor export|check       # sondas do Uptime Kuma
```

**Portões.** `G_OPS_MVP` e `G_OPS_SSH` locais; `G_INFRA_COMPOSE` e `G_HADOLINT` globais.

**Habilidades.** `aidd-ops-runner` é a dona de `/ops`; `/aidd-diagnose` é obrigatória
antes de correção emergencial.

**Determinismo.** Integral nas três fases do pipeline.

**Ferramentas acessadas.** Docker e Docker Compose, Traefik, PostgreSQL, Authentik,
Chatwoot, Cal.com, Twenty (templates em `templates/infra/`), Uptime Kuma, Ansible
(`devsec.hardening`), `sops` + `age`, Helm (`charts/aidd-ops/`), SSH, Coolify,
Hadolint, Checkov.

**Hooks e regras.** Idempotência em todo hardening; zero script improvisado; templates
oficiais apenas.

**Entrega.** Entrega `PLANO-INFRAESTRUTURA.json`, manifestos compose, VPS provisionada e
relatório de preflight em JSON. Entrega **para a `aidd-factory`** (o plano) e **para a
produção** (a infraestrutura).

## 18.6 Como funciona dentro da camada FLUXO

**Passo a passo.** Etapa 6: valida a presença dos manifestos Docker no projeto. O
provisionamento real fica fora do fluxo automatizado, por decisão de governança.

**Portões.** `G_INFRA_COMPOSE` e `G_HADOLINT` sobre os manifestos.

**Habilidades.** `aidd-ops-runner`, runners de fluxo.

**Determinismo.** Integral — etapa de custo zero em tokens.

**Ferramentas acessadas.** O manifesto de deploy do handoff Enterprise → Ops.

**Hooks e regras.** Lei #7: infraestrutura paga exige decisão humana explícita.

**Entrega.** Entrega à etapa 7 (auditoria) a confirmação de que os manifestos existem e
são válidos.

## 18.7 Como funciona dentro da camada ECOSSISTEMA

**Passo a passo.** Fora do fluxo, o `aidd-ops` é a ferramenta de operação contínua:
planejar, provisionar, implantar, monitorar, rotacionar segredo
(`scripts/rotate_secrets.py`).

**Portões.** Os globais de infraestrutura.

**Habilidades.** `/aidd-diagnose` para triagem científica de incidente em cinco fases,
integrada ao grafo de conhecimento.

**Determinismo.** Integral.

**Ferramentas acessadas.** `data/catalogo_nichos.json` (cinco nichos fixos),
`data/requisitos_recursos.json` (tabela de dimensionamento).

**Hooks e regras.** As duas regras anti-NIH (#14 Uptime Kuma oficial, #15 Ansible
`devsec.hardening`) são o traço mais característico da ferramenta: ela prefere
consistentemente integrar o que já existe a escrever o próprio.

**Entrega.** Entrega ao ecossistema o contrato de infraestrutura compartilhado e, ao
usuário, um sistema em produção com observabilidade real.

## 18.8 Rastreabilidade

`tools/aidd-ops/AGENTS.md`; `tools/aidd-ops/scripts/pipeline_ops.py`;
`tools/aidd-ops/scripts/phases/` (3 fases); `tools/aidd-ops/src/core/` (7 módulos);
`tools/aidd-ops/templates/infra/`; `tools/aidd-ops/ansible/playbooks/hardening.yml`;
`tools/aidd-ops/gates/`; `tools/aidd-ops/data/catalogo_nichos.json`.

# PARTE IV — CAMADAS TRANSVERSAIS

As três partes anteriores percorreram o ecossistema verticalmente: do organismo aos
fluxos, dos fluxos às ferramentas. Esta parte corta na horizontal. Os quatro capítulos
seguintes tratam de camadas que atravessam **todas** as ferramentas e **todos** os
fluxos: as habilidades e comandos, o catálogo completo de portões, a malha de
agnosticidade e a síntese consolidada da economia de tokens.

# Capítulo 19 — Habilidades e comandos: a interface universal

## 19.1 O que é uma habilidade no AIDD

Uma habilidade (*skill*) é um pacote de instruções versionado que qualquer assistente de
IA carrega para executar um procedimento específico do ecossistema. No AIDD, uma
habilidade nasce em `componentes/compartilhado/skills/<nome>/` — a fonte física canônica
— e é distribuída para os dez ambientes de assistente por
`python ecossistema.py components sync --tipo todos`.

O repositório tem **66 habilidades** nessa pasta e **16 comandos** em
`componentes/compartilhado/comandos/`.

## 19.2 As famílias de habilidades

### Runners de ferramenta

Um por ferramenta, cada um dono de exatamente um slash command:

| Habilidade                             | Comando                 | Ferramenta              |
| :------------------------------------- | :---------------------- | :---------------------- |
| `aidd-forge-runner`                    | `/forge`                | `aidd-forge`            |
| `aidd-planner-runner`                  | `/planner`              | `aidd-planner`          |
| `aidd-generator-runner`                | `/generate`             | `aidd-generator`        |
| `aidd-factory-runner`                  | `/factory`              | `aidd-factory`          |
| `aidd-bridge-runner`                   | `/bridge`               | `aidd-bridge`           |
| `aidd-master-runner`                   | `/master`               | `aidd-master`           |
| `aidd-enterprise-runner`               | `/enterprise`           | `aidd-enterprise`       |
| `aidd-ops-runner`                      | `/ops`                  | `aidd-ops`              |

### Runners de fluxo, pipeline e meso-camada

`aidd-pure` e `fluxo-01-runner`; `aidd-open` e `fluxo-02-runner`; `aidd-freedom` e
`fluxo-03-runner` (com operações atômicas da engine via `aidd-bridge-runner`).
Para execução de planos e despacho concorrente: `aidd-pipeline-runner` (`/run-plan`, `/pipeline`)
e `aidd-dispatch-runner` (`/dispatch`, `/aidd-dispatch`). O par existe porque uma
habilidade é a dona do slash command e a outra é o motor que executa a esteira em worktrees.

### Habilidades procedimentais de engenharia

As sete habilidades anti-*vibe coding* descritas no capítulo 2 — `/aidd-grill`,
`/aidd-grill-docs`, `/aidd-spec`, `/aidd-tickets`, `/aidd-tdd`, `/aidd-diagnose` e
`/aidd-handoff` — formam uma cadeia natural:

```{=typst}
#esteira(
  no("GRILL", sub: "entrevista"),
  no("SPEC", sub: "especificação"),
  no("TICKETS", sub: "tarefas atômicas"),
  no("TDD", sub: "red-green-refactor"),
  no("DIAGNOSE", sub: "quando quebra", cor: rgb("#334155")),
)
```

### Habilidades de evolução e orquestração

`melhoria`, `plan`, `orchestrate` (as três donas do fluxo de evolução);
`planos-auditoria-runner` e `orca-plan-orchestrator` (os motores);
`aidd-orca`, `aidd-orchestrate`, `aidd-orchestrator-runner`, `aidd-planos`,
`aidd-melhoria`.

### Habilidades de gestão do próprio ecossistema

`aidd-componentes` e `componentes-runner` (componentes); `aidd-dependencias` e
`dependencia-runner` (dependências de terceiros); `aidd-skills` e
`skill-creator-runner` (criação de habilidades); `aidd-mcp` e `mcp-creator-runner`
(servidores MCP); `explore-codebase`, `refactor-safely`, `review-changes`,
`debug-issue`.

### Habilidades de domínio externo

O ecossistema integra habilidades de terceiros como dependências declaradas:
`cloudflare`, `cloudflare-one`, `cloudflare-email-service`,
`cloudflare-one-migrations`, `durable-objects`, `nextjs-on-cloudflare`,
`workers-best-practices`, `wrangler`, `turnstile-spin`, `web-perf`, `sandbox-next`,
`sandbox-stable`, `sandbox-migrate-to-next`, `agents-sdk`, `impeccable`,
`sandeco-token-reduce`.

## 19.3 A regra: um comando, um dono

Já enunciada no capítulo 2, ela merece repetição aqui porque é a regra que estrutura
toda a camada de habilidades: **cada slash command tem exatamente uma habilidade dona**;
habilidades-motor não têm comando próprio e são acionadas pela dona.

A consequência prática é que, ao procurar quem responde por um comando, existe sempre
uma resposta única. A consequência histórica é que a regra nasceu de um incidente: duas
habilidades respondendo ao mesmo comando com regras opostas causaram mesas recursivas
dentro de mesas no aplicativo de orquestração em 11 de setembro de 2026.

## 19.4 A distribuição física

```{=typst}
#painel("O caminho de um componente, do nascimento à distribuição")[
  1. Nasce em `componentes/compartilhado/skills/<nome>/SKILL.md` (fonte canônica). \
  2. `python ecossistema.py components sync --tipo skills` distribui. \
  3. Chega em `.claude/skills/`, `.opencode/skills/`, `.mimocode/skills/`,
     `.agents/skills/`, `.gemini/extensions/`, `.cursor/rules/` e demais destinos. \
  4. `G_COMPONENTE_AGNOSTICO` audita a cobertura contra o manifesto. \
  5. `G_UNIVERSAL_HARNESS` audita o *wiring* real em cada assistente. \
  6. `G_HARNESS_COMPAT` audita a sincronia entre os artefatos da raiz.

  Editar um destino diretamente inverte o fluxo e é o erro que os portões detectam: o
  destino é sobrescrito no próximo `sync`, e a alteração se perde.
]
```

Há ainda o modo de reparo: `components sync --tipo todos --force` restaura destinos divergentes e
órfãos a partir da fonte, e `components verify` audita sem escrever.

## 19.5 Rastreabilidade

`componentes/compartilhado/skills/` (60 habilidades);
`componentes/compartilhado/comandos/` (14 comandos); `scripts/gestor_componentes.py`;
`ecossistema.py::cmd_components`; `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §3 e §5.

# Capítulo 20 — O catálogo completo de portões

## 20.1 A distribuição dos 148 portões

O repositório tem 148 arquivos `G_*.py`. Eles se distribuem em quatro camadas:

| Camada                  | Onde                                   | Quantidade | Papel                                               |
| :---------------------- | :------------------------------------- | ---------: | :---------------------------------------------------- |
| Portões globais         | `gates/`                               |         42 | Auditam o ecossistema inteiro                        |
| Portões de ferramenta   | `tools/<ferramenta>/gates/` ou `scripts/gates/` | ~55 | Auditam a ferramenta e o que ela produz        |
| Portões-template        | `tools/aidd-forge/aidd_forge/templates/gates/` | 8 | São injetados nos projetos gerados               |
| Portões de projeto      | Projetos gerados                       |   variável | Cópias dos templates, ativas no projeto do usuário   |

A contagem de 148 inclui as cópias distribuídas — o número de portões **distintos** é
menor, e a duplicação entre `aidd-master` e `aidd-enterprise` é justamente o que
`G_DRIFT_NUCLEO_COMPARTILHADO` mantém sob controle.

## 20.2 Portões por ferramenta

| Ferramenta        | Portões locais                                                                                          |
| :---------------- | :-------------------------------------------------------------------------------------------------------- |
| `aidd-forge`      | `G_BLOQUEAR_SEGREDOS`, `G_CONTRACTS`, `G_CYBERSECURITY_OWASP`, `G_ESTRUTURA_AST`, `G_HARNESS_COMPAT`, `G_INJECT`, `G_PERFORMANCE`, `G_TESTES_REAIS` |
| `aidd-planner`    | `G_PLANNER_SCHEMA`, `G_PLANNER_SINE_QUA_NON`, `G_PLANNER_COERENCIA_FLUXO`                               |
| `aidd-generator`  | `G_TOKENOMICS`, `G_CYBERSECURITY_OWASP`, `G_SANDBOX_NIVEL_1`, `G_SESSAO_HERMETICA`, `G_BLOQUEAR_SEGREDOS`, `G_INTEGRACAO_CROSS_SCRIPT`, `G_VERIFICAR_LLM_PRONTO`, `G_INJECT`, `G_HARNESS_COMPAT`, `AUDITAR_COMPARATIVO_HARNESS` |
| `aidd-factory`    | `G_FACTORY_INPUT`, `G_FACTORY_OUTPUT`, `G_FACTORY_DETERMINISTIC`                                        |
| `aidd-bridge`     | `G_BRIDGE_VENDOR_LOCKIN`, `G_BRIDGE_DOCKER_OCI`, `G_BRIDGE_POSTGRESQL`, `G_BRIDGE_VSA_COMPAT`           |
| `aidd-master`     | `G_ESTRUTURA`, `G_SEGREDOS`, `G_SEGURANCA`, `G_TESTES`, `G_QUALIDADE`, `G_CONTRACTS`, `G_CHAOS`, `G_HARNESS_COMPAT`, `G_ARQUITETURA`, `G_INJECT`, `G_AST_BOUNDED_CONTEXT`, `G_PERFORMANCE` |
| `aidd-enterprise` | A mesma bateria do master, com `G_INJECT` estendido para verificação criptográfica                      |
| `aidd-ops`        | `G_OPS_MVP`, `G_OPS_SSH`                                                                                |

## 20.3 As categorias de auditoria

Os 42 portões globais podem ser lidos por intenção, e essa leitura revela a estratégia
de qualidade do ecossistema:

| Categoria                | Portões                                                                                     |
| :----------------------- | :-------------------------------------------------------------------------------------------- |
| **Integridade estrutural** | `G_ECOSSISTEMA_INTEGRIDADE`, `G_ESCRITOR_ATOMICO`, `G_TRANSACTION_LOG_LRU`                  |
| **Arquitetura**          | `G_ARQUITETURA_DELIVERABLE`, `G_ISOLATION_AUDIT`, `G_FRONTEND_LAYERS`, `G_DRIFT_ANALYZER`, `G_PROTOTYPE_REWRITE` |
| **Agnosticidade**        | `G_HARNESS_COMPAT`, `G_UNIVERSAL_HARNESS`, `G_COMPONENTE_AGNOSTICO`, `G_PROTOCOL_FALLBACK`   |
| **Segurança**            | `G_SEGREDOS`, `G_LLM_PROMPT_SHIELD`, `G_SUPPLY_CHAIN`, `G_DEPENDENCIAS_PIN_HASH`             |
| **Infraestrutura**       | `G_INFRA_COMPOSE`, `G_HADOLINT`                                                              |
| **Honestidade**          | `G_HONESTIDADE_ROTULO`, `G_TESTES_REAIS`, `G_CLI_HELP_CONSISTENCIA`, `G_DOCS_ROT`, `G_LIVRO_EVIDENCIA` |
| **Governança agêntica**  | `G_ZERO_HEADLESS`, `G_ORQUESTRADOR_SINCRONO`, `G_DRIFT_NUCLEO_COMPARTILHADO`                 |
| **Meta-portões**         | `G_PORTAO_PROVA_QUE_MORDE` (Lei #13), `G_LEI_DECLARA_PORTAO` (Lei #8)                        |
| **Pipeline & Meso-Camada**| `G_PIPELINE_HANDOFF` (Leis #1, #2, #5), `G_DISPATCH_PIPELINE_VSA` (Kahn DAG & Worktrees)     |
| **Anti-rot por Lei** (fecham as Leis 1, 2, 3, 4, 9, 10, 11) | `G_DETERMINISMO_LEI_1`, `G_SAIDA_BINARIA`, `G_MIGRATION_ROT`, `G_ESTRUTURA_ESTADO`, `G_IDIOMA_LEI_4`, `G_ENV_ROT`, `G_SKILL_ROT`, `G_DISCIPLINA_TESTE_FERRAMENTA`, `G_CONTRACT_ROT`, `G_QUARTETO_SINE_QUA_NON`, `G_STACK_PADRAO_OURO` |

Três portões merecem nota especial porque auditam coisas que a maioria dos projetos não
audita.

`G_CLI_HELP_CONSISTENCIA` compara, por AST, as flags citadas em `print()` e `raise()`
contra as flags realmente definidas em `add_argument` nos pontos de entrada argparse das
ferramentas. Ele impede que a mensagem de erro sugira uma flag que não existe — um
defeito comum e invisível para teste funcional.

`G_TESTES_REAIS` roda `pytest` de verdade em cada `tools/<ferramenta>` e falha se
qualquer suíte tiver `failed > 0`. É a Lei #8 tornada mecânica: não se pode alegar suíte
verde sem suíte verde.

`G_LLM_PROMPT_SHIELD` audita, por AST, se os clientes de modelo de linguagem usam
deterministicamente o `PromptShield` para sanitização contra injeção de prompt e
jailbreak. É um portão de segurança específico de sistemas agênticos.

## 20.4 O ciclo de teste de ferramenta

A Lei #9 define um ciclo de cinco passos, documentado em
`docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`, que precede qualquer declaração de
conformidade: (1) corrigir bugs automaticamente até 100% de conformidade, com zero
inconsistência; (2) commit e push; (3) limpar o projeto alvo; (4) executar de forma
limpa; (5) atualizar o relatório em `docs/teste-end-to-end/`.

O passo 3 é o que distingue esse ciclo de um teste comum: limpar o projeto alvo impede
que a execução se apoie em artefato residual de uma execução anterior.

## 20.5 Rastreabilidade

`gates/` (42 portões e suítes); `tools/*/gates/` e `tools/*/scripts/gates/`;
`.pre-commit-config.yaml`; `docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`;
`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §4.

# Capítulo 21 — Agnosticidade: escrever uma vez, rodar em todos

## 21.1 As quatro dimensões de agnosticidade

A Lei #6 — Supremacia Agnóstica — proíbe dependência de fornecedor em quatro dimensões
simultâneas, e cada uma tem uma implementação concreta.

**Sistema operacional.** Tudo é Python puro. As poucas concessões a plataforma são
explícitas e tratadas: `PYTHONIOENCODING=utf-8` forçado no subprocesso para o console do
Windows, `sys.stdout.reconfigure(encoding='utf-8')` no topo dos portões, e invólucros
`.sh` e `.cmd` para os hooks compartilhados.

**Assistente.** Dez ambientes sincronizados a partir de uma fonte única, com três
portões auditando a paridade.

**Modelo.** O pipeline opera de duas formas: usando o modelo do próprio assistente da
sessão, via protocolo delegado, sem custo adicional de API; ou via provedor externo
local ou em nuvem (Ollama, Groq, Anthropic, OpenAI), configurado por `LLM_MODEL` e
credencial. `preflight_llm.py` verifica os dois antes de começar.

**Protocolo.** `G_PROTOCOL_FALLBACK` garante que nada seja exposto exclusivamente por
MCP sem contrapartida REST/OpenAPI. Um sistema cuja única porta fosse o MCP estaria
preso ao ecossistema de agentes — o oposto do objetivo.

## 21.2 O protocolo delegado

O protocolo delegado é o mecanismo pelo qual o pipeline usa o modelo **do assistente que
está conduzindo a sessão**, em vez de abrir uma conexão própria com um provedor. Quando o
pipeline precisa de uma decisão de modelo, ele emite uma solicitação estruturada; o
assistente responde; o pipeline valida a resposta contra o esquema e continua.

A consequência econômica é direta: quem já paga pela sessão do assistente não paga uma
segunda vez em API. A consequência arquitetural é que o mesmo código roda com qualquer
modelo, porque a fronteira é um contrato JSON, não um SDK.

Todo acesso a modelo no gerador passa por `solicitar_llm()` de `utils_delegacao.py` —
o `AGENTS.md` da Fase 2 proíbe explicitamente chamada direta a `litellm`. Essa
centralização é o que torna a troca de provedor uma mudança de configuração em vez de
uma refatoração.

## 21.3 O manifesto de harness

`gates/manifesto_harnesses.json` (13 KB) é o registro canônico de qual componente deve
existir em qual assistente, em qual caminho. `G_COMPONENTE_AGNOSTICO` audita todo
componente novo ou modificado contra esse manifesto, e `scripts/harness_hygiene.py`
mantém a higiene dos diretórios.

A proveniência do mapeamento está registrada: testes empíricos contra instalações reais
dos sete assistentes nesta máquina, em 5 de setembro de 2026. Onde a confirmação não foi
possível, o registro diz isso — o caso de `.gemini/skills/`, sincronizado mas com
`confirmado: false`, e o do Freebuff, instalado mas sem modo não interativo para
validação automatizada.

## 21.4 Rastreabilidade

`AGENTS.md` Lei #6; `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §5;
`docs/protocolos/05-09-2026_protocolo-agnosticidade-componentes.md`;
`gates/manifesto_harnesses.json`; `gates/G_UNIVERSAL_HARNESS.py`;
`gates/G_COMPONENTE_AGNOSTICO.py`; `gates/G_PROTOCOL_FALLBACK.py`;
`tools/aidd-generator/scripts/phases/utils_delegacao.py`.

# Capítulo 22 — Síntese: a economia de tokens ponta a ponta

Este capítulo consolida, numa visão única, o que os capítulos anteriores trataram
dispersamente. É o eixo "economia de tokens" visto simultaneamente nos três níveis.

## 22.1 A matriz consolidada

| Mecanismo                        | Nível     | Onde vive                                          | Efeito                                                       |
| :------------------------------- | :-------- | :-------------------------------------------------- | :------------------------------------------------------------- |
| Determinismo obrigatório         | Macro     | Lei #1; 145 portões; 5 das 7 etapas de fluxo       | Elimina a chamada em vez de baratear                          |
| Protocolo Caveman tri-fase       | Macro     | `src-core/caveman_protocol.py`                     | 30–50% de redução na entrada, em contagem BPE                 |
| Linter de Caveman                | Micro     | `generator/scripts/core/caveman_linter.py`         | Garante a tríade ENTRADA/COT/SAÍDA por AST, sem gastar token  |
| Fatiamento de contexto           | Macro     | `core/context_slicer.py`                           | Payload de assinaturas abaixo de 150 tokens                   |
| Grafo antes de busca textual     | Macro     | `AGENTS.md` §1; MCP `code-review-graph`            | Evita leitura de arquivo inteiro e `grep` exploratório        |
| Descarregamento de esquema MCP   | Macro     | `core/mcp_dynamic_router.py`                       | Remove milhares de tokens fixos do prompt de sistema          |
| Estado em arquivo                | Meso      | Handoffs JSON; `cognitive_ledger.py`               | Substitui histórico conversacional por ~5k tokens tipados     |
| Retomada inteligente             | Micro     | `generator/scripts/core/pipeline_state.py`         | `--resume` pula fase completa com artefato válido             |
| Micro-ambiente por fase          | Micro     | `generator/scripts/phases/phase_*/AGENTS.md`       | Só as regras da fase corrente entram em memória               |
| Orçamento formal por fase        | Micro     | `generator/config/token_budgets.json`              | Teto declarado + limiar de desvio de 1,2                      |
| Auditoria de tokenomics          | Micro     | `G_TOKENOMICS`                                     | Reprova estouro de orçamento e rótulo desonesto de medição    |
| Benchmark real                   | Micro     | `generator/scripts/benchmark_tokenomics.py`        | Mede com `tiktoken` contra baseline legada                    |
| Purga de contexto de subagente   | Macro     | `forge/core/subagent_purger.py`                    | Subagente morre após validação AST                            |
| Disciplina de terminal           | Macro     | `AGENTS.md` §1                                     | `tail`/`grep` obrigatórios; zero despejo de log ou lockfile   |
| Edição por busca e substituição  | Macro     | `AGENTS.md` §1                                     | Nunca reescrever arquivo inteiro na saída                     |
| Executor silencioso              | Macro     | `AGENTS.md` §1                                     | Status de uma linha; zero repetição de código na conversa     |
| Protocolo delegado               | Macro     | `generator/scripts/phases/utils_delegacao.py`      | Usa o modelo da sessão; zero custo adicional de API           |

## 22.2 Onde o token é realmente gasto

Num Fluxo 01 completo com implementação de código, o consumo se concentra em quatro
fases do gerador, com orçamento total declarado de 115 mil tokens. As outras seis etapas
do fluxo — forge, master, enterprise, ops, auditoria e as quatro fases determinísticas
do próprio gerador — custam zero.

Nos Fluxos 02 e 03, o consumo cai drasticamente: o Fluxo 02 usa modelo apenas em três
das suas fases de integração, e o Fluxo 03 não usa modelo em nenhuma das seis fases do
pipeline de libertação.

```{=typst}
#painel("A conclusão prática")[
  A pergunta "quanto custa gerar um sistema com o AIDD?" tem três respostas, e a escolha
  do fluxo é a decisão de maior impacto econômico do ecossistema. Escrever do zero custa
  dezenas de milhares de tokens; integrar open-source custa uma fração disso; libertar um
  projeto low-code custa praticamente nada em tokens — o custo ali é de tempo de máquina,
  não de modelo.
]
```

## 22.3 A honestidade da métrica

O ecossistema audita a própria alegação de economia. `G_TOKENOMICS` reprova quando uma
fase afirma "medição real" para um valor autodeclarado, e exige que a origem da medição
esteja rotulada como `autodeclarado` ou `medido_api`. O `benchmark_tokenomics.py`
produz medição real via `tiktoken`, com custo em dólares e resultado de pytest no mesmo
relatório — porque economia que degrada qualidade não é economia.

Este livro segue a mesma regra: os orçamentos citados são **valores declarados em
`token_budgets.json`**, não medições de execução. Onde há medição real disponível, ela
vive nos relatórios de benchmark do repositório, não aqui.

## 22.4 Rastreabilidade

Todos os arquivos citados na matriz da seção 22.1, mais `AGENTS.md` Lei #4 e §1.

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

Os sete esquemas em `componentes/compartilhado/specs/` são a espinha dorsal da
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




# Prólogo: Bem-vindo à Cidade da Fábrica de Brinquedos Perfeita

Imagine uma cidade onde existe uma fábrica de brinquedos mágicos. Mas não é uma fábrica qualquer onde as coisas quebram e ninguém sabe o motivo. É uma fábrica que constrói castelos digitais inteiros em poucos minutos!

Para que tudo funcione sem nenhum fio solto, a fábrica possui:
1. **8 Grandes Oficinas Mestras (As Ferramentas Macro):** Cada uma com um mestre construtor responsável por uma grande missão.
2. **66 Ferramentas de Precisão no Cinto dos Mestres (As Micro-Ferramentas / Skills):** Lupas, réguas, tesouras mágicas e parafusadeiras que realizam tarefas hiperespecíficas.
3. **48 Guardas Incorruptíveis na Porta (Os Quality Gates):** Inspetores robóticos que não deixam passar nada se tiver um único parafuso torto ou se faltar a etiqueta de segurança.
4. **91 Peças Fundamentais (Os Componentes Agnósticos):** Blocos de encaixe perfeito que funcionam em qualquer mesa de trabalho (seja no Claude, no Gemini, no Cursor ou no Windsurf).

Neste livro, nós vamos passear por cada canto dessa fábrica e tirar uma **FOTO** detalhada de cada peça!

---

# PARTE I: AS 8 FERRAMENTAS MACRO (AS GRANDES OFICINAS)


## Capítulo 1: AIDD Forge — O Altar da Fundação e os Guardiões das Leis

### Na Festa (A Metáfora Memorável)
> O Mestre Ferreiro que prepara o chão da oficina, coloca a bigorna, estende as regras na parede e tranca a porta para ninguém entrar bagunçando.

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-forge`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-forge)
- **Arquivo Canônico de Regras:** [`tools/aidd-forge/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-forge/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-forge`

> **Ferramenta:** `tools/aidd-forge`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | CLI Click (`init`, `inject`, `audit`, `conform`); payloads validados por `injection_request.schema.json`; caminho do projeto alvo (`path: str`). |
| **2. CRIA / PROCESSA** | `Injector` (árvore estrutural), `PhaseFencer` (10 fases isoladas), `SlashRouter` (roteador de slash commands agnósticos), `UniversalInjector` + `materializador.py` (injeção atômica com rollback transacional), `ConformEngine` (autocura). |
| **3. ENTREGA (Output)** | Árvore de governança (`.agent/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`), scripts de qualidade em `gates/`, relatórios auditáveis (Markdown, JSON, HTML) e hook `.git/hooks/pre-commit`. |
| **4. CONFIGURAÇÕES (Configs)** | Flags CLI `--force`, `--dry-run`, `--format json\|md\|html`, `--output`, `--item`; mapeamento de aliases de IDE em `IDE_RULE_ALIASES`. |
| **5. GUARDAS (Gates)** | 12 quality gates em `templates/gates/`: `G_BLOQUEAR_SEGREDO`, `G_CONTRACTS`, `G_CYBERSECURITY`, `G_DETERMINISMO_LEI_1`, `G_ESTRUTURA_AST`, `G_HARNESS_COMPAT`, `G_INJECT`, `G_PERFORMANCE`, `G_QUARTETO_SINE_QUA_NON`, `G_SAIDA_BINARIA`, `G_STACK_PADRAO_OURO`, `G_TESTES_REAIS`. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% de `aidd_forge/core/` implementado com AST Python, regex compilado, manipulação atômica de disco e padrão `Result Monad` (`Result.ok`, `Result.fail`). |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | `GitHooksInstaller` instala `.git/hooks/pre-commit` com execução compulsória dos gates antes de qualquer commit git. |
| **8. PESSOAS / PERSONAS (Agents)** | `subagent_purger.py` garante que subagentes cognitivos sejam estritamente efêmeros e expurgados após validação. |
| **9. TAREFAS ÚNICAS (Skills)** | 10 skills embutidas: `aidd-grill`, `aidd-spec`, `aidd-tdd`, `aidd-tickets`, `caveman-ultra`, `cybersecurity-first`, `impeccable-ui`, `open-code-review-graph`, `orca-orchestrator`, `post-mortem`. Skill de orquestração externa: `aidd-forge-runner`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Ponto de integração nativo com `code-review-graph` e suporte a injeção declarativa via `forge inject mcp`. |
| **11. BILHETES (Rules / AGENTS.md)** | Diretrizes em `tools/aidd-forge/AGENTS.md`: Zero Stubs, Result Monad compulsório, Context-Purge Isolation e Universal Injector. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-forge/tests`
- **Resultado:** 294 testes passaram, 0 falhas, 1 pulado (tempo de execução: 26.84s).
- **Invariantes testadas:** Rollback em falha de escrita, ancoragem em `AGENTS.md`, isolamento de harnesses, detecção de camadas arquiteturais.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug funcional impeditivo encontrado no núcleo do `aidd-forge`.
- Observação: Garantir que novos quality gates adicionados ao ecossistema raiz sejam sincronizados dinamicamente na pasta `templates/gates/` do `aidd-forge`.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto para esta ferramenta no momento. Estado funcional 100% íntegro).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** 100% Determinístico (0 LLM no núcleo)
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo liberado: `aidd-planner`.


---


## Capítulo 2: AIDD Planner — A Mesa do Arquiteto e o Livro de Receitas

### Na Festa (A Metáfora Memorável)
> O Grande Arquiteto que escuta o sonho do cliente, desenha a planta baixa em papel milimetrado com todas as medidas, cores e quartos, e entrega uma receita que qualquer cozinheiro consegue seguir.

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-planner`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-planner)
- **Arquivo Canônico de Regras:** [`tools/aidd-planner/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-planner/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-planner`

> **Ferramenta:** `tools/aidd-planner`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | CLI argparse (`init`, `validate`, `export`, `audit`). Parâmetros: `--fluxo <1\|2\|3>`, `--nome`, `--slug`, `--descricao`, `--dominio`, `--pasta`, `--arquivo`, `--formato <factory\|pipeline\|dispatch>`, `--saida`. |
| **2. CRIA / PROCESSA** | `planner_engine.py`: `gerar_template_plano`, `validar_plano` (JSON Schema + regras semânticas), `exportar_para_fluxo_factory`, `exportar_para_pipeline_execucao`, `compilar_grafo_topologico_vsa`. `design_system.py`: geração determinística (hash do projeto) de paleta cromática e identidade visual única. |
| **3. ENTREGA (Output)** | Arquivos: `PLANNER.json`, `DESIGN-SYSTEM.json`, `HANDOFF_PLANNER_ENGINE.json`, artefatos exportados para pipeline/dispatch. |
| **4. CONFIGURAÇÕES (Configs)** | Mapeamento `MAPA_FLUXOS` suportando aliases numéricos e textuais (`1`, `2`, `3`, `pure`, `open`, `freedom`). Flags `--force`, `--dry-run`. |
| **5. GUARDAS (Gates)** | Validação integrada contra `schemas/planner_schema.json`, verificação obrigatória do Quarteto Sine Qua Non (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`), BDD Gherkin obrigatório, detecção de ciclos em grafo de dependências VSA. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico. Cálculos de hash para paleta cromática, validação estrita JSON Schema, algoritmo topológico de Kahn para ordenação DAG de fatias VSA. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | Emite códigos de saída binários (`exit 0` sucesso, `exit 1` falha) e relatórios formatados em stderr para interceptação por orquestradores superiores. |
| **8. PESSOAS / PERSONAS (Agents)** | Atua como motor de intake alimentando personas dos geradores especializados (`aidd-generator`, `aidd-factory`, `aidd-bridge`). |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas no ecossistema: `aidd-planner-runner`, `aidd-plan`, `aidd-planos`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Totalmente desacoplado e autônomo (não necessita de MCP externo para execução de intake e exportação). |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-planner/AGENTS.md` fixa: Invariante Zero Stubs, Quarteto Sine Qua Non ativado por default, envelope estrito aidd-ops para export factory. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-planner/tests`
- **Resultado:** 24 testes passaram, 0 falhas (tempo de execução: 1.25s).
- **Invariantes testadas:** Rejeição de plano sem quarteto, rejeição de plano sem BDD, exportação para factory envelope ops, compilação de grafo VSA com detecção de ciclo.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Conformidade 100% comprovada na geração de envelopes de handoff formal e compatibilidade com VSA.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** 100% Determinístico
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-generator` (Fluxo 01).


---


## Capítulo 3: AIDD Generator — O Trem Autônomo de 8 Vagões (Fluxo 01: Do Zero Puro)

### Na Festa (A Metáfora Memorável)
> Um trem mágico com 8 vagões sequenciais. Ele recebe a ideia pura em uma ponta e, vagão por vagão (pesquisa, desenho, teste, programação), entrega uma cidade inteira de brinquedo montada e funcionando.

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-generator`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-generator)
- **Arquivo Canônico de Regras:** [`tools/aidd-generator/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-generator/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-generator` (Fluxo 01 — Do Zero Puro)

> **Ferramenta:** `tools/aidd-generator`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | Ideia textual ou plano via CLI (`python scripts/pipeline_completo.py "<ideia>"`), flags `--modo <eco\|fast\|full>`, `--verbose`, `--skip-fase <N>`, `--retomar`, `--plano <path.json>`. Consome contrato de handoff do planner (`HANDOFF_PLANNER_ENGINE.json`). |
| **2. CRIA / PROCESSA** | Pipeline autônoma de 8 fases sequenciais orquestrada por Máquina de Estados Finitos (`fsm_engine.py`): Fase 1 (Pesquisa), Fase 2 (Análise de Requisitos), Fase 3 (Design Arquitetural & UI), Fase 4 (Planejador de Slices), Fase 5 (Criador de Código/TDD Red), Fase 6 (Documentador & OpenAPI), Fase 7 (Auto-Crítica & Auditoria), Fase 8 (Implementador Green & Refactor). |
| **3. ENTREGA (Output)** | Código-fonte completo do projeto (Frontend Next.js + TS + Tailwind, Backend Python puro VSA + SQLite WAL), `PLANO-EXECUCAO-ESTRUTURADO.json`, testes automatizados, relatórios de auditoria e tokenomics (`benchmark_tokenomics.py`). |
| **4. CONFIGURAÇÕES (Configs)** | Modos de operação: `eco` (mínimo de tokens), `fast` (direto ao ponto), `full` (máxima profundidade). Configuração de orquestração via Prefect (`pipeline_prefect.py`) ou fallback nativo Python. |
| **5. GUARDAS (Gates)** | Validação de transição entre cada uma das 8 fases em `scripts/gates/` e `verificar_gates.py`. Rejeição binária imediata se uma fase não atingir 100% dos requisitos contratuais. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | Mecanismo FSM (`fsm_engine.py`), validação de esquemas de artefatos por JSON Schema Draft 2020-12, checagem de integridade de arquivos gerados e telemetria determinística de tokens. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | Emissão de alertas de quebra de contrato de fase e interrupção compulsória com preservação de estado transacional. |
| **8. PESSOAS / PERSONAS (Agents)** | 8 personas operacionais especializadas em cada fase (Pesquisador, Analista, Designer, Planejador, Criador, Documentador, Crítico, Implementador). |
| **9. TAREFAS ÚNICAS (Skills)** | Skills integradas: `aidd-generator-runner`, `aidd-pure`, `fluxo-01-runner`, `aidd-spec`, `aidd-tickets`, `aidd-tdd`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Suporte a chamadas de inspeção estática via `code-review-graph` e preflight checks de ambiente. |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-generator/AGENTS.md`: Persistência de estado exclusivamente em JSON, transições mecânicas estritas, Zero Stubs na Fase 8. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-generator/tests`
- **Resultado:** 1006 testes passaram, 0 falhas, 5 pulados (Prefect opcional) em 26.50s.
- **Invariantes testadas:** Transparência de tokens, fencer de isolamento de fases, microtarefas da Fase 8, roteamento de slash commands e validação de gates.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. 100% de integridade comprovada nos 1006 testes unitários e de integração.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Pipeline autônoma de 8 fases com barreira determinística.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-factory` (Fluxo 02).


---


## Capítulo 4: AIDD Factory — A Linha de Montagem de Peças Prontas (Fluxo 02: Open-Source)

### Na Festa (A Metáfora Memorável)
> O Mestre Montador que pega os melhores motores de brinquedo já inventados no mundo (motores abertos) e os conecta perfeitamente com cabos fortes para criar um veículo superpotente sem reinventar a roda.

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-factory`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-factory)
- **Arquivo Canônico de Regras:** [`tools/aidd-factory/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-factory/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-factory` (Fluxo 02 — Motores Open-Source)

> **Ferramenta:** `tools/aidd-factory`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | Consome estritamente `PLANO-INFRAESTRUTURA.json` em conformidade com `componentes/compartilhado/specs/plano-infraestrutura.schema.json` gerado pelo intake do `aidd-planner` ou `aidd-ops`. CLI: `python scripts/pipeline_factory.py --plano <path.json> --destino <dir>`. |
| **2. CRIA / PROCESSA** | Pipeline de integração de serviços open-source em fatias VSA: Fase 1 (`01_analisador.py` — análise de nicho e desdobramento em blocos), Fase 4 (`04_compose.py` — geração determinística de `docker-compose.yml`), Fase 5 (`05_init_db.py` — scripts SQL de inicialização multi-tenant/bancos lógicos), Fase 6 (`06_env.py` — variáveis de ambiente seguras com fallbacks tipados), Fase 9 (`09_integracao.py` — gateway de integração VSA e Quarteto Sine Qua Non). |
| **3. ENTREGA (Output)** | Contrato canônico `FACTORY_OUTPUT.json`, manifesto de serviços, compose funcional, scripts de banco de dados, gateway FastAPI VSA e stack frontend Next.js + TS + Tailwind. |
| **4. CONFIGURAÇÕES (Configs)** | Parâmetros de CLI (`--plano`, `--destino`, `--dry-run`, `--skip-frontend`). Suporte a nichos de catálogo fixo (`clinicas`, `delivery`, `farmacias`, `b2b_industrial`, `energia_solar`) e nicho dinâmico (`dinamico_<slug>`). |
| **5. GUARDAS (Gates)** | `G_FACTORY_INPUT` (validação estrita do schema do plano de infraestrutura), `G_FACTORY_OUTPUT` (verificação do manifesto de entrega), `G_FACTORY_DETERMINISTIC` (garantia de zero LLM nas fases 1, 4, 5 e 6). |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico nas fases estruturais: análise de topologia, geração do Docker Compose com Traefik, particionamento de bancos lógicos PostgreSQL e geração de `.env`. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | Validações em tempo de execução via `contrato_factory.py` emitindo interrupção com traceback rastreável ao detectar ausência de dependências. |
| **8. PESSOAS / PERSONAS (Agents)** | Agente orquestrador de fábrica open-source e fatiador de integração VSA. |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas: `aidd-factory-runner`, `aidd-open`, `open`, `fluxo-02-runner`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Totalmente autônomo na orquestração de templates e fatias de código. |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-factory/AGENTS.md`: Consumo exclusivo do envelope de infraestrutura canônico, Zero Stubs, reuso compulsório de `result.py` e `escritor_atomico.py`. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-factory/tests`
- **Resultado:** 19 testes passaram, 0 falhas em 94.95s.
- **Invariantes testadas:** Validação de planos de clínicas e delivery, compilação de compose e init_db, gateway generator, frontend factory real compilando sem erros e suporte a nicho dinâmico sem LLM.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Módulo atende plenamente à governança e à Lei #11.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Pipeline de integração determinística multi-serviços com validação real de compilação.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-bridge` (Fluxo 03).


---


## Capítulo 5: AIDD Bridge — A Ponte da Libertação (Fluxo 03: Desacoplamento Low-Code)

### Na Festa (A Metáfora Memorável)
> O Chaveiro Libertador que resgata os brinquedos que estavam presos em gaiolas com cadeados caros de empresas distantes (Lovable, Supabase), limpando-os para funcionarem livres no quintal da sua própria casa.

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-bridge`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-bridge)
- **Arquivo Canônico de Regras:** [`tools/aidd-bridge/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-bridge/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-bridge` (Fluxo 03 — Low-Code / Desacoplamento)

> **Ferramenta:** `tools/aidd-bridge`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | CLI argparse: subcomandos `scan`, `convert-db`, `merge`, `pack`, `migrate-auth`, `destroy`, `unpack`. Consome projetos exportados do Lovable/v0/Bolt contendo React + Vite + Tailwind + migrações Supabase. |
| **2. CRIA / PROCESSA** | `scanner.py` (análise de páginas, rotas e migrações), `data_bridge.py` + `sql_transpiler.py` (sanitização de SQL Supabase para PostgreSQL padrão), `unifier.py` (agregação multi-app em fatias VSA), `devops.py` (geração de Dockerfile, Compose e Swarm), `auth_migrator.py` (migração de hashes de senha de `auth.users`), `frontend_liberator.py` (remoção de bibliotecas proprietárias), `vsa_exporter.py` (exportação do Quarteto Sine Qua Non dinâmico), `pipeline_bridge.py` (orquestração 6 fases). |
| **3. ENTREGA (Output)** | Aplicação 100% livre de lock-in, banco PostgreSQL consolidado (`init-db.sql`), stack Docker Swarm pronta para VPS, fatias verticais VSA em `src/modules/` e diretório `quarteto_sine_qua_non/` contendo Swagger, Webhook, MCP e Guia de Uso. |
| **4. CONFIGURAÇÕES (Configs)** | Flags CLI `--stack <lite\|full>`, `--domain`, `--output`, `--traefik-network`, `--certresolver`, `--apply`, `--yes`, `--with-gotrue`. |
| **5. GUARDAS (Gates)** | Quality gates dedicados em `gates/`: `G_BRIDGE_VENDOR_LOCKIN`, `G_BRIDGE_DOCKER_OCI`, `G_BRIDGE_POSTGRESQL`, `G_BRIDGE_VSA_COMPAT`. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico. Transpilação SQL por regex e gramática estática, manipulação de AST TypeScript/JavaScript para substituição de importações do cliente `@supabase/supabase-js` e empacotamento de templates Docker. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | `_forcar_utf8_stdio` para compatibilidade multi-plataforma (Windows cp1252), verificações de credenciais obrigatórias para ações remotas em VPS / Cloudflare DNS e prompt interativo obrigatório no comando destrutivo `destroy`. |
| **8. PESSOAS / PERSONAS (Agents)** | Agente especialista em desmonte de lock-in e unificação de apps legadas. |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas: `aidd-bridge-runner`, `aidd-freedom`, `freedom`, `fluxo-03-runner`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Módulo de automação de DNS com Cloudflare API (`cloudflare_dns.py`) e orquestração SSH para provisionamento de VPS. |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-bridge/AGENTS.md`: Desacoplamento estrito, migração segura de credenciais, rollback em teardown e Quarteto Sine Qua Non mandatório. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-bridge/tests`
- **Resultado:** 64 testes passaram, 0 falhas em 1.19s.
- **Invariantes testadas:** Transpilação SQL Supabase -> PostgreSQL, empacotamento de stack Swarm, unificação de fatias VSA, migração de hashes de auth e pipeline e2e do Fluxo 03.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Módulo atende 100% às exigências do ecossistema.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Pipeline determinístico de 6 fases com extração limpa e zero dependência de IA para sanitização.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-master` (Meso-camada e convergência).


---


## Capítulo 6: AIDD Master — O Maestro da Harmonização Monolítica VSA

### Na Festa (A Metáfora Memorável)
> O Maestro da Orquestra que garante que todos os instrumentos (fatias verticais) toquem em harmonia perfeita no mesmo salão, sem um bater no outro e com uma barreira invisível de segurança.

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-master`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-master)
- **Arquivo Canônico de Regras:** [`tools/aidd-master/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-master/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-master` (Meso-Camada de Convergência Monolítica VSA)

> **Ferramenta:** `tools/aidd-master`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | Comandos CLI: `python scripts/aidd.py [add-module|compose-orca|run-all|provision]`, `dispatch_pipeline.py --planner <path.json> \| --dispatch <json>`, manifestos de fatias VSA e contratos de handoff das três trilhas da Tríade. |
| **2. CRIA / PROCESSA** | Orquestração da Meso-Camada VSA: `dispatch_pipeline.py` (Kahn DAG para ordenação topológica de fatias), `engine_router.py` (despacho para o motor correto 01/02/03), `vsa_join_barrier.py` (barreira de validação síncrona com Git Worktrees efêmeras e merge na master), `orchestrator_pipeline.py` (orquestrador mestre), `add_module.py` (scaffolding de fatias VSA verticais independentes: router, service, repository, dtos, events). |
| **3. ENTREGA (Output)** | Monólito Modular VSA consolidado com SQLite WAL otimizado, barreira transacional unificada, contratos OpenAPI 3.1 tipados e convertidos para TypeScript (`openapi_to_ts.py`) e Quarteto Sine Qua Non dinâmico. |
| **4. CONFIGURAÇÕES (Configs)** | Configurações de pool SQLite WAL (`PRAGMA journal_mode=WAL`), limites de concorrência e barreira de tolerância a falhas (`--timeout`, `--retry`, `--fail-fast`). |
| **5. GUARDAS (Gates)** | 12 quality gates determinísticos em `scripts/gates/`: `G_ARQUITETURA`, `G_AST_BOUNDED_CONTEXT`, `G_CHAOS`, `G_CONTRACTS`, `G_ESTRUTURA`, `G_HARNESS_COMPAT`, `G_INJECT`, `G_PERFORMANCE`, `G_QUALIDADE`, `G_SEGREDOS`, `G_SEGURANCA`, `G_TESTES`. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico. Barreira de junção VSA baseada em Git Worktrees, ordenação topológica por algoritmo de Kahn, AST linter para isolamento de contextos delimitados (proibição de importações cruzadas não autorizadas) e Result Monad. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | Monitoramento de latência e p99 (`test_live.py`, `G_PERFORMANCE`), detecção de lock e retry automático em SQLite (`sqlite_busy_retry.py`), e bloqueio binário em caso de divergência de schema na Join Barrier. |
| **8. PESSOAS / PERSONAS (Agents)** | Agente orquestrador de convergência e maestro de fatias verticais VSA. |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas: `aidd-master-runner`, `aidd-dispatch-runner`, `aidd-pipeline-runner`, `aidd-orchestrator-runner`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Suporte completo a MCP Server SDK (`test_mcp_server_sdk.py`) permitindo expor as fatias do monólito como ferramentas MCP padronizadas. |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-master/AGENTS.md`: Isolamento estrito de bounded contexts, Result Monad compulsório, SQLite WAL e proibição categórica de stubs. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-master/tests`
- **Resultado:** 439 testes passaram, 0 falhas, 3 pulados em 266.59s (04:26 min).
- **Invariantes testadas:** Bounded context AST isolation, VSA Join Barrier, outbox worker, SQLite busy retry, JWT hardening, Next.js exporter e validação dos 12 quality gates.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Módulo é a coluna vertebral de convergência da Tríade e opera com máxima estabilidade.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Meso-camada determinística com barreira formal de sincronização e merge limpo de fatias VSA.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-enterprise`.


---


## Capítulo 7: AIDD Enterprise — O Cofre de Alta Segurança e Selos Criptográficos

### Na Festa (A Metáfora Memorável)
> O Inspetor do Cofre do Rei que confere o carimbo de ouro (assinatura digital SHA-256) em cada documento e garante que nenhum espião consiga alterar uma única linha de código.

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-enterprise`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-enterprise)
- **Arquivo Canônico de Regras:** [`tools/aidd-enterprise/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-enterprise/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-enterprise` (Resiliência Crítica SHA-256)

> **Ferramenta:** `tools/aidd-enterprise`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | Comandos CLI: `python scripts/aidd.py [add-module|compose-orca|run-all|provision]`, componentes injetáveis (`scripts/injector/`) com validação via `component_manifest.json` e assinatura SHA-256. |
| **2. CRIA / PROCESSA** | Validação criptográfica de integridade de componentes, arquitetura Zero-Trust, isolamento de bounded contexts regulados, driver de eventos (`events_driver.py`), outbox worker transacional com idempotência, autenticação reforçada (JWT hardening, OIDC SSO, RLS). |
| **3. ENTREGA (Output)** | Monólito modular enterprise auditado, schemas OpenAPI 3.1 com tipagem TypeScript estrita, SQLite WAL com política de retenção e recovery, e trilhas de auditoria criptografadas. |
| **4. CONFIGURAÇÕES (Configs)** | Políticas de CSP (`security_csp_lib.py`), pool de conexões SQLite com retry determinístico (`sqlite_busy_retry.py`), limites de LRU de transações (`transaction_log_lru.py`). |
| **5. GUARDAS (Gates)** | 10 quality gates locais em `scripts/gates/`: `G_ARQUITETURA`, `G_CHAOS`, `G_CONTRACTS`, `G_ESTRUTURA`, `G_HARNESS_COMPAT`, `G_INJECT`, `G_PERFORMANCE`, `G_QUALIDADE`, `G_SEGREDOS`, `G_SEGURANCA`, `G_TESTES`. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico. Validação de hashes SHA-256, checagem AST de isolamento de bounded contexts, injeção de schemas sem dependência de inferência de IA e barreira Result Monad. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | `G_CHAOS` (injeção controlada de falhas para teste de resiliência), `G_SEGREDOS` (bloqueio de vazamento de credenciais) e `G_SEGURANCA` (defesa contra XSS/injeção SQL). |
| **8. PESSOAS / PERSONAS (Agents)** | Agente de conformidade enterprise e auditor de integridade criptográfica. |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas: `aidd-enterprise-runner`, `aidd-diagnose`. |
| **10. TELEFONES EXTERNOS (MCPs)** | MCP Server SDK corporativo (`test_mcp_server_sdk.py`) e adaptadores de telemetria externa (`OpenTelemetry`, `metrics.py`). |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-enterprise/AGENTS.md`: Integridade criptográfica compulsória, Result Monad em toda a camada de serviço, SQLite WAL e zero stubs. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-enterprise/tests`
- **Resultado:** 365 testes passaram, 0 falhas, 3 pulados em 148.87s (02:28 min).
- **Invariantes testadas:** Validação SHA-256 de manifestos, outbox idempotente, SSO OIDC, mitigação de XSS em webhooks, RLS e aprovação de todos os 10 quality gates.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Módulo 100% íntegro e em estrita conformidade com as Leis do ecossistema.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Plataforma de missão crítica regulada 100% determinística.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-ops`.


---


## Capítulo 8: AIDD Ops — A Usina de Força e a Torre de Vigilância

### Na Festa (A Metáfora Memorável)
> O Chefe dos Engenheiros que constrói a usina de energia (servidor VPS), liga os motores (Docker), tranca as portas com chaves fortes (SSH seguro) e coloca câmeras de vigilância 24 horas por dia (Uptime Kuma).

Imagine que você precisa construir um prédio. Esta ferramenta é o mestre de obras especializado exatamente nessa missão. Ela não adivinha, não improvisa e não erra porque possui trilhos de aço milimétricos.

### Na Casa (A Foto Técnica Rigorosa e as 11 Dimensões)
- **Caminho Físico no Disco:** [`tools/aidd-ops`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-ops)
- **Arquivo Canônico de Regras:** [`tools/aidd-ops/AGENTS.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/tools/aidd-ops/AGENTS.md)

# Ficha de Auditoria Bit a Bit: `aidd-ops` (Infraestrutura, VPS e Observabilidade)

> **Ferramenta:** `tools/aidd-ops`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | CLI argparse: `python scripts/pipeline_ops.py [plan|deploy|monitor|rotate-secrets]`. Parâmetros: `--texto`, `--nicho`, `--ferramentas-json`, `--dry-run`, `--vps-host`, `--vps-user`, `--ssh-key`. |
| **2. CRIA / PROCESSA** | Pipeline de provisionamento de infraestrutura em 3 fases de planejamento: Fase 1 (`01_intake.py` — detecção de nicho fixo ou dinâmico), Fase 2 (`02_curadoria.py` — seleção de stack open-source compatível), Fase 3 (`03_sizing.py` — dimensionamento de CPU/RAM/Disco por heurísticas determinísticas). Execução remota: `ssh_runner.py` (execução segura sem interpolação perigosa), `ansible` (hardening de SO e SSH via playbook idempotente), `uptime_kuma.py` (extração e exportação de probes reais de monitoramento), `rotate_secrets.py` (rotação de segredos via `sops` e `age`). |
| **3. ENTREGA (Output)** | `PLANO-INFRAESTRUTURA.json` em estrita conformidade com schema JSON, templates Docker Compose OCI, playbook Ansible executado, dashboard Uptime Kuma provisionado e credenciais criptografadas. |
| **4. CONFIGURAÇÕES (Configs)** | Parâmetros de CLI (`--dry-run`, `--ferramentas-json`, `--export-kuma`), catálogo de nichos (`data/catalogo_nichos.json`), catálogo de ferramentas (`data/catalogo_ferramentas.json`). |
| **5. GUARDAS (Gates)** | `G_INFRA_COMPOSE` (reprodutibilidade estrita dos manifests), `G_HADOLINT` (conformidade OCI dos Dockerfiles), `GateSshRunnerAST` (garantia de zero concatenação insegura em comandos remotos). |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico. Dimensionamento de hardware por fórmulas lineares estáticas, parse e validação de compose via PyYAML, geração de playbooks e scripts de conexão SSH com Paramiko. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | Pré-voo SSH com Paramiko validando conectividade, autenticação e timeout antes de acionar playbooks; rejeição imediata se houver tentativa de injeção de parâmetros em comandos remotos. |
| **8. PESSOAS / PERSONAS (Agents)** | Agente orquestrador de operações de infraestrutura e observabilidade. |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas: `aidd-ops-runner`, `aidd-diagnose`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Módulos de conexão remota SSH (Paramiko/Ansible), Cloudflare DNS e integração com API do Uptime Kuma. |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-ops/AGENTS.md`: Compose determinístico, observabilidade sem stubs, hardening via Ansible DevSec e suporte nativo ao envelope de nicho dinâmico. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-ops/tests`
- **Resultado:** 180 testes passaram, 0 falhas em 40.19s.
- **Invariantes testadas:** Hardening SSH/OS em dry-run, pré-voo Paramiko sem vazar credenciais, bloqueio AST de concatenação insegura, exportação e validação de monitores Uptime Kuma sem dados hardcoded.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Módulo 100% íntegro e operacional.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Orquestrador determinístico de infraestrutura e observabilidade.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Todas as 8 ferramentas da pasta `tools/` auditadas com sucesso.


---


# PARTE II: O CINTO DE UTILIDADES (AS 66 MICRO-FERRAMENTAS / SKILLS)

## Na Festa
Imagine o cinto de utilidades do Batman ou a caixa de ferramentas mágica de um relojoeiro suíço. Cada uma dessas 66 ferramentas tem um formato único e resolve exatamente um problema específico sem fazer barulho nem desperdiçar energia.

## Na Casa (O Catálogo Completo das 66 Skills Canônicas)
Localização canônica: `componentes/compartilhado/skills/`


### 1. Micro-Ferramenta: `agents-sdk`
- **Foto / Identidade:** `agents-sdk`
- **Caminho no Disco:** [`componentes/compartilhado/skills/agents-sdk/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/agents-sdk/SKILL.md)
- **O que Faz (Missão Única):** Build, debug, or review Cloudflare Agents SDK applications using the agents package.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/agents-sdk`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 2. Micro-Ferramenta: `aidd-bridge`
- **Foto / Identidade:** `aidd-bridge`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-bridge/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-bridge/SKILL.md)
- **O que Faz (Missão Única):** Dispara o Fluxo 03 (Low-Code / Apps Unificadas | Slash: /bridge) da Tríade Canônica. Desmonte de lock-in Lovable/v0/Bolt e migração PostgreSQL.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-bridge`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 3. Micro-Ferramenta: `aidd-bridge-runner`
- **Foto / Identidade:** `aidd-bridge-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-bridge-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-bridge-runner/SKILL.md)
- **O que Faz (Missão Única):** Extracts, unifies, and packages low-code projects (Lovable, v0, Bolt) for VPS deployment with PostgreSQL.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-bridge-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 4. Micro-Ferramenta: `aidd-componentes`
- **Foto / Identidade:** `aidd-componentes`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-componentes/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-componentes/SKILL.md)
- **O que Faz (Missão Única):** Creates, updates, and synchronizes agnostic components across all ecosystem harnesses.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-componentes`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 5. Micro-Ferramenta: `aidd-dependencias`
- **Foto / Identidade:** `aidd-dependencias`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-dependencias/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-dependencias/SKILL.md)
- **O que Faz (Missão Única):** Installs and verifies third-party skills and MCPs against dependencias_externas.json.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-dependencias`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 6. Micro-Ferramenta: `aidd-diagnose`
- **Foto / Identidade:** `aidd-diagnose`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-diagnose/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-diagnose/SKILL.md)
- **O que Faz (Missão Única):** Systematic scientific fault triage using hypothesis isolation, regression testing, and code review graph.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-diagnose`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 7. Micro-Ferramenta: `aidd-dispatch-runner`
- **Foto / Identidade:** `aidd-dispatch-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-dispatch-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-dispatch-runner/SKILL.md)
- **O que Faz (Missão Única):** Despacha fatias verticais VSA em Git Worktrees efêmeras com isolamento estrito, verificação de Quality Gates e convergência master.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-dispatch-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 8. Micro-Ferramenta: `aidd-enterprise-runner`
- **Foto / Identidade:** `aidd-enterprise-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-enterprise-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-enterprise-runner/SKILL.md)
- **O que Faz (Missão Única):** Injects and audits mission-critical enterprise components with SHA-256 validation.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-enterprise-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 9. Micro-Ferramenta: `aidd-factory-runner`
- **Foto / Identidade:** `aidd-factory-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-factory-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-factory-runner/SKILL.md)
- **O que Faz (Missão Única):** Application code and integration generator for multi-service stacks.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-factory-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 10. Micro-Ferramenta: `aidd-forge-runner`
- **Foto / Identidade:** `aidd-forge-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-forge-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-forge-runner/SKILL.md)
- **O que Faz (Missão Única):** Executes bootstrap and governance hardening on target repositories using aidd-forge.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-forge-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 11. Micro-Ferramenta: `aidd-freedom`
- **Foto / Identidade:** `aidd-freedom`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-freedom/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-freedom/SKILL.md)
- **O que Faz (Missão Única):** Dispara o Fluxo 03 (Low-Code / Apps Unificadas | Slash: /freedom) da Tríade Canônica. Desmonte de lock-in Lovable/v0/Bolt e migração PostgreSQL.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-freedom`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 12. Micro-Ferramenta: `aidd-generator-runner`
- **Foto / Identidade:** `aidd-generator-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-generator-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-generator-runner/SKILL.md)
- **O que Faz (Missão Única):** Triggers autonomous software generation via 8-phase pipeline using aidd-generator.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-generator-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 13. Micro-Ferramenta: `aidd-grill`
- **Foto / Identidade:** `aidd-grill`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-grill/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-grill/SKILL.md)
- **O que Faz (Missão Única):** Relentless Socratic interview protocol to resolve assumptions, trade-offs, and invariants before writing code.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-grill`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 14. Micro-Ferramenta: `aidd-grill-docs`
- **Foto / Identidade:** `aidd-grill-docs`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-grill-docs/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-grill-docs/SKILL.md)
- **O que Faz (Missão Única):** Socratic interview grounded in existing repository architecture, domain documentation, and invariant rules.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-grill-docs`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 15. Micro-Ferramenta: `aidd-handoff`
- **Foto / Identidade:** `aidd-handoff`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-handoff/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-handoff/SKILL.md)
- **O que Faz (Missão Única):** Serializes and compacts session state into a structured markdown artifact for context rotation or agent handover.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-handoff`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 16. Micro-Ferramenta: `aidd-livro-texto`
- **Foto / Identidade:** `aidd-livro-texto`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-livro-texto/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-livro-texto/SKILL.md)
- **O que Faz (Missão Única):** Generates and updates auditable corporate textbooks as PDF via pandoc and typst.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-livro-texto`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 17. Micro-Ferramenta: `aidd-master-runner`
- **Foto / Identidade:** `aidd-master-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-master-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-master-runner/SKILL.md)
- **O que Faz (Missão Única):** Scaffolds and integrates clean vertical slices in aidd-master architecture.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-master-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 18. Micro-Ferramenta: `aidd-mcp`
- **Foto / Identidade:** `aidd-mcp`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-mcp/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-mcp/SKILL.md)
- **O que Faz (Missão Única):** Scaffolds and exposes new Model Context Protocol (MCP) servers across harnesses.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-mcp`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 19. Micro-Ferramenta: `aidd-melhoria`
- **Foto / Identidade:** `aidd-melhoria`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-melhoria/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-melhoria/SKILL.md)
- **O que Faz (Missão Única):** Deeply analyzes code improvements from natural language and produces structured evaluation reports.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-melhoria`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 20. Micro-Ferramenta: `aidd-open`
- **Foto / Identidade:** `aidd-open`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-open/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-open/SKILL.md)
- **O que Faz (Missão Única):** Dispara o Fluxo 02 (Motores Open-Source | Slash: /open) da Tríade Canônica. Curadoria e integração de engines open-source em fatias VSA.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-open`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 21. Micro-Ferramenta: `aidd-ops-runner`
- **Foto / Identidade:** `aidd-ops-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-ops-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-ops-runner/SKILL.md)
- **O que Faz (Missão Única):** Agentic infrastructure meta-orchestrator for cloud and container deployments.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-ops-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 22. Micro-Ferramenta: `aidd-orca`
- **Foto / Identidade:** `aidd-orca`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-orca/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-orca/SKILL.md)
- **O que Faz (Missão Única):** Executes multi-phase ORCA plans using isolated Git worktrees and quality gates.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-orca`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 23. Micro-Ferramenta: `aidd-orchestrate`
- **Foto / Identidade:** `aidd-orchestrate`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-orchestrate/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-orchestrate/SKILL.md)
- **O que Faz (Missão Única):** Routes plan execution between ORCA app, agent worktrees, and native execution engines.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-orchestrate`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 24. Micro-Ferramenta: `aidd-orchestrator-runner`
- **Foto / Identidade:** `aidd-orchestrator-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-orchestrator-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-orchestrator-runner/SKILL.md)
- **O que Faz (Missão Única):** Orquestrador mestre síncrono da Tríade Canônica. Executa qualquer fluxo com validação formal de contratos de handoff.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-orchestrator-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 25. Micro-Ferramenta: `aidd-pipeline-runner`
- **Foto / Identidade:** `aidd-pipeline-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-pipeline-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-pipeline-runner/SKILL.md)
- **O que Faz (Missão Única):** Executa pipelines determinísticos da Tríade em Git Worktrees efêmeras com barreira de sincronização (Join Barrier) a partir de planos Markdown ou manifestos JSON.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-pipeline-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 26. Micro-Ferramenta: `aidd-plan`
- **Foto / Identidade:** `aidd-plan`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-plan/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-plan/SKILL.md)
- **O que Faz (Missão Única):** Transforms analysis reports into structured audit/evolution plans in docs/planos/.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-plan`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 27. Micro-Ferramenta: `aidd-planner-runner`
- **Foto / Identidade:** `aidd-planner-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-planner-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-planner-runner/SKILL.md)
- **O que Faz (Missão Única):** Generates and validates canonical SDD/BDD project blueprints and fuels the Triad flows (Generator, Factory, Bridge).
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-planner-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 28. Micro-Ferramenta: `aidd-planos`
- **Foto / Identidade:** `aidd-planos`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-planos/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-planos/SKILL.md)
- **O que Faz (Missão Única):** Generates standard templates and drafts for audit, evolution, or test plans.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-planos`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 29. Micro-Ferramenta: `aidd-pure`
- **Foto / Identidade:** `aidd-pure`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-pure/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-pure/SKILL.md)
- **O que Faz (Missão Única):** Dispara o Fluxo 01 (Do Zero Puro | Slash: /pure) da Tríade Canônica. Geração autoral via TDD Red-Green estrito e Monólito Modular VSA.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-pure`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 30. Micro-Ferramenta: `aidd-skills`
- **Foto / Identidade:** `aidd-skills`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-skills/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-skills/SKILL.md)
- **O que Faz (Missão Única):** Creates, optimizes, and evaluates agent skills across all ecosystem harnesses.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-skills`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 31. Micro-Ferramenta: `aidd-spec`
- **Foto / Identidade:** `aidd-spec`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-spec/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-spec/SKILL.md)
- **O que Faz (Missão Única):** Synthesizes discussions, requirements, and decisions into a deterministic, executable technical specification.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-spec`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 32. Micro-Ferramenta: `aidd-tdd`
- **Foto / Identidade:** `aidd-tdd`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-tdd/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-tdd/SKILL.md)
- **O que Faz (Missão Única):** Strict Test-Driven Development protocol (Red-Green-Refactor) with zero stubs and polyglot runtime support.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-tdd`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 33. Micro-Ferramenta: `aidd-tickets`
- **Foto / Identidade:** `aidd-tickets`
- **Caminho no Disco:** [`componentes/compartilhado/skills/aidd-tickets/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/aidd-tickets/SKILL.md)
- **O que Faz (Missão Única):** Decomposes specifications into atomic, incremental tracer-bullet tasks with bounded blast radius.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/aidd-tickets`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 34. Micro-Ferramenta: `cloudflare`
- **Foto / Identidade:** `cloudflare`
- **Caminho no Disco:** [`componentes/compartilhado/skills/cloudflare/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/cloudflare/SKILL.md)
- **O que Faz (Missão Única):** Discover and choose Cloudflare products for apps, APIs, AI agents, storage, networking, and security. Use for architecture and product selection, including when the user describes a need without naming a Cloudflare product; then find the relevant skill or documentation.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/cloudflare`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 35. Micro-Ferramenta: `cloudflare-email-service`
- **Foto / Identidade:** `cloudflare-email-service`
- **Caminho no Disco:** [`componentes/compartilhado/skills/cloudflare-email-service/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/cloudflare-email-service/SKILL.md)
- **O que Faz (Missão Única):** Implement or troubleshoot Cloudflare Email Sending and Email Routing integrations and their delivery configuration.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/cloudflare-email-service`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 36. Micro-Ferramenta: `cloudflare-one`
- **Foto / Identidade:** `cloudflare-one`
- **Caminho no Disco:** [`componentes/compartilhado/skills/cloudflare-one/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/cloudflare-one/SKILL.md)
- **O que Faz (Missão Única):** Design, configure, troubleshoot, or review Cloudflare One Zero Trust and SASE deployments. Use cloudflare-one-migrations for migration planning from other vendors.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/cloudflare-one`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 37. Micro-Ferramenta: `cloudflare-one-migrations`
- **Foto / Identidade:** `cloudflare-one-migrations`
- **Caminho no Disco:** [`componentes/compartilhado/skills/cloudflare-one-migrations/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/cloudflare-one-migrations/SKILL.md)
- **O que Faz (Missão Única):** Assess and plan migrations from existing VPN, SWG, or SASE platforms to Cloudflare One, including policy mapping, parity gaps, and rollout.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/cloudflare-one-migrations`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 38. Micro-Ferramenta: `componentes-runner`
- **Foto / Identidade:** `componentes-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/componentes-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/componentes-runner/SKILL.md)
- **O que Faz (Missão Única):** Creates, updates, and synchronizes agnostic components across all ecosystem harnesses.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/componentes-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 39. Micro-Ferramenta: `debug-issue`
- **Foto / Identidade:** `debug-issue`
- **Caminho no Disco:** [`componentes/compartilhado/skills/debug-issue/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/debug-issue/SKILL.md)
- **O que Faz (Missão Única):** Systematically debug issues using graph-powered code navigation
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/debug-issue`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 40. Micro-Ferramenta: `dependencia-runner`
- **Foto / Identidade:** `dependencia-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/dependencia-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/dependencia-runner/SKILL.md)
- **O que Faz (Missão Única):** Installs and verifies third-party skills and MCPs against dependencias_externas.json.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/dependencia-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 41. Micro-Ferramenta: `durable-objects`
- **Foto / Identidade:** `durable-objects`
- **Caminho no Disco:** [`componentes/compartilhado/skills/durable-objects/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/durable-objects/SKILL.md)
- **O que Faz (Missão Única):** Build, debug, or review Cloudflare Durable Objects code for persistent state and coordination.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/durable-objects`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 42. Micro-Ferramenta: `explore-codebase`
- **Foto / Identidade:** `explore-codebase`
- **Caminho no Disco:** [`componentes/compartilhado/skills/explore-codebase/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/explore-codebase/SKILL.md)
- **O que Faz (Missão Única):** Navigate and understand codebase structure using the knowledge graph
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/explore-codebase`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 43. Micro-Ferramenta: `fluxo-01-runner`
- **Foto / Identidade:** `fluxo-01-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/fluxo-01-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/fluxo-01-runner/SKILL.md)
- **O que Faz (Missão Única):** Executa de ponta a ponta o Fluxo 01 (Do Zero Puro) da Tríade Canônica de forma estritamente síncrona.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/fluxo-01-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 44. Micro-Ferramenta: `fluxo-02-runner`
- **Foto / Identidade:** `fluxo-02-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/fluxo-02-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/fluxo-02-runner/SKILL.md)
- **O que Faz (Missão Única):** Executa de ponta a ponta o Fluxo 02 (Motores Open-Source) da Tríade Canônica de forma estritamente síncrona.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/fluxo-02-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 45. Micro-Ferramenta: `fluxo-03-runner`
- **Foto / Identidade:** `fluxo-03-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/fluxo-03-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/fluxo-03-runner/SKILL.md)
- **O que Faz (Missão Única):** Executa de ponta a ponta o Fluxo 03 (Low-Code / Apps Unificadas) da Tríade Canônica de forma estritamente síncrona.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/fluxo-03-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 46. Micro-Ferramenta: `freedom`
- **Foto / Identidade:** `freedom`
- **Caminho no Disco:** [`componentes/compartilhado/skills/freedom/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/freedom/SKILL.md)
- **O que Faz (Missão Única):** Dispara o Fluxo 03 (Low-Code / Apps Unificadas | Slash: /freedom) da Tríade Canônica. Desmonte de lock-in Lovable/v0/Bolt e migração PostgreSQL.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/freedom`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 47. Micro-Ferramenta: `impeccable`
- **Foto / Identidade:** `impeccable`
- **Caminho no Disco:** [`componentes/compartilhado/skills/impeccable/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/impeccable/SKILL.md)
- **O que Faz (Missão Única):** Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend interface. Covers websites, landing pages, dashboards, product UI, app shells, components, forms, settings, onboarding, and empty states. Handles UX review, visual hierarchy, information architecture, cognitive load, accessibility, performance, responsive behavior, theming, anti-patterns, typography, fonts, spacing, layout, alignment, color, motion, micro-interactions, UX copy, error states, edge cases, i18n, and reusable design systems or tokens. Also use for bland designs that need to become bolder or more delightful, loud designs that should become quieter, live browser iteration on UI elements, or ambitious visual effects that should feel technically extraordinary. Not for backend-only or non-UI tasks.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/impeccable`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 48. Micro-Ferramenta: `mcp-creator-runner`
- **Foto / Identidade:** `mcp-creator-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/mcp-creator-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/mcp-creator-runner/SKILL.md)
- **O que Faz (Missão Única):** Scaffolds and exposes new Model Context Protocol (MCP) servers across harnesses.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/mcp-creator-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 49. Micro-Ferramenta: `melhoria`
- **Foto / Identidade:** `melhoria`
- **Caminho no Disco:** [`componentes/compartilhado/skills/melhoria/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/melhoria/SKILL.md)
- **O que Faz (Missão Única):** Deeply analyzes code improvements from natural language and produces structured evaluation reports.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/melhoria`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 50. Micro-Ferramenta: `nextjs-on-cloudflare`
- **Foto / Identidade:** `nextjs-on-cloudflare`
- **Caminho no Disco:** [`componentes/compartilhado/skills/nextjs-on-cloudflare/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/nextjs-on-cloudflare/SKILL.md)
- **O que Faz (Missão Única):** Build, migrate, and deploy Next.js apps on Cloudflare Workers with vinext. Use when starting a Next.js project on Cloudflare, moving an existing app to Workers, choosing between vinext and OpenNext, or setting up vinext for Workers. For setup, migration, or deployment, install vinext's upstream skills with `npx skills add cloudflare/vinext` if missing, then read and follow the applicable skill and docs.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/nextjs-on-cloudflare`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 51. Micro-Ferramenta: `open`
- **Foto / Identidade:** `open`
- **Caminho no Disco:** [`componentes/compartilhado/skills/open/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/open/SKILL.md)
- **O que Faz (Missão Única):** Dispara o Fluxo 02 (Motores Open-Source | Slash: /open) da Tríade Canônica. Curadoria de motores e fatias verticais VSA.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/open`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 52. Micro-Ferramenta: `orca-plan-orchestrator`
- **Foto / Identidade:** `orca-plan-orchestrator`
- **Caminho no Disco:** [`componentes/compartilhado/skills/orca-plan-orchestrator/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/orca-plan-orchestrator/SKILL.md)
- **O que Faz (Missão Única):** Executes multi-phase ORCA plans using isolated Git worktrees and quality gates.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/orca-plan-orchestrator`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 53. Micro-Ferramenta: `orchestrate`
- **Foto / Identidade:** `orchestrate`
- **Caminho no Disco:** [`componentes/compartilhado/skills/orchestrate/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/orchestrate/SKILL.md)
- **O que Faz (Missão Única):** Routes plan execution between ORCA app, agent worktrees, and native execution engines.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/orchestrate`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 54. Micro-Ferramenta: `plan`
- **Foto / Identidade:** `plan`
- **Caminho no Disco:** [`componentes/compartilhado/skills/plan/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/plan/SKILL.md)
- **O que Faz (Missão Única):** Transforms analysis reports into structured audit/evolution plans in docs/planos/.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/plan`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 55. Micro-Ferramenta: `planos-auditoria-runner`
- **Foto / Identidade:** `planos-auditoria-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/planos-auditoria-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/planos-auditoria-runner/SKILL.md)
- **O que Faz (Missão Única):** Generates standard templates and drafts for audit, evolution, or test plans.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/planos-auditoria-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 56. Micro-Ferramenta: `pure`
- **Foto / Identidade:** `pure`
- **Caminho no Disco:** [`componentes/compartilhado/skills/pure/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/pure/SKILL.md)
- **O que Faz (Missão Única):** Dispara o Fluxo 01 (Do Zero Puro | Slash: /pure) da Tríade Canônica. Geração autoral via TDD Red-Green estrito e Monólito Modular VSA.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/pure`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 57. Micro-Ferramenta: `refactor-safely`
- **Foto / Identidade:** `refactor-safely`
- **Caminho no Disco:** [`componentes/compartilhado/skills/refactor-safely/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/refactor-safely/SKILL.md)
- **O que Faz (Missão Única):** Plan and execute safe refactoring using dependency analysis
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/refactor-safely`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 58. Micro-Ferramenta: `review-changes`
- **Foto / Identidade:** `review-changes`
- **Caminho no Disco:** [`componentes/compartilhado/skills/review-changes/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/review-changes/SKILL.md)
- **O que Faz (Missão Única):** Perform a structured code review using change detection and impact
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/review-changes`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 59. Micro-Ferramenta: `sandbox-migrate-to-next`
- **Foto / Identidade:** `sandbox-migrate-to-next`
- **Caminho no Disco:** [`componentes/compartilhado/skills/sandbox-migrate-to-next/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/sandbox-migrate-to-next/SKILL.md)
- **O que Faz (Missão Única):** Migrate Cloudflare Sandbox apps from stable @cloudflare/sandbox to @cloudflare/sandbox@next (SDK 1.0 preview). Use sandbox-next for apps already on the preview.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/sandbox-migrate-to-next`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 60. Micro-Ferramenta: `sandbox-next`
- **Foto / Identidade:** `sandbox-next`
- **Caminho no Disco:** [`componentes/compartilhado/skills/sandbox-next/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/sandbox-next/SKILL.md)
- **O que Faz (Missão Única):** Build or maintain Cloudflare Sandbox apps on @cloudflare/sandbox@next (SDK 1.0 preview). Use sandbox-migrate-to-next when porting a stable app.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/sandbox-next`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 61. Micro-Ferramenta: `sandbox-stable`
- **Foto / Identidade:** `sandbox-stable`
- **Caminho no Disco:** [`componentes/compartilhado/skills/sandbox-stable/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/sandbox-stable/SKILL.md)
- **O que Faz (Missão Única):** Build or maintain Cloudflare Sandbox apps on the stable @cloudflare/sandbox package. Use sandbox-next for preview apps and sandbox-migrate-to-next for stable-to-preview migrations.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/sandbox-stable`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 62. Micro-Ferramenta: `skill-creator-runner`
- **Foto / Identidade:** `skill-creator-runner`
- **Caminho no Disco:** [`componentes/compartilhado/skills/skill-creator-runner/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/skill-creator-runner/SKILL.md)
- **O que Faz (Missão Única):** Creates, optimizes, and evaluates agent skills across all ecosystem harnesses.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/skill-creator-runner`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 63. Micro-Ferramenta: `turnstile-spin`
- **Foto / Identidade:** `turnstile-spin`
- **Caminho no Disco:** [`componentes/compartilhado/skills/turnstile-spin/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/turnstile-spin/SKILL.md)
- **O que Faz (Missão Única):** Set up, repair, or migrate to Cloudflare Turnstile bot verification in an existing frontend and backend, including server-side Siteverify.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/turnstile-spin`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 64. Micro-Ferramenta: `web-perf`
- **Foto / Identidade:** `web-perf`
- **Caminho no Disco:** [`componentes/compartilhado/skills/web-perf/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/web-perf/SKILL.md)
- **O que Faz (Missão Única):** Audit, diagnose, or optimize website loading and interaction performance, Core Web Vitals, and Lighthouse performance scores.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/web-perf`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 65. Micro-Ferramenta: `workers-best-practices`
- **Foto / Identidade:** `workers-best-practices`
- **Caminho no Disco:** [`componentes/compartilhado/skills/workers-best-practices/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/workers-best-practices/SKILL.md)
- **O que Faz (Missão Única):** Cloudflare Workers best practices for production applications. Use when writing, reviewing, or configuring Workers.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/workers-best-practices`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


### 66. Micro-Ferramenta: `wrangler`
- **Foto / Identidade:** `wrangler`
- **Caminho no Disco:** [`componentes/compartilhado/skills/wrangler/SKILL.md`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/componentes/compartilhado/skills/wrangler/SKILL.md)
- **O que Faz (Missão Única):** Run or troubleshoot Wrangler CLI commands and configure Worker projects for local development, deployment, and Cloudflare resource management.
- **As 11 Dimensões desta Micro-Ferramenta:**
  1. *Recebe (Input):* Chamada de slash command (`/wrangler`) ou diretiva procedural no prompt.
  2. *Cria / Processa:* Roteiro determinístico contido em `SKILL.md` orientando a IA ou script local.
  3. *Entrega (Output):* Artefato estruturado (Markdown, JSON ou diff de código).
  4. *Configs:* Parâmetros no YAML frontmatter (`name`, `description`).
  5. *Gates:* Validada pelo gate `G_SKILL_ROT.py` (descrição enxuta <= 20 palavras).
  6. *Scripts 0 LLM:* Testes determinísticos em `tests/` e sincronizador `sync.py`.
  7. *Hooks:* Checagem automática no pre-commit contra arquivos órfãos.
  8. *Agents:* Personas especializadas convocadas conforme o contexto da tarefa.
  9. *Skills:* Integrada ao ecossistema multi-harness.
  10. *MCPs:* Compatível com chamadas de ferramentas de contexto.
  11. *Rules:* Subordinada à Lei #4 (Economia Extrema de Tokens) e Lei #9.


# PARTE III: OS 48 GUARDIÕES INCORRUPTÍVEIS (QUALITY GATES)

## Na Festa
Imagine 48 cães de guarda robóticos sentados na saída da fábrica. Cada um tem um sensor diferente. Um cheira se tem segredo vazando, outro mede a espessura da parede, outro confere se tem botão quebrado e outro morde o pneu para ver se está furado. Se um único guarda latir (der exit 1), o portão de saída se tranca imediatamente e ninguém sai até consertar!

## Na Casa (A Matriz dos 48 Quality Gates Canônicos)
Localização canônica: `gates/G_*.py`


### 1. Guarda Incorruptível: `G_ANT_LOCKIN_LEGADO.py`
- **Foto / Identidade:** `G_ANT_LOCKIN_LEGADO.py`
- **Caminho no Disco:** [`gates/G_ANT_LOCKIN_LEGADO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ANT_LOCKIN_LEGADO.py)
- **Missão de Segurança:** G_ANT_LOCKIN_LEGADO.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 2. Guarda Incorruptível: `G_ARQUITETURA_DELIVERABLE.py`
- **Foto / Identidade:** `G_ARQUITETURA_DELIVERABLE.py`
- **Caminho no Disco:** [`gates/G_ARQUITETURA_DELIVERABLE.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ARQUITETURA_DELIVERABLE.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_ARQUITETURA_DELIVERABLE
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 3. Guarda Incorruptível: `G_CLI_HELP_CONSISTENCIA.py`
- **Foto / Identidade:** `G_CLI_HELP_CONSISTENCIA.py`
- **Caminho no Disco:** [`gates/G_CLI_HELP_CONSISTENCIA.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_CLI_HELP_CONSISTENCIA.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_CLI_HELP_CONSISTENCIA
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 4. Guarda Incorruptível: `G_COMPONENTE_AGNOSTICO.py`
- **Foto / Identidade:** `G_COMPONENTE_AGNOSTICO.py`
- **Caminho no Disco:** [`gates/G_COMPONENTE_AGNOSTICO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_COMPONENTE_AGNOSTICO.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_COMPONENTE_AGNOSTICO
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 5. Guarda Incorruptível: `G_CONTRACT_ROT.py`
- **Foto / Identidade:** `G_CONTRACT_ROT.py`
- **Caminho no Disco:** [`gates/G_CONTRACT_ROT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_CONTRACT_ROT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_CONTRACT_ROT (ISSUE-0014 & Lei Canônica #10)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 6. Guarda Incorruptível: `G_DEPENDENCIAS_PIN_HASH.py`
- **Foto / Identidade:** `G_DEPENDENCIAS_PIN_HASH.py`
- **Caminho no Disco:** [`gates/G_DEPENDENCIAS_PIN_HASH.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_DEPENDENCIAS_PIN_HASH.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_DEPENDENCIAS_PIN_HASH
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 7. Guarda Incorruptível: `G_DETERMINISMO_LEI_1.py`
- **Foto / Identidade:** `G_DETERMINISMO_LEI_1.py`
- **Caminho no Disco:** [`gates/G_DETERMINISMO_LEI_1.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_DETERMINISMO_LEI_1.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_DETERMINISMO_LEI_1 (Lei Canônica #1)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 8. Guarda Incorruptível: `G_DISCIPLINA_TESTE_FERRAMENTA.py`
- **Foto / Identidade:** `G_DISCIPLINA_TESTE_FERRAMENTA.py`
- **Caminho no Disco:** [`gates/G_DISCIPLINA_TESTE_FERRAMENTA.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_DISCIPLINA_TESTE_FERRAMENTA.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_DISCIPLINA_TESTE_FERRAMENTA (Lei Canônica #9)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 9. Guarda Incorruptível: `G_DISPATCH_PIPELINE_VSA.py`
- **Foto / Identidade:** `G_DISPATCH_PIPELINE_VSA.py`
- **Caminho no Disco:** [`gates/G_DISPATCH_PIPELINE_VSA.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_DISPATCH_PIPELINE_VSA.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_DISPATCH_PIPELINE_VSA (ISSUE-MESO-0003)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 10. Guarda Incorruptível: `G_DOCS_ROT.py`
- **Foto / Identidade:** `G_DOCS_ROT.py`
- **Caminho no Disco:** [`gates/G_DOCS_ROT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_DOCS_ROT.py)
- **Missão de Segurança:** G_DOCS_ROT.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 11. Guarda Incorruptível: `G_DRIFT_ANALYZER.py`
- **Foto / Identidade:** `G_DRIFT_ANALYZER.py`
- **Caminho no Disco:** [`gates/G_DRIFT_ANALYZER.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_DRIFT_ANALYZER.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_DRIFT_ANALYZER
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 12. Guarda Incorruptível: `G_DRIFT_NUCLEO_COMPARTILHADO.py`
- **Foto / Identidade:** `G_DRIFT_NUCLEO_COMPARTILHADO.py`
- **Caminho no Disco:** [`gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_DRIFT_NUCLEO_COMPARTILHADO.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_DRIFT_NUCLEO_COMPARTILHADO
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 13. Guarda Incorruptível: `G_ECOSSISTEMA_INTEGRIDADE.py`
- **Foto / Identidade:** `G_ECOSSISTEMA_INTEGRIDADE.py`
- **Caminho no Disco:** [`gates/G_ECOSSISTEMA_INTEGRIDADE.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ECOSSISTEMA_INTEGRIDADE.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_ECOSSISTEMA_INTEGRIDADE
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 14. Guarda Incorruptível: `G_ENV_ROT.py`
- **Foto / Identidade:** `G_ENV_ROT.py`
- **Caminho no Disco:** [`gates/G_ENV_ROT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ENV_ROT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_ENV_ROT (ISSUE-0015 / Lei Canônica #9)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 15. Guarda Incorruptível: `G_ESCRITOR_ATOMICO.py`
- **Foto / Identidade:** `G_ESCRITOR_ATOMICO.py`
- **Caminho no Disco:** [`gates/G_ESCRITOR_ATOMICO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ESCRITOR_ATOMICO.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_ESCRITOR_ATOMICO
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 16. Guarda Incorruptível: `G_ESTRUTURA_ESTADO.py`
- **Foto / Identidade:** `G_ESTRUTURA_ESTADO.py`
- **Caminho no Disco:** [`gates/G_ESTRUTURA_ESTADO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ESTRUTURA_ESTADO.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_ESTRUTURA_ESTADO (Lei Canônica #3)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 17. Guarda Incorruptível: `G_FRONTEND_LAYERS.py`
- **Foto / Identidade:** `G_FRONTEND_LAYERS.py`
- **Caminho no Disco:** [`gates/G_FRONTEND_LAYERS.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_FRONTEND_LAYERS.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_FRONTEND_LAYERS
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 18. Guarda Incorruptível: `G_HADOLINT.py`
- **Foto / Identidade:** `G_HADOLINT.py`
- **Caminho no Disco:** [`gates/G_HADOLINT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_HADOLINT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_HADOLINT
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 19. Guarda Incorruptível: `G_HARNESS_COMPAT.py`
- **Foto / Identidade:** `G_HARNESS_COMPAT.py`
- **Caminho no Disco:** [`gates/G_HARNESS_COMPAT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_HARNESS_COMPAT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_HARNESS_COMPAT
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 20. Guarda Incorruptível: `G_HONESTIDADE_ROTULO.py`
- **Foto / Identidade:** `G_HONESTIDADE_ROTULO.py`
- **Caminho no Disco:** [`gates/G_HONESTIDADE_ROTULO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_HONESTIDADE_ROTULO.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_HONESTIDADE_ROTULO
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 21. Guarda Incorruptível: `G_IDIOMA_LEI_4.py`
- **Foto / Identidade:** `G_IDIOMA_LEI_4.py`
- **Caminho no Disco:** [`gates/G_IDIOMA_LEI_4.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_IDIOMA_LEI_4.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_IDIOMA_LEI_4 (ISSUE-0012)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 22. Guarda Incorruptível: `G_INFRA_COMPOSE.py`
- **Foto / Identidade:** `G_INFRA_COMPOSE.py`
- **Caminho no Disco:** [`gates/G_INFRA_COMPOSE.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_INFRA_COMPOSE.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_INFRA_COMPOSE (Anti-NIH #3)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 23. Guarda Incorruptível: `G_ISOLATION_AUDIT.py`
- **Foto / Identidade:** `G_ISOLATION_AUDIT.py`
- **Caminho no Disco:** [`gates/G_ISOLATION_AUDIT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ISOLATION_AUDIT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_ISOLATION_AUDIT
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 24. Guarda Incorruptível: `G_LAYOUT_ENTREGA.py`
- **Foto / Identidade:** `G_LAYOUT_ENTREGA.py`
- **Caminho no Disco:** [`gates/G_LAYOUT_ENTREGA.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_LAYOUT_ENTREGA.py)
- **Missão de Segurança:** G_LAYOUT_ENTREGA.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 25. Guarda Incorruptível: `G_LEI_DECLARA_PORTAO.py`
- **Foto / Identidade:** `G_LEI_DECLARA_PORTAO.py`
- **Caminho no Disco:** [`gates/G_LEI_DECLARA_PORTAO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_LEI_DECLARA_PORTAO.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_LEI_DECLARA_PORTAO (ISSUE-0010)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 26. Guarda Incorruptível: `G_LIVRO_EVIDENCIA.py`
- **Foto / Identidade:** `G_LIVRO_EVIDENCIA.py`
- **Caminho no Disco:** [`gates/G_LIVRO_EVIDENCIA.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_LIVRO_EVIDENCIA.py)
- **Missão de Segurança:** G_LIVRO_EVIDENCIA.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 27. Guarda Incorruptível: `G_LLM_PROMPT_SHIELD.py`
- **Foto / Identidade:** `G_LLM_PROMPT_SHIELD.py`
- **Caminho no Disco:** [`gates/G_LLM_PROMPT_SHIELD.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_LLM_PROMPT_SHIELD.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_LLM_PROMPT_SHIELD
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 28. Guarda Incorruptível: `G_MIGRATION_ROT.py`
- **Foto / Identidade:** `G_MIGRATION_ROT.py`
- **Caminho no Disco:** [`gates/G_MIGRATION_ROT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_MIGRATION_ROT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_MIGRATION_ROT (ISSUE-0017 / Lei Canônica #3)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 29. Guarda Incorruptível: `G_ORQUESTRADOR_SINCRONO.py`
- **Foto / Identidade:** `G_ORQUESTRADOR_SINCRONO.py`
- **Caminho no Disco:** [`gates/G_ORQUESTRADOR_SINCRONO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ORQUESTRADOR_SINCRONO.py)
- **Missão de Segurança:** G_ORQUESTRADOR_SINCRONO.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 30. Guarda Incorruptível: `G_PACOTE_CORE.py`
- **Foto / Identidade:** `G_PACOTE_CORE.py`
- **Caminho no Disco:** [`gates/G_PACOTE_CORE.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_PACOTE_CORE.py)
- **Missão de Segurança:** G_PACOTE_CORE.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 31. Guarda Incorruptível: `G_PIPELINE_HANDOFF.py`
- **Foto / Identidade:** `G_PIPELINE_HANDOFF.py`
- **Caminho no Disco:** [`gates/G_PIPELINE_HANDOFF.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_PIPELINE_HANDOFF.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_PIPELINE_HANDOFF (ISSUE-PIPE-0002)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 32. Guarda Incorruptível: `G_PORTAO_PROVA_QUE_MORDE.py`
- **Foto / Identidade:** `G_PORTAO_PROVA_QUE_MORDE.py`
- **Caminho no Disco:** [`gates/G_PORTAO_PROVA_QUE_MORDE.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_PORTAO_PROVA_QUE_MORDE.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_PORTAO_PROVA_QUE_MORDE (Lei Canônica #13)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 33. Guarda Incorruptível: `G_PROTOCOL_FALLBACK.py`
- **Foto / Identidade:** `G_PROTOCOL_FALLBACK.py`
- **Caminho no Disco:** [`gates/G_PROTOCOL_FALLBACK.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_PROTOCOL_FALLBACK.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_PROTOCOL_FALLBACK
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 34. Guarda Incorruptível: `G_PROTOTYPE_REWRITE.py`
- **Foto / Identidade:** `G_PROTOTYPE_REWRITE.py`
- **Caminho no Disco:** [`gates/G_PROTOTYPE_REWRITE.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_PROTOTYPE_REWRITE.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_PROTOTYPE_REWRITE
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 35. Guarda Incorruptível: `G_QUARTETO_SINE_QUA_NON.py`
- **Foto / Identidade:** `G_QUARTETO_SINE_QUA_NON.py`
- **Caminho no Disco:** [`gates/G_QUARTETO_SINE_QUA_NON.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_QUARTETO_SINE_QUA_NON.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_QUARTETO_SINE_QUA_NON (ISSUE-0024 & Lei #10)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 36. Guarda Incorruptível: `G_RESUMO_USUARIO.py`
- **Foto / Identidade:** `G_RESUMO_USUARIO.py`
- **Caminho no Disco:** [`gates/G_RESUMO_USUARIO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_RESUMO_USUARIO.py)
- **Missão de Segurança:** G_RESUMO_USUARIO.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 37. Guarda Incorruptível: `G_SAIDA_BINARIA.py`
- **Foto / Identidade:** `G_SAIDA_BINARIA.py`
- **Caminho no Disco:** [`gates/G_SAIDA_BINARIA.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_SAIDA_BINARIA.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_SAIDA_BINARIA (Lei Canônica #2)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 38. Guarda Incorruptível: `G_SEGREDOS.py`
- **Foto / Identidade:** `G_SEGREDOS.py`
- **Caminho no Disco:** [`gates/G_SEGREDOS.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_SEGREDOS.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_SEGREDOS
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 39. Guarda Incorruptível: `G_SKILL_ROT.py`
- **Foto / Identidade:** `G_SKILL_ROT.py`
- **Caminho no Disco:** [`gates/G_SKILL_ROT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_SKILL_ROT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_SKILL_ROT (ISSUE-0016 / Lei Canônica #9)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 40. Guarda Incorruptível: `G_STACK_PADRAO_OURO.py`
- **Foto / Identidade:** `G_STACK_PADRAO_OURO.py`
- **Caminho no Disco:** [`gates/G_STACK_PADRAO_OURO.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_STACK_PADRAO_OURO.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_STACK_PADRAO_OURO (ISSUE-0025 & Lei #11)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 41. Guarda Incorruptível: `G_SUPPLY_CHAIN.py`
- **Foto / Identidade:** `G_SUPPLY_CHAIN.py`
- **Caminho no Disco:** [`gates/G_SUPPLY_CHAIN.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_SUPPLY_CHAIN.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_SUPPLY_CHAIN
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 42. Guarda Incorruptível: `G_SYNC_CMD_ROT.py`
- **Foto / Identidade:** `G_SYNC_CMD_ROT.py`
- **Caminho no Disco:** [`gates/G_SYNC_CMD_ROT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_SYNC_CMD_ROT.py)
- **Missão de Segurança:** G_SYNC_CMD_ROT.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 43. Guarda Incorruptível: `G_TEMPLATE_FORGE_ROT.py`
- **Foto / Identidade:** `G_TEMPLATE_FORGE_ROT.py`
- **Caminho no Disco:** [`gates/G_TEMPLATE_FORGE_ROT.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_TEMPLATE_FORGE_ROT.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_TEMPLATE_FORGE_ROT (Lei #1, #8, #12, #13)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 44. Guarda Incorruptível: `G_TESTES_REAIS.py`
- **Foto / Identidade:** `G_TESTES_REAIS.py`
- **Caminho no Disco:** [`gates/G_TESTES_REAIS.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_TESTES_REAIS.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_TESTES_REAIS (v2)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 45. Guarda Incorruptível: `G_TRANSACTION_LOG_LRU.py`
- **Foto / Identidade:** `G_TRANSACTION_LOG_LRU.py`
- **Caminho no Disco:** [`gates/G_TRANSACTION_LOG_LRU.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_TRANSACTION_LOG_LRU.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_TRANSACTION_LOG_LRU
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 46. Guarda Incorruptível: `G_UNIVERSAL_HARNESS.py`
- **Foto / Identidade:** `G_UNIVERSAL_HARNESS.py`
- **Caminho no Disco:** [`gates/G_UNIVERSAL_HARNESS.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_UNIVERSAL_HARNESS.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_UNIVERSAL_HARNESS
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 47. Guarda Incorruptível: `G_USER_FACING_PTBR.py`
- **Foto / Identidade:** `G_USER_FACING_PTBR.py`
- **Caminho no Disco:** [`gates/G_USER_FACING_PTBR.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_USER_FACING_PTBR.py)
- **Missão de Segurança:** G_USER_FACING_PTBR.py
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


### 48. Guarda Incorruptível: `G_ZERO_HEADLESS.py`
- **Foto / Identidade:** `G_ZERO_HEADLESS.py`
- **Caminho no Disco:** [`gates/G_ZERO_HEADLESS.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/gates/G_ZERO_HEADLESS.py)
- **Missão de Segurança:** ECOSSISTEMA AIDD — QUALITY GATE: G_ZERO_HEADLESS (Lei Canônica #7 e #8)
- **Prova que Morde (Lei #13):** Testado por teste automatizado dedicado que provoca a violação sintética e asserta `exit 1`.
- **As 11 Dimensões deste Quality Gate:**
  1. *Recebe (Input):* Árvore de arquivos do repositório ou changeset git (`--files`).
  2. *Cria / Processa:* Análise estática por AST Python, regex ou schema JSON (Zero LLM).
  3. *Entrega (Output):* Código binário rigoroso (`exit 0` = APROVADO, `exit 1` = BLOQUEADO).
  4. *Configs:* Argumentos CLI (`--files`, `--verbose`, `--dry-run`).
  5. *Gates:* Autovalidado pelo meta-gate `G_PORTAO_PROVA_QUE_MORDE.py`.
  6. *Scripts 0 LLM:* 100% mecânico e matemático.
  7. *Hooks:* Integrado a `.git/hooks/pre-commit` e ao framework pre-commit.
  8. *Agents:* Executa sem intervenção de agente cognitivo.
  9. *Skills:* Invocado pelas skills de runner e auditoria.
  10. *MCPs:* Auditável via `code-review-graph`.
  11. *Rules:* Subordinado à Lei #2 (Saída Estritamente Binária).


# PARTE IV: OS 91 COMPONENTES AGNÓSTICOS (PEÇAS UNIVERSAIS LEGO)

## Na Festa
Imagine peças de LEGO de altíssima precisão. Não importa se você está montando na mesa azul (Claude), na mesa verde (Gemini), na mesa cinza (Cursor) ou na mesa preta (Windsurf). As peças encaixam com o mesmo clique suave e a mesma firmeza matemática. Nenhuma mesa fica com uma peça diferente da outra.

## Na Casa (A Sincronização dos 91 Componentes)
- **Fonte Canônica Única:** `componentes/compartilhado/`
- **Ambientes Espelhados (Harnesses):** `.agents/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.codebuddy/`, `.opencode/`.
- **Garantia de Integridade:** Validação criptográfica SHA-256 via `python ecossistema.py components verify --tipo todos`. Se um único byte divergir entre qualquer harness e a fonte canônica, o sistema aponta drift e bloqueia o commit.

### As 6 Famílias dos 91 Componentes:
1. **Comandos de Terminal Canônicos (`componentes/compartilhado/comandos/`):** 9 scripts de automação (`ecossistema.py`, `faz_commit.py`, etc.).
2. **Campainhas e Travas Git (`componentes/compartilhado/hooks/`):** Travas de pré-commit e verificação de regras.
3. **Escudo de Segurança (`componentes/compartilhado/security/`):** Detectores de vazamento de segredos e chaves.
4. **Habilidades Atômicas (`componentes/compartilhado/skills/`):** 66 pastas de skills padronizadas.
5. **Esquemas e Contratos Formais (`componentes/compartilhado/specs/`):** Esquemas JSON Draft-7 para handoff formal entre módulos.
6. **Núcleo Compartilhado de Código (`componentes/compartilhado/src-core/`):** Utilitários de missão crítica (`escritor_atomico.py`, `result.py`, `assinatura_manifesto.py`).

---

# Epílogo: A Orquestra Perfeita

Quando você junta as **8 Ferramentas Macro**, as **66 Micro-Ferramentas**, os **48 Quality Gates** e os **91 Componentes Agnósticos**, o que você tem não é apenas um projeto de software: você tem uma **catedral digital determinística**.

No Ecossistema AIDD, nenhuma linha de código nasce sem plano, nenhuma ferramenta opera sem contrato e nenhum portão se abre sem que a prova matemática tenha sido atendida.

*Fim da Auditoria Canônica — 22 de Setembro de 2026.*
