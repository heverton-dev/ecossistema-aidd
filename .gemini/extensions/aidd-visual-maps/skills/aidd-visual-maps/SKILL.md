---
name: aidd-visual-maps
description: Builds or updates a visual map of one ecosystem piece type (guards, skills...) in docs/mapas-visuais/ from a PT-BR molde plus data read from the parts catalog, with tests that prove the generator bites. Use when the user wants a new map, to refresh a stale map, or says "mapa visual", "novo mapa", "mapa das skills", "mapa dos guardas", "atualizar mapa".
---

# aidd-visual-maps

A map has three pieces and nothing in its lists is hand-written:
- **molde** `docs/mapas-visuais/moldes/<type>.html`: fixed PT-BR text with `{{MARKER}}` slots;
- **generator** `valores_<type>(cat)` in `scripts/mapa_visual.py`: fills every marker from the catalog;
- **data** `docs/auditoria/mapa-pecas/catalogo-pecas.json`, produced by `scripts/catalogo_pecas.py`.

The maps the ecosystem needs are listed in `MAPAS_PREVISTOS` (`scripts/mapa_visual.py`); the index `docs/mapas-visuais/mapa-00-indice.html` shows each one as concluded, stale or to create, checked against disk. Read two existing moldes before writing a new one. The assembly manual (`docs/mapas-visuais/manual-montagem-aidd.html`) links every map (`tests/test_visual_maps_manual_links.py` fails on a missing link).

## Unified CLI

`python ecossistema.py visual-maps <subcommand>` (alias `aidd-visual-maps`; source `scripts/cli.py` of this skill):
- `catalogo [args]` and `mapa <type> [args]`: pass-through to `scripts/catalogo_pecas.py` and `scripts/mapa_visual.py`;
- `gerar`: catalog -> every map -> index -> book parts -> aidd-textbook build, in this fixed order, inside an ephemeral git worktree; only files under `docs/mapas-visuais/`, `docs/auditoria/mapa-pecas/` and `docs/livros/mapas-aidd/` are promoted back, in one atomic batch, then `docs/mapas-visuais/MANIFESTO-MAPAS.json` is written (catalog hash, sha256 and status of every map in both versions, book parts and PDF handed off to aidd-textbook; no timestamps);
- `check`: catalog freshness, `--check` of every map and the book, then the manifest hashes; exit 1 on the first drift.

## New map

1. **Make sure the catalog has the data.** If a field is missing, add it in `scripts/catalogo_pecas.py` (e.g. `coletar_skills_terceiros()`) with a test in `tests/test_catalogo_pecas.py`. Done when `python scripts/catalogo_pecas.py` exits 0 and the field is in the JSON.
2. **Write the molde** in PT-BR, same sections as the existing moldes: what / why / what for, when to build and when not, where it lives, how to build, done when / who checks, common mistakes, filterable list. Every catalog-driven part is a `{{MARKER}}`; `{{LINK_MANUAL}}` is mandatory. When an official rule exists (e.g. `docs/protocolos/CONVENCAO-AUTORIA-GATES.md`), the molde summarizes it and links to it; never copy its text. Styles come from `moldes/base.css`.
3. **Write the generator** `valores_<type>(cat)` returning exactly the molde's markers (without `LINK_MANUAL`, added by `montar`). Escape catalog text with `e()`. Register it in `GERADORES`, its title in `TITULOS` and the map in `MAPAS_PREVISTOS`.
4. **Write the tests** in `tests/test_mapa_visual.py`, at least:
   - a molde marker without a value raises `ValueError` (proof that it bites);
   - badges and lists come from a fake catalog;
   - a real run: `python scripts/mapa_visual.py <type> --fragmento --saida <tmp>` exits 0, with no `{{` left and the expected item count.
   Done when `python -m pytest tests/test_mapa_visual.py -q` exits 0.
