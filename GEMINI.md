# Gemini Agent Pointer
Canonical governance and instructions: [AGENTS.md](AGENTS.md)

## Mandatory Answer Shape (Rule 10 / Law #4)
1. One top sentence stating what to do or what happened. No preamble.
2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
3. One closing suggestion block, separated from the body.
Forbidden: introductions, restating the request, recapping what was just said, listing options without a recommendation.

*Note on Hook Enforcement:* Automated stop-hook enforcement is unavailable in Gemini CLI / Antigravity due to lack of a native response-interception hook event; compliance is maintained by convention.

## Universal & Agnostic Flow Activation (Law #6)
Since Gemini CLI and Google Antigravity UI do not register arbitrary user slash commands in the UI prompt box:
- Any user input referencing `/freedom`, `freedom`, `/pure`, `pure`, `/open`, `open`, `/bridge`, `bridge`, or natural language equivalents (e.g. "desacoplar lovable", "criar do zero puro", "migrar open source") MUST be intercepted immediately by the agent as the direct invocation of the corresponding Canonical Flow or Tool.
- **NEVER** reply that the command is unknown, unsupported, or invalid.
- Immediately execute the corresponding skill (`aidd-freedom`, `aidd-pure`, `aidd-open`, `aidd-bridge-runner`) or CLI command (`python ecossistema.py freedom|pure|open|bridge <args>`).
- If arguments are missing, ask for the required input (e.g., path to export) while confirming that the flow is active.

