---
name: aidd-audit-4f
description: Runs the linear 4-phase audit pipeline (Inspector, Architect, Builder, Return) on an ecosystem tool through the 15-D lens, in a cycle folder docs/auditoria/<tool>/ciclo-NN/ and an own branch, merging only on human approval. Use when the user wants to audit a tool, or types "/audit-4f", "/aidd-auditor", "audit-4f", "auditoria 4F", "auditar ferramenta", "rodar pipeline de auditoria".
---

# aidd-audit-4f

## Agnostic by rule

1. **OS:** scripts use `os.path.join` and cross-platform calls (Windows, Linux, Mac).
2. **Harness/LLM:** the `Harness` and `Model` fields of the orchestration JSON drive the injection.
3. **Activation:** `python ecossistema.py audit-4f --manifest <path.json>`, slash `/audit-4f <path.json>`, or natural language ("inicie a auditoria 4F na ferramenta X").

## Folder rule

The whole cycle lives in `docs/auditoria/<target-tool>/ciclo-NN/` (e.g. `docs/auditoria/aidd-melhoria/ciclo-01/`); only the `G_auditoria_15D.py` gate sits at the tool root. Each round opens the next cycle with `python scripts/scaffold_auditoria.py <tool>`: no cycle -> `ciclo-01`; current cycle without `LAUDO-15D-REVISADO.md` -> resume; closed cycle -> `ciclo-NN+1`, inheriting `DOD.md` and comparing previous -> new grade. Never put reports, 15-D laudos, DoD or evolution plans in `docs/planos/`.

## Execution (4 phases)

1. Read the target manifest (e.g. `docs/auditoria/template-pipeline-4f.json`).
2. Create or reuse `docs/auditoria/<tool>/ciclo-NN/`. If every phase already has output, report `NADA A FAZER` and do not claim success.
3. Accumulate phases on the cycle's own branch (`audit/<pipeline_id>`) without touching the current branch. Each phase runs its `gate_fase` before commit; a failure stops the pipeline without committing.
4. Phase 1 (Inspector): wait for exit 0 and the `output_handoff` (15-D laudo).
5. Phase 2 (Architect): writes `PLANO-EVOLUCAO.md` in the audit folder.
6. Phase 3 (Builder): implements the code.
7. Phase 4 (Return inspector): checks the `DOD`.
8. Run `gate_final` (full battery) once. On exit 0 the join barrier holds: merge happens only with `python scripts/orquestrador_4f.py --manifest <json> --aprovar` (human action), and only if the cycle branch did not change after `gate_final`.

## Trigger

On slash or natural language, stop, ask the user to confirm the Harness/Model in the manifest JSON, then run the orchestration command in the terminal.

## Negative Guardrails

- NEVER write a 15-D laudo, `DOD.md` or `PLANO-EVOLUCAO.md` under `docs/planos/`; they live only in the cycle folder opened by `python scripts/scaffold_auditoria.py <tool>`.
- NEVER run `python scripts/orquestrador_4f.py --manifest <json> --aprovar` or `git merge audit/<pipeline_id>` yourself: the merge is the human join-barrier action. Report the `gate_final` exit and stop.
- NEVER run `python ecossistema.py audit` or `scripts/e2e_foto.py` from inside a phase worker; the orchestrator runs `gate_fase` per phase and `gate_final` once.
- NEVER `git commit`, `git commit --no-verify` or `git push` from a phase: only `orquestrador_4f.py` commits, and its own `--no-verify` is followed by the phase gate before the amend.
- NEVER close a cycle with `--fase <name>`: a single-phase run writes no approvable ref, so `--aprovar` refuses it.
- NEVER put an LLM API key in the manifest or `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`; each phase model is the harness in `comando_terminal`.

## Failure Modes & Fallback

- **Phase without `gate_fase`:** the orchestrator exits 1 ("Nenhuma fase é commitada sem gate"). Regenerate the manifest with `scripts/scaffold_auditoria.py` (or `scripts/compilador_plano_evolucao.py`); never delete the gate key to get past it.
- **`gate_fase` red:** the pipeline stops with nothing committed. Fix inside the same phase and re-run the same manifest; phases whose `output_handoff` already exists are skipped as `[CACHE]`, so only the red phase repeats.
- **`--aprovar` prints "mudou depois do gate_final":** a commit landed on `audit/<pipeline_id>` after the gate. Re-run the full manifest so `gate_final` re-signs the ref, then ask the user to approve again.
- **Merge conflict outside the derivatives map:** `--aprovar` aborts the merge and lists `[código]` paths. Hand that list to the user; the cycle branch stays approvable.

## Stopping Checklist

- [ ] Cycle folder complete: `ls docs/auditoria/<tool>/ciclo-NN/ > ls.txt 2>&1; echo $? > ls.exit` gives 0 and lists the laudo, `PLANO-EVOLUCAO.md` and `DOD.md`.
- [ ] Orchestrator exit read from a file: `python scripts/orquestrador_4f.py --manifest <json> > run.log 2>&1; echo $? > run.exit` gives 0 and `run.log` has no `NADA A FAZER`.
- [ ] Every phase commit is signed: `git log --oneline audit/<pipeline_id> > log.txt` shows `(gate_fase exit 0)` on each phase line.
- [ ] `docs/planos/` untouched: `git diff --name-only HEAD...audit/<pipeline_id> -- docs/planos/ > planos.txt` is empty.
- [ ] The user was asked to run `--aprovar`; the agent did no merge (`git rev-parse HEAD` unchanged since the start).
