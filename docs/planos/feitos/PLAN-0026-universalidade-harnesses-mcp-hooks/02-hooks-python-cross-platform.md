# 02 — Hooks Python Cross-Platform

> **Iniciativa:** PLAN-0026-universalidade-harnesses-mcp-hooks
> **Foco:** Substituir hooks puramente bash (.sh) por scripts Python nativos e compatíveis com Windows, Linux e macOS.

---

## 1. Diagnóstico e Problema

Os hooks do grafo (`.gemini/hooks/crg-update.sh` e `crg-session-start.sh`) foram implementados apenas em shell script Unix. No Windows, o harness opera em PowerShell nativo, impedindo a execução e atualização contínua do grafo do `code-review-graph`. Além disso, não há integração no ciclo de vida de commit git (`.githooks`).

## 2. Definição de Pronto

1. Criar scripts agnósticos em Python em `componentes/compartilhado/hooks/`:
   - `crg_update.py` (atualiza o grafo com `code-review-graph update` de forma resiliente)
   - `crg_session_start.py` (garante a inicialização e integridade do grafo no início da sessão)
2. Criar wrappers executáveis universais e configurar `.githooks` e os manifests dos harnesses.
3. Propagar para os harnesses via `python ecossistema.py components sync`.
