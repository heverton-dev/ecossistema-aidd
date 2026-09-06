# 🏛️ AGENTS.md — Governança Canônica do Ecossistema AIDD Unificado

> **Repositório:** https://github.com/heverton-dev/ecossistema-aidd  
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)  
> **Lei Fundamental:** Transparência Total, Determinismo Estrito, Zero Stubs, Economia Extrema de Tokens.

---

## 1. VISÃO GERAL DO ECOSSISTEMA

O **Ecossistema AIDD** unifica 5 ferramentas complementares de Engenharia Agêntica de Software em um monorepo modular e desacoplado:

| Ferramenta | Diretório | Papel Principal | Slash Command |
| :--- | :--- | :--- | :--- |
| **AIDD Forge** | 	ools/aidd-forge | Bootstrap, micro-ambientes isolados, fatiamento de fases e purge de contexto | /forge [caminho] |
| **AIDD Generator** | 	ools/aidd-generator | Fábrica autônoma de software (Pipeline 8 fases a partir de ideia natural) | /generate <ideia> |
| **AIDD Master** | 	ools/aidd-master | Suíte modular com Clean Architecture, Fatias Verticais e SQLite WAL | /master <modulo> |
| **AIDD Enterprise** | 	ools/aidd-enterprise | Plataforma de Missão Crítica com Injeção de Componentes SHA-256 e Zero-Trust | /enterprise <tipo> <nome> |
| **AIDD Ops** | 	ools/aidd-ops | Meta-Orquestrador Agêntico de Infraestrutura — MVP em construção, ver docs/planos/integracao-aidd-ops/ | (em construção — Pacote 3) |

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
- gates/G_INFRA_COMPOSE.py: Audita estaticamente a integridade e sintaxe de orquestrações Docker Compose e scripts de banco de dados do aidd-ops.
- Execução unificada via CLI: python ecossistema.py audit (roda os 7 gates em sequência)

---

## 5. REGRAS DE COMPATIBILIDADE MULTI-HARNESS

- **Claude Code / Grok / OpenCode / Mimo (MimoCode):** Carregam skills a partir de `.claude/skills/` (confirmado via inspeção direta e saídas JSON de debug dos harnesses reais instalados). Claude Code adicionalmente carrega comandos em `.claude/commands/` e lê `CLAUDE.md`.
- **Pasta `.agent/`:** Mantida como destino físico gerado pelo mecanismo de sincronização (`.agent/commands/` e `.agent/skills/`) para compatibilidade com ferramentas que adotem essa convenção, mas os testes reais confirmam que OpenCode e MimoCode descobrem skills em `.claude/skills/`, e não em `.agent/skills/`.
- **Gemini CLI:** Carrega skills em `.gemini/skills/` (requer arquivos estritamente sem UTF-8 BOM no início).
- **Hermes Agent:** Adota a convenção de `.agents/skills` (plural) e `.hermes/skills`, exigindo autorização explícita por projeto via `hermes skills trust <dir>` (teste real com `hermes skills trust .` confirmou a busca exclusiva por `.hermes\skills` ou `.agents\skills`, não descobrindo `.claude/skills/` nem `.agent/skills/`).
- **Antigravity (agy):** Mecanismo real identificado por investigação estática de custo zero (binário `agy` v1.1.27 instalado + documentação oficial `antigravity.google/docs/skills`, sem gastar nenhuma chamada de LLM): descobre skills em `.agents/skills/<nome>/SKILL.md` (plural — mesma convenção do Hermes acima) ou globalmente em `~/.gemini/config/skills/`, com um manifesto opcional `.agents/skills.json` na raiz do repositório para apontar a um diretório compartilhado. O ecossistema gera hoje apenas `.agent/skills/` (singular). A documentação oficial alega suporte retroativo a `.agent/skills` (singular), mas isso contradiz o teste real anterior (duas chamadas `agy --print`, mesma versão instalada, 0/5 skills encontradas de forma estável) — contradição não resolvida sem gastar uma chamada real adicional; não presumir funcionamento automático via `.agent/skills/`. Ver `docs/planos/refinamento-notas-auditoria/05-investigacao-mecanismo-agy.md` para o diagnóstico completo.
- **Freebuff:** Instalado na máquina, porém não expõe modo não interativo via CLI para validação automatizada.
- **Kiro CLI:** Utiliza conceito e diretório próprios (`.kiro/agents/`), não fazendo parte do padrão de skills deste ecossistema.
- **Cursor IDE:** Carrega regras a partir de `.cursor/rules/` (mecanismo de arquivo único, não pasta por componente).
- **Raiz Canônica:** Todos os harnesses convergem para as definições canônicas de AGENTS.md e da CLI ecossistema.py.
- **Fonte física única de todo componente (skill, mcp, spec, hook, config, command, sub-agent, script):** `componentes/<ferramenta ou compartilhado>/<tipo>/`. O mapeamento de cada tipo para as pastas físicas por harness listadas acima está formalizado em `gates/manifesto_harnesses.json` e é aplicado por `python ecossistema.py components sync|verify --tipo <tipo>`. As pastas físicas por harness (.agent/, .claude/, .gemini/, skills/ bare, etc.) são DESTINOS GERADOS por esse comando — nunca editadas manualmente a partir desta migração.

> **Nota de Proveniência:** Esta seção reflete testes empíricos executados em 2026-09-05 contra instalações reais dos 7 harnesses nesta máquina — não suposições conceituais. A entrada do `agy` foi atualizada em 05/09/2026 por investigação estática de custo zero (sem chamada de LLM), não por um novo teste comportamental — a contradição com o teste comportamental anterior permanece registrada. Deve ser re-verificada caso essas ferramentas passem por atualizações ou caso o mecanismo exato do `freebuff` seja identificado no futuro.
