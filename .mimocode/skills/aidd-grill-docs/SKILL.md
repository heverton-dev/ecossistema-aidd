---
name: aidd-grill-docs
description: Socratic interview grounded in existing repository architecture, domain documentation, and invariant rules. Use when a change must be checked against MEMORY.md, AGENTS.md laws or domain docs before coding, or the user says "grill com docs", "confrontar com a arquitetura".
---

# AIDD-Grill-Docs — Architecture-Grounded Interview

Grounded variation of `aidd-grill` (same numbered rounds with recommended answers) strictly anchored in the repository's documentation and architectural constraints.

## Execution Rules

1. **Context Ingestion:** Briefly inspect canonical project context files (`AGENTS.md`, `MEMORY.md`, and `docs/`) before querying. When present, read the glossary `CONTEXT.md` and the decision records in docs/adr/ (optional folder; may not exist yet).
2. **Ubiquitous Language:** Strictly enforce established domain terminology (e.g., Vertical Slice, Quality Gates, Harnesses, Result Monad). When the user resolves a term, update the glossary in `CONTEXT.md` (propose the diff; ambiguous terms stay flagged until the user decides).
3. **Detect Architectural Violations:** Interrogate any request threatening:
   - Inviolable Laws (Determinism, Zero Stubs, Extreme Token Economy).
   - Module isolation and bounded context boundaries.
   - Schema conventions, database WAL pragma, or API contract standards.
4. **Concrete Evidence Queries:** Cite specific documentation paths when highlighting discrepancies: *"Doc X establishes Y, but request proposes Z. Which direction takes precedence?"*.
5. **Completion Gate:** Once architectural compliance is verified, route directly to `/aidd-spec`.

## Negative Guardrails

- NEVER cite a law or doc you did not open in this session; every discrepancy names a real path (`AGENTS.md`, `MEMORY.md`, `CONTEXT.md`, `docs/adr/`).
- NEVER write `CONTEXT.md` before the user resolves the term; propose the diff and keep the term under "Ambiguidades sinalizadas".
- NEVER let pass a request that edits generated copies (`.claude/skills/`, `.agents/skills/`) instead of `componentes/`, or that adds an LLM API key; flag both as law violations.
- NEVER decide alone whether the doc or the request takes precedence; ask the user.

## Failure Modes & Fallback

- **Doc missing (`docs/adr/` empty, `CONTEXT.md` absent):** say so and fall back to `AGENTS.md` plus the code; never invent a rule.
- **Two docs disagree:** quote both paths and lines, ask which one is canonical, record the answer as a proposed `CONTEXT.md` or ADR diff.
- **Another session is editing `AGENTS.md` or `CONTEXT.md`:** run `git status` first; if the file changed, stop and ask.

## Stopping Checklist

Exit codes go to a file, never through a pipe: `<cmd> > "$TEMP/gd.log" 2>&1; echo $? > "$TEMP/gd.rc"`.

- [ ] Each discrepancy cites a path that exists (`test -e <path>` wrote rc 0).
- [ ] Every new term is resolved by the user or listed as ambiguous.
- [ ] `git diff --stat CONTEXT.md` shows only changes the user approved.
- [ ] Handoff to `/aidd-spec` named; no code written.
