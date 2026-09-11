# ARQUITETURA-BASELINE-DDD-CLEAN.md

> **Data:** 2026-09-09
> **Status:** ✅ PLANO FORMALIZADO — `docs/planos/a-fazer/01-reestruturacao-ddd-clean-architecture/`
> **Tags:** #plano-gerado #clean-architecture #ddd #engine #deliverables
> **Método:** inspeção estática de código real (AST/leitura direta), contagens medidas (`wc -l`), diff real entre cópias, cruzamento com `docs/planos/fazendo/codigo-limpo-profundo-ecossistema/` e `AGENTS.md`.
> **Dimensão 1 (Engine):** como as ferramentas e a orquestração são construídas.
> **Dimensão 2 (Deliverables):** a arquitetura do código/templates que cada ferramenta **entrega** ao usuário final.
> **Escala:** 1 = ausente/anti-padrão dominante · 3 = funcional com violações conhecidas · 5 = referência de mercado.

---

## 1. Executive Scorecard

| Tool | Engine Clean Arch | Engine DDD | Deliverable Clean Arch | Deliverable DDD |
|:---|:---:|:---:|:---:|:---:|
| Orquestração (`ecossistema.py` + `gates/` + `componentes/`) | **4** | **3** | **3** | **3** |
| AIDD Forge | **4** | **3** | **3** | **2** |
| AIDD Generator | **3** | **2** | **2** | **2** |
| AIDD Master | **3** | **2** | **2** | **2** |
| AIDD Enterprise | **3** | **2** | **2** | **2** |
| AIDD Ops | **4** | **3** | **3** | **3** |

**Leitura executiva:** o ecossistema é forte onde é determinístico (gates, sizing, sync de componentes, Result/erro explícito) e fraco exatamente onde entrega código de domínio: os deliverables de Master/Enterprise são *transaction scripts* sobre SQL cru — sem Entities, Value Objects, Aggregates, Domain Events de domínio ou Repositories. A duplicação de 27 arquivos (8.781 linhas) entre `master/src/core` e `enterprise/src/core` é a maior dívida de Clean Arch do engine, já mapeada em plano pendente.

---

## 2. Engine Architecture Findings (por ferramenta)

### 2.1 Orquestração (`ecossistema.py`, `gates/`, `componentes/`)

