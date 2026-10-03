---
name: aidd-anatomy
description: Extracts and documents the complete technical anatomy of an ecosystem target (pipeline, tool, or component) producing both Markdown and visual HTML artifacts in docs/anatomias/anatomia-<target>/. Use when dissecting a target, or when the user asks for "anatomia", "/anatomia", "desmontar ferramenta", "anatomia do alvo", "analisar anatomia", or "anatomia do pipeline".
---

# aidd-anatomy

Deterministic inspection manual to dissect any ecosystem target (tool, pipeline, or component) and generate coupled Markdown and HTML visual artifacts.

## Protocol

1. **Target and Version Resolution:**
   - Determine target slug `<target>` (e.g. `orquestrador-4f`, `aidd-evolution`, `aidd-orchestrate`).
   - Determine target version `<version>` (default `v1`, increment if `docs/anatomias/anatomia-<target>/anatomia-v1-<target>.md` exists).
   - Resolve destination directory: `docs/anatomias/anatomia-<target>/`. Create if missing.

2. **Factual Evidence Collection (Strict Hierarchy):**
   - **Step 2.1 (Knowledge Graph):** Query `codebase-memory-mcp` (`search_graph`, `trace_path`, `query_graph`, `get_architecture`) for definitions, callers, callees, and dependencies.
   - **Step 2.2 (Canonical Docs):** Read relevant living docs in `docs/protocolos/`, `AGENTS.md`, and active schemas.
   - **Step 2.3 (Target Source Path):** Inspect source files directly in `tools/`, `scripts/`, or `componentes/`.
   - **Step 2.4 (Ecosystem CLI):** Verify command-line wiring in `ecossistema.py`.

3. **Mandatory Sections (Markdown and HTML):**
   Both artifacts (`anatomia-<version>-<target>.md` and `anatomia-<version>-<target>.html`) must contain:
   - **1. CARTÃO DE IDENTIDADE (NO EMOJIS):** Structured block containing:
     - `nome do alvo` | `finalidade` | `nível de maturidade` | `trava principal` | `comando acionador` | `localização`
   - **2. FLUXO DE EXECUÇÃO:** Sequential execution steps (Step 1 -> Step 2 -> ...), including gates, hooks, handoff files, and preconditions.
   - **3. ESTEIRA VISUAL COM BLOCOS:** Explicit blocks showcasing `Entrada ➔ Processo ➔ Trava ➔ Saída`.
   - **4. DESTAQUE EM NEGRITO NO PRIMEIRO VERBO:** Every step or bullet item MUST start with an active bold verb (e.g., **Executa**, **Valida**, **Compila**, **Isola**, **Bloqueia**) to enable instant diagonal scanning.
   - **5. DEFEITOS E LIMITAÇÕES:** Real architectural flaws, coupling bottlenecks, and operational constraints.
   - **6. BOXES DE DESTAQUE NATIVOS:** Standard GitHub alerts:
     - `> [!WARNING]` for defects and operational risks.
     - `> [!TIP]` for practical architectural recommendations.

4. **HTML Styling Standards:**
   - The `.html` file must adhere strictly to the visual tokens of `docs/mapas-visuais/`:
     - Fonts: Bricolage Grotesque (display), IBM Plex Sans (body), IBM Plex Mono (code).
     - Palette: `--paper`, `--surface`, `--ink`, `--muted`, `--line`, `--brick`, `--tint`.
     - Containers: `.wrap` (max-width 1040px), `.box`, `.chip`, `.passos`, `.grid2`, `.nota`.
     - Support light and dark theme variables.

5. **Artifact Generation:**
   - Write Markdown: `docs/anatomias/anatomia-<target>/anatomia-<version>-<target>.md`.
   - Write HTML: `docs/anatomias/anatomia-<target>/anatomia-<version>-<target>.html`.

6. **Terminal Output Constraint:**
   - Emit exactly one line in chat upon completion:
     `ARTEFATOS GERADOS EM: docs/anatomias/anatomia-<alvo>`

## Negative Guardrails

- NEVER overwrite an existing `anatomia-v<N>-<target>.md` or `.html`; bump the version (example: `docs/anatomias/anatomia-orquestrador-4f/`).
- NEVER fill DEFEITOS E LIMITAÇÕES from memory or reading alone; each defect cites a file:line or a command you ran.
- NEVER skip Step 2.1: query `codebase-memory-mcp` before grep or full-file reads (Law #14).
- NEVER hand-roll HTML outside the `docs/mapas-visuais/` tokens; render through `salvar_anatomia_html` in `scripts/gerar_anatomia_html.py`.
- NEVER print more than the single `ARTEFATOS GERADOS EM:` line in chat.

## Failure Modes & Fallback

- **No graph project for this worktree:** use the main repo project from `codebase-memory-mcp:list_projects`, confirm each path on disk, and say so in DEFEITOS E LIMITAÇÕES.
- **`KeyError` from `HTML_TEMPLATE.format`:** a key is missing in the data dict; add it, never edit the template.
- **Target slug ambiguous (tool vs pipeline):** ask the user which one; never create two folders.

## Stopping Checklist

Exit codes go to a file, never through a pipe: `<cmd> > "$TEMP/an.log" 2>&1; echo $? > "$TEMP/an.rc"`.

- [ ] Both `docs/anatomias/anatomia-<target>/anatomia-<version>-<target>.md` and its `.html` exist (`test -e` rc 0).
- [ ] Both files carry the 6 mandatory sections (`grep -c "DEFEITOS E LIMITAÇÕES"` is at least 1 per file).
- [ ] No earlier version changed (`git diff --stat docs/anatomias/` is empty; only new files in `git status`).
- [ ] Chat output is the single line.
