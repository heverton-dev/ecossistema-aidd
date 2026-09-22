---
id: ISSUE-USA-0003
title: Entrega fora do clone e aninhamento achatado (A4)
status: open
blocked_by: [ISSUE-USA-0002]
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A4)
---

# ISSUE-USA-0003 — Entrega fora do clone e aninhamento achatado (A4)

**Deliver:** Generated project lands as a flat sibling of the user’s legacy app (or at workspace root), not buried 4 levels under `ecossistema-aidd/projetos/<app>/proj_<app>/`. User always sees one delivery card.

**Blocked by:** ISSUE-USA-0002.

## Scope

1. Use `resolve_pasta_entrega()` as the only path source (no local defaults).
2. Flatten layout — eliminate redundant `proj_` prefix and extra nesting layer:
   - PROHIBITED: `.../ecossistema-aidd/projetos/<app>/proj_<app>/{src,frontend}`
   - REQUIRED: `<pasta_entrega>/<app>/{src,frontend,tests,docker}`
3. End-of-flow delivery card (PT-BR simple, first line is path):
   ```
   === SEU APP ESTÁ PRONTO ===
   Onde está:  <caminho_absoluto>
   Como subir:  <um_comando_copiavel>
   Abrir:       http://localhost:<porta>
   Guia:        <caminho>/README-USUARIO.md
   ```
4. `git init` at delivery root (or one manual command printed) — closes the “no versionable delivery” half of A8 wiring.
5. Integration test: synthetic “clone inside existing project” fixture asserts output path is workspace root, not `projetos/`, and card contains absolute path.

## Acceptance criteria

- [ ] No `proj_` prefix and no double `<app>/<app>` nesting in generated trees.
- [ ] Delivery card emitted on success; missing card = ticket incomplete.
- [ ] Ambiguous layout still stops and asks (from ISSUE-USA-0002) — never silent `projetos/`.
- [ ] E2E fixture: legacy sibling present ⇒ delivery at workspace root.
- [ ] `python ecossistema.py audit` exit 0.
