# `docs/issues/pipeline-orquestracao-triade/` — Work Tickets

Initiative: **Pipeline Unificado de Orquestração com Acionamento Tríade e Git Worktrees**  
Target: Bridge the gap between planning (`aidd-plan` / `aidd-planner`) and deterministic execution (`tools/aidd-master/scripts/orchestrator_pipeline.py`) across all harnesses.

## Language Rule (AGENTS.md Law #4)
- **Title and `title:` field — PT-BR:** Fast visual scanning by Brazilian developers.
- **Body — English, telegraphic imperative:** Token-efficient agent instruction.
- **Field names and values — English:** Machine-parseable by gates and scripts.

## Invariant Laws Enforced
- **Law #1 (Determinism First):** Execution driven strictly by JSON Schema (`handoff-execucao.schema.json`).
- **Law #2 (Binary Quality):** Every ticket and phase verified by real tests with binary exit code (0 or 1).
- **Law #3 (Structured Persistence):** Execution state persisted in JSON artifacts, never volatile conversation memory.
- **Law #4 (Extreme Token Economy):** Git Worktrees isolate filesystem changes without duplicate LLM context loads.
- **Law #6 (Agnostic Supremacy):** Universal triad dispatch (CLI `ecossistema.py`, Slash commands, Skill runners).
- **Law #7 (Developer in Control):** Strictly sequential phase gates; zero invisible concurrent headless agents.
- **Law #13 (Gate Must Bite):** All new gates include automated tests asserting exit 1 on violation.
