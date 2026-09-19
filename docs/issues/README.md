# `docs/issues/` — work tickets

Experiment started 2026-09-19. A ticket is a slice of work small enough for one
clean session, cutting end-to-end through the system (not one layer), demoable on
its own when finished.

**Versus `docs/planos/`:** a plan is an initiative with governance, 0-10 scores and
formal human approval. A ticket is smaller and more direct — born ready for someone
(person or agent) to pick up and execute. One plan may spawn several tickets; a
ticket never replaces a plan.

## Language rule (AGENTS.md Law #4)

Core rules go in compact English; dense PT-BR is for user-facing answers. Applied here:

- **Title and `title:` field — PT-BR.** The user scans the index in their own language.
- **Body — English, telegraphic imperative.** The agent reads this.
- **Field names and values — English.** Machine-parseable, one convention.

Measured on this set: English telegraphic costs ~33% fewer tokens than the PT-BR
prose original (~13% from the language, ~20% from the style).

## Format

One numbered `.md` per ticket. Data header between `---` at the top:

| Field | Purpose |
|---|---|
| `id` | stable identifier; survives file rename |
| `title` | short name, PT-BR |
| `status` | `ready-for-agent`, `in-progress`, `done`, `archived` |
| `blocked_by` | list of ids that must finish first; `[]` means start now |
| `created` | date |
| `source` | where the demand came from |

Header is script-readable; body is human-readable. One source of truth.

## Honesty rule

Same Law #8 as the rest of the project: tick an acceptance criterion only after
**real reproduction** — command run, exit code checked. Reading the code and
concluding it should work does not close a criterion.
