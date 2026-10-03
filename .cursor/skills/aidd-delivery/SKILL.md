---
name: aidd-delivery
description: Provides the delivery template with before/after evidence and real exit codes, rollback door and blast radius. Use when writing a long commit body, a PR body, a RELATORIO-CONSTRUTOR.md entry, or closing a ticket, or the user says "entrega", "fechar ticket".
---

# aidd-delivery (delivery with evidence)

Every delivery proves itself: what changed, before/after evidence with real exit codes, whether it can be undone, what can break.

Adapted from `pr` in mattpocock/skills (commit c55ee46), MIT license. "Resumo" section derives from the `show-me` skill by Dex Horthy (humanlayer).

## Where to Use
- **Long commit body:** current flow commits straight to a branch, often without a PR. The body carries the template.
- **PR body:** when a PR exists.
- **RELATORIO-CONSTRUTOR.md:** one entry per ticket of a 4F cycle.
- **Closing a ticket:** the ticket closes only with this template filled.

## Template

```markdown
## Resumo

<smallest view that makes the point: pseudocode, call tree, file tree, or diff sketch>

## Evidência (antes/depois)

- **Antes:** <command> → exit <N> (<failing test or output line>)
  **Depois:** <same command> → exit 0 (<passing test or output line>)

## Dá para desfazer?

**Porta:** <mão dupla (revert simples) | mão única (apaga dado, migra schema, publica)>

<optional: how to undo>

## O que pode quebrar

**Raio:** <one word: local | ferramenta | harnesses | ecossistema>

<optional: consumers, copies, gates that may react>
```

## Rules
- **Resumo:** skip preamble. Use `CONTEXT.md` terms. One visual next to the short text it supports; keep only the files, calls, and boundaries needed.
- **Evidência:** show the exact command run before and after, with its real exit code. Capture it by redirecting output to a file and reading `$?` on the same line (`cmd > out.txt 2>&1; echo $?`). Never read an exit code through a pipe: `cmd | tail` returns the exit code of `tail`, not of `cmd`.
- A checkbox marked `[x]` requires its evidence in the same document (command + exit code + output line). A box with no evidence stays `[ ]`.
- **Dá para desfazer?:** two-way door = cheap rollback (revert commit). One-way door = destructive or hard to reverse (deletes data, migrates schema, pushes, publishes). One-way doors need explicit user approval before running.
- **O que pode quebrar:** consider consumers of the changed file, harness copies from `python ecossistema.py components sync`, forge templates, and gates that read the file.

## Negative Guardrails

- NEVER fill **Evidência** with a command not run in this session, or with an exit code read through a pipe (`cmd | tail`).
- NEVER mark a ticket `[x]` in `RELATORIO-CONSTRUTOR.md` when the commit diff only touches the checkbox; the evidence must point at changed code or tests.
- NEVER write a fix's "Antes" without a test that failed first; a red-then-green pair is the proof, a green-only run is not.
- NEVER classify as **mão dupla** a change that pushes, publishes, migrates a schema or deletes copies; those are **mão única** and wait for explicit user approval.
- NEVER cite a delivery committed with `--no-verify` as passed, nor run `python ecossistema.py audit` inside a 4F phase to collect evidence: the orchestrator runs the phase gate.

## Failure Modes & Fallback

- **No "before" output exists (work already done):** check out the parent commit in a scratch worktree, rerun the same command there, and record that exit code; if impossible, write `Antes: não capturado` instead of inventing one.
- **Evidence command exits non-zero after the change:** the delivery is not closed; leave the box `[ ]`, paste the failing line, and report it to the user or coordinator.
- **Blast radius unclear:** run `python ecossistema.py components verify --tipo todos` and search consumers of the changed file before choosing `local` over `harnesses` or `ecossistema`.

## Stopping Checklist

- [ ] All four headings present: `grep -c -E "^## (Resumo|Evidência|Dá para desfazer|O que pode quebrar)" <file>` returns 4.
- [ ] Every evidence line carries a command and an exit code captured as `cmd > out.txt 2>&1; echo $? > cmd.rc`.
- [ ] Each `[x]` has its evidence in the same document; the count of `[x]` equals the count of evidence lines.
- [ ] **Porta** is `mão dupla` or `mão única`, and **Raio** is one of `local|ferramenta|harnesses|ecossistema`.
