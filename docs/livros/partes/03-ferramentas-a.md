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
