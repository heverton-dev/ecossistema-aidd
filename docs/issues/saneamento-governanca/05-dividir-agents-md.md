---
id: ISSUE-0005
title: Dividir o AGENTS.md em nucleo obrigatorio e secoes sob demanda
status: closed
blocked_by: [ISSUE-0001]
created: 2026-09-19
closed: 2026-09-20
source: open-decision sweep 2026-09-19 / PLAN-0022 item 2
---

# ISSUE-0005 — Dividir o AGENTS.md em núcleo e seções sob demanda

**Deliver:** every session of every assistant loads only what is always needed,
fetching the rest on demand. Lower cost per session, no rule lost.

**Blocked by:** ISSUE-0001 — both touch the same file, and that one is small. Land
the small one first to avoid two efforts fighting over the same text (a failure
mode already recorded in this project when two sessions edit one folder).

## Verified this session

PLAN-0022 item 2 formally specified and validated in `docs/planos/fazendo/PLAN-0022-config-arquivos-tokens/02-avaliar-dividir-agentsmd.md`.

Modelled as operations manual ("laminated sheet on the wall vs folder in the drawer"):
- **Core (`AGENTS.md`):** Turn-by-turn operational constraints, 100% of the 13 Inviolable Laws and gates, Canonical Triad (`pure`, `open`, `freedom`), and context dispatch matrix.
- **On-Demand (`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`):** Complete gate reference tables, manual/pre-commit options, slash command CLI parameters, visual/design guidelines, multi-harness physical synchronization matrix, and MCP tools.

## Acceptance criteria

- [x] PLAN-0022 item 2 scope is genuinely filled in, with the proposed split and a reason per section leaving the core (`02-avaliar-dividir-agentsmd.md`).
- [x] Core still holds every inviolable law — no governance rule becomes on-demand (all 13 inviolable laws and gates maintained).
- [x] A real on-demand loading mechanism exists (explicit header pointer, AST regex of references in `G_HARNESS_COMPAT.py`, architectural dispatch).
- [x] Core size reduction measured in numbers, before and after (reduction of 56.7% in bytes and 59.4% in words vs original monolith; from ~3,800 tokens to ~1,260 tokens in core).
- [x] Pointer files for the other assistants (CLAUDE.md, GEMINI.md, QODER.md, CODEBUDDY.md) still resolve correctly (validated with exit 0 in `test_g_harness_compat.py`).

