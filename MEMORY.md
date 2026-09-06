# 🧠 MEMORY.md — Memória Estruturada e Contexto Operacional Consolidado

> **Repositório:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Última Atualização:** 2026-09-06  
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)  
> **Finalidade:** Memória persistente de longo prazo para guiar desenvolvedores e agentes de IA em qualquer harness, evitando amnésia de contexto e retrabalho.

---

## 1. IDENTIDADE E ARQUITETURA DO ECOSSISTEMA

O **Ecossistema AIDD** é um monorepo agnóstico que integra 4 ferramentas complementares de Engenharia Agêntica de Software:

- **AIDD Forge (`tools/aidd-forge`):** Bootstrap de governança, isolamento de fases e purge de contexto (`/forge`).
- **AIDD Generator (`tools/aidd-generator`):** Fábrica autônoma com pipeline de 8 fases e contratos JSON Schema (`/generate`).
- **AIDD Master (`tools/aidd-master`):** Monólito modular com fatias verticais, SQLite WAL e Result Monad (`/master`).
- **AIDD Enterprise (`tools/aidd-enterprise`):** Missão crítica com injeção de componentes SHA-256 e Zero-Trust (`/enterprise`).

**Fonte Física Canônica Única:** Todo componente (`skill`, `command`, `mcp`, `hook`, `spec`) reside estritamente em `componentes/<escopo>/<tipo>/`. As pastas `.agent/`, `.claude/`, `.gemini/`, `.agents/`, `skills/` são alvos de materialização gerados pelo script `scripts/gestor_componentes.py` (`python ecossistema.py components sync`).

---

## 2. AS 7 REGRAS DE OURO INEGOCIÁVEIS (`AGENTS.md`)

1. **Determinismo Primeiro (Zero Token Fallacy):** Nunca usar LLM para tarefas mecânicas determinísticas (usar scripts Python, AST, regex, JSON Schema).
2. **Qualidade Binária (Gates Determinísticos):** Toda validação produz saída binária (`exit 0` = aprovado, `exit 1` = bloqueado).
3. **Persistência Estruturada e Transparência Total:** Estado reside em arquivos auditáveis (JSON, SQLite WAL, Git), nunca na memória volátil do chat.
4. **Economia Extrema de Tokens (Tríade Caveman Ultra):** Thinking telegráfico Caveman, saídas concisas em PT-BR, purge de contexto entre fases.
5. **Zero Stubs / Zero Mocks Falsos em Produção:** Código gerado deve ser funcional, tipado e com testes reais.
6. **Supremacia Agnóstica (Universalidade Total):** Nenhuma dependência proprietária ou lock-in. Suporte idêntico entre sistemas operacionais (Windows, Linux, macOS) e harnesses (Claude Code, Antigravity, OpenCode, MimoCode, Gemini CLI, Hermes, Cursor).
7. **Desenvolvedor no Controle (Zero Subagentes Headless Paralelos):** Proibido disparar subagentes invisíveis em segundo plano (`invoke_subagent` ou subprocessos desassistidos). Execução sequencial governada pelo desenvolvedor no terminal.

---

## 3. OS 7 META-QUALITY GATES UNIFICADOS (`python ecossistema.py audit`)

| Gate | Arquivo | Responsabilidade |
|---|---|---|
| **G1** | `gates/G_ECOSSISTEMA_INTEGRIDADE.py` | Audita presença estrutural, sintaxe Python (AST) e integridade dos subprojetos. |
| **G2** | `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` | Detecta divergências de código entre o núcleo compartilhado `aidd-master` e `aidd-enterprise`. |
| **G3** | `gates/G_HARNESS_COMPAT.py` | Garante sincronismo universal de componentes e correspondência entre gates e documentação. |
| **G4** | `gates/G_SEGREDOS.py` | Varredura de credenciais e tokens expostos em arquivos rastreados pelo git. |
| **G5** | `gates/G_CLI_HELP_CONSISTENCIA.py` | Compara flags mencionadas em mensagens de ajuda/erro contra argumentos reais do argparse. |
| **G6** | `gates/G_COMPONENTE_AGNOSTICO.py` | Audita integridade e cobertura multi-harness de componentes novos ou modificados. |
| **G7** | `gates/G_ZERO_HEADLESS.py` | Assegura que o motor de orquestração tenha modo interativo obrigatório e bloqueia execução headless oculta. |

---

## 4. MATRIZ DE SLASH COMMANDS UNIVERSAIS

| Slash Command | Skill Subjacente | CLI Universal Equivalente | Função |
|---|---|---|---|
| `/forge [caminho]` | `aidd-forge-runner` | `python ecossistema.py forge init [caminho]` | Bootstrap e blindagem de governança em novos projetos. |
| `/generate <ideia>` | `aidd-generator-runner` | `python ecossistema.py generate "<ideia>"` | Disparo da fábrica de 8 fases a partir de ideia. |
| `/master <modulo>` | `aidd-master-runner` | `python ecossistema.py master add-module <modulo>` | Criação de fatia vertical desacoplada em monólito modular. |
| `/enterprise <tipo> <nome>` | `aidd-enterprise-runner` | `python ecossistema.py enterprise inject <tipo> <nome>` | Injeção de componentes corporativos certificados SHA-256. |
| `/orchestrate [plano]` | `orca-plan-orchestrator` | `python ecossistema.py orchestrate [plano]` | Orquestração interativa de planos fatiados via worktrees efêmeras. |
| `/plan <nome>` | `planos-auditoria-runner` | `python ecossistema.py plan init <nome>` | Estruturação determinística de planos de auditoria e evolução. |

---

## 5. TRAVAS ANTI-HEADLESS E PROTOCOLO ORCA ADE

- **Modo Interativo Mandatório:** O orquestrador (`orchestrator_engine.py`) opera com `interactive: bool = True` por padrão.
- **Flag Perigosa Requerida:** Qualquer tentativa de execução não assistida deve explicitar `--dangerously-force-headless` na CLI do `ecossistema.py`.
- **Abort Atômico (`Ctrl+C`):** Se o desenvolvedor interromper a execução no terminal, o motor captura o sinal, atualiza o estado para `FAILED`, executa a purga imediata da worktree efêmera e libera os locks git.
- **Prévia de Escopo:** Antes de iniciar a worktree, o comando a ser executado, o harness atribuído e a worktree são impressos no terminal para confirmação do desenvolvedor.
- **Seleção Interativa de Harness por Frente:** Durante o pré-voo, o usuário escolhe se quer harness único ou definir um harness específico para cada frente (ex: Claude para arquitetura, Mimo para implementação, Agy para validação).

---

## 6. HISTÓRICO CONSOLIDADO DE DECISÕES ARQUITETURAIS

- **2026-09-04:** Criação dos gates de integridade inicial, baseline de núcleo compartilhado e varredura de segredos.
- **2026-09-05:** Centralização de componentes em `componentes/` e automação multi-harness via `gestor_componentes.py`.
- **2026-09-06:**
  - Resolução do Achado #1 do `aidd-enterprise` (exposição do `--tipo-ambiguo` na CLI com testes reais aprovados).
  - Universalização dos comandos `/orchestrate` e `/plan` para todos os harnesses (`.agent/commands/` e `.claude/commands/`).
  - Implementação da seleção interativa de harness executor por frente no pré-voo da orquestração.
  - Implementação da Regra de Ouro #7 no `AGENTS.md` e criação do 7º Quality Gate (`G_ZERO_HEADLESS.py`).
  - Estabelecimento do padrão de trabalho com abort atômico e bloqueio completo de subagentes headless.
