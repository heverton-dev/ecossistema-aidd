---
name: aidd-evolucao-runner
description: "Motor agnóstico do Pipeline de Evolução Técnica gerado a partir do Plano de Evolução. Executa fases sequenciais de tickets em Git Worktrees efêmeras."
---

# `aidd-evolucao-runner` (AIDD Pipeline de Evolução)

Este motor orquestra a execução sequencial dos tickets de evolução técnica gerados pelo Arquiteto na Fase 2 da auditoria, implementando código e testes em Git Worktrees efêmeras com isolamento estrito.

## Invariância e Agnosticismo
1. **OS Agnostic:** Os scripts e shells utilizam `os.path.join` e chamadas cross-platform, garantindo sucesso em Windows, Linux e Mac.
2. **Harness/LLM Agnostic:** A injeção de `harness`, `model` e `comando_terminal` é resolvida dinamicamente a partir de `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`.
3. **Omni-Ativação (Tríplice Ativação Canônica):** 
   - **Terminal (CLI):** `python ecossistema.py evolucao <tool-name>` ou `python ecossistema.py evolucao --manifest <path.json>`
   - **Slash Command:** `/evolucao <tool-name_ou_json>` ou `/aidd-evolucao <tool-name>`
   - **Natural Language:** "Execute a evolução da ferramenta X", "rode o pipeline de evolução", "evolua a ferramenta X a partir do plano".

## Estrutura de Entrada e Saída
- **Origem dos Tickets:** `docs/auditoria/<ferramenta-alvo>/ciclo-NN/PLANO-EVOLUCAO.md` (ciclo vigente) compilado deterministicamente para `docs/auditoria/<ferramenta-alvo>/ciclo-NN/PLANO-EVOLUCAO.json`.
- **Configuração de Execução:** `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`.
- **Áreas de Trabalho:** Git Worktrees efêmeras isoladas geradas em `../worktrees_evolucao-<ferramenta>/`.
- **Destino do Código:** `.agents/skills/<ferramenta>/scripts/` e `tests/`.

## Fluxo de Execução Estrita
1. O Runner intercepta o manifesto JSON de evolução (ex: `docs/auditoria/<tool-name>/ciclo-NN/PLANO-EVOLUCAO.json`).
2. Para cada ticket do plano:
   - Isola uma Git Worktree efêmera na branch `evolucao/<tool-name>/<ticket_nome>`.
   - Lê a especificação do ticket (`input_prompt`).
   - Dispara o agente configurado com TTY interativo e monitoramento térmico do Watchdog.
   - Aguarda a entrega do artefato esperado (`output_handoff`).
   - Valida a suite de testes associada (`pytest tests/`).
   - Comita e descarta a worktree temporária.
   - Executa merge cumulativo na branch principal.
3. Ao finalizar todos os tickets:
   - Emite barreira de decisão humana (Join Barrier).
   - Registra o encerramento em `RESUMO-USUARIO.md` e `RELATORIO-TECNICO.md`.

## Disparo
Quando acionado via linguagem natural ou slash, este agente DEVE identificar a ferramenta alvo, verificar a existência de `PLANO-EVOLUCAO.json` (compilando-o a partir do Markdown caso ainda não exista), confirmar a preferência de Harness/Model do usuário e acionar o comando de terminal do ecossistema.
