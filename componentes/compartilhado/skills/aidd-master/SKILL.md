---
name: aidd-master
description: Scaffolds and integrates self-contained vertical slices in the aidd-master modular monolith (models, services, REST routes, contract tests, UI). Use when the user wants a new module or slice, or says "master", "/master", "nova fatia vertical", "adicionar módulo".
---

# aidd-master

- Creates self-contained vertical slices in `src/modules/<module>/`.
- Generates models, services, HTTP/REST routes, contract tests and UI components.
- Keeps a clean integration with the Shared Kernel and the polyglot DatabaseAdapter.

## Run

```bash
python ecossistema.py master add-module <module>
```

Slash command: `/master <module>`.

Done when: the command exits 0 and the module's contract tests pass.

## Negative Guardrails

- NEVER run `master add-module <module>` for a module that already exists in `src/modules/<module>/`: the generator uses `overwrite_if_exists=True` and replaces hand-written code; check the folder first.
- NEVER run it without `--dir <project>` from the ecosystem root: the default `.` writes the slice into the ecosystem itself.
- NEVER mistype the subcommand: `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/aidd.py` sends unknown words to natural-language intent parsing instead of failing.
- NEVER import another module's internals from a slice; cross-slice talk goes through the Shared Kernel and the EventBus.
- NEVER declare the slice done without a red-then-green contract test: show `master test contracts` failing before the service code, then passing.

## Failure Modes & Fallback

- **`master test contracts --dir <project>` fails:** fix `src/modules/<module>/services.py`, not the test; for BDD rules run `master refine-module <module> --dir <project>`.
- **`refine-module` exits 1 ("Arquivo de especificação não encontrado"):** write `features/<module>.feature` with the Given/When/Then from `PLANNER.json`, then rerun.
- **Slice must attach to an exported frontend (Flow 03):** use `master attach-vsa`, never `add-module` over the frontend folder.

## Stopping Checklist

- [ ] `test -d <project>/src/modules/<module>` was false before `add-module` (or the user approved the overwrite).
- [ ] `python ecossistema.py master add-module <module> --dir <project> > am.log 2>&1; echo $? > am.rc` and `am.rc` holds `0`.
- [ ] `python ecossistema.py master test contracts --dir <project> > ct.log 2>&1; echo $? > ct.rc` holds `0`, after a recorded red run.
- [ ] `python ecossistema.py master integrate --dir <project> > it.log 2>&1; echo $? > it.rc` holds `0` and `HANDOFF_MASTER_ENTERPRISE.json` (C4) exists.
