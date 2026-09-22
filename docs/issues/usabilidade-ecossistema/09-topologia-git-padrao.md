---
id: ISSUE-USA-0009
title: Topologia Git padrão documentada e aplicada (A8)
status: open
blocked_by: [ISSUE-USA-0003]
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A8)
---

# ISSUE-USA-0009 — Topologia Git padrão documentada e aplicada (A8)

**Deliver:** Clear Git boundaries: delivery root is versionable; tool history never pollutes the user’s product repo.

**Blocked by:** ISSUE-USA-0003 (delivery root / `git init` wiring).

## Scope

1. Standard topology (spec §2.9):
   ```
   <workspace-usuario>/   ← git init HERE (versionable delivery root)
   ├── proj_legado/       ← subtree OR own repo (declared)
   ├── <app_gerado>/      ← subtree of same repo (default)
   └── (ecossistema-aidd/)← tool OUTSIDE delivery; if present, sparse/shallow only
   ```
2. Auto `git init` at delivery root when missing (already partially in ISSUE-USA-0003); if repo exists, do not nest a second one silently.
3. Nested-tool guard: refuse/warn when creating a Git repo inside the tool clone that would split product history (`ecossistema-aidd` + `projetos/*` + `proj_*` triple).
4. Mini-livro: 5-line standard topology note (`docs/livros/partes/02-fluxos.md` or equivalent).
5. E2E usability case: delivery root has exactly one product `.git`; tool history not mixed.

## Acceptance criteria

- [ ] Delivery root has a single `.git` for the product (or explicit warning + manual command).
- [ ] No silent triple-repo nesting in generated workspaces.
- [ ] Mini-livro states the 5-line topology standard.
- [ ] E2E case asserts one product repo at delivery root.
- [ ] `python ecossistema.py audit` exit 0.
