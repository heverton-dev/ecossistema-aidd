# Arquitetura Técnica do Ecossistema AIDD

> **Versão:** 1.0  
> **Última atualização:** 2026-09-14  
> **Escopo:** Visão técnica completa do ecossistema — estrutura, camadas, fluxos e invariantes.

---

## 1. Visão Geral

O Ecossistema AIDD é um monorepo que implementa uma linha de produção de software com 6 ferramentas especializadas, 16 Quality Gates determinísticos e um CLI unificado. Cada ferramenta é autônoma (sem dependências de runtime entre si) e compartilha governança via AGENTS.md.

```
ecossistema-aidd/
├── ecossistema.py              ← CLI unificado (ponto de entrada)
├── AGENTS.md                   ← Lei Fundamental (governança canônica)
├── gates/                      ← 16 Quality Gates determinísticos
├── componentes/                ← Fonte única de componentes compartilhados
│   ├── compartilhado/          ← Núcleo core + skills universais
│   └── aidd-master/            ← Componentes do Master
├── tools/                      ← As 6 ferramentas (cada uma autônoma)
│   ├── aidd-forge/
│   ├── aidd-generator/
│   ├── aidd-master/
│   ├── aidd-enterprise/
│   ├── aidd-ops/
│   └── aidd-bridge/
├── core/                       ← Módulos cibernéticos (Ledger, Slicer, Router)
└── docs/                       ← Documentação técnica e planos
```

---

## 2. Camadas Arquiteturais

### Camada 1 — CLI Unificado (`ecossistema.py`)

Ponto de entrada único. Roteia comandos para as ferramentas via `subprocess.run()`:

| Comando | Ferramenta | Entry Point |
|:---|:---|:---|
| `forge` | aidd-forge | `python -m aidd_forge.cli` |
| `generate` | aidd-generator | `scripts/pipeline_completo.py` |
| `master` | aidd-master | `scripts/aidd.py` |
| `enterprise` | aidd-enterprise | `scripts/aidd.py` |
| `ops` | aidd-ops | `scripts/pipeline_ops.py` |
| `bridge` | aidd-bridge | `python -m aidd_bridge.cli` |
| `audit` | gates/ | `python ecossistema.py audit` |
| `components` | componentes/ | `scripts/gestor_componentes.py` |
| `dependencia` | scripts/ | `scripts/gestor_dependencias.py` |
| `orchestrate` | orca-plan-orchestrator | `scripts/orchestrator_engine.py` |

**Princípio:** O CLI é um compilador mecânico — nunca invoca LLM, nunca toma decisões. Cada ferramenta herda `os.environ.copy()` e opera em seu próprio `cwd`.

### Camada 2 — Ferramentas Autocontidas (`tools/`)

Cada tool tem:
- `AGENTS.md` — Diretrizes canônicas para agentes de IA (31-35 linhas, inglês)
- `README.md` — Documentação de uso
- Código-fonte Python (autônomo, zero imports cruzados entre tools)
- Testes pytest locais
- Gates locais (quando aplicável)

**Invariante:** Nenhuma tool importa código de outra em runtime. Consolidação é via `componentes/compartilhado/` + materialização física.

### Camada 3 — Quality Gates (`gates/`)

16 verificações determinísticas que bloqueiam qualquer entrega não-conforme:

| Gate | Função |
|:---|:---|
| `G_ECOSSISTEMA_INTEGRIDADE` | Integridade estrutural do repositório |
| `G_DRIFT_NUCLEO_COMPARTILHADO` | Divergência entre Master/Enterprise |
| `G_HARNESS_COMPAT` | Sincronização multi-harness |
| `G_SEGREDOS` | Deteção de credenciais vazadas |
| `G_CLI_HELP_CONSISTENCIA` | AST de help vs flags reais |
| `G_COMPONENTE_AGNOSTICO` | Universalidade de componentes |
| `G_ZERO_HEADLESS` | Proibição de subagentes invisíveis |
| `G_INFRA_COMPOSE` | Docker Compose (Checkov + PyYAML) |
| `G_HADOLINT` | Dockerfiles (OCI best practices) |
| `G_TESTES_REAIS` | Suíte pytest real (zero mocks) |
| `G_HONESTIDADE_ROTULO` | Anti-marketing nos gates |
| `G_ARQUITETURA_DELIVERABLE` | Clean Architecture/DDD (AST) |
| `G_DEPENDENCIAS_PIN_HASH` | Dependências com hash SHA-256 |
| `G_ESCRITOR_ATOMICO` | Escrita atômica de arquivos |
| `G_TRANSACTION_LOG_LRU` | LRU do transaction log |
| `G_UNIVERSAL_HARNESS` | Compatibilidade universal |

**Validação:** `python ecossistema.py audit` — exit 0 = aprovado, exit 1 = bloqueado.

### Camada 4 — Orquestração (`/orchestrate`)

Motor de orquestração multi-agente com 3 ambientes:
- **ORCA** — App ORCA real via orca-cli (worktree + terminal)
- **Subagentes** — Agent tool da sessão (contexto compartilhado)
- **Git Worktree** — Motor nativo (git worktree + harness spawnado)

---

## 3. Fluxos de Trabalho

### 3.1 Projeto Novo (do zero)

