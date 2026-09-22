---
id: ISSUE-USA-0004
title: Perfil de linguagem leigo e GEMINI.md em PT-BR simples (A2)
status: done
blocked_by: []
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A2)
---

# ISSUE-USA-0004 — Perfil de linguagem leigo e GEMINI.md em PT-BR simples (A2)

**Deliver:** Lay-user facing surfaces speak simple PT-BR with dual voice (“Na Festa / Na Casa”). Rule 10 vs Law #10 naming is unambiguous. Gemini/Antigravity harness has an enforceable answer shape.

**Blocked by:** nothing. Start now.

## Scope

1. Disambiguate governance labels in `AGENTS.md` + `GEMINI.md` + `CODEX.md` + `MIMOCODE.md` + `OPENCODE.md`:
   - `Rule 10 (Formato de Resposta)` — never “Lei #10” for language.
   - `Lei #10 (Quarteto)` — never “Rule 10” for `/api` `/webhook` `/mcp` `/docs`.
   - `Lei #4 (Idioma)` unchanged.
2. Rewrite `GEMINI.md` answer-shape section in simple PT-BR (currently English + hook disabled).
3. Preflight language profile: `python ecossistema.py preflight-host --perfil leigo|tecnico` (default `tecnico`). Lay profile enforces: 1 simple sentence, ≤5 bullets, every acronym translated on first use, full copyable commands, banned-jargon list from spec §2.6.
4. Extend Rule 10 scope beyond chat: `README.md`, CLI `--help`, gate messages, session reports.
5. Gate `gates/G_USER_FACING_PTBR.py`: fail on banned jargon in README/`--help` without translation.
6. Bite test `gates/test_g_user_facing_ptbr.py`: jargon README fixture asserts exit 1.
7. Require `docs/glossario/` (term → everyday phrase) in generated `/docs` (Quarteto already has the page slot).

## Acceptance criteria

- [x] Zero ambiguous “Lei #10”/“Rule 10” misuse in harness files — `AGENTS.md` rotulado `Rule 10 (Formato de Resposta)` e `Lei #10 (Quarteto; distinto de Rule 10)`.
- [x] `GEMINI.md` 100% simple PT-BR; no English “Mandatory Answer Shape”.
- [x] `preflight-host --perfil leigo` changes agent answer shape (documented contract) — bloco `=== PERFIL LEIGO ===` impresso.
- [x] `G_USER_FACING_PTBR` exit 1 on jargon fixture; exit 0 on clean README — 4/4 bite tests.
- [x] Glossary present in generated `/docs` — `docs/glossario/glossario.md`.
- [x] `python ecossistema.py audit` exit 0 — `G_USER_FACING_PTBR`/`G_HARNESS_COMPAT` (45 gates)/`G_SAIDA_BINARIA`/`G_IDIOMA` exit 0.
