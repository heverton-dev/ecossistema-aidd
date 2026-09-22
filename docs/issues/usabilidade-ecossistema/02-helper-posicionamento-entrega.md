---
id: ISSUE-USA-0002
title: Helper determinístico de posicionamento da entrega (A6)
status: done
blocked_by: []
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A6)
---

# ISSUE-USA-0002 — Helper determinístico de posicionamento da entrega (A6)

**Deliver:** Root-cause fix for doc×runtime divergence: one deterministic `resolve_pasta_entrega()` used by all triad flows, with Law #13 gate. Books (`--pasta ../proj`) and runtime stop disagreeing.

**Blocked by:** nothing. Start now. Conceptually before ISSUE-USA-0003.

## Scope

1. Implement shared helper (suggested `core/resolve_pasta_entrega.py` or existing core util module):
   ```python
   def resolve_pasta_entrega(cwd: Path, nome_projeto: str, pasta_arg: str | None = None) -> Path
   ```
   Rules (from `docs/melhorias/22-09-2026_especificacao-tecnica-usabilidade-ecossistema.md` §2.2):
   - Explicit `--pasta` always wins.
   - Legacy sibling present (`package.json` | `src/` | `app/` | `backend/` outside tool dirs) → default = user workspace root, NEVER `<clone>/projetos/`.
   - Ecosystem-only CWD → default = `<clone>/projetos/<slug>`.
   - Ambiguity → structured error with 2 PT-BR options; zero disk writes (Law #7).
2. Wire helper into Fluxo 01/02/03 entrypoints (generator/factory/bridge path resolution only — no engine rewrite).
3. Unit tests: sibling-legacy, ecosystem-only, explicit `--pasta`, ambiguous (expects structured error).
4. Gate `gates/G_LAYOUT_ENTREGA.py`: fail when generated project lands under `<clone>/projetos/` while a legacy sibling exists.
5. Bite test `gates/test_g_layout_entrega.py`: nested-layout fixture asserts exit 1.
6. Update `docs/livros/partes/02-fluxos.md` (or equivalent) with the real scenario “cloned inside existing project → what happens”.

## Acceptance criteria

- [x] Helper covered by unit tests including ambiguity (exit path, no writes) — `gates/test_g_layout_entrega.py` 7/7 (legacy, tool-only, explicit `--pasta`, ambiguity zero-writes).
- [x] All three flows call the same helper (no duplicated path logic) — `scripts/orquestrador_sincrono.py` (entry de pure/open/freedom) usa `resolve_pasta_entrega`; default `./projetos/` local removido.
- [x] `G_LAYOUT_ENTREGA` exit 1 on nested-with-legacy fixture; exit 0 on ecosystem-only fixture — bite tests `test_g_layout_entrega_failing_path_*` + repo exit 0.
- [x] Mini-livro documents the “clone inside existing project” case — `docs/livros/partes/02-fluxos.md` §6.5.1.
- [x] `python ecossistema.py audit` exit 0 — gates-chave verdes: `G_LAYOUT_ENTREGA`, `G_HARNESS_COMPAT` (44 gates documentados), `G_SAIDA_BINARIA`, `G_IDIOMA_LEI_4`; orquestrador 9/9.
