---
name: orca-plan-orchestrator
description: Orquestrador multi-agente determinístico ORCA ADE para execução paralela de planos fatiados com git worktrees efêmeras, hooks reativos e gates locais.
---

# ORCA ADE — Plan Orchestrator

Esta skill orquestra a execução automatizada de planos fatiados (`00-PROCESSO-E-DECISOES.md` + `NN-*.md`) em qualquer projeto ou repositório.

## Capacidades

- **Parser Determinístico de Planos:** interpreta pastas de planos com frentes paralelas.
- **Ciclo de Vida Efêmero de Worktree:** isolamento estrito via `git worktree` e branches efêmeras.
- **Hooks Reativos (Zero Polling):** sinalização por eventos push e sincronismo de estado.
- **Auditoria de Gates Locais:** validação estrita (exit 0) antes de qualquer merge.
- **Circuit Breaker Anti-Loop:** proteção ativa contra travamento ou excesso de tempo/inatividade.
- **CLI e Plano de Voo Interativo:** compilação de comandos de harness, detecção de binários instalados e seleção interativa.

## Protocolo Interativo do Agente (/orchestrate)

Quando o comando `/orchestrate [plano]` for invocado:

1. **Inspeção do Plano e Estado Existente:**
   - Valide se o caminho possui `00-PROCESSO-E-DECISOES.md` e arquivos `NN-*.md`.
   - Inspecione `.orca/.orca_state.json` (se existir) para identificar frentes já no estado `MERGED`.
   - Apresente ao usuário as frentes já concluídas (que serão puladas automaticamente) e liste as frentes pendentes.

2. **Atribuição Multi-Harness Nativa por Frente (Obrigatória):**
   - NUNCA assuma um único harness global para todas as fases.
   - O harness da sessão atual (orquestrador líder) é nativamente o **Auditor dos Quality Gates** antes de cada merge.
   - Para CADA uma das frentes pendentes mapeadas, pergunte interativamente ao usuário qual harness (`claude`, `mimo`, `agy`, `opencode`) executará aquela fase específica:
     - Exemplo: "Frente 4 (SSH Runner): qual harness?"
     - Exemplo: "Frente 5 (MCPs Cloudflare/Docker): qual harness?"
     - (E assim para todas as frentes pendentes do plano).

3. **Compilação e Apresentação do Plano de Voo:**
   - Gere e apresente o Plano de Voo em tabela Markdown exibindo: Número, Nome da Frente, Branch Efêmera, Worktree, Harness Executor atribuído e Comando correspondente.

4. **Confirmação e Modo Interativo Sequencial:**
   - ⛔ **PROIBIÇÃO TOTAL DE SUBAGENTES/BACKGROUND TASKS NESTA VIA (ambiente ORCA/worktree):** É terminantemente proibido ao assistente chamar as tools `task create`, `task start`, `invoke_subagent` ou disparar tarefas em background enquanto o ambiente escolhido for ORCA/worktree.
   - O papel do assistente nesta skill encerra-se na compilação do Plano de Voo, na criação da worktree e na apresentação das instruções para o desenvolvedor executar a frente no terminal.
   - Toda execução é estritamente **sequencial (uma frente por vez)** governada no terminal pelo desenvolvedor, eliminando saturação de contexto e loops de subprocessos.
   - Existe um segundo ambiente de execução (Subagentes, via Agent tool desta sessão, sem worktree) — **não é responsabilidade desta skill**. O gate de escolha entre os dois ambientes e o protocolo do modo Subagentes vivem em `componentes/compartilhado/skills/orchestrate/SKILL.md`.

## Uso via CLI

```bash
# Modo Interativo Automático (pergunta modo interativo/headless e harness por frente)
python ecossistema.py orchestrate [plano]

# Modo Interativo direto
python ecossistema.py orchestrate [plano] --interactive

# Miscelânea por frente via CLI
python ecossistema.py orchestrate [plano] --interactive --harness-map frente1=claude,frente2=agy

# Visualizar plano de voo sem executar (Zero LLM / Zero Token)
python ecossistema.py orchestrate [plano] --dry-run
```
