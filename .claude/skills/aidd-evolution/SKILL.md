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
