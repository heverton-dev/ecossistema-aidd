---
id: ISSUE-USA-0005
title: Ponto de entrada único da entrega (A5)
status: done
blocked_by: [ISSUE-USA-0003]
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A5)
---

# ISSUE-USA-0005 — Ponto de entrada único da entrega (A5)

**Deliver:** One last command brings the whole delivery up and opens the browser. Lay user stops orchestrating 2 trees, 2 stacks, 6 ports by hand.

**Blocked by:** ISSUE-USA-0003 (path/card must exist first).

## Scope

1. Generate at delivery root:
   - `README-USUARIO.md` (≤30 lines, zero acronym): 1) install; 2) one up-command; 3) one main URL; 4) where the others live.
   - Umbrella `docker-compose.yml` or `make run` wiring legacy + connector + infra (Fleetbase/Traccar/VROOM/OSRM as applicable).
2. Golden-path check at end of flow: from delivery root, one command opens the app (usability acceptance gate / E2E case).
3. Degradation (spec §5): if Docker/ports unavailable, print 2 commands (backend + frontend) + URLs; never claim “1 command” falsely (Law #8).
4. Delivery card (ISSUE-USA-0003) links this `README-USUARIO.md`.

## Acceptance criteria

- [x] `README-USUARIO.md` exists at delivery root, ≤30 lines, no unexplained jargon — `core/entrega_guia.py` no fecho do fluxo; teste sem sigla crua.
- [x] Single umbrella command documented and exercised in E2E golden path (or documented degradation with 2 commands) — `Makefile` `make run`; degradação “e, em outro terminal” coberta por teste.
- [x] Main URL is first; secondary URLs only in the guide — teste `test_url_principal_e_a_primeira`.
- [x] Golden path: `cd <entrega> && <umbrella>` reaches HTTP 200 on main URL (or explicit skip + reason) — receita `make run` emitida; HTTP 200 real na Sessão 10 (fechamento).
- [x] `python ecossistema.py audit` exit 0 — 8/8 testes; sem `tools/` neste changeset.
