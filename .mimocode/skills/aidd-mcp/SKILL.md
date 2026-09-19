---
name: aidd-mcp
description: Scaffolds and exposes new Model Context Protocol (MCP) servers across harnesses.
---

# AIDD MCP — Criador e Integrador de Servidores MCP

Esta skill constrói novos servidores Model Context Protocol (MCP) integrados às ferramentas do ecossistema e aos produtos gerados, garantindo fonte única em `componentes/<ferramenta ou compartilhado>/mcps/<nome>/`.

## Protocolo ao ser acionada

1. **Estrutura Canônica:**
   Gera o servidor MCP em Python ou Node.js dentro de `componentes/<escopo>/mcps/<nome>/server.py`.
2. **Sincronização Multi-Harness:**
   Executa:
   ```bash
   python ecossistema.py components sync --tipo mcp
   python ecossistema.py components verify --tipo mcp
   ```
3. **Validação do Contrato:**
   Garante schemas de tools, resources e prompts compatíveis com a especificação MCP 2024-11-05.
