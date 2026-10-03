---
name: aidd-evolution
description: Runs the technical evolution pipeline that executes, ticket by ticket, the PLANO-EVOLUCAO of an audit cycle in ephemeral git worktrees, with a gate before every commit and merge only on human approval. Use when the user wants to evolve a tool from its evolution plan, or types "/evolucao", "/aidd-evolucao", "evolucao", "evoluir ferramenta", "rodar pipeline de evolução".
---

# aidd-evolution

Executes the evolution tickets written by the Architect in phase 2 of the audit (`aidd-audit-4f`), implementing code and tests in isolated ephemeral worktrees.

## Agnostic by rule

1. **OS:** scripts use `os.path.join` and cross-platform calls.
2. **Harness/LLM:** `harness`, `model` and `comando_terminal` come from `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`.
3. **Activation:** `python ecossistema.py evolucao <tool>` or `python ecossistema.py evolucao --manifest <path.json>`, slash `/evolucao <tool-or-json>`, or natural language ("execute a evolução da ferramenta X").

## Input and output

- Tickets: `docs/auditoria/<tool>/ciclo-NN/PLANO-EVOLUCAO.md` (current cycle), compiled to `PLANO-EVOLUCAO.json` in the same folder.
- Execution config: `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`.
- Work areas: ephemeral worktrees in `../worktrees_evolucao-<tool>/`.
- Code destination: `.agents/skills/<tool>/scripts/` and `tests/`.

## Execution

1. Read the evolution manifest (e.g. `docs/auditoria/<tool>/ciclo-NN/PLANO-EVOLUCAO.json`).
2. All tickets accumulate on the cycle's own branch (`audit/<pipeline_id>`); the current branch never changes during the run.
3. For each ticket:
   - isolate an ephemeral worktree on the cycle branch;
   - read the ticket spec (`input_prompt`);
   - launch the configured agent with an interactive TTY and the Watchdog;
   - wait for the expected artifact (`output_handoff`);
   - run the ticket `gate_fase` (`pytest tests`) **before** committing; on failure the pipeline stops, nothing is committed and the worktree is kept for inspection;
   - commit on the cycle branch and discard the worktree.
4. After the last ticket:
   - run `gate_final` (`python ecossistema.py audit`) once; only a pass makes the cycle approvable;
   - join barrier: merge into the current branch only with `python scripts/orquestrador_4f.py --manifest <json> --aprovar`, and only if the cycle branch did not change after `gate_final`;
   - record the closing in `RESUMO-USUARIO.md` and `RELATORIO-TECNICO.md`.

## Trigger

Identify the target tool, check that `PLANO-EVOLUCAO.json` exists (compile it from the Markdown if not), confirm the user's Harness/Model and run the ecosystem terminal command.

## Negative Guardrails

- NEVER run tickets straight from `PLANO-EVOLUCAO.md`; compile with `python scripts/compilador_plano_evolucao.py --plano <md> --out <json>` and run the JSON, so every ticket carries its `gate_fase`.
- NEVER commit a ticket by hand, with or without `--no-verify`; only the orchestrator commits, after the ticket `gate_fase` exits 0.
- NEVER commit on or switch the current branch during the run; tickets land only on `audit/<pipeline_id>`, and only the user merges with `scripts/orquestrador_4f.py --aprovar`.
- NEVER delete a worktree that a red ticket left in `../worktrees_evolucao-<tool>/` without the user's OK; it is kept for inspection.
- NEVER run `python ecossistema.py audit` or `scripts/e2e_foto.py` inside a ticket; `gate_final` is the orchestrator's single run.
- NEVER add an LLM API key to `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`; the ticket agent is the harness named in `comando_terminal`.

## Failure Modes & Fallback

- **No `PLANO-EVOLUCAO.json` nor `.md` in the current cycle:** `evolucao <tool>` cannot start; the cycle has no phase-2 plan. Run the Architect phase of `aidd-audit-4f` first.
- **Watchdog never sees `output_handoff`:** the agent crashed or wrote elsewhere. Inspect the kept worktree and confirm the harness process really exited (a surviving autonomous agent may keep committing), then re-run the same manifest; finished tickets come from cache.
- **`gate_final` red:** the cycle is not approvable. Read the failing gate, add a fix ticket to `PLANO-EVOLUCAO.md`, recompile and re-run.
- **`--aprovar` refused ("mudou depois do gate_final") or conflict in `[código]` paths:** re-run the full manifest in the first case; hand the conflict list to the user in the second.

## Stopping Checklist

- [ ] Orchestrator exit read from a file: `python ecossistema.py evolucao <tool> > evolucao.log 2>&1; echo $? > evolucao.exit` gives 0.
- [ ] Every ticket signed: `git log --oneline audit/<pipeline_id> > log.txt` shows `(gate_fase exit 0)` on each ticket line.
- [ ] No leftover worktree after success: `git worktree list > wt.txt` has no `worktrees_evolucao-<tool>` entry.
- [ ] `RESUMO-USUARIO.md` and `RELATORIO-TECNICO.md` exist in the cycle folder.
- [ ] Current branch unchanged until the user approves: `git rev-parse HEAD` equals the value taken before the run.
