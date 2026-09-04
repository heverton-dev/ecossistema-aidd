# 🏛️ AGENTS.md — Governança Canônica do Ecossistema AIDD Unificado

> **Repositório:** https://github.com/heverton-dev/ecossistema-aidd  
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)  
> **Lei Fundamental:** Transparência Total, Determinismo Estrito, Zero Stubs, Economia Extrema de Tokens.

---

## 1. VISÃO GERAL DO ECOSSISTEMA

O **Ecossistema AIDD** unifica 4 ferramentas complementares de Engenharia Agêntica de Software em um monorepo modular e desacoplado:

| Ferramenta | Diretório | Papel Principal | Slash Command |
| :--- | :--- | :--- | :--- |
| **AIDD Forge** | 	ools/aidd-forge | Bootstrap, micro-ambientes isolados, fatiamento de fases e purge de contexto | /forge [caminho] |
| **AIDD Generator** | 	ools/aidd-generator | Fábrica autônoma de software (Pipeline 8 fases a partir de ideia natural) | /generate <ideia> |
| **AIDD Master** | 	ools/aidd-master | Suíte modular com Clean Architecture, Fatias Verticais e SQLite WAL | /master <modulo> |
| **AIDD Master Enterprise** | 	ools/aidd-master-enterprise | Plataforma de Missão Crítica com Injeção de Componentes SHA-256 e Zero-Trust | /enterprise <tipo> <nome> |

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

---

## 4. AUDITORIA E META-QUALITY GATES

O ecossistema dispõe de Quality Gates globais em gates/:
- gates/G_ECOSSISTEMA_INTEGRIDADE.py: Audita a integridade física, sintática e estrutural dos 4 subprojetos e das skills.
- gates/G_DRIFT_NUCLEO_COMPARTILHADO.py: Detecta divergência não documentada entre os arquivos de núcleo compartilhados por linhagem entre aidd-master e aidd-master-enterprise (baseline em gates/baseline_nucleo_compartilhado.json).
- gates/G_HARNESS_COMPAT.py: Verifica que os artefatos multi-harness da raiz (comandos, skills, arquivos-ponteiro) permanecem sincronizados entre si.
- gates/G_SEGREDOS.py: Escaneia todo o repositório rastreado pelo git em busca de credenciais hardcoded (allowlist auditada em gates/allowlist_segredos.json).
- Execução unificada via CLI: python ecossistema.py audit (roda os 4 gates em sequência)

---

## 5. REGRAS DE COMPATIBILIDADE MULTI-HARNESS

- **Antigravity / MimoCode / OpenCode:** Carrega definições em .agent/commands/ e .agent/skills/.
- **Claude Code:** Carrega comandos em .claude/commands/ e lê CLAUDE.md.
- **Cursor IDE:** Carrega regras a partir de .cursor/rules/.
- **Raiz Canônica:** Todos os harnesses convergem para as definições canônicas de AGENTS.md e da CLI ecossistema.py.
