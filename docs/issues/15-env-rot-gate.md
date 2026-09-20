---
id: ISSUE-0015
title: Portão de Env Rot (variáveis exigidas versus .env.example)
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md — category 7
---

# ISSUE-0015 — Portão de Env Rot

**Deliver:** a variable the code reads but `.env.example` does not list stops being
a crash on a clean machine and becomes a blocked commit.

**Blocked by:** nothing. Start now.

## Why this one is genuinely new

Checked against all 27 existing gates: `G_INFRA_COMPOSE` validates compose files,
`G_SEGREDOS` scans for hardcoded credentials. Neither reconciles environment keys
read by code against the documented example.

The source document maps this to "Lei #9 (Execução Limpa em Máquina Nova)". **That law
does not exist** — Law #9 is Tool Testing Discipline. Map it correctly before declaring.

## Scope

AST scan for `os.getenv(...)`, `os.environ[...]`, `process.env.*`. Every key found
must appear in `.env.example`. Exit 1 on any missing key.

Cover both sides: keys in `.env.example` that no code reads are also rot, and should
at minimum be reported.

## Acceptance criteria

- [ ] AST scan, not regex, so dynamic key construction is detected or explicitly reported as undecidable.
- [ ] Every key read by code appears in `.env.example`; exit 1 otherwise, naming the key and file.
- [ ] Orphan keys in `.env.example` reported.
- [ ] Failing-path test, strict Law #13: add a `os.getenv` call for an undocumented key, execute the gate, assert exit 1.
- [ ] Correct law mapping recorded — not the non-existent "Lei #9 Execução Limpa".
- [ ] Declared against its law in `AGENTS.md`, per ISSUE-0010 convention.
