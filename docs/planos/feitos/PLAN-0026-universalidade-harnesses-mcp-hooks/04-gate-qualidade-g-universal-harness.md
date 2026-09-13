# 04 — Gate de Paridade Universal

> **Iniciativa:** PLAN-0026-universalidade-harnesses-mcp-hooks
> **Foco:** Criar teste binário automatizado (Exit 0 = Pass, Exit 1 = Reject) para validar a paridade de skills, configs MCP e hooks entre todos os harnesses.

---

## 1. Diagnóstico e Problema

Sem um gate binário automatizado, drifts silenciosos entre harnesses reaparecem com facilidade. É preciso um guardrail que falhe imediatamente se um harness tiver uma skill faltando, se as configs MCP divergirem da declaração canônica ou se houver scripts de hooks não agnósticos.

## 2. Definição de Pronto

1. Criar `gates/G_UNIVERSAL_HARNESS.py`:
   - Verifica simetria de skills em todos os 7 harnesses suportados.
   - Verifica presença de configurações MCP geradas (`.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, etc.).
   - Valida que hooks registrados são executáveis multiplataforma (Python).
2. Adicionar o gate à suíte de auditoria em `ecossistema.py audit`.
