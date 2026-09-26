---
name: aidd-tickets
description: Decomposes specifications into atomic, incremental tracer-bullet tasks with bounded blast radius.
---

# AIDD-Tickets — Atomic Task Decomposition

Decomposes the specification created by `/aidd-spec` into executable tickets operating as *tracer bullets* (end-to-end functional vertical slices), ordered by explicit blockers instead of a fixed phase sequence.

## Decomposition Invariants

1. **Vertical Slice:** Each ticket delivers one complete, independently verifiable behavior, cutting through every layer it needs (contract, test, code, wiring). Never split one behavior into a "tests" ticket, a "code" ticket and a "refactor" ticket: each ticket carries its own failing test, implementation and cleanup. Never a setup-only ticket (types, exceptions, module skeleton): that code goes inside the first behavior ticket that needs it, and every ticket's Target Files include at least one test file.
2. **Fresh Context Fit:** Each ticket must be small enough to be executed from a fresh context window using only its own text plus the files it names.
3. **Bounded Blast Radius:** Each ticket must touch the minimum set of contiguous files necessary.
4. **Prefactor First:** When the code must be reshaped before the new behavior fits, the prefactor is its own ticket, scheduled first and blocking the tickets that depend on it. A prefactor changes structure only, never behavior.
5. **Explicit Blockers:** Every ticket declares **Blocked by:** with the IDs it waits on, or `none`. A ticket with no blockers can start immediately; tickets without a blocker between them may run in parallel.
6. **Wide Refactor (expand → migrate → contract):** A change that touches many call sites is never one big-bang ticket. Split it into: expand (add the new path next to the old one), migrate in batches (one ticket per batch of callers, each green on its own), contract (remove the old path only after the last batch).
7. **Standard Ticket Schema:**
   - **ID & Title:** `[TICKET-XX] <Clear imperative action>`
   - **Target Files:** Explicit relative paths to modified or created files.
   - **Validation Command:** Exact automated command verifying ticket completion (e.g., `pytest tests/test_mod.py`, `cargo test`, `go test ./...`).
   - **Blocked by:** Comma-separated ticket IDs, or `none`.

## Example

```markdown
### [TICKET-01] Reject expired tokens at login
- **Target Files:** src/auth/login.py, tests/test_login_expired.py
- **Validation Command:** `pytest tests/test_login_expired.py`
- **Blocked by:** none

### [TICKET-02] Show token expiry reason in login response
- **Target Files:** src/auth/login.py, tests/test_login_reason.py
- **Validation Command:** `pytest tests/test_login_reason.py`
- **Blocked by:** TICKET-01
```

## Publishing

1. Present the full ticket list (titles, blockers, target files, validation commands) to the user for review and approval before you publish it. Do not publish without explicit approval.
2. **Downstream Dispatch:** Approved tickets feed directly into `aidd-master` (Vertical Slices) or the structured plan execution engine; `scripts/compilador_tickets_plano.py` parses the schema above (`[TICKET-XX]` headers, Target Files, Validation Command, Blocked by).
