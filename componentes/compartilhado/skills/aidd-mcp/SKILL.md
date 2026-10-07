---
name: aidd-mcp
description: Builds a new Model Context Protocol (MCP) server that ships inside an ecosystem tool or generated product, with its single source in componentes/<scope>/mcps/<name>/ and distribution through components sync --tipo todos. Use when the user wants to create or change an own MCP server, or says "criar MCP", "novo servidor MCP", "expor ferramenta via MCP". Not for third-party MCPs the agent consumes (that is aidd-dependencies).
---

# aidd-mcp

Thin coordinator: it does not reimplement the MCP protocol. Third-party MCPs the agent uses to work here (Playwright, GitHub, Context7, codebase-memory-mcp) belong to `aidd-dependencies`.

## Protocol

1. **Find the active harness and its capabilities.** If it has a native MCP authoring tool, use it to decide tools/resources, input/output schemas and error handling. Done when the server design is decided.
2. **Without a native tool**, build on the Python libraries already in the ecosystem (`mcp`/`fastmcp`; check `pip show fastmcp` before installing again) instead of hand-written JSON-RPC 2.0. Read an existing server first as a structural reference: `modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/mcps/cloudflare-mcp/server.py` or `modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/mcps/mcp-verificador-cve/`.
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

## Negative Guardrails

- NEVER hand-write JSON-RPC 2.0 framing when `fastmcp`/`mcp` is installed (`pip show fastmcp`).
- NEVER treat the shipped copies under `modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/mcps/` or `tools/<x>/.claude/` as the source; `components sync --tipo mcp` overwrites them.
- NEVER read an LLM API key inside `server.py` or call a model from a tool: the server exposes deterministic tools and the calling harness is the model.
- NEVER hardcode a token in `server.py`, its README or tests; read `os.environ["<NAME>"]` and fail with a clear message when it is absent (`G_SEGREDOS` scans the source).
- NEVER register an own server through `dependencia add-mcp` as if it were third-party; that path belongs to `aidd-dependencies`.

## Failure Modes & Fallback

- **`components verify --tipo mcp` exits 1:** the copy differs from `componentes/<scope>/mcps/<name>/`; resync with `--ferramenta <scope>` and verify again, never patch the copy.
- **Server crashes at startup on a missing env var:** keep the crash explicit, document the variable name in the MCP README, and ask the user to export it; never add a default secret.
- **No reference server under `componentes/`:** `componentes/compartilhado/mcps/` holds only `.gitkeep` today; read `modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/mcps/cloudflare-mcp/server.py` for structure and still write the new source under `componentes/`.

## Stopping Checklist

- [ ] Source exists: `test -f componentes/<scope>/mcps/<name>/server.py; echo $? > mcp_src.rc` holds `0`.
- [ ] `python -m py_compile componentes/<scope>/mcps/<name>/server.py; echo $? > mcp_compile.rc` holds `0`.
- [ ] `python ecossistema.py components verify --tipo mcp > mcp_verify.txt 2>&1; echo $? > mcp_verify.rc` holds `0`.
- [ ] `python gates/G_SEGREDOS.py > seg.txt 2>&1; echo $? > seg.rc` holds `0`.
