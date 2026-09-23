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

Pense numa casa pré-fabricada que você comprou de outra construtora: por fora está
linda, mas a fiação e a fundação são proprietárias — só o técnico daquela construtora
mexe nelas, e você paga aluguel de manutenção para sempre. `aidd-bridge` é a equipe que
entra, refaz a fiação e a fundação com material aberto e padrão de mercado, **sem
tocar na decoração que você já gosta**. `aidd-bridge` resolve o aprisionamento por
fornecedor em aplicações geradas por
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

Se o `aidd-master` já instalou fechaduras normais em cada porta da casa, o
`aidd-enterprise` é o especialista que chega depois e troca todas por **fechadura de
cofre com selo de violação**: cada peça só entra se vier com certificado de origem
(a assinatura SHA-256), e um sensor continua verificando depois se alguém trocou a
fechadura escondido (a detecção de drift). `aidd-enterprise` é o `aidd-master` com uma
camada adicional de garantia: todo componente
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

Fechando a obra: a casa está construída, mobiliada e trancada — falta a concessionária
ligar água, luz e internet, e o síndico instalar câmeras que avisam se algo cair. É
isso que o `aidd-ops` faz pelo sistema: dimensiona o "tamanho do imóvel" (a VPS),
liga os serviços essenciais e mantém um vigia ligado 24 horas. `aidd-ops` transforma um
requisito em linguagem natural — *"uma clínica com agendamento
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
