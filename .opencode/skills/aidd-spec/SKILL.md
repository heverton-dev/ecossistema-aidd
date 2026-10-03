---
name: aidd-spec
description: Turns discussions and decisions into an executable spec with binary acceptance criteria. Use when writing a spec, or "especificação".
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

## Negative Guardrails

- NEVER hand a spec to `/aidd-planner` or `/aidd-tickets` before `python ecossistema.py spec validar --arquivo <spec.md>` exits 0.
- NEVER rename or reorder the 5 headings; `scripts/parser.py` finds them by regex (`Context & Explicit Non-Goals` ... `Failure & Degradation Modes`) and fails the spec when one is missing.
- NEVER write an acceptance criterion that no command, exit code or HTTP status can check ("works well", "is fast").
- NEVER add a decision the user or the `aidd-grill` resolutions did not make; list it as a Non-Goal or an open question.
- NEVER hand-write the compiled JSON; only `spec compilar --output` or `spec exportar --output` produce the signed handoff.

## Failure Modes & Fallback

- **`[FALHA] Validação estrutural`:** a heading is missing or misspelled. Fix the heading named in the output and re-run `spec validar`.
- **`[FALHA] Validação de critérios e regras`:** a criterion is not binary or the invariants are not numbered. Rewrite those items and re-run.
- **`[FALHA] Não foi possível gerar o handoff assinado`:** re-run `spec compilar` with a writable `--output`; if it fails again, report the stderr to the user.
- **Key decision still open:** stop and send the question back to `/aidd-grill` instead of guessing it into the spec.

## Stopping Checklist

- [ ] `python ecossistema.py spec validar --arquivo <spec.md> > validar.log 2>&1; echo $? > validar.exit` gives 0.
- [ ] `python ecossistema.py spec compilar --arquivo <spec.md> --output <manifest.json> > compilar.log 2>&1; echo $? > compilar.exit` gives 0 and the JSON exists.
- [ ] Every Binary Acceptance Criteria item names a command, an exit code or an HTTP status.
- [ ] The user approved the spec in this conversation before the next skill was invoked.

## Encadeamento Canônico de Intake
Após aprovação da especificação formal:
- **Próxima Skill:** `/aidd-planner` (gera o blueprint formal `PLANNER.json` com DDD/BDD/SDD).
- **Fluxo Geral:** `/aidd-grill` ➔ `/aidd-spec` ➔ `/aidd-planner` ➔ `/aidd-dispatch`.

