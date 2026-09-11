# 🏛️ AGENTS.md — Governança Canônica do Ecossistema AIDD Unificado

> **Repositório:** https://github.com/heverton-dev/ecossistema-aidd
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)
> **Lei Fundamental:** Transparência Total, Determinismo Estrito, Zero Stubs, Economia Extrema de Tokens.
>
> **Detalhes de slash commands, gates, convenções, design de relatórios, multi-harness e MCP:**
> → `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`

---

## 0. PRIMEIRO USO — BOOTSTRAP AUTOMÁTICO

Ao iniciar QUALQUER sessão neste repositório (Claude Code, Cursor, Antigravity, OpenCode, MimoCode, Gemini CLI, Codex CLI):

1. Rodar silenciosamente `python ecossistema.py dependencia verify`.
2. Se exit 1, rodar `python ecossistema.py dependencia bootstrap` e informar em 1 frase. Não pedir permissão — é idempotente.
3. Se o usuário pedir `/dependencia bootstrap|skill|mcp`, acionar `skills/dependencia-runner`.

Exceção: não repetir dentro de subagente/worktree efêmero — é checagem de sessão principal.

---

## 1. VISÃO GERAL DO ECOSSISTEMA

> **North Star:** Transformar uma ideia em software testado, e distribuir a mesma governança pra qualquer harness de IA.

| Ferramenta | Diretório | Papel Principal | Slash Command |
| :--- | :--- | :--- | :--- |
| **AIDD Forge** | tools/aidd-forge | Bootstrap, micro-ambientes isolados, fatiamento de fases e purge de contexto | /forge [caminho] |
| **AIDD Generator** | tools/aidd-generator | Fábrica autônoma de software (Pipeline 8 fases a partir de ideia natural) | /generate <ideia> |
| **AIDD Master** | tools/aidd-master | Suíte modular com Clean Architecture, Fatias Verticais e SQLite WAL | /master <modulo> |
| **AIDD Enterprise** | tools/aidd-enterprise | Plataforma de Missão Crítica com Injeção de Componentes SHA-256 e Zero-Trust | /enterprise <tipo> <nome> |
| **AIDD Ops** | tools/aidd-ops | Meta-Orquestrador Agêntico de Infraestrutura | /ops [requisito] |
| **AIDD Bridge** | tools/aidd-bridge | Extrator, Unificador e Empacotador de Projetos Low-Code (Lovable/Supabase) para VPS | /bridge [comando] |

---

## 2. REGRAS DE OURO INEGOCIÁVEIS (LEI FUNDAMENTAL)

1. **Determinismo Primeiro:** Nunca use LLM para tarefas mecânicas resolúveis com scripts Python, regex, AST ou JSON Schema.
2. **Qualidade Binária:** Nenhuma entrega sem aprovação dos Quality Gates (exit 0 = aprovado, exit 1 = bloqueado).
3. **Persistência Estruturada:** Estado em arquivos auditáveis (JSON, SQLite), nunca na memória volátil do chat.
4. **Economia Extrema de Tokens (Tríade Caveman Ultra):** Thinking telegráfico. Saídas concisas em PT-BR. Purge entre subagentes.
5. **Zero Stubs / Zero Mocks em Produção:** Código 100% funcional, tipado, com testes reais.
6. **Supremacia Agnóstica:** Tudo opera de forma agnóstica a OS, harness e provedor de LLM. Sem vendor lock-in. Ver `docs/protocolos/05-09-2026_protocolo-agnosticidade-componentes.md`.
7. **Desenvolvedor no Controle (Zero Subagentes Headless Paralelos):** Proibido disparar subagentes invisíveis. Toda execução é interativa e sequencial no terminal.
8. **Anti-NIH:** Antes de escrever mecanismo novo com >30-50 linhas para problema genérico, justificar por escrito por que nenhuma ferramenta OSS resolve. Ver `docs/features/08-09-2026_feature-oportunidades-reaproveitamento-nih.md`.
9. **Honestidade de Rótulo:** Nenhuma saída pode alegar certificação/segurança maior que a cobertura real testada. Verificado por `gates/G_HONESTIDADE_ROTULO.py`.
10. **Comunicação Direta, Sem Jargão:** Respostas concisas, densas, em PT-BR. Sem preâmbulos. Organização visual com títulos, listas e negrito.

---

## 3. SLASH COMMANDS (resumo rápido)

| Comando | Skill | CLI |
| :--- | :--- | :--- |
| `/forge [caminho]` | aidd-forge-runner | `python ecossistema.py forge init [caminho]` |
| `/generate <ideia>` | aidd-generator-runner | `python ecossistema.py generate "<ideia>"` |
| `/master <modulo>` | aidd-master-runner | `python ecossistema.py master add-module <modulo>` |
| `/enterprise <tipo> <nome>` | aidd-enterprise-runner | `python ecossistema.py enterprise inject <tipo> <nome>` |
| `/ops [requisito]` | aidd-ops-runner | `python ecossistema.py ops [requisito]` |
| `/melhoria <pedido>` | melhoria | `python ecossistema.py melhoria init --pedido "..." --nome "..."` |
| `/plan <nome>` | plan → planos-auditoria-runner | `python ecossistema.py plan init <nome>` |
| `/orchestrate [plano]` | orchestrate → orca-plan-orchestrator | `python ecossistema.py orchestrate [plano]` |
| `/bridge [comando]` | aidd-bridge-runner | `python ecossistema.py bridge [scan\|convert-db\|merge\|pack]` |

Fluxo obrigatório: `/melhoria` → `/plan` → `/orchestrate` (3 etapas, parada humana entre cada uma — Regra #7).
Detalhes de cada comando: `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md#§3`.

---

## 4. GATES & COMPATIBILIDADE (referências rápidas)

- **Auditoria:** `python ecossistema.py audit` (delega ao pre-commit).
- **Gates:** `gates/G_*.py` — detalhes em `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md#§4`.
- **Convenção PT-BR/EN:** código técnico em inglês, domínio de negócio em português — detalhes em `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md#§4.1`.
- **Relatórios HTML:** pareamento `.html`+`.json`, scrollbar 4px, geração determinística — detalhes em `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md#§4.2`.
- **Multi-harness:** fonte canônica em `componentes/`, destinos gerados por `python ecossistema.py components sync` — detalhes em `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md#§5`.
- **MCP code-review-graph:** use graph ANTES de Grep/Glob/Read — detalhes em `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md#§MCP`.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes_tool` or `query_graph_tool` instead of Grep
- **Understanding impact**: `get_impact_radius_tool` instead of manually tracing imports
- **Code review**: `detect_changes_tool` + `get_review_context_tool` instead of reading entire files
- **Finding relationships**: `query_graph_tool` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview_tool` + `list_communities_tool`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes_tool` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context_tool` | Need source snippets for review — token-efficient |
| `get_impact_radius_tool` | Understanding blast radius of a change |
| `get_affected_flows_tool` | Finding which execution paths are impacted |
| `query_graph_tool` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes_tool` | Finding functions/classes by name or keyword |
| `get_architecture_overview_tool` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes_tool` for code review.
3. Use `get_affected_flows_tool` to understand impact.
4. Use `query_graph_tool` pattern="tests_for" to check coverage.
