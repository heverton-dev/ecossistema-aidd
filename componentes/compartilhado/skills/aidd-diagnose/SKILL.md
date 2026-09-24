---
name: aidd-diagnose
description: Systematic scientific fault triage using hypothesis isolation, regression testing, and code review graph.
depends:
  mcp: code-review-graph
---

# AIDD-Diagnose — Scientific Fault Triage

Execute this skill when triaging unexpected test failures, regressions, or system anomalies. Unprincipled trial-and-error (*shotgun debugging*) is strictly prohibited.

## 5-Phase Protocol

1. **Deterministic Reproduction:**
   - Isolate the failure into a minimal reproducible command or unit test.
   - Do not proceed until reproduction is 100% deterministic locally.
2. **Graph Blast Radius Analysis:**
   - **Mandatory coverage pre-check (before any impact query):** run `python .agents/skills/aidd-diagnose/scripts/cobertura_grafo.py verificar <suspect-files>`. It queries each suspect file with `query_graph_tool(pattern="file_summary", target=<file>)`; zero results = graph stale for that file (the script runs `code-review-graph update --repo .` once and rechecks). Still zero → `modo_fase2 = "fallback"` and execute the Ticket 4 fallback below. Never report "0 impacted" for a file without graph nodes — only files with `zero_impacto_permitido: true` may appear as zero impact; for uncovered files report `grafo desatualizado → fallback`.
   - Use `code-review-graph` (`query_graph_tool` with callers/callees, `detect_changes_tool`, `get_impact_radius_tool`).
   - Trace entry points, affected call flows, and direct downstream consumers.

   **Fallback (MCP unavailable)** — prefer `code-review-graph` when available (fast, precise); otherwise run once `python .agents/skills/aidd-diagnose/scripts/fallback.py analisar --repo <raiz> --arquivos <suspect-files> [--funcao <alvo>]`. It probes the MCP `code-review-graph` with retry + exponential backoff (the cold start takes ~11 s); if the connection stays down, it completes the triage deterministically in the spirit of Grep/Glob/Read, without any LLM: callers via AST search by function name across repo `.py` files, callees via body read of the target function, and impact via search of who imports the suspect module. It records the real Phase 2 mode in `sessao.json` (`fase2.modo` = `"grafo"` or `"fallback"`) — never claim graph provenance for conclusions derived by static fallback. Exit 1 means the fallback itself could not run; exit 0 means Phase 2 completed in either mode.
3. **Single Hypothesis Formulation:**
   - Formulate exactly ONE testable hypothesis: *"The failure occurs because function X receives null input when Y is uninitialized"*.
4. **Instrumentation & Proof:**
   - Add minimal assertions or temporary instrumentation to prove or disprove the hypothesis.
   - If disproved, discard immediately and formulate the next hypothesis. If proved, proceed.
5. **Surgical Fix & Regression Test:**
   - Apply the minimal viable fix.
   - Convert the reproduction step from Phase 1 into a permanent automated regression test.
   - Strip all temporary instrumentation before committing.
