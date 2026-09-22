---
id: ISSUE-MESO-0007
title: Integração no Orquestrador Síncrono e Comando CLI ecossistema.py
status: done
blocked_by: [ISSUE-MESO-0006]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0007 — Integração no Orquestrador Síncrono e Comando CLI ecossistema.py

**Deliver:** Refactored `scripts/orquestrador_sincrono.py` eliminating mocked payloads and new CLI command in `ecossistema.py`.

**Blocked by:** `ISSUE-MESO-0006`

## Scope

1. Refactor `scripts/orquestrador_sincrono.py`:
   - Replace hardcoded entity mocks ("RegistroPrincipal" dicts in lines 178-221 and 274-300).
   - In `etapa_03_engine()`, invoke `dispatch_pipeline.py` passing the compiled DAG from `PLANNER.json`.
   - In `etapa_04_master()`, invoke `vsa_join_barrier.py` to finalize convergence into the Modular Monolith VSA.
   - Maintain exact CLI interface for backward compatibility (`python ecossistema.py run-fluxo --fluxo <1|2|3> ...`).
2. Add new command in `ecossistema.py`:
   - `python ecossistema.py dispatch --planner <caminho_planner.json> [--dry-run]`
   - Expose ergonomic alias `python ecossistema.py run-dispatch ...`.
3. Add end-to-end regression tests verifying that running `python ecossistema.py pure --dry-run` and `python ecossistema.py dispatch --help` succeed.

## Acceptance criteria

- [ ] All static mock dictionaries removed from `orquestrador_sincrono.py`.
- [ ] `python ecossistema.py dispatch --help` displays clean, compliant CLI help.
- [ ] `python ecossistema.py run-fluxo` routes execution via the new dispatch pipeline.
- [ ] Backward compatibility maintained for `pure`, `open`, `freedom` aliases.
