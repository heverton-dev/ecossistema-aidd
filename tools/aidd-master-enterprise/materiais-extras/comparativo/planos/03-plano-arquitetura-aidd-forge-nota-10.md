# Plano de Arquitetura: AIDD Forge — Motor Universal de Governança Agêntica e Economia Extrema de Tokens

> **Novo Projeto:** `AIDD Forge` (Nome de Código: `aidd-forge`)  
> **Conceito:** Ferramenta autônoma de bootstrap e padronização que injeta em qualquer repositório a infraestrutura completa de Engenharia Agêntica, Economia Severa de Tokens, MCPs, Skills e Quality Gates mecânicos.  
> **Mecanismo de Descarte:** Orquestração de Subagentes com Descarte Imediato de Contexto (Context-Purge Engine).  
> **Tolerância a Falhas:** Auto-Descoberta de Frota de Agentes e Fallback em Cascata no ORCA ADE.  
> **Arquitetura de Isolamento:** Modularização Granular por Fase com AGENTS.md e MCPs dedicados por etapa.  
> **Interface Humana:** Zero Fricção — Disparo 100% via Slash Command (`/forge`) ou Linguagem Natural no Chat.  
> **Protocolo de Tokens:** Tríade Mandatória Caveman Ultra (Input EN / CoT English Caveman / Output PT-BR).  
> **Objetivo de Avaliação:** **Nota 10.0+ em TODAS as 5 dimensões técnicas desde o Dia 1.**

---

## 1. Visão Geral e Proposta de Valor

O **`AIDD Forge`** é o orquestrador definitivo da engenharia agêntica. Ao rodar em um projeto via `/forge` ou linguagem natural, ele:
1. Detecta dinamicamente quais agentes estão presentes no host (Auto-Descoberta de Frota).
2. Estrutura o projeto em **Micro-Ambientes de Fases Granulares** com regras e MCPs estritamente isolados.
3. Opera com **Subagentes Efêmeros**: a cognição de IA é acionada sob demanda e **a sessão do subagente é destruída imediatamente** após salvar o artefato, garantindo zero acúmulo de contexto.

---

## 2. Orquestração de Subagentes com Descarte Imediato de Contexto (Context-Purge Engine)

```
                  AIDD FORGE (Runner Maestro)
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   MECÂNICA DETERMINÍSTICA           SUBAGENTES COGNITIVOS EFÊMEROS
  (Zero Token / Python Puro)        (Cognição Sob Demanda / Descarte)
  ─────────────────────────         ─────────────────────────────────
  • Cria pastas e micro-ambientes.  • Modela contratos e requisitos.
  • Injeta symlinks e regras IDE.   • Constrói fatias de código.
  • Executa linter AST e Gates.     • Dispara post-mortem e auto-cura.
  • Controla o ciclo de vida.       • SESSÃO DESTRUÍDA APÓS CONCLUSÃO.
```

- **Ciclo de Vida Cirúrgico do Subagente:**
  * **Spawn:** Inicializado com prompt de ~800 tokens contendo unicamente o `AGENTS.md` e a `SKILL.md` daquela fase.
  * **Execução:** Produz o artefato atômico (código, schema ou teste).
  * **Verificação:** O Python valida o resultado via AST e Quality Gates (`exit 0`).
  * **Purge:** A sessão do subagente é **completamente destruída**. A próxima etapa inicia com contexto zerado.

---

## 3. Auto-Descoberta de Frota & Fallback em Cascata no ORCA ADE

O AIDD Forge nunca quebra por falta de agentes específicos no computador do usuário:

```
                              INÍCIO DO RUNNER ORCA
                                        │
                                        ▼
                      ┌────────────────────────────────────┐
                      │ 1. Auto-Descoberta de Ferramentas  │
                      │    (which claude, codex, agy, etc) │
                      └─────────────────┬──────────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
   DETECTOU MÚLTIPLOS AGENTES                             DETECTOU APENAS 1 AGENTE
(Ex: Tem Claude e Codex no host)                        (Ex: Usuário só tem Antigravity)
             │                                                     │
             ▼                                                     ▼
ROTEIA POR ESPECIALIDADE                               MODO "AGENTE ÚNICO ISOLADO"
• Arquiteto  ➔ Claude                                  • Todos os workers usam Antigravity!
• Database   ➔ Codex                                   • MAS rodam em Worktrees separadas
                                                       • Mantém o ganho de contexto limpo!
```

- **Configuração no `.env`:**
  ```env
  ORCA_DEFAULT_HARNESS=antigravity   # ou claude, codex, cursor, ollama
  ```
- Caso não configurado, o Forge auto-detecta a frota. Se o host tiver apenas 1 agente, todos os workers do Orca operam nele com isolamento de worktree, mantendo a estabilidade de 100%.

---

## 4. Modularização Granular por Fase (Phase-Level Agentic Fencing)

O comando `/forge` provisiona a árvore de micro-ambientes:
* `.aidd/pipeline/phase_00_bootstrap/`: diagnóstico e verificação de hardware.
* `.aidd/pipeline/phase_01_requirements/`: escopo e especificação semântica.
* `.aidd/pipeline/phase_02_architecture/`: modelagem de schemas JSON Draft 2020-12.
* `.aidd/pipeline/phase_03_implementation/`: Result Monad, pytest e Database MCP.
* `.aidd/pipeline/phase_04_audit_security/`: auditoria cega OWASP Top 10.

---

