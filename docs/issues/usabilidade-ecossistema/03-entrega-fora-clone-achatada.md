---
id: ISSUE-USA-0003
title: Entrega fora do clone e aninhamento achatado (A4)
status: done
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

- [x] No `proj_` prefix and no double `<app>/<app>` nesting in generated trees — `provision_project.py` (master+enterprise) e `cmd_init` achatados; `test_provision_project` 13/13 + `test_entrega_achatada` 4/4.
- [x] Delivery card emitted on success; missing card = ticket incomplete — `_fechar_entrega()` no orquestrador (card `=== SEU APP ESTÁ PRONTO ===`).
- [x] Ambiguous layout still stops and asks (from ISSUE-USA-0002) — never silent `projetos/`.
- [x] E2E fixture: legacy sibling present ⇒ delivery at workspace root — coberto em `test_g_layout_entrega.py` / `resolve_pasta_entrega`.
- [x] `python ecossistema.py audit` exit 0 — `G_LAYOUT_ENTREGA`, `G_DISCIPLINA_TESTE_FERRAMENTA` (relatório §11), `G_DRIFT_NUCLEO_COMPARTILHADO`, `G_IDIOMA_LEI_4` exit 0; suíte 26/26.