5. **Generate and check:**
   ```bash
   python scripts/catalogo_pecas.py
   python scripts/mapa_visual.py <type>
   python scripts/mapa_visual.py <type> --check
   ```
   Done when `--check` exits 0. Each run writes both versions: technical in `docs/mapas-visuais/` and non-technical in `docs/mapas-visuais/nao-tecnicos/` (molde in `moldes-nao-tecnicos/<type>.html`, same file name); `--check` checks both.
6. **Link it from the manual:** add a `mapa-link` in the matching section of `docs/mapas-visuais/manual-montagem-aidd.html`.
7. **Commit** molde, generator, tests, catalog and generated map together, through the full pre-commit.

## Refresh an existing map

A new or removed piece (a guard, a skill) makes maps stale. Run `python ecossistema.py visual-maps gerar`; it runs, in order:

```bash
python scripts/catalogo_pecas.py
python scripts/mapa_visual.py <type>      # each type in MAPAS_PREVISTOS
python scripts/mapa_visual.py indice      # last: its status reads the other files
python scripts/livro_mapas.py
python componentes/compartilhado/skills/aidd-textbook/scripts/livro.py build docs/livros/mapas-aidd
```

Done when `python ecossistema.py visual-maps check` exits 0 and the index shows every map as concluded.

## Publishing

`--fragmento` writes without `<!doctype>`/`<head>` (Artifact publishing format). `--link-manual <url>` sets the "back to the manual" link.

## Negative Guardrails

- NEVER hand-edit a generated map in `docs/mapas-visuais/` or `docs/mapas-visuais/nao-tecnicos/`; change the molde or `valores_<type>()` and regenerate, or `--check` fails.
- NEVER type a list, count or badge into a molde; it must be a `{{MARKER}}` filled from `docs/auditoria/mapa-pecas/catalogo-pecas.json`.
- NEVER copy the text of an official rule (e.g. `docs/protocolos/CONVENCAO-AUTORIA-GATES.md`) into a molde; summarize it and link.
- NEVER regenerate `mapa-00-indice.html` before the other maps; its status reads them from disk.
- NEVER skip the bite test (a marker without value raises `ValueError`) or commit the map with `--no-verify`.

## Failure Modes & Fallback

- **`ValueError: molde e gerador desencontrados`:** `montar()` lists the markers missing on each side; add them to `valores_<type>()` or remove them from the molde, then rerun.
- **`--check` exits 1:** the catalog or a piece changed; run `python ecossistema.py visual-maps gerar`.
- **`visual-maps check` reports `MANIFESTO-MAPAS.json`:** a map, a book part or the PDF changed after the last `gerar`; rerun `gerar`, never edit the manifest.
- **aidd-textbook build fails during `gerar`:** maps are still promoted and the failure is recorded in the manifest (`handoff_livro.build.exit_code`); run `livro.py doctor`, fix pandoc/typst, rerun `gerar`.
- **Catalog lacks a field the map needs:** add it in `scripts/catalogo_pecas.py` with a test in `tests/test_catalogo_pecas.py` first; never fill it inside the generator by hand.
- **`G_mapa_pecas` fails at pre-commit:** a required map or manual link is missing; add the `mapa-link` in `docs/mapas-visuais/manual-montagem-aidd.html`.

## Stopping Checklist

- [ ] `python scripts/catalogo_pecas.py > cat.txt 2>&1; echo $? > cat.rc` holds `0`.
- [ ] `python -m pytest tests/test_mapa_visual.py -q > mv.txt 2>&1; echo $? > mv.rc` holds `0`.
- [ ] `python scripts/mapa_visual.py <type> --check > chk.txt 2>&1; echo $? > chk.rc` holds `0` (both versions).
- [ ] `python modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py > gmp.txt 2>&1; echo $? > gmp.rc` holds `0`.
- [ ] `python ecossistema.py visual-maps check > vm.txt 2>&1; echo $? > vm.rc` holds `0` (catalog, maps, book and manifest).
