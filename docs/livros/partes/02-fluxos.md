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

