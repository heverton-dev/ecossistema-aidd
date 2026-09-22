---
id: ISSUE-USA-0006
title: Pacote core enxuto de distribuição (A3)
status: done
blocked_by: []
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A3)
---

# ISSUE-USA-0006 — Pacote core enxuto de distribuição (A3)

**Deliver:** End-user clone/package carries only the functional core. Drop 221 MB / 8.186-file inflation (~80% dev-only). Books stay out of the runtime clone.

**Blocked by:** nothing. Start now.

## Scope

1. `.gitattributes` `export-ignore` for: `tests/`, `testes/`, `*.db`, `requirements-dev*`, `pytest.ini`, `__pycache__/`, `.pytest_cache/`, `.worktrees/`, `.ade_tmp/`, `PLANO-EXECUCAO-ESTRUTURADO.json`, `.pre-commit-config.yaml`, `.secrets.baseline`.
2. `.gitignore` explicit for `*.db`, `__pycache__/`, `.pytest_cache/`, `.worktrees/`, `.ade_tmp/`; remove already-committed residue from the tree.
3. Profile command: `python ecossistema.py package --perfil usuario` (zip or documented `git clone --depth 1` + sparse-checkout).
   - INCLUDE: `ecossistema.py`, `gates/`, `core/`, `componentes/`, `scripts/`, `tools/`, `requirements.txt`, `README.md`, `LICENSE`, `docs/protocolos/`, active schemas.
   - EXCLUDE: tests, `*.db`, dev requirements, `docs/relatorios/`, `docs/reports/`, `docs/livros/` (PDF/images).
4. Move heavyweight docs (`docs/relatorios`, `docs/reports`, `docs/livros` PDF/images) to release assets or doc site — in-tree keep `docs/protocolos/` + active schemas (Law #12 spirit).
5. Document shallow/sparse alternative for `core` profile (5-line recipe in README).
6. Gate `gates/G_PACOTE_CORE.py`: fail if release contains `*.db`, `requirements-dev*`, or `docs/relatorios/`.
7. Bite test `gates/test_g_pacote_core.py`: dirty release fixture asserts exit 1.

## Acceptance criteria

- [x] `package --perfil usuario` (or documented `git archive`) output has zero EXCLUDE hits — zip 3425 arquivos, 0 violações; receita sparse no README.
- [x] Committed `test_verify.db` / `verify_check.db` and cache dirs gone from tree — `git rm --cached` + `*.db` no `.gitignore`.
- [x] `G_PACOTE_CORE` exit 1 on dirty fixture; exit 0 on clean package — 4/4 bite tests.
- [x] README documents 5-line sparse/shallow recipe — bloco “Só o núcleo” em Primeiros Passos.
- [x] `python ecossistema.py audit` exit 0 — `G_PACOTE_CORE`/`G_HARNESS_COMPAT` (46 gates)/`G_USER_FACING_PTBR` exit 0.
