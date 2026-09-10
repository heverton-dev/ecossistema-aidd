# 🏛️ AGENTS.md — Governança Canônica do Ecossistema AIDD Unificado

> **Repositório:** https://github.com/heverton-dev/ecossistema-aidd  
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)  
> **Lei Fundamental:** Transparência Total, Determinismo Estrito, Zero Stubs, Economia Extrema de Tokens.

---

## 0. PRIMEIRO USO — BOOTSTRAP AUTOMÁTICO (LEIA ANTES DE QUALQUER OUTRA COISA)

O usuário NUNCA deve precisar digitar comando Python no terminal para o projeto
funcionar. `git clone` sozinho não executa nada (limitação do próprio Git) —
por isso, ao iniciar QUALQUER sessão neste repositório (Claude Code, Cursor,
Antigravity, OpenCode, MimoCode, Gemini CLI, Codex CLI), o assistente deve:

1. Rodar silenciosamente `python ecossistema.py dependencia verify`.
2. Se retornar exit 1 (dependência externa faltando — ex.: skill `impeccable`
   ainda não instalada nesta máquina), rodar `python ecossistema.py dependencia
   bootstrap` e informar o resultado ao usuário em 1 frase curta. Não pedir
   permissão para isso: é idempotente, só instala o que falta, nunca
   sobrescreve nada que o usuário já tenha.
3. Se o usuário digitar `/dependencia bootstrap|skill|mcp` (ou pedir em
   linguagem natural para "configurar"/"instalar dependências"/adicionar uma
   skill ou MCP novo), acionar a skill `skills/dependencia-runner` (ver §3).

Exceção: não repetir isso dentro de um subagente/worktree efêmero disparado
para uma tarefa específica — é checagem de sessão principal, não por-tarefa.

---

## 1. VISÃO GERAL DO ECOSSISTEMA

> **North Star:** Transformar uma ideia em software testado, e distribuir a mesma governança pra qualquer harness de IA.

O **Ecossistema AIDD** unifica 5 ferramentas complementares de Engenharia Agêntica de Software em um monorepo modular e desacoplado, todas a serviço desse north star:

| Ferramenta | Diretório | Papel Principal | Slash Command |
| :--- | :--- | :--- | :--- |
| **AIDD Forge** | 	ools/aidd-forge | Bootstrap, micro-ambientes isolados, fatiamento de fases e purge de contexto | /forge [caminho] |
| **AIDD Generator** | 	ools/aidd-generator | Fábrica autônoma de software (Pipeline 8 fases a partir de ideia natural) | /generate <ideia> |
| **AIDD Master** | 	ools/aidd-master | Suíte modular com Clean Architecture, Fatias Verticais e SQLite WAL | /master <modulo> |
| **AIDD Enterprise** | tools/aidd-enterprise | Plataforma de Missão Crítica com Injeção de Componentes SHA-256 e Zero-Trust | /enterprise <tipo> <nome> |
| **AIDD Ops** | tools/aidd-ops | Meta-Orquestrador Agêntico de Infraestrutura — MVP em construção, ver docs/planos/feitos/integracao-aidd-ops/ | (em construção — Pacote 3) |
| **AIDD Bridge** | tools/aidd-bridge | Extrator, Unificador e Empacotador de Projetos Low-Code (Lovable/Supabase) para VPS | /bridge [comando] |

---

## 2. REGRAS DE OURO INEGOCIÁVEIS (LEI FUNDAMENTAL)

1. **Determinismo Primeiro (Zero Token Fallacy):**
   - Nunca use LLM para tarefas mecânicas que podem ser resolvidas com scripts Python, regex, AST ou JSON Schema.
2. **Qualidade Binária (Gates Determinísticos):**
   - Nenhuma entrega é aceita sem a aprovação estrita dos Quality Gates (exit 0 = aprovado, exit 1 = bloqueado).
3. **Persistência Estruturada e Transparência Total:**
   - O estado vive em arquivos estruturados (JSON, SQLite), nunca na memória volátil do chat.
   - Qualquer modificação deve ser auditável e rastreável via commit limpo.
4. **Economia Extrema de Tokens (Tríade Caveman Ultra):**
   - Pensamento interno telegráfico (Caveman Style).
   - Saídas ao usuário estritamente concisas em PT-BR.
   - Purge imediato de contexto entre execuções de subagentes.
5. **Zero Stubs / Zero Mocks Falsos em Produção:**
   - Código gerado deve ser 100% funcional, tipado e com testes unitários e de integração reais.