## 5. Interface Humana Zero Fricção (Zero Terminal Barrier)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CANAL DE ENTRADA ZERO FRICÇÃO                                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. SLASH COMMANDS NATIVOS (No Chat da IDE / Harness)                                   │
│    • `/forge` ou `/aidd-init`                                                          │
│    • Configura todo o ecossistema agêntico com um único toque.                         │
│                                                                                        │
│ 2. DISPARO POR LINGUAGEM NATURAL (Intent Router no AGENTS.md)                          │
│    • "prepare o ambiente", "configure este projeto com aidd", "blinde as regras"       │
│    • O agente reconhece a intenção semântica e roda o setup automaticamente.          │
│                                                                                        │
│ 3. EXECUTÁVEL DE 1-CLIQUE (Desktop / Duplo Clique)                                     │
│    • Windows: `setup.bat` ➔ Executa o bootstrap em 3 segundos sem abrir prompt preto.  │
│    • Linux/Mac: `setup.sh` ➔ Configuração silenciosa via script executável.            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Protocolo Tríplice Caveman Ultra de Economia Severa de Tokens

1. **ENTRADA (System Prompts em Inglês):** Economia de 30% a 50% de tokens de BPE.
2. **PROCESSAMENTO (Internal Thinking em English Caveman):** CoT ultra-denso (3 a 5 linhas no máximo): *"inspect files, verify gate, impl clean slice, test exit 0"*.
3. **SAÍDA / OUTPUT (Português do Brasil - PT-BR de Alta Qualidade):** Comunicação, artefatos e código entregues em PT-BR, com Result Monad e sem stubs.

---

## 7. Estrutura Completa do Repositório `aidd-forge`

```
aidd-forge/
├── aidd_forge/
│   ├── __init__.py
│   ├── cli.py                     # Entrypoint CLI: forge init
│   ├── commands/
│   │   └── slash_router.py        # Processador de Slash Commands (/forge) e Intent Router
│   ├── core/
│   │   ├── detector.py            # Diagnóstico de SO, Git, Python e auto-descoberta de frota
│   │   ├── injector.py            # Motor determinístico de injeção de arquivos e symlinks
│   │   ├── phase_fencer.py        # Provedor de micro-ambientes granulares por fase
│   │   ├── subagent_purger.py     # Engine de descarte imediato de contexto de subagentes
│   │   ├── token_optimizer.py     # Gerador de regras de economia extrema (Caveman Ultra)
│   │   └── orca_bridge.py         # Compilador de planos e scripts Bash com fallback
│   ├── templates/
│   │   ├── governance/
│   │   │   ├── AGENTS.md          # Fonte única da verdade com Slash Commands mapeados
│   │   │   ├── AGENTS-WORKFLOW.md # Cadência operacional obrigatória
│   │   │   ├── LEI-FUNDAMENTAL-TRANSPARENCIA.md
│   │   │   └── PLANO-EXECUCAO-ESTRUTURADO.json # Template de saga e estado
│   │   ├── pipeline_phases/       # Templates granulares de fases com AGENTS/MCPs dedicados
│   │   ├── orca/
│   │   │   ├── 01_orca_inventory.json
│   │   │   ├── 02_routing_rules.json
│   │   │   ├── 04_gate_policies.json
│   │   │   └── 05_orchestrate_plan.sh
│   │   ├── skills/
│   │   │   ├── caveman-ultra/SKILL.md
│   │   │   ├── orca-orchestration/SKILL.md
│   │   │   ├── impeccable-ui/SKILL.md
│   │   │   ├── open-code-review/SKILL.md
│   │   │   ├── post-mortem/SKILL.md
│   │   │   └── cybersecurity-audit/SKILL.md
│   │   └── gates/
│   │       ├── G_BLOQUEAR_SEGREDOS.py
│   │       ├── G_ESTRUTURA_AST.py
│   │       ├── G_HARNESS_COMPAT.py
│   │       ├── G_CONTRACTS.py
│   │       ├── G_CYBERSECURITY_OWASP.py
│   │       └── G_TESTES_REAIS.py
├── setup.bat                      # Executável de 1-Clique para Windows
├── setup.sh                       # Executável de 1-Clique para Linux/Mac
├── setup.py                       # Instalação via pip (pip install -e .)
└── README.md                      # Manual: "Use /forge no chat ou dê duplo clique no setup.bat"
```

---

## 8. Cronograma de Execução

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   CRONOGRAMA DE ELEVAÇÃO: AIDD FORGE ➔ NOTA 10.0+                │
├──────────────────────────────────────────────────────────────────────────────────┤
│ SPRINT 1: Engine de Subagentes Efêmeros com Descarte Imediato de Contexto        │
│ SPRINT 2: Auto-Descoberta Dinâmica de Frota & Fallback Universal no ORCA         │
│ SPRINT 3: Reestruturação Granular por Fase (Micro-Ambientes com AGENTS/MCPs)    │
│ SPRINT 4: Camada Zero Fricção (Slash Commands /forge + Intent Router)            │
│ SPRINT 5: Protocolo Tríplice Caveman Ultra nos Prompts (Input EN / CoT / PT-BR)  │
│ SPRINT 6: Injeção das 6 Skills Físicas Especializadas (.skills/)                 │
│ SPRINT 7: Blindagem de 7 Quality Gates Mecânicos + Gate de Cibersegurança OWASP │
└──────────────────────────────────────────────────────────────────────────────────┘
```
