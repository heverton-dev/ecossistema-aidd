# AIDD Generator — Canonical Agent Directives & Factory Rules

> **Tool:** `aidd-pure`  
> **Role:** Autonomous 8-Phase Software Factory (Idea -> Fully Tested & Audited System).  
> **Governance Standard:** Schema-First (Draft 2020-12), Zero Token Waste, Deterministic Gates.

---

## 1. Core Execution Constraints

- Root `AGENTS.md` §1 governs execution (compact thinking, 3-5 steps, silent executor, piped bash, exact edits).

---

## 2. Factory Architecture & Invariants

1. **Deterministic Persistence:** State is strictly persisted in `PLANO-EXECUCAO-ESTRUTURADO.json` (root). Agents read JSON state (~5k tokens), never conversational history.
2. **Strict 8-Phase Pipeline:**
   - Phase 1: Research (`pesquisa`) -> Phase 2: Analyzer (`analisador`)
   - Phase 3: Designer (`designer`) -> Phase 4: Planner (`planejador`)
   - Phase 5: Creator (`criador`) -> Phase 6: Documenter (`documentador`)
   - Phase 7: Self-Critique (`auto_critica`) -> Phase 8: Implementer (`implementador`)
3. **Mechanical Gates:** Every phase transition requires `exit 0` from validation gates (`python scripts/validar_fase.py --fase N`). Exit 1 strictly blocks progression.
4. **Zero Stubs:** Code produced in Phase 8 must be fully typed, production-ready, and accompanied by executable tests.
5. **Engineering Skills Alignment:** Phases 1 and 2 strictly leverage `/aidd-spec` (formal deterministic specs) and `/aidd-tickets` (atomic task decomposition) to prevent vibe coding.

---

## 3. Command Dispatch

- `/generate <idea>`: Triggers the autonomous software pipeline via `python ecossistema.py generate "<idea>"`.
- Phase-specific operations execute via deterministic CLI in `scripts/`.