6. **Supremacia Agnóstica (Universalidade Total):**
   - Absolutamente TUDO (skills, mcps, specs, hooks, slash commands, fluxos, configurações) deve operar de forma 100% agnóstica a ambiente de execução, sistema operacional, harness (OpenCode, Antigravity, Claude, Mimo, Freebuff, Hermes, DeepSeek, etc.) e provedor de LLM.
   - Nenhuma dependência proprietária ou vendor lock-in é permitida no ecossistema.
   - **Protocolo Permanente de Agnosticidade:** consulte e siga estritamente o checklist canônico em `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`.
7. **Desenvolvedor no Controle (Zero Subagentes Headless Paralelos):**
   - É estritamente proibido ao assistente disparar subagentes paralelos invisíveis via tools (`task create`, `task start`, `invoke_subagent`, `background_task`) ou via subprocessos ocultos de CLI que concorram sem observabilidade.
   - Toda execução de worktree opera em modo interativo sequencial governado pelo desenvolvedor no terminal, eliminando saturação de contexto, rate limits e timeouts silenciosos.
8. **Anti-NIH (Not Invented Here):**
   - Antes de escrever mecanismo novo com mais de ~30-50 linhas para um problema genérico (scaffolding, parsing, scanner, fila, dashboard, hardening), documentar por escrito por que nenhuma ferramenta OSS madura resolve o problema.
   - Origem: o levantamento NIH (`docs/features/oportunidades-reaproveitamento-oss-nih.md`) documentou 26 casos onde a Regra #1 foi lida como "escreva seu próprio script determinístico" em vez de "não gaste esforço reinventando o que já está resolvido".
9. **Honestidade de Rótulo:**
   - Nenhuma mensagem de saída de gate/CLI pode usar linguagem que sugira certificação/segurança maior do que a cobertura real testada (proibido: "blindagem militar", "homologado para produção global", "nota A+" sem rubrica auditável por trás).
   - Verificado mecanicamente por `gates/G_HONESTIDADE_ROTULO.py` (AST sobre `print()`/`raise()` dos scripts de `gates/` e `scripts/gates/` de cada ferramenta, contra a lista em `gates/termos_proibidos_marketing.json`).
10. **Comunicação Direta, Sem Jargão e Sem Formalidade:**
    - Toda resposta ao usuário deve ser concisa, direta e em linguagem simples — evitar jargão técnico não explicado (nomes internos de mecanismos, termos de infraestrutura) e preferir analogia do dia a dia quando ela ajudar a entender mais rápido que a explicação técnica crua.
    - **Respostas Curtas, Mas Densas (Economia Ativa de Tokens):** alta densidade de informação com o menor volume de texto possível. Eliminar preâmbulos, saudações, paráfrases da pergunta e conclusões óbvias. Tokens de saída são os mais caros do modelo e acumulam no histórico de contexto dos turnos seguintes.
    - Simplicidade de forma nunca reduz a profundidade real nem justifica fabricar ou simplificar fatos — o conteúdo técnico continua completo e verdadeiro; só a forma de comunicar muda.
    - Zero rodeio/formalidade desnecessária: ir direto ao que foi feito, encontrado ou decidido.
    - Origem: feedback explícito do usuário em 2026-09-08 — uma explicação tecnicamente correta sobre consolidação de código (`fleet_discovery.py`) foi rejeitada por excesso de jargão antes de ser aceita na versão reescrita em linguagem simples.
    - Organização visual da saída: usar títulos, negrito, listas e blocos de código para estruturar a resposta e aproveitar as cores do tema do terminal, facilitando a leitura — isso organiza a forma, nunca substitui a linguagem simples e direta exigida acima.

---

## 3. SLASH COMMANDS UNIVERSAIS & SKILLS

Cada comando possui contrato formal executável em qualquer harness (Antigravity, Claude Code, MimoCode, Cursor):

### /forge [caminho]
- **Skill:** skills/aidd-forge-runner
- **Ação:** Inicializa o ecossistema AIDD, cria governança, gates e otimizadores de token no diretório indicado (ou . para o diretório atual).
- **CLI Equivalente:** python ecossistema.py forge init [caminho]

### /generate <ideia>
- **Skill:** skills/aidd-generator-runner
- **Ação:** Inicia o pipeline autônomo de 8 fases para transformar uma ideia em um projeto completo de software.
- **CLI Equivalente:** python ecossistema.py generate "<ideia>"

