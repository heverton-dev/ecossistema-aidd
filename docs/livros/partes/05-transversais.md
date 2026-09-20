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
`python ecossistema.py components sync`.

O repositório tem **60 habilidades** nessa pasta e **14 comandos** em
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

### Runners de fluxo

`aidd-pure` e `fluxo-01-runner`; `aidd-open` e `fluxo-02-runner`; `aidd-freedom` e
`fluxo-03-runner` (com operações atômicas da engine via `aidd-bridge-runner`). O par
existe porque uma habilidade é a dona do slash command e a outra é o motor que executa a esteira.

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

Há ainda o modo de reparo: `components sync --force` restaura destinos divergentes e
órfãos a partir da fonte, e `components verify` audita sem escrever.

## 19.5 Rastreabilidade

`componentes/compartilhado/skills/` (60 habilidades);
`componentes/compartilhado/comandos/` (14 comandos); `scripts/gestor_componentes.py`;
`ecossistema.py::cmd_components`; `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` §3 e §5.

# Capítulo 20 — O catálogo completo de portões

## 20.1 A distribuição dos 145 portões

O repositório tem 145 arquivos `G_*.py`. Eles se distribuem em quatro camadas:

| Camada                  | Onde                                   | Quantidade | Papel                                               |
| :---------------------- | :------------------------------------- | ---------: | :---------------------------------------------------- |
| Portões globais         | `gates/`                               |         24 | Auditam o ecossistema inteiro                        |
| Portões de ferramenta   | `tools/<ferramenta>/gates/` ou `scripts/gates/` | ~55 | Auditam a ferramenta e o que ela produz        |
| Portões-template        | `tools/aidd-forge/aidd_forge/templates/gates/` | 8 | São injetados nos projetos gerados               |
| Portões de projeto      | Projetos gerados                       |   variável | Cópias dos templates, ativas no projeto do usuário   |

A contagem de 145 inclui as cópias distribuídas — o número de portões **distintos** é
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

Os 39 portões globais podem ser lidos por intenção, e essa leitura revela a estratégia
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
| **Anti-rot por Lei** (fecham as Leis 1, 2, 3, 4, 9, 10, 11 — Sessões 12-24) | `G_DETERMINISMO_LEI_1`, `G_SAIDA_BINARIA`, `G_MIGRATION_ROT`, `G_ESTRUTURA_ESTADO`, `G_IDIOMA_LEI_4`, `G_ENV_ROT`, `G_SKILL_ROT`, `G_DISCIPLINA_TESTE_FERRAMENTA`, `G_CONTRACT_ROT`, `G_QUARTETO_SINE_QUA_NON`, `G_STACK_PADRAO_OURO` |

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

`gates/` (39 portões e suítes); `tools/*/gates/` e `tools/*/scripts/gates/`;
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
