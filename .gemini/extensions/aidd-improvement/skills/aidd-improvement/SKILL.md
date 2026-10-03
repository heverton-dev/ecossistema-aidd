---
name: aidd-improvement
description: Deeply investigates a requested ecosystem improvement in the real code and writes a scored evaluation report (current grade 0-10 with evidence) in docs/melhorias/. Step 1 of the melhoria -> plan -> orchestrate flow. Use when the user asks to analyze, evaluate or grade an improvement or refactor before planning, or to re-analyze an existing plan, or types "/melhoria", "melhoria", "analisar melhoria", "avaliar melhoria", "reanalisar plano".
---

# aidd-improvement (step 1 of 3)

## Place in the flow

| Step | Command | In | Out | Mandatory stop |
|---|---|---|---|---|
| 1 | `/melhoria <request>` | user request, or an existing plan to re-analyze | report in `docs/melhorias/` with current grade and evidence | "Generate the plan from this?" |
| 2 | `/plan <name>` | step 1 report or a direct request | `docs/planos/<name>/`, every item in draft | "Approve this plan?" |
| 3 | `/orchestrate <plan>` | approved plan | real execution | environment choice + Flight Plan approval |

No step triggers the next one by itself (Golden Rule #7, `AGENTS.md`). One owner per command: `aidd-improvement`, `aidd-plan`, `aidd-orchestrate`.

Do not use when: a report already exists and the user only wants the plan (`/plan`); the plan must be executed (`/orchestrate`).

## Agnostic by rule

Works the same in every harness (Golden Rule #6): heavy work runs in the shared CLI; `codebase-memory-mcp` is preferred when present, with Grep/Glob/Read as the universal fallback.

## Protocol

1. **Start only on an explicit request** in natural language. Never infer one from ambiguous context.
2. **Investigate the real code**, strictly within the request:
   - first the `codebase-memory-mcp` tools when available (`search_graph`, `get_architecture`, `trace_path`, `query_graph`, `search_code`, `get_code_snippet`);
   - fill gaps with Grep/Glob/Read; never stop because one tool is missing;
   - reproduce for real (command, test, gate) whenever it applies; cross-reading code is not proof of behavior.
3. **Current grade (0-10) with real evidence** (files checked, command run, concrete finding). Without a reliable grade the field is `NAO AUDITADO`, never an estimate.
4. **Re-analysis of an existing plan** (only when the request points to one):
   ```bash
   python ecossistema.py plan ler-nota <plan-path> [--item <NN>]
   ```
   Returns `NAO AUDITADO` for old-format plans. For each in-scope item, read its `Escopo` and `Definicao de Pronto`, then classify from the real investigation: `feito`, `parcial` (say exactly what is missing) or `nao-feito`. Pass it as `--itens-avaliados "<item>::<feito|parcial|nao-feito>::<reason>"`.
5. **Generate the report deterministically** (never paste long HTML in chat):
   ```bash
   python ecossistema.py melhoria init --pedido "<original user text>" \
     --nome "<3 short words>" \
     --nota-atual "<0-10 or omit>" --evidencia "<real proof or omit>" \
     --resumo "<2-3 sentences>" \
     --achados "finding 1" "finding 2" --riscos "risk 1" \
     --recomendacao "<suggested next step>" \
     [--plano-existente "<plan-path>" [--item "<NN>"]] \
     [--itens-avaliados "01::parcial::reason" "02::feito::reason"]
   ```
   Creates in `docs/melhorias/` the pair `<dd-mm-aaaa>_melhoria-<3-words>.html` (reading version, rules in `docs/relatorios/DIRETRIZES-DESIGN-RELATORIOS.md`; with `--plano-existente` it shows previous -> new grade and the item table) and `.json` (raw data reused by `/plan`). Done when the command exits 0 and both files exist.
6. **Chat output:** only the file path and a 2-3 sentence summary with the grade (and the planned-vs-implemented summary on re-analysis).
7. **Suggest the next step, never decide it:**
   - new analysis: ask whether to start `/plan` from this report;
   - re-analysis: ask whether to write the new grade into that plan:
     ```bash
     python ecossistema.py plan atualizar-nota <plan-path> [--item <NN>] \
       --nota-atual "<new grade>" --evidencia "<generated report path>"
     ```
   Never run `/plan` or `atualizar-nota` by yourself: `atualizar-nota` overwrites a grade permanently.

## Negative Guardrails

- NEVER pass `--nota-atual` without a command you ran or a file you read as `--evidencia`; omit it so the report says `NAO AUDITADO`.
- NEVER grade from cross-reading code: re-run the gate, test or CLI that drives the behavior and cite its exit code.
- NEVER classify a plan item `feito` because its box is `[x]`; read the commit diff (`git show --stat <sha>`), since a commit that only ticks the box changes no code.
- NEVER write the report by hand or paste HTML in chat; only `python ecossistema.py melhoria init` writes the pair in `docs/melhorias/`.
- NEVER create or edit anything under `docs/planos/` in this step (that is `aidd-plan`); a tool audit plan goes to `docs/auditoria/<tool>/ciclo-NN/PLANO-EVOLUCAO.md` through `aidd-audit-4f`.
- NEVER run `/plan` or `python ecossistema.py plan atualizar-nota` without an explicit "sim" from the user in this conversation.

## Failure Modes & Fallback

- **`plan ler-nota` returns `NAO AUDITADO`:** old-format plan. Do not invent a previous grade; generate the report without the previous -> new comparison and say so in the summary.
- **`codebase-memory-mcp` absent or project not indexed:** continue with Grep/Glob/Read and add "grafo indisponível" to `--achados`; never stop the analysis for it.
- **`melhoria init` exits non-zero or one file of the pair is missing:** read its stderr, correct the argument and re-run; never complete the `.json` or `.html` by hand.
- **Request too vague to scope:** ask the user one question naming the two readings before investigating.

## Stopping Checklist

- [ ] `python ecossistema.py melhoria init ... > melhoria.log 2>&1; echo $? > melhoria.exit` gives 0.
- [ ] Both `.html` and `.json` of the pair exist: `ls docs/melhorias/<dd-mm-aaaa>_melhoria-<3-words>.* > par.txt` lists two files.
- [ ] The grade is a number with `--evidencia`, or `NAO AUDITADO`.
- [ ] `git status --short docs/planos/ > planos.txt` is empty.
- [ ] The chat ends with the next-step question; no `/plan` or `atualizar-nota` was run.

## Tool engine

`scripts/` holds the deterministic engine of the melhoria tool (analyzer, fallback, handoff, isolation, observability, rollback). `python ecossistema.py melhoria --manifest <json>` runs `scripts/cli.py`. `tests/` covers the report manager.
