---
name: aidd-spec
description: Synthesizes discussions, requirements, and decisions into a deterministic, executable technical specification.
---

# AIDD-Spec — Deterministic Technical Specification

Transforms idea discussions, user briefings, and `aidd-grill` resolutions into a formal, auditable specification ready for task decomposition.

## Mandatory Specification Structure

Every specification produced by this skill must include:

1. **Context & Explicit Non-Goals:** What is being built and what is strictly out of scope.
2. **Contracts & Typed Interfaces:** Concrete definitions of structs, types, JSON schemas, or service interfaces (polyglot: Python, Go, Rust, TypeScript).
3. **Invariants & Business Rules:** Numbered list of logical invariants the system must enforce at all times.
4. **Binary Acceptance Criteria:** Objective, mechanically verifiable conditions (e.g., *"Endpoint returns 404 when ID is missing"*, *"Test X passes with exit code 0"*).
5. **Failure & Degradation Modes:** Expected behavior on timeouts, malformed inputs, or downstream service failures.

## Efficiency Rules
- Concise, dense Markdown. Zero conversational filler.
- Outputs must be structured for direct insertion into `docs/planos/`.
- Upon user approval of the specification, invoke `/aidd-tickets` or proceed directly to `/aidd-planner`.

## Encadeamento Canônico de Intake
Após aprovação da especificação formal:
- **Próxima Skill:** `/aidd-planner` (gera o blueprint formal `PLANNER.json` com DDD/BDD/SDD).
- **Fluxo Geral:** `/aidd-grill` ➔ `/aidd-spec` ➔ `/aidd-planner` ➔ `/aidd-dispatch-runner`.