**Positivos**
- `ecossistema.py` (603 linhas) é roteador puro: CLI click → `subprocess.run` com `PYTHONPATH` isolado por ferramenta (`cmd_forge`, `cmd_generate`, `cmd_master`, `cmd_enterprise`, `cmd_ops`). Zero lógica de negócio no roteador — front correta entre *interface adapter* e *orchestration*.
- `gates/` é determinismo puro: AST para consistência de help (`G_CLI_HELP_CONSISTENCIA`), AST para honestidade de rótulo (`G_HONESTIDADE_ROTULO`), delegação a detect-secrets/Checkov/Hadolint em vez de reimplementar (Anti-NIH #4/8 cumprido). Exit 0/1 binário — Qualidade Binária respeitada.
- `componentes/` como fonte física única + `components sync|verify` é um *Shared Kernel* formalizado via `gates/manifesto_harnesses.json` — o único Context Map formal do repositório.

**Violações / riscos**
- **[E-1] Context Map implícito entre ferramentas:** a integração `ops → master/enterprise` (sizing → Helm) existe apenas como elo comprovado nº1; não há contrato versionado (schema) entre o `PLANO-INFRAESTRUTURA.json` do ops e o `scaffold_infra.py`. Acoplamento por convenção, não por contrato.
- **[E-2] `G_HONESTIDADE_ROTULO` documenta violação real em aberto** (rótulos "blindagem militar" em gates de master/enterprise sem cobertura auditável) — a linguagem ubíqua de governança é violada pelos próprios artefatos de governança. Pendência humana rastreada.
- **[E-3] Orquestração por subprocess + paths relativos:** frágil a renomeação de diretórios, sem modelo de domínio do "ecossistema" (Ferramenta, Comando, Contrato) — é scriptagem, não design.

### 2.2 AIDD Forge

**Positivos**
- Pacote real (`aidd_forge/`) com separação limpa: `cli.py` (click, 133 linhas) → `commands/slash_router` → `core/*` (detector, injector, materializador, phase_fencer, subagent_purger, token_optimizer, harness_sync — ~1.7k linhas no total). Melhor relação tamanho/coesão do repositório.
- Testes unitários + integração (`tests/unit/`, `tests/integration/test_full_forge_pipeline.py`) — o único tool com teste de pipeline ponta a ponta do engine.
- `Injector`/`UniversalInjector` são Ports claros: entrada `TEMPLATES_ROOT` + target, saída estruturada (`created`/`skipped`/`overwritten`).

**Violações**
- **[F-1] Deliverable de governança sem verificação de semântica:** o forge entrega gates (ex.: `G_CYBERSECURITY_OWASP.py`) que checam padrões textuais/estruturais; o rótulo do deliverable sugere cobertura maior que a real — mesmo problema de honestidade de rótulo do ecossistema, herdado pelo projeto-alvo.
- **[F-2] `IDE_RULE_ALIASES` e caminhos de harness hardcoded no CLI** — a linguagem ubíqua de harnesses existe no manifesto do ecossistema mas não é reutilizada aqui (conhecimento duplicado).

### 2.3 AIDD Generator

**Positivos**
- `_FASE_REGISTRY` centralizado (fase → alias/script/micro-ambiente) — tabela de decisão explícita, fácil de auditar.
- Política "sem fallback silencioso" (`_falhar` para o pipeline e reporta fase/ causa) — falha explícita como valor de domínio.
- `preflight_llm` verifica credencial antes de gastar tokens.

**Violações**
- **[G-1] Manipulação de `sys.path` + `importlib` dinâmico** (`sys.path.insert` em 2 pontos, `spec_from_file_location`) para carregar fases — fuga do sistema de pacotes, dificulta tipagem/teste das fases e cria ordem implícita de import. Anti-padrão de engine.
- **[G-2] Dois orquestradores paralelos:** `pipeline_completo.py` (393 linhas) e `pipeline_prefect.py` (344 linhas) modelam o mesmo fluxo 1→8; `web/pipeline_runner.py` é um terceiro caminho de execução. Sem fonte única da verdade do pipeline — divergência silenciosa esperada (mesmo padrão do achado #1 entre master/enterprise).
- **[G-3] `web/` (328+320+289+264 linhas) mistura transporte HTTP, parsing de status e configuração no mesmo nível** — sem camada de aplicação explícita entre UI e pipeline.

### 2.4 AIDD Master

**Positivos**
- `src/core/` contém padrões reais e corretos: `ReadModelCache` com Stale-While-Revalidate (`cqrs.py`), `CRDTSet` grow-only (`local_first.py`), Outbox transacional + WORM audit hash chain (usados em `modulo1/services.py`), `DatabaseAdapter` ABC com factory SQLite/Postgres/Supabase (`database_adapter.py`), `CircuitBreaker`, `Result`.
- Gates próprios (`scripts/gates/G_ARQUITETURA.py`, `G_ESTRUTURA.py`, `G_CONTRACTS.py`...) aplicam estrutura por AST.

**Violações**
- **[M-1] `scripts/aidd.py` = monolito de 1.162 linhas** misturando parsing de argumentos, orquestração, I/O de arquivos e mensagens — a fronteira CLI ↔ orquestração de negócio pedida no critério 2 não existe no ponto de entrada principal.
- **[M-2] Duplicação de núcleo:** 27 arquivos byte-idênticos + 8.781 linhas compartilhados com Enterprise; 3 divergências silenciosas já confirmadas (`mcp_server.register_injected_tools`, `intent_router` hook/gancho, formato de hook bash vs JSON no `materializador`). `G_DRIFT_NUCLEO_COMPARTHIDO` só **detecta**, não previne. (Plano Item 1 pendente.)
- **[M-3] `src/core` é biblioteca de runtime do projeto gerado, não do engine** — mesmo pacote serve a dois papéis (engine interno e runtime do deliverable), acoplando a evolução do framework à do produto gerado.

### 2.5 AIDD Enterprise

- Herda **integralmente** os achados [M-1]–[M-3] (mesmos `scripts/aidd.py`, mesmos 27 arquivos, mesmos gates).
- **[N-1] Positivo diferencial:** pipeline de injeção com verificação SHA-256 (`scripts/injector/`, `scaffold_infra.py`) — integridade de componente é o único mecanismo de *supply chain* formal do ecossistema.
- **[N-2]** Divergência silenciosa nº1 afeta diretamente o deliverable: `register_injected_tools()` existe só no master — o enterprise **não carrega ferramentas MCP injetadas**, ou seja, as duas "gêmeas" têm comportamento de runtime diferente com código supostamente igual.

### 2.6 AIDD Ops

**Positivos**
- Melhor Clean Arch do ecossistema em proporção: `src/core/result.py` (`Result.ok/fail`), fases puras e determinísticas (`03_sizing.py`: "100% determinístico — zero LLM, aritmética pura"), separação `scripts/phases/` ↔ `src/core/` (cofre_credenciais, ssh_runner, coolify, uptime_kuma, preflight).
- Linguagem ubíqua PT-BR consistente e coerente com a regra §4.1: `dimensionar`, `bancos_logicos`, `ferramentas_com_banco`, `FERRAMENTAS_VAZIAS` — domínio legível.

**Violações**
- **[O-1] Fases carregam dados por path relativo calculado à mão** (`os.path.join(__file__, "..", "..", "data")`) — sem camada de repositório/config; aceitável no MVP, frágil na evolução.
- **[O-2] `pipeline_ops.py` (789 linhas) e `pipeline_ops_deploy.py` (352) repetem lógica de orquestração** em vez de compor fases.

### Restrição transversal: Standalone Constraint ✅

Varredura de imports em `tools/*/src`, `tools/*/scripts`, `tools/*/aidd_forge`: **nenhuma importação runtime cruzada entre tools**. Os hits de grep são autorreferências (defaults `alvo_projeto="aidd-master"`) e comentários ("mesmo padrão do aidd-forge"). A única dependência inter-tool é o elo documentado ops → master/enterprise **via artefato JSON** (dados, não código) — conforme a regra #6, isso é composição legítima por contrato de dados, mas falta schema versionado compartilhado (ver [E-1]).

---

## 3. Deliverables & Templates Architecture Findings (por ferramenta)

### 3.1 Orquestração — Deliverables: governança multi-harness

- **Positivo:** contratos formais (`manifesto_harnesses.json`, `dependencias_externas.json`, `termos_proibidos_marketing.json`) são Value Objects de fato — imutáveis, comparáveis, versionados por gate.
- **[D-1]** Destinos gerados (`.claude/`, `.agents/`, `.opencode/`, `.mimocode/`...) são espelhos mecânicos — correto — mas o *contrato* de um componente (o que o torna válido) vive espalhado entre o manifesto e os gates, não em um schema único.

### 3.2 AIDD Forge — Deliverables: bootstrap de governança

- Entrega AGENTS.md, gates de segredos/OWASP/estrutura, hooks git, fases. **DDD: parcialmente não aplicável** (não há domínio de negócio), mas o deliverable é avaliável como contrato: os gates entregues impõem *estrutura*, não *invariantes de domínio* — nota 2 em DDD reflete que nenhum conceito de domínio é modelado.

### 3.3 AIDD Generator — Deliverables: sistemas greenfield

- **[DG-1] Arquitetura do deliverable não é verificável estaticamente:** o código final é produzido pela Fase 8 via LLM com loop de teste/correção; não existe template estrutural rígido (ao contrário de Master/Enterprise). Consequência: qualidade de camadas do produto gerado varia por execução e depende do micro-ambiente AGENTS.md da fase — governança por prompt, não por código.
- **[DG-2]** `verificar_gates.py` existe, mas os gates do ecossistema não auditam o *código gerado* (auditam o repositório do ecossistema). O deliverable vive fora do perímetro dos Quality Gates — a promessa "testado" depende só da fase 8.
- **[DG-3]** `output-clinica/` (único artefato versionado) contém só `.aidd/cache/data/*.json` — evidência de que os produtos gerados não são tratados como cidadãos de primeira classe no repositório.

### 3.4 AIDD Master — Deliverables: fatias verticais `src/modules/<modulo>/`

Auditado o slice canônico `modulo1` (models/services/routes) — é o molde de **toda** fatia gerada:

- **[DM-1] Anemic Domain Model confirmado:** `models.py` é DDL SQLite + seed (`CREATE TABLE mod_modulo1...`) — não há Entity, Value Object, Aggregate, invariantes ou comportamento. O "modelo de domínio" é `dict(row)` retornado do banco. Regras de negócio se resumem a `titulo.strip() or raise`.
- **[DM-2] SQL cru dentro do Service (fuga de camada):** `services.py` constrói strings SQL (`query += " AND status = ?"`) direto sobre a conexão — sem Repository, sem abstração de persistência. Parâmetros são bound (sem injeção), mas a camada de aplicação conhece o esquema físico, a sintaxe do SQLite e a paginação — violação direta da Dependency Rule (Frameworks/DB dentro da lógica de negócio).
- **[DM-3] Route handler com lógica de infra:** `routes.py` manipula parsing de query params, chaves de cache (`read_model.invalidate_prefix("modulo1_")`) e tradução de exceção para JSON — a fronteira Interface Adapter contém política de cache e tratamento de erro de domínio.
- **[DM-4] Bounded Context = pasta:** `src/modules/modulo1/` é arbitrário; não há Context Map, linguagem ubíqua por contexto, nem Domain Events de domínio (os eventos são strings de infra: `"modulo1_criado"` via outbox — mecanismo correto, semântica de infra).
- **Positivos que valem registro:** outbox transacional na mesma transação da mutação, audit log WORM encadeado por SHA-256, CQRS de leitura com invalidação por prefixo — mecanismos maduros aplicados a um domínio anêmico.

### 3.5 AIDD Enterprise — Deliverables: componentes regulados + scaffolding

- **[DE-1]** `templates/core/` e `templates/v2/` + `cookiecutter-scaffold/` reproduzem o mesmo molde models/services/routes do Master — herda [DM-1]–[DM-4] na íntegra, com agravante: o deliverable é rotulado "missão crítica/zero-trust", e a camada de domínio continua sendo um CRUD sobre dicts.
- **[DE-2] Positivo:** SHA-256 por componente injetado dá integridade verificável — melhor prática de supply chain que nenhum outro tool tem.
- **[DE-3]** Duplicação tripla do mesmo template (`core/`, `v2/`, `cookiecutter/`) sem fonte única — o mesmo problema do Item 1, agora em templates (Item 3 do plano pendente).

### 3.6 AIDD Ops — Deliverables: infraestrutura declarativa

- **Positivo:** compose/Helm gerados a partir de sizing determinístico (`requisitos_recursos.json` → spec de VPS → resources do Helm); validados por `G_INFRA_COMPOSE` (Checkov + PyYAML) e `G_HADOLINT` — os únicos deliverables do ecossistema auditados por gate real.
- **[DO-1]** Sem teste de integração que valide o Helm gerado contra um cluster (lint apenas) — rótulo "deployável" hoje se apoia em lint, não em apply testado.

### Restrição transversal: Zero Stubs ✅ / Anti-NIH ⚠️

- **Zero Stubs:** pipelines falham explicitamente (generator: "nunca segue adiante com dado fabricado"); slices geram seed determinístico + testes; `G_TESTES_REAIS` roda pytest real por tool. Conforme a regra #5.
- **Anti-NIH:** cadastro formal de 26 casos (`docs/features/08-09-2026_feature-oportunidades-reaproveitamento-nih.md`) e delegação real (detect-secrets, Checkov, Hadolint, cookiecutter, Prefect). Ponto de atenção: `ReadModelCache` e `CRDTSet` em `src/core` reimplementam mecanismos com OSS maduro (dogpile/redis, automerge/yjs) — candidatos a item no cadastro NIH.

---

## 4. Canonical Architecture Blueprint

### 4.1 Blueprint do ENGINE interno (por tool)

```
tools/<ferramenta>/
├── cli.py                     # Adapter de entrada: parsing + help. ZERO lógica (≤300 linhas)
├── application/               # Use Cases / orquestração de comandos (portas de entrada)
│   ├── commands/              # 1 arquivo por comando (init, inject, add-module, pipeline)
│   └── ports/                 # Interfaces (Protocol/ABC): LLMRunner, FileSystem, HarnessRegistry
├── domain/                    # Modelo do PRÓPRIO engine (Fase, Componente, Gate, Contrato, Result)
│   ├── entities/              # Aggregates do engine (ex.: Componente{hash, destinos, tipo})
│   └── policies/              # Invariantes (o que torna um componente/phase válido)
├── infrastructure/            # Adapters: subprocess, importlib, http, git, fs
├── core/                      # (transição) núcleo compartilhado — ver 4.3
├── templates/                 # Deliverables declarativos (cookiecutter/jinja), fonte única
└── tests/{unit,integration}/
```

**Contratos de camada (engine):**
1. `cli` → `application`: chama Use Case com DTO simples; nunca importa `infrastructure`.
2. `application` → `domain`: executa políticas; recebe adapters **via injeção** (ports).
3. `infrastructure` implementa `ports/`; dependência sempre aponta para dentro.
4. Erros: `Result` (padrão já existente em ops — generalizar para os 5).
5. Uma única fonte de orquestração por pipeline (elimina pares `pipeline_completo`/`pipeline_prefect`, `pipeline_ops`/`_deploy`).

### 4.2 Blueprint do DELIVERABLE (projeto/módulo gerado)

```
<projeto-gerado>/
├── src/
│   ├── modules/<contexto>/            # 1 Bounded Context = 1 módulo (nome PT-BR, regra §4.1)
│   │   ├── domain/
│   │   │   ├── entities.py            # Aggregate Root com invariantes (ex.: Item.criar() valida)
│   │   │   ├── value_objects.py       # Status, Titulo — imutáveis, auto-validados
│   │   │   ├── events.py              # Eventos de DOMÍNIO (ItemCriado), não strings de infra
│   │   │   └── repositories.py        # Porta: Protocol ItemRepository
│   │   ├── application/
│   │   │   ├── use_cases.py           # CriarItem, ListarItens (orquestra domain + ports)
│   │   │   └── dtos.py                # Entrada/saída de use case (sem dict cru)
│   │   ├── infrastructure/
│   │   │   ├── sqlite_repository.py   # Adapter: SQL vive AQUI (e só aqui)
│   │   │   └── outbox.py              # Outbox transacional (já existe em core)
│   │   └── interfaces/
│   │       └── routes.py              # Apenas transporte; chama use case
│   ├── shared/                        # (já existe) ui, utils, events
│   └── core/                          # runtime compartilhado — ver 4.3
└── tests/modules/<contexto>/{unit,integration}/
```

**Contratos de camada (deliverable):**
1. `domain` não importa nada de fora do próprio pacote (nenhum sqlite, nenhum http, nenhum `core.*`).
2. `application` depende de `domain` + `ports` (repositories definidos no domain).
3. `infrastructure` é o único lugar com SQL/DDL; `models.py` (DDL+seed) migra para `infrastructure/schema.py`.
4. `interfaces/routes` não conhece cache nem banco; invalidação de read-model vira efeito colateral do use case via Domain Event.
5. Gate novo `G_ARQUITETURA_DELIVERABLE` (AST): proíbe `import sqlite3`/`execute(` fora de `infrastructure/`, e `routes.py` importando adapter — torna os critérios acima binários.

### 4.3 Núcleo compartilhado (resolve [M-2]/[N-2]/[DE-3])

```
componentes/compartilhado/src-core/   # "almoxarifado" — fonte ÚNICA (decisão já registrada no Item 1)
└── 27 arquivos hoje duplicados + divergências resolvidas por decisão explícita
gates/G_DRIFT_NUCLEO_COMPARTILHADO.py  # passa a VERIFICAR sync (não só detectar)
```

---

## 5. Integrated Action Plan (Phased Roadmap)

### Fase 0 — Decisões e segurança (sem refatoração) — *1 semana*
| # | Ação | Resolve | Critério de pronto |
|:--|:--|:--|:--|
| 0.1 | Fechar Item 1 do plano `codigo-limpo-profundo`: extrair `componentes/compartilhado/src-core/` com sync mecânico; resolver as 3 divergências conforme decisão registrada (hook → JSON) | [M-2], [N-2] | MD5 diff = 0 divergência não documentada; pytest verde nas 2 tools; G_DRIFT verde |
| 0.2 | Corrigir rótulos dos gates de master/enterprise (item `07-corrigir-gate-de-seguranca...` pendente) | [E-2], [F-1] | `G_HONESTIDADE_ROTULO` verde em `audit` |
| 0.3 | Congelar `pipeline_prefect.py` (deprecar) ou torná-lo o único — eliminar o par | [G-2] | 1 orquestrador por pipeline; testes do sobrevivente verdes |

### Fase 1 — Engine Clean Arch — *2–3 semanas*
| # | Ação | Resolve |
|:--|:--|:--|
| 1.1 | Extrair `cli.py` fino de `scripts/aidd.py` (master/enterprise): parsing fica no CLI, orquestração vai para `application/` | [M-1] |
| 1.2 | Remover `sys.path` hacks do generator: transformar fases em pacote importável (`generator/phases/`) mantendo carregamento lazy | [G-1] |
| 1.3 | Definir schema versionado do contrato ops→master/enterprise (`PLANO-INFRAESTRUTURA.schema.json`) + gate que valida a interface | [E-1] |
| 1.4 | Unificar templates `core/`/`v2/`/`cookiecutter/` com fonte única + sync mecânico (Item 3 do plano pendente) | [DE-3] |
| 1.5 | Generalizar `Result` (ops) para os 5 engines como contrato único de erro explícito | [G-3], [M-1] |

### Fase 2 — Deliverable DDD (molde da fatia vertical) — *3–4 semanas*
| # | Ação | Resolve |
|:--|:--|:--|
| 2.1 | Reescrever o molde `modulo1` uma única vez como referência: `domain/` (Entity com invariantes + VOs + eventos), `application/use_cases`, `infrastructure/sqlite_repository` (SQL migra para cá), `interfaces/routes` fino | [DM-1]–[DM-4] |
| 2.2 | Atualizar geradores (add_module/cookiecutter) para emitir o novo molde; slice legado marcado deprecated por release | [DM-1]–[DM-4] |
| 2.3 | Criar gate `G_ARQUITETURA_DELIVERABLE` (AST): SQL só em `infrastructure/`; routes sem `execute(`/cache; domain sem imports externos. Aplicar a deliverables e templates | Trava regressão |
| 2.4 | Eventos de domínio tipados (`ItemCriado`) substituindo strings de outbox; outbox permanece como transporte | [DM-4] |

### Fase 3 — Deliverable do Generator + Ops — *2–3 semanas*
| # | Ação | Resolve |
|:--|:--|:--|
| 3.1 | Fase 8 do generator passa a emitir contra o blueprint 4.2 (micro-ambiente `phase_08` atualizado + validação AST pós-geração com o gate 2.3) | [DG-1] |
| 3.2 | Trazer o código gerado para dentro do perímetro de gates: job que roda `G_ARQUITETURA_DELIVERABLE` + pytest no `output/` antes de declarar sucesso da fase 7/8 | [DG-2] |
| 3.3 | Ops: teste de integração opcional (flag) que aplica o Helm em cluster de teste (kind) — rótulo "deployável" passa a ter cobertura real | [DO-1] |

### Fase 4 — Consolidação — *contínua*
- Avaliar OSS para `ReadModelCache`/`CRDTSet` no cadastro NIH (regra #8).
- Context Map formal do ecossistema em `docs/` (Shared Kernel = src-core; Customer-Supplier = ops→master/enterprise; ACL = injeção SHA-256 enterprise).
- Re-executar esta auditoria como gate comparativo (scorecard vira baseline versionado).

---

## Evidências primárias (rastreabilidade)

| Achado | Evidência |
|:--|:--|
| 27 arquivos duplicados / 8.781 linhas / 3 divergências | `docs/planos/fazendo/codigo-limpo-profundo-ecossistema/01-*.md` (MD5 real, §1.3 do relatório de auditoria) |
| SQL em service, modelo anêmico | `tools/aidd-master/src/modules/modulo1/{models,services,routes}.py` (leitura direta) |
| Monolito CLI | `wc -l tools/aidd-master/scripts/aidd.py` = 1.162 |
| sys.path hacks / dual pipeline | `tools/aidd-generator/scripts/pipeline_completo.py` L57-59, 89-115; `pipeline_prefect.py` (344 linhas) |
| Determinismo ops | `tools/aidd-ops/scripts/phases/03_sizing.py` (cabeçalho + `Result.ok/fail`) |
| Padões core corretos | `src/core/{cqrs,local_first,database_adapter}.py` (leitura direta) |
| Standalone constraint | grep de imports em `tools/*/src|scripts|aidd_forge` — 0 import cruzado |
| Honestidade de rótulo pendente | `AGENTS.md` §4 nota G_HONESTIDADE_ROTULO |
