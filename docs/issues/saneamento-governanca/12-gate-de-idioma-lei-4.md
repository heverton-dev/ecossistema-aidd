---
id: ISSUE-0012
title: Gate de idioma para a Lei #4 (inglês compacto no núcleo)
status: closed
blocked_by: []
created: 2026-09-19
closed: 2026-09-20
source: open-decision sweep 2026-09-19 — enforcement gap analysis
---

# ISSUE-0012 — Gate de idioma para a Lei #4

**Deliver:** Law #4 stops being unenforced. Agent-facing text written in PT-BR gets
blocked at commit, instead of depending on whoever writes it remembering the law.

**Blocked by:** nothing. Start now. Conceptually downstream of ISSUE-0010, which
reveals such gaps — but this gap is already confirmed, so no wait.

## Verified this session

- Path scope list agreed: must-be-English (ticket bodies, SKILL.md, prompt templates, gate output strings, AGENTS.md core) vs PT-BR (title fields, INDEX.md, docs/ explanatory material, book, reports).
- Deterministic quality gate delivered in `gates/G_IDIOMA_LEI_4.py` (zero LLM calls).
- Failing-path test implemented in `gates/test_g_idioma_lei_4.py::test_failing_path_pt_prose_asserts_exit_1` asserting exit 1.
- False-positive check verified against `INDEX.md` and frontmatter titles asserting exit 0.
- Repository run executed: 4 existing ticket violations individually triaged and rewritten to compact English (zero bulk suppression).
- Declared against Law #4 in `AGENTS.md` and reference catalog `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`.
- Integrated into `ecossistema.py` (`_GATES_AUDIT`) and `.pre-commit-config.yaml` (`g-idioma-lei-4`).

## Acceptance criteria

- [x] Scope list written and agreed: which paths must be English, which stay PT-BR.
- [x] Gate detects PT-BR prose in must-be-English paths, deterministically, no LLM call.
- [x] Gate carries a failing-path test per ISSUE-0011: feed PT-BR prose into a must-be-English path, assert exit 1.
- [x] Run against the current repo; resulting violations triaged individually, not bulk-suppressed.
- [x] Law #4 in `AGENTS.md` names this gate, per ISSUE-0010.
- [x] False-positive check against a PT-BR path that must NOT trigger (e.g. `INDEX.md`).
