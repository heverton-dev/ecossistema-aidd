# AGENTS — Referência Completa (Seções sob Demanda)

> Arquivo complementar ao `AGENTS.md` (núcleo). Carregue este arquivo apenas quando precisar
> de detalhes de slash commands, gates, convenções de código, design de relatórios,
> compatibilidade multi-harness ou instruções de MCP.
>
> **Fonte canônica:** este arquivo. Não edite as cópias distribuídas pelos harnesses diretamente.

---

## §3 — SLASH COMMANDS UNIVERSAIS & SKILLS (detalhado)

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

### Fluxo único de trabalho: `/melhoria` → `/plan` → `/orchestrate`

| Etapa | Comando | Entra | Sai | Parada no fim |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `/melhoria` | pedido em linguagem natural, ou plano existente pra reanalisar | relatório em `docs/melhorias/` com Nota Atual + evidência | "gero o plano a partir disto?" |
| 2 | `/plan` | relatório da etapa 1 (ou pedido direto) | pasta em `docs/planos/<nome>/`, tudo em rascunho | "aprova este plano?" |
| 3 | `/orchestrate` | plano aprovado | execução real das frentes | escolha de ambiente + aprovação do Plano de Voo |

**Um comando, um dono.** Cada slash command tem exatamente uma skill dona; as
skills-motor não têm slash command próprio e são acionadas pela dona. Duas
skills respondendo ao mesmo comando, com regras opostas, foi a causa direta das
árvores de mesa dentro de mesa no app ORCA (incidente de 11-09-2026).

### /melhoria <descrição em linguagem natural>
- **Skill:** skills/melhoria (dona) — etapa 1 de 3
- **Ação:** Investiga o código real (graph → Grep/Read → reprodução real), atribui Nota Atual 0-10 **com evidência**, e gera relatório `.html` + `.json` em `docs/melhorias/`. Também reanalisa um plano já existente, comparando previsto vs. implementado item a item.
- **CLI Equivalente:** python ecossistema.py melhoria init --pedido "<texto>" --nome "<3 palavras>"

### /plan <nome>
- **Skill:** skills/plan (dona) — etapa 2 de 3; motor: skills/planos-auditoria-runner
- **Ação:** Gera estruturação padronizada e rascunhos de planos de auditoria, evolução ou testes com checagem determinística de cercas markdown sem fabricar decisões ou aprovações.
- **CLI Equivalente:** python ecossistema.py plan init <nome>

### /orchestrate [plano]
- **Skill:** skills/orchestrate (dona) — etapa 3 de 3; motor da via nativa: skills/orca-plan-orchestrator
- **Ação:** Roteador de ambiente (ORCA / Subagentes / Git Worktree nativo) + Plano de Voo, e execução das frentes do plano. **Não é o comando do AIDD Ops** (que é `/ops`).
- **Regras fixas da via ORCA:** carregar o manual da versão instalada (`orca skills get orca-cli`) antes de qualquer comando; mesa independente (`--no-parent`) por padrão, filha só a pedido explícito; **nunca** lançar harness com `--resume <id-de-sessão>`; esperar `tui-idle` com `satisfied: true` antes de enviar o prompt; nunca reenviar no silêncio.
- **CLI Equivalente:** python ecossistema.py orchestrate [plano]

### /bridge [comando]
- **Skill:** skills/aidd-bridge-runner
- **Ação:** Extrai, unifica e empacota aplicações Low-Code (Lovable, v0, Bolt) para VPS própria com PostgreSQL puro, PostgREST e Docker Compose.
- **CLI Equivalente:** python ecossistema.py bridge [scan|convert-db|merge|pack]

---

## §4 — AUDITORIA E META-QUALITY GATES (detalhado)

O ecossistema dispõe de Quality Gates globais em gates/:
- gates/G_ECOSSISTEMA_INTEGRIDADE.py: Audita a integridade física, sintática e estrutural dos 5 subprojetos e das skills.
- gates/G_DRIFT_NUCLEO_COMPARTILHADO.py: Detecta divergência não documentada entre os arquivos de núcleo compartilhados por linhagem entre aidd-master e aidd-enterprise (baseline em gates/baseline_nucleo_compartilhado.json).
- gates/G_HARNESS_COMPAT.py: Verifica que os artefatos multi-harness da raiz (comandos, skills, arquivos-ponteiro) permanecem sincronizados entre si.
- gates/G_SEGREDOS.py: Escaneia todo o repositório rastreado pelo git em busca de credenciais hardcoded, delegando ao detect-secrets (Yelp); baseline auditado em .secrets.baseline na raiz. Em `stages: [manual]` desde 2026-09-08 — roda sob demanda, não em todo commit.
- gates/G_CLI_HELP_CONSISTENCIA.py: Compara, via AST, flags citadas em print()/raise() contra flags realmente definidas via add_argument nos pontos de entrada argparse das 4 ferramentas.
- gates/G_COMPONENTE_AGNOSTICO.py: Audita a integridade e cobertura multi-harness de todo componente novo ou modificado contra o manifesto.
- gates/G_ZERO_HEADLESS.py: Impede a execução de subagentes headless paralelos e assegura o modo interativo como rota primária e mandatória.
- gates/G_INFRA_COMPOSE.py: Audita estaticamente a integridade, sintaxe e segurança de orquestrações Docker Compose (Checkov + PyYAML).
- gates/G_HADOLINT.py: Audita estaticamente melhores práticas OCI, segurança e sintaxe de todos os Dockerfiles via Hadolint.
- gates/G_TESTES_REAIS.py: Roda pytest de verdade em cada tools/<ferramenta> e falha (exit 1) se qualquer suíte tiver failed > 0.
- gates/G_HONESTIDADE_ROTULO.py: Verifica Regra #9 — escaneia print()/raise() dos scripts de gates/ contra termos de marketing proibidos em gates/termos_proibidos_marketing.json.
- gates/G_ARQUITETURA_DELIVERABLE.py: Audita conformidade com Clean Architecture/DDD via AST. Em `stages: [manual]` (violações legadas conhecidas).
- gates/G_ESCRITOR_ATOMICO.py: Audita o uso de gravação atômica em arquivos críticos do ecossistema.
- **Execução unificada:** `python ecossistema.py audit` delega para `pre-commit run --all-files`.

