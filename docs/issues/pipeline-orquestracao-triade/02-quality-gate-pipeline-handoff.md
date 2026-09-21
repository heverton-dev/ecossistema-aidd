---
id: ISSUE-PIPE-0002
title: Quality Gate G_PIPELINE_HANDOFF com Prova que Morde
status: done
blocked_by: [ISSUE-PIPE-0001]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Pipeline Unificado de Orquestração
---

# ISSUE-PIPE-0002 — Quality Gate G_PIPELINE_HANDOFF com Prova que Morde

**Deliver:** Deterministic root Quality Gate at `gates/G_PIPELINE_HANDOFF.py` verifying that any handoff manifest passed to the execution engine strictly conforms to `handoff-execucao.schema.json`.

**Blocked by:** `ISSUE-PIPE-0001`.

## Scope

1. Implement `gates/G_PIPELINE_HANDOFF.py` accepting `--manifesto <path>`.
2. Validates JSON structure, required keys, and ensures zero stubs (rejects `TODO`, `FIXME`, empty targets).
3. Verifies that all `arquivos_alvo` referenced either exist or have valid parent directories.
4. Complies with Law #2 (Binary Quality: `sys.exit(0)` on valid, `sys.exit(1)` on invalid).
5. Implement `tests/test_gate_pipeline_handoff.py` per Law #13:
   - Must run real subprocess executing the gate script.
   - Assert exit 1 on corrupt, missing, or stubbed JSON handoff.
   - Assert exit 0 on compliant handoff manifest.

## Acceptance criteria

- [x] `gates/G_PIPELINE_HANDOFF.py` exists with binary exit points.
- [x] Automated test `tests/test_gate_pipeline_handoff.py` passes `pytest`.
- [x] Test proves gate bites by exercising a deliberately invalid manifest asserting exit 1.
- [x] Gate registered in `ecossistema.py` `_GATES_AUDIT` list.
