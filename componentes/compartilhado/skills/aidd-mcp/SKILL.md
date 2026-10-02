---
name: aidd-mcp
description: Builds a new Model Context Protocol (MCP) server that ships inside an ecosystem tool or generated product, with its single source in componentes/<scope>/mcps/<name>/ and distribution through components sync. Use when the user wants to create or change an own MCP server, or says "criar MCP", "novo servidor MCP", "expor ferramenta via MCP". Not for third-party MCPs the agent consumes (that is aidd-dependencies).
---

# aidd-mcp

Thin coordinator: it does not reimplement the MCP protocol. Third-party MCPs the agent uses to work here (Playwright, GitHub, Context7, code-review-graph) belong to `aidd-dependencies`.

## Protocol

1. **Find the active harness and its capabilities.** If it has a native MCP authoring tool, use it to decide tools/resources, input/output schemas and error handling. Done when the server design is decided.
2. **Without a native tool**, build on the Python libraries already in the ecosystem (`mcp`/`fastmcp`; check `pip show fastmcp` before installing again) instead of hand-written JSON-RPC 2.0. Read an existing server first as a structural reference: `tools/aidd-ops/mcps/cloudflare-mcp/server.py` or `tools/aidd-pure/mcps/mcp-verificador-cve/`.
3. **Write the source only in** `componentes/<tool or compartilhado>/mcps/<name>/server.py` (plus its own `requirements.txt`/README when needed), never in a harness folder.
4. **Keep the contract valid:** tool, resource and prompt schemas compatible with the MCP specification.
5. **Distribute and confirm:**
   ```bash
   python ecossistema.py components sync --tipo mcp --ferramenta <tool or compartilhado>
   python ecossistema.py components verify --tipo mcp
   ```
   Done when verify exits 0; report success only then.
6. **Secrets:** never ask for or write a secret or API key in the server or the commit. Expose only the environment variable **name** and document in the MCP README that the user exports the real value on their machine.

Edit an existing MCP in `componentes/` and resync; never edit the copies in `.claude/`, `tools/<x>/.claude/` etc.