```
Ideia (linguagem natural)
  └─→ /generate "sistema de agendamento"
       └─→ Pipeline 8 fases (Pesquisa → Implementação)
            └─→ Projeto completo com testes e docs
                 └─→ /forge . (instala governança)
                      └─→ /master <módulo> (expande)
                           └─→ /ops (provisiona infra)
```

### 3.2 Projeto Existente (código próprio)

```
Projeto legado
  └─→ /forge . (instala gates + governança)
       └─→ /master <módulo> (adiciona funcionalidades)
            └─→ /enterprise auth <nome> (componentes certificados)
                 └─→ /ops (deploy)
```

### 3.3 Projeto Low-Code (Lovable/v0/Bolt)

```
App no-code
  └─→ /bridge scan (mapeia estrutura)
       └─→ /bridge convert-db (Supabase → PostgreSQL)
            └─→ /bridge merge (unifica apps, se necessário)
                 └─→ /bridge pack (Docker + SSL)
                      └─→ /forge . (governança)
                           └─→ /master / /enterprise (expansão)
                                └─→ /ops (VPS)
```

### 3.4 Orquestração Multi-Frente

```
Plano de execução (JSON)
  └─→ /orchestrate docs/planos/<plano>/
       └─→ Compila Flight Plan
            └─→ Spawna frentes paralelas (worktrees isoladas)
                 └─→ Cada frente executa independentemente
                      └─→ Merge + validação conjunta
```

---

## 4. Núcleo Cibernético (`core/`)

Três módulos que otimizam o uso de contexto e tokens:

| Módulo | Arquivo | Função |
|:---|:---|:---|
| **Cognitive Session Ledger** | `core/cognitive_ledger.py` | Persiste estado de sessão em SQLite-WAL. Recuperável em <5ms sem consumir histórico do chat. |
| **Dynamic Context Slicer** | `core/context_slicer.py` | Fatiamento sintático via AST. Gera payloads <150 tokens com contratos e assinaturas. |
| **MCP Dynamic Router** | `core/mcp_dynamic_router.py` | Fachada lazy para MCP servers. Mantém system prompt <1.200 tokens. |

---

## 5. Sistema de Componentes (`componentes/`)

Fonte única de verdade para código compartilhado entre ferramentas:

```
componentes/
├── compartilhado/
│   ├── src-core/           ← Database, Result Monad, EventBus, Saga, etc.
│   └── skills/             ← Skills universais (orca-plan-orchestrator, etc.)
├── aidd-master/
│   ├── templates/          ← Templates de módulos verticais
│   └── gates/              ← Gates locais do Master
└── aidd-ops/
    ├── templates/infra/    ← Docker Compose, Dockerfiles
    └── ansible/            ← Playbooks de hardening
```

**Distribuição:** O `scripts/gestor_componentes.py` sincroniza fisicamente os componentes para todos os harnesses (`.agent/`, `.claude/`, `.cursor/`, `.gemini/`, `.mimocode/`, `.opencode/`). Nunca há imports cruzados em runtime.

---

## 6. Multi-Harness (Supremacia Agnóstica)

O ecossistema opera em qualquer harness de IA. A sincronização é automática:

| Harness | Diretório | Mecanismo |
|:---|:---|:---|
| Antigravity (AGY) | `.agent/` | Padrão canônico |
| Claude Code | `.claude/` | CLAUDE.md + commands/ |
| Cursor IDE | `.cursor/` | rules/ |
| MimoCode | `.mimocode/` | skills/ + hooks/ |
| OpenCode | `.opencode/` | skill(s)/ |
| Gemini CLI | `.gemini/` | extensions/ + skills/ |
| Hermes | `.agents/` | skills/ |

**Invariantes:**
- Uma skill criada é distribuída para todos os harnesses
- AGENTS.md é o ponto único de governança (CLAUDE.md e GEMINI.md são ponteiros)
- `.gitattributes` força `eol=lf` para estabilidade de prompt caching

---

## 7. Economia de Tokens

O ecossistema implementa 4 estratégias para minimizar consumo de tokens:

1. **AGENTS.md enxuto:** Raiz = 51 linhas (~510 tokens). Tools = 31-35 linhas cada.
2. **Context-Purge:** Cada fase de trabalho descarta contexto anterior (FSM no generator).
3. **Dynamic Context Slicer:** AST-based, payloads <150 tokens.
4. **Cache Invariance:** `.gitattributes` com `eol=lf` garante hash estável para prompt caching.

---

## 8. Invariantes Arquiteturais

1. **Zero Stubs:** Todo código é funcional, tipado e testado. Sem `pass`, sem mocks.
2. **Result Monad:** Todas as operações retornam `Result.ok()` ou `Result.fail()`.
3. **Determinismo:** Scripts determinísticos para tarefas mecânicas. LLM apenas para cognição.
4. **Isolamento:** Ferramentas não se importam em runtime. Comunicação via arquivos JSON/SQLite.
5. **Binary Quality:** `python ecossistema.py audit` é o único árbitro de qualidade.
6. **Developer in Control:** Zero headless background subagents. Interação sempre sequencial.
7. **Zero Vendor Lock-in:** Python puro, qualquer SO, qualquer harness, qualquer provedor LLM.
