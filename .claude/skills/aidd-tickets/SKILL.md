---
name: aidd-tickets
description: Decomposes specifications into atomic, incremental tracer-bullet tasks with bounded blast radius.
---

# AIDD-Tickets — Atomic Task Decomposition

Decomposes the specification created by `/aidd-spec` into a linear sequence of executable tickets operating as *tracer bullets* (end-to-end functional vertical slices).

## Decomposition Invariants

1. **Atomicity:** Each ticket must be fully self-contained and independently testable.
2. **Bounded Blast Radius:** Each ticket must touch the minimum set of contiguous files necessary.
3. **Strict Dependency Order:**
   - Ticket 1: Types/Contracts and Failing Tests (Red).
   - Ticket 2: Minimal Functional Implementation (Green).
   - Ticket 3: Refactoring, System Integration, and Gate Validation.
4. **Standard Ticket Schema:**
   - **ID & Title:** `[TICKET-XX] <Clear imperative action>`
   - **Target Files:** Explicit relative paths to modified or created files.
   - **Validation Command:** Exact automated command verifying ticket completion (e.g., `pytest tests/test_mod.py`, `cargo test`, `go test ./...`).
5. **Downstream Dispatch:** Generated tickets feed directly into `aidd-master` (Vertical Slices) or the structured plan execution engine.
