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

4. **Confirmação e Disparo:**
   - Aguarde a confirmação explícita do usuário para disparar a execução determinística da orquestração.

## Uso via CLI

```bash
# Modo Interativo Automático (detecta harnesses instalados no sistema e pergunta ao usuário)
python ecossistema.py orchestrate [plano]

# Visualizar plano de voo sem executar (Zero LLM / Zero Token)
python ecossistema.py orchestrate [plano] --dry-run

# Executar direto com harness específico (modo não-interativo)
python ecossistema.py orchestrate [plano] --harness claude --yes
```
