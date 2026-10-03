---
name: aidd-handoff
description: Serializes and compacts session state into a structured markdown artifact for context rotation or agent handover. Use when the context is heavy, the session ends or work passes to another agent, or the user says "handoff", "passar o bastão", "salvar contexto".
---

# AIDD-Handoff — Structured Context Preservation

Execute this skill when closing a session, rotating context, or transferring work between agents to prevent knowledge drift and token fragmentation.

## Protocol Invariants

1. **Artifact Destination:**
   - Save the serialized handoff to `docs/secoes/sessao-<date>-<slug>.md`.
2. **Mandatory Handoff Sections:**
   - **Initial Goal:** What was originally requested.
   - **Completed Work:** Explicit list of created/modified files and verified test suites.
   - **Quality Gate State:** Current status of gates (`python ecossistema.py audit`, test runner outputs).
   - **Next Actions:** Prioritized, sequential backlog for the incoming agent.
   - **Discovered Invariants & Gotchas:** Non-obvious architectural nuances or discovered edge cases.
3. **Extreme Token Economy:**
   - Never paste full source code into the handoff artifact. Reference relative file paths and symbol names.
   - Use telegraphic markdown tables and bullet points.

## Negative Guardrails

- NEVER fill "Quality Gate State" from memory: paste the exit codes read from `.rc` files; inside an orchestrated phase do not run `python ecossistema.py audit`, record "audit: owned by the orchestrator".
- NEVER assume `docs/secoes/sessao-<date>-<slug>.md` reaches another worktree or branch: `docs/secoes/*.md` is in `.gitignore`; give the incoming agent the absolute path.
- NEVER list a file under "Completed Work" without `git diff --stat` showing it, nor mark a ticket done when its commit only touched a checkbox.
- NEVER write approvals or user decisions the user did not give into "Next Actions".
- NEVER confuse this file with the signed `handoff-melhoria` (`gates/G_HANDOFF_MELHORIA.py`, owned by `aidd-improvement`) or the session ID record in `secoes/historico_sessoes.json` (`aidd-session`).

## Failure Modes & Fallback

- **Another session writes in the same folder:** check `git status --short` and the newest files in `docs/secoes/` before writing; on a name clash append `-2` and never overwrite.
- **Context too heavy to recall everything:** build "Completed Work" from `git log --oneline <base>..HEAD` and `git diff --stat <base>`, not from conversation memory.
- **Gate state unknown:** write "not run" for that gate; never guess pass.

## Stopping Checklist

Prove each item with the exit code read from a file (`> x.log 2>&1; echo $? > x.rc`, read `x.rc`), never through a pipe.

- [ ] `test -f docs/secoes/sessao-<date>-<slug>.md` exit 0.
- [ ] The 5 mandatory headings exist: `grep -c` over the file returns 5.
- [ ] Every path in "Completed Work" appears in `git diff --stat <base>` or `git log --name-only <base>..HEAD`.
- [ ] No source code was pasted: `grep -cE '^(def|class|import|function) ' <file>` returns 0.
