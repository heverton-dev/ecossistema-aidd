# Gemini Agent Pointer
Canonical governance and instructions: [AGENTS.md](AGENTS.md)

## Mandatory Answer Shape (Rule 10 / Law #4)
1. One top sentence stating what to do or what happened. No preamble.
2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
3. One closing suggestion block, separated from the body.
Forbidden: introductions, restating the request, recapping what was just said, listing options without a recommendation.

*Note on Hook Enforcement:* Automated stop-hook enforcement is unavailable in Gemini CLI / Antigravity due to lack of a native response-interception hook event; compliance is maintained by convention.

## Universal & Agnostic Flow Activation (Law #6)
- Any user input referencing `/freedom`, `freedom`, `/pure`, `pure`, `/open`, `/aidd-open`, `open`, `/factory`, `/bridge`, `bridge`, `/run-plan`, `run-plan`, `/pipeline`, `pipeline`, or natural language equivalents (e.g. "desacoplar lovable", "criar do zero puro", "migrar open source", "executar plano", "rodar pipeline") MUST be intercepted immediately by the agent as the direct invocation of the corresponding Canonical Flow, Pipeline or Tool.
- **Importante para o Fluxo 02 no Antigravity/AGY:** No Antigravity CLI (`agy`), o comando `/open <path>` é reservado internamente para abrir arquivos no editor do sistema. Portanto, no AGY utilize o comando `/aidd-open` (ou `/factory` ou menção natural) para disparar o Fluxo 02 sem conflito de namespace.
- **NEVER** reply that the command is unknown, unsupported, or invalid.
- Immediately execute the corresponding skill (`freedom`, `pure`, `aidd-open`, `open`, `aidd-bridge-runner`, `aidd-pipeline-runner`) or CLI command (`python ecossistema.py freedom|pure|open|bridge|run-plan|pipeline <args>`).
- If arguments are missing, ask for the required input (e.g., path to export, plan path, or handoff JSON) while confirming that the flow is active.

