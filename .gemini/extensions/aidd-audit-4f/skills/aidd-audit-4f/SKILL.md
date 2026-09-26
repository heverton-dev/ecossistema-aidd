---
name: aidd-audit-4f
description: Runs the linear 4-phase audit pipeline (Inspector, Architect, Builder, Return) on an ecosystem tool through the 15-D lens, in a cycle folder docs/auditoria/<tool>/ciclo-NN/ and an own branch, merging only on human approval. Use when the user wants to audit a tool, or types "/audit-4f", "/aidd-auditor", "audit-4f", "auditoria 4F", "auditar ferramenta", "rodar pipeline de auditoria".
---

# aidd-audit-4f

## Agnostic by rule

1. **OS:** scripts use `os.path.join` and cross-platform calls (Windows, Linux, Mac).
2. **Harness/LLM:** the `Harness` and `Model` fields of the orchestration JSON drive the injection.
3. **Activation:** `python ecossistema.py audit-4f --manifest <path.json>`, slash `/audit-4f <path.json>`, or natural language ("inicie a auditoria 4F na ferramenta X").

## Folder rule

The whole cycle lives in `docs/auditoria/<target-tool>/ciclo-NN/` (e.g. `docs/auditoria/aidd-melhoria/ciclo-01/`); only the `G_auditoria_15D.py` gate sits at the tool root. Each round opens the next cycle with `python scripts/scaffold_auditoria.py <tool>`: no cycle -> `ciclo-01`; current cycle without `LAUDO-15D-REVISADO.md` -> resume; closed cycle -> `ciclo-NN+1`, inheriting `DOD.md` and comparing previous -> new grade. Never put reports, 15-D laudos, DoD or evolution plans in `docs/planos/`.

## Execution (4 phases)

1. Read the target manifest (e.g. `docs/auditoria/template-pipeline-4f.json`).
2. Create or reuse `docs/auditoria/<tool>/ciclo-NN/`. If every phase already has output, report `NADA A FAZER` and do not claim success.
3. Accumulate phases on the cycle's own branch (`audit/<pipeline_id>`) without touching the current branch. Each phase runs its `gate_fase` before commit; a failure stops the pipeline without committing.
4. Phase 1 (Inspector): wait for exit 0 and the `output_handoff` (15-D laudo).
5. Phase 2 (Architect): writes `PLANO-EVOLUCAO.md` in the audit folder.
6. Phase 3 (Builder): implements the code.
7. Phase 4 (Return inspector): checks the `DOD`.
8. Run `gate_final` (full battery) once. On exit 0 the join barrier holds: merge happens only with `python scripts/orquestrador_4f.py --manifest <json> --aprovar` (human action), and only if the cycle branch did not change after `gate_final`.

## Trigger

On slash or natural language, stop, ask the user to confirm the Harness/Model in the manifest JSON, then run the orchestration command in the terminal.
