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
   - Use `code-review-graph` (`query_graph_tool` with callers/callees, `detect_changes_tool`, `get_impact_radius_tool`).
   - Trace entry points, affected call flows, and direct downstream consumers.
3. **Single Hypothesis Formulation:**
   - Formulate exactly ONE testable hypothesis: *"The failure occurs because function X receives null input when Y is uninitialized"*.
4. **Instrumentation & Proof:**
   - Add minimal assertions or temporary instrumentation to prove or disprove the hypothesis.
   - If disproved, discard immediately and formulate the next hypothesis. If proved, proceed.
5. **Surgical Fix & Regression Test:**
   - Apply the minimal viable fix.
   - Convert the reproduction step from Phase 1 into a permanent automated regression test.
   - Strip all temporary instrumentation before committing.
