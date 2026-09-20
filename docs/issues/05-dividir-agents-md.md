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

PLAN-0022 item 2 foi formalmente especificado e validado em `docs/planos/fazendo/PLAN-0022-config-arquivos-tokens/02-avaliar-dividir-agentsmd.md`.

Modelado como manual de operações ("folha plastificada na parede vs pasta no gaveteiro"):
- **Núcleo (`AGENTS.md`):** Restrições operacionais a cada turno, 100% das 13 Leis Invioláveis e portões, a Tríade Canônica (`pure`, `open`, `freedom`), e matriz de roteamento de contexto.
- **Sob Demanda (`docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`):** Tabelas completas de gates, opções manuais/pre-commit, parâmetros CLI de slash commands, diretrizes visuais/design, matriz de sincronização física multi-harness e ferramentas MCP.

## Acceptance criteria

- [x] PLAN-0022 item 2 scope is genuinely filled in, with the proposed split and a reason per section leaving the core (`02-avaliar-dividir-agentsmd.md`).
- [x] Core still holds every inviolable law — no governance rule becomes on-demand (todas as 13 leis invioláveis e portões mantidos).
- [x] A real on-demand loading mechanism exists (ponteiro explícito de cabeçalho, AST regex de referências em `G_HARNESS_COMPAT.py`, dispatch arquitetural).
- [x] Core size reduction measured in numbers, before and after (redução de 56,7% em bytes e 59,4% em palavras frente ao monólito original; de ~3.800 tokens para ~1.260 tokens no núcleo).
- [x] Pointer files for the other assistants (CLAUDE.md, GEMINI.md, QODER.md, CODEBUDDY.md) still resolve correctly (validado com exit 0 em `test_g_harness_compat.py`).

