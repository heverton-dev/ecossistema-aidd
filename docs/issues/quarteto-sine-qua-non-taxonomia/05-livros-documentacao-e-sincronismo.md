---
id: ISSUE-QUARTETO-0005
title: Documentation, Textbooks and Component Synchronization
status: done
blocked_by: [ISSUE-QUARTETO-0004]
created: 2026-09-21
source: Architecture Decision Record 21-09-2026 — Quarteto Sine Qua Non
---

# ISSUE-QUARTETO-0005 — Documentation, Textbooks and Component Synchronization

**Deliver:** Update official textbook chapters, recompile PDFs via Typst, and synchronize all 91 components across ecosystem harnesses.

**Blocked by:** ISSUE-QUARTETO-0004.

## Scope

1. Update textbook part `docs/livros/partes/02-fluxos.md` to reflect new taxonomy.
2. Recompile official ecosystem PDF and step-by-step mini-book using Typst template.
3. Synchronize all 91 components across the 7 harnesses with `python ecossistema.py components sync`.
4. Verify SHA-256 integrity with `python ecossistema.py components verify --tipo todos`.

## Acceptance criteria

- [x] Textbook chapters updated and PDFs recompiled.
- [x] All 91 components pass SHA-256 verification across all harnesses.
