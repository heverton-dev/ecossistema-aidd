# AGENTS.md — Canonical Governance Directives

This repository adheres to the AIDD Framework.
All AI agent operations must strictly follow these invariant directives.

## Core Execution Constraints

<!-- AIDD-FORGE:EXEC-DIRECTIVES:BEGIN -->
- **Thinking constraint:** Think strictly in compact English. No meta-deliberation. Focus only on architectural invariants and edge cases. Under 150 words of reasoning.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format:** Silent executor. Return code edits and 1-line execution status only. Do not explain what was changed unless explicitly asked. Do not repeat code in conversational reply.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest 2>&1 | tail -n 25`. Never dump raw bundle outputs, logs, or lockfiles into context.
- **Graph-first:** Always query knowledge graph (code-review-graph MCP) before Grep, Glob, or full file reads.
<!-- AIDD-FORGE:EXEC-DIRECTIVES:END -->

## Inviolable Laws

1. **Determinism First:** Use deterministic scripts, AST, regex, or JSON Schema.
2. **Binary Quality:** Every change must pass Quality Gates (exit 0 = pass, exit 1 = block).
3. **Zero Stubs / Zero Mocks:** 100% functional, typed production code.
4. **Extreme Token Economy:** Minimalist prompts, compact English core rules, dense PT-BR user responses.
