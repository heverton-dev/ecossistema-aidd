---
id: ISSUE-USA-0001
title: Alias de sincronização e correção da documentação canônica (A1)
status: done
blocked_by: []
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A1)
---

# ISSUE-USA-0001 — Sync Alias and Canonical Docs Fix (A1)

**Deliver:** Single canonical sync command path that works from CLI aliases and from every canonical doc. Kill both wrong forms in circulation (bare `components sync`; `ecossistema.py --tipos all`).

**Blocked by:** nothing. Start now.

## Scope

1. Parser (`ecossistema.py` ~1149–1191, `scripts/gestor_componentes.py:841`):
   - Accept `sync` as alias of `components sync`.
   - Accept `--tipos` as synonym of `--tipo`.
   - Missing `--tipo`/`--tipos` defaults to value `all` (PT token `todos`) + 1-line warning. Do not abort.
   - Unknown subcommand error text is already copy-pasteable:

```text
Erro: use "python ecossistema.py components sync --tipo todos".
```

2. Rewrite canonical docs to the full form:

```text
python ecossistema.py components sync --tipo todos
python ecossistema.py components verify --tipo todos
```

   Targets: `MEMORY.md:33`, `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md:181`, `docs/livros/**`, `docs/livros/partes/05-transversais.md:17`, `docs/melhorias/**venture-os.md:196` (nonexistent `componentes sync` subcommand).

3. New gate `gates/G_SYNC_CMD_ROT.py` (Law #1 + #13): fail if any canonical doc shows `components sync` without `--tipo`, or references unmapped `ecossistema.py sync` / `--tipos`.
4. Bite test `gates/test_g_sync_cmd_rot.py`: dirty fixture asserts exit 1.

## Acceptance criteria

- [x] `components sync --tipo todos` and `components verify --tipo todos` still exit 0 (regression) — `sync_canon:0`, `verify:0`.
- [x] `python ecossistema.py sync` and bare `components sync` both exit 0 with default + 1-line warning — `sync_alias:0`, aviso impresso.
- [x] `--tipos` accepted as synonym of `--tipo` — `tipos_syn:0`.
- [x] Unknown command prints the exact canonical line above and exits 1 — `ecossistema.py --tipos todos` imprime a linha canônica.
- [x] Zero hits of bare `components sync` without `--tipo` in canonical docs — `G_SYNC_CMD_ROT` exit 0.
- [x] `G_SYNC_CMD_ROT` exit 1 on dirty fixture (Law #13 proof) and exit 0 on clean repo — 4/4 em `gates/test_g_sync_cmd_rot.py`; `G_PORTAO_PROVA_QUE_MORDE` 42/42.
- [x] `python ecossistema.py audit` exit 0 — gates-chave verdes: `G_SYNC_CMD_ROT`, `G_HARNESS_COMPAT`, `G_IDIOMA_LEI_4`, `G_PORTAO_PROVA_QUE_MORDE`, `G_LEI_DECLARA_PORTAO`.
