---
name: aidd-handoff
description: Serializes and compacts session state into a structured markdown artifact for context rotation or agent handover.
---

# AIDD-Handoff — Structured Context Preservation

Execute this skill when closing a session, rotating context, or transferring work between agents to prevent knowledge drift and token fragmentation.

## Protocol Invariants

1. **Artifact Destination:**
   - Save the serialized handoff to `secoes/sessao-<date>-<slug>.md`.
2. **Mandatory Handoff Sections:**
   - **Initial Goal:** What was originally requested.
   - **Completed Work:** Explicit list of created/modified files and verified test suites.
   - **Quality Gate State:** Current status of gates (`python ecossistema.py audit`, test runner outputs).
   - **Next Actions:** Prioritized, sequential backlog for the incoming agent.
   - **Discovered Invariants & Gotchas:** Non-obvious architectural nuances or discovered edge cases.
3. **Extreme Token Economy:**
   - Never paste full source code into the handoff artifact. Reference relative file paths and symbol names.
   - Use telegraphic markdown tables and bullet points.
