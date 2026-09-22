---
id: ISSUE-USA-0007
title: Template duplo de encerramento usuário + técnico (A9)
status: done
blocked_by: []
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A9)
---

# ISSUE-USA-0007 — Template duplo de encerramento usuário + técnico (A9)

**Deliver:** Every flow ends with a lay-readable summary AND a technical report. Lay user can audit their own delivery without jargon.

**Blocked by:** nothing. Start now. Complements ISSUE-USA-0005.

## Scope

1. Mandatory dual template at end of any triad flow:
   - `RESUMO-USUARIO.md` (≤20 lines, zero acronym) answering exactly 3 questions: o que mudou / como abro / como verifico.
   - `RELATORIO-TECNICO.md` (current dense report style — jargon allowed).
2. Both land at delivery root (same place as `README-USUARIO.md` from ISSUE-USA-0005).
3. Gate `gates/G_RESUMO_USUARIO.py`: fail if flow close lacks `RESUMO-USUARIO.md` or exceeds 20 lines / misses any of the 3 questions.
4. Bite test `gates/test_g_resumo_usuario.py`: missing/overlong/wrong-shape fixture asserts exit 1.
5. Apply Rule 10 dual-voice to the template itself (sample in gate fixtures).

## Acceptance criteria

- [x] Template dual emitted on flow close; omission = gate exit 1 — `gerar_resumo_usuario`/`gerar_relatorio_tecnico` no `_fechar_entrega`.
- [x] `RESUMO-USUARIO.md` ≤20 lines and contains the 3 mandatory answers — gerador trunca em 20 linhas; 3 perguntas obrigatórias.
- [x] `RELATORIO-TECNICO.md` preserves full telemetry (no dumbing-down) — JSON de metadados no rodapé.
- [x] `G_RESUMO_USUARIO` exit 1 on bad fixture (Law #13); exit 0 on good close — 5/5 bite tests.
- [x] `python ecossistema.py audit` exit 0 — `G_RESUMO_USUARIO`/`G_HARNESS_COMPAT` (47 gates)/`G_LEI_DECLARA_PORTAO` exit 0.
