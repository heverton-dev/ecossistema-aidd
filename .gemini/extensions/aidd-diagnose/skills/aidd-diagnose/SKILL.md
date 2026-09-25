---
name: aidd-diagnose
description: Systematic scientific fault triage using hypothesis isolation, regression testing, and code review graph.
depends:
  mcp: code-review-graph
---

# AIDD-Diagnose — Scientific Fault Triage

Execute this skill when triaging unexpected test failures, regressions, or system anomalies. Unprincipled trial-and-error (*shotgun debugging*) is strictly prohibited.

## CLI (single entry point)

All steps go through `python ecossistema.py diagnose <sub>`; the session lives in `docs/diagnosticos/<data>_<slug>/`.

| Step | Command |
|---|---|
| Open session | `iniciar --sintoma "<text>"` |
| Advance phase (no skipping) | `fase --numero <1-5>` |
| Log a phase (repro command, active/discarded hypothesis) | `registrar --fase N [--comando C] [--hipotese H] [--descartada H --prova P] [--modo-fase2 grafo\|fallback]` |
| Phase 4 isolated worktree | `worktree --slug <slug>` |
| End of Phase 5 cleanup | `limpar [--slug <slug>]` |
| Root-cause report | `relatorio --execucoes N --teste-regressao <file> --exit-antes <code>` |
| Gate | `python gates/G_aidd_diagnose.py --relatorio docs/diagnosticos/<sessao>/RELATORIO-CAUSA-RAIZ.md` |
| Handoff | `python .agents/skills/aidd-diagnose/scripts/handoff.py emitir ...` / `transicionar ...` |

## 5-Phase Protocol

1. **Deterministic Reproduction:**
   - Isolate the failure into a minimal reproducible command or unit test.
   - Do not proceed until reproduction is 100% deterministic locally.
   - Record it: `diagnose registrar --fase 1 --comando "<repro>"`.
2. **Graph Blast Radius Analysis:**
   - **Mandatory coverage pre-check (before any impact query):** run `python .agents/skills/aidd-diagnose/scripts/cobertura_grafo.py verificar <suspect-files>`. It queries each suspect file with `query_graph_tool(pattern="file_summary", target=<file>)`; zero results = graph stale for that file (the script runs `code-review-graph update --repo .` once and rechecks). Still zero → `modo_fase2 = "fallback"` and execute the Ticket 4 fallback below. Never report "0 impacted" for a file without graph nodes — only files with `zero_impacto_permitido: true` may appear as zero impact; for uncovered files report `grafo desatualizado → fallback`.
   - Use `code-review-graph` (`query_graph_tool` with callers/callees, `detect_changes_tool`, `get_impact_radius_tool`).
   - Trace entry points, affected call flows, and direct downstream consumers.

   **Fallback (MCP unavailable)** — prefer `code-review-graph` when available (fast, precise); otherwise run once `python .agents/skills/aidd-diagnose/scripts/fallback.py analisar --repo <raiz> --arquivos <suspect-files> [--funcao <alvo>]`. It probes the MCP `code-review-graph` with retry + exponential backoff (the cold start takes ~11 s); if the connection stays down, it completes the triage deterministically in the spirit of Grep/Glob/Read, without any LLM: callers via AST search by function name across repo `.py` files, callees via body read of the target function, and impact via search of who imports the suspect module. It records the real Phase 2 mode in `sessao.json` (`fase2.modo` = `"grafo"` or `"fallback"`) — never claim graph provenance for conclusions derived by static fallback. Exit 1 means the fallback itself could not run; exit 0 means Phase 2 completed in either mode.
3. **Single Hypothesis Formulation:**
   - Formulate exactly ONE testable hypothesis: *"The failure occurs because function X receives null input when Y is uninitialized"*.
   - Record it: `diagnose registrar --fase 3 --hipotese "<hypothesis>"`.
4. **Instrumentation & Proof:**
   - Instrument only inside the isolated worktree: `diagnose worktree --slug <slug>` (`isolamento.py` blocks writes outside it and `docs/diagnosticos/`).
   - Add minimal assertions or temporary instrumentation to prove or disprove the hypothesis. End every temporary line with `# AIDD-DIAGNOSE-TEMP`.
   - If disproved, discard immediately (`diagnose registrar --fase 4 --descartada "<h>" --prova "<evidence>"`) and formulate the next hypothesis. If proved, proceed.
5. **Surgical Fix & Regression Test:**
   - Apply the minimal viable fix.
   - Convert the reproduction step from Phase 1 into a permanent automated regression test.
   - Strip all temporary instrumentation before committing: `diagnose limpar --slug <slug>` removes every `AIDD-DIAGNOSE-TEMP` line and discards the worktree (`rollback.py`).
   - Generate the report with `diagnose relatorio ...` and run `G_aidd_diagnose`: it re-runs the regression test file and fails if it is missing or red. `falhou_antes` stays self-declared.
   - Hand off with `handoff.py emitir` (`handoff-diagnose.json`).