### /master <modulo>
- **Skill:** skills/aidd-master-runner
- **Ação:** Cria e integra uma nova fatia vertical de negócio (src/modules/<modulo>/) com rotas, modelos, serviços, UI e testes.
- **CLI Equivalente:** python ecossistema.py master add-module <modulo>

### /enterprise <tipo> <nome>
- **Skill:** skills/aidd-enterprise-runner
- **Ação:** Injeta e valida componentes certificados com hashes SHA-256 e conformidade Zero-Trust.
- **CLI Equivalente:** python ecossistema.py enterprise inject <tipo> <nome>

### /ops [requisito]
- **Skill:** skills/aidd-ops-runner
- **Ação:** Meta-Orquestrador Agêntico de Infraestrutura — orquestra stacks self-hosted a partir de requisitos em linguagem natural (sizing VPS, hardening SSH, Docker, deploy).
- **CLI Equivalente:** python ecossistema.py ops [requisito]

### /orchestrate [plano]
- **Skill:** skills/orca-plan-orchestrator
- **Ação:** ORCA ADE — orquestra a execução paralela e determinística de planos de **desenvolvimento de software** via git worktrees efêmeras e hooks reativos. **Não é o comando do AIDD Ops** (que é `/ops`).
- **CLI Equivalente:** python ecossistema.py orchestrate [plano]

### /plan <nome>
- **Skill:** skills/planos-auditoria-runner
- **Ação:** Gera estruturação padronizada e rascunhos de planos de auditoria, evolução ou testes com checagem determinística de cercas markdown sem fabricar decisões ou aprovações.
- **CLI Equivalente:** python ecossistema.py plan init <nome>

### /bridge [comando]
- **Skill:** skills/aidd-bridge-runner
- **Ação:** Extrai, unifica e empacota aplicações Low-Code (Lovable, v0, Bolt) para VPS própria com PostgreSQL puro, PostgREST e Docker Compose.
- **CLI Equivalente:** python ecossistema.py bridge [scan|convert-db|merge|pack]

---

## 4. AUDITORIA E META-QUALITY GATES