**Nota (G_SEGREDOS):** movido para `stages: [manual]` em 2026-09-08, decisão explícita do usuário. Causa: inconsistência reproduzida entre `python gates/G_SEGREDOS.py` direto (aprovava) e o mesmo via hook pre-commit (reprovava), causa raiz não encontrada. Roda sob demanda: `pre-commit run --hook-stage manual g-segredos --all-files`.

**Nota (G_HONESTIDADE_ROTULO):** ainda não incluído no `audit` agregado — reprova contra violação conhecida em tools/aidd-master e aidd-enterprise `scripts/gates/G_SEGURANCA.py`, `G_ARQUITETURA.py`, `G_PERFORMANCE.py`. Pendente de decisão humana em `docs/planos/fazendo/01-correcao-pos-auditoria-sem-maquiagem/`.

---

## §4.1 — CONVENÇÃO DE NOMENCLATURA DE CÓDIGO (PT-BR / INGLÊS)

Regra de estilo para código **novo** nas 5 ferramentas. Não retroage.

- **Nomes técnicos / infraestrutura → inglês:** mecanismos genéricos de framework sem relação com regra de negócio. Ex: `SecurityGate`, `JWTService`, `MCPServer`, `CircuitBreaker`.
- **Nomes de domínio de negócio → português:** conceitos e ações do negócio que o AIDD gera. Ex: `materializar`, `dimensionar`, `reconhecer_nicho`, `sincronizar_componente`.
- **Critério prático:** se o nome faz sentido num projeto genérico qualquer → inglês. Se só faz sentido no contexto do AIDD → português.
- **Decisão:** aprovada pelo usuário em 2026-09-09.

---

## §4.2 — DIRETRIZES DE DESIGN E GOVERNANÇA PARA RELATÓRIOS HTML

Para qualquer relatório gerado em `.html` salvo em `docs/relatorios/`:
- **Scrollbars Elegantes (Máx 4px):** `width: 4px; height: 4px;`, trilho `var(--bg)`, thumb `var(--accent)`. Compatibilidade W3C + WebKit obrigatória.
- **Nomenclatura & Pareamento:** sempre `<dd-mm-aaaa>_<nome>.html` + `<dd-mm-aaaa>_<nome>.json`.
- **Geração Determinística:** nunca HTML longo no chat — executar script Python gerador.
- **Tríade Canônica:** `impeccable` + `dataviz` + `artifact-design`.
- **Guia Completo:** `docs/relatorios/DIRETRIZES-DESIGN-RELATORIOS.md`.

---

## §5 — REGRAS DE COMPATIBILIDADE MULTI-HARNESS (detalhado)

- **Claude Code / Grok:** `.claude/skills/` + `.claude/commands/` + `CLAUDE.md`.
- **OpenCode:** `.opencode/skills/<nome>/SKILL.md` (confirmado ao vivo v1.18.29). Fallback: `.claude/skills/` e `.agents/skills/`.
- **MimoCode:** `.mimocode/skills/<nome>/SKILL.md` (confirmado ao vivo v0.1.14). Fallback: `.opencode/skills/`.
- **Gemini CLI:** `.gemini/extensions/<nome>/gemini-extension.json` — mecanismo real. `.gemini/skills/` sincronizado mas `confirmado: false`.
- **Hermes Agent:** `.agents/skills` (plural) e `.hermes/skills` — requer `hermes skills trust <dir>`.
- **Antigravity (agy):** `.agents/skills/<nome>/SKILL.md` (plural) e `.agents/rules/`. `.agent/` (singular) é fallback legado.
- **Freebuff:** instalado, sem modo não interativo para validação automatizada.
- **Kiro CLI:** `.kiro/agents/` — não faz parte do padrão de skills deste ecossistema.
- **Cursor IDE:** `.cursor/rules/` (mecanismo de arquivo único).
- **Fonte física canônica:** `componentes/<ferramenta ou compartilhado>/<tipo>/`. Pastas por harness são destinos gerados por `python ecossistema.py components sync`.

> **Proveniência:** testes empíricos em 2026-09-05 contra instalações reais dos 7 harnesses nesta máquina.

---

## §MCP — MCP Tools: code-review-graph

**IMPORTANTE:** Este projeto tem knowledge graph. Use as ferramentas `code-review-graph` ANTES de Grep/Glob/Read.

| Ferramenta | Quando usar |
| ------ | ---------- |
| `detect_changes_tool` | Revisão de mudanças — análise com risk score |
| `get_review_context_tool` | Snippets de código para revisão — eficiente em tokens |
| `get_impact_radius_tool` | Blast radius de uma mudança |
| `get_affected_flows_tool` | Caminhos de execução impactados |
| `query_graph_tool` | Callers, callees, imports, tests, dependências |
| `semantic_search_nodes_tool` | Funções/classes por nome ou palavra-chave |
| `get_architecture_overview_tool` | Estrutura de alto nível do codebase |
| `refactor_tool` | Planejamento de renomes, dead code |

Fallback para Grep/Glob/Read **apenas** quando o graph não cobrir o que você precisa.
