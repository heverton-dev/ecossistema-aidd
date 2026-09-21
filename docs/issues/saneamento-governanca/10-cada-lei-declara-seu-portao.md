---
id: ISSUE-0010
title: Cada lei declara seu portão verificador (inventário + meta-gate)
status: closed
blocked_by: []
created: 2026-09-19
closed: 2026-09-19
source: open-decision sweep 2026-09-19 — enforcement gap analysis
---

# ISSUE-0010 — Cada lei declara seu portão verificador

**Deliver:** every inviolable law names the gate that enforces it — or states
explicitly that none exists. A meta-gate fails when any law lacks that declaration.
Silent absence becomes loud absence.

**Blocked by:** nothing. Start now.

## Verified this session

- `AGENTS.md` holds **13 laws** (12 originais + Lei #13 adicionada na ISSUE-0011).
- Todas as 13 leis agora carregam linha de declaração de portão e nível de força de enforcement.
- Meta-gate determinístico `gates/G_LEI_DECLARA_PORTAO.py` criado e testado contra falsos positivos e negativos.
- Suíte `gates/test_g_lei_declara_portao.py` inclui testes de caminho feliz e reprovação (exit 1), 100% conforme a Lei #13 e `G_PORTAO_PROVA_QUE_MORDE.py`.
- O backlog das leis sem portão foi formalizado em `docs/protocolos/BACKLOG-LEIS-SEM-GATE.md`.
- Contagem corrigida para 12 no doc de arquitetura e no livro do ecossistema.

## Scope

For each of the laws, append one declaration line: the enforcing gate, or the
explicit string `sem gate — cumprimento por convenção`. Then a meta-gate that parses
the law list and exits 1 on any law missing the declaration.

**Also record enforcement strength per law**, not just presence. Three states:

- `provado` — a gate exists AND a test proves it fails when the guarded thing breaks.
- `nao-provado` — a gate exists, but nothing proves it bites (see ISSUE-0011).
- `sem-gate` — no gate; honest gap.

Without that third column this ticket produces a false sense of coverage: a law can
point at a facade gate (see ISSUE-0009, where `G_ZERO_HEADLESS` greps for a string
and declares victory). The map must show which extinguishers were actually test-fired.

## Acceptance criteria

- [x] All laws carry a declaration line naming gate or explicit absence (`AGENTS.md` §2).
- [x] Each declaration carries enforcement strength: `provado`, `nao-provado`, `sem-gate`.
- [x] Meta-gate exists, parses the law list, exits 1 on any missing declaration (`gates/G_LEI_DECLARA_PORTAO.py`).
- [x] Meta-gate has its own failing-path test (`gates/test_g_lei_declara_portao.py` per ISSUE-0011 / Lei #13).
- [x] Law count corrected in the architecture doc and book: 12, not 11 (`docs/explicacoes/16-09-2026_CONSOLIDACAO-DECISOES-ARQUITETURA-ECOSSISTEMA.md` e `docs/livros/`).
- [x] The resulting `sem-gate` list is written down as a backlog, not silently accepted (`docs/protocolos/BACKLOG-LEIS-SEM-GATE.md`).