O ecossistema dispõe de Quality Gates globais em gates/:
- gates/G_ECOSSISTEMA_INTEGRIDADE.py: Audita a integridade física, sintática e estrutural dos 5 subprojetos e das skills.
- gates/G_DRIFT_NUCLEO_COMPARTILHADO.py: Detecta divergência não documentada entre os arquivos de núcleo compartilhados por linhagem entre aidd-master e aidd-enterprise (baseline em gates/baseline_nucleo_compartilhado.json).
- gates/G_HARNESS_COMPAT.py: Verifica que os artefatos multi-harness da raiz (comandos, skills, arquivos-ponteiro) permanecem sincronizados entre si.
- gates/G_SEGREDOS.py: Escaneia todo o repositório rastreado pelo git em busca de credenciais hardcoded, delegando ao detect-secrets (Yelp); baseline auditado em .secrets.baseline na raiz. Em `stages: [manual]` desde 2026-09-08 (ver nota abaixo) — roda sob demanda, não em todo commit.
- gates/G_CLI_HELP_CONSISTENCIA.py: Compara, via AST, flags citadas em print()/raise() contra flags realmente definidas via add_argument nos pontos de entrada argparse das 4 ferramentas (allowlist de flags de ferramenta externa em gates/allowlist_cli_help.json).
- gates/G_COMPONENTE_AGNOSTICO.py: Audita a integridade e cobertura multi-harness de todo componente novo ou modificado contra o manifesto.
- gates/G_ZERO_HEADLESS.py: Impede a execução de subagentes headless paralelos e assegura o modo interativo como rota primária e mandatória.
- gates/G_INFRA_COMPOSE.py: Audita estaticamente a integridade, sintaxe e segurança de orquestrações Docker Compose delegando ao Checkov e com parsing estruturado PyYAML, além de validar scripts de banco de dados do aidd-ops.
- gates/G_HADOLINT.py: Audita estaticamente melhores práticas OCI, segurança e sintaxe de todos os Dockerfiles (existentes e gerados) via Hadolint (Haskell Dockerfile Linter).
- gates/G_TESTES_REAIS.py: Roda pytest de verdade em cada tools/<ferramenta> e falha (exit 1) se qualquer suíte tiver failed > 0.
- gates/G_HONESTIDADE_ROTULO.py: Verifica a Regra de Ouro #9 — escaneia (via AST) print()/raise() dos scripts de gates/ e scripts/gates/ de cada ferramenta contra a lista de termos de marketing proibidos em gates/termos_proibidos_marketing.json.
- **Execução unificada:** os gates acima são hooks locais do framework **pre-commit** (`.pre-commit-config.yaml`, todos `repo: local`/`language: system`, herméticos e agnósticos). `python ecossistema.py audit` **delega** para `pre-commit run --all-files` (fallback ao runner legado se o pre-commit não estiver instalado). Roda também em **todo commit** via `.githooks/pre-commit` (gates → syncs). G_HONESTIDADE_ROTULO e G_SEGREDOS ficam em `stages: [manual]` (ver notas abaixo) — nunca mascaram um gate vermelho, só mudam a frequência de obrigatório. (NIH #4 / Fase 2-Gates3)
- **Nota (G_SEGREDOS):** movido para `stages: [manual]` em 2026-09-08, decisão explícita do usuário, registrada em `.pre-commit-config.yaml` (comentário no topo do arquivo). Motivo: reproduzimos uma inconsistência real entre `python gates/G_SEGREDOS.py` rodado direto (aprovava) e o mesmo script rodado dentro do hook do `git commit` via pre-commit framework (reprovava), nos mesmos arquivos, sem diferença de conteúdo nem de configuração do detect-secrets identificável — causa raiz não encontrada em tempo hábil. Isso bloqueava commits legítimos repetidamente por achados já revisados manualmente como falso positivo (documentação de skill, fixtures de teste, telemetria auto-gerada). Continua disponível sob demanda: `pre-commit run --hook-stage manual g-segredos --all-files` ou dentro de `python ecossistema.py audit`. Recomendado rodar periodicamente (ex.: antes de um push importante). Para reverter e voltar a rodar em todo commit, trocar `stages: [manual]` por `always_run: true` no hook `g-segredos` de `.pre-commit-config.yaml` — nenhuma outra mudança é necessária.
- **Nota (G_HONESTIDADE_ROTULO):** ainda não está incluído no `audit` agregado acima — rodando-o hoje (`python -m pre_commit run g-honestidade-rotulo --all-files --hook-stage manual`) ele reprova de verdade contra uma violação já conhecida e rastreada (tools/aidd-master e tools/aidd-enterprise `scripts/gates/G_SEGURANCA.py`, `G_ARQUITETURA.py`, `G_PERFORMANCE.py`), cuja correção de rota (rótulo vs. cobertura real) é escopo do item `docs/planos/fazendo/01-correcao-pos-auditoria-sem-maquiagem/07-corrigir-gate-de-seguranca-rotulado-blindagem-militar-rotulo-ou-cobertura-real.md`, pendente de decisão humana. Adicioná-lo ao `audit` antes disso exigiria mascarar a violação numa allowlist — o que contradiz a própria regra que o gate existe pra fazer cumprir.

---

## 4.1 CONVENÇÃO DE NOMENCLATURA DE CÓDIGO (PT-BR / INGLÊS)

Regra de estilo para código **novo** escrito daqui pra frente nas 5 ferramentas — formaliza o padrão que já existia de fato no código, sem nunca ter sido escrito. Não retroage: nenhum identificador existente é renomeado por causa desta regra.

- **Nomes técnicos / de infraestrutura → inglês.** Tudo que é mecanismo genérico de framework, sem relação com a regra de negócio do domínio gerado (classes de segurança, transporte, persistência, resiliência). Exemplos reais já no código: `SecurityGate`, `JWTService`, `MCPServer`, `CircuitBreaker`.
- **Nomes de domínio de negócio → português.** Tudo que representa um conceito ou uma ação do negócio que o AIDD gera para o usuário final (módulos, funções de regra, entidades). Exemplos reais já no código: `materializar`, `dimensionar`, `reconhecer_nicho`, `sincronizar_componente`.
- **Critério prático quando a fronteira não for óbvia:** se o nome ainda faz sentido reaproveitado num projeto genérico qualquer (não-AIDD), é técnico → inglês. Se o nome só faz sentido no contexto do negócio que está sendo gerado, é domínio → português.
- **Decisão:** aprovada pelo usuário em 2026-09-09, formalizando o padrão observado (opção única apresentada foi aceita sem alteração).

---

## 5. REGRAS DE COMPATIBILIDADE MULTI-HARNESS

- **CORRIGIDO em 2026-09-07** (a versão anterior desta seção, abaixo em itálico, estava errada pra OpenCode/MimoCode — corrigida com teste ao vivo, binário real instalado, contra o estado atual do repo, custo zero de LLM):
- **Claude Code / Grok:** Carregam skills a partir de `.claude/skills/`. Claude Code adicionalmente carrega comandos em `.claude/commands/` e lê `CLAUDE.md`.
- **OpenCode:** Confirmado ao vivo (`opencode debug skill`, binário real v1.18.29): descobre as 16 skills do projeto 100% a partir de `.opencode/skills/<nome>/SKILL.md` — nenhuma de `.claude/skills/` nem `.agent/skills/`. Também documentado oficialmente (opencode.ai/docs/skills) como buscas extras (não primárias): `.claude/skills/` e `.agents/skills/`.
- **MimoCode (binário `mimo`):** Confirmado ao vivo (`mimo debug skill`, binário real v0.1.14 — fork oficial do OpenCode pela Xiaomi, github.com/XiaomiMiMo/MiMo-Code): descobre 15 das 16 skills do projeto a partir de `.mimocode/skills/<nome>/SKILL.md`; a 16ª (`impeccable`, ainda não instalada sob o provider "mimocode" no `npx impeccable install`) foi encontrada via fallback em `.opencode/skills/`.
- **Gemini CLI:** `.gemini/skills/` é sincronizado (requer arquivos sem UTF-8 BOM), mas `confirmado: false` em `gates/manifesto_harnesses.json` — nenhuma doc oficial confirma que o Gemini CLI leia `SKILL.md` solto; o mecanismo real documentado é "extensions" (`.gemini/extensions/<nome>/gemini-extension.json`), não implementado aqui.
- **Hermes Agent:** Adota a convenção de `.agents/skills` (plural) e `.hermes/skills` — confirmado pelo próprio texto de ajuda da CLI real instalada (`hermes skills trust --help`: "Trust a project so its repo-local skills (./.hermes/skills, ./.agents/skills) load"), exigindo autorização explícita por projeto via `hermes skills trust <dir>`.
- **Antigravity (agy):** Documentação oficial (`antigravity.google/docs/skills/`, `antigravity.google/docs/rules-workflows/`) confirma que o default atual é `.agents/skills/<nome>/SKILL.md` (plural) e `.agents/rules/`; `.agent/` (singular) só sobrevive como fallback de compatibilidade legado, não é mais o caminho recomendado. O ecossistema gera hoje `.agents/` (corrigido em 2026-09-07 — antes gerava só `.agent/`, que nunca foi o default real). Não repetido o teste ao vivo via `agy --print` nesta correção (evita gastar uma chamada real de LLM sem necessidade); a base é documentação oficial, não teste próprio.
- *(Nota histórica removida em 2026-09-07 — dizia que Claude Code/OpenCode/MimoCode liam de `.claude/skills/` e que `.agent/` era o destino físico "real" pra esse trio. Estava incorreto para OpenCode e MimoCode, ambos com pasta própria; substituído pelas linhas acima.)*
- **Freebuff:** Instalado na máquina, porém não expõe modo não interativo via CLI para validação automatizada.
- **Kiro CLI:** Utiliza conceito e diretório próprios (`.kiro/agents/`), não fazendo parte do padrão de skills deste ecossistema.
- **Cursor IDE:** Carrega regras a partir de `.cursor/rules/` (mecanismo de arquivo único, não pasta por componente).
- **Raiz Canônica:** Todos os harnesses convergem para as definições canônicas de AGENTS.md e da CLI ecossistema.py.
- **Fonte física única de todo componente (skill, mcp, spec, hook, config, command, sub-agent, script):** `componentes/<ferramenta ou compartilhado>/<tipo>/`. O mapeamento de cada tipo para as pastas físicas por harness listadas acima está formalizado em `gates/manifesto_harnesses.json` e é aplicado por `python ecossistema.py components sync|verify --tipo <tipo>`. As pastas físicas por harness (.claude/, .agents/, .opencode/, .mimocode/, .cursor/, .gemini/, skills/ bare, etc.) são DESTINOS GERADOS por esse comando — nunca editadas manualmente a partir desta migração.

> **Nota de Proveniência:** Esta seção reflete testes empíricos executados em 2026-09-05 contra instalações reais dos 7 harnesses nesta máquina — não suposições conceituais. A entrada do `agy` foi atualizada em 05/09/2026 por investigação estática de custo zero (sem chamada de LLM), não por um novo teste comportamental — a contradição com o teste comportamental anterior permanece registrada. Deve ser re-verificada caso essas ferramentas passem por atualizações ou caso o mecanismo exato do `freebuff` seja identificado no futuro.

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
