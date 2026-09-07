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

O **Ecossistema AIDD** unifica 5 ferramentas complementares de Engenharia Agêntica de Software em um monorepo modular e desacoplado:

| Ferramenta | Diretório | Papel Principal | Slash Command |
| :--- | :--- | :--- | :--- |
| **AIDD Forge** | 	ools/aidd-forge | Bootstrap, micro-ambientes isolados, fatiamento de fases e purge de contexto | /forge [caminho] |
| **AIDD Generator** | 	ools/aidd-generator | Fábrica autônoma de software (Pipeline 8 fases a partir de ideia natural) | /generate <ideia> |
| **AIDD Master** | 	ools/aidd-master | Suíte modular com Clean Architecture, Fatias Verticais e SQLite WAL | /master <modulo> |
| **AIDD Enterprise** | 	ools/aidd-enterprise | Plataforma de Missão Crítica com Injeção de Componentes SHA-256 e Zero-Trust | /enterprise <tipo> <nome> |
| **AIDD Ops** | 	ools/aidd-ops | Meta-Orquestrador Agêntico de Infraestrutura — MVP em construção, ver docs/planos/feitos/integracao-aidd-ops/ | (em construção — Pacote 3) |

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

### /orchestrate [plano]
- **Skill:** skills/orca-plan-orchestrator
- **Ação:** Orquestra a execução paralela e determinística de planos de software via ORCA ADE com git worktrees efêmeras e hooks reativos.
- **CLI Equivalente:** python ecossistema.py orchestrate [plano]

### /plan <nome>
- **Skill:** skills/planos-auditoria-runner
- **Ação:** Gera estruturação padronizada e rascunhos de planos de auditoria, evolução ou testes com checagem determinística de cercas markdown sem fabricar decisões ou aprovações.
- **CLI Equivalente:** python ecossistema.py plan init <nome>

---

## 4. AUDITORIA E META-QUALITY GATES

O ecossistema dispõe de Quality Gates globais em gates/:
- gates/G_ECOSSISTEMA_INTEGRIDADE.py: Audita a integridade física, sintática e estrutural dos 5 subprojetos e das skills.
- gates/G_DRIFT_NUCLEO_COMPARTILHADO.py: Detecta divergência não documentada entre os arquivos de núcleo compartilhados por linhagem entre aidd-master e aidd-enterprise (baseline em gates/baseline_nucleo_compartilhado.json).
- gates/G_HARNESS_COMPAT.py: Verifica que os artefatos multi-harness da raiz (comandos, skills, arquivos-ponteiro) permanecem sincronizados entre si.
- gates/G_SEGREDOS.py: Escaneia todo o repositório rastreado pelo git em busca de credenciais hardcoded (allowlist auditada em gates/allowlist_segredos.json).
- gates/G_CLI_HELP_CONSISTENCIA.py: Compara, via AST, flags citadas em print()/raise() contra flags realmente definidas via add_argument nos pontos de entrada argparse das 4 ferramentas (allowlist de flags de ferramenta externa em gates/allowlist_cli_help.json).
- gates/G_COMPONENTE_AGNOSTICO.py: Audita a integridade e cobertura multi-harness de todo componente novo ou modificado contra o manifesto.
- gates/G_ZERO_HEADLESS.py: Impede a execução de subagentes headless paralelos e assegura o modo interativo como rota primária e mandatória.
- gates/G_INFRA_COMPOSE.py: Audita estaticamente a integridade e sintaxe de orquestrações Docker Compose e scripts de banco de dados do aidd-ops.
- Execução unificada via CLI: python ecossistema.py audit (roda os 8 gates em sequência)

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
