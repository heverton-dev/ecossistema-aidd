# Relatório: Correção de Agnosticismo, Duplicidade e Slash Commands

**Data:** 2026-09-10
**Escopo:** Correção estrutural do ecossistema AIDD — slash commands, duplicidade, agnosticismo
**Resumo:** 103 arquivos | +311 linhas | -2.029 linhas

---

## 1. Problemas Identificados e Corrigidos

### 1.1 Conflito de Slash Commands `/orchestrate` vs `/ops`

AGENTS.md §3 listava `/orchestrate` como comando do AIDD Ops, mas na verdade `/orchestrate` é exclusivo da ORCA ADE (orquestração de planos de desenvolvimento). O comando correto do AIDD Ops é `/ops`.

**Correções:**
- `AGENTS.md` §3: Adicionada entrada `/ops [requisito]` com skill `aidd-ops-runner`; `/orchestrate` agora declara "Não é o comando do AIDD Ops"
- `ecossistema.py` banner: adicionada linha `/ops [requisito]` antes de `/orchestrate`
- `MEMORY.md` §4: adicionada entrada `/ops` na matriz de slash commands
- `docs/explicacoes/10-09-2026_explica-ecossistema-fluxo-completo.md`: 3 referências `/orchestrate (Ops)` → `/ops`

### 1.2 Duplicidade de Componentes em `componentes/<tool>/`

Existiam cópias byte-a-byte idênticas de skills e MCPs em `componentes/aidd-{ops,master,enterprise,generator}/` que já viviam em `tools/<tool>/` e nunca eram sincronizadas.

**Removidos:**
- `componentes/aidd-ops/` (inteiro — 10 arquivos .gitkeep + 2 MCPs duplicados)
- `componentes/aidd-master/skills/` (2 skills duplicadas)
- `componentes/aidd-enterprise/skills/` (1 skill duplicada)
- `componentes/aidd-generator/` (inteiro — 2 skills + 1 MCP duplicados)
- 5 escopos `aidd-*` removidos do `manifesto_harnesses.json`

### 1.3 Skills Plain-Named Stub Duplicadas

Cada ferramenta tinha dois skills: um `aidd-*-runner` (canônico, wireado ao slash command) e um plain-named stub (8 linhas, redirect vazio). Total: 5 pares duplicados.

**Removidos (stub + Gemini extension):**
- `forge/` → mantido `aidd-forge-runner`
- `generate/` → mantido `aidd-generator-runner`
- `master/` → mantido `aidd-master-runner`
- `enterprise/` → mantido `aidd-enterprise-runner`
- `bridge/` → mantido `aidd-bridge-runner` (era cópia idêntica)

### 1.4 Violações de Agnosticismo

| Skill | Violação | Correção |
|---|---|---|
| `skill-creator-runner` | Hardcodava "Claude Code" como primário | Reescrito: "se o harness dispuser de ferramenta nativa" |
| `mcp-creator-runner` | Hardcodava "Anthropic" e "Claude Code" | Reescrito: abordagem agnóstica + refs para `tools/` |
| `orca-plan-orchestrator` | Listava só 4 de 7 harnesses | Atualizado: todos os 7 harnesses |
| 4 skills `.claude-only` | Dependiam de MCP `code-review-graph` sem aviso, não distribuídas | Movidas para `componentes/compartilhado/` com frontmatter `depends: mcp: code-review-graph` |

### 1.5 Path Hardcoded em Hooks

| Arquivo | Antes | Depois |
|---|---|---|
| `.gemini/hooks/crg-session-start.sh` | `C:/Users/trcnologia/Desktop/ecossistema-aidd` | `$(git rev-parse --show-toplevel)` |
| `.gemini/hooks/crg-update.sh` | `C:/Users/trcnologia/Desktop/ecossistema-aidd` | `$(git rev-parse --show-toplevel)` |

### 1.6 Harness `.codebuddy/` não documentado

Adicionado ao `manifesto_harnesses.json` como 7º harness suportado (skill, command, hook).

### 1.7 Comando `/ops` com status defasado

`componentes/compartilhado/comandos/ops.md` e `aidd-ops-runner/SKILL.md` diziam "Pacote 3 não entregue" — atualizados para refletir MVP funcional.

---

## 2. Regressão Preventiva

Nova seção no `G_ECOSSISTEMA_INTEGRIDADE.py` (**seção 6: Anti-regressão**):
- Verifica se existe algum diretório plain-named (`forge/`, `bridge/`, etc.) que tenha um correspondente `aidd-*-runner`
- Se encontrar → gate REPROVA (exit 1)
- Roda em todo commit via pre-commit hook

