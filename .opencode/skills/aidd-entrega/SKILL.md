---
name: aidd-entrega
description: Delivery template with evidence. Use when writing a long commit body, a PR body, a RELATORIO-CONSTRUTOR.md entry, or closing a ticket.
---

# AIDD-Entrega — Delivery with Evidence

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
