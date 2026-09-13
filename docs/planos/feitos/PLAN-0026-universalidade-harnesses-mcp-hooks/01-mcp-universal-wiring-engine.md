# 01 — MCP Universal Wiring Engine

> **Iniciativa:** PLAN-0026-universalidade-harnesses-mcp-hooks
> **Foco:** Gerar e sincronizar deterministicamente as configurações de MCP para todos os harnesses suportados.

---

## 1. Diagnóstico e Problema

Atualmente, `gates/manifesto_harnesses.json` não realiza a distribuição ou geração das configurações de MCP (`.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, e a pasta de MCPs do Antigravity CLI). Como resultado, o `code-review-graph` e outros servidores MCP ficam disponíveis apenas em harnesses que leram um arquivo específico, deixando o Antigravity CLI e outros sem as ferramentas de grafo.

## 2. Definição de Pronto

1. Criar `scripts/mcp_universal_sync.py` consumindo `gates/dependencias_externas.json` e fontes de MCP canônicas.
2. Gerar de forma determinística:
   - `.mcp.json` (Claude Code / OpenCode / Kiro)
   - `.cursor/mcp.json` (Cursor)
   - `.vscode/mcp.json` (VS Code)
   - Ferramentas/schemas para Antigravity CLI sob `~/.gemini/antigravity-cli/mcp/` ou configuração em `.agents/mcp_config.json`.
3. Garantir que `code-review-graph` esteja devidamente configurado e operacional em todos esses harnesses.
4. Integrar o comando no CLI do ecossistema: `python ecossistema.py mcp sync`.