---

## 3. Checklist de Alterações

### 3.1 Arquivos Canônicos Modificados (8)

| # | Arquivo | Alteração |
|---|---|---|
| 1 | `AGENTS.md` | §3: +`/ops`, `/orchestrate` clarificado |
| 2 | `ecossistema.py` | Banner: +`/ops` |
| 3 | `MEMORY.md` | §4: +`/ops` na matriz |
| 4 | `componentes/compartilhado/comandos/ops.md` | Status atualizado |
| 5 | `componentes/compartilhado/skills/aidd-ops-runner/SKILL.md` | Status atualizado |
| 6 | `gates/G_ECOSSISTEMA_INTEGRIDADE.py` | +seção 6 anti-regressão |
| 7 | `gates/manifesto_harnesses.json` | -5 escopos tools/*, +codebuddy |
| 8 | `docs/explicacoes/02-...fluxo-completo.md` | `/orchestrate (Ops)` → `/ops` |

### 3.2 Skills Movidas para `componentes/compartilhado/` (4 novas)

| Skill | Antes | + frontmatter |
|---|---|---|
| `debug-issue` | `.claude/skills/` (não distribuída) | `depends: mcp: code-review-graph` |
| `explore-codebase` | `.claude/skills/` (não distribuída) | `depends: mcp: code-review-graph` |
| `refactor-safely` | `.claude/skills/` (não distribuída) | `depends: mcp: code-review-graph` |
| `review-changes` | `.claude/skills/` (não distribuída) | `depends: mcp: code-review-graph` |

### 3.3 Skills Canônicas Corrigidas (3)

| Skill | Violação | Correção |
|---|---|---|
| `skill-creator-runner` | Hardcoded "Claude Code" | Agnóstico |
| `mcp-creator-runner` | Hardcoded "Anthropic" | Agnóstico |
| `orca-plan-orchestrator` | 4 de 7 harnesses | 7 de 7 |

### 3.4 Hooks Corrigidos (2)

| Arquivo | Fix |
|---|---|
| `.gemini/hooks/crg-session-start.sh` | `git rev-parse --show-toplevel` |
| `.gemini/hooks/crg-update.sh` | `git rev-parse --show-toplevel` |

### 3.5 Deletados — Componentes Duplicados tools/* (20 arquivos)

- `componentes/aidd-ops/` inteiro (12 arquivos)
- `componentes/aidd-master/skills/` (2 skills, 2 arquivos)
- `componentes/aidd-enterprise/skills/` (1 skill, 1 arquivo)
- `componentes/aidd-generator/` inteiro (7 arquivos)

### 3.6 Deletados — Skills Plain-Named Stubs (40 arquivos)

5 stubs × (`componentes/` + 6 harnesses + Gemini extension) = ~35 arquivos removidos

| Stub | Canônico mantido |
|---|---|
| `forge/` | `aidd-forge-runner` |
| `generate/` | `aidd-generator-runner` |
| `master/` | `aidd-master-runner` |
| `enterprise/` | `aidd-enterprise-runner` |
| `bridge/` | `aidd-bridge-runner` |

### 3.7 Sincronizados (231 componentes)

Todos os arquivos em `.{claude,agents,opencode,mimocode,cursor}/skills/` e `commands/` + `.gemini/extensions/` + `.codebuddy/skills/` re-gerados pelo `components sync`.

---

## 4. Verificação Final

| Check | Resultado |
|---|---|
| `python ecossistema.py components verify --tipo todos` | 42 componentes, SHA-256 OK |
| `python gates/G_ECOSSISTEMA_INTEGRIDADE.py` | 100% APROVADO (inclui seção 6 anti-regressão) |
| `pytest gates/test_g_ecossistema_integridade.py` | 10/10 passed |
| `pytest tools/aidd-ops/tests/` | 150/150 passed |
| Duplicidade plain-named | NENHUMA |
| Skills por harness | 33-34 (sync) + 1 impeccable (terceiro) |

---

## 5. Pendente (requer decisão)

| Item | Situação |
|---|---|
| `sandeco-token-reduce` | Anthropic-locked por design (SDK + modelo + env var) |
| `impeccable` | Skill de terceiros, instalação independente |
| MCPs OpenCode/MimoCode | Harnesses não suportam `.mcp.json` nativamente |
| `.gemini/skills/` (legado) | Skills bare de iteração anterior — limpeza futura |
| `.impeccable/` | Config de terceiro — adicionar ao `.gitignore` |
